"""
Analyse Comparative de Deux Métriques d'Engagement

MÉTRIQUE 1: Ratio d'Engagement (Actuelle)
  - Mesure: Temps total passé / Temps disponible depuis première visite
  - Formule: ratio = total_time_minutes / (days_elapsed × 24 × 60)

MÉTRIQUE 2: Taux de Lecture (Interest-Based)
  - Mesure: Vitesse de lecture par rapport à la longueur des articles
  - Formule: taux_lecture = temps_lecture_réel / temps_lecture_attendu
  - Temps attendu basé sur nombre de mots (ex: 200 mots/minute)

But: Comparer ces deux approches et voir laquelle est plus pertinente
     pour mesurer l'intérêt réel de l'utilisateur
"""

import pandas as pd
import numpy as np
import json
from pathlib import Path
from datetime import datetime

# Configuration
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "news-portal-user-interactions-by-globocom"
CLICKS_DIR = DATA_DIR / "clicks"
OUTPUT_DIR = Path(__file__).parent

# Paramètres de lecture
READING_SPEED_WPM = 200  # Mots par minute (vitesse moyenne de lecture)
MIN_READ_TIME_SECONDS = 5  # Minimum pour considérer qu'un article a été lu
MAX_READ_TIME_MINUTES = 60  # Maximum raisonnable pour lire un article

class ComparativeMetricsAnalyzer:
    def __init__(self):
        self.metadata = None
        self.clicks = None

    def load_data(self):
        """Charge les métadonnées et échantillon de clics"""
        print("📂 Chargement des données...")

        # Métadonnées articles
        metadata_path = DATA_DIR / "articles_metadata.csv"
        self.metadata = pd.read_csv(metadata_path)
        print(f"  ✓ {len(self.metadata):,} articles chargés")

        # Charger un échantillon de clics (premiers 10 fichiers pour rapidité)
        clicks_files = sorted(CLICKS_DIR.glob("clicks_hour_*.csv"))[:10]

        clicks_list = []
        for i, file in enumerate(clicks_files, 1):
            df = pd.read_csv(file)
            clicks_list.append(df)
            if i % 5 == 0:
                print(f"  ✓ {i} fichiers de clics chargés...")

        self.clicks = pd.concat(clicks_list, ignore_index=True)
        print(f"  ✓ {len(self.clicks):,} interactions chargées")
        print(f"  ✓ {self.clicks['user_id'].nunique():,} utilisateurs uniques")

    def calculate_metric1_engagement_ratio(self):
        """
        MÉTRIQUE 1: Ratio d'Engagement
        Temps total passé / Temps disponible depuis première visite
        """
        print("\n" + "="*80)
        print("MÉTRIQUE 1: RATIO D'ENGAGEMENT (Actuelle)")
        print("="*80)

        # Calculer le temps entre clics (approximation du temps passé)
        clicks_sorted = self.clicks.sort_values(['user_id', 'click_timestamp'])

        user_metrics = []

        for user_id, group in clicks_sorted.groupby('user_id'):
            timestamps = group['click_timestamp'].values

            if len(timestamps) < 2:
                continue

            # Temps total: différence entre premier et dernier clic
            first_visit = timestamps[0]
            last_visit = timestamps[-1]

            # Calculer temps entre chaque paire de clics
            time_diffs = np.diff(timestamps) / 1000 / 60  # en minutes

            # Filtrer les temps aberrants (> 60 min = probablement pause)
            time_diffs = time_diffs[time_diffs <= MAX_READ_TIME_MINUTES]

            total_time_minutes = time_diffs.sum()

            # Temps disponible: depuis première visite
            days_elapsed = (last_visit - first_visit) / 1000 / 60 / 60 / 24

            if days_elapsed < 0.001:  # Moins de ~1.5 minutes
                days_elapsed = 0.001

            available_time_minutes = days_elapsed * 24 * 60

            # Ratio d'engagement
            engagement_ratio = total_time_minutes / available_time_minutes

            user_metrics.append({
                'user_id': user_id,
                'total_time_minutes': total_time_minutes,
                'days_elapsed': days_elapsed,
                'available_time_minutes': available_time_minutes,
                'engagement_ratio': engagement_ratio,
                'engagement_ratio_pct': engagement_ratio * 100,
                'num_interactions': len(timestamps)
            })

        df_metric1 = pd.DataFrame(user_metrics)

        print(f"\n📊 Statistiques sur {len(df_metric1):,} utilisateurs:")
        print(f"\nRatio d'engagement (%):")
        print(f"  Moyenne:  {df_metric1['engagement_ratio_pct'].mean():.4f}%")
        print(f"  Médiane:  {df_metric1['engagement_ratio_pct'].median():.4f}%")
        print(f"  Q25:      {df_metric1['engagement_ratio_pct'].quantile(0.25):.4f}%")
        print(f"  Q75:      {df_metric1['engagement_ratio_pct'].quantile(0.75):.4f}%")
        print(f"  Min:      {df_metric1['engagement_ratio_pct'].min():.4f}%")
        print(f"  Max:      {df_metric1['engagement_ratio_pct'].max():.4f}%")

        print(f"\nTemps moyen par utilisateur:")
        print(f"  Total:    {df_metric1['total_time_minutes'].mean():.2f} minutes")
        print(f"  Médiane:  {df_metric1['total_time_minutes'].median():.2f} minutes")

        return df_metric1

    def calculate_metric2_reading_rate(self):
        """
        MÉTRIQUE 2: Taux de Lecture (Interest-Based)
        Compare le temps passé à lire vs temps attendu basé sur longueur article
        """
        print("\n" + "="*80)
        print("MÉTRIQUE 2: TAUX DE LECTURE (Interest-Based)")
        print("="*80)

        # Joindre avec métadonnées pour avoir words_count
        clicks_with_words = self.clicks.merge(
            self.metadata[['article_id', 'words_count']],
            left_on='click_article_id',
            right_on='article_id',
            how='inner'
        )

        print(f"\n✓ {len(clicks_with_words):,} clics avec info sur nombre de mots")

        # Calculer le temps passé sur chaque article
        clicks_sorted = clicks_with_words.sort_values(['user_id', 'click_timestamp'])

        article_reads = []

        for user_id, group in clicks_sorted.groupby('user_id'):
            timestamps = group['click_timestamp'].values
            articles = group['click_article_id'].values
            words_counts = group['words_count'].values

            # Pour chaque article (sauf le dernier), calculer temps jusqu'au prochain clic
            for i in range(len(timestamps) - 1):
                time_spent_seconds = (timestamps[i+1] - timestamps[i]) / 1000
                time_spent_minutes = time_spent_seconds / 60

                # Filtrer les temps aberrants
                if time_spent_seconds < MIN_READ_TIME_SECONDS:
                    continue  # Trop court, pas vraiment lu

                if time_spent_minutes > MAX_READ_TIME_MINUTES:
                    continue  # Trop long, probablement parti faire autre chose

                # Temps attendu pour lire cet article
                words = words_counts[i]
                expected_time_minutes = words / READING_SPEED_WPM

                # Taux de lecture: temps réel / temps attendu
                # > 1 = lecture lente (très intéressé ?)
                # < 1 = lecture rapide (survol ?)
                # ≈ 1 = lecture normale
                reading_rate = time_spent_minutes / expected_time_minutes if expected_time_minutes > 0 else 0

                article_reads.append({
                    'user_id': user_id,
                    'article_id': articles[i],
                    'words_count': words,
                    'time_spent_minutes': time_spent_minutes,
                    'expected_time_minutes': expected_time_minutes,
                    'reading_rate': reading_rate,
                    'interest_score': min(reading_rate, 3.0)  # Cap à 3x pour éviter outliers
                })

        df_reads = pd.DataFrame(article_reads)

        print(f"\n📊 Statistiques sur {len(df_reads):,} lectures d'articles:")

        print(f"\nTemps passé par article:")
        print(f"  Moyenne:  {df_reads['time_spent_minutes'].mean():.2f} minutes")
        print(f"  Médiane:  {df_reads['time_spent_minutes'].median():.2f} minutes")

        print(f"\nTemps attendu par article:")
        print(f"  Moyenne:  {df_reads['expected_time_minutes'].mean():.2f} minutes")
        print(f"  Médiane:  {df_reads['expected_time_minutes'].median():.2f} minutes")

        print(f"\nTaux de lecture (temps_réel / temps_attendu):")
        print(f"  Moyenne:  {df_reads['reading_rate'].mean():.2f}x")
        print(f"  Médiane:  {df_reads['reading_rate'].median():.2f}x")
        print(f"  Q25:      {df_reads['reading_rate'].quantile(0.25):.2f}x")
        print(f"  Q75:      {df_reads['reading_rate'].quantile(0.75):.2f}x")

        # Calculer le taux moyen par utilisateur
        user_reading_rates = df_reads.groupby('user_id').agg({
            'reading_rate': 'mean',
            'interest_score': 'mean',
            'time_spent_minutes': 'sum',
            'article_id': 'count'
        }).rename(columns={'article_id': 'num_articles_read'})

        print(f"\n📊 Par utilisateur ({len(user_reading_rates):,} utilisateurs):")
        print(f"\nTaux de lecture moyen:")
        print(f"  Moyenne:  {user_reading_rates['reading_rate'].mean():.2f}x")
        print(f"  Médiane:  {user_reading_rates['reading_rate'].median():.2f}x")

        print(f"\nScore d'intérêt moyen (capé à 3x):")
        print(f"  Moyenne:  {user_reading_rates['interest_score'].mean():.2f}")
        print(f"  Médiane:  {user_reading_rates['interest_score'].median():.2f}")

        return df_reads, user_reading_rates

    def compare_metrics(self, df_metric1, user_reading_rates):
        """
        Compare les deux métriques côte à côte
        """
        print("\n" + "="*80)
        print("COMPARAISON DES DEUX MÉTRIQUES")
        print("="*80)

        # Joindre les deux métriques
        comparison = df_metric1.merge(
            user_reading_rates,
            on='user_id',
            how='inner'
        )

        print(f"\n✓ {len(comparison):,} utilisateurs avec les deux métriques")

        # Calculer corrélation
        corr = comparison['engagement_ratio_pct'].corr(comparison['reading_rate'])
        print(f"\n📊 Corrélation entre les deux métriques: {corr:.3f}")

        # Impact recommandations (+83%)
        boost = 1.83

        print("\n" + "="*80)
        print("IMPACT DU SYSTÈME DE RECOMMANDATION (+83% temps)")
        print("="*80)

        # MÉTRIQUE 1: Ratio d'engagement
        header1 = "MÉTRIQUE 1: RATIO D'ENGAGEMENT"
        print(f"\n{header1:-^80}")
        baseline_ratio = comparison['engagement_ratio_pct'].mean()
        boosted_ratio = baseline_ratio * boost

        print(f"\n  Sans recommandation:")
        print(f"    Ratio moyen: {baseline_ratio:.4f}%")

        print(f"\n  Avec recommandation (+83% temps):")
        print(f"    Ratio moyen: {boosted_ratio:.4f}%")
        print(f"    Gain: +{(boosted_ratio - baseline_ratio):.4f}% (+{((boosted_ratio/baseline_ratio - 1)*100):.1f}%)")

        # MÉTRIQUE 2: Taux de lecture
        header2 = "MÉTRIQUE 2: TAUX DE LECTURE"
        print(f"\n{header2:-^80}")

        baseline_rate = comparison['reading_rate'].mean()
        baseline_interest = comparison['interest_score'].mean()

        # Avec recommandation, utilisateurs lisent plus d'articles
        # MAIS le taux de lecture pourrait être différent

        # Hypothèse 1: Même taux de lecture, juste plus d'articles
        print(f"\n  Sans recommandation:")
        print(f"    Taux de lecture moyen: {baseline_rate:.2f}x")
        print(f"    Score d'intérêt: {baseline_interest:.2f}")
        print(f"    Articles lus par user: {comparison['num_articles_read'].mean():.1f}")

        print(f"\n  Avec recommandation - Hypothèse 1 (même taux, +83% articles):")
        boosted_articles_h1 = comparison['num_articles_read'].mean() * boost
        print(f"    Taux de lecture moyen: {baseline_rate:.2f}x (inchangé)")
        print(f"    Score d'intérêt: {baseline_interest:.2f} (inchangé)")
        print(f"    Articles lus par user: {boosted_articles_h1:.1f}")
        print(f"    Gain: +{((boosted_articles_h1 - comparison['num_articles_read'].mean()) / comparison['num_articles_read'].mean() * 100):.1f}%")

        # Hypothèse 2: Taux de lecture amélioré (meilleure pertinence)
        # Assume +20% d'intérêt grâce aux recommandations
        interest_boost = 1.20
        boosted_rate_h2 = baseline_rate * interest_boost
        boosted_interest_h2 = baseline_interest * interest_boost

        print(f"\n  Avec recommandation - Hypothèse 2 (taux amélioré +20% + 83% articles):")
        print(f"    Taux de lecture moyen: {boosted_rate_h2:.2f}x (+{((interest_boost-1)*100):.0f}%)")
        print(f"    Score d'intérêt: {boosted_interest_h2:.2f} (+{((interest_boost-1)*100):.0f}%)")
        print(f"    Articles lus par user: {boosted_articles_h1:.1f}")
        print(f"    Gain en engagement: +{((boosted_rate_h2 * boosted_articles_h1) / (baseline_rate * comparison['num_articles_read'].mean()) - 1) * 100:.1f}%")

        # Résumé
        print("\n" + "="*80)
        print("RÉSUMÉ COMPARATIF")
        print("="*80)

        print("""
┌──────────────────────────────────────────────────────────────────────────┐
│  MÉTRIQUE 1: Ratio d'Engagement (Temps / Temps Disponible)              │
├──────────────────────────────────────────────────────────────────────────┤
│  ✅ Avantages:                                                           │
│    • Simple à comprendre et calculer                                    │
│    • Normalisée par l'ancienneté du compte                              │
│    • Mesure l'engagement global sur le site                             │
│    • Facile à suivre dans le temps                                      │
│                                                                          │
│  ⚠️  Limites:                                                            │
│    • Ne mesure pas la QUALITÉ de l'engagement                           │
│    • Un user qui lit vite vs lentement = même ratio                     │
│    • Ne capte pas l'intérêt réel pour le contenu                        │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────┐
│  MÉTRIQUE 2: Taux de Lecture (Temps Réel / Temps Attendu)               │
├──────────────────────────────────────────────────────────────────────────┤
│  ✅ Avantages:                                                           │
│    • Mesure l'INTÉRÊT réel pour le contenu                              │
│    • Tient compte de la longueur des articles                           │
│    • Distingue lecture rapide (survol) vs lente (intéressé)             │
│    • Plus granulaire (par article)                                      │
│                                                                          │
│  ⚠️  Limites:                                                            │
│    • Dépend de l'hypothèse de vitesse de lecture (200 wpm)              │
│    • Plus complexe à calculer                                           │
│    • Nécessite le nombre de mots (pas toujours disponible)              │
│    • Difficile à suivre dans le temps (variance élevée)                 │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
        """)

        # Sauvegarde résultats
        results = {
            'metric1_engagement_ratio': {
                'name': 'Ratio d\'Engagement',
                'baseline_pct': float(baseline_ratio),
                'with_reco_pct': float(boosted_ratio),
                'gain_pct': float(boosted_ratio - baseline_ratio),
                'gain_relative_pct': float((boosted_ratio/baseline_ratio - 1) * 100)
            },
            'metric2_reading_rate': {
                'name': 'Taux de Lecture',
                'baseline_rate': float(baseline_rate),
                'baseline_interest_score': float(baseline_interest),
                'baseline_articles_per_user': float(comparison['num_articles_read'].mean()),
                'hypothesis1_same_rate': {
                    'rate': float(baseline_rate),
                    'articles_per_user': float(boosted_articles_h1),
                    'gain_pct': 83.0
                },
                'hypothesis2_improved_rate': {
                    'rate': float(boosted_rate_h2),
                    'interest_score': float(boosted_interest_h2),
                    'articles_per_user': float(boosted_articles_h1),
                    'total_engagement_gain_pct': float(((boosted_rate_h2 * boosted_articles_h1) / (baseline_rate * comparison['num_articles_read'].mean()) - 1) * 100)
                }
            },
            'correlation': float(corr),
            'num_users': len(comparison),
            'reading_speed_wpm': READING_SPEED_WPM
        }

        output_file = OUTPUT_DIR / "comparative_metrics_results.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        print(f"\n✅ Résultats sauvegardés: {output_file}")

        return comparison, results

def main():
    print("="*80)
    print("ANALYSE COMPARATIVE DES MÉTRIQUES D'ENGAGEMENT")
    print("="*80)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Vitesse de lecture assumée: {READING_SPEED_WPM} mots/minute")
    print("="*80)

    analyzer = ComparativeMetricsAnalyzer()

    # Charger données
    analyzer.load_data()

    # Calculer métrique 1
    df_metric1 = analyzer.calculate_metric1_engagement_ratio()

    # Calculer métrique 2
    df_reads, user_reading_rates = analyzer.calculate_metric2_reading_rate()

    # Comparer
    comparison, results = analyzer.compare_metrics(df_metric1, user_reading_rates)

    print("\n" + "="*80)
    print("✅ ANALYSE TERMINÉE")
    print("="*80)

if __name__ == "__main__":
    main()
