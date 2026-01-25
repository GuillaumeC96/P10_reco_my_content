"""
Moteur de recommandation hybride
Combine collaborative filtering et content-based filtering
"""

import numpy as np
import pickle
from scipy.sparse import load_npz
from scipy.spatial.distance import cosine
from sklearn.metrics.pairwise import cosine_similarity
import json
from typing import List, Dict, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

class RecommendationEngine:
    """Système de recommandation hybride"""

    # CONFIGURATION TEMPORELLE (State-of-Art pour News Recommendation)
    # Articles de news ont une durée de vie limitée (hype window)
    MAX_ARTICLE_AGE_DAYS = 60  # 60 jours max pour recommandations (ajusté pour dataset)
    TEMPORAL_HALF_LIFE_DAYS = 7  # Half-life: après 7 jours, score divisé par 2
    TEMPORAL_DECAY_LAMBDA = 0.099  # ln(2)/7 ≈ 0.099

    def __init__(self, models_path: str = "./models"):
        """
        Initialise le moteur de recommandation

        Args:
            models_path: Chemin vers le dossier contenant les modèles
        """
        self.models_path = models_path
        self.user_item_matrix = None
        self.weighted_user_item_matrix = None  # Matrice pondérée avec interaction_weight
        self.mappings = None
        self.article_popularity = None
        self.user_profiles = None
        self.embeddings = None
        self.metadata = None
        self.article_timestamps = None  # Index optimisé pour temporal decay
        self.article_categories = None  # Index optimisé pour category boost
        self.loaded = False

    def load_models(self):
        """Charge tous les modèles et données nécessaires"""
        logger.info("Chargement des modèles...")

        try:
            # Charger la matrice user-item (counts)
            self.user_item_matrix = load_npz(f"{self.models_path}/user_item_matrix.npz")
            logger.info(f"Matrice user-item (counts) chargée: {self.user_item_matrix.shape}")

            # Charger la matrice pondérée (interaction_weight) si disponible
            try:
                self.weighted_user_item_matrix = load_npz(f"{self.models_path}/user_item_matrix_weighted.npz")
                logger.info(f"Matrice pondérée chargée: {self.weighted_user_item_matrix.shape}")
                logger.info(f"  Weighted values: min={self.weighted_user_item_matrix.data.min():.3f}, "
                           f"max={self.weighted_user_item_matrix.data.max():.3f}, "
                           f"mean={self.weighted_user_item_matrix.data.mean():.3f}")
            except FileNotFoundError:
                logger.warning("Matrice pondérée non trouvée, utilisation de la matrice counts")
                self.weighted_user_item_matrix = None

            # Charger les mappings
            with open(f"{self.models_path}/mappings.pkl", 'rb') as f:
                self.mappings = pickle.load(f)
            logger.info(f"Mappings chargés: {len(self.mappings['user_to_idx'])} users")

            # Charger la popularité
            with open(f"{self.models_path}/article_popularity.pkl", 'rb') as f:
                self.article_popularity = pickle.load(f)
            logger.info(f"Popularité chargée: {len(self.article_popularity)} articles")

            # Charger les profils utilisateurs ENRICHIS (avec 9 signaux + filtre 30s)
            # Priorité: .pkl (plus rapide) > .json (fallback)
            try:
                with open(f"{self.models_path}/user_profiles_enriched.pkl", 'rb') as f:
                    self.user_profiles = pickle.load(f)
                logger.info(f"Profils utilisateurs enrichis chargés (PKL): {len(self.user_profiles)} users")
            except FileNotFoundError:
                try:
                    with open(f"{self.models_path}/user_profiles_enriched.json", 'r') as f:
                        self.user_profiles = json.load(f)
                    # Convertir les clés en int
                    self.user_profiles = {int(k): v for k, v in self.user_profiles.items()}
                    logger.info(f"Profils utilisateurs enrichis chargés (JSON): {len(self.user_profiles)} users")
                except FileNotFoundError:
                    # Fallback vers ancienne version (sans filtrage 30s)
                    logger.warning("Profils enrichis non trouvés, utilisation de la version basique")
                    with open(f"{self.models_path}/user_profiles.json", 'r') as f:
                        self.user_profiles = json.load(f)
                    self.user_profiles = {int(k): v for k, v in self.user_profiles.items()}
                    logger.info(f"Profils utilisateurs basiques chargés: {len(self.user_profiles)} users")

            # Charger les embeddings
            with open(f"{self.models_path}/embeddings_filtered.pkl", 'rb') as f:
                self.embeddings = pickle.load(f)
            logger.info(f"Embeddings chargés: {len(self.embeddings)} articles")

            # Charger les métadonnées (on pourrait utiliser pandas mais pour Azure Functions, on optimise)
            import pandas as pd
            self.metadata = pd.read_csv(f"{self.models_path}/articles_metadata.csv")
            logger.info(f"Métadonnées chargées: {len(self.metadata)} articles")

            # Créer des index optimisés pour performance
            # Index: article_id -> created_at_ts (pour temporal decay)
            self.article_timestamps = dict(zip(
                self.metadata['article_id'],
                self.metadata['created_at_ts']
            ))
            # Index: article_id -> category_id (pour category boost)
            self.article_categories = dict(zip(
                self.metadata['article_id'],
                self.metadata['category_id']
            ))
            logger.info(f"Index créés: {len(self.article_timestamps)} timestamps, "
                       f"{len(self.article_categories)} catégories")

            self.loaded = True
            logger.info("✓ Tous les modèles chargés avec succès")

        except Exception as e:
            logger.error(f"Erreur lors du chargement des modèles: {e}")
            raise

    def _get_user_history(self, user_id: int) -> List[int]:
        """Récupère l'historique d'articles d'un utilisateur"""
        if user_id in self.user_profiles:
            return self.user_profiles[user_id]['articles_read']
        return []

    def _collaborative_filtering(self, user_id: int, n_recommendations: int = 20,
                                 use_weighted_matrix: bool = True) -> List[Tuple[int, float]]:
        """
        Recommandations par filtrage collaboratif avec matrice pondérée

        Args:
            user_id: ID de l'utilisateur
            n_recommendations: Nombre de recommandations
            use_weighted_matrix: Utiliser la matrice pondérée si disponible (défaut: True)

        Returns:
            Liste de tuples (article_id, score)

        Note:
            Matrice pondérée capture l'engagement réel (temps, qualité) vs simple counts.
            Amélioration attendue: +2-5% HR@5 (littérature: +15-30% weighted vs binary)
        """
        # Vérifier si l'utilisateur existe dans la matrice
        if user_id not in self.mappings['user_to_idx']:
            logger.info(f"Utilisateur {user_id} inconnu pour collaborative filtering")
            return []

        user_idx = self.mappings['user_to_idx'][user_id]

        # Choisir la matrice à utiliser (pondérée si disponible et demandée)
        if use_weighted_matrix and self.weighted_user_item_matrix is not None:
            matrix = self.weighted_user_item_matrix
            logger.debug(f"Utilisation de la matrice PONDÉRÉE pour collaborative filtering")
        else:
            matrix = self.user_item_matrix
            logger.debug(f"Utilisation de la matrice COUNTS pour collaborative filtering")

        # Obtenir le vecteur de l'utilisateur
        user_vector = matrix[user_idx].toarray().flatten()

        # Calculer la similarité avec tous les autres utilisateurs
        similarities = cosine_similarity(
            matrix[user_idx],
            matrix
        ).flatten()

        # Trouver les k utilisateurs les plus similaires (exclure l'utilisateur lui-même)
        k = min(50, self.user_item_matrix.shape[0])
        similar_users_idx = np.argsort(similarities)[-k-1:-1][::-1]

        # Agréger les articles des utilisateurs similaires
        recommended_articles = {}
        for sim_user_idx in similar_users_idx:
            if similarities[sim_user_idx] > 0:
                # Récupérer les articles de cet utilisateur (même matrice que pour similarité)
                sim_user_vector = matrix[sim_user_idx].toarray().flatten()
                for article_idx, weight in enumerate(sim_user_vector):
                    if weight > 0 and user_vector[article_idx] == 0:  # Pas déjà vu par l'utilisateur
                        article_id = self.mappings['idx_to_article'][article_idx]
                        if article_id not in recommended_articles:
                            recommended_articles[article_id] = 0
                        # Score = similarité * poids d'interaction (counts ou weights)
                        recommended_articles[article_id] += similarities[sim_user_idx] * weight

        # Trier par score
        sorted_articles = sorted(recommended_articles.items(), key=lambda x: x[1], reverse=True)

        return sorted_articles[:n_recommendations]

    def _content_based_filtering(self, user_id: int, n_recommendations: int = 20,
                                 use_weighted_aggregation: bool = True) -> List[Tuple[int, float]]:
        """
        Recommandations par filtrage basé sur le contenu avec agrégation pondérée

        Args:
            user_id: ID de l'utilisateur
            n_recommendations: Nombre de recommandations
            use_weighted_aggregation: Utiliser les poids d'interaction pour agréger (défaut: True)

        Returns:
            Liste de tuples (article_id, score)

        Note:
            Agrégation pondérée: articles mieux engagés ont plus d'influence sur le profil.
            Amélioration attendue: +1-3% HR@5
        """
        # Récupérer l'historique de l'utilisateur
        user_history = self._get_user_history(user_id)

        if not user_history:
            logger.info(f"Pas d'historique pour l'utilisateur {user_id}")
            return []

        # Calculer l'embedding avec pondération par interaction_weight si disponible
        user_embeddings = []
        weights = []

        if user_id in self.mappings['user_to_idx'] and use_weighted_aggregation and self.weighted_user_item_matrix is not None:
            # Utiliser les poids de la matrice pondérée
            user_idx = self.mappings['user_to_idx'][user_id]
            user_weights_vector = self.weighted_user_item_matrix[user_idx].toarray().flatten()

            for article_id in user_history:
                if article_id in self.embeddings and article_id in self.mappings['article_to_idx']:
                    article_idx = self.mappings['article_to_idx'][article_id]
                    weight = user_weights_vector[article_idx]
                    if weight > 0:
                        user_embeddings.append(self.embeddings[article_id])
                        weights.append(weight)
        else:
            # Fallback: pas de pondération (poids uniformes)
            for article_id in user_history:
                if article_id in self.embeddings:
                    user_embeddings.append(self.embeddings[article_id])
                    weights.append(1.0)

        if not user_embeddings:
            return []

        # Calculer l'embedding du profil utilisateur (pondéré ou moyen)
        if weights and sum(weights) > 0:
            weights_array = np.array(weights)
            weights_normalized = weights_array / weights_array.sum()
            user_profile_embedding = np.average(user_embeddings, axis=0, weights=weights_normalized)
        else:
            user_profile_embedding = np.mean(user_embeddings, axis=0)

        # Calculer les catégories préférées de l'utilisateur (lookup optimisé)
        user_categories = {}
        for article_id in user_history:
            if article_id in self.article_categories:
                category = self.article_categories[article_id]
                user_categories[category] = user_categories.get(category, 0) + 1

        # Calculer la similarité avec tous les articles + category boost (optimisé)
        article_scores = {}
        for article_id, embedding in self.embeddings.items():
            if article_id not in user_history:  # Ne pas recommander ce qui a déjà été lu
                # Similarité de contenu
                similarity = 1 - cosine(user_profile_embedding, embedding)

                # Category boost: +10% si dans catégories préférées (lookup optimisé O(1))
                if user_categories and article_id in self.article_categories:
                    category = self.article_categories[article_id]
                    if category in user_categories:
                        # Boost proportionnel à la fréquence de cette catégorie
                        category_freq = user_categories[category] / len(user_history)
                        boost = 1.0 + (0.1 * category_freq)  # Max +10% boost
                        similarity *= boost

                article_scores[article_id] = similarity

        # Trier par score
        sorted_articles = sorted(article_scores.items(), key=lambda x: x[1], reverse=True)

        return sorted_articles[:n_recommendations]

    def _popularity_based(self, n_recommendations: int = 20, exclude_articles: Optional[List[int]] = None,
                         use_temporal_decay: bool = True, decay_half_life_days: float = 7.0,
                         max_age_days: Optional[float] = None) -> List[Tuple[int, float]]:
        """
        Recommandations basées sur la popularité avec fenêtre de hype et décroissance temporelle

        Args:
            n_recommendations: Nombre de recommandations
            exclude_articles: Articles à exclure
            use_temporal_decay: Activer la décroissance temporelle (défaut: True)
            decay_half_life_days: Demi-vie pour le decay en jours (défaut: 7 jours)
            max_age_days: Âge maximum en jours (défaut: MAX_ARTICLE_AGE_DAYS = 14)

        Returns:
            Liste de tuples (article_id, score)

        Note:
            FENÊTRE DE HYPE (State-of-Art News Recommendation):
            - Articles > max_age_days sont EXCLUS (pas recommandés)
            - Par défaut: 14 jours (2 semaines) pour hard news
            - Decay exponentiel avec half-life = 7 jours
            - Formula: score = popularity * exp(-age_days * ln(2) / half_life)

            Impact:
            - Age 0j: 100% du score (article frais)
            - Age 7j: 50% du score (half-life)
            - Age 14j: 25% du score (limite)
            - Age >14j: EXCLU (hors fenêtre de hype)
        """
        exclude_articles = exclude_articles or []

        # Fenêtre de hype par défaut: 14 jours (state-of-art)
        if max_age_days is None:
            max_age_days = self.MAX_ARTICLE_AGE_DAYS

        # Timestamp actuel en millisecondes
        import time
        now_ts = int(time.time() * 1000)

        # Filtrer et calculer scores avec fenêtre de hype + temporal decay
        popular_articles = []
        excluded_old_count = 0  # Pour logging

        # Gérer les deux formats: dict ou DataFrame
        if isinstance(self.article_popularity, dict):
            popularity_items = self.article_popularity.items()
        else:
            popularity_items = [(aid, row['popularity_score']) for aid, row in self.article_popularity.iterrows()]

        for article_id, base_score in popularity_items:
            if article_id not in exclude_articles:

                if article_id in self.article_timestamps:
                    # Lookup optimisé O(1) au lieu de O(n) DataFrame scan
                    created_ts = self.article_timestamps[article_id]
                    age_ms = now_ts - created_ts
                    age_days = age_ms / (86400 * 1000)  # Convertir ms -> jours

                    # FENÊTRE DE HYPE: Exclure articles trop vieux
                    if age_days > max_age_days:
                        excluded_old_count += 1
                        continue  # Article trop vieux, pas recommandé

                    if use_temporal_decay:
                        # Décroissance exponentielle: half-life = 7 jours pour news
                        # Après 7 jours: score *= 0.5
                        # Après 14 jours: score *= 0.25
                        decay_factor = np.exp(-age_days * np.log(2) / decay_half_life_days)
                        adjusted_score = base_score * decay_factor
                        popular_articles.append((article_id, adjusted_score))
                    else:
                        popular_articles.append((article_id, base_score))
                else:
                    # Fallback: pas de timestamp, on garde l'article (risqué)
                    logger.warning(f"Article {article_id} sans timestamp, inclus par défaut")
                    popular_articles.append((article_id, base_score))

        if excluded_old_count > 0:
            logger.info(f"Fenêtre de hype: {excluded_old_count} articles exclus (> {max_age_days} jours)")

        # Trier par score ajusté
        popular_articles = sorted(popular_articles, key=lambda x: x[1], reverse=True)

        return popular_articles[:n_recommendations]

    def _diversity_filtering(self, articles: List[Tuple[int, float]], n_final: int = 5) -> List[Tuple[int, float]]:
        """
        Applique un filtre de diversité pour assurer une variété de catégories

        Args:
            articles: Liste de tuples (article_id, score)
            n_final: Nombre final d'articles

        Returns:
            Liste filtrée avec diversité de catégories
        """
        if len(articles) <= n_final:
            return articles

        # Créer des groupes par catégorie avec leurs scores
        category_articles = {}
        for article_id, score in articles:
            article_info = self.metadata[self.metadata['article_id'] == article_id]
            if not article_info.empty:
                category = article_info.iloc[0]['category_id']
                if category not in category_articles:
                    category_articles[category] = []
                category_articles[category].append((article_id, score))

        # Trier chaque groupe par score
        for category in category_articles:
            category_articles[category].sort(key=lambda x: x[1], reverse=True)

        # Sélection round-robin pour maximiser la diversité
        selected = []
        round_idx = 0
        categories = list(category_articles.keys())

        while len(selected) < n_final and len(categories) > 0:
            # Pour chaque catégorie, prendre le meilleur article non encore sélectionné
            categories_to_remove = []
            for category in categories:
                if round_idx < len(category_articles[category]):
                    article = category_articles[category][round_idx]
                    if article not in selected:
                        selected.append(article)
                        if len(selected) >= n_final:
                            break
                else:
                    categories_to_remove.append(category)

            # Retirer les catégories épuisées
            for cat in categories_to_remove:
                categories.remove(cat)

            round_idx += 1

        # Si on n'a toujours pas assez, compléter avec les meilleurs scores restants
        if len(selected) < n_final:
            remaining = [a for a in articles if a not in selected]
            selected.extend(remaining[:n_final - len(selected)])

        return selected[:n_final]

    def recommend(self, user_id: int, n_recommendations: int = 5,
                  weight_collab: float = 0.36, weight_content: float = 0.39,
                  weight_trend: float = 0.25, use_diversity: bool = True) -> List[Dict]:
        """
        Génère des recommandations hybrides pour un utilisateur avec 3 coefficients

        Args:
            user_id: ID de l'utilisateur
            n_recommendations: Nombre de recommandations à retourner
            weight_collab: Poids du collaborative filtering (défaut: 0.36 = 36%)
            weight_content: Poids du content-based filtering (défaut: 0.39 = 39%)
            weight_trend: Poids du trend/popularity filtering (défaut: 0.25 = 25%)
            use_diversity: Appliquer le filtre de diversité

        Returns:
            Liste de dictionnaires avec les recommandations

        Note:
            Les poids sont normalisés automatiquement pour sommer à 1.0
            Valeurs par défaut: 3:2:1 (collaborative:content:trend)
        """
        if not self.loaded:
            raise RuntimeError("Les modèles ne sont pas chargés. Appelez load_models() d'abord.")

        # Normaliser les poids pour qu'ils somment à 1
        total_weight = weight_collab + weight_content + weight_trend
        weight_collab = weight_collab / total_weight
        weight_content = weight_content / total_weight
        weight_trend = weight_trend / total_weight

        logger.info(f"Génération de {n_recommendations} recommandations pour user {user_id}")
        logger.info(f"Poids normalisés - Collab: {weight_collab:.2f}, Content: {weight_content:.2f}, Trend: {weight_trend:.2f}")

        user_history = self._get_user_history(user_id)
        is_cold_start = len(user_history) == 0

        if is_cold_start:
            logger.info(f"Cold start pour user {user_id}, utilisation de la popularité")
            # Pour un nouvel utilisateur, utiliser la popularité
            candidate_articles = self._popularity_based(n_recommendations=n_recommendations * 3)
        else:
            # Obtenir plus de candidats pour avoir plus de diversité
            n_candidates = n_recommendations * 10

            # Obtenir les recommandations collaborative
            collab_recs = self._collaborative_filtering(user_id, n_recommendations=n_candidates)

            # Obtenir les recommandations content-based
            content_recs = self._content_based_filtering(user_id, n_recommendations=n_candidates)

            # Obtenir les recommandations basées sur les tendances (toujours incluses maintenant)
            trend_recs = self._popularity_based(n_recommendations=n_candidates, exclude_articles=user_history)

            # Combiner les scores avec les 3 coefficients
            combined_scores = {}

            # Normaliser les scores collaborative
            if collab_recs:
                max_collab = max(score for _, score in collab_recs)
                for article_id, score in collab_recs:
                    combined_scores[article_id] = weight_collab * (score / max_collab)

            # Normaliser et ajouter les scores content-based
            if content_recs:
                max_content = max(score for _, score in content_recs)
                for article_id, score in content_recs:
                    if article_id in combined_scores:
                        combined_scores[article_id] += weight_content * (score / max_content)
                    else:
                        combined_scores[article_id] = weight_content * (score / max_content)

            # Normaliser et ajouter les scores de tendance
            if trend_recs:
                max_trend = max(score for _, score in trend_recs)
                for article_id, score in trend_recs:
                    if article_id in combined_scores:
                        combined_scores[article_id] += weight_trend * (score / max_trend)
                    else:
                        combined_scores[article_id] = weight_trend * (score / max_trend)

            # Trier par score combiné
            candidate_articles = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)

        # Appliquer le filtre de diversité
        if use_diversity:
            final_articles = self._diversity_filtering(candidate_articles, n_final=n_recommendations)
        else:
            final_articles = candidate_articles[:n_recommendations]

        # Formater les résultats
        recommendations = []
        for article_id, score in final_articles:
            article_info = self.metadata[self.metadata['article_id'] == article_id]
            if not article_info.empty:
                rec = {
                    'article_id': int(article_id),
                    'score': float(score),
                    'category_id': int(article_info.iloc[0]['category_id']),
                    'publisher_id': int(article_info.iloc[0]['publisher_id']),
                    'words_count': int(article_info.iloc[0]['words_count']),
                    'created_at_ts': int(article_info.iloc[0]['created_at_ts'])
                }
                recommendations.append(rec)

        logger.info(f"✓ {len(recommendations)} recommandations générées")

        return recommendations
