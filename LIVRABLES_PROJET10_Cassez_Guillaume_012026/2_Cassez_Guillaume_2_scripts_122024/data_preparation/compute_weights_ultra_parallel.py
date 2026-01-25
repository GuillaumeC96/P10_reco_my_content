"""
Script ULTRA-PARALLÉLISÉ pour calcul des poids d'interactions
Parallélisation COMPLÈTE sur 28 threads pour TOUTES les étapes critiques
UTILISE 9 SIGNAUX: temps, clicks, session, device, env, referrer, OS, country, region
"""

import pandas as pd
import numpy as np
import glob
import json
import pickle
from tqdm import tqdm
from multiprocessing import Pool, cpu_count
import warnings
warnings.filterwarnings('ignore')

print("="*80)
print("CALCUL ULTRA-PARALLÉLISÉ DES POIDS (28 THREADS PARTOUT)")
print("="*80)

CLICKS_PATH = "/home/ser/Bureau/P10_reco_new/news-portal-user-interactions-by-globocom/clicks/"
OUTPUT_PATH = "/home/ser/Bureau/P10_reco/models/"
N_CORES = cpu_count()
MAX_TIME_SPENT = 600
MIN_TIME_SPENT = 5

print(f"\nConfiguration: {N_CORES} threads pour TOUTES les étapes")

# === ÉTAPE 1: Chargement parallélisé ===
print("\n1. Chargement PARALLÉLISÉ (28 threads)...")
click_files = sorted(glob.glob(f"{CLICKS_PATH}clicks_hour_*.csv"))
print(f"   Fichiers: {len(click_files)}")

def load_and_preprocess_file(filepath):
    """Charge ET prétraite un fichier (parallélisé)"""
    df = pd.read_csv(filepath)
    # Tri par user, session, timestamp
    df = df.sort_values(['user_id', 'session_id', 'click_timestamp'])
    return df

with Pool(N_CORES) as pool:
    all_clicks = list(tqdm(
        pool.imap(load_and_preprocess_file, click_files),
        total=len(click_files),
        desc="Loading & sorting"
    ))

df_clicks = pd.concat(all_clicks, ignore_index=True)
del all_clicks
print(f"   ✓ {len(df_clicks):,} clicks, {df_clicks.user_id.nunique():,} users")

# === ÉTAPE 2: Calcul features (vectorisé - rapide) ===
print("\n2. Calcul features (vectorisé)...")

# Temps passé
df_clicks['time_spent_seconds'] = df_clicks.groupby(['user_id', 'session_id'])['click_timestamp'].diff(-1) / -1000
df_clicks.loc[df_clicks['time_spent_seconds'] > MAX_TIME_SPENT, 'time_spent_seconds'] = MAX_TIME_SPENT
df_clicks.loc[df_clicks['time_spent_seconds'] < MIN_TIME_SPENT, 'time_spent_seconds'] = MIN_TIME_SPENT
median_time = df_clicks.groupby('user_id')['time_spent_seconds'].transform('median')
df_clicks['time_spent_seconds'] = df_clicks['time_spent_seconds'].fillna(median_time).fillna(60)

# Session, device, env, referrer quality
df_clicks['session_quality'] = (df_clicks['session_size'] - 2) / (9 - 2)
device_map = {1: 0.6, 3: 0.8, 4: 1.0}
env_map = {2: 0.7, 4: 1.0}
referrer_map = {1: 1.0, 2: 0.8, 3: 0.8, 4: 0.7, 5: 0.6, 6: 0.5, 7: 0.5}
df_clicks['device_quality'] = df_clicks['click_deviceGroup'].map(device_map).fillna(0.7)
df_clicks['env_quality'] = df_clicks['click_environment'].map(env_map).fillna(0.85)
df_clicks['referrer_quality'] = df_clicks['click_referrer_type'].map(referrer_map).fillna(0.7)

# NOUVEAUX SIGNAUX: OS, Country, Region (encodage par popularité)
# OS quality - basé sur fréquence (valeurs fréquentes = qualité moyenne)
os_counts = df_clicks['click_os'].value_counts()
total_os = len(df_clicks)
os_map = {}
for os_id, count in os_counts.items():
    frequency = count / total_os
    # Fréquence élevée = neutre (0.85), fréquence faible = légère baisse (0.75)
    os_map[os_id] = 0.85 if frequency > 0.1 else 0.80 if frequency > 0.01 else 0.75
df_clicks['os_quality'] = df_clicks['click_os'].map(os_map).fillna(0.80)

# Country quality - basé sur popularité (pays principal = neutre)
country_counts = df_clicks['click_country'].value_counts()
main_country = country_counts.index[0] if len(country_counts) > 0 else 1
country_map = {}
for country_id, count in country_counts.items():
    frequency = count / len(df_clicks)
    if country_id == main_country:
        country_map[country_id] = 0.90  # Pays principal (Brésil probablement)
    elif frequency > 0.01:
        country_map[country_id] = 0.85  # Pays secondaires fréquents
    else:
        country_map[country_id] = 0.80  # Pays rares
df_clicks['country_quality'] = df_clicks['click_country'].map(country_map).fillna(0.85)

# Region quality - basé sur densité (régions populaires = plus d'utilisateurs)
region_counts = df_clicks['click_region'].value_counts()
region_map = {}
for region_id, count in region_counts.items():
    frequency = count / len(df_clicks)
    if frequency > 0.1:
        region_map[region_id] = 0.90  # Région très active
    elif frequency > 0.05:
        region_map[region_id] = 0.85  # Région active
    else:
        region_map[region_id] = 0.80  # Région moins active
df_clicks['region_quality'] = df_clicks['click_region'].map(region_map).fillna(0.85)

print("   ✓ Features calculées (9 signaux)")

# === ÉTAPE 3: Agrégation PARALLÉLISÉE par chunks d'utilisateurs ===
print("\n3. Agrégation PARALLÉLISÉE par chunks d'utilisateurs...")

unique_users = df_clicks['user_id'].unique()
n_users = len(unique_users)
chunk_size = max(1, n_users // N_CORES)  # Diviser en 28 chunks
user_chunks = [unique_users[i:i+chunk_size] for i in range(0, n_users, chunk_size)]

print(f"   Users: {n_users:,} | Chunks: {len(user_chunks)} | Size: ~{chunk_size}")

def aggregate_user_chunk(user_list):
    """Agrège les interactions pour un chunk d'utilisateurs"""
    # Filtrer le DataFrame pour ces utilisateurs
    chunk_df = df_clicks[df_clicks['user_id'].isin(user_list)]

    # Agrégation (9 signaux)
    agg_dict = {
        'click_timestamp': ['count', 'min', 'max'],
        'time_spent_seconds': ['sum', 'mean', 'median'],
        'session_quality': 'mean',
        'device_quality': 'mean',
        'env_quality': 'mean',
        'referrer_quality': 'mean',
        'os_quality': 'mean',        # NOUVEAU
        'country_quality': 'mean',   # NOUVEAU
        'region_quality': 'mean',    # NOUVEAU
        'session_size': 'mean'
    }

    result = chunk_df.groupby(['user_id', 'click_article_id']).agg(agg_dict).reset_index()

    # Aplatir colonnes
    result.columns = [
        'user_id', 'article_id',
        'num_clicks', 'first_click', 'last_click',
        'total_time_seconds', 'avg_time_seconds', 'median_time_seconds',
        'avg_session_quality', 'avg_device_quality', 'avg_env_quality',
        'avg_referrer_quality', 'avg_os_quality', 'avg_country_quality',
        'avg_region_quality', 'avg_session_size'
    ]

    return result

print(f"   Agrégation sur {N_CORES} threads...")
with Pool(N_CORES) as pool:
    chunk_results = list(tqdm(
        pool.imap(aggregate_user_chunk, user_chunks),
        total=len(user_chunks),
        desc="Aggregating chunks"
    ))

# Fusionner tous les chunks
interaction_stats = pd.concat(chunk_results, ignore_index=True)
del chunk_results
print(f"   ✓ {len(interaction_stats):,} interactions agrégées")

# === ÉTAPE 4: Calcul poids (vectorisé) ===
print("\n4. Calcul des poids (vectorisé)...")

max_clicks = interaction_stats['num_clicks'].max()
max_time = interaction_stats['total_time_seconds'].quantile(0.99)

interaction_stats['clicks_norm'] = np.log1p(interaction_stats['num_clicks']) / np.log1p(max_clicks)
interaction_stats['time_norm'] = interaction_stats['total_time_seconds'].clip(0, max_time) / max_time

interaction_stats['interaction_weight'] = (
    0.35 * interaction_stats['time_norm'] +              # Temps (35% - réduit légèrement)
    0.20 * interaction_stats['clicks_norm'] +            # Clicks (20%)
    0.15 * interaction_stats['avg_session_quality'] +    # Session (15%)
    0.10 * interaction_stats['avg_device_quality'] +     # Device (10%)
    0.05 * interaction_stats['avg_env_quality'] +        # Environment (5%)
    0.05 * interaction_stats['avg_referrer_quality'] +   # Referrer (5%)
    0.05 * interaction_stats['avg_os_quality'] +         # OS (5%) NOUVEAU
    0.03 * interaction_stats['avg_country_quality'] +    # Country (3%) NOUVEAU
    0.02 * interaction_stats['avg_region_quality']       # Region (2%) NOUVEAU
).clip(0.1, 1.0)  # Total = 100%

print(f"   ✓ Poids: mean={interaction_stats['interaction_weight'].mean():.3f}, "
      f"median={interaction_stats['interaction_weight'].median():.3f}")

# === ÉTAPE 5: Construction profils PARALLÉLISÉE ===
print("\n5. Construction profils PARALLÉLISÉE (28 threads)...")

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
            'avg_os_quality': float(row['avg_os_quality']),           # NOUVEAU
            'avg_country_quality': float(row['avg_country_quality']), # NOUVEAU
            'avg_region_quality': float(row['avg_region_quality']),   # NOUVEAU
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
        'avg_os_quality': float(user_data['avg_os_quality'].mean()),           # NOUVEAU
        'avg_country_quality': float(user_data['avg_country_quality'].mean()), # NOUVEAU
        'avg_region_quality': float(user_data['avg_region_quality'].mean())    # NOUVEAU
    })

unique_users_final = interaction_stats['user_id'].unique()
print(f"   Building {len(unique_users_final):,} profiles...")

with Pool(N_CORES) as pool:
    results = list(tqdm(
        pool.imap(build_user_profile, unique_users_final, chunksize=100),
        total=len(unique_users_final),
        desc="Building profiles"
    ))

user_profiles_enriched = {user_id: profile for user_id, profile in results if profile is not None}
print(f"   ✓ {len(user_profiles_enriched):,} profils créés")

# === ÉTAPE 6: Sauvegarde ===
print("\n6. Sauvegarde...")

with open(f"{OUTPUT_PATH}user_profiles_enriched.json", 'w') as f:
    json.dump(user_profiles_enriched, f)
print(f"   ✓ user_profiles_enriched.json")

with open(f"{OUTPUT_PATH}user_profiles_enriched.pkl", 'wb') as f:
    pickle.dump(user_profiles_enriched, f)
print(f"   ✓ user_profiles_enriched.pkl")

interaction_stats.to_csv(f"{OUTPUT_PATH}interaction_stats_enriched.csv", index=False)
print(f"   ✓ interaction_stats_enriched.csv")

# === STATISTIQUES ===
print("\n" + "="*80)
print("STATISTIQUES FINALES")
print("="*80)
print(f"\nUtilisateurs: {len(user_profiles_enriched):,}")
print(f"Interactions: {interaction_stats['num_clicks'].sum():,}")
print(f"Articles: {interaction_stats['article_id'].nunique():,}")

print(f"\n📊 Poids d'interaction:")
print(interaction_stats['interaction_weight'].describe())

print(f"\n📊 Qualité moyenne:")
print(f"  Session:  {interaction_stats['avg_session_quality'].mean():.3f}")
print(f"  Device:   {interaction_stats['avg_device_quality'].mean():.3f}")
print(f"  Env:      {interaction_stats['avg_env_quality'].mean():.3f}")
print(f"  Referrer: {interaction_stats['avg_referrer_quality'].mean():.3f}")

print(f"\n📊 Corrélations (poids vs signaux):")
corr = interaction_stats[[
    'interaction_weight', 'time_norm', 'clicks_norm',
    'avg_session_quality', 'avg_device_quality', 'avg_referrer_quality'
]].corr()['interaction_weight'].sort_values(ascending=False)
for col, val in corr.items():
    if col != 'interaction_weight':
        print(f"  {col:25s}: {val:.3f}")

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
print("✅ TERMINÉ ! Parallélisation maximale sur 28 threads")
print("="*80)
