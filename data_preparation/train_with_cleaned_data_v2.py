"""
Entraînement du modèle avec données nettoyées V2
(Gestion des sessions + plafonnement)
"""

import pandas as pd
import numpy as np
import json
from pathlib import Path
from scipy.sparse import csr_matrix
from sklearn.metrics.pairwise import cosine_similarity
from tqdm import tqdm

def train_with_cleaned_data_v2():
    """
    Entraîne le modèle avec les données nettoyées V2
    """

    print("=" * 80)
    print("ENTRAÎNEMENT DU MODÈLE AVEC DONNÉES NETTOYÉES V2")
    print("=" * 80)

    base_dir = Path(__file__).parent.parent
    models_dir = base_dir / "models"

    # 1. Charger les statistiques nettoyées V2
    print("\n1. Chargement des données nettoyées V2...")
    interactions = pd.read_csv(models_dir / "interaction_stats_cleaned_v2.csv")
    articles = pd.read_csv(models_dir / "articles_metadata.csv")

    print(f"   - {len(interactions):,} interactions")
    print(f"   - {interactions['user_id'].nunique():,} utilisateurs uniques")
    print(f"   - {interactions['article_id'].nunique():,} articles uniques")

    # 2. Calculer les poids d'interaction
    print("\n2. Calcul des poids d'interaction...")

    # Normaliser le nombre de clics (0-1)
    interactions['clicks_norm'] = interactions['num_clicks'] / interactions['num_clicks'].max()

    # Normaliser le temps passé (0-1)
    interactions['time_norm'] = interactions['total_time_seconds'] / interactions['total_time_seconds'].max()

    # Poids final: 50% clics + 50% temps
    interactions['interaction_weight'] = (
        0.5 * interactions['clicks_norm'] +
        0.5 * interactions['time_norm']
    )

    print(f"   - Poids moyen: {interactions['interaction_weight'].mean():.4f}")
    print(f"   - Poids médian: {interactions['interaction_weight'].median():.4f}")

    # 3. Créer la matrice user-item
    print("\n3. Création de la matrice user-item...")

    # Mapper les IDs
    user_ids = interactions['user_id'].unique()
    article_ids = interactions['article_id'].unique()

    user_to_idx = {uid: idx for idx, uid in enumerate(user_ids)}
    article_to_idx = {aid: idx for idx, aid in enumerate(article_ids)}

    # Créer la matrice sparse
    rows = interactions['user_id'].map(user_to_idx)
    cols = interactions['article_id'].map(article_to_idx)
    data = interactions['interaction_weight']

    user_item_matrix = csr_matrix(
        (data, (rows, cols)),
        shape=(len(user_ids), len(article_ids))
    )

    print(f"   - Matrice: {user_item_matrix.shape}")
    print(f"   - Densité: {user_item_matrix.nnz / (user_item_matrix.shape[0] * user_item_matrix.shape[1]) * 100:.4f}%")

    # 4. Calculer la similarité item-item
    print("\n4. Calcul de la similarité item-item...")
    print("   (Cela peut prendre quelques minutes...)")

    item_similarity = cosine_similarity(user_item_matrix.T, dense_output=False)

    print(f"   ✅ Similarité calculée: {item_similarity.shape}")

    # 5. Créer les profils utilisateur
    print("\n5. Création des profils utilisateur...")

    user_profiles = {}

    for user_id in tqdm(user_ids, desc="Profils"):
        user_interactions = interactions[interactions['user_id'] == user_id]

        user_profiles[int(user_id)] = {
            'num_articles': len(user_interactions),
            'total_time': float(user_interactions['total_time_seconds'].sum()),
            'avg_time': float(user_interactions['total_time_seconds'].mean()),
            'total_clicks': int(user_interactions['num_clicks'].sum()),
            'articles': user_interactions['article_id'].tolist(),
            'weights': user_interactions['interaction_weight'].tolist()
        }

    print(f"   - {len(user_profiles):,} profils créés")

    # 6. Sauvegarder les modèles
    print("\n6. Sauvegarde des modèles...")

    # Sauvegarder la matrice
    from scipy.sparse import save_npz
    matrix_file = models_dir / "user_item_matrix_cleaned_v2.npz"
    save_npz(matrix_file, user_item_matrix)
    print(f"   ✅ Matrice sauvegardée: {matrix_file}")

    # Sauvegarder la similarité
    similarity_file = models_dir / "item_similarity_cleaned_v2.npz"
    save_npz(similarity_file, item_similarity)
    print(f"   ✅ Similarité sauvegardée: {similarity_file}")

    # Sauvegarder les profils
    profiles_file = models_dir / "user_profiles_cleaned_v2.json"
    with open(profiles_file, 'w') as f:
        json.dump(user_profiles, f)
    print(f"   ✅ Profils sauvegardés: {profiles_file}")

    # Sauvegarder les mappings
    mappings = {
        'user_to_idx': {str(k): v for k, v in user_to_idx.items()},
        'article_to_idx': {str(k): v for k, v in article_to_idx.items()},
        'idx_to_user': {v: int(k) for k, v in user_to_idx.items()},
        'idx_to_article': {v: int(k) for k, v in article_to_idx.items()}
    }

    mappings_file = models_dir / "mappings_cleaned_v2.json"
    with open(mappings_file, 'w') as f:
        json.dump(mappings, f)
    print(f"   ✅ Mappings sauvegardés: {mappings_file}")

    # 7. Créer le rapport
    report = {
        'num_users': len(user_ids),
        'num_articles': len(article_ids),
        'num_interactions': len(interactions),
        'matrix_shape': list(user_item_matrix.shape),
        'matrix_density_pct': float(user_item_matrix.nnz / (user_item_matrix.shape[0] * user_item_matrix.shape[1]) * 100),
        'avg_weight': float(interactions['interaction_weight'].mean()),
        'median_weight': float(interactions['interaction_weight'].median()),
        'files': {
            'matrix': str(matrix_file),
            'similarity': str(similarity_file),
            'profiles': str(profiles_file),
            'mappings': str(mappings_file)
        }
    }

    report_file = base_dir / "evaluation" / "training_report_cleaned_v2.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)

    print(f"\n   ✅ Rapport sauvegardé: {report_file}")

    print("\n" + "=" * 80)
    print("ENTRAÎNEMENT TERMINÉ !")
    print("=" * 80)

    print(f"\n📊 Résumé:")
    print(f"   - Utilisateurs: {len(user_ids):,}")
    print(f"   - Articles: {len(article_ids):,}")
    print(f"   - Interactions: {len(interactions):,}")
    print(f"   - Poids moyen: {interactions['interaction_weight'].mean():.4f}")

    print(f"\n🎯 Prochaine étape: Évaluer le modèle")

    return report

if __name__ == "__main__":
    train_with_cleaned_data_v2()
