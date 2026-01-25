"""
Analyse des anomalies de temps dans les données
Détecte:
1. Temps excessifs sur articles (> 3x temps attendu)
2. Sessions parallèles (multitabs)
3. Distribution des temps de lecture
"""

import pandas as pd
import numpy as np
import json
from pathlib import Path

def analyze_time_anomalies():
    """Analyse les anomalies de temps dans les données"""

    print("=" * 80)
    print("ANALYSE DES ANOMALIES DE TEMPS")
    print("=" * 80)

    # Charger les données
    base_dir = Path(__file__).parent.parent
    models_dir = base_dir / "models"
    raw_data_dir = base_dir / "news-portal-user-interactions-by-globocom"

    print("\n1. Chargement des données...")

    # Charger un échantillon de clics pour analyse
    # On prend les 10 premiers fichiers pour avoir un échantillon représentatif
    click_files = sorted((raw_data_dir / "clicks").glob("clicks_hour_*.csv"))[:10]

    clicks_list = []
    for f in click_files:
        print(f"   - Chargement: {f.name}...")
        df = pd.read_csv(f)
        clicks_list.append(df)

    clicks = pd.concat(clicks_list, ignore_index=True)
    articles = pd.read_csv(models_dir / "articles_metadata.csv")

    print(f"   - {len(clicks):,} clics")
    print(f"   - {len(articles):,} articles")

    # Calculer le temps attendu pour chaque article (200 mots/min)
    print("\n2. Calcul des temps attendus...")
    articles['expected_time_minutes'] = articles['words_count'] / 200

    # Merger pour avoir les infos d'articles dans clicks
    clicks = clicks.merge(
        articles[['article_id', 'words_count', 'expected_time_minutes']],
        left_on='click_article_id',
        right_on='article_id',
        how='left'
    )

    # Calculer le temps de lecture observé (différence entre clics consécutifs)
    print("\n3. Calcul des temps de lecture observés...")
    clicks = clicks.sort_values(['user_id', 'click_timestamp'])
    clicks['next_timestamp'] = clicks.groupby('user_id')['click_timestamp'].shift(-1)
    clicks['time_spent_minutes'] = (clicks['next_timestamp'] - clicks['click_timestamp']) / 60

    # Filtrer les valeurs valides (pas le dernier clic de chaque utilisateur)
    valid_clicks = clicks[clicks['time_spent_minutes'].notna()].copy()

    print(f"   - {len(valid_clicks):,} clics avec temps calculable")

    # Analyse 1: Temps excessifs
    print("\n" + "=" * 80)
    print("ANALYSE 1: TEMPS EXCESSIFS (> 2x temps attendu)")
    print("=" * 80)

    valid_clicks['expected_time_2x'] = valid_clicks['expected_time_minutes'] * 2
    valid_clicks['is_excessive'] = valid_clicks['time_spent_minutes'] > valid_clicks['expected_time_2x']

    excessive_count = valid_clicks['is_excessive'].sum()
    excessive_pct = (excessive_count / len(valid_clicks)) * 100

    print(f"\nNombre de lectures excessives: {excessive_count:,} ({excessive_pct:.1f}%)")

    # Statistiques sur les temps excessifs
    excessive = valid_clicks[valid_clicks['is_excessive']].copy()
    if len(excessive) > 0:
        excessive['excess_ratio'] = excessive['time_spent_minutes'] / excessive['expected_time_minutes']
        print(f"\nStatistiques sur les ratios d'excès:")
        print(f"   - Médiane: {excessive['excess_ratio'].median():.1f}x le temps attendu")
        print(f"   - Moyenne: {excessive['excess_ratio'].mean():.1f}x le temps attendu")
        print(f"   - Max: {excessive['excess_ratio'].max():.1f}x le temps attendu")

    # Analyse 2: Distribution des temps de lecture
    print("\n" + "=" * 80)
    print("ANALYSE 2: DISTRIBUTION DES TEMPS DE LECTURE")
    print("=" * 80)

    print(f"\nTemps de lecture observés:")
    print(f"   - Moyenne: {valid_clicks['time_spent_minutes'].mean():.2f} min")
    print(f"   - Médiane: {valid_clicks['time_spent_minutes'].median():.2f} min")
    print(f"   - Écart-type: {valid_clicks['time_spent_minutes'].std():.2f} min")
    print(f"   - Min: {valid_clicks['time_spent_minutes'].min():.2f} min")
    print(f"   - Max: {valid_clicks['time_spent_minutes'].max():.2f} min")

    # Percentiles
    print(f"\nPercentiles:")
    for p in [50, 75, 90, 95, 99]:
        val = valid_clicks['time_spent_minutes'].quantile(p/100)
        print(f"   - P{p}: {val:.2f} min")

    # Analyse 3: Temps par rapport à l'attendu
    print("\n" + "=" * 80)
    print("ANALYSE 3: RATIO TEMPS OBSERVÉ / TEMPS ATTENDU")
    print("=" * 80)

    valid_clicks['reading_rate'] = valid_clicks['time_spent_minutes'] / valid_clicks['expected_time_minutes']

    print(f"\nRatio de lecture (temps réel / temps attendu):")
    print(f"   - Moyenne: {valid_clicks['reading_rate'].mean():.2f}x")
    print(f"   - Médiane: {valid_clicks['reading_rate'].median():.2f}x")

    print(f"\nDistribution:")
    print(f"   - < 0.5x (lecture très rapide): {(valid_clicks['reading_rate'] < 0.5).sum():,} ({(valid_clicks['reading_rate'] < 0.5).sum() / len(valid_clicks) * 100:.1f}%)")
    print(f"   - 0.5x - 1.5x (lecture normale): {((valid_clicks['reading_rate'] >= 0.5) & (valid_clicks['reading_rate'] <= 1.5)).sum():,} ({((valid_clicks['reading_rate'] >= 0.5) & (valid_clicks['reading_rate'] <= 1.5)).sum() / len(valid_clicks) * 100:.1f}%)")
    print(f"   - 1.5x - 2x (lecture lente): {((valid_clicks['reading_rate'] > 1.5) & (valid_clicks['reading_rate'] <= 2)).sum():,} ({((valid_clicks['reading_rate'] > 1.5) & (valid_clicks['reading_rate'] <= 2)).sum() / len(valid_clicks) * 100:.1f}%)")
    print(f"   - > 2x (temps excessif): {(valid_clicks['reading_rate'] > 2).sum():,} ({(valid_clicks['reading_rate'] > 2).sum() / len(valid_clicks) * 100:.1f}%)")

    # Analyse 4: Impact du nettoyage
    print("\n" + "=" * 80)
    print("ANALYSE 4: IMPACT POTENTIEL DU NETTOYAGE")
    print("=" * 80)

    # Simuler le nettoyage (plafonner à 2x)
    valid_clicks['time_spent_cleaned'] = valid_clicks.apply(
        lambda row: min(row['time_spent_minutes'], row['expected_time_2x']),
        axis=1
    )

    original_total = valid_clicks['time_spent_minutes'].sum()
    cleaned_total = valid_clicks['time_spent_cleaned'].sum()
    reduction = original_total - cleaned_total
    reduction_pct = (reduction / original_total) * 100

    print(f"\nTemps total de lecture:")
    print(f"   - Avant nettoyage: {original_total:,.0f} minutes")
    print(f"   - Après nettoyage: {cleaned_total:,.0f} minutes")
    print(f"   - Réduction: {reduction:,.0f} minutes ({reduction_pct:.1f}%)")

    print(f"\nTemps moyen par lecture:")
    print(f"   - Avant: {valid_clicks['time_spent_minutes'].mean():.2f} min")
    print(f"   - Après: {valid_clicks['time_spent_cleaned'].mean():.2f} min")
    print(f"   - Réduction: {valid_clicks['time_spent_minutes'].mean() - valid_clicks['time_spent_cleaned'].mean():.2f} min ({(1 - valid_clicks['time_spent_cleaned'].mean() / valid_clicks['time_spent_minutes'].mean()) * 100:.1f}%)")

    # Sauvegarder les résultats
    results = {
        'total_clicks': len(clicks),
        'valid_clicks': len(valid_clicks),
        'excessive_time_count': int(excessive_count),
        'excessive_time_pct': float(excessive_pct),
        'time_stats': {
            'original': {
                'mean': float(valid_clicks['time_spent_minutes'].mean()),
                'median': float(valid_clicks['time_spent_minutes'].median()),
                'std': float(valid_clicks['time_spent_minutes'].std()),
                'total': float(original_total)
            },
            'cleaned': {
                'mean': float(valid_clicks['time_spent_cleaned'].mean()),
                'median': float(valid_clicks['time_spent_cleaned'].median()),
                'std': float(valid_clicks['time_spent_cleaned'].std()),
                'total': float(cleaned_total)
            },
            'reduction': {
                'minutes': float(reduction),
                'pct': float(reduction_pct)
            }
        },
        'reading_rate_distribution': {
            'very_fast_lt_0.5x': int((valid_clicks['reading_rate'] < 0.5).sum()),
            'normal_0.5_to_1.5x': int(((valid_clicks['reading_rate'] >= 0.5) & (valid_clicks['reading_rate'] <= 1.5)).sum()),
            'slow_1.5_to_3x': int(((valid_clicks['reading_rate'] > 1.5) & (valid_clicks['reading_rate'] <= 3)).sum()),
            'excessive_gt_3x': int((valid_clicks['reading_rate'] > 3).sum())
        }
    }

    output_file = Path(__file__).parent.parent / "evaluation" / "time_anomalies_analysis.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n✅ Résultats sauvegardés dans: {output_file}")
    print("\n" + "=" * 80)

if __name__ == "__main__":
    analyze_time_anomalies()
