"""
Script de preprocessing PARALLÉLISÉ des données Globo.com
Utilise multiprocessing pour charger plusieurs fichiers en même temps
Beaucoup plus rapide que la version séquentielle
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
from joblib import Parallel, delayed
from multiprocessing import cpu_count

# Configuration des chemins
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "news-portal-user-interactions-by-globocom"
CLICKS_DIR = DATA_DIR / "clicks"
MODELS_DIR = BASE_DIR / "models"
MODELS_DIR.mkdir(exist_ok=True)

# Nombre de workers parallèles (50% des CPU pour laisser de la place)
N_WORKERS = max(2, cpu_count() // 2)

def load_single_file(filepath):
    """Charge un seul fichier CSV (fonction pour multiprocessing)"""
    try:
        return pd.read_csv(filepath)
    except Exception as e:
        print(f"Erreur chargement {filepath}: {e}")
        return None

def load_all_clicks_parallel():
    """Charge et agrège tous les fichiers de clics EN PARALLÈLE avec joblib"""
    print("=" * 80)
    print("CHARGEMENT DES CLICS (VERSION PARALLÈLE - JOBLIB)")
    print("=" * 80)

    click_files = sorted(glob.glob(str(CLICKS_DIR / "clicks_hour_*.csv")))
    print(f"\nNombre de fichiers trouvés : {len(click_files)}")
    print(f"Workers parallèles : {N_WORKERS}")
    print("\n⚙️  Chargement en cours...")

    # Charger tous les fichiers en parallèle avec joblib
    all_clicks = Parallel(n_jobs=N_WORKERS, verbose=10)(
        delayed(load_single_file)(f) for f in click_files
    )

    # Filtrer les None (erreurs)
    all_clicks = [df for df in all_clicks if df is not None]

    print(f"\n✓ {len(all_clicks)} fichiers chargés")
    print("\n⚙️  Concaténation des données...")
    df_clicks = pd.concat(all_clicks, ignore_index=True)

    print(f"\n✓ Total d'interactions : {len(df_clicks):,}")
    print(f"✓ Utilisateurs uniques : {df_clicks['user_id'].nunique():,}")
    print(f"✓ Articles uniques cliqués : {df_clicks['click_article_id'].nunique():,}")
    print(f"✓ Sessions uniques : {df_clicks['session_id'].nunique():,}")

    return df_clicks

def create_user_item_matrix(df_clicks, min_interactions=5):
    """Crée la matrice user-item pour le collaborative filtering"""
    print("\n" + "=" * 80)
    print("CRÉATION DE LA MATRICE USER-ITEM")
    print("=" * 80)

    # Filtrer les utilisateurs avec peu d'interactions
    print("\n⚙️  Filtrage des utilisateurs actifs...")
    user_counts = df_clicks['user_id'].value_counts()
    active_users = user_counts[user_counts >= min_interactions].index

    df_filtered = df_clicks[df_clicks['user_id'].isin(active_users)].copy()

    print(f"\n👥 Utilisateurs actifs (>= {min_interactions} interactions) : {len(active_users):,}")
    print(f"📊 Interactions conservées : {len(df_filtered):,} ({len(df_filtered)/len(df_clicks)*100:.1f}%)")

    # Créer la matrice d'interactions (nombre de clics par user-article)
    print("\n⚙️  Création de la matrice d'interactions...")
    interactions = df_filtered.groupby(['user_id', 'click_article_id']).size().reset_index(name='count')

    print(f"✓ Paires user-article uniques : {len(interactions):,}")

    # Créer des mappings
    print("\n⚙️  Création des mappings...")
    user_to_idx = {user: idx for idx, user in enumerate(interactions['user_id'].unique())}
    article_to_idx = {article: idx for idx, article in enumerate(interactions['click_article_id'].unique())}
    idx_to_user = {idx: user for user, idx in user_to_idx.items()}
    idx_to_article = {idx: article for article, idx in article_to_idx.items()}

    # Convertir en indices
    interactions['user_idx'] = interactions['user_id'].map(user_to_idx)
    interactions['article_idx'] = interactions['click_article_id'].map(article_to_idx)

    # Créer la matrice sparse
    print("\n⚙️  Création de la matrice sparse...")
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
    print(f"\nTop 10 articles les plus populaires :")
    print(article_stats.head(10))

    return article_stats

def create_user_profiles(df_clicks, df_metadata):
    """Crée des profils utilisateurs basés sur leurs interactions"""
    print("\n" + "=" * 80)
    print("CRÉATION DES PROFILS UTILISATEURS")
    print("=" * 80)

    # Joindre avec les métadonnées
    print("\n⚙️  Jointure avec métadonnées...")
    df_with_meta = df_clicks.merge(
        df_metadata[['article_id', 'category_id', 'words_count']],
        left_on='click_article_id',
        right_on='article_id',
        how='left'
    )

    # Calculer les préférences de catégories par utilisateur
    print("\n⚙️  Calcul des préférences par catégorie...")
    user_categories = df_with_meta.groupby(['user_id', 'category_id']).size().reset_index(name='count')
    user_top_categories = user_categories.sort_values('count', ascending=False).groupby('user_id').head(5)

    # Créer un dictionnaire de profils
    print("\n⚙️  Génération des profils...")
    user_profiles = {}
    unique_users = df_clicks['user_id'].unique()

    for i, user_id in enumerate(unique_users):
        if (i + 1) % 10000 == 0:
            print(f"    Profils créés: {i+1}/{len(unique_users)}")

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

def prepare_embeddings(embeddings_array, article_to_idx):
    """Prépare les embeddings pour les articles du dataset"""
    print("\n" + "=" * 80)
    print("PRÉPARATION DES EMBEDDINGS")
    print("=" * 80)

    print(f"Shape des embeddings originaux : {embeddings_array.shape}")
    print(f"Nombre d'articles dans le mapping : {len(article_to_idx)}")

    # Créer un dictionnaire d'embeddings
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
    size_mb = os.path.getsize(matrix_path) / (1024**2)
    print(f"✓ Matrice user-item sauvegardée : {matrix_path} ({size_mb:.1f} MB)")

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
    size_mb = os.path.getsize(mappings_path) / (1024**2)
    print(f"✓ Mappings sauvegardés : {mappings_path} ({size_mb:.1f} MB)")

    # Sauvegarder la popularité des articles
    article_stats_path = MODELS_DIR / "article_popularity.pkl"
    with open(article_stats_path, 'wb') as f:
        pickle.dump(article_stats, f)
    size_kb = os.path.getsize(article_stats_path) / 1024
    print(f"✓ Popularité articles sauvegardée : {article_stats_path} ({size_kb:.0f} KB)")

    # Sauvegarder les profils utilisateurs
    user_profiles_path = MODELS_DIR / "user_profiles.json"
    with open(user_profiles_path, 'w') as f:
        json.dump(user_profiles, f, indent=2)
    size_mb = os.path.getsize(user_profiles_path) / (1024**2)
    print(f"✓ Profils utilisateurs sauvegardés : {user_profiles_path} ({size_mb:.1f} MB)")

    # Sauvegarder les embeddings filtrés
    embeddings_path = MODELS_DIR / "embeddings_filtered.pkl"
    with open(embeddings_path, 'wb') as f:
        pickle.dump(embeddings_dict, f)
    size_mb = os.path.getsize(embeddings_path) / (1024**2)
    print(f"✓ Embeddings filtrés sauvegardés : {embeddings_path} ({size_mb:.1f} MB)")

    # Sauvegarder les métadonnées
    metadata_path = MODELS_DIR / "articles_metadata.csv"
    df_metadata.to_csv(metadata_path, index=False)
    size_mb = os.path.getsize(metadata_path) / (1024**2)
    print(f"✓ Métadonnées sauvegardées : {metadata_path} ({size_mb:.1f} MB)")

    # Créer un fichier de stats
    stats = {
        'version': 'full_parallel',
        'num_users': matrix.shape[0],
        'num_articles': matrix.shape[1],
        'num_interactions': int(matrix.nnz),
        'matrix_sparsity': float(100 * (1 - matrix.nnz / (matrix.shape[0] * matrix.shape[1]))),
        'processed_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'num_files': 385,
        'num_workers': N_WORKERS
    }
    stats_path = MODELS_DIR / "preprocessing_stats.json"
    with open(stats_path, 'w') as f:
        json.dump(stats, f, indent=2)
    print(f"✓ Statistiques sauvegardées : {stats_path}")

    # Calculer taille totale
    total_size = sum(
        os.path.getsize(MODELS_DIR / f)
        for f in os.listdir(MODELS_DIR)
        if os.path.isfile(MODELS_DIR / f)
    ) / (1024**2)
    print(f"\n✅ Taille totale : {total_size:.1f} MB")

def main():
    """Fonction principale de preprocessing"""
    print("\n")
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 15 + "PREPROCESSING COMPLET (VERSION PARALLÈLE)" + " " * 22 + "║")
    print("╚" + "═" * 78 + "╝")

    try:
        start_time = datetime.now()

        # 1. Charger les métadonnées
        print("\n[1/8] Chargement des métadonnées...")
        df_metadata = pd.read_csv(DATA_DIR / "articles_metadata.csv")
        print(f"✓ {len(df_metadata):,} articles chargés")

        # 2. Charger les embeddings
        print("\n[2/8] Chargement des embeddings...")
        with open(DATA_DIR / "articles_embeddings.pickle", 'rb') as f:
            embeddings_array = pickle.load(f)
        print(f"✓ Embeddings chargés : {embeddings_array.shape}")

        # 3. Charger tous les clics EN PARALLÈLE
        print("\n[3/8] Chargement des clics (PARALLÈLE)...")
        df_clicks = load_all_clicks_parallel()

        # 4. Créer la matrice user-item
        print("\n[4/8] Création de la matrice user-item...")
        matrix, user_to_idx, article_to_idx, idx_to_user, idx_to_article, df_filtered = create_user_item_matrix(
            df_clicks, min_interactions=5
        )

        # 5. Calculer la popularité des articles
        print("\n[5/8] Calcul de la popularité...")
        article_stats = compute_article_popularity(df_clicks)

        # 6. Créer les profils utilisateurs
        print("\n[6/8] Création des profils utilisateurs...")
        user_profiles = create_user_profiles(df_clicks, df_metadata)

        # 7. Préparer les embeddings
        print("\n[7/8] Préparation des embeddings...")
        embeddings_dict = prepare_embeddings(embeddings_array, article_to_idx)

        # 8. Sauvegarder tout
        print("\n[8/8] Sauvegarde des données...")
        save_processed_data(
            matrix, user_to_idx, article_to_idx, idx_to_user, idx_to_article,
            article_stats, user_profiles, embeddings_dict, df_metadata
        )

        # Résumé final
        elapsed = (datetime.now() - start_time).total_seconds()
        print("\n" + "=" * 80)
        print("RÉSUMÉ DU PREPROCESSING")
        print("=" * 80)
        print(f"\n✓ Version: FULL PARALLEL ({N_WORKERS} workers)")
        print(f"✓ Utilisateurs actifs : {matrix.shape[0]:,}")
        print(f"✓ Articles avec interactions : {matrix.shape[1]:,}")
        print(f"✓ Interactions totales : {int(matrix.nnz):,}")
        print(f"✓ Sparsité : {100 * (1 - matrix.nnz / (matrix.shape[0] * matrix.shape[1])):.2f}%")
        print(f"✓ Embeddings dimension : {embeddings_array.shape[1]}")
        print(f"✓ Temps d'exécution : {elapsed:.1f}s ({elapsed/60:.1f} minutes)")

        print("\n✅ Preprocessing terminé avec succès!")
        print(f"\n📁 Fichiers créés dans : {MODELS_DIR}")

    except Exception as e:
        print(f"\n❌ Erreur lors du preprocessing : {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
