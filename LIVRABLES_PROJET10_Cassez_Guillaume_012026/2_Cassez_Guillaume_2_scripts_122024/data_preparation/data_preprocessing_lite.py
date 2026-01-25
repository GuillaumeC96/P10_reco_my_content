"""
Script de preprocessing LITE des données Globo.com
Version allégée qui utilise seulement un échantillon des données
Pour tests rapides (~2-3 minutes au lieu de 45+)
"""

import pandas as pd
import numpy as np
import pickle
import glob
import os
from pathlib import Path
from datetime import datetime
from scipy.sparse import csr_matrix, save_npz
import json

# Configuration des chemins
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "news-portal-user-interactions-by-globocom"
CLICKS_DIR = DATA_DIR / "clicks"
MODELS_DIR = BASE_DIR / "models"
MODELS_DIR.mkdir(exist_ok=True)

# CONFIGURATION LITE
N_FILES_SAMPLE = 50  # Au lieu de 385
MIN_INTERACTIONS = 3  # Au lieu de 5 (plus permissif)

def load_sample_clicks():
    """Charge un échantillon des fichiers de clics"""
    print("=" * 80)
    print("CHARGEMENT DES CLICS (VERSION LITE)")
    print("=" * 80)

    click_files = sorted(glob.glob(str(CLICKS_DIR / "clicks_hour_*.csv")))

    # Prendre seulement N_FILES_SAMPLE fichiers
    sample_files = click_files[:N_FILES_SAMPLE]
    print(f"\n📊 Échantillon: {len(sample_files)}/{len(click_files)} fichiers")

    all_clicks = []
    for i, file in enumerate(sample_files):
        if i % 10 == 0:
            print(f"  Chargement fichier {i+1}/{len(sample_files)}...")
        df = pd.read_csv(file)
        all_clicks.append(df)

    print("\n⚙️  Concaténation des données...")
    df_clicks = pd.concat(all_clicks, ignore_index=True)

    print(f"\n✓ Total d'interactions : {len(df_clicks):,}")
    print(f"✓ Utilisateurs uniques : {df_clicks['user_id'].nunique():,}")
    print(f"✓ Articles uniques cliqués : {df_clicks['click_article_id'].nunique():,}")

    return df_clicks

def create_user_item_matrix(df_clicks, min_interactions=MIN_INTERACTIONS):
    """Crée la matrice user-item pour le collaborative filtering"""
    print("\n" + "=" * 80)
    print("CRÉATION DE LA MATRICE USER-ITEM")
    print("=" * 80)

    # Filtrer les utilisateurs avec peu d'interactions
    user_counts = df_clicks['user_id'].value_counts()
    active_users = user_counts[user_counts >= min_interactions].index

    df_filtered = df_clicks[df_clicks['user_id'].isin(active_users)].copy()

    print(f"\n👥 Utilisateurs actifs (>= {min_interactions} interactions) : {len(active_users):,}")
    print(f"📊 Interactions conservées : {len(df_filtered):,} ({len(df_filtered)/len(df_clicks)*100:.1f}%)")

    # Créer la matrice d'interactions
    interactions = df_filtered.groupby(['user_id', 'click_article_id']).size().reset_index(name='count')

    # Créer des mappings
    user_to_idx = {user: idx for idx, user in enumerate(interactions['user_id'].unique())}
    article_to_idx = {article: idx for idx, article in enumerate(interactions['click_article_id'].unique())}
    idx_to_user = {idx: user for user, idx in user_to_idx.items()}
    idx_to_article = {idx: article for article, idx in article_to_idx.items()}

    # Convertir en indices
    interactions['user_idx'] = interactions['user_id'].map(user_to_idx)
    interactions['article_idx'] = interactions['click_article_id'].map(article_to_idx)

    # Créer la matrice sparse
    matrix = csr_matrix(
        (interactions['count'], (interactions['user_idx'], interactions['article_idx'])),
        shape=(len(user_to_idx), len(article_to_idx))
    )

    print(f"\n✓ Matrice créée : {matrix.shape[0]:,} users × {matrix.shape[1]:,} articles")
    print(f"✓ Sparsité : {100 * (1 - matrix.nnz / (matrix.shape[0] * matrix.shape[1])):.2f}%")

    return matrix, user_to_idx, article_to_idx, idx_to_user, idx_to_article, df_filtered

def compute_article_popularity(df_clicks):
    """Calcule la popularité des articles"""
    print("\n" + "=" * 80)
    print("CALCUL DE LA POPULARITÉ DES ARTICLES")
    print("=" * 80)

    article_stats = df_clicks.groupby('click_article_id').agg({
        'user_id': 'count',
        'session_id': 'nunique'
    }).rename(columns={'user_id': 'num_clicks', 'session_id': 'num_sessions'})

    article_stats['popularity_score'] = (
        0.7 * (article_stats['num_clicks'] / article_stats['num_clicks'].max()) +
        0.3 * (article_stats['num_sessions'] / article_stats['num_sessions'].max())
    )

    article_stats = article_stats.sort_values('popularity_score', ascending=False)

    print(f"\n✓ Articles avec au moins un clic : {len(article_stats):,}")

    return article_stats

def create_user_profiles(df_clicks, df_metadata):
    """Crée des profils utilisateurs basés sur leurs interactions"""
    print("\n" + "=" * 80)
    print("CRÉATION DES PROFILS UTILISATEURS")
    print("=" * 80)

    df_with_meta = df_clicks.merge(
        df_metadata[['article_id', 'category_id', 'words_count']],
        left_on='click_article_id',
        right_on='article_id',
        how='left'
    )

    user_categories = df_with_meta.groupby(['user_id', 'category_id']).size().reset_index(name='count')
    user_top_categories = user_categories.sort_values('count', ascending=False).groupby('user_id').head(5)

    user_profiles = {}
    for user_id in df_clicks['user_id'].unique():
        user_data = df_with_meta[df_with_meta['user_id'] == user_id]
        top_cats = user_top_categories[user_top_categories['user_id'] == user_id]['category_id'].tolist()

        user_profiles[int(user_id)] = {
            'num_interactions': len(user_data),
            'num_articles': user_data['click_article_id'].nunique(),
            'top_categories': top_cats,
            'avg_words': float(user_data['words_count'].mean()),
            'articles_read': user_data['click_article_id'].tolist()
        }

    print(f"\n✓ Profils créés pour {len(user_profiles):,} utilisateurs")

    return user_profiles

def prepare_embeddings_lite(embeddings_array, article_to_idx):
    """Prépare les embeddings (version lite - seulement les articles utilisés)"""
    print("\n" + "=" * 80)
    print("PRÉPARATION DES EMBEDDINGS (LITE)")
    print("=" * 80)

    embeddings_dict = {}
    for article_id, idx in article_to_idx.items():
        if article_id < len(embeddings_array):
            embeddings_dict[article_id] = embeddings_array[article_id]

    print(f"✓ Embeddings extraits : {len(embeddings_dict):,}")

    return embeddings_dict

def save_processed_data(matrix, user_to_idx, article_to_idx, idx_to_user, idx_to_article,
                       article_stats, user_profiles, embeddings_dict, df_metadata):
    """Sauvegarde toutes les données préparées"""
    print("\n" + "=" * 80)
    print("SAUVEGARDE DES DONNÉES PRÉPARÉES")
    print("=" * 80)

    # Sauvegarder la matrice sparse
    matrix_path = MODELS_DIR / "user_item_matrix.npz"
    save_npz(matrix_path, matrix)
    print(f"✓ Matrice user-item : {matrix_path}")

    # Sauvegarder les mappings
    mappings = {
        'user_to_idx': user_to_idx,
        'article_to_idx': article_to_idx,
        'idx_to_user': idx_to_user,
        'idx_to_article': idx_to_article
    }
    mappings_path = MODELS_DIR / "mappings.pkl"
    with open(mappings_path, 'wb') as f:
        pickle.dump(mappings, f)
    print(f"✓ Mappings : {mappings_path}")

    # Sauvegarder la popularité
    article_stats_path = MODELS_DIR / "article_popularity.pkl"
    with open(article_stats_path, 'wb') as f:
        pickle.dump(article_stats, f)
    print(f"✓ Popularité articles : {article_stats_path}")

    # Sauvegarder les profils
    user_profiles_path = MODELS_DIR / "user_profiles.json"
    with open(user_profiles_path, 'w') as f:
        json.dump(user_profiles, f, indent=2)
    print(f"✓ Profils utilisateurs : {user_profiles_path}")

    # Sauvegarder les embeddings
    embeddings_path = MODELS_DIR / "embeddings_filtered.pkl"
    with open(embeddings_path, 'wb') as f:
        pickle.dump(embeddings_dict, f)
    print(f"✓ Embeddings : {embeddings_path}")

    # Sauvegarder les métadonnées
    metadata_path = MODELS_DIR / "articles_metadata.csv"
    df_metadata.to_csv(metadata_path, index=False)
    print(f"✓ Métadonnées : {metadata_path}")

    # Stats
    stats = {
        'version': 'lite',
        'num_users': matrix.shape[0],
        'num_articles': matrix.shape[1],
        'num_interactions': int(matrix.nnz),
        'matrix_sparsity': float(100 * (1 - matrix.nnz / (matrix.shape[0] * matrix.shape[1]))),
        'processed_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'sample_size': N_FILES_SAMPLE
    }
    stats_path = MODELS_DIR / "preprocessing_stats.json"
    with open(stats_path, 'w') as f:
        json.dump(stats, f, indent=2)
    print(f"✓ Statistiques : {stats_path}")

    print(f"\n✅ Tous les fichiers sauvegardés dans {MODELS_DIR}")

def main():
    """Fonction principale"""
    print("\n")
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 18 + "PREPROCESSING LITE (VERSION RAPIDE)" + " " * 25 + "║")
    print("╚" + "═" * 78 + "╝")

    try:
        start_time = datetime.now()

        # 1. Charger métadonnées
        print("\n[1/7] Chargement des métadonnées...")
        df_metadata = pd.read_csv(DATA_DIR / "articles_metadata.csv")
        print(f"✓ {len(df_metadata):,} articles")

        # 2. Charger embeddings
        print("\n[2/7] Chargement des embeddings...")
        with open(DATA_DIR / "articles_embeddings.pickle", 'rb') as f:
            embeddings_array = pickle.load(f)
        print(f"✓ Shape: {embeddings_array.shape}")

        # 3. Charger échantillon de clics
        print("\n[3/7] Chargement échantillon de clics...")
        df_clicks = load_sample_clicks()

        # 4. Créer matrice
        print("\n[4/7] Création matrice user-item...")
        matrix, user_to_idx, article_to_idx, idx_to_user, idx_to_article, df_filtered = create_user_item_matrix(df_clicks)

        # 5. Popularité
        print("\n[5/7] Calcul popularité...")
        article_stats = compute_article_popularity(df_clicks)

        # 6. Profils
        print("\n[6/7] Création profils...")
        user_profiles = create_user_profiles(df_clicks, df_metadata)

        # 7. Embeddings
        print("\n[7/7] Préparation embeddings...")
        embeddings_dict = prepare_embeddings_lite(embeddings_array, article_to_idx)

        # Sauvegarder
        save_processed_data(
            matrix, user_to_idx, article_to_idx, idx_to_user, idx_to_article,
            article_stats, user_profiles, embeddings_dict, df_metadata
        )

        # Résumé
        elapsed = (datetime.now() - start_time).total_seconds()
        print("\n" + "=" * 80)
        print("RÉSUMÉ")
        print("=" * 80)
        print(f"\n✓ Version: LITE ({N_FILES_SAMPLE}/{385} fichiers)")
        print(f"✓ Utilisateurs: {matrix.shape[0]:,}")
        print(f"✓ Articles: {matrix.shape[1]:,}")
        print(f"✓ Interactions: {int(matrix.nnz):,}")
        print(f"✓ Sparsité: {100 * (1 - matrix.nnz / (matrix.shape[0] * matrix.shape[1])):.2f}%")
        print(f"✓ Temps d'exécution: {elapsed:.1f}s")

        print("\n✅ Preprocessing LITE terminé!")
        print(f"\n📁 Fichiers dans: {MODELS_DIR}")
        print("\n💡 Pour la version complète, utilisez data_preprocessing.py")

    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
