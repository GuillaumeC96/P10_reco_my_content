#!/usr/bin/env python3
"""
Création de modèles LITE V2 (10k users) pour Azure Functions
Utilise les données nettoyées V2 (avec gestion des sessions)
"""

import json
import pandas as pd
import numpy as np
from scipy.sparse import load_npz, save_npz
from pathlib import Path
import gc

print("=" * 80)
print("CRÉATION MODÈLES LITE V2 - 10k USERS ÉQUILIBRÉS")
print("=" * 80)
print()

# Chemins
MODELS_DIR = Path("/home/ser/Bureau/P10_reco_new/models")
LITE_DIR = Path("/home/ser/Bureau/P10_reco_new/models_lite")
LITE_DIR.mkdir(exist_ok=True)

# Configuration
TARGET_USERS = 10_000

# 1. Charger les profils utilisateurs V2
print("1. Chargement des profils utilisateurs V2...")
with open(MODELS_DIR / "user_profiles_cleaned_v2.json", 'r') as f:
    user_profiles = json.load(f)

# Convertir les clés en int
user_profiles = {int(k): v for k, v in user_profiles.items()}

print(f"   Total users: {len(user_profiles):,}")

# 2. Analyser la distribution d'activité
print("\n2. Analyse de la distribution d'activité...")
activity_levels = []
for user_id, profile in user_profiles.items():
    n_articles = profile.get('num_articles', 0)
    activity_levels.append({
        'user_id': user_id,
        'num_articles': n_articles,
        'total_time': profile.get('total_time', 0)
    })

activity_df = pd.DataFrame(activity_levels)

# Définir les strates (quartiles)
quartiles = activity_df['num_articles'].quantile([0.25, 0.5, 0.75, 1.0]).values
print(f"   Distribution d'activité (quartiles):")
print(f"     Q1 (25%): {quartiles[0]:.0f} articles")
print(f"     Q2 (50%): {quartiles[1]:.0f} articles (médiane)")
print(f"     Q3 (75%): {quartiles[2]:.0f} articles")
print(f"     Q4 (100%): {quartiles[3]:.0f} articles (max)")
print()

# Créer les strates
def get_activity_level(n_articles):
    if n_articles <= quartiles[0]:
        return 'low'  # 0-25%
    elif n_articles <= quartiles[1]:
        return 'medium_low'  # 25-50%
    elif n_articles <= quartiles[2]:
        return 'medium_high'  # 50-75%
    else:
        return 'high'  # 75-100%

activity_df['activity_level'] = activity_df['num_articles'].apply(get_activity_level)

print("   Distribution par niveau:")
level_counts = activity_df['activity_level'].value_counts()
for level in ['low', 'medium_low', 'medium_high', 'high']:
    count = level_counts.get(level, 0)
    pct = count / len(activity_df) * 100
    print(f"     {level:12s}: {count:7,} users ({pct:5.1f}%)")
print()

# 3. Échantillonnage stratifié
print(f"3. Sélection équilibrée de {TARGET_USERS:,} utilisateurs...")

# Calculer combien prendre de chaque strate (proportionnel)
selected_users = []
for level in ['low', 'medium_low', 'medium_high', 'high']:
    level_df = activity_df[activity_df['activity_level'] == level]
    pct = len(level_df) / len(activity_df)
    n_to_sample = int(TARGET_USERS * pct)

    # Échantillonner
    if len(level_df) > n_to_sample:
        sampled = level_df.sample(n=n_to_sample, random_state=42)
    else:
        sampled = level_df  # Prendre tous si pas assez

    selected_users.extend(sampled['user_id'].tolist())

    print(f"   {level:12s}: {n_to_sample:5,} users sélectionnés (sur {len(level_df):,})")

# Compléter si nécessaire
if len(selected_users) < TARGET_USERS:
    remaining = TARGET_USERS - len(selected_users)
    available = activity_df[~activity_df['user_id'].isin(selected_users)]
    extra = available.sample(n=remaining, random_state=42)['user_id'].tolist()
    selected_users.extend(extra)
    print(f"   + {remaining:5,} users aléatoires pour atteindre {TARGET_USERS:,}")

selected_users_set = set(selected_users)
print(f"\n   ✓ {len(selected_users):,} utilisateurs sélectionnés")
print()

# 4. Filtrer les profils utilisateurs
print("4. Filtrage des profils utilisateurs V2...")
lite_profiles = {uid: profile for uid, profile in user_profiles.items() if uid in selected_users_set}
print(f"   ✓ {len(lite_profiles):,} profils filtrés")

# Statistiques
total_articles = sum(p['num_articles'] for p in lite_profiles.values())
total_time = sum(p['total_time'] for p in lite_profiles.values())
print(f"   Articles uniques: {total_articles:,}")
print(f"   Temps total: {total_time / 3600:.0f} heures")
print()

# Sauvegarder en JSON (pour Azure)
print("   Sauvegarde profils lite JSON...")
with open(LITE_DIR / "user_profiles_cleaned_v2.json", 'w') as f:
    # Convertir les clés en string pour JSON
    json_profiles = {str(k): v for k, v in lite_profiles.items()}
    json.dump(json_profiles, f)
print(f"   ✓ {(LITE_DIR / 'user_profiles_cleaned_v2.json').stat().st_size / 1024 / 1024:.1f} MB")

del user_profiles
gc.collect()

# 5. Filtrer les matrices user-item
print("\n5. Filtrage des matrices user-item V2...")

# Charger les mappings V2
with open(MODELS_DIR / "mappings_cleaned_v2.json", 'r') as f:
    mappings = json.load(f)

# Convertir les clés en int
user_to_idx = {int(k): v for k, v in mappings['user_to_idx'].items()}
idx_to_user = {int(k): v for k, v in mappings['idx_to_user'].items()}
article_to_idx = {int(k): v for k, v in mappings['article_to_idx'].items()}
idx_to_article = {int(k): v for k, v in mappings['idx_to_article'].items()}

# Créer les nouveaux mappings
lite_user_to_idx = {}
lite_idx_to_user = {}
for new_idx, user_id in enumerate(sorted(selected_users)):
    lite_user_to_idx[user_id] = new_idx
    lite_idx_to_user[new_idx] = user_id

print(f"   Nouveaux mappings: {len(lite_user_to_idx):,} users")

# Filtrer la matrice V2
print("   Chargement matrice user-item V2...")
user_item_matrix = load_npz(MODELS_DIR / "user_item_matrix_cleaned_v2.npz")
print(f"   Shape originale: {user_item_matrix.shape}")

# Sélectionner les lignes (users)
old_user_indices = [user_to_idx[uid] for uid in selected_users if uid in user_to_idx]
lite_matrix = user_item_matrix[old_user_indices, :]

# Supprimer les colonnes (articles) sans interactions
article_mask = np.array(lite_matrix.sum(axis=0) > 0).flatten()
lite_matrix = lite_matrix[:, article_mask]

print(f"   Shape filtrée: {lite_matrix.shape}")
print(f"   Densité: {lite_matrix.nnz / (lite_matrix.shape[0] * lite_matrix.shape[1]) * 100:.4f}%")

# Mettre à jour les mappings d'articles
old_article_indices = np.where(article_mask)[0]
lite_article_to_idx = {}
lite_idx_to_article = {}
for new_idx, old_idx in enumerate(old_article_indices):
    article_id = idx_to_article[old_idx]
    lite_article_to_idx[article_id] = new_idx
    lite_idx_to_article[new_idx] = article_id

print(f"   Articles conservés: {len(lite_article_to_idx):,}")

# Sauvegarder
save_npz(LITE_DIR / "user_item_matrix_cleaned_v2.npz", lite_matrix)
print(f"   ✓ {(LITE_DIR / 'user_item_matrix_cleaned_v2.npz').stat().st_size / 1024 / 1024:.1f} MB")

del user_item_matrix
gc.collect()

# 6. Filtrer la similarité item-item V2
print("\n6. Filtrage de la similarité item-item V2...")
print("   Chargement item_similarity V2...")
item_similarity = load_npz(MODELS_DIR / "item_similarity_cleaned_v2.npz")
print(f"   Shape originale: {item_similarity.shape}")

# Filtrer les lignes et colonnes (articles)
lite_similarity = item_similarity[article_mask, :][:, article_mask]
print(f"   Shape filtrée: {lite_similarity.shape}")

save_npz(LITE_DIR / "item_similarity_cleaned_v2.npz", lite_similarity)
print(f"   ✓ {(LITE_DIR / 'item_similarity_cleaned_v2.npz').stat().st_size / 1024 / 1024:.1f} MB")

del item_similarity, lite_similarity
gc.collect()

# 7. Sauvegarder les nouveaux mappings
print("\n7. Sauvegarde des nouveaux mappings V2...")
lite_mappings = {
    'user_to_idx': {str(k): v for k, v in lite_user_to_idx.items()},
    'idx_to_user': {str(k): int(v) for k, v in lite_idx_to_user.items()},
    'article_to_idx': {str(k): v for k, v in lite_article_to_idx.items()},
    'idx_to_article': {str(k): int(v) for k, v in lite_idx_to_article.items()}
}
with open(LITE_DIR / "mappings_cleaned_v2.json", 'w') as f:
    json.dump(lite_mappings, f)
print(f"   ✓ {(LITE_DIR / 'mappings_cleaned_v2.json').stat().st_size / 1024 / 1024:.1f} MB")

# 8. Filtrer les métadonnées
print("\n8. Filtrage des métadonnées...")
metadata = pd.read_csv(MODELS_DIR / "articles_metadata.csv")
print(f"   Articles originaux: {len(metadata):,}")

lite_metadata = metadata[metadata['article_id'].isin(lite_article_to_idx.keys())].copy()
print(f"   Articles conservés: {len(lite_metadata):,}")

lite_metadata.to_csv(LITE_DIR / "articles_metadata.csv", index=False)
print(f"   ✓ {(LITE_DIR / 'articles_metadata.csv').stat().st_size / 1024 / 1024:.1f} MB")

# 9. Créer la popularité (basée sur les interactions V2)
print("\n9. Calcul de la popularité des articles...")
interactions = pd.read_csv(MODELS_DIR / "interaction_stats_cleaned_v2.csv")
interactions_lite = interactions[
    (interactions['user_id'].isin(selected_users_set)) &
    (interactions['article_id'].isin(lite_article_to_idx.keys()))
]

article_popularity = interactions_lite.groupby('article_id')['num_clicks'].sum().to_dict()
print(f"   {len(article_popularity):,} articles avec popularité")

# Sauvegarder en JSON (pour Azure)
with open(LITE_DIR / "article_popularity.json", 'w') as f:
    json.dump(article_popularity, f)
print(f"   ✓ {(LITE_DIR / 'article_popularity.json').stat().st_size / 1024:.1f} KB")

# 10. Calculer la taille totale
print("\n" + "=" * 80)
print("RÉSUMÉ")
print("=" * 80)

total_size = 0
files = [
    "user_profiles_cleaned_v2.json",
    "user_item_matrix_cleaned_v2.npz",
    "item_similarity_cleaned_v2.npz",
    "mappings_cleaned_v2.json",
    "article_popularity.json",
    "articles_metadata.csv"
]

print("\nFichiers créés:")
for fname in files:
    fpath = LITE_DIR / fname
    if fpath.exists():
        size_mb = fpath.stat().st_size / 1024 / 1024
        total_size += size_mb
        print(f"  {fname:40s} : {size_mb:6.1f} MB")

print(f"\n{'TOTAL':>40s} : {total_size:6.1f} MB")
print()

# Comparer avec l'original
original_files = [
    "user_profiles_cleaned_v2.json",
    "user_item_matrix_cleaned_v2.npz",
    "item_similarity_cleaned_v2.npz",
    "mappings_cleaned_v2.json",
    "articles_metadata.csv"
]
original_size = sum((MODELS_DIR / f).stat().st_size for f in original_files if (MODELS_DIR / f).exists()) / 1024 / 1024
reduction_pct = (1 - total_size / original_size) * 100

print(f"Taille originale : {original_size:.1f} MB")
print(f"Taille lite      : {total_size:.1f} MB")
print(f"Réduction        : {reduction_pct:.1f}%")
print()

print("Statistiques Lite:")
print(f"  Users            : {len(lite_user_to_idx):,}")
print(f"  Articles         : {len(lite_article_to_idx):,}")
print(f"  Interactions     : {lite_matrix.nnz:,}")
print(f"  Densité matrice  : {lite_matrix.nnz / (lite_matrix.shape[0] * lite_matrix.shape[1]) * 100:.3f}%")
print()

print("=" * 80)
print("✅ MODÈLES LITE V2 CRÉÉS AVEC SUCCÈS")
print("=" * 80)
print(f"\nRépertoire: {LITE_DIR}")
print(f"\nPrêt pour upload sur Azure Functions")
print()
