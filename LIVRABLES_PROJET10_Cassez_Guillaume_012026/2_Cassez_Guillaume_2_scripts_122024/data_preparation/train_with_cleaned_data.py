"""
Entraînement du modèle de recommandation avec les données nettoyées
Utilise interaction_stats_cleaned.csv au lieu des données brutes
"""

import pandas as pd
import numpy as np
from pathlib import Path
from scipy.sparse import csr_matrix
from sklearn.preprocessing import normalize
import json
from datetime import datetime

def train_recommendation_model():
    """
    Entraîne le modèle de recommandation avec les données nettoyées
    """

    print("=" * 80)
    print("ENTRAÎNEMENT DU MODÈLE AVEC DONNÉES NETTOYÉES")
    print("=" * 80)

    base_dir = Path(__file__).parent.parent
    models_dir = base_dir / "models"

    # 1. Charger les données nettoyées
    print("\n1. Chargement des données nettoyées...")
    interactions = pd.read_csv(models_dir / "interaction_stats_cleaned.csv")
    articles = pd.read_csv(models_dir / "articles_metadata.csv")

    print(f"   - {len(interactions):,} interactions")
    print(f"   - {len(articles):,} articles")
    print(f"   - {interactions['user_id'].nunique():,} utilisateurs uniques")

    # 2. Créer les poids d'interaction
    print("\n2. Calcul des poids d'interaction...")

    # Normaliser le nombre de clics
    interactions['clicks_norm'] = interactions['num_clicks'] / interactions['num_clicks'].max()

    # Normaliser le temps passé
    interactions['time_norm'] = interactions['total_time_seconds'] / interactions['total_time_seconds'].max()

    # Calculer le poids final (50% clics + 50% temps)
    interactions['interaction_weight'] = (
        0.5 * interactions['clicks_norm'] +
        0.5 * interactions['time_norm']
    )

    print(f"   - Poids moyen: {interactions['interaction_weight'].mean():.4f}")
    print(f"   - Poids médian: {interactions['interaction_weight'].median():.4f}")

    # 3. Créer la matrice user-item
    print("\n3. Création de la matrice utilisateur-article...")

    # Mapper les IDs aux indices
    unique_users = interactions['user_id'].unique()
    unique_articles = interactions['article_id'].unique()

    user_to_idx = {user_id: idx for idx, user_id in enumerate(unique_users)}
    article_to_idx = {article_id: idx for idx, article_id in enumerate(unique_articles)}

    # Créer la matrice sparse
    row_indices = interactions['user_id'].map(user_to_idx)
    col_indices = interactions['article_id'].map(article_to_idx)
    weights = interactions['interaction_weight'].values

    user_item_matrix = csr_matrix(
        (weights, (row_indices, col_indices)),
        shape=(len(unique_users), len(unique_articles))
    )

    print(f"   - Forme de la matrice: {user_item_matrix.shape}")
    print(f"   - Densité: {user_item_matrix.nnz / (user_item_matrix.shape[0] * user_item_matrix.shape[1]) * 100:.4f}%")

    # 4. Normaliser la matrice
    print("\n4. Normalisation de la matrice...")
    user_item_matrix_normalized = normalize(user_item_matrix, norm='l2', axis=1)

    # 5. Calculer la similarité item-item (pour filtrage collaboratif)
    print("\n5. Calcul de la similarité article-article...")
    item_item_similarity = user_item_matrix_normalized.T @ user_item_matrix_normalized

    print(f"   - Forme de la matrice de similarité: {item_item_similarity.shape}")
    print(f"   - Similarité moyenne: {item_item_similarity.mean():.4f}")

    # 6. Créer les profils utilisateurs
    print("\n6. Création des profils utilisateurs...")

    # Pour chaque utilisateur, agréger les catégories des articles lus
    user_profiles = {}

    # Merger interactions avec catégories
    interactions_with_cat = interactions.merge(
        articles[['article_id', 'category_id']],
        on='article_id',
        how='left'
    )

    for user_id in unique_users:
        user_data = interactions_with_cat[interactions_with_cat['user_id'] == user_id]

        # Calculer les préférences de catégories (pondérées par interaction_weight)
        category_weights = user_data.groupby('category_id')['interaction_weight'].sum()
        category_prefs = (category_weights / category_weights.sum()).to_dict()

        # Calculer les stats
        total_time = user_data['total_time_seconds'].sum()
        num_articles = len(user_data)
        avg_time = user_data['total_time_seconds'].mean()

        user_profiles[str(user_id)] = {
            'category_preferences': category_prefs,
            'total_time_seconds': float(total_time),
            'num_articles_read': int(num_articles),
            'avg_time_per_article': float(avg_time)
        }

    print(f"   - {len(user_profiles):,} profils créés")

    # 7. Sauvegarder les modèles
    print("\n7. Sauvegarde des modèles...")

    # Sauvegarder les profils utilisateurs
    profiles_file = models_dir / "user_profiles_cleaned.json"
    with open(profiles_file, 'w') as f:
        json.dump(user_profiles, f, indent=2)
    print(f"   ✅ Profils sauvegardés: {profiles_file}")

    # Sauvegarder les mappings
    mappings = {
        'user_to_idx': {str(k): int(v) for k, v in user_to_idx.items()},
        'article_to_idx': {str(k): int(v) for k, v in article_to_idx.items()},
        'idx_to_user': {int(v): str(k) for k, v in user_to_idx.items()},
        'idx_to_article': {int(v): str(k) for k, v in article_to_idx.items()}
    }

    mappings_file = models_dir / "id_mappings_cleaned.json"
    with open(mappings_file, 'w') as f:
        json.dump(mappings, f, indent=2)
    print(f"   ✅ Mappings sauvegardés: {mappings_file}")

    # Sauvegarder la matrice (format npz pour sparse matrix)
    import scipy.sparse as sp
    matrix_file = models_dir / "user_item_matrix_cleaned.npz"
    sp.save_npz(matrix_file, user_item_matrix_normalized)
    print(f"   ✅ Matrice sauvegardée: {matrix_file}")

    # Sauvegarder la similarité item-item
    similarity_file = models_dir / "item_similarity_cleaned.npz"
    sp.save_npz(similarity_file, item_item_similarity)
    print(f"   ✅ Similarité sauvegardée: {similarity_file}")

    # 8. Créer le rapport d'entraînement
    print("\n8. Création du rapport d'entraînement...")

    report = {
        'timestamp': datetime.now().isoformat(),
        'data_source': 'interaction_stats_cleaned.csv',
        'num_users': len(unique_users),
        'num_articles': len(unique_articles),
        'num_interactions': len(interactions),
        'matrix_shape': list(user_item_matrix.shape),
        'matrix_density': float(user_item_matrix.nnz / (user_item_matrix.shape[0] * user_item_matrix.shape[1]) * 100),
        'weight_stats': {
            'mean': float(interactions['interaction_weight'].mean()),
            'median': float(interactions['interaction_weight'].median()),
            'std': float(interactions['interaction_weight'].std())
        },
        'time_stats': {
            'mean_seconds': float(interactions['total_time_seconds'].mean()),
            'median_seconds': float(interactions['total_time_seconds'].median()),
            'mean_minutes': float(interactions['total_time_seconds'].mean() / 60),
            'median_minutes': float(interactions['total_time_seconds'].median() / 60)
        },
        'files': {
            'user_profiles': str(profiles_file),
            'id_mappings': str(mappings_file),
            'user_item_matrix': str(matrix_file),
            'item_similarity': str(similarity_file)
        }
    }

    report_file = base_dir / "evaluation" / "training_report_cleaned.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)

    print(f"   ✅ Rapport sauvegardé: {report_file}")

    print("\n" + "=" * 80)
    print("ENTRAÎNEMENT TERMINÉ !")
    print("=" * 80)

    print(f"\n📊 Résumé:")
    print(f"   - Utilisateurs: {len(unique_users):,}")
    print(f"   - Articles: {len(unique_articles):,}")
    print(f"   - Interactions: {len(interactions):,}")
    print(f"   - Temps moyen: {interactions['total_time_seconds'].mean() / 60:.2f} min")
    print(f"   - Poids moyen: {interactions['interaction_weight'].mean():.4f}")

    print(f"\n🎯 Prochaine étape: Recalculer les métriques d'évaluation")

    return report

if __name__ == "__main__":
    train_recommendation_model()
