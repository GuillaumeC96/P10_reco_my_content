"""
Script PARALLÉLISÉ pour calculer les poids d'interactions enrichis
Utilise : clicks, temps, session_size, device, environment, referrer
Parallélisation sur 28 threads (i7 14e gen)

Basé sur les bonnes pratiques de recherche en implicit feedback:
- Hu, Koren & Volinsky (2008) - Collaborative Filtering for Implicit Feedback
- RecSys best practices pour multi-signal weighting
"""

import pandas as pd
import numpy as np
import glob
import json
import pickle
from tqdm import tqdm
from collections import defaultdict
import os
from multiprocessing import Pool, cpu_count
import warnings
warnings.filterwarnings('ignore')

print("="*80)
print("CALCUL PARALLÉLISÉ DES POIDS D'INTERACTIONS ENRICHIS")
print("="*80)

# Configuration
CLICKS_PATH = "/home/ser/Bureau/P10_reco_new/news-portal-user-interactions-by-globocom/clicks/"
OUTPUT_PATH = "/home/ser/Bureau/P10_reco/models/"
N_CORES = cpu_count()  # 28 threads
MAX_TIME_SPENT = 600
MIN_TIME_SPENT = 5

print(f"\nConfiguration:")
print(f"  Threads disponibles: {N_CORES}")
print(f"  Threads utilisés: {N_CORES}")

# === ÉTAPE 1: Chargement parallélisé des fichiers ===
print("\n1. Chargement PARALLÉLISÉ des fichiers de clicks...")
click_files = sorted(glob.glob(f"{CLICKS_PATH}clicks_hour_*.csv"))
print(f"   Fichiers trouvés: {len(click_files)}")

def load_single_file(filepath):
    """Charge un fichier CSV (pour parallélisation)"""
    return pd.read_csv(filepath)

print(f"\n2. Lecture en parallèle ({N_CORES} threads)...")
with Pool(N_CORES) as pool:
    all_clicks = list(tqdm(
        pool.imap(load_single_file, click_files),
        total=len(click_files),
        desc="Loading clicks"
    ))

df_clicks = pd.concat(all_clicks, ignore_index=True)
del all_clicks  # Libérer mémoire

print(f"   ✓ Total de clicks: {len(df_clicks):,}")
print(f"   ✓ Utilisateurs: {df_clicks.user_id.nunique():,}")
print(f"   ✓ Articles: {df_clicks.click_article_id.nunique():,}")

# === ÉTAPE 2: Enrichissement avec features contextuelles ===
print("\n3. Calcul des features enrichies...")

# Tri par user, session, timestamp
df_clicks = df_clicks.sort_values(['user_id', 'session_id', 'click_timestamp'])

# 3.1 Temps passé
print("   - Temps passé sur articles...")
df_clicks['time_spent_seconds'] = df_clicks.groupby(['user_id', 'session_id'])['click_timestamp'].diff(-1) / -1000
df_clicks.loc[df_clicks['time_spent_seconds'] > MAX_TIME_SPENT, 'time_spent_seconds'] = MAX_TIME_SPENT
df_clicks.loc[df_clicks['time_spent_seconds'] < MIN_TIME_SPENT, 'time_spent_seconds'] = MIN_TIME_SPENT
median_time = df_clicks.groupby('user_id')['time_spent_seconds'].transform('median')
df_clicks['time_spent_seconds'] = df_clicks['time_spent_seconds'].fillna(median_time).fillna(60)

# 3.2 Session quality (sessions longues = engagement fort)
print("   - Qualité de session (session_size)...")
# Normaliser session_size (range 2-9 d'après l'analyse)
df_clicks['session_quality'] = (df_clicks['session_size'] - 2) / (9 - 2)  # [0, 1]

# 3.3 Device quality (Desktop > Tablet > Mobile)
print("   - Qualité device...")
# Mapping basé sur les patterns observés:
# deviceGroup: 1=Mobile, 3=?, 4=Desktop/Tablet (à affiner)
# Hypothèse raisonnable: plus grand deviceGroup = meilleur écran
device_mapping = {
    1: 0.6,  # Mobile - écran petit, attention divisée
    3: 0.8,  # Tablette (hypothèse)
    4: 1.0   # Desktop - meilleur contexte de lecture
}
df_clicks['device_quality'] = df_clicks['click_deviceGroup'].map(device_mapping).fillna(0.7)

# 3.4 Environment quality
print("   - Qualité environnement...")
# environment: 2 ou 4 (probablement Mobile vs Desktop)
env_mapping = {
    2: 0.7,  # Mobile environment
    4: 1.0   # Desktop environment
}
df_clicks['env_quality'] = df_clicks['click_environment'].map(env_mapping).fillna(0.85)

# 3.5 Referrer quality (intention de l'utilisateur)
print("   - Qualité referrer (source du trafic)...")
# referrer_type 1-7
# Hypothèses basées sur les bonnes pratiques:
# - Search direct (type 1) = forte intention
# - Social media (type 5-7) = découverte passive
# - Internal (type 2-4) = navigation
referrer_mapping = {
    1: 1.0,   # Search/Direct - forte intention
    2: 0.8,   # Internal navigation
    3: 0.8,   # Internal
    4: 0.7,   # Internal
    5: 0.6,   # Social - découverte passive
    6: 0.5,   # Social
    7: 0.5    # Social
}
df_clicks['referrer_quality'] = df_clicks['click_referrer_type'].map(referrer_mapping).fillna(0.7)

print(f"   ✓ Features enrichies calculées")

# === ÉTAPE 3: Agrégation par (user, article) ===
print("\n4. Agrégation des interactions par (user, article)...")

aggregations = {
    'click_timestamp': ['count', 'min', 'max'],
    'time_spent_seconds': ['sum', 'mean', 'median'],
    'session_quality': 'mean',
    'device_quality': 'mean',
    'env_quality': 'mean',
    'referrer_quality': 'mean',
    'session_size': 'mean'
}

interaction_stats = df_clicks.groupby(['user_id', 'click_article_id']).agg(aggregations).reset_index()

# Aplatir les colonnes multi-index
interaction_stats.columns = [
    'user_id', 'article_id',
    'num_clicks', 'first_click', 'last_click',
    'total_time_seconds', 'avg_time_seconds', 'median_time_seconds',
    'avg_session_quality', 'avg_device_quality', 'avg_env_quality',
    'avg_referrer_quality', 'avg_session_size'
]

print(f"   ✓ Interactions agrégées: {len(interaction_stats):,}")

# === ÉTAPE 4: Calcul du poids d'interaction ENRICHI ===
print("\n5. Calcul des poids d'interaction enrichis...")

# Normalisation de chaque signal
print("   - Normalisation des signaux...")

# 5.1 Nombre de clicks (log-scale)
max_clicks = interaction_stats['num_clicks'].max()
interaction_stats['clicks_norm'] = np.log1p(interaction_stats['num_clicks']) / np.log1p(max_clicks)

# 5.2 Temps total passé
max_time = interaction_stats['total_time_seconds'].quantile(0.99)
interaction_stats['time_norm'] = interaction_stats['total_time_seconds'].clip(0, max_time) / max_time

# 5.3 Les autres sont déjà normalisés [0, 1]

# 5.4 Poids FINAL - Approche basée sur la recherche académique
# Référence: Implicit feedback systems pondèrent fortement le temps d'engagement
# puis les signaux contextuels

print("   - Combinaison pondérée des signaux...")
print("""
   Formule du poids (basée sur recherche RecSys):

   weight = 0.40 × temps_passé          (signal le plus fort d'engagement)
          + 0.25 × nombre_clicks         (récurrence = intérêt)
          + 0.15 × session_quality       (contexte d'engagement)
          + 0.10 × device_quality        (confort de lecture)
          + 0.05 × env_quality           (environnement)
          + 0.05 × referrer_quality      (intention)

   Justification des poids:
   - Temps passé (40%): Signal le plus fiable d'intérêt réel
   - Clicks (25%): Récurrence indique attachement
   - Session (15%): Sessions longues = utilisateur engagé
   - Device (10%): Meilleur contexte = plus d'attention
   - Environment (5%): Contexte technique
   - Referrer (5%): Intention initiale
""")

interaction_stats['interaction_weight'] = (
    0.40 * interaction_stats['time_norm'] +
    0.25 * interaction_stats['clicks_norm'] +
    0.15 * interaction_stats['avg_session_quality'] +
    0.10 * interaction_stats['avg_device_quality'] +
    0.05 * interaction_stats['avg_env_quality'] +
    0.05 * interaction_stats['avg_referrer_quality']
)

# Clip pour assurer [0.1, 1.0]
interaction_stats['interaction_weight'] = interaction_stats['interaction_weight'].clip(0.1, 1.0)

print(f"   ✓ Poids calculés")
print(f"     Poids moyen: {interaction_stats['interaction_weight'].mean():.3f}")
print(f"     Poids médian: {interaction_stats['interaction_weight'].median():.3f}")
print(f"     Poids min: {interaction_stats['interaction_weight'].min():.3f}")
print(f"     Poids max: {interaction_stats['interaction_weight'].max():.3f}")

# === ÉTAPE 5: Construction des profils enrichis (PARALLÉLISÉ) ===
print("\n6. Construction PARALLÉLISÉE des profils utilisateurs...")

def build_user_profile(user_id):
    """Construit le profil pour un utilisateur (pour parallélisation)"""
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
            # Nouveaux signaux enrichis
            'avg_session_quality': float(row['avg_session_quality']),
            'avg_device_quality': float(row['avg_device_quality']),
            'avg_env_quality': float(row['avg_env_quality']),
            'avg_referrer_quality': float(row['avg_referrer_quality']),
            'avg_session_size': float(row['avg_session_size'])
        }
        for _, row in user_data.iterrows()
    }

    profile = {
        'articles_read': [int(a) for a in articles_read],
        'article_weights': {int(k): float(v) for k, v in article_weights.items()},
        'article_stats': article_stats,
        'num_interactions': int(user_data['num_clicks'].sum()),
        'num_articles': len(articles_read),
        'total_time_seconds': float(user_data['total_time_seconds'].sum()),
        'avg_weight': float(user_data['interaction_weight'].mean()),
        # Statistiques globales enrichies
        'avg_session_quality': float(user_data['avg_session_quality'].mean()),
        'avg_device_quality': float(user_data['avg_device_quality'].mean()),
        'avg_referrer_quality': float(user_data['avg_referrer_quality'].mean())
    }

    return (int(user_id), profile)

unique_users = interaction_stats['user_id'].unique()
print(f"   Utilisateurs à traiter: {len(unique_users):,}")
print(f"   Utilisation de {N_CORES} threads...")

with Pool(N_CORES) as pool:
    results = list(tqdm(
        pool.imap(build_user_profile, unique_users, chunksize=100),
        total=len(unique_users),
        desc="Building profiles"
    ))

# Filtrer les None et créer le dictionnaire
user_profiles_enriched = {user_id: profile for user_id, profile in results if profile is not None}

print(f"   ✓ Profils créés: {len(user_profiles_enriched):,}")

# === ÉTAPE 6: Sauvegarde ===
print("\n7. Sauvegarde des résultats...")

output_file = f"{OUTPUT_PATH}user_profiles_enriched.json"
with open(output_file, 'w') as f:
    json.dump(user_profiles_enriched, f)
print(f"   ✓ {output_file}")

output_pickle = f"{OUTPUT_PATH}user_profiles_enriched.pkl"
with open(output_pickle, 'wb') as f:
    pickle.dump(user_profiles_enriched, f)
print(f"   ✓ {output_pickle}")

stats_file = f"{OUTPUT_PATH}interaction_stats_enriched.csv"
interaction_stats.to_csv(stats_file, index=False)
print(f"   ✓ {stats_file}")

# === ÉTAPE 7: Statistiques finales ===
print("\n" + "="*80)
print("STATISTIQUES FINALES")
print("="*80)

print(f"\nUtilisateurs: {len(user_profiles_enriched):,}")
print(f"Total interactions: {interaction_stats['num_clicks'].sum():,}")
print(f"Articles uniques: {interaction_stats['article_id'].nunique():,}")

print(f"\n📊 Distribution des poids d'interaction:")
print(interaction_stats['interaction_weight'].describe())

print(f"\n📊 Distribution du temps passé (secondes):")
print(interaction_stats['total_time_seconds'].describe())

print(f"\n📊 Qualité moyenne des signaux:")
print(f"  Session quality:  {interaction_stats['avg_session_quality'].mean():.3f}")
print(f"  Device quality:   {interaction_stats['avg_device_quality'].mean():.3f}")
print(f"  Env quality:      {interaction_stats['avg_env_quality'].mean():.3f}")
print(f"  Referrer quality: {interaction_stats['avg_referrer_quality'].mean():.3f}")

print(f"\n📊 Corrélations entre poids et signaux:")
correlations = interaction_stats[[
    'interaction_weight', 'time_norm', 'clicks_norm',
    'avg_session_quality', 'avg_device_quality', 'avg_referrer_quality'
]].corr()['interaction_weight'].sort_values(ascending=False)
print(correlations)

# Exemples
print("\n" + "="*80)
print("EXEMPLES DE PROFILS ENRICHIS")
print("="*80)

sample_users = list(user_profiles_enriched.keys())[:3]
for user_id in sample_users:
    profile = user_profiles_enriched[user_id]
    print(f"\n👤 User {user_id}:")
    print(f"   Articles: {profile['num_articles']}")
    print(f"   Total clicks: {profile['num_interactions']}")
    print(f"   Temps total: {profile['total_time_seconds']:.0f}s ({profile['total_time_seconds']/60:.1f}min)")
    print(f"   Poids moyen: {profile['avg_weight']:.3f}")
    print(f"   Session quality: {profile['avg_session_quality']:.3f}")
    print(f"   Device quality: {profile['avg_device_quality']:.3f}")
    print(f"   Referrer quality: {profile['avg_referrer_quality']:.3f}")

    print(f"   Top 3 articles par poids:")
    sorted_articles = sorted(
        profile['article_weights'].items(),
        key=lambda x: x[1],
        reverse=True
    )[:3]
    for article_id, weight in sorted_articles:
        stats = profile['article_stats'][article_id]
        print(f"     - Article {article_id}: weight={weight:.3f}, "
              f"clicks={stats['num_clicks']}, "
              f"time={stats['total_time_seconds']:.0f}s, "
              f"session_q={stats['avg_session_quality']:.2f}")

print("\n" + "="*80)
print("✅ TRAITEMENT TERMINÉ AVEC SUCCÈS!")
print("="*80)
print(f"\nFichiers générés:")
print(f"  - {output_file}")
print(f"  - {output_pickle}")
print(f"  - {stats_file}")
print(f"\nParallélisation: {N_CORES} threads utilisés")
print("Prochaine étape: Utiliser recommendation_engine_weighted.py")
