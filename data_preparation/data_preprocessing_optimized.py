"""
Version OPTIMISÉE du preprocessing - traitement par batches
Évite la concaténation massive de 385 DataFrames
"""

import pandas as pd
import numpy as np
import pickle
import glob
import os
from pathlib import Path
from datetime import datetime
from scipy.sparse import csr_matrix, save_npz, vstack
import json
from collections import defaultdict

# Configuration
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "news-portal-user-interactions-by-globocom"
CLICKS_DIR = DATA_DIR / "clicks"
MODELS_DIR = BASE_DIR / "models"
MODELS_DIR.mkdir(exist_ok=True)

BATCH_SIZE = 50  # Traiter 50 fichiers à la fois

def load_clicks_streaming():
    """Charge les clics en streaming (batch par batch) pour économiser mémoire"""
    print("=" * 80)
    print("CHARGEMENT DES CLICS (STREAMING OPTIMISÉ)")
    print("=" * 80)

    click_files = sorted(glob.glob(str(CLICKS_DIR / "clicks_hour_*.csv")))
    print(f"\nFichiers trouvés : {len(click_files)}")
    print(f"Traitement par batches de {BATCH_SIZE}")

    # Accumulateurs
    all_user_article_pairs = defaultdict(int)  # (user_id, article_id) -> count
    user_interactions = defaultdict(list)  # user_id -> [article_ids]
    article_clicks = defaultdict(int)  # article_id -> num_clicks
    article_sessions = defaultdict(set)  # article_id -> {session_ids}
    user_article_metadata = []  # Pour profils

    total_interactions = 0

    # Traiter par batches
    for batch_start in range(0, len(click_files), BATCH_SIZE):
        batch_end = min(batch_start + BATCH_SIZE, len(click_files))
        batch_files = click_files[batch_start:batch_end]

        print(f"\n  Batch {batch_start//BATCH_SIZE + 1}/{(len(click_files)-1)//BATCH_SIZE + 1} "
              f"(fichiers {batch_start+1}-{batch_end})...")

        # Charger le batch
        batch_dfs = []
        for f in batch_files:
            try:
                df = pd.read_csv(f)
                batch_dfs.append(df)
            except Exception as e:
                print(f"    Erreur {f}: {e}")

        # Concat seulement ce batch (rapide)
        if batch_dfs:
            batch_df = pd.concat(batch_dfs, ignore_index=True)

            # ✅ VECTORISÉ: Compter interactions user-article
            pair_counts = batch_df.groupby(['user_id', 'click_article_id']).size()
            for (user_id, article_id), count in pair_counts.items():
                all_user_article_pairs[(user_id, article_id)] += count

            # ✅ VECTORISÉ: Historique utilisateur (groupby + tolist)
            user_articles = batch_df.groupby('user_id')['click_article_id'].apply(list)
            for user_id, articles in user_articles.items():
                user_interactions[user_id].extend(articles)

            # ✅ VECTORISÉ: Stats articles (clics)
            article_counts = batch_df['click_article_id'].value_counts()
            for article_id, count in article_counts.items():
                article_clicks[article_id] += count

            # ✅ VECTORISÉ: Stats sessions par article
            article_session_groups = batch_df.groupby('click_article_id')['session_id'].apply(set)
            for article_id, sessions in article_session_groups.items():
                article_sessions[article_id].update(sessions)

            total_interactions += len(batch_df)

            # Garder un échantillon pour profils (pas tout pour économiser RAM)
            if batch_start == 0:
                user_article_metadata = batch_df[['user_id', 'click_article_id']].copy()

        print(f"    ✓ {len(batch_dfs)} fichiers traités | Total interactions: {total_interactions:,}")

    print(f"\n✓ Total interactions : {total_interactions:,}")
    print(f"✓ Paires user-article uniques : {len(all_user_article_pairs):,}")
    print(f"✓ Utilisateurs uniques : {len(user_interactions):,}")
    print(f"✓ Articles uniques : {len(article_clicks):,}")

    return all_user_article_pairs, user_interactions, article_clicks, article_sessions, user_article_metadata

def create_user_item_matrix_from_dict(user_article_pairs, user_interactions, min_interactions=5):
    """Crée la matrice directement depuis le dictionnaire"""
    print("\n" + "=" * 80)
    print("CRÉATION DE LA MATRICE USER-ITEM")
    print("=" * 80)

    # Filtrer utilisateurs actifs
    print("\n⚙️  Filtrage utilisateurs actifs...")
    active_users = {uid for uid, articles in user_interactions.items()
                    if len(articles) >= min_interactions}

    print(f"✓ Utilisateurs actifs (>= {min_interactions} interactions) : {len(active_users):,}")

    # Filtrer les paires
    filtered_pairs = {k: v for k, v in user_article_pairs.items() if k[0] in active_users}
    print(f"✓ Paires conservées : {len(filtered_pairs):,}")

    # Créer mappings
    print("\n⚙️  Création des mappings...")
    all_users = sorted(active_users)
    all_articles = sorted(set(article_id for (_, article_id) in filtered_pairs.keys()))

    user_to_idx = {user: idx for idx, user in enumerate(all_users)}
    article_to_idx = {article: idx for idx, article in enumerate(all_articles)}
    idx_to_user = {idx: user for user, idx in user_to_idx.items()}
    idx_to_article = {idx: article for article, idx in article_to_idx.items()}

    # Créer matrice
    print("\n⚙️  Construction de la matrice sparse...")
    rows = []
    cols = []
    data = []

    for (user_id, article_id), count in filtered_pairs.items():
        if user_id in user_to_idx and article_id in article_to_idx:
            rows.append(user_to_idx[user_id])
            cols.append(article_to_idx[article_id])
            data.append(count)

    matrix = csr_matrix((data, (rows, cols)), shape=(len(user_to_idx), len(article_to_idx)))

    print(f"\n✓ Matrice : {matrix.shape[0]:,} users × {matrix.shape[1]:,} articles")
    print(f"✓ Sparsité : {100 * (1 - matrix.nnz / (matrix.shape[0] * matrix.shape[1])):.2f}%")

    return matrix, user_to_idx, article_to_idx, idx_to_user, idx_to_article

def compute_article_popularity_from_dict(article_clicks, article_sessions):
    """Calcule popularité depuis les dictionnaires"""
    print("\n" + "=" * 80)
    print("CALCUL DE LA POPULARITÉ")
    print("=" * 80)

    stats_data = []
    for article_id in article_clicks.keys():
        num_clicks = article_clicks[article_id]
        num_sessions = len(article_sessions[article_id])
        stats_data.append({
            'article_id': article_id,
            'num_clicks': num_clicks,
            'num_sessions': num_sessions
        })

    df_stats = pd.DataFrame(stats_data).set_index('article_id')

    df_stats['popularity_score'] = (
        0.7 * (df_stats['num_clicks'] / df_stats['num_clicks'].max()) +
        0.3 * (df_stats['num_sessions'] / df_stats['num_sessions'].max())
    )

    df_stats = df_stats.sort_values('popularity_score', ascending=False)

    print(f"✓ Articles : {len(df_stats):,}")

    return df_stats

def create_user_profiles_from_dict(user_interactions, article_to_idx, df_metadata):
    """Crée profils depuis dictionnaire"""
    print("\n" + "=" * 80)
    print("CRÉATION DES PROFILS UTILISATEURS")
    print("=" * 80)

    # ✅ OPTIMISATION: Créer lookup dict une seule fois
    print("⚙️  Création lookup dict métadonnées...")
    metadata_dict = df_metadata.set_index('article_id')[['category_id', 'words_count']].to_dict('index')
    print(f"✓ {len(metadata_dict):,} articles en mémoire")

    user_profiles = {}

    for i, (user_id, articles) in enumerate(user_interactions.items()):
        if (i + 1) % 10000 == 0:
            print(f"  {i+1}/{len(user_interactions)} profils...")

        # Articles lus
        articles_read = list(set(articles))

        # Top catégories (lookup rapide)
        article_categories = []
        article_words = []
        for article_id in articles_read[:50]:  # Limiter pour performance
            if article_id in metadata_dict:
                article_categories.append(metadata_dict[article_id]['category_id'])
                article_words.append(metadata_dict[article_id]['words_count'])

        from collections import Counter
        top_cats = [cat for cat, _ in Counter(article_categories).most_common(5)]

        user_profiles[int(user_id)] = {
            'num_interactions': len(articles),
            'num_articles': len(articles_read),
            'top_categories': top_cats,
            'avg_words': float(np.mean(article_words)) if article_words else 0.0,
            'articles_read': articles_read[:100]  # Limiter pour taille JSON
        }

    print(f"\n✓ {len(user_profiles):,} profils créés")

    return user_profiles

def prepare_embeddings(embeddings_array, article_to_idx):
    """Prépare embeddings"""
    print("\n" + "=" * 80)
    print("PRÉPARATION DES EMBEDDINGS")
    print("=" * 80)

    embeddings_dict = {}
    for article_id, idx in article_to_idx.items():
        if article_id < len(embeddings_array):
            embeddings_dict[article_id] = embeddings_array[article_id]

    print(f"✓ {len(embeddings_dict):,} embeddings")

    return embeddings_dict

def save_all(matrix, mappings, article_stats, user_profiles, embeddings_dict, df_metadata, elapsed):
    """Sauvegarde tout"""
    print("\n" + "=" * 80)
    print("SAUVEGARDE")
    print("=" * 80)

    save_npz(MODELS_DIR / "user_item_matrix.npz", matrix)
    print(f"✓ Matrice")

    with open(MODELS_DIR / "mappings.pkl", 'wb') as f:
        pickle.dump(mappings, f)
    print(f"✓ Mappings")

    with open(MODELS_DIR / "article_popularity.pkl", 'wb') as f:
        pickle.dump(article_stats, f)
    print(f"✓ Popularité")

    with open(MODELS_DIR / "user_profiles.json", 'w') as f:
        json.dump(user_profiles, f)
    print(f"✓ Profils")

    with open(MODELS_DIR / "embeddings_filtered.pkl", 'wb') as f:
        pickle.dump(embeddings_dict, f)
    print(f"✓ Embeddings")

    df_metadata.to_csv(MODELS_DIR / "articles_metadata.csv", index=False)
    print(f"✓ Métadonnées")

    stats = {
        'version': 'full_optimized',
        'num_users': matrix.shape[0],
        'num_articles': matrix.shape[1],
        'num_interactions': int(matrix.nnz),
        'matrix_sparsity': float(100 * (1 - matrix.nnz / (matrix.shape[0] * matrix.shape[1]))),
        'processed_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'num_files': 385,
        'elapsed_seconds': elapsed
    }
    with open(MODELS_DIR / "preprocessing_stats.json", 'w') as f:
        json.dump(stats, f, indent=2)
    print(f"✓ Stats")

def main():
    print("\n╔" + "═" * 78 + "╗")
    print("║" + " " * 20 + "PREPROCESSING OPTIMISÉ (FULL)" + " " * 28 + "║")
    print("╚" + "═" * 78 + "╝")

    start = datetime.now()

    try:
        # 1. Métadonnées
        print("\n[1/7] Métadonnées...")
        df_metadata = pd.read_csv(DATA_DIR / "articles_metadata.csv")
        print(f"✓ {len(df_metadata):,} articles")

        # 2. Embeddings
        print("\n[2/7] Embeddings...")
        with open(DATA_DIR / "articles_embeddings.pickle", 'rb') as f:
            embeddings_array = pickle.load(f)
        print(f"✓ {embeddings_array.shape}")

        # 3. Clics streaming
        print("\n[3/7] Clics (streaming)...")
        user_article_pairs, user_interactions, article_clicks, article_sessions, _ = load_clicks_streaming()

        # 4. Matrice
        print("\n[4/7] Matrice...")
        matrix, user_to_idx, article_to_idx, idx_to_user, idx_to_article = create_user_item_matrix_from_dict(
            user_article_pairs, user_interactions, min_interactions=5
        )

        # 5. Popularité
        print("\n[5/7] Popularité...")
        article_stats = compute_article_popularity_from_dict(article_clicks, article_sessions)

        # 6. Profils
        print("\n[6/7] Profils...")
        user_profiles = create_user_profiles_from_dict(user_interactions, article_to_idx, df_metadata)

        # 7. Embeddings
        print("\n[7/7] Embeddings...")
        embeddings_dict = prepare_embeddings(embeddings_array, article_to_idx)

        # Sauvegarder
        elapsed = (datetime.now() - start).total_seconds()
        mappings = {
            'user_to_idx': user_to_idx,
            'article_to_idx': article_to_idx,
            'idx_to_user': idx_to_user,
            'idx_to_article': idx_to_article
        }
        save_all(matrix, mappings, article_stats, user_profiles, embeddings_dict, df_metadata, elapsed)

        # Résumé
        print("\n" + "=" * 80)
        print("TERMINÉ!")
        print("=" * 80)
        print(f"\n✓ Users: {matrix.shape[0]:,}")
        print(f"✓ Articles: {matrix.shape[1]:,}")
        print(f"✓ Interactions: {int(matrix.nnz):,}")
        print(f"✓ Temps: {elapsed:.0f}s ({elapsed/60:.1f} min)")

    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
