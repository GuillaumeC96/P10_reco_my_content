"""
Script de nettoyage des données d'interaction
Nettoie les temps aberrants causés par:
1. Onglets laissés ouverts (temps > 3x temps attendu)
2. Sessions parallèles (multitabs)

Règle de nettoyage: plafonner à 3x le temps de lecture attendu
"""

import pandas as pd
import numpy as np
from pathlib import Path
import json
from tqdm import tqdm

def clean_interaction_data():
    """
    Nettoie les données d'interaction en plafonnant les temps excessifs
    """

    print("=" * 80)
    print("NETTOYAGE DES DONNÉES D'INTERACTION")
    print("=" * 80)

    base_dir = Path(__file__).parent.parent
    models_dir = base_dir / "models"
    raw_data_dir = base_dir / "news-portal-user-interactions-by-globocom"

    # 1. Charger les métadonnées d'articles
    print("\n1. Chargement des métadonnées...")
    articles = pd.read_csv(models_dir / "articles_metadata.csv")
    articles['expected_time_minutes'] = articles['words_count'] / 200
    print(f"   - {len(articles):,} articles chargés")

    # 2. Traiter tous les fichiers de clics
    print("\n2. Traitement des fichiers de clics...")
    click_files = sorted((raw_data_dir / "clicks").glob("clicks_hour_*.csv"))
    print(f"   - {len(click_files)} fichiers à traiter")

    all_interactions = []
    total_clicks = 0
    total_cleaned = 0

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

        # Calculer le temps entre clics consécutifs
        clicks['next_timestamp'] = clicks.groupby('user_id')['click_timestamp'].shift(-1)
        clicks['time_spent_seconds'] = (clicks['next_timestamp'] - clicks['click_timestamp'])

        # Appliquer le nettoyage: plafonner au temps attendu (1x)
        clicks['expected_time_seconds'] = clicks['expected_time_minutes'] * 60
        clicks['max_time_seconds'] = clicks['expected_time_seconds'] * 1  # Exactement le temps de lecture normale

        # Nettoyer
        clicks['time_spent_cleaned'] = clicks.apply(
            lambda row: min(row['time_spent_seconds'], row['max_time_seconds'])
            if pd.notna(row['time_spent_seconds']) and pd.notna(row['max_time_seconds'])
            else np.nan,
            axis=1
        )

        # Compter les nettoyages
        cleaned_count = (clicks['time_spent_cleaned'] < clicks['time_spent_seconds']).sum()
        total_cleaned += cleaned_count

        # Garder uniquement les colonnes utiles
        interactions = clicks[clicks['time_spent_cleaned'].notna()][
            ['user_id', 'click_article_id', 'click_timestamp', 'time_spent_cleaned',
             'session_id', 'words_count']
        ].copy()

        interactions.rename(columns={'click_article_id': 'article_id'}, inplace=True)

        all_interactions.append(interactions)

    # 3. Consolider toutes les interactions
    print("\n3. Consolidation des interactions...")
    interactions_df = pd.concat(all_interactions, ignore_index=True)

    print(f"\n   - Total clics: {total_clicks:,}")
    print(f"   - Interactions avec temps: {len(interactions_df):,}")
    print(f"   - Temps nettoyés: {total_cleaned:,} ({total_cleaned/len(interactions_df)*100:.1f}%)")

    # 4. Statistiques avant/après
    print("\n4. Statistiques de nettoyage...")

    # Calculer les statistiques globales
    total_time_before = interactions_df['time_spent_cleaned'].sum()
    mean_time = interactions_df['time_spent_cleaned'].mean()
    median_time = interactions_df['time_spent_cleaned'].median()

    print(f"\n   Temps moyen par interaction:")
    print(f"   - Moyenne: {mean_time / 60:.2f} minutes")
    print(f"   - Médiane: {median_time / 60:.2f} minutes")
    print(f"   - Total: {total_time_before / 3600:.0f} heures")

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

    # Sauvegarder les interactions détaillées
    interactions_file = models_dir / "interactions_cleaned.csv"
    interactions_df.to_csv(interactions_file, index=False)
    print(f"   ✅ Interactions sauvegardées: {interactions_file}")

    # Sauvegarder les statistiques agrégées
    stats_file = models_dir / "interaction_stats_cleaned.csv"
    user_article_stats.to_csv(stats_file, index=False)
    print(f"   ✅ Statistiques sauvegardées: {stats_file}")

    # 7. Créer le rapport de nettoyage
    report = {
        'total_clicks': int(total_clicks),
        'valid_interactions': len(interactions_df),
        'cleaned_interactions': int(total_cleaned),
        'cleaned_pct': float(total_cleaned / len(interactions_df) * 100),
        'unique_user_article_pairs': len(user_article_stats),
        'time_stats': {
            'mean_seconds': float(mean_time),
            'median_seconds': float(median_time),
            'mean_minutes': float(mean_time / 60),
            'median_minutes': float(median_time / 60),
            'total_hours': float(total_time_before / 3600)
        },
        'files': {
            'interactions': str(interactions_file),
            'stats': str(stats_file)
        }
    }

    report_file = base_dir / "evaluation" / "cleaning_report.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)

    print(f"\n   ✅ Rapport sauvegardé: {report_file}")

    print("\n" + "=" * 80)
    print("NETTOYAGE TERMINÉ !")
    print("=" * 80)

    print(f"\n📊 Résumé:")
    print(f"   - Interactions nettoyées: {len(interactions_df):,}")
    print(f"   - Temps moyen: {mean_time / 60:.2f} min (réaliste!)")
    print(f"   - Taux de nettoyage: {total_cleaned/len(interactions_df)*100:.1f}%")
    print(f"\n🎯 Prochaine étape: Réentraîner le modèle avec {stats_file}")

    return user_article_stats

if __name__ == "__main__":
    clean_interaction_data()
