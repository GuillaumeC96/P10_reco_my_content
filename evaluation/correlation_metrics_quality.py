"""
Analyse: Est-ce que l'amélioration du Ratio d'Engagement (Métrique 1)
        améliore aussi le Taux de Lecture par article (Métrique 2) ?

Question: Si on augmente le temps passé (+83%), est-ce que:
  A) Les utilisateurs lisent plus d'articles au même rythme ?
  B) Les utilisateurs lisent mieux (taux de lecture amélioré) ?
  C) Un mix des deux ?
"""

import pandas as pd
import numpy as np
from pathlib import Path
import json

# Configuration
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "news-portal-user-interactions-by-globocom"
CLICKS_DIR = DATA_DIR / "clicks"
OUTPUT_DIR = Path(__file__).parent

READING_SPEED_WPM = 200
MIN_READ_TIME_SECONDS = 5
MAX_READ_TIME_MINUTES = 60

print("="*80)
print("ANALYSE: RATIO D'ENGAGEMENT → TAUX DE LECTURE")
print("="*80)
print("\nQuestion: L'augmentation du temps passé améliore-t-elle la QUALITÉ")
print("          de la lecture (taux de lecture par article) ?")
print("="*80)

class QualityCorrelationAnalyzer:
    def __init__(self):
        self.metadata = None
        self.clicks = None

    def load_data(self):
        """Charge les métadonnées et échantillon de clics"""
        print("\n📂 Chargement des données...")

        # Métadonnées articles
        metadata_path = DATA_DIR / "articles_metadata.csv"
        self.metadata = pd.read_csv(metadata_path)

        # Charger échantillon de clics (10 premiers fichiers)
        clicks_files = sorted(CLICKS_DIR.glob("clicks_hour_*.csv"))[:10]
        clicks_list = []
        for file in clicks_files:
            df = pd.read_csv(file)
            clicks_list.append(df)

        self.clicks = pd.concat(clicks_list, ignore_index=True)
        print(f"  ✓ {len(self.clicks):,} interactions chargées")
        print(f"  ✓ {self.clicks['user_id'].nunique():,} utilisateurs uniques")

    def calculate_user_metrics(self):
        """Calcule les deux métriques pour chaque utilisateur"""
        print("\n📊 Calcul des métriques par utilisateur...")

        # Joindre avec métadonnées
        clicks_with_words = self.clicks.merge(
            self.metadata[['article_id', 'words_count']],
            left_on='click_article_id',
            right_on='article_id',
            how='inner'
        )

        clicks_sorted = clicks_with_words.sort_values(['user_id', 'click_timestamp'])

        user_metrics = []

        for user_id, group in clicks_sorted.groupby('user_id'):
            timestamps = group['click_timestamp'].values
            words_counts = group['words_count'].values

            if len(timestamps) < 2:
                continue

            # MÉTRIQUE 1: Ratio d'engagement
            first_visit = timestamps[0]
            last_visit = timestamps[-1]

            time_diffs = np.diff(timestamps) / 1000 / 60  # en minutes
            time_diffs = time_diffs[time_diffs <= MAX_READ_TIME_MINUTES]

            total_time_minutes = time_diffs.sum()
            days_elapsed = (last_visit - first_visit) / 1000 / 60 / 60 / 24

            if days_elapsed < 0.001:
                days_elapsed = 0.001

            available_time_minutes = days_elapsed * 24 * 60
            engagement_ratio = total_time_minutes / available_time_minutes
            engagement_ratio_pct = engagement_ratio * 100

            # MÉTRIQUE 2: Taux de lecture moyen
            reading_rates = []

            for i in range(len(timestamps) - 1):
                time_spent_seconds = (timestamps[i+1] - timestamps[i]) / 1000
                time_spent_minutes = time_spent_seconds / 60

                if time_spent_seconds < MIN_READ_TIME_SECONDS:
                    continue
                if time_spent_minutes > MAX_READ_TIME_MINUTES:
                    continue

                words = words_counts[i]
                expected_time_minutes = words / READING_SPEED_WPM

                if expected_time_minutes > 0:
                    reading_rate = time_spent_minutes / expected_time_minutes
                    reading_rates.append(min(reading_rate, 3.0))  # Cap à 3x

            if len(reading_rates) == 0:
                continue

            avg_reading_rate = np.mean(reading_rates)
            median_reading_rate = np.median(reading_rates)

            user_metrics.append({
                'user_id': user_id,
                'engagement_ratio_pct': engagement_ratio_pct,
                'total_time_minutes': total_time_minutes,
                'num_articles': len(timestamps),
                'avg_reading_rate': avg_reading_rate,
                'median_reading_rate': median_reading_rate,
                'num_valid_reads': len(reading_rates)
            })

        df_users = pd.DataFrame(user_metrics)
        print(f"  ✓ {len(df_users):,} utilisateurs avec les deux métriques")

        return df_users

    def analyze_correlation(self, df_users):
        """Analyse la corrélation entre ratio d'engagement et taux de lecture"""
        print("\n" + "="*80)
        print("CORRÉLATION: RATIO D'ENGAGEMENT ↔ TAUX DE LECTURE")
        print("="*80)

        # Corrélation globale
        corr_avg = df_users['engagement_ratio_pct'].corr(df_users['avg_reading_rate'])
        corr_median = df_users['engagement_ratio_pct'].corr(df_users['median_reading_rate'])

        print(f"\n📊 Corrélation Pearson:")
        print(f"  Ratio d'engagement ↔ Taux de lecture moyen:    {corr_avg:.3f}")
        print(f"  Ratio d'engagement ↔ Taux de lecture médian:   {corr_median:.3f}")

        print(f"\nInterprétation:")
        if abs(corr_avg) < 0.1:
            print(f"  → Corrélation TRÈS FAIBLE ({corr_avg:.3f})")
            print(f"  → Le ratio d'engagement et le taux de lecture sont INDÉPENDANTS")
        elif abs(corr_avg) < 0.3:
            print(f"  → Corrélation FAIBLE ({corr_avg:.3f})")
            print(f"  → Lien faible entre les deux métriques")
        elif abs(corr_avg) < 0.5:
            print(f"  → Corrélation MODÉRÉE ({corr_avg:.3f})")
            print(f"  → Les deux métriques sont partiellement liées")
        else:
            print(f"  → Corrélation FORTE ({corr_avg:.3f})")
            print(f"  → Les deux métriques varient ensemble")

        # Segmenter par quartiles de ratio d'engagement
        print("\n" + "="*80)
        print("ANALYSE PAR QUARTILE DE RATIO D'ENGAGEMENT")
        print("="*80)

        # Utiliser des percentiles au lieu de qcut
        q25 = df_users['engagement_ratio_pct'].quantile(0.25)
        q50 = df_users['engagement_ratio_pct'].quantile(0.50)
        q75 = df_users['engagement_ratio_pct'].quantile(0.75)

        def assign_quartile(val):
            if val <= q25:
                return 'Q1 (Faible)'
            elif val <= q50:
                return 'Q2 (Moyen-)'
            elif val <= q75:
                return 'Q3 (Moyen+)'
            else:
                return 'Q4 (Élevé)'

        df_users['engagement_quartile'] = df_users['engagement_ratio_pct'].apply(assign_quartile)

        print(f"\n📊 Taux de lecture moyen par quartile d'engagement:")
        print("")

        for quartile in ['Q1 (Faible)', 'Q2 (Moyen-)', 'Q3 (Moyen+)', 'Q4 (Élevé)']:
            segment = df_users[df_users['engagement_quartile'] == quartile]

            if len(segment) == 0:
                continue

            avg_ratio = segment['engagement_ratio_pct'].mean()
            avg_reading = segment['avg_reading_rate'].mean()
            median_reading = segment['median_reading_rate'].mean()
            avg_articles = segment['num_articles'].mean()

            print(f"  {quartile}:")
            print(f"    Ratio d'engagement:     {avg_ratio:.2f}%")
            print(f"    Taux de lecture moyen:  {avg_reading:.2f}x")
            print(f"    Taux de lecture médian: {median_reading:.2f}x")
            print(f"    Nombre d'articles:      {avg_articles:.1f}")
            print("")

        # Comparer Q1 vs Q4
        q1 = df_users[df_users['engagement_quartile'] == 'Q1 (Faible)']
        q4 = df_users[df_users['engagement_quartile'] == 'Q4 (Élevé)']

        print("="*80)
        print("COMPARAISON: Engagement Faible (Q1) vs Élevé (Q4)")
        print("="*80)

        print(f"\n  Q1 (Engagement Faible):")
        print(f"    Ratio d'engagement:     {q1['engagement_ratio_pct'].mean():.2f}%")
        print(f"    Taux de lecture:        {q1['avg_reading_rate'].mean():.2f}x")

        print(f"\n  Q4 (Engagement Élevé):")
        print(f"    Ratio d'engagement:     {q4['engagement_ratio_pct'].mean():.2f}%")
        print(f"    Taux de lecture:        {q4['avg_reading_rate'].mean():.2f}x")

        ratio_improvement = (q4['engagement_ratio_pct'].mean() / q1['engagement_ratio_pct'].mean() - 1) * 100
        reading_improvement = (q4['avg_reading_rate'].mean() / q1['avg_reading_rate'].mean() - 1) * 100

        print(f"\n  Amélioration Q4 vs Q1:")
        print(f"    Ratio d'engagement:     +{ratio_improvement:.1f}%")
        print(f"    Taux de lecture:        {reading_improvement:+.1f}%")

        if abs(reading_improvement) < 5:
            conclusion = "PAS D'AMÉLIORATION"
            detail = "Le taux de lecture reste stable même avec plus d'engagement"
        elif reading_improvement > 0:
            conclusion = "AMÉLIORATION POSITIVE"
            detail = "Plus d'engagement = meilleure qualité de lecture"
        else:
            conclusion = "DÉGRADATION"
            detail = "Plus d'engagement = lecture plus rapide (survol)"

        print(f"\n  ⚠️  Conclusion: {conclusion}")
        print(f"      {detail}")

        return df_users, corr_avg

    def answer_main_question(self, df_users, corr_avg):
        """Répond à la question principale"""
        print("\n" + "="*80)
        print("RÉPONSE À LA QUESTION PRINCIPALE")
        print("="*80)

        print("""
┌────────────────────────────────────────────────────────────────────────┐
│  QUESTION: Si on augmente le temps passé (+83% avec recommandations),  │
│            est-ce que le TAUX DE LECTURE par article s'améliore aussi? │
└────────────────────────────────────────────────────────────────────────┘
""")

        q1 = df_users[df_users['engagement_quartile'] == 'Q1 (Faible)']
        q4 = df_users[df_users['engagement_quartile'] == 'Q4 (Élevé)']

        reading_diff = q4['avg_reading_rate'].mean() - q1['avg_reading_rate'].mean()

        if abs(corr_avg) < 0.1:
            answer = "NON - Indépendance"
            explanation = """
Les deux métriques sont INDÉPENDANTES (corrélation ≈ 0).

Cela signifie:
  • Augmenter le temps passé N'améliore PAS le taux de lecture
  • Les utilisateurs lisent plus d'articles, mais à la MÊME vitesse
  • L'amélioration est QUANTITATIVE (plus d'articles) pas QUALITATIVE

Hypothèse recommandée pour la présentation:
  ✅ HYPOTHÈSE 1: Même taux de lecture, +83% articles
     → Gain: +83%
"""
        elif corr_avg > 0.3:
            answer = "OUI - Corrélation Positive"
            explanation = f"""
Corrélation positive modérée ({corr_avg:.3f}).

Cela signifie:
  • Augmenter le temps passé AMÉLIORE le taux de lecture
  • Les utilisateurs lisent plus ET mieux
  • L'amélioration est à la fois QUANTITATIVE et QUALITATIVE

Q4 vs Q1: Taux de lecture {reading_diff:+.2f}x

Hypothèse recommandée pour la présentation:
  ✅ HYPOTHÈSE 2: Taux amélioré +20%, +83% articles
     → Gain: +119.6%
"""
        else:
            answer = "FAIBLEMENT - Corrélation Faible"
            explanation = f"""
Corrélation faible ({corr_avg:.3f}).

Cela signifie:
  • Lien faible entre temps passé et taux de lecture
  • L'amélioration est PRINCIPALEMENT quantitative
  • Légère amélioration qualitative possible

Hypothèse recommandée pour la présentation:
  ✅ HYPOTHÈSE 1: Même taux, +83% articles (conservative)
  ⚠️  HYPOTHÈSE 2 possible mais optimiste
"""

        print(f"RÉPONSE: {answer}")
        print(explanation)

        # Recommandation finale
        print("\n" + "="*80)
        print("RECOMMANDATION POUR LA PRÉSENTATION")
        print("="*80)

        if abs(corr_avg) < 0.1:
            print("""
✅ Utilisez HYPOTHÈSE 1 (conservative):
   "Notre système augmente le temps passé de +83%, ce qui se traduit
    par 83% plus d'articles lus par utilisateur, générant +41-46€ de
    revenus supplémentaires pour notre échantillon."

❌ NE PAS utiliser Hypothèse 2:
   Les données ne supportent PAS une amélioration du taux de lecture.
""")
        else:
            print(f"""
✅ Vous POUVEZ utiliser HYPOTHÈSE 2 (avec prudence):
   "Notre système augmente le temps passé de +83%, avec une amélioration
    probable de la qualité d'engagement (corrélation: {corr_avg:.3f}).
    Cela pourrait générer jusqu'à +119.6% de revenus."

⚠️  MAIS restez conservatif:
   Hypothèse 1 (+83%) est plus sûre pour la présentation.
   Hypothèse 2 (+119.6%) est optimiste, utilisez-la en "scénario haut".
""")

        # Sauvegarder résultats
        results = {
            'correlation': float(corr_avg),
            'question': 'Does increasing engagement ratio improve reading rate?',
            'answer': answer,
            'quartile_comparison': {
                'q1_engagement_pct': float(q1['engagement_ratio_pct'].mean()),
                'q1_reading_rate': float(q1['avg_reading_rate'].mean()),
                'q4_engagement_pct': float(q4['engagement_ratio_pct'].mean()),
                'q4_reading_rate': float(q4['avg_reading_rate'].mean()),
                'reading_rate_diff': float(reading_diff)
            },
            'recommendation': 'Hypothesis 1' if abs(corr_avg) < 0.1 else 'Hypothesis 2 (with caution)'
        }

        output_file = OUTPUT_DIR / "correlation_metrics_quality.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        print(f"\n✅ Résultats sauvegardés: {output_file}")

def main():
    analyzer = QualityCorrelationAnalyzer()
    analyzer.load_data()
    df_users = analyzer.calculate_user_metrics()
    df_users, corr_avg = analyzer.analyze_correlation(df_users)
    analyzer.answer_main_question(df_users, corr_avg)

    print("\n" + "="*80)
    print("✅ ANALYSE TERMINÉE")
    print("="*80)

if __name__ == "__main__":
    main()
