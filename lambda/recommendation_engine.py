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

    def __init__(self, models_path: str = "./models"):
        """
        Initialise le moteur de recommandation

        Args:
            models_path: Chemin vers le dossier contenant les modèles
        """
        self.models_path = models_path
        self.user_item_matrix = None
        self.mappings = None
        self.article_popularity = None
        self.user_profiles = None
        self.embeddings = None
        self.metadata = None
        self.loaded = False

    def load_models(self):
        """Charge tous les modèles et données nécessaires"""
        logger.info("Chargement des modèles...")

        try:
            # Charger la matrice user-item
            self.user_item_matrix = load_npz(f"{self.models_path}/user_item_matrix.npz")
            logger.info(f"Matrice user-item chargée: {self.user_item_matrix.shape}")

            # Charger les mappings
            with open(f"{self.models_path}/mappings.pkl", 'rb') as f:
                self.mappings = pickle.load(f)
            logger.info(f"Mappings chargés: {len(self.mappings['user_to_idx'])} users")

            # Charger la popularité
            with open(f"{self.models_path}/article_popularity.pkl", 'rb') as f:
                self.article_popularity = pickle.load(f)
            logger.info(f"Popularité chargée: {len(self.article_popularity)} articles")

            # Charger les profils utilisateurs
            with open(f"{self.models_path}/user_profiles.json", 'r') as f:
                self.user_profiles = json.load(f)
            # Convertir les clés en int
            self.user_profiles = {int(k): v for k, v in self.user_profiles.items()}
            logger.info(f"Profils utilisateurs chargés: {len(self.user_profiles)} users")

            # Charger les embeddings
            with open(f"{self.models_path}/embeddings_filtered.pkl", 'rb') as f:
                self.embeddings = pickle.load(f)
            logger.info(f"Embeddings chargés: {len(self.embeddings)} articles")

            # Charger les métadonnées (on pourrait utiliser pandas mais pour Lambda, on optimise)
            import pandas as pd
            self.metadata = pd.read_csv(f"{self.models_path}/articles_metadata.csv")
            logger.info(f"Métadonnées chargées: {len(self.metadata)} articles")

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

    def _collaborative_filtering(self, user_id: int, n_recommendations: int = 20) -> List[Tuple[int, float]]:
        """
        Recommandations par filtrage collaboratif

        Args:
            user_id: ID de l'utilisateur
            n_recommendations: Nombre de recommandations

        Returns:
            Liste de tuples (article_id, score)
        """
        # Vérifier si l'utilisateur existe dans la matrice
        if user_id not in self.mappings['user_to_idx']:
            logger.info(f"Utilisateur {user_id} inconnu pour collaborative filtering")
            return []

        user_idx = self.mappings['user_to_idx'][user_id]

        # Obtenir le vecteur de l'utilisateur
        user_vector = self.user_item_matrix[user_idx].toarray().flatten()

        # Calculer la similarité avec tous les autres utilisateurs
        similarities = cosine_similarity(
            self.user_item_matrix[user_idx],
            self.user_item_matrix
        ).flatten()

        # Trouver les k utilisateurs les plus similaires (exclure l'utilisateur lui-même)
        k = min(50, self.user_item_matrix.shape[0])
        similar_users_idx = np.argsort(similarities)[-k-1:-1][::-1]

        # Agréger les articles des utilisateurs similaires
        recommended_articles = {}
        for sim_user_idx in similar_users_idx:
            if similarities[sim_user_idx] > 0:
                # Récupérer les articles de cet utilisateur
                sim_user_vector = self.user_item_matrix[sim_user_idx].toarray().flatten()
                for article_idx, count in enumerate(sim_user_vector):
                    if count > 0 and user_vector[article_idx] == 0:  # Pas déjà vu par l'utilisateur
                        article_id = self.mappings['idx_to_article'][article_idx]
                        if article_id not in recommended_articles:
                            recommended_articles[article_id] = 0
                        # Score = similarité * nombre d'interactions
                        recommended_articles[article_id] += similarities[sim_user_idx] * count

        # Trier par score
        sorted_articles = sorted(recommended_articles.items(), key=lambda x: x[1], reverse=True)

        return sorted_articles[:n_recommendations]

    def _content_based_filtering(self, user_id: int, n_recommendations: int = 20) -> List[Tuple[int, float]]:
        """
        Recommandations par filtrage basé sur le contenu

        Args:
            user_id: ID de l'utilisateur
            n_recommendations: Nombre de recommandations

        Returns:
            Liste de tuples (article_id, score)
        """
        # Récupérer l'historique de l'utilisateur
        user_history = self._get_user_history(user_id)

        if not user_history:
            logger.info(f"Pas d'historique pour l'utilisateur {user_id}")
            return []

        # Calculer l'embedding moyen des articles lus
        user_embeddings = []
        for article_id in user_history:
            if article_id in self.embeddings:
                user_embeddings.append(self.embeddings[article_id])

        if not user_embeddings:
            return []

        user_profile_embedding = np.mean(user_embeddings, axis=0)

        # Calculer la similarité avec tous les articles
        article_scores = {}
        for article_id, embedding in self.embeddings.items():
            if article_id not in user_history:  # Ne pas recommander ce qui a déjà été lu
                similarity = 1 - cosine(user_profile_embedding, embedding)
                article_scores[article_id] = similarity

        # Trier par score
        sorted_articles = sorted(article_scores.items(), key=lambda x: x[1], reverse=True)

        return sorted_articles[:n_recommendations]

    def _popularity_based(self, n_recommendations: int = 20, exclude_articles: Optional[List[int]] = None) -> List[Tuple[int, float]]:
        """
        Recommandations basées sur la popularité (pour cold start)

        Args:
            n_recommendations: Nombre de recommandations
            exclude_articles: Articles à exclure

        Returns:
            Liste de tuples (article_id, score)
        """
        exclude_articles = exclude_articles or []

        # Filtrer et trier par popularité
        popular_articles = []
        for article_id, row in self.article_popularity.iterrows():
            if article_id not in exclude_articles:
                popular_articles.append((article_id, row['popularity_score']))

        # Trier par score de popularité
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
                  alpha: float = 0.6, use_diversity: bool = True) -> List[Dict]:
        """
        Génère des recommandations hybrides pour un utilisateur

        Args:
            user_id: ID de l'utilisateur
            n_recommendations: Nombre de recommandations à retourner
            alpha: Poids du collaborative filtering (0-1), 1-alpha pour content-based
            use_diversity: Appliquer le filtre de diversité

        Returns:
            Liste de dictionnaires avec les recommandations
        """
        if not self.loaded:
            raise RuntimeError("Les modèles ne sont pas chargés. Appelez load_models() d'abord.")

        logger.info(f"Génération de {n_recommendations} recommandations pour user {user_id}")

        user_history = self._get_user_history(user_id)
        is_cold_start = len(user_history) == 0

        if is_cold_start:
            logger.info(f"Cold start pour user {user_id}, utilisation de la popularité")
            # Pour un nouvel utilisateur, utiliser la popularité
            candidate_articles = self._popularity_based(n_recommendations=n_recommendations * 3)
        else:
            # Obtenir plus de candidats pour avoir plus de diversité
            n_candidates = n_recommendations * 10  # Au lieu de 20, demander 10x plus

            # Obtenir les recommandations collaborative
            collab_recs = self._collaborative_filtering(user_id, n_recommendations=n_candidates)

            # Obtenir les recommandations content-based
            content_recs = self._content_based_filtering(user_id, n_recommendations=n_candidates)

            # Combiner les scores
            combined_scores = {}

            # Normaliser les scores collaborative
            if collab_recs:
                max_collab = max(score for _, score in collab_recs)
                for article_id, score in collab_recs:
                    combined_scores[article_id] = alpha * (score / max_collab)

            # Normaliser et ajouter les scores content-based
            if content_recs:
                max_content = max(score for _, score in content_recs)
                for article_id, score in content_recs:
                    if article_id in combined_scores:
                        combined_scores[article_id] += (1 - alpha) * (score / max_content)
                    else:
                        combined_scores[article_id] = (1 - alpha) * (score / max_content)

            # Si pas assez de recommandations, ajouter des articles populaires
            if len(combined_scores) < n_recommendations * 2:
                pop_recs = self._popularity_based(n_recommendations=20, exclude_articles=user_history)
                for article_id, score in pop_recs:
                    if article_id not in combined_scores:
                        combined_scores[article_id] = 0.5 * score  # Poids plus faible

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
