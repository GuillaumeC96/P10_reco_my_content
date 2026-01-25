"""
Script d'optimisation amélioré avec masking des profils utilisateurs
Résout le problème des métriques à 0 en créant des profils train/test séparés
"""

import sys
sys.path.append('../lambda')

import numpy as np
import pandas as pd
import pickle
import json
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from recommendation_engine import RecommendationEngine
import logging
from itertools import product
from tqdm import tqdm
import copy

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ImprovedRecommendationEvaluator:
    """Classe améliorée pour évaluer les performances du système de recommandation"""

    def __init__(self, models_path: str = "../models"):
        self.models_path = models_path
        self.engine = None
        self.original_user_profiles = None
        self.train_interactions = None
        self.val_interactions = None
        self.user_reference_timestamps = {}  # Date de référence (dernier article train) par utilisateur

    def load_engine(self):
        """Charge le moteur de recommandation"""
        logger.info("Chargement du moteur de recommandation...")
        self.engine = RecommendationEngine(models_path=self.models_path)
        self.engine.load_models()

        # Sauvegarder les profils originaux
        self.original_user_profiles = copy.deepcopy(self.engine.user_profiles)

        logger.info("✓ Moteur chargé")

    def create_temporal_split(self, train_ratio: float = 0.8, min_interactions: int = 10):
        """
        Crée un split temporel des interactions

        Args:
            train_ratio: Ratio de données pour le train (0.8 = 80%)
            min_interactions: Nombre minimum d'interactions pour inclure un utilisateur
        """
        logger.info(f"Création du split temporel (train: {train_ratio*100:.0f}%, val: {(1-train_ratio)*100:.0f}%)...")

        train_interactions = {}
        val_interactions = {}
        user_reference_timestamps = {}

        # Pour chaque utilisateur, split ses interactions par temps
        for user_id, profile in tqdm(self.original_user_profiles.items(), desc="Split des utilisateurs"):
            articles = profile['articles_read']

            if len(articles) < min_interactions:  # Besoin de suffisamment d'interactions
                continue

            # Split temporel : les articles sont déjà triés chronologiquement
            split_idx = int(len(articles) * train_ratio)

            # S'assurer qu'on a au moins 1 article dans chaque split
            if split_idx > 0 and split_idx < len(articles):
                train_interactions[user_id] = articles[:split_idx]
                val_interactions[user_id] = articles[split_idx:]

                # Calculer la date de référence = timestamp du dernier article train
                last_train_article_id = articles[split_idx - 1]
                if last_train_article_id in self.engine.article_timestamps:
                    user_reference_timestamps[user_id] = self.engine.article_timestamps[last_train_article_id]

        self.train_interactions = train_interactions
        self.val_interactions = val_interactions
        self.user_reference_timestamps = user_reference_timestamps

        logger.info(f"✓ Split créé: {len(train_interactions)} utilisateurs")
        logger.info(f"  - Train: {sum(len(v) for v in train_interactions.values())} interactions")
        logger.info(f"  - Val: {sum(len(v) for v in val_interactions.values())} interactions")

        return train_interactions, val_interactions

    def _mask_user_profile(self, user_id: int):
        """
        Remplace temporairement le profil utilisateur par le profil train uniquement

        Args:
            user_id: ID de l'utilisateur
        """
        if user_id in self.train_interactions:
            self.engine.user_profiles[user_id] = {
                'articles_read': self.train_interactions[user_id]
            }

    def _restore_user_profile(self, user_id: int):
        """
        Restaure le profil utilisateur original

        Args:
            user_id: ID de l'utilisateur
        """
        if user_id in self.original_user_profiles:
            self.engine.user_profiles[user_id] = self.original_user_profiles[user_id]

    def precision_at_k(self, recommended: List[int], relevant: List[int], k: int) -> float:
        """Calcule Precision@K"""
        if k == 0 or len(recommended) == 0:
            return 0.0

        recommended_at_k = recommended[:k]
        relevant_set = set(relevant)

        hits = len([article for article in recommended_at_k if article in relevant_set])

        return hits / k

    def recall_at_k(self, recommended: List[int], relevant: List[int], k: int) -> float:
        """Calcule Recall@K"""
        if len(relevant) == 0:
            return 0.0

        recommended_at_k = recommended[:k]
        relevant_set = set(relevant)

        hits = len([article for article in recommended_at_k if article in relevant_set])

        return hits / len(relevant)

    def ndcg_at_k(self, recommended: List[int], relevant: List[int], k: int) -> float:
        """Calcule NDCG@K (Normalized Discounted Cumulative Gain)"""
        if len(relevant) == 0:
            return 0.0

        recommended_at_k = recommended[:k]
        relevant_set = set(relevant)

        # DCG
        dcg = 0.0
        for i, article in enumerate(recommended_at_k):
            if article in relevant_set:
                dcg += 1.0 / np.log2(i + 2)

        # IDCG (DCG idéal)
        idcg = sum(1.0 / np.log2(i + 2) for i in range(min(k, len(relevant))))

        if idcg == 0:
            return 0.0

        return dcg / idcg

    def mrr(self, recommended: List[int], relevant: List[int]) -> float:
        """
        Calcule MRR (Mean Reciprocal Rank)
        Mesure à quelle position apparaît le premier article pertinent
        """
        relevant_set = set(relevant)

        for i, article in enumerate(recommended):
            if article in relevant_set:
                return 1.0 / (i + 1)

        return 0.0

    def diversity_score(self, recommended_articles: List[int]) -> float:
        """
        Calcule un score de diversité basé sur les catégories

        Returns:
            Score entre 0 et 1 (1 = très diversifié)
        """
        if len(recommended_articles) == 0:
            return 0.0

        categories = []
        for article_id in recommended_articles:
            article_info = self.engine.metadata[self.engine.metadata['article_id'] == article_id]
            if not article_info.empty:
                categories.append(article_info.iloc[0]['category_id'])

        if len(categories) == 0:
            return 0.0

        # Diversité = nombre de catégories uniques / nombre total d'articles
        return len(set(categories)) / len(categories)

    def novelty_score(self, recommended_articles: List[int], user_id: int) -> float:
        """
        Calcule un score de nouveauté (articles peu populaires)

        Returns:
            Score moyen de nouveauté (popularité inversée, normalisée)
        """
        if len(recommended_articles) == 0:
            return 0.0

        novelty_scores = []
        max_popularity = self.engine.article_popularity['popularity_score'].max()

        for article_id in recommended_articles:
            if article_id in self.engine.article_popularity.index:
                popularity = self.engine.article_popularity.loc[article_id, 'popularity_score']
                # Nouveauté = 1 - popularité normalisée
                novelty = 1.0 - (popularity / max_popularity)
                novelty_scores.append(novelty)

        if len(novelty_scores) == 0:
            return 0.0

        return np.mean(novelty_scores)

    def gini_coefficient(self, all_recommendations: List[List[int]]) -> float:
        """
        Calcule le coefficient de Gini pour mesurer la bulle de filtre

        Le coefficient de Gini mesure l'inégalité de distribution des articles recommandés:
        - 0 = parfaitement équilibré (tous les articles recommandés autant)
        - 1 = inégalité extrême (bulle de filtre, seuls quelques articles dominent)

        Args:
            all_recommendations: Liste de listes d'articles recommandés par utilisateur

        Returns:
            Coefficient de Gini entre 0 et 1

        Note:
            State-of-Art: Gini < 0.5 est acceptable, < 0.3 est bon
            Paper: "Filter Bubbles in Recommender Systems: Fact or Fallacy" (2024)
        """
        if len(all_recommendations) == 0:
            return 0.0

        # Compter la fréquence de chaque article recommandé
        from collections import Counter
        article_counts = Counter()
        for recs in all_recommendations:
            article_counts.update(recs)

        if len(article_counts) == 0:
            return 0.0

        # Trier les comptages
        counts = np.array(sorted(article_counts.values()))
        n = len(counts)

        if n == 0 or counts.sum() == 0:
            return 0.0

        # Calcul du coefficient de Gini
        # Formule: G = (2 * sum(i * x_i)) / (n * sum(x_i)) - (n + 1) / n
        index = np.arange(1, n + 1)
        gini = (2 * np.sum(index * counts)) / (n * np.sum(counts)) - (n + 1) / n

        return float(gini)

    def intra_user_diversity(self, recommended_articles: List[int]) -> float:
        """
        Calcule la diversité intra-utilisateur (variété du contenu pour un seul utilisateur)

        Mesure la variété thématique et temporelle dans les recommandations d'un utilisateur.
        Plus haute = recommandations plus variées (évite la bulle de filtre)

        Args:
            recommended_articles: Liste d'articles recommandés pour un utilisateur

        Returns:
            Score de diversité entre 0 et 1 (1 = très diversifié)

        Note:
            State-of-Art: > 0.6 est bon pour news recommendation
            Combine diversité de catégories ET de publishers
        """
        if len(recommended_articles) <= 1:
            return 0.0

        categories = []
        publishers = []

        for article_id in recommended_articles:
            article_info = self.engine.metadata[self.engine.metadata['article_id'] == article_id]
            if not article_info.empty:
                categories.append(article_info.iloc[0]['category_id'])
                publishers.append(article_info.iloc[0]['publisher_id'])

        if len(categories) == 0:
            return 0.0

        # Diversité = moyenne de diversité de catégories et de publishers
        category_diversity = len(set(categories)) / len(categories)
        publisher_diversity = len(set(publishers)) / len(publishers) if len(publishers) > 0 else 0

        # Moyenne pondérée: catégories plus importantes que publishers
        diversity = 0.7 * category_diversity + 0.3 * publisher_diversity

        return float(diversity)

    def temporal_diversity(self, recommended_articles: List[int]) -> float:
        """
        Calcule la diversité temporelle (équilibre articles récents vs anciens)

        Mesure si les recommandations couvrent bien la fenêtre temporelle:
        - Score élevé = bon équilibre entre articles très récents et moins récents
        - Score bas = tous les articles ont le même âge (manque de diversité temporelle)

        Args:
            recommended_articles: Liste d'articles recommandés

        Returns:
            Score de diversité temporelle entre 0 et 1

        Note:
            State-of-Art: Variance normalisée de l'âge des articles
            Pour news: diversité temporelle évite de recommander que du "breaking news"
        """
        if len(recommended_articles) <= 1:
            return 0.0

        import time
        now_ts = int(time.time() * 1000)

        ages_days = []
        for article_id in recommended_articles:
            if article_id in self.engine.article_timestamps:
                created_ts = self.engine.article_timestamps[article_id]
                age_ms = now_ts - created_ts
                age_days = age_ms / (86400 * 1000)
                ages_days.append(age_days)

        if len(ages_days) <= 1:
            return 0.0

        # Diversité = coefficient de variation normalisé
        # Plus l'écart-type est élevé par rapport à la moyenne, plus c'est diversifié
        ages_array = np.array(ages_days)
        mean_age = np.mean(ages_array)
        std_age = np.std(ages_array)

        if mean_age == 0:
            return 0.0

        # Coefficient de variation normalisé entre 0 et 1
        # Plafonner à 1 pour éviter valeurs > 1
        cv = min(std_age / mean_age, 1.0)

        return float(cv)

    def evaluate_user(self, user_id: int, weight_collab: float, weight_content: float,
                      weight_trend: float, k: int = 10, max_article_age_days: Optional[float] = None) -> Dict[str, float]:
        """
        Évalue les recommandations pour un utilisateur avec masking du profil

        Args:
            user_id: ID de l'utilisateur
            weight_collab, weight_content, weight_trend: Poids des approches
            k: Nombre de recommandations à générer

        Returns:
            Dictionnaire avec les métriques
        """
        # Obtenir les articles de validation (ground truth)
        relevant_articles = self.val_interactions.get(user_id, [])

        if len(relevant_articles) == 0:
            return None

        try:
            # IMPORTANT: Masquer le profil utilisateur pour n'utiliser que le train
            self._mask_user_profile(user_id)

            # Obtenir le timestamp de référence pour cet utilisateur (date du dernier article train)
            reference_ts = self.user_reference_timestamps.get(user_id, None)

            # Générer les recommandations avec les poids donnés
            recommendations = self.engine.recommend(
                user_id=user_id,
                n_recommendations=k,
                weight_collab=weight_collab,
                weight_content=weight_content,
                weight_trend=weight_trend,
                use_diversity=False,  # Désactiver pour avoir un ranking pur par score
                reference_timestamp=reference_ts,  # Date de référence pour calcul d'âge des articles
                max_article_age_days=max_article_age_days  # Fenêtre temporelle (optuna hyperparamètre)
            )

            # Restaurer le profil original
            self._restore_user_profile(user_id)

            # Extraire les IDs des articles recommandés
            recommended_articles = [rec['article_id'] for rec in recommendations]

            # Calculer les métriques de performance
            metrics = {
                # Métriques de ranking (accuracy)
                'precision@5': self.precision_at_k(recommended_articles, relevant_articles, 5),
                'precision@10': self.precision_at_k(recommended_articles, relevant_articles, 10),
                'recall@5': self.recall_at_k(recommended_articles, relevant_articles, 5),
                'recall@10': self.recall_at_k(recommended_articles, relevant_articles, 10),
                'ndcg@5': self.ndcg_at_k(recommended_articles, relevant_articles, 5),
                'ndcg@10': self.ndcg_at_k(recommended_articles, relevant_articles, 10),
                'mrr@10': self.mrr(recommended_articles[:10], relevant_articles),  # MRR@10

                # Métriques de diversité (State-of-Art 2024)
                'diversity': self.diversity_score(recommended_articles),  # Diversité catégories (legacy)
                'intra_diversity': self.intra_user_diversity(recommended_articles),  # Diversité intra-user
                'temporal_diversity': self.temporal_diversity(recommended_articles),  # Diversité temporelle

                # Métriques de nouveauté/découverte
                'novelty': self.novelty_score(recommended_articles, user_id),
            }

            return metrics

        except Exception as e:
            logger.warning(f"Erreur pour user {user_id}: {e}")
            # Toujours restaurer le profil en cas d'erreur
            self._restore_user_profile(user_id)
            return None

    def evaluate_weights(self, weight_collab: float, weight_content: float,
                        weight_trend: float, sample_users: int = None) -> Dict[str, float]:
        """
        Évalue une combinaison de poids sur l'ensemble de validation

        Args:
            weight_collab, weight_content, weight_trend: Poids à évaluer
            sample_users: Nombre d'utilisateurs à échantillonner (None = tous)

        Returns:
            Moyennes des métriques sur tous les utilisateurs
        """
        users = list(self.val_interactions.keys())

        if sample_users and sample_users < len(users):
            users = np.random.choice(users, sample_users, replace=False)

        all_metrics = []

        for user_id in users:
            metrics = self.evaluate_user(user_id, weight_collab, weight_content, weight_trend, k=10)
            if metrics:
                all_metrics.append(metrics)

        if len(all_metrics) == 0:
            return None

        # Calculer les moyennes
        avg_metrics = {}
        for key in all_metrics[0].keys():
            avg_metrics[key] = np.mean([m[key] for m in all_metrics])

        avg_metrics['n_users_evaluated'] = len(all_metrics)

        return avg_metrics

    def grid_search(self, weight_ranges: Dict[str, List[float]],
                   sample_users: int = 100, output_file: str = "improved_tuning_results.json"):
        """
        Grid search pour trouver les meilleurs poids

        Args:
            weight_ranges: Dictionnaire avec les valeurs à tester pour chaque poids
            sample_users: Nombre d'utilisateurs à utiliser pour l'évaluation
            output_file: Fichier pour sauvegarder les résultats
        """
        logger.info("Démarrage du Grid Search amélioré...")
        logger.info(f"Ranges: {weight_ranges}")
        logger.info(f"Échantillon: {sample_users} utilisateurs")

        results = []

        # Générer toutes les combinaisons
        combinations = list(product(
            weight_ranges['weight_collab'],
            weight_ranges['weight_content'],
            weight_ranges['weight_trend']
        ))

        logger.info(f"Nombre de combinaisons à tester: {len(combinations)}")

        # Tester chaque combinaison
        for weight_collab, weight_content, weight_trend in tqdm(combinations, desc="Grid Search"):
            logger.info(f"\nTest: collab={weight_collab}, content={weight_content}, trend={weight_trend}")

            metrics = self.evaluate_weights(weight_collab, weight_content, weight_trend, sample_users)

            if metrics:
                result = {
                    'weight_collab': weight_collab,
                    'weight_content': weight_content,
                    'weight_trend': weight_trend,
                    'ratio': f"{weight_collab}:{weight_content}:{weight_trend}",
                    **metrics
                }
                results.append(result)

                logger.info(f"  Precision@5: {metrics['precision@5']:.4f}")
                logger.info(f"  NDCG@5: {metrics['ndcg@5']:.4f}")
                logger.info(f"  Diversity: {metrics['diversity']:.4f}")

        # Sauvegarder les résultats
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)

        logger.info(f"\n✓ Résultats sauvegardés dans {output_file}")

        # Afficher le top 5 par NDCG@5
        logger.info("\n" + "="*70)
        logger.info("TOP 5 configurations par NDCG@5:")
        logger.info("="*70)

        results_sorted = sorted(results, key=lambda x: x['ndcg@5'], reverse=True)

        for i, result in enumerate(results_sorted[:5], 1):
            logger.info(f"\n{i}. Ratio {result['ratio']}")
            logger.info(f"   NDCG@5: {result['ndcg@5']:.4f}")
            logger.info(f"   Precision@5: {result['precision@5']:.4f}")
            logger.info(f"   Recall@5: {result['recall@5']:.4f}")
            logger.info(f"   MRR: {result['mrr']:.4f}")
            logger.info(f"   Diversity: {result['diversity']:.4f}")
            logger.info(f"   Novelty: {result['novelty']:.4f}")

        return results


def main():
    """Fonction principale"""
    # Initialiser l'évaluateur
    evaluator = ImprovedRecommendationEvaluator(models_path="../models")

    # Charger le moteur
    evaluator.load_engine()

    # Créer le split temporel
    evaluator.create_temporal_split(train_ratio=0.8, min_interactions=10)

    # Définir les poids à tester (Grid Search)
    weight_ranges = {
        'weight_collab': [1.0, 2.0, 3.0, 4.0, 5.0],   # Collaborative
        'weight_content': [1.0, 2.0, 3.0, 4.0, 5.0],  # Content-based
        'weight_trend': [0.5, 1.0, 2.0, 3.0],          # Trend (souvent moins important)
    }

    logger.info("\n" + "="*70)
    logger.info("CONFIGURATION DU GRID SEARCH AMÉLIORÉ")
    logger.info("="*70)
    logger.info(f"Plages de poids:")
    logger.info(f"  - Collaborative: 1 à 5")
    logger.info(f"  - Content-based: 1 à 5")
    logger.info(f"  - Trend/Popularity: 0.5 à 3")
    logger.info(f"Total de combinaisons: {len(weight_ranges['weight_collab']) * len(weight_ranges['weight_content']) * len(weight_ranges['weight_trend'])}")
    logger.info(f"Métriques: Precision, Recall, NDCG, MRR, Diversity, Novelty")
    logger.info("="*70 + "\n")

    # Lancer le Grid Search
    results = evaluator.grid_search(
        weight_ranges=weight_ranges,
        sample_users=100,  # Échantillon de 100 utilisateurs pour rapidité
        output_file="improved_tuning_results.json"
    )

    # Créer un DataFrame pour analyse
    df = pd.DataFrame(results)
    df.to_csv("improved_tuning_results.csv", index=False)
    logger.info("\n✓ Résultats aussi sauvegardés en CSV")

    logger.info("\n" + "="*70)
    logger.info("Optimisation terminée !")
    logger.info("="*70)


if __name__ == "__main__":
    main()
