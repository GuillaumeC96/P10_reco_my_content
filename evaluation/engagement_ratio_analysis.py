"""
MÉTRIQUE D'ENGAGEMENT: RATIO DU TEMPS PASSÉ

Définition:
    Ratio = Temps passé sur le site / Temps total disponible depuis la première visite

Exemple:
    - Première visite: il y a 31 jours
    - Temps total passé: 24 heures = 1440 minutes
    - Temps disponible: 31 jours × 24h × 60min = 44,640 minutes
    - Ratio = 1440 / 44,640 = 0.0323 = 3.23%

Objectif:
    Augmenter ce ratio grâce au système de recommandation
    → Plus l'utilisateur revient et lit d'articles, plus le ratio augmente
"""

import pandas as pd
import numpy as np
import json
from pathlib import Path
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import seaborn as sns

# Configuration
BASE_DIR = Path(__file__).parent.parent
MODELS_DIR = BASE_DIR / "models"
OUTPUT_DIR = BASE_DIR / "evaluation"

class EngagementRatioAnalyzer:
    """
    Analyse le ratio d'engagement (temps passé / temps disponible)
    """

    def __init__(self, models_path="../models"):
        self.models_path = Path(models_path)
        self.stats_df = None
        self.user_profiles = None

    def load_data(self):
        """Charge les données nécessaires"""
        print("📂 Chargement des données...")

        # Charger les stats d'interactions
        stats_path = self.models_path / "interaction_stats_enriched.csv"
        self.stats_df = pd.read_csv(stats_path)
        print(f"  ✓ {len(self.stats_df):,} interactions chargées")

        # Charger les profils utilisateurs
        profiles_path = self.models_path / "user_profiles_enriched.json"
        with open(profiles_path, 'r') as f:
            self.user_profiles = json.load(f)
        print(f"  ✓ {len(self.user_profiles):,} utilisateurs chargés")

    def calculate_engagement_ratios(self):
        """
        Calcule le ratio d'engagement pour chaque utilisateur

        Ratio = Temps total passé / Temps écoulé depuis première visite

        Returns:
            DataFrame avec les ratios par utilisateur
        """
        print("\n📊 Calcul des ratios d'engagement...")

        # Agréger par utilisateur
        user_metrics = self.stats_df.groupby('user_id').agg({
            'total_time_seconds': 'sum',      # Temps total passé
            'first_click': 'min',              # Première interaction (timestamp)
            'last_click': 'max'                # Dernière interaction (timestamp)
        }).reset_index()

        # Calculer le temps écoulé (en jours) depuis la première visite
        user_metrics['first_click_date'] = pd.to_datetime(user_metrics['first_click'], unit='ms')
        user_metrics['last_click_date'] = pd.to_datetime(user_metrics['last_click'], unit='ms')

        # Temps écoulé = dernière interaction - première interaction
        user_metrics['days_elapsed'] = (user_metrics['last_click_date'] - user_metrics['first_click_date']).dt.total_seconds() / (24 * 3600)

        # Pour éviter division par 0, minimum 1 jour
        user_metrics['days_elapsed'] = user_metrics['days_elapsed'].clip(lower=1.0)

        # Convertir temps passé en minutes
        user_metrics['total_time_minutes'] = user_metrics['total_time_seconds'] / 60.0

        # Temps disponible (en minutes) depuis la première visite
        user_metrics['available_time_minutes'] = user_metrics['days_elapsed'] * 24 * 60

        # RATIO D'ENGAGEMENT = temps passé / temps disponible
        user_metrics['engagement_ratio'] = user_metrics['total_time_minutes'] / user_metrics['available_time_minutes']

        # Ratio en pourcentage
        user_metrics['engagement_ratio_pct'] = user_metrics['engagement_ratio'] * 100

        print(f"\n  Statistiques des ratios d'engagement:")
        print(f"    Moyenne:  {user_metrics['engagement_ratio_pct'].mean():.4f}%")
        print(f"    Médiane:  {user_metrics['engagement_ratio_pct'].median():.4f}%")
        print(f"    Min:      {user_metrics['engagement_ratio_pct'].min():.4f}%")
        print(f"    Max:      {user_metrics['engagement_ratio_pct'].max():.4f}%")
        print(f"    Std:      {user_metrics['engagement_ratio_pct'].std():.4f}%")

        # Quantiles
        print(f"\n  Quantiles:")
        for q in [0.25, 0.5, 0.75, 0.90, 0.95]:
            val = user_metrics['engagement_ratio_pct'].quantile(q)
            print(f"    Q{int(q*100):02d}: {val:.4f}%")

        return user_metrics

    def estimate_baseline_scenario(self, user_metrics):
        """
        Scénario SANS système de recommandation

        On utilise les ratios actuels comme baseline
        """
        print(f"\n💰 SCÉNARIO BASELINE (SANS système de recommandation)")
        print("="*80)

        baseline_stats = {
            'mean_ratio': user_metrics['engagement_ratio'].mean(),
            'median_ratio': user_metrics['engagement_ratio'].median(),
            'mean_ratio_pct': user_metrics['engagement_ratio_pct'].mean(),
            'median_ratio_pct': user_metrics['engagement_ratio_pct'].median(),
            'mean_time_minutes': user_metrics['total_time_minutes'].mean(),
            'mean_days_elapsed': user_metrics['days_elapsed'].mean()
        }

        print(f"\n  Ratio d'engagement moyen:   {baseline_stats['mean_ratio_pct']:.4f}%")
        print(f"  Ratio d'engagement médian:  {baseline_stats['median_ratio_pct']:.4f}%")
        print(f"  Temps moyen passé:          {baseline_stats['mean_time_minutes']:.2f} minutes")
        print(f"  Période moyenne:            {baseline_stats['mean_days_elapsed']:.2f} jours")

        return baseline_stats

    def estimate_with_recommendation_scenario(self, user_metrics, time_increase_pct=83):
        """
        Scénario AVEC système de recommandation

        Hypothèse: Le temps passé augmente de X% grâce aux recommandations
        → Le ratio d'engagement augmente proportionnellement

        Args:
            user_metrics: DataFrame avec les métriques utilisateurs
            time_increase_pct: Augmentation du temps passé en % (défaut: 83%)
        """
        print(f"\n\n💎 SCÉNARIO AVEC SYSTÈME DE RECOMMANDATION")
        print(f"   Augmentation du temps: +{time_increase_pct}%")
        print("="*80)

        # Nouveau temps passé
        user_metrics['new_time_minutes'] = user_metrics['total_time_minutes'] * (1 + time_increase_pct / 100.0)

        # Nouveau ratio (le temps disponible ne change pas)
        user_metrics['new_engagement_ratio'] = user_metrics['new_time_minutes'] / user_metrics['available_time_minutes']
        user_metrics['new_engagement_ratio_pct'] = user_metrics['new_engagement_ratio'] * 100

        reco_stats = {
            'mean_ratio': user_metrics['new_engagement_ratio'].mean(),
            'median_ratio': user_metrics['new_engagement_ratio'].median(),
            'mean_ratio_pct': user_metrics['new_engagement_ratio_pct'].mean(),
            'median_ratio_pct': user_metrics['new_engagement_ratio_pct'].median(),
            'mean_time_minutes': user_metrics['new_time_minutes'].mean(),
            'mean_days_elapsed': user_metrics['days_elapsed'].mean()
        }

        print(f"\n  Ratio d'engagement moyen:   {reco_stats['mean_ratio_pct']:.4f}%")
        print(f"  Ratio d'engagement médian:  {reco_stats['median_ratio_pct']:.4f}%")
        print(f"  Temps moyen passé:          {reco_stats['mean_time_minutes']:.2f} minutes")
        print(f"  Période moyenne:            {reco_stats['mean_days_elapsed']:.2f} jours")

        return reco_stats

    def compare_scenarios(self, baseline_stats, reco_stats):
        """
        Compare les deux scénarios
        """
        print(f"\n\n📈 COMPARAISON DES SCÉNARIOS")
        print("="*80)

        # Gains absolus
        gain_ratio_pct = reco_stats['mean_ratio_pct'] - baseline_stats['mean_ratio_pct']
        gain_time_minutes = reco_stats['mean_time_minutes'] - baseline_stats['mean_time_minutes']

        # Gains relatifs
        gain_ratio_relative = (gain_ratio_pct / baseline_stats['mean_ratio_pct']) * 100
        gain_time_relative = (gain_time_minutes / baseline_stats['mean_time_minutes']) * 100

        comparison = {
            'baseline_ratio_pct': baseline_stats['mean_ratio_pct'],
            'reco_ratio_pct': reco_stats['mean_ratio_pct'],
            'gain_ratio_pct_absolute': gain_ratio_pct,
            'gain_ratio_pct_relative': gain_ratio_relative,
            'baseline_time': baseline_stats['mean_time_minutes'],
            'reco_time': reco_stats['mean_time_minutes'],
            'gain_time_absolute': gain_time_minutes,
            'gain_time_relative': gain_time_relative
        }

        print(f"\n  📊 RATIO D'ENGAGEMENT:")
        print(f"     SANS reco: {baseline_stats['mean_ratio_pct']:.4f}%")
        print(f"     AVEC reco: {reco_stats['mean_ratio_pct']:.4f}%")
        print(f"     GAIN:      +{gain_ratio_pct:.4f} points (+{gain_ratio_relative:.1f}%)")

        print(f"\n  ⏱️  TEMPS PASSÉ:")
        print(f"     SANS reco: {baseline_stats['mean_time_minutes']:.2f} minutes")
        print(f"     AVEC reco: {reco_stats['mean_time_minutes']:.2f} minutes")
        print(f"     GAIN:      +{gain_time_minutes:.2f} minutes (+{gain_time_relative:.1f}%)")

        return comparison

    def calculate_revenue_impact(self, user_metrics, baseline_stats, reco_stats, cpm_popup=6.0, popup_interval_minutes=3.55):
        """
        Calcule l'impact sur les revenus basé sur le temps passé

        Args:
            user_metrics: DataFrame avec les métriques
            baseline_stats: Stats du scénario baseline
            reco_stats: Stats du scénario avec reco
            cpm_popup: CPM des pubs pop-up (défaut: 6€)
            popup_interval_minutes: Intervalle entre pubs (défaut: 3.55 min pour N2)
        """
        print(f"\n\n💰 IMPACT SUR LES REVENUS")
        print(f"   CPM pop-up: {cpm_popup}€")
        print(f"   Fréquence: 1 pub toutes les {popup_interval_minutes:.2f} minutes")
        print("="*80)

        num_users = len(user_metrics)

        # Baseline: revenus par utilisateur
        baseline_pubs_per_user = baseline_stats['mean_time_minutes'] / popup_interval_minutes
        baseline_revenue_per_user = (baseline_pubs_per_user / 1000.0) * cpm_popup

        # Avec reco: revenus par utilisateur
        reco_pubs_per_user = reco_stats['mean_time_minutes'] / popup_interval_minutes
        reco_revenue_per_user = (reco_pubs_per_user / 1000.0) * cpm_popup

        # Revenus totaux
        baseline_revenue_total = baseline_revenue_per_user * num_users
        reco_revenue_total = reco_revenue_per_user * num_users

        # Gain
        gain_revenue = reco_revenue_total - baseline_revenue_total
        gain_revenue_pct = (gain_revenue / baseline_revenue_total) * 100

        revenue_impact = {
            'cpm_popup': cpm_popup,
            'popup_interval_minutes': popup_interval_minutes,
            'num_users': num_users,
            'baseline_pubs_per_user': baseline_pubs_per_user,
            'baseline_revenue_per_user': baseline_revenue_per_user,
            'baseline_revenue_total': baseline_revenue_total,
            'reco_pubs_per_user': reco_pubs_per_user,
            'reco_revenue_per_user': reco_revenue_per_user,
            'reco_revenue_total': reco_revenue_total,
            'gain_revenue': gain_revenue,
            'gain_revenue_pct': gain_revenue_pct
        }

        print(f"\n  Pour {num_users:,} utilisateurs:")
        print(f"\n  SANS reco:")
        print(f"     Pubs/user:        {baseline_pubs_per_user:.2f}")
        print(f"     Revenu/user:      {baseline_revenue_per_user:.6f} €")
        print(f"     Revenu TOTAL:     {baseline_revenue_total:.2f} €")

        print(f"\n  AVEC reco:")
        print(f"     Pubs/user:        {reco_pubs_per_user:.2f}")
        print(f"     Revenu/user:      {reco_revenue_per_user:.6f} €")
        print(f"     Revenu TOTAL:     {reco_revenue_total:.2f} €")

        print(f"\n  GAIN:")
        print(f"     +{gain_revenue:.2f} € (+{gain_revenue_pct:.1f}%)")

        return revenue_impact

    def create_visualizations(self, user_metrics, baseline_stats, reco_stats):
        """
        Crée des visualisations
        """
        print(f"\n\n📊 Création des visualisations...")

        fig, axes = plt.subplots(2, 2, figsize=(16, 12))

        # Graphique 1: Distribution des ratios (AVANT)
        ax1 = axes[0, 0]
        ax1.hist(user_metrics['engagement_ratio_pct'], bins=50, alpha=0.7, color='blue', edgecolor='black')
        ax1.axvline(baseline_stats['mean_ratio_pct'], color='red', linestyle='--', linewidth=2, label=f'Moyenne: {baseline_stats["mean_ratio_pct"]:.4f}%')
        ax1.axvline(baseline_stats['median_ratio_pct'], color='green', linestyle='--', linewidth=2, label=f'Médiane: {baseline_stats["median_ratio_pct"]:.4f}%')
        ax1.set_xlabel('Ratio d\'engagement (%)', fontsize=12)
        ax1.set_ylabel('Nombre d\'utilisateurs', fontsize=12)
        ax1.set_title('Distribution des Ratios d\'Engagement (SANS recommandation)', fontsize=14, fontweight='bold')
        ax1.legend(fontsize=10)
        ax1.grid(axis='y', alpha=0.3)

        # Graphique 2: Distribution des ratios (APRÈS)
        ax2 = axes[0, 1]
        ax2.hist(user_metrics['new_engagement_ratio_pct'], bins=50, alpha=0.7, color='orange', edgecolor='black')
        ax2.axvline(reco_stats['mean_ratio_pct'], color='red', linestyle='--', linewidth=2, label=f'Moyenne: {reco_stats["mean_ratio_pct"]:.4f}%')
        ax2.axvline(reco_stats['median_ratio_pct'], color='green', linestyle='--', linewidth=2, label=f'Médiane: {reco_stats["median_ratio_pct"]:.4f}%')
        ax2.set_xlabel('Ratio d\'engagement (%)', fontsize=12)
        ax2.set_ylabel('Nombre d\'utilisateurs', fontsize=12)
        ax2.set_title('Distribution des Ratios d\'Engagement (AVEC recommandation)', fontsize=14, fontweight='bold')
        ax2.legend(fontsize=10)
        ax2.grid(axis='y', alpha=0.3)

        # Graphique 3: Comparaison AVANT/APRÈS
        ax3 = axes[1, 0]
        categories = ['SANS reco', 'AVEC reco']
        means = [baseline_stats['mean_ratio_pct'], reco_stats['mean_ratio_pct']]
        colors = ['blue', 'orange']
        bars = ax3.bar(categories, means, color=colors, alpha=0.7, edgecolor='black')
        ax3.set_ylabel('Ratio d\'engagement moyen (%)', fontsize=12)
        ax3.set_title('Comparaison des Ratios d\'Engagement', fontsize=14, fontweight='bold')
        ax3.grid(axis='y', alpha=0.3)

        # Ajouter les valeurs sur les barres
        for bar in bars:
            height = bar.get_height()
            ax3.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.4f}%',
                    ha='center', va='bottom', fontsize=11, fontweight='bold')

        # Graphique 4: Temps passé AVANT/APRÈS
        ax4 = axes[1, 1]
        times = [baseline_stats['mean_time_minutes'], reco_stats['mean_time_minutes']]
        bars2 = ax4.bar(categories, times, color=colors, alpha=0.7, edgecolor='black')
        ax4.set_ylabel('Temps moyen passé (minutes)', fontsize=12)
        ax4.set_title('Comparaison du Temps Passé', fontsize=14, fontweight='bold')
        ax4.grid(axis='y', alpha=0.3)

        # Ajouter les valeurs sur les barres
        for bar in bars2:
            height = bar.get_height()
            ax4.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.2f} min',
                    ha='center', va='bottom', fontsize=11, fontweight='bold')

        plt.tight_layout()

        # Sauvegarder
        output_path = OUTPUT_DIR / "engagement_ratio_analysis.png"
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"  ✓ Graphiques sauvegardés: {output_path}")

        plt.close()

    def save_results(self, user_metrics, baseline_stats, reco_stats, comparison, revenue_impact):
        """
        Sauvegarde les résultats
        """
        print(f"\n💾 Sauvegarde des résultats...")

        results = {
            'metric': 'engagement_ratio',
            'definition': 'Temps passé / Temps disponible depuis première visite',
            'num_users': len(user_metrics),
            'baseline_scenario': baseline_stats,
            'recommendation_scenario': reco_stats,
            'comparison': comparison,
            'revenue_impact': revenue_impact,
            'user_metrics_summary': {
                'mean_ratio_pct': float(user_metrics['engagement_ratio_pct'].mean()),
                'median_ratio_pct': float(user_metrics['engagement_ratio_pct'].median()),
                'std_ratio_pct': float(user_metrics['engagement_ratio_pct'].std()),
                'min_ratio_pct': float(user_metrics['engagement_ratio_pct'].min()),
                'max_ratio_pct': float(user_metrics['engagement_ratio_pct'].max())
            }
        }

        # Convertir les numpy types en types Python natifs
        def convert_to_native(obj):
            if isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, dict):
                return {k: convert_to_native(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_to_native(i) for i in obj]
            return obj

        results = convert_to_native(results)

        output_path = OUTPUT_DIR / "engagement_ratio_results.json"
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)

        print(f"  ✓ Résultats sauvegardés: {output_path}")

    def run_full_analysis(self, time_increase_pct=83, popup_interval_minutes=3.55):
        """
        Lance l'analyse complète
        """
        print("\n" + "="*80)
        print("ANALYSE DU RATIO D'ENGAGEMENT")
        print("="*80)

        # Charger les données
        self.load_data()

        # Calculer les ratios
        user_metrics = self.calculate_engagement_ratios()

        # Scénario baseline
        baseline_stats = self.estimate_baseline_scenario(user_metrics)

        # Scénario avec recommandation
        reco_stats = self.estimate_with_recommendation_scenario(user_metrics, time_increase_pct)

        # Comparer
        comparison = self.compare_scenarios(baseline_stats, reco_stats)

        # Impact revenus
        revenue_impact = self.calculate_revenue_impact(
            user_metrics, baseline_stats, reco_stats,
            popup_interval_minutes=popup_interval_minutes
        )

        # Visualisations
        self.create_visualizations(user_metrics, baseline_stats, reco_stats)

        # Sauvegarder
        self.save_results(user_metrics, baseline_stats, reco_stats, comparison, revenue_impact)

        print("\n" + "="*80)
        print("✅ ANALYSE TERMINÉE")
        print("="*80)

        return user_metrics, baseline_stats, reco_stats, comparison, revenue_impact


def main():
    """
    Point d'entrée principal
    """
    analyzer = EngagementRatioAnalyzer(models_path="../models")
    user_metrics, baseline, reco, comparison, revenue = analyzer.run_full_analysis(
        time_increase_pct=83,
        popup_interval_minutes=3.55  # N2
    )

    # Afficher le résumé final
    print("\n\n📋 RÉSUMÉ EXÉCUTIF")
    print("="*80)
    print(f"\nMÉTRIQUE: Ratio d'Engagement")
    print(f"  Définition: Temps passé / Temps disponible depuis première visite")
    print(f"  Utilisateurs analysés: {len(user_metrics):,}")

    print(f"\n\nRÉSULTATS:")
    print(f"  SANS recommandation:")
    print(f"    Ratio moyen: {baseline['mean_ratio_pct']:.4f}%")
    print(f"    Temps moyen: {baseline['mean_time_minutes']:.2f} minutes")

    print(f"\n  AVEC recommandation (+83% temps):")
    print(f"    Ratio moyen: {reco['mean_ratio_pct']:.4f}%")
    print(f"    Temps moyen: {reco['mean_time_minutes']:.2f} minutes")

    print(f"\n  GAIN:")
    print(f"    Ratio: +{comparison['gain_ratio_pct_absolute']:.4f} points (+{comparison['gain_ratio_pct_relative']:.1f}%)")
    print(f"    Temps: +{comparison['gain_time_absolute']:.2f} minutes (+{comparison['gain_time_relative']:.1f}%)")

    print(f"\n\nIMPACT REVENUS (pubs pop-up, fréquence N2):")
    print(f"  SANS reco: {revenue['baseline_revenue_total']:.2f}€")
    print(f"  AVEC reco: {revenue['reco_revenue_total']:.2f}€")
    print(f"  GAIN: +{revenue['gain_revenue']:.2f}€ (+{revenue['gain_revenue_pct']:.1f}%)")


if __name__ == "__main__":
    main()
