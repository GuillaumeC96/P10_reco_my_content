#!/usr/bin/env python3
"""
Prépare les modèles V2 pour Azure Functions
Convertit les fichiers JSON en pickle et crée les fichiers manquants
"""

import json
import pickle
import pandas as pd
import numpy as np
from scipy.sparse import load_npz, save_npz
from pathlib import Path

print("=" * 80)
print("PRÉPARATION MODÈLES V2 POUR AZURE")
print("=" * 80)
print()

LITE_DIR = Path("/home/ser/Bureau/P10_reco_new/models_lite")
AZURE_DIR = Path("/home/ser/Bureau/P10_reco_new/azure_models_v2")
AZURE_DIR.mkdir(exist_ok=True)
MODELS_DIR = Path("/home/ser/Bureau/P10_reco_new/models")

# 1. Copier les matrices NPZ (renommer pour correspondre aux noms attendus)
print("1. Préparation des matrices...")

# user_item_matrix_cleaned_v2.npz → user_item_matrix.npz
print("   Copie user_item_matrix_cleaned_v2.npz → user_item_matrix.npz")
src = load_npz(LITE_DIR / "user_item_matrix_cleaned_v2.npz")
save_npz(AZURE_DIR / "user_item_matrix.npz", src)
print(f"   ✓ {(AZURE_DIR / 'user_item_matrix.npz').stat().st_size / 1024:.1f} KB")

# Pas de matrice weighted pour V2, utiliser la même matrice
print("   Copie user_item_matrix_cleaned_v2.npz → user_item_matrix_weighted.npz")
save_npz(AZURE_DIR / "user_item_matrix_weighted.npz", src)
print(f"   ✓ {(AZURE_DIR / 'user_item_matrix_weighted.npz').stat().st_size / 1024:.1f} KB")
del src

# 2. Convertir mappings JSON → pickle
print("\n2. Conversion des mappings...")
with open(LITE_DIR / "mappings_cleaned_v2.json", 'r') as f:
    mappings = json.load(f)

# Convertir les clés en int
mappings_pkl = {
    'user_to_idx': {int(k): v for k, v in mappings['user_to_idx'].items()},
    'idx_to_user': {int(k): v for k, v in mappings['idx_to_user'].items()},
    'article_to_idx': {int(k): v for k, v in mappings['article_to_idx'].items()},
    'idx_to_article': {int(k): v for k, v in mappings['idx_to_article'].items()}
}

with open(AZURE_DIR / "mappings.pkl", 'wb') as f:
    pickle.dump(mappings_pkl, f)
print(f"   ✓ {(AZURE_DIR / 'mappings.pkl').stat().st_size / 1024:.1f} KB")

# 3. Convertir popularité JSON → pickle
print("\n3. Conversion de la popularité...")
with open(LITE_DIR / "article_popularity.json", 'r') as f:
    popularity = json.load(f)

# Convertir les clés en int
popularity_pkl = {int(k): v for k, v in popularity.items()}

with open(AZURE_DIR / "article_popularity.pkl", 'wb') as f:
    pickle.dump(popularity_pkl, f)
print(f"   ✓ {(AZURE_DIR / 'article_popularity.pkl').stat().st_size / 1024:.1f} KB")

# 4. Renommer user_profiles JSON
print("\n4. Préparation des profils utilisateurs...")
with open(LITE_DIR / "user_profiles_cleaned_v2.json", 'r') as f:
    profiles = json.load(f)

# Convertir les clés en int et adapter le format
profiles_adapted = {}
for user_id, profile in profiles.items():
    # Adapter le format pour correspondre à ce que attend le Azure Functions
    # V2 profile: {num_articles, total_time, avg_time, total_clicks, articles, weights}
    # Azure Functions attend: {articles_read, ...}

    user_id_int = int(user_id)
    profiles_adapted[user_id_int] = {
        'articles_read': profile.get('articles', []),
        'num_articles': profile.get('num_articles', 0),
        'total_time': profile.get('total_time', 0),
        'avg_time': profile.get('avg_time', 0),
        'total_clicks': profile.get('total_clicks', 0)
    }

# Sauvegarder en JSON
with open(AZURE_DIR / "user_profiles.json", 'w') as f:
    json.dump(profiles_adapted, f)
print(f"   ✓ {(AZURE_DIR / 'user_profiles.json').stat().st_size / 1024 / 1024:.1f} MB")

# Sauvegarder aussi en pickle (pour compatibilité)
with open(AZURE_DIR / "user_profiles_enriched.pkl", 'wb') as f:
    pickle.dump(profiles_adapted, f)
print(f"   ✓ {(AZURE_DIR / 'user_profiles_enriched.pkl').stat().st_size / 1024 / 1024:.1f} MB")

# 5. Copier articles_metadata.csv
print("\n5. Copie des métadonnées...")
import shutil
shutil.copy(LITE_DIR / "articles_metadata.csv", AZURE_DIR / "articles_metadata.csv")
print(f"   ✓ {(AZURE_DIR / 'articles_metadata.csv').stat().st_size / 1024:.1f} KB")

# 6. Créer un fichier embeddings vide (pour éviter les erreurs de chargement)
print("\n6. Création d'embeddings vides...")
# Charger les métadonnées pour avoir la liste d'articles
metadata = pd.read_csv(AZURE_DIR / "articles_metadata.csv")

# Créer des embeddings factices (vecteurs nuls)
# Le Azure Functions peut fonctionner sans embeddings si on ne fait que du collaborative filtering
fake_embeddings = {}
for article_id in metadata['article_id'].values[:100]:  # Seulement 100 pour économiser l'espace
    fake_embeddings[int(article_id)] = np.zeros(768, dtype=np.float32)  # Taille BERT standard

with open(AZURE_DIR / "embeddings_filtered.pkl", 'wb') as f:
    pickle.dump(fake_embeddings, f)
print(f"   ✓ {(AZURE_DIR / 'embeddings_filtered.pkl').stat().st_size / 1024:.1f} KB")
print(f"   ⚠️  Embeddings factices créés (100 articles avec vecteurs nuls)")

# 7. Résumé
print("\n" + "=" * 80)
print("RÉSUMÉ")
print("=" * 80)

files = [
    "user_item_matrix.npz",
    "user_item_matrix_weighted.npz",
    "mappings.pkl",
    "article_popularity.pkl",
    "user_profiles.json",
    "user_profiles_enriched.pkl",
    "articles_metadata.csv",
    "embeddings_filtered.pkl"
]

total_size = 0
print("\nFichiers créés pour Azure:")
for fname in files:
    fpath = AZURE_DIR / fname
    if fpath.exists():
        size_mb = fpath.stat().st_size / 1024 / 1024
        total_size += size_mb
        print(f"  {fname:35s} : {size_mb:6.2f} MB")

print(f"\n{'TOTAL':>35s} : {total_size:6.2f} MB")
print()

print("=" * 80)
print("✅ MODÈLES V2 PRÊTS POUR AZURE")
print("=" * 80)
print(f"\nRépertoire: {AZURE_DIR}")
print(f"\nProchaine étape: Upload sur Azure Storage")
print()
