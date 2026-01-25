"""
Script OPTIMISÉ MÉMOIRE pour calcul des poids d'interactions
LIMITE: 30 Go de RAM maximum
STRATÉGIE: Traitement par chunks, libération mémoire agressive, monitoring continu
UTILISE 9 SIGNAUX: temps, clicks, session, device, env, referrer, OS, country, region
"""

import pandas as pd
import numpy as np
import glob
import json
import pickle
import gc
import psutil
from tqdm import tqdm
from multiprocessing import Pool
import warnings
warnings.filterwarnings('ignore')

# Configuration
CLICKS_PATH = "/home/ser/Bureau/P10_reco_new/news-portal-user-interactions-by-globocom/clicks/"
OUTPUT_PATH = "/home/ser/Bureau/P10_reco_new/models/"
MAX_MEMORY_GB = 30  # Limite stricte de mémoire
N_CORES = 12  # Réduit à 12 threads pour économiser la RAM
MAX_TIME_SPENT = 600  # Temps max considéré (10 min)
MIN_TIME_READ = 30  # SEUIL CRITIQUE: < 30s = 2ème pub non affichée = article NON lu
BATCH_SIZE = 50  # Traiter 50 fichiers à la fois
USER_CHUNK_SIZE = 5000  # Traiter 5000 utilisateurs à la fois

print("="*80)
print(f"CALCUL OPTIMISÉ MÉMOIRE - LIMITE {MAX_MEMORY_GB} Go")
print("="*80)
print(f"Configuration: {N_CORES} threads, batch {BATCH_SIZE} fichiers, chunks {USER_CHUNK_SIZE} users")
print(f"RÈGLE: Seules les interactions >= {MIN_TIME_READ}s sont comptabilisées (2ème pub affichée)")

def get_memory_usage_gb():
    """Retourne l'utilisation mémoire actuelle en Go"""
    process = psutil.Process()
    return process.memory_info().rss / (1024**3)

def check_memory_limit():
    """Vérifie qu'on ne dépasse pas la limite mémoire"""
    current_mem = get_memory_usage_gb()
    if current_mem > MAX_MEMORY_GB:
        raise MemoryError(f"LIMITE MÉMOIRE DÉPASSÉE: {current_mem:.1f} Go > {MAX_MEMORY_GB} Go")
    return current_mem

def load_and_preprocess_file(filepath):
    """Charge ET prétraite un fichier (minimal pour économiser RAM)"""
    df = pd.read_csv(filepath)
    # Tri par user, session, timestamp
    df = df.sort_values(['user_id', 'session_id', 'click_timestamp'])
    # Conversion en types plus économes
    df['user_id'] = df['user_id'].astype('int32')
    df['click_article_id'] = df['click_article_id'].astype('int32')
    return df

def compute_features(df):
    """Calcul des features de qualité (vectorisé)"""
    # Temps passé
    df['time_spent_seconds'] = df.groupby(['user_id', 'session_id'])['click_timestamp'].diff(-1) / -1000

    # RÈGLE CRITIQUE: Si < 30 secondes, la 2ème pub ne s'affiche pas = article NON lu
    # On supprime complètement ces interactions
    initial_len = len(df)
    df = df[df['time_spent_seconds'].isna() | (df['time_spent_seconds'] >= 30)].copy()
    filtered_len = len(df)
    print(f"   Filtrage 30s: {initial_len:,} -> {filtered_len:,} ({initial_len - filtered_len:,} interactions < 30s supprimées)")

    # Limites pour les articles vraiment lus (>= 30s)
    df.loc[df['time_spent_seconds'] > MAX_TIME_SPENT, 'time_spent_seconds'] = MAX_TIME_SPENT

    # Pour les valeurs manquantes (dernière interaction de session), on utilise la médiane de l'user
    median_time = df.groupby('user_id')['time_spent_seconds'].transform('median')
    df['time_spent_seconds'] = df['time_spent_seconds'].fillna(median_time).fillna(60)

    # Session, device, env, referrer quality
    df['session_quality'] = (df['session_size'] - 2) / (9 - 2)
    device_map = {1: 0.6, 3: 0.8, 4: 1.0}
    env_map = {2: 0.7, 4: 1.0}
    referrer_map = {1: 1.0, 2: 0.8, 3: 0.8, 4: 0.7, 5: 0.6, 6: 0.5, 7: 0.5}
    df['device_quality'] = df['click_deviceGroup'].map(device_map).fillna(0.7)
    df['env_quality'] = df['click_environment'].map(env_map).fillna(0.85)
    df['referrer_quality'] = df['click_referrer_type'].map(referrer_map).fillna(0.7)

    # OS quality
    os_counts = df['click_os'].value_counts()
    total_os = len(df)
    os_map = {}
    for os_id, count in os_counts.items():
        frequency = count / total_os
        os_map[os_id] = 0.85 if frequency > 0.1 else 0.80 if frequency > 0.01 else 0.75
    df['os_quality'] = df['click_os'].map(os_map).fillna(0.80)

    # Country quality
    country_counts = df['click_country'].value_counts()
    main_country = country_counts.index[0] if len(country_counts) > 0 else 1
    country_map = {}
    for country_id, count in country_counts.items():
        frequency = count / len(df)
        if country_id == main_country:
            country_map[country_id] = 0.90
        elif frequency > 0.01:
            country_map[country_id] = 0.85
        else:
            country_map[country_id] = 0.80
    df['country_quality'] = df['click_country'].map(country_map).fillna(0.85)

    # Region quality
    region_counts = df['click_region'].value_counts()
    region_map = {}
    for region_id, count in region_counts.items():
        frequency = count / len(df)
        if frequency > 0.1:
            region_map[region_id] = 0.90
        elif frequency > 0.05:
            region_map[region_id] = 0.85
        else:
            region_map[region_id] = 0.80
    df['region_quality'] = df['click_region'].map(region_map).fillna(0.85)

    return df

def aggregate_batch(df_batch):
    """Agrège un batch de données"""
    agg_dict = {
        'click_timestamp': ['count', 'min', 'max'],
        'time_spent_seconds': ['sum', 'mean', 'median'],
        'session_quality': 'mean',
        'device_quality': 'mean',
        'env_quality': 'mean',
        'referrer_quality': 'mean',
        'os_quality': 'mean',
        'country_quality': 'mean',
        'region_quality': 'mean',
        'session_size': 'mean'
    }

    result = df_batch.groupby(['user_id', 'click_article_id']).agg(agg_dict).reset_index()

    result.columns = [
        'user_id', 'article_id',
        'num_clicks', 'first_click', 'last_click',
        'total_time_seconds', 'avg_time_seconds', 'median_time_seconds',
        'avg_session_quality', 'avg_device_quality', 'avg_env_quality',
        'avg_referrer_quality', 'avg_os_quality', 'avg_country_quality',
        'avg_region_quality', 'avg_session_size'
    ]

    return result

# === ÉTAPE 1: Chargement et agrégation PAR BATCHES ===
print(f"\n1. Chargement et agrégation par batches de {BATCH_SIZE} fichiers...")
click_files = sorted(glob.glob(f"{CLICKS_PATH}clicks_hour_*.csv"))
print(f"   Total: {len(click_files)} fichiers")
print(f"   Mémoire initiale: {get_memory_usage_gb():.2f} Go")

all_interactions = []
n_batches = (len(click_files) + BATCH_SIZE - 1) // BATCH_SIZE

for batch_idx in range(n_batches):
    start_idx = batch_idx * BATCH_SIZE
    end_idx = min((batch_idx + 1) * BATCH_SIZE, len(click_files))
    batch_files = click_files[start_idx:end_idx]

    print(f"\n   Batch {batch_idx+1}/{n_batches} ({len(batch_files)} fichiers)...")

    # Chargement parallélisé du batch
    with Pool(N_CORES) as pool:
        batch_dfs = list(tqdm(
            pool.imap(load_and_preprocess_file, batch_files),
            total=len(batch_files),
            desc=f"   Loading batch {batch_idx+1}"
        ))

    # Fusion du batch
    df_batch = pd.concat(batch_dfs, ignore_index=True)
    del batch_dfs
    gc.collect()

    mem_after_load = check_memory_limit()
    print(f"   Mémoire après chargement: {mem_after_load:.2f} Go")

    # Calcul des features
    df_batch = compute_features(df_batch)

    mem_after_features = check_memory_limit()
    print(f"   Mémoire après features: {mem_after_features:.2f} Go")

    # Agrégation du batch
    batch_interactions = aggregate_batch(df_batch)
    all_interactions.append(batch_interactions)

    # Libération mémoire
    del df_batch
    gc.collect()

    mem_after_agg = check_memory_limit()
    print(f"   Mémoire après agrégation: {mem_after_agg:.2f} Go")
    print(f"   ✓ {len(batch_interactions):,} interactions agrégées dans ce batch")

# Fusion de toutes les interactions
print("\n2. Fusion finale des interactions...")
interaction_stats = pd.concat(all_interactions, ignore_index=True)
del all_interactions
gc.collect()

# Ré-agréger si un utilisateur apparaît dans plusieurs batches
print("   Ré-agrégation par user-article...")
interaction_stats = interaction_stats.groupby(['user_id', 'article_id']).agg({
    'num_clicks': 'sum',
    'first_click': 'min',
    'last_click': 'max',
    'total_time_seconds': 'sum',
    'avg_time_seconds': 'mean',
    'median_time_seconds': 'median',
    'avg_session_quality': 'mean',
    'avg_device_quality': 'mean',
    'avg_env_quality': 'mean',
    'avg_referrer_quality': 'mean',
    'avg_os_quality': 'mean',
    'avg_country_quality': 'mean',
    'avg_region_quality': 'mean',
    'avg_session_size': 'mean'
}).reset_index()

mem_after_merge = check_memory_limit()
print(f"   Mémoire après fusion: {mem_after_merge:.2f} Go")
print(f"   ✓ {len(interaction_stats):,} interactions uniques")

# === ÉTAPE 3: Calcul des poids ===
print("\n3. Calcul des poids (vectorisé)...")
max_clicks = interaction_stats['num_clicks'].max()
max_time = interaction_stats['total_time_seconds'].quantile(0.99)

interaction_stats['clicks_norm'] = np.log1p(interaction_stats['num_clicks']) / np.log1p(max_clicks)
interaction_stats['time_norm'] = interaction_stats['total_time_seconds'].clip(0, max_time) / max_time

interaction_stats['interaction_weight'] = (
    0.35 * interaction_stats['time_norm'] +
    0.20 * interaction_stats['clicks_norm'] +
    0.15 * interaction_stats['avg_session_quality'] +
    0.10 * interaction_stats['avg_device_quality'] +
    0.05 * interaction_stats['avg_env_quality'] +
    0.05 * interaction_stats['avg_referrer_quality'] +
    0.05 * interaction_stats['avg_os_quality'] +
    0.03 * interaction_stats['avg_country_quality'] +
    0.02 * interaction_stats['avg_region_quality']
).clip(0.1, 1.0)

print(f"   ✓ Poids: mean={interaction_stats['interaction_weight'].mean():.3f}, "
      f"median={interaction_stats['interaction_weight'].median():.3f}")
mem_after_weights = check_memory_limit()
print(f"   Mémoire: {mem_after_weights:.2f} Go")

# === ÉTAPE 4: Construction profils PAR CHUNKS D'UTILISATEURS ===
print(f"\n4. Construction profils par chunks de {USER_CHUNK_SIZE} users...")

def build_user_profile(user_id):
    """Construit profil pour 1 utilisateur"""
    user_data = interaction_stats[interaction_stats['user_id'] == user_id].sort_values('first_click')

    if len(user_data) == 0:
        return None

    articles_read = user_data['article_id'].tolist()
    article_weights = dict(zip(user_data['article_id'], user_data['interaction_weight']))

    article_stats = {
        int(row['article_id']): {
            'weight': float(row['interaction_weight']),
            'num_clicks': int(row['num_clicks']),
            'total_time_seconds': float(row['total_time_seconds']),
            'avg_time_seconds': float(row['avg_time_seconds']),
            'median_time_seconds': float(row['median_time_seconds']),
            'first_click_ts': int(row['first_click']),
            'last_click_ts': int(row['last_click']),
            'avg_session_quality': float(row['avg_session_quality']),
            'avg_device_quality': float(row['avg_device_quality']),
            'avg_env_quality': float(row['avg_env_quality']),
            'avg_referrer_quality': float(row['avg_referrer_quality']),
            'avg_os_quality': float(row['avg_os_quality']),
            'avg_country_quality': float(row['avg_country_quality']),
            'avg_region_quality': float(row['avg_region_quality']),
            'avg_session_size': float(row['avg_session_size'])
        }
        for _, row in user_data.iterrows()
    }

    return (int(user_id), {
        'articles_read': [int(a) for a in articles_read],
        'article_weights': {int(k): float(v) for k, v in article_weights.items()},
        'article_stats': article_stats,
        'num_interactions': int(user_data['num_clicks'].sum()),
        'num_articles': len(articles_read),
        'total_time_seconds': float(user_data['total_time_seconds'].sum()),
        'avg_weight': float(user_data['interaction_weight'].mean()),
        'avg_session_quality': float(user_data['avg_session_quality'].mean()),
        'avg_device_quality': float(user_data['avg_device_quality'].mean()),
        'avg_referrer_quality': float(user_data['avg_referrer_quality'].mean()),
        'avg_os_quality': float(user_data['avg_os_quality'].mean()),
        'avg_country_quality': float(user_data['avg_country_quality'].mean()),
        'avg_region_quality': float(user_data['avg_region_quality'].mean())
    })

unique_users = interaction_stats['user_id'].unique()
n_users = len(unique_users)
user_profiles_enriched = {}

n_user_chunks = (n_users + USER_CHUNK_SIZE - 1) // USER_CHUNK_SIZE

for chunk_idx in range(n_user_chunks):
    start_idx = chunk_idx * USER_CHUNK_SIZE
    end_idx = min((chunk_idx + 1) * USER_CHUNK_SIZE, n_users)
    user_chunk = unique_users[start_idx:end_idx]

    print(f"   Chunk {chunk_idx+1}/{n_user_chunks}: {len(user_chunk)} users...")

    with Pool(N_CORES) as pool:
        results = list(tqdm(
            pool.imap(build_user_profile, user_chunk, chunksize=100),
            total=len(user_chunk),
            desc=f"   Building chunk {chunk_idx+1}"
        ))

    # Ajouter les profils
    for user_id, profile in results:
        if profile is not None:
            user_profiles_enriched[user_id] = profile

    del results
    gc.collect()

    mem_after_chunk = check_memory_limit()
    print(f"   Mémoire: {mem_after_chunk:.2f} Go")

print(f"   ✓ {len(user_profiles_enriched):,} profils créés")

# === ÉTAPE 5: Sauvegarde ===
print("\n5. Sauvegarde...")

print("   Sauvegarde JSON...")
with open(f"{OUTPUT_PATH}user_profiles_enriched.json", 'w') as f:
    json.dump(user_profiles_enriched, f)
print(f"   ✓ user_profiles_enriched.json")

print("   Sauvegarde PKL...")
with open(f"{OUTPUT_PATH}user_profiles_enriched.pkl", 'wb') as f:
    pickle.dump(user_profiles_enriched, f)
print(f"   ✓ user_profiles_enriched.pkl")

print("   Sauvegarde CSV...")
interaction_stats.to_csv(f"{OUTPUT_PATH}interaction_stats_enriched.csv", index=False)
print(f"   ✓ interaction_stats_enriched.csv")

# === STATISTIQUES ===
print("\n" + "="*80)
print("STATISTIQUES FINALES")
print("="*80)
print(f"\nUtilisateurs: {len(user_profiles_enriched):,}")
print(f"Interactions: {interaction_stats['num_clicks'].sum():,}")
print(f"Articles: {interaction_stats['article_id'].nunique():,}")
print(f"Mémoire finale: {get_memory_usage_gb():.2f} Go / {MAX_MEMORY_GB} Go")

print(f"\n📊 Poids d'interaction:")
print(interaction_stats['interaction_weight'].describe())

print(f"\n📊 Qualité moyenne:")
print(f"  Session:  {interaction_stats['avg_session_quality'].mean():.3f}")
print(f"  Device:   {interaction_stats['avg_device_quality'].mean():.3f}")
print(f"  Env:      {interaction_stats['avg_env_quality'].mean():.3f}")
print(f"  Referrer: {interaction_stats['avg_referrer_quality'].mean():.3f}")
print(f"  OS:       {interaction_stats['avg_os_quality'].mean():.3f}")
print(f"  Country:  {interaction_stats['avg_country_quality'].mean():.3f}")
print(f"  Region:   {interaction_stats['avg_region_quality'].mean():.3f}")

# Exemples
print("\n" + "="*80)
print("EXEMPLES")
print("="*80)
for user_id in list(user_profiles_enriched.keys())[:2]:
    p = user_profiles_enriched[user_id]
    print(f"\n👤 User {user_id}:")
    print(f"   Articles: {p['num_articles']}, Clicks: {p['num_interactions']}, "
          f"Time: {p['total_time_seconds']/60:.1f}min")
    print(f"   Poids moyen: {p['avg_weight']:.3f}")
    top_articles = sorted(p['article_weights'].items(), key=lambda x: x[1], reverse=True)[:2]
    for art_id, weight in top_articles:
        s = p['article_stats'][art_id]
        print(f"     Article {art_id}: w={weight:.3f}, clicks={s['num_clicks']}, "
              f"time={s['total_time_seconds']:.0f}s")

print("\n" + "="*80)
print(f"✅ TERMINÉ ! Mémoire max utilisée: {get_memory_usage_gb():.2f} Go / {MAX_MEMORY_GB} Go")
print("="*80)
