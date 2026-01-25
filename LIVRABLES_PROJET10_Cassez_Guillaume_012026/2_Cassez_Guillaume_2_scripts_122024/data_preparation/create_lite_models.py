#!/usr/bin/env python3
"""
Création de modèles LITE (10k users) pour Azure Functions Consumption Plan
Sélection ÉQUILIBRÉE par niveau d'activité
"""

import pickle
import json
import pandas as pd
import numpy as np
from scipy.sparse import load_npz, save_npz
from pathlib import Path
import gc

print("=" * 80)
print("CRÉATION MODÈLES LITE - 10k USERS ÉQUILIBRÉS")
print("=" * 80)
print()

# Chemins
MODELS_DIR = Path("/home/ser/Bureau/P10_reco_new/models")
LITE_DIR = Path("/home/ser/Bureau/P10_reco_new/models_lite")
LITE_DIR.mkdir(exist_ok=True)

# Configuration
TARGET_USERS = 10_000

# 1. Charger les profils utilisateurs enrichis
print("1. Chargement des profils utilisateurs enrichis...")
with open(MODELS_DIR / "user_profiles_enriched.pkl", 'rb') as f:
    user_profiles = pickle.load(f)

print(f"   Total users: {len(user_profiles):,}")

# 2. Analyser la distribution d'activité
print("\n2. Analyse de la distribution d'activité...")
activity_levels = []
for user_id, profile in user_profiles.items():
    n_articles = profile.get('num_articles', 0)
    activity_levels.append({
        'user_id': user_id,
        'num_articles': n_articles,
        'num_interactions': profile.get('num_interactions', 0)
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
print("4. Filtrage des profils utilisateurs...")
lite_profiles = {uid: profile for uid, profile in user_profiles.items() if uid in selected_users_set}
print(f"   ✓ {len(lite_profiles):,} profils filtrés")

# Statistiques
total_articles = sum(p['num_articles'] for p in lite_profiles.values())
total_interactions = sum(p['num_interactions'] for p in lite_profiles.values())
print(f"   Articles uniques: {total_articles:,}")
print(f"   Interactions: {total_interactions:,}")
print()

# Sauvegarder
print("   Sauvegarde profils lite...")
with open(LITE_DIR / "user_profiles_enriched.pkl", 'wb') as f:
    pickle.dump(lite_profiles, f)
print(f"   ✓ {(LITE_DIR / 'user_profiles_enriched.pkl').stat().st_size / 1024 / 1024:.1f} MB")

with open(LITE_DIR / "user_profiles_enriched.json", 'w') as f:
    json.dump(lite_profiles, f, indent=2)
print(f"   ✓ {(LITE_DIR / 'user_profiles_enriched.json').stat().st_size / 1024 / 1024:.1f} MB")

del user_profiles
gc.collect()

# 5. Filtrer les matrices user-item
print("\n5. Filtrage des matrices user-item...")

# Charger les mappings
with open(MODELS_DIR / "mappings.pkl", 'rb') as f:
    mappings = pickle.load(f)

user_to_idx = mappings['user_to_idx']
idx_to_user = mappings['idx_to_user']
article_to_idx = mappings['article_to_idx']
idx_to_article = mappings['idx_to_article']

# Créer les nouveaux mappings
lite_user_to_idx = {}
lite_idx_to_user = {}
for new_idx, user_id in enumerate(sorted(selected_users)):
    lite_user_to_idx[user_id] = new_idx
    lite_idx_to_user[new_idx] = user_id

print(f"   Nouveaux mappings: {len(lite_user_to_idx):,} users")

# Filtrer la matrice pondérée
print("   Chargement matrice pondérée...")
weighted_matrix = load_npz(MODELS_DIR / "user_item_matrix_weighted.npz")
print(f"   Shape originale: {weighted_matrix.shape}")

# Sélectionner les lignes (users)
old_user_indices = [user_to_idx[uid] for uid in selected_users if uid in user_to_idx]
lite_weighted = weighted_matrix[old_user_indices, :]

# Supprimer les colonnes (articles) sans interactions
article_mask = np.array(lite_weighted.sum(axis=0) > 0).flatten()
lite_weighted = lite_weighted[:, article_mask]

print(f"   Shape filtrée: {lite_weighted.shape}")
print(f"   Sparsité: {lite_weighted.nnz / (lite_weighted.shape[0] * lite_weighted.shape[1]) * 100:.2f}%")

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
save_npz(LITE_DIR / "user_item_matrix_weighted.npz", lite_weighted)
print(f"   ✓ {(LITE_DIR / 'user_item_matrix_weighted.npz').stat().st_size / 1024 / 1024:.1f} MB")

del weighted_matrix
gc.collect()

# Matrice counts (si elle existe)
try:
    print("\n   Chargement matrice counts...")
    counts_matrix = load_npz(MODELS_DIR / "user_item_matrix.npz")
    lite_counts = counts_matrix[old_user_indices, :][:, article_mask]
    save_npz(LITE_DIR / "user_item_matrix.npz", lite_counts)
    print(f"   ✓ {(LITE_DIR / 'user_item_matrix.npz').stat().st_size / 1024 / 1024:.1f} MB")
    del counts_matrix, lite_counts
    gc.collect()
except FileNotFoundError:
    print("   (Matrice counts non trouvée, ignorée)")

# 6. Sauvegarder les nouveaux mappings
print("\n6. Sauvegarde des nouveaux mappings...")
lite_mappings = {
    'user_to_idx': lite_user_to_idx,
    'idx_to_user': lite_idx_to_user,
    'article_to_idx': lite_article_to_idx,
    'idx_to_article': lite_idx_to_article
}
with open(LITE_DIR / "mappings.pkl", 'wb') as f:
    pickle.dump(lite_mappings, f)
print(f"   ✓ {(LITE_DIR / 'mappings.pkl').stat().st_size / 1024 / 1024:.1f} MB")

# 7. Filtrer les embeddings
print("\n7. Filtrage des embeddings...")
with open(MODELS_DIR / "embeddings_filtered.pkl", 'rb') as f:
    embeddings = pickle.load(f)

lite_embeddings = {aid: emb for aid, emb in embeddings.items() if aid in lite_article_to_idx}
print(f"   {len(lite_embeddings):,} embeddings conservés (sur {len(embeddings):,})")

with open(LITE_DIR / "embeddings_filtered.pkl", 'wb') as f:
    pickle.dump(lite_embeddings, f)
print(f"   ✓ {(LITE_DIR / 'embeddings_filtered.pkl').stat().st_size / 1024 / 1024:.1f} MB")

del embeddings, lite_embeddings
gc.collect()

# 8. Filtrer la popularité
print("\n8. Filtrage de la popularité...")
with open(MODELS_DIR / "article_popularity.pkl", 'rb') as f:
    popularity = pickle.load(f)

lite_popularity = {aid: pop for aid, pop in popularity.items() if aid in lite_article_to_idx}
print(f"   {len(lite_popularity):,} articles conservés")

with open(LITE_DIR / "article_popularity.pkl", 'wb') as f:
    pickle.dump(lite_popularity, f)
print(f"   ✓ {(LITE_DIR / 'article_popularity.pkl').stat().st_size / 1024 / 1024:.1f} MB")

del popularity, lite_popularity
gc.collect()

# 9. Filtrer les métadonnées
print("\n9. Filtrage des métadonnées...")
metadata = pd.read_csv(MODELS_DIR / "articles_metadata.csv")
print(f"   Articles originaux: {len(metadata):,}")

lite_metadata = metadata[metadata['article_id'].isin(lite_article_to_idx.keys())].copy()
print(f"   Articles conservés: {len(lite_metadata):,}")

lite_metadata.to_csv(LITE_DIR / "articles_metadata.csv", index=False)
print(f"   ✓ {(LITE_DIR / 'articles_metadata.csv').stat().st_size / 1024 / 1024:.1f} MB")

# 10. Calculer la taille totale
print("\n" + "=" * 80)
print("RÉSUMÉ")
print("=" * 80)

total_size = 0
files = [
    "user_profiles_enriched.pkl",
    "user_profiles_enriched.json",
    "user_item_matrix_weighted.npz",
    "user_item_matrix.npz",
    "mappings.pkl",
    "embeddings_filtered.pkl",
    "article_popularity.pkl",
    "articles_metadata.csv"
]

print("\nFichiers créés:")
for fname in files:
    fpath = LITE_DIR / fname
    if fpath.exists():
        size_mb = fpath.stat().st_size / 1024 / 1024
        total_size += size_mb
        print(f"  {fname:35s} : {size_mb:6.1f} MB")

print(f"\n{'TOTAL':>35s} : {total_size:6.1f} MB")
print()

# Comparer avec l'original
original_size = sum((MODELS_DIR / f).stat().st_size for f in files if (MODELS_DIR / f).exists()) / 1024 / 1024
reduction_pct = (1 - total_size / original_size) * 100

print(f"Taille originale : {original_size:.1f} MB")
print(f"Taille lite      : {total_size:.1f} MB")
print(f"Réduction        : {reduction_pct:.1f}%")
print()

print("Statistiques Lite:")
print(f"  Users            : {len(lite_user_to_idx):,}")
print(f"  Articles         : {len(lite_article_to_idx):,}")
print(f"  Interactions     : {lite_weighted.nnz:,}")
print(f"  Densité matrice  : {lite_weighted.nnz / (lite_weighted.shape[0] * lite_weighted.shape[1]) * 100:.3f}%")
print()

print("=" * 80)
print("✅ MODÈLES LITE CRÉÉS AVEC SUCCÈS")
print("=" * 80)
print(f"\nRépertoire: {LITE_DIR}")
print(f"\nPrêt pour upload sur Azure Functions Consumption Plan")
print()
