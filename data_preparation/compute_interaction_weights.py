"""
Script pour calculer les poids d'interactions basés sur :
- Nombre de clicks par article
- Temps passé sur chaque article (estimé)

Ces poids seront utilisés pour améliorer les recommandations
"""

import pandas as pd
import numpy as np
import glob
import json
import pickle
from tqdm import tqdm
from collections import defaultdict
import os

print("="*80)
print("CALCUL DES POIDS D'INTERACTIONS À PARTIR DES CLICKS")
print("="*80)

# Chemins
CLICKS_PATH = "/home/ser/Bureau/P10_reco_new/news-portal-user-interactions-by-globocom/clicks/"
OUTPUT_PATH = "/home/ser/Bureau/P10_reco/models/"

# Paramètres
MAX_TIME_SPENT = 600  # 10 minutes max (au-delà = outlier)
MIN_TIME_SPENT = 5    # 5 secondes min (en-dessous = pas lu)

print("\n1. Chargement des fichiers de clicks...")
click_files = sorted(glob.glob(f"{CLICKS_PATH}clicks_hour_*.csv"))
print(f"   Fichiers trouvés: {len(click_files)}")

# Charger tous les clicks (peut prendre du temps et de la RAM)
print("\n2. Lecture des fichiers (cela peut prendre quelques minutes)...")
all_clicks = []

for f in tqdm(click_files, desc="Loading clicks"):
    df = pd.read_csv(f)
    all_clicks.append(df)

df_clicks = pd.concat(all_clicks, ignore_index=True)
print(f"   Total de clicks chargés: {len(df_clicks):,}")
print(f"   Utilisateurs uniques: {df_clicks.user_id.nunique():,}")
print(f"   Articles uniques: {df_clicks.click_article_id.nunique():,}")

# Libérer la mémoire
del all_clicks

print("\n3. Tri des clicks par utilisateur et timestamp...")
df_clicks = df_clicks.sort_values(['user_id', 'session_id', 'click_timestamp'])

print("\n4. Calcul du temps passé sur chaque article...")
# Temps passé = différence entre click actuel et click suivant dans la même session
df_clicks['time_spent_seconds'] = df_clicks.groupby(['user_id', 'session_id'])['click_timestamp'].diff(-1) / -1000

# Nettoyer les valeurs aberrantes
df_clicks.loc[df_clicks['time_spent_seconds'] > MAX_TIME_SPENT, 'time_spent_seconds'] = MAX_TIME_SPENT
df_clicks.loc[df_clicks['time_spent_seconds'] < MIN_TIME_SPENT, 'time_spent_seconds'] = MIN_TIME_SPENT

# Remplacer les NaN (dernier click de chaque session) par la médiane de l'utilisateur
print("   Remplissage des valeurs manquantes...")
median_time = df_clicks.groupby('user_id')['time_spent_seconds'].transform('median')
df_clicks['time_spent_seconds'].fillna(median_time, inplace=True)
df_clicks['time_spent_seconds'].fillna(60, inplace=True)  # Défaut : 60s si pas de médiane

print(f"   Temps passé moyen: {df_clicks['time_spent_seconds'].mean():.1f}s")
print(f"   Temps passé médian: {df_clicks['time_spent_seconds'].median():.1f}s")

print("\n5. Agrégation des interactions par (user, article)...")
# Pour chaque paire (user_id, article_id), calculer :
# - nombre de clicks
# - temps total passé
# - temps moyen passé

interaction_stats = df_clicks.groupby(['user_id', 'click_article_id']).agg({
    'click_timestamp': ['count', 'min', 'max'],  # count = nombre de clicks
    'time_spent_seconds': ['sum', 'mean']
}).reset_index()

# Renommer les colonnes
interaction_stats.columns = ['user_id', 'article_id', 'num_clicks', 'first_click', 'last_click',
                              'total_time_seconds', 'avg_time_seconds']

print(f"   Interactions uniques (user, article): {len(interaction_stats):,}")

print("\n6. Calcul des poids d'interaction...")
# Poids = fonction du nombre de clicks et du temps passé
# Approche : normaliser puis combiner

# Normaliser le nombre de clicks (log pour réduire l'impact des outliers)
interaction_stats['clicks_normalized'] = np.log1p(interaction_stats['num_clicks']) / np.log1p(interaction_stats['num_clicks'].max())

# Normaliser le temps total
max_time = interaction_stats['total_time_seconds'].quantile(0.99)  # 99ème percentile pour éviter outliers
interaction_stats['time_normalized'] = interaction_stats['total_time_seconds'].clip(0, max_time) / max_time

# Poids final : moyenne pondérée (60% temps, 40% clicks)
interaction_stats['interaction_weight'] = (
    0.6 * interaction_stats['time_normalized'] +
    0.4 * interaction_stats['clicks_normalized']
)

# S'assurer que le poids est entre 0.1 et 1.0
interaction_stats['interaction_weight'] = interaction_stats['interaction_weight'].clip(0.1, 1.0)

print(f"   Poids moyen: {interaction_stats['interaction_weight'].mean():.3f}")
print(f"   Poids médian: {interaction_stats['interaction_weight'].median():.3f}")

print("\n7. Création des profils utilisateurs enrichis...")
user_profiles_enriched = {}

for user_id in tqdm(interaction_stats['user_id'].unique(), desc="Building user profiles"):
    user_data = interaction_stats[interaction_stats['user_id'] == user_id].sort_values('first_click')

    # Articles lus (ordonnés chronologiquement)
    articles_read = user_data['article_id'].tolist()

    # Poids pour chaque article
    article_weights = dict(zip(user_data['article_id'], user_data['interaction_weight']))

    # Statistiques détaillées
    article_stats = {
        int(row['article_id']): {
            'weight': float(row['interaction_weight']),
            'num_clicks': int(row['num_clicks']),
            'total_time_seconds': float(row['total_time_seconds']),
            'avg_time_seconds': float(row['avg_time_seconds']),
            'first_click_ts': int(row['first_click']),
            'last_click_ts': int(row['last_click'])
        }
        for _, row in user_data.iterrows()
    }

    user_profiles_enriched[int(user_id)] = {
        'articles_read': [int(a) for a in articles_read],
        'article_weights': {int(k): float(v) for k, v in article_weights.items()},
        'article_stats': article_stats,
        'num_interactions': int(user_data['num_clicks'].sum()),
        'num_articles': len(articles_read),
        'total_time_seconds': float(user_data['total_time_seconds'].sum()),
        'avg_weight': float(user_data['interaction_weight'].mean())
    }

print(f"   Profils créés: {len(user_profiles_enriched):,}")

print("\n8. Sauvegarde des résultats...")

# Sauvegarder les profils enrichis
output_file = f"{OUTPUT_PATH}user_profiles_enriched.json"
with open(output_file, 'w') as f:
    json.dump(user_profiles_enriched, f)
print(f"   ✓ Profils enrichis sauvegardés: {output_file}")

# Sauvegarder aussi en pickle pour accès plus rapide
output_pickle = f"{OUTPUT_PATH}user_profiles_enriched.pkl"
with open(output_pickle, 'wb') as f:
    pickle.dump(user_profiles_enriched, f)
print(f"   ✓ Profils enrichis sauvegardés (pickle): {output_pickle}")

# Sauvegarder les statistiques d'interactions en CSV pour analyse
stats_file = f"{OUTPUT_PATH}interaction_stats.csv"
interaction_stats.to_csv(stats_file, index=False)
print(f"   ✓ Statistiques d'interactions sauvegardées: {stats_file}")

print("\n9. Statistiques finales...")
print("="*80)
print(f"Utilisateurs avec profils enrichis: {len(user_profiles_enriched):,}")
print(f"Total d'interactions: {interaction_stats['num_clicks'].sum():,}")
print(f"Articles uniques: {interaction_stats['article_id'].nunique():,}")
print(f"\nDistribution des poids d'interaction:")
print(interaction_stats['interaction_weight'].describe())

print(f"\nDistribution du temps passé (secondes):")
print(interaction_stats['total_time_seconds'].describe())

print(f"\nDistribution du nombre de clicks:")
print(interaction_stats['num_clicks'].describe())

# Exemple pour quelques utilisateurs
print("\n10. Exemples de profils enrichis:")
print("="*80)
sample_users = list(user_profiles_enriched.keys())[:3]
for user_id in sample_users:
    profile = user_profiles_enriched[user_id]
    print(f"\nUser {user_id}:")
    print(f"  Articles lus: {profile['num_articles']}")
    print(f"  Total interactions: {profile['num_interactions']}")
    print(f"  Temps total: {profile['total_time_seconds']:.0f}s ({profile['total_time_seconds']/60:.1f}min)")
    print(f"  Poids moyen: {profile['avg_weight']:.3f}")
    print(f"  Échantillon d'articles avec poids:")
    for article_id in list(profile['articles_read'])[:3]:
        weight = profile['article_weights'][article_id]
        stats = profile['article_stats'][article_id]
        print(f"    - Article {article_id}: poids={weight:.3f}, clicks={stats['num_clicks']}, temps={stats['total_time_seconds']:.0f}s")

print("\n" + "="*80)
print("TRAITEMENT TERMINÉ !")
print("="*80)
print("\nFichiers générés:")
print(f"  - {output_file}")
print(f"  - {output_pickle}")
print(f"  - {stats_file}")
print("\nProchaine étape: Modifier recommendation_engine.py pour utiliser ces poids")
