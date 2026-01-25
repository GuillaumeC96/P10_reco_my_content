"""
Script de nettoyage des données d'interaction - Version 3
Gère les sessions chevauchantes, plafonnement ET détection des clics accidentels

Règles de nettoyage:
1. Si temps < 10 secondes → clic accidentel (temps = 0)
2. Si changement de session → ancien article reçoit 0 temps (nouvelle session = ancien article abandonné)
3. Sinon → plafonner à 1× le temps théorique de lecture (200 mots/min)

Exemples de clics accidentels:
- Clic par erreur → ferme immédiatement (< 10 sec)
- Titre trompeur → retour arrière rapide
- Navigation rapide avec bouton retour du navigateur
"""

import pandas as pd
import numpy as np
from pathlib import Path
import json
from tqdm import tqdm

def clean_interaction_data_v3():
    """
    Nettoie les données en gérant les clics accidentels, sessions ET plafonnement
    """

    print("=" * 80)
    print("NETTOYAGE DES DONNÉES D'INTERACTION - VERSION 3")
    print("Détecte les clics accidentels + gère les sessions + plafonnement")
    print("=" * 80)

    base_dir = Path(__file__).parent.parent
    models_dir = base_dir / "models"
    raw_data_dir = base_dir / "news-portal-user-interactions-by-globocom"

    # 1. Charger les métadonnées d'articles
    print("\n1. Chargement des métadonnées...")
    articles = pd.read_csv(models_dir / "articles_metadata.csv")
    articles['expected_time_minutes'] = articles['words_count'] / 200  # 200 mots/min
    print(f"   - {len(articles):,} articles chargés")

    # 2. Traiter tous les fichiers de clics
    print("\n2. Traitement des fichiers de clics...")
    click_files = sorted((raw_data_dir / "clicks").glob("clicks_hour_*.csv"))
    print(f"   - {len(click_files)} fichiers à traiter")

    all_interactions = []
    total_clicks = 0
    stats = {
        'accidental_clicks': 0,  # Clics accidentels (< 10 sec)
        'session_changes': 0,    # Changements de session (temps = 0)
        'time_capped': 0,         # Temps plafonnés
        'normal_time': 0          # Temps normaux (< théorique)
    }

    ACCIDENTAL_THRESHOLD = 10  # 10 secondes

    for click_file in tqdm(click_files, desc="Traitement"):
        # Charger le fichier
        clicks = pd.read_csv(click_file)
        total_clicks += len(clicks)

        # Merger avec les métadonnées
        clicks = clicks.merge(
            articles[['article_id', 'words_count', 'expected_time_minutes']],
            left_on='click_article_id',
            right_on='article_id',
            how='left'
        )

        # Trier par utilisateur et timestamp
        clicks = clicks.sort_values(['user_id', 'click_timestamp'])

        # Calculer les infos du prochain clic
        clicks['next_timestamp'] = clicks.groupby('user_id')['click_timestamp'].shift(-1)
        clicks['next_session'] = clicks.groupby('user_id')['session_id'].shift(-1)

        # Calculer le temps brut entre clics (en secondes)
        clicks['time_between_clicks'] = (clicks['next_timestamp'] - clicks['click_timestamp'])

        # Calculer le temps théorique maximum
        clicks['expected_time_seconds'] = clicks['expected_time_minutes'] * 60

        # Appliquer les règles de nettoyage (approche vectorisée)

        # Initialiser les colonnes
        clicks['time_spent_cleaned'] = np.nan
        clicks['cleaning_reason'] = 'no_next'

        # Masque pour les lignes valides (pas dernier clic)
        valid_mask = clicks['time_between_clicks'].notna() & clicks['expected_time_seconds'].notna()

        # Règle 1: Clic accidentel (temps < 10 secondes) → temps = 0
        accidental_mask = valid_mask & (clicks['time_between_clicks'] < ACCIDENTAL_THRESHOLD)
        clicks.loc[accidental_mask, 'time_spent_cleaned'] = 0.0
        clicks.loc[accidental_mask, 'cleaning_reason'] = 'accidental_click'

        # Règle 2: Changement de session (ET pas accidentel) → temps = 0
        session_change_mask = valid_mask & ~accidental_mask & clicks['next_session'].notna() & (clicks['session_id'] != clicks['next_session'])
        clicks.loc[session_change_mask, 'time_spent_cleaned'] = 0.0
        clicks.loc[session_change_mask, 'cleaning_reason'] = 'session_change'

        # Règle 3: Même session ET pas accidentel → plafonner au temps théorique
        same_session_mask = valid_mask & ~accidental_mask & ~session_change_mask

        # Comparer temps observé vs temps max
        time_ok_mask = same_session_mask & (clicks['time_between_clicks'] <= clicks['expected_time_seconds'])
        time_excessive_mask = same_session_mask & (clicks['time_between_clicks'] > clicks['expected_time_seconds'])

        # Appliquer
        clicks.loc[time_ok_mask, 'time_spent_cleaned'] = clicks.loc[time_ok_mask, 'time_between_clicks']
        clicks.loc[time_ok_mask, 'cleaning_reason'] = 'normal'

        clicks.loc[time_excessive_mask, 'time_spent_cleaned'] = clicks.loc[time_excessive_mask, 'expected_time_seconds']
        clicks.loc[time_excessive_mask, 'cleaning_reason'] = 'capped'

        # Compter les statistiques
        stats['accidental_clicks'] += (clicks['cleaning_reason'] == 'accidental_click').sum()
        stats['session_changes'] += (clicks['cleaning_reason'] == 'session_change').sum()
        stats['time_capped'] += (clicks['cleaning_reason'] == 'capped').sum()
        stats['normal_time'] += (clicks['cleaning_reason'] == 'normal').sum()

        # Garder uniquement les colonnes utiles
        interactions = clicks[clicks['time_spent_cleaned'].notna()][[
            'user_id', 'click_article_id', 'click_timestamp', 'time_spent_cleaned',
            'session_id', 'words_count', 'cleaning_reason'
        ]].copy()

        interactions.rename(columns={'click_article_id': 'article_id'}, inplace=True)

        all_interactions.append(interactions)

    # 3. Consolider toutes les interactions
    print("\n3. Consolidation des interactions...")
    interactions_df = pd.concat(all_interactions, ignore_index=True)

    total_with_time = len(interactions_df)

    print(f"\n   📊 Statistiques de nettoyage:")
    print(f"   - Total clics: {total_clicks:,}")
    print(f"   - Interactions avec temps: {total_with_time:,}")
    print(f"   ")
    print(f"   - Clics accidentels (< 10 sec): {stats['accidental_clicks']:,} ({stats['accidental_clicks']/total_with_time*100:.1f}%)")
    print(f"   - Changements de session (temps=0): {stats['session_changes']:,} ({stats['session_changes']/total_with_time*100:.1f}%)")
    print(f"   - Temps plafonnés: {stats['time_capped']:,} ({stats['time_capped']/total_with_time*100:.1f}%)")
    print(f"   - Temps normaux: {stats['normal_time']:,} ({stats['normal_time']/total_with_time*100:.1f}%)")

    # 4. Statistiques globales
    print("\n4. Statistiques de temps...")

    # Exclure les temps = 0 pour les statistiques
    non_zero_times = interactions_df[interactions_df['time_spent_cleaned'] > 0]

    mean_time = non_zero_times['time_spent_cleaned'].mean()
    median_time = non_zero_times['time_spent_cleaned'].median()
    total_time = interactions_df['time_spent_cleaned'].sum()

    print(f"\n   Temps par interaction (excluant temps=0):")
    print(f"   - Moyenne: {mean_time / 60:.2f} minutes")
    print(f"   - Médiane: {median_time / 60:.2f} minutes")

    print(f"\n   Temps total:")
    print(f"   - Total: {total_time / 3600:.0f} heures")
    print(f"   - Incluant {stats['accidental_clicks'] + stats['session_changes']:,} interactions à 0 sec")

    # 5. Agréger par utilisateur-article
    print("\n5. Agrégation par utilisateur-article...")
    user_article_stats = interactions_df.groupby(['user_id', 'article_id']).agg({
        'click_timestamp': ['min', 'max', 'count'],
        'time_spent_cleaned': ['sum', 'mean', 'median'],
        'words_count': 'first'
    }).reset_index()

    # Aplatir les colonnes
    user_article_stats.columns = [
        'user_id', 'article_id',
        'first_click', 'last_click', 'num_clicks',
        'total_time_seconds', 'avg_time_seconds', 'median_time_seconds',
        'words_count'
    ]

    print(f"   - {len(user_article_stats):,} paires utilisateur-article uniques")

    # 6. Sauvegarder les données nettoyées
    print("\n6. Sauvegarde des données nettoyées...")

    # Sauvegarder les interactions détaillées (SANS la colonne cleaning_reason)
    interactions_to_save = interactions_df.drop(columns=['cleaning_reason'])
    interactions_file = models_dir / "interactions_cleaned_v3.csv"
    interactions_to_save.to_csv(interactions_file, index=False)
    print(f"   ✅ Interactions sauvegardées: {interactions_file}")

    # Sauvegarder les statistiques agrégées
    stats_file = models_dir / "interaction_stats_cleaned_v3.csv"
    user_article_stats.to_csv(stats_file, index=False)
    print(f"   ✅ Statistiques sauvegardées: {stats_file}")

    # 7. Créer le rapport de nettoyage
    report = {
        'total_clicks': int(total_clicks),
        'valid_interactions': len(interactions_df),
        'cleaning_stats': {
            'accidental_clicks': int(stats['accidental_clicks']),
            'accidental_clicks_pct': float(stats['accidental_clicks'] / total_with_time * 100),
            'session_changes': int(stats['session_changes']),
            'session_changes_pct': float(stats['session_changes'] / total_with_time * 100),
            'time_capped': int(stats['time_capped']),
            'time_capped_pct': float(stats['time_capped'] / total_with_time * 100),
            'normal_time': int(stats['normal_time']),
            'normal_time_pct': float(stats['normal_time'] / total_with_time * 100)
        },
        'unique_user_article_pairs': len(user_article_stats),
        'time_stats': {
            'mean_seconds': float(mean_time),
            'median_seconds': float(median_time),
            'mean_minutes': float(mean_time / 60),
            'median_minutes': float(median_time / 60),
            'total_hours': float(total_time / 3600)
        },
        'files': {
            'interactions': str(interactions_file),
            'stats': str(stats_file)
        }
    }

    report_file = base_dir / "evaluation" / "cleaning_report_v3.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)

    print(f"\n   ✅ Rapport sauvegardé: {report_file}")

    print("\n" + "=" * 80)
    print("NETTOYAGE TERMINÉ !")
    print("=" * 80)

    print(f"\n📊 Résumé:")
    print(f"   - Interactions nettoyées: {len(interactions_df):,}")
    print(f"   - Temps moyen (hors sessions abandonnées/accidentelles): {mean_time / 60:.2f} min")
    print(f"   - Clics accidentels: {stats['accidental_clicks']:,} ({stats['accidental_clicks']/total_with_time*100:.1f}%)")
    print(f"   - Sessions abandonnées: {stats['session_changes']:,} ({stats['session_changes']/total_with_time*100:.1f}%)")
    print(f"   - Temps plafonnés: {stats['time_capped']:,} ({stats['time_capped']/total_with_time*100:.1f}%)")
    print(f"\n🎯 Prochaine étape: Réentraîner le modèle avec {stats_file}")

    return user_article_stats

if __name__ == "__main__":
    clean_interaction_data_v3()
