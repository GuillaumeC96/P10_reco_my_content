"""
ANALYSE DU RATIO D'ENGAGEMENT - BASÉE SUR LA MÉDIANE

Version corrigée: Utilise la MÉDIANE au lieu de la MOYENNE
→ Plus représentative de l'utilisateur typique
→ Pas biaisée par les power users (valeurs extrêmes)
"""

import pandas as pd
import numpy as np
import json
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns

BASE_DIR = Path(__file__).parent.parent
MODELS_DIR = BASE_DIR / "models"
OUTPUT_DIR = BASE_DIR / "evaluation"

class MedianEngagementRatioAnalyzer:
    """
    Analyse basée sur la MÉDIANE (utilisateur typique)
    """

    def __init__(self, models_path="../models"):
        self.models_path = Path(models_path)
        self.stats_df = None

    def load_data(self):
        """Charge les données"""
        print("📂 Chargement des données...")
        stats_path = self.models_path / "interaction_stats_enriched.csv"
        self.stats_df = pd.read_csv(stats_path)
        print(f"  ✓ {len(self.stats_df):,} interactions chargées")

    def calculate_engagement_ratios(self):
        """Calcule les ratios d'engagement par utilisateur"""
        print("\n📊 Calcul des ratios d'engagement...")

        user_metrics = self.stats_df.groupby('user_id').agg({
            'total_time_seconds': 'sum',
            'first_click': 'min',
            'last_click': 'max'
        }).reset_index()

        user_metrics['first_click_date'] = pd.to_datetime(user_metrics['first_click'], unit='ms')
        user_metrics['last_click_date'] = pd.to_datetime(user_metrics['last_click'], unit='ms')
        user_metrics['days_elapsed'] = (user_metrics['last_click_date'] - user_metrics['first_click_date']).dt.total_seconds() / (24 * 3600)
        user_metrics['days_elapsed'] = user_metrics['days_elapsed'].clip(lower=1.0)
        user_metrics['total_time_minutes'] = user_metrics['total_time_seconds'] / 60.0
        user_metrics['available_time_minutes'] = user_metrics['days_elapsed'] * 24 * 60
        user_metrics['engagement_ratio'] = user_metrics['total_time_minutes'] / user_metrics['available_time_minutes']
        user_metrics['engagement_ratio_pct'] = user_metrics['engagement_ratio'] * 100

        print(f"\n  📊 Statistiques des ratios (FOCUS SUR LA MÉDIANE):")
        print(f"    Moyenne:  {user_metrics['engagement_ratio_pct'].mean():.4f}% (⚠️  biaisée par outliers)")
        print(f"    Médiane:  {user_metrics['engagement_ratio_pct'].median():.4f}% ⭐ UTILISATEUR TYPIQUE")
        print(f"    Min:      {user_metrics['engagement_ratio_pct'].min():.4f}%")
        print(f"    Max:      {user_metrics['engagement_ratio_pct'].max():.4f}%")

        return user_metrics

    def analyze_with_median(self, user_metrics, time_increase_pct=83, popup_interval_minutes=3.55, cpm=6.0):
        """
        Analyse complète basée sur la MÉDIANE
        """
        print(f"\n\n{'='*80}")
        print("ANALYSE BASÉE SUR L'UTILISATEUR MÉDIAN (TYPIQUE)")
        print(f"{'='*80}")

        # Métriques médianes (utilisateur typique)
        median_ratio_baseline = user_metrics['engagement_ratio_pct'].median()
        median_time_baseline = user_metrics['total_time_minutes'].median()
        median_days = user_metrics['days_elapsed'].median()

        print(f"\n📊 UTILISATEUR TYPIQUE (MÉDIANE) - BASELINE:")
        print(f"   Ratio d'engagement:  {median_ratio_baseline:.4f}%")
        print(f"   Temps passé:         {median_time_baseline:.2f} minutes")
        print(f"   Jours écoulés:       {median_days:.2f} jours")

        # Avec recommandation
        median_time_reco = median_time_baseline * (1 + time_increase_pct / 100)
        median_ratio_reco = median_ratio_baseline * (1 + time_increase_pct / 100)

        print(f"\n💎 UTILISATEUR TYPIQUE (MÉDIANE) - AVEC RECO (+{time_increase_pct}%):")
        print(f"   Ratio d'engagement:  {median_ratio_reco:.4f}%")
        print(f"   Temps passé:         {median_time_reco:.2f} minutes")
        print(f"   Jours écoulés:       {median_days:.2f} jours (inchangé)")

        # Gains
        gain_ratio = median_ratio_reco - median_ratio_baseline
        gain_time = median_time_reco - median_time_baseline

        print(f"\n📈 GAINS POUR L'UTILISATEUR TYPIQUE:")
        print(f"   Ratio: +{gain_ratio:.4f} points (+{time_increase_pct}%)")
        print(f"   Temps: +{gain_time:.2f} minutes (+{time_increase_pct}%)")

        # Revenus pour l'utilisateur médian
        num_users = len(user_metrics)

        # Baseline
        baseline_pubs = median_time_baseline / popup_interval_minutes
        baseline_revenue_per_user = (baseline_pubs / 1000) * cpm

        # Avec reco
        reco_pubs = median_time_reco / popup_interval_minutes
        reco_revenue_per_user = (reco_pubs / 1000) * cpm

        # Revenus totaux (si tous les users sont comme le médian)
        baseline_revenue_total = baseline_revenue_per_user * num_users
        reco_revenue_total = reco_revenue_per_user * num_users
        gain_revenue = reco_revenue_total - baseline_revenue_total
        gain_revenue_pct = (gain_revenue / baseline_revenue_total) * 100

        print(f"\n💰 REVENUS (basés sur l'utilisateur médian)")
        print(f"   Fréquence des pubs: 1 toutes les {popup_interval_minutes:.2f} minutes")
        print(f"   CPM: {cpm}€")
        print(f"   Nombre d'utilisateurs: {num_users:,}")

        print(f"\n   SANS reco (médiane):")
        print(f"     Pubs/user:        {baseline_pubs:.2f}")
        print(f"     Revenu/user:      {baseline_revenue_per_user:.6f}€")
        print(f"     Revenu TOTAL:     {baseline_revenue_total:.2f}€")

        print(f"\n   AVEC reco (médiane):")
        print(f"     Pubs/user:        {reco_pubs:.2f}")
        print(f"     Revenu/user:      {reco_revenue_per_user:.6f}€")
        print(f"     Revenu TOTAL:     {reco_revenue_total:.2f}€")

        print(f"\n   GAIN:")
        print(f"     +{gain_revenue:.2f}€ (+{gain_revenue_pct:.1f}%)")

        results = {
            'metric': 'engagement_ratio_median',
            'definition': 'Basé sur la MÉDIANE (utilisateur typique)',
            'num_users': num_users,
            'popup_interval_minutes': popup_interval_minutes,
            'cpm': cpm,
            'baseline': {
                'median_ratio_pct': float(median_ratio_baseline),
                'median_time_minutes': float(median_time_baseline),
                'median_days_elapsed': float(median_days),
                'pubs_per_user': float(baseline_pubs),
                'revenue_per_user': float(baseline_revenue_per_user),
                'revenue_total': float(baseline_revenue_total)
            },
            'with_recommendation': {
                'median_ratio_pct': float(median_ratio_reco),
                'median_time_minutes': float(median_time_reco),
                'median_days_elapsed': float(median_days),
                'pubs_per_user': float(reco_pubs),
                'revenue_per_user': float(reco_revenue_per_user),
                'revenue_total': float(reco_revenue_total)
            },
            'gains': {
                'ratio_points': float(gain_ratio),
                'time_minutes': float(gain_time),
                'revenue_euros': float(gain_revenue),
                'revenue_pct': float(gain_revenue_pct)
            }
        }

        return results

    def create_comparison_chart(self, results):
        """Crée un graphique comparatif simple"""
        print(f"\n📊 Création du graphique...")

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

        # Graphique 1: Ratio d'engagement
        categories = ['SANS reco\n(médiane)', 'AVEC reco\n(médiane)']
        ratios = [
            results['baseline']['median_ratio_pct'],
            results['with_recommendation']['median_ratio_pct']
        ]
        colors = ['#3498db', '#e74c3c']

        bars1 = ax1.bar(categories, ratios, color=colors, alpha=0.8, edgecolor='black', linewidth=2)
        ax1.set_ylabel('Ratio d\'engagement (%)', fontsize=12, fontweight='bold')
        ax1.set_title('Ratio d\'Engagement (Utilisateur Médian)', fontsize=14, fontweight='bold')
        ax1.grid(axis='y', alpha=0.3)

        for bar in bars1:
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.4f}%',
                    ha='center', va='bottom', fontsize=12, fontweight='bold')

        # Graphique 2: Revenus totaux
        revenues = [
            results['baseline']['revenue_total'],
            results['with_recommendation']['revenue_total']
        ]

        bars2 = ax2.bar(categories, revenues, color=colors, alpha=0.8, edgecolor='black', linewidth=2)
        ax2.set_ylabel('Revenus totaux (€)', fontsize=12, fontweight='bold')
        ax2.set_title(f'Revenus Totaux ({results["num_users"]:,} utilisateurs)', fontsize=14, fontweight='bold')
        ax2.grid(axis='y', alpha=0.3)

        for bar in bars2:
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.0f}€',
                    ha='center', va='bottom', fontsize=12, fontweight='bold')

        plt.tight_layout()

        output_path = OUTPUT_DIR / "engagement_ratio_median_comparison.png"
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"  ✓ Graphique sauvegardé: {output_path}")
        plt.close()

    def save_results(self, results):
        """Sauvegarde les résultats"""
        print(f"\n💾 Sauvegarde des résultats...")
        output_path = OUTPUT_DIR / "engagement_ratio_median_results.json"
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"  ✓ Résultats sauvegardés: {output_path}")

    def run_analysis(self, time_increase_pct=83, popup_interval_minutes=3.55):
        """Lance l'analyse complète"""
        print("\n" + "="*80)
        print("ANALYSE RATIO D'ENGAGEMENT - VERSION MÉDIANE")
        print("="*80)

        self.load_data()
        user_metrics = self.calculate_engagement_ratios()
        results = self.analyze_with_median(
            user_metrics,
            time_increase_pct=time_increase_pct,
            popup_interval_minutes=popup_interval_minutes
        )
        self.create_comparison_chart(results)
        self.save_results(results)

        print("\n" + "="*80)
        print("✅ ANALYSE TERMINÉE (VERSION MÉDIANE)")
        print("="*80)

        return results


def main():
    analyzer = MedianEngagementRatioAnalyzer(models_path="../models")
    results = analyzer.run_analysis(
        time_increase_pct=83,
        popup_interval_minutes=3.55
    )

    print("\n\n📋 RÉSUMÉ EXÉCUTIF (UTILISATEUR MÉDIAN)")
    print("="*80)
    print(f"\nMÉTRIQUE: Ratio d'Engagement (Médiane)")
    print(f"  Utilisateurs analysés: {results['num_users']:,}")

    print(f"\n\nUTILISATEUR TYPIQUE (MÉDIANE):")
    print(f"  SANS recommandation:")
    print(f"    Ratio:   {results['baseline']['median_ratio_pct']:.4f}%")
    print(f"    Temps:   {results['baseline']['median_time_minutes']:.2f} minutes")
    print(f"    Revenu:  {results['baseline']['revenue_per_user']:.6f}€/user")

    print(f"\n  AVEC recommandation (+83% temps):")
    print(f"    Ratio:   {results['with_recommendation']['median_ratio_pct']:.4f}%")
    print(f"    Temps:   {results['with_recommendation']['median_time_minutes']:.2f} minutes")
    print(f"    Revenu:  {results['with_recommendation']['revenue_per_user']:.6f}€/user")

    print(f"\n\nREVENUS TOTAUX ({results['num_users']:,} utilisateurs):")
    print(f"  SANS reco: {results['baseline']['revenue_total']:.2f}€")
    print(f"  AVEC reco: {results['with_recommendation']['revenue_total']:.2f}€")
    print(f"  GAIN:      +{results['gains']['revenue_euros']:.2f}€ (+{results['gains']['revenue_pct']:.1f}%)")

    print(f"\n\n💡 INTERPRÉTATION:")
    print(f"  L'utilisateur TYPIQUE (médiane) passe {results['baseline']['median_ratio_pct']:.4f}%")
    print(f"  de son temps disponible sur le site.")
    print(f"  Avec le système de recommandation, ce ratio passe à {results['with_recommendation']['median_ratio_pct']:.4f}%")


if __name__ == "__main__":
    main()
