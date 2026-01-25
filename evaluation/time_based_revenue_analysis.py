"""
NOUVELLE MÉTRIQUE: REVENUS BASÉS SUR LE TEMPS PASSÉ

Au lieu de calculer les revenus basés sur le CPM d'articles lus,
on calcule maintenant les revenus basés sur:
- Le TEMPS PASSÉ par l'utilisateur
- Des publicités pop-up affichées à intervalle régulier (N1, N2, N3, N4 minutes)
- CPM de 6€ pour ces pubs pop-up

Objectif: Comparer le CA SANS système de reco VS AVEC système de reco
          pour différentes fréquences de pub (N1, N2, N3, N4)
          où Nx = quantiles des durées de session
"""

import pandas as pd
import numpy as np
import json
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns

# Configuration
BASE_DIR = Path(__file__).parent.parent
MODELS_DIR = BASE_DIR / "models"
OUTPUT_DIR = BASE_DIR / "evaluation"

# Paramètres de la métrique
CPM_POPUP = 6.0  # €/1000 impressions pour les pubs pop-up

class TimeBasedRevenueAnalyzer:
    """
    Analyse les revenus basés sur le temps passé et les pubs pop-up
    """

    def __init__(self, models_path="../models"):
        self.models_path = Path(models_path)
        self.stats_df = None
        self.user_profiles = None
        self.quantiles = None

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

    def calculate_session_quantiles(self):
        """
        Calcule les quantiles des durées de session pour définir N1, N2, N3, N4
        """
        print("\n📊 Calcul des quantiles des durées de session...")

        # Calculer le temps total par utilisateur (somme de toutes les interactions)
        user_times = self.stats_df.groupby('user_id')['total_time_seconds'].sum()
        user_times_minutes = user_times / 60.0

        # Calculer les quantiles
        self.quantiles = {
            'N1_Q25': user_times_minutes.quantile(0.25),
            'N2_Q50': user_times_minutes.quantile(0.50),
            'N3_Q75': user_times_minutes.quantile(0.75),
            'N4_Q90': user_times_minutes.quantile(0.90)
        }

        print("\n  Quantiles des durées de session (temps total par utilisateur):")
        print(f"    N1 (Q25): {self.quantiles['N1_Q25']:.2f} minutes")
        print(f"    N2 (Q50): {self.quantiles['N2_Q50']:.2f} minutes")
        print(f"    N3 (Q75): {self.quantiles['N3_Q75']:.2f} minutes")
        print(f"    N4 (Q90): {self.quantiles['N4_Q90']:.2f} minutes")

        print(f"\n  Statistiques des durées de session:")
        print(f"    Moyenne: {user_times_minutes.mean():.2f} minutes")
        print(f"    Médiane: {user_times_minutes.median():.2f} minutes")
        print(f"    Écart-type: {user_times_minutes.std():.2f} minutes")
        print(f"    Min: {user_times_minutes.min():.2f} minutes")
        print(f"    Max: {user_times_minutes.max():.2f} minutes")

        return self.quantiles

    def calculate_popup_revenue(self, session_time_minutes, popup_interval_minutes):
        """
        Calcule le revenu généré par les pubs pop-up pour une session

        Args:
            session_time_minutes: Durée de la session en minutes
            popup_interval_minutes: Intervalle entre chaque pub (N1, N2, N3, ou N4)

        Returns:
            Revenu en euros pour cette session
        """
        if popup_interval_minutes == 0:
            return 0.0

        # Nombre de pubs affichées = durée / intervalle
        num_popups = session_time_minutes / popup_interval_minutes

        # Revenu = (nombre de pubs / 1000) * CPM
        revenue = (num_popups / 1000.0) * CPM_POPUP

        return revenue

    def estimate_baseline_scenario(self, num_sessions=100000):
        """
        Estime le CA SANS système de recommandation

        Scénario baseline:
        - Les utilisateurs passent leur temps normal (distribution actuelle)
        - Pas d'augmentation du temps passé

        Args:
            num_sessions: Nombre de sessions à simuler (défaut: 100,000)

        Returns:
            Dict avec les revenus pour chaque fréquence de pub
        """
        print(f"\n💰 SCÉNARIO BASELINE (SANS système de recommandation)")
        print(f"   {num_sessions:,} sessions simulées")
        print("="*80)

        # Calculer le temps total par utilisateur
        user_times = self.stats_df.groupby('user_id')['total_time_seconds'].sum()
        user_times_minutes = user_times / 60.0

        # Temps moyen par session
        avg_session_time = user_times_minutes.mean()

        print(f"\n  Temps moyen par session: {avg_session_time:.2f} minutes")

        results = {}

        for name, interval in [
            ('N1_Q25', self.quantiles['N1_Q25']),
            ('N2_Q50', self.quantiles['N2_Q50']),
            ('N3_Q75', self.quantiles['N3_Q75']),
            ('N4_Q90', self.quantiles['N4_Q90'])
        ]:
            # Calculer le revenu moyen par session
            avg_revenue_per_session = self.calculate_popup_revenue(avg_session_time, interval)

            # Calculer le revenu total
            total_revenue = avg_revenue_per_session * num_sessions

            results[name] = {
                'interval_minutes': interval,
                'avg_session_time_minutes': avg_session_time,
                'avg_popups_per_session': avg_session_time / interval if interval > 0 else 0,
                'avg_revenue_per_session': avg_revenue_per_session,
                'total_revenue': total_revenue
            }

            print(f"\n  📊 {name}: 1 pub toutes les {interval:.2f} minutes")
            print(f"     Pubs/session: {results[name]['avg_popups_per_session']:.2f}")
            print(f"     Revenu/session: {avg_revenue_per_session:.4f} €")
            print(f"     REVENU TOTAL: {total_revenue:.2f} €/an")

        return results

    def estimate_with_recommendation_scenario(self, num_sessions=100000, time_increase_pct=83):
        """
        Estime le CA AVEC système de recommandation

        Scénario avec recommandation:
        - Les utilisateurs passent +83% de temps (baseline: 1 → 1.83 articles)
        - Le temps passé augmente proportionnellement

        Args:
            num_sessions: Nombre de sessions à simuler (défaut: 100,000)
            time_increase_pct: Augmentation du temps passé en % (défaut: 83%)

        Returns:
            Dict avec les revenus pour chaque fréquence de pub
        """
        print(f"\n\n💎 SCÉNARIO AVEC SYSTÈME DE RECOMMANDATION")
        print(f"   {num_sessions:,} sessions simulées")
        print(f"   Augmentation du temps: +{time_increase_pct}%")
        print("="*80)

        # Calculer le temps total par utilisateur
        user_times = self.stats_df.groupby('user_id')['total_time_seconds'].sum()
        user_times_minutes = user_times / 60.0

        # Temps moyen par session AVEC recommandation
        avg_session_time_base = user_times_minutes.mean()
        avg_session_time_with_reco = avg_session_time_base * (1 + time_increase_pct / 100.0)

        print(f"\n  Temps moyen par session (baseline): {avg_session_time_base:.2f} minutes")
        print(f"  Temps moyen par session (avec reco): {avg_session_time_with_reco:.2f} minutes")
        print(f"  Gain de temps: +{avg_session_time_with_reco - avg_session_time_base:.2f} minutes ({time_increase_pct}%)")

        results = {}

        for name, interval in [
            ('N1_Q25', self.quantiles['N1_Q25']),
            ('N2_Q50', self.quantiles['N2_Q50']),
            ('N3_Q75', self.quantiles['N3_Q75']),
            ('N4_Q90', self.quantiles['N4_Q90'])
        ]:
            # Calculer le revenu moyen par session AVEC recommandation
            avg_revenue_per_session = self.calculate_popup_revenue(avg_session_time_with_reco, interval)

            # Calculer le revenu total
            total_revenue = avg_revenue_per_session * num_sessions

            results[name] = {
                'interval_minutes': interval,
                'avg_session_time_minutes': avg_session_time_with_reco,
                'avg_popups_per_session': avg_session_time_with_reco / interval if interval > 0 else 0,
                'avg_revenue_per_session': avg_revenue_per_session,
                'total_revenue': total_revenue
            }

            print(f"\n  📊 {name}: 1 pub toutes les {interval:.2f} minutes")
            print(f"     Pubs/session: {results[name]['avg_popups_per_session']:.2f}")
            print(f"     Revenu/session: {avg_revenue_per_session:.4f} €")
            print(f"     REVENU TOTAL: {total_revenue:.2f} €/an")

        return results

    def compare_scenarios(self, baseline_results, reco_results, num_sessions=100000):
        """
        Compare les deux scénarios et calcule les gains
        """
        print(f"\n\n📈 COMPARAISON DES SCÉNARIOS")
        print("="*80)

        comparison = {}

        for name in baseline_results.keys():
            baseline = baseline_results[name]
            reco = reco_results[name]

            gain_revenue = reco['total_revenue'] - baseline['total_revenue']
            gain_pct = (gain_revenue / baseline['total_revenue']) * 100 if baseline['total_revenue'] > 0 else 0

            comparison[name] = {
                'interval_minutes': baseline['interval_minutes'],
                'baseline_revenue': baseline['total_revenue'],
                'reco_revenue': reco['total_revenue'],
                'gain_revenue': gain_revenue,
                'gain_pct': gain_pct
            }

            print(f"\n  🎯 {name}: 1 pub toutes les {baseline['interval_minutes']:.2f} minutes")
            print(f"     SANS reco: {baseline['total_revenue']:.2f} €")
            print(f"     AVEC reco: {reco['total_revenue']:.2f} €")
            print(f"     GAIN:      +{gain_revenue:.2f} € (+{gain_pct:.1f}%)")

        return comparison

    def create_visualization(self, baseline_results, reco_results, comparison):
        """
        Crée des visualisations pour comparer les scénarios
        """
        print(f"\n\n📊 Création des visualisations...")

        # Préparer les données pour le graphique
        scenarios = []
        intervals = []
        revenues = []
        types = []

        for name in baseline_results.keys():
            interval_label = f"{baseline_results[name]['interval_minutes']:.2f} min"

            # Baseline
            scenarios.append(name)
            intervals.append(interval_label)
            revenues.append(baseline_results[name]['total_revenue'])
            types.append('Sans recommandation')

            # Avec recommandation
            scenarios.append(name)
            intervals.append(interval_label)
            revenues.append(reco_results[name]['total_revenue'])
            types.append('Avec recommandation')

        df_plot = pd.DataFrame({
            'Intervalle': intervals,
            'Revenu': revenues,
            'Type': types
        })

        # Créer le graphique
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

        # Graphique 1: Comparaison des revenus
        sns.barplot(data=df_plot, x='Intervalle', y='Revenu', hue='Type', ax=ax1)
        ax1.set_title('Comparaison des Revenus: SANS vs AVEC Recommandation', fontsize=14, fontweight='bold')
        ax1.set_xlabel('Fréquence des publicités pop-up', fontsize=12)
        ax1.set_ylabel('Revenu annuel (€)', fontsize=12)
        ax1.legend(title='Scénario', fontsize=10)
        ax1.grid(axis='y', alpha=0.3)

        # Ajouter les valeurs sur les barres
        for container in ax1.containers:
            ax1.bar_label(container, fmt='%.0f €', padding=3, fontsize=9)

        # Graphique 2: Gains en %
        gains_data = []
        intervals_labels = []
        for name in comparison.keys():
            intervals_labels.append(f"{comparison[name]['interval_minutes']:.2f} min")
            gains_data.append(comparison[name]['gain_pct'])

        ax2.bar(intervals_labels, gains_data, color='green', alpha=0.7)
        ax2.set_title('Gain en % avec le Système de Recommandation', fontsize=14, fontweight='bold')
        ax2.set_xlabel('Fréquence des publicités pop-up', fontsize=12)
        ax2.set_ylabel('Gain (%)', fontsize=12)
        ax2.grid(axis='y', alpha=0.3)

        # Ajouter les valeurs sur les barres
        for i, v in enumerate(gains_data):
            ax2.text(i, v + 0.5, f'+{v:.1f}%', ha='center', fontsize=10, fontweight='bold')

        plt.tight_layout()

        # Sauvegarder
        output_path = OUTPUT_DIR / "time_based_revenue_comparison.png"
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"  ✓ Graphique sauvegardé: {output_path}")

        plt.close()

    def save_results(self, baseline_results, reco_results, comparison):
        """
        Sauvegarde les résultats en JSON
        """
        print(f"\n💾 Sauvegarde des résultats...")

        results = {
            'metric': 'time_based_popup_revenue',
            'cpm_popup': CPM_POPUP,
            'quantiles': self.quantiles,
            'baseline_scenario': baseline_results,
            'recommendation_scenario': reco_results,
            'comparison': comparison
        }

        output_path = OUTPUT_DIR / "time_based_revenue_results.json"
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)

        print(f"  ✓ Résultats sauvegardés: {output_path}")

    def run_full_analysis(self, num_sessions=100000):
        """
        Lance l'analyse complète
        """
        print("\n" + "="*80)
        print("ANALYSE DES REVENUS BASÉS SUR LE TEMPS PASSÉ (MÉTRIQUE PUB POP-UP)")
        print("="*80)

        # Charger les données
        self.load_data()

        # Calculer les quantiles
        self.calculate_session_quantiles()

        # Scénario baseline
        baseline_results = self.estimate_baseline_scenario(num_sessions)

        # Scénario avec recommandation
        reco_results = self.estimate_with_recommendation_scenario(num_sessions)

        # Comparer
        comparison = self.compare_scenarios(baseline_results, reco_results, num_sessions)

        # Visualisations
        self.create_visualization(baseline_results, reco_results, comparison)

        # Sauvegarder
        self.save_results(baseline_results, reco_results, comparison)

        print("\n" + "="*80)
        print("✅ ANALYSE TERMINÉE")
        print("="*80)

        return baseline_results, reco_results, comparison


def main():
    """
    Point d'entrée principal
    """
    analyzer = TimeBasedRevenueAnalyzer(models_path="../models")
    baseline, reco, comparison = analyzer.run_full_analysis(num_sessions=100000)

    # Afficher le résumé final
    print("\n\n📋 RÉSUMÉ EXÉCUTIF")
    print("="*80)
    print(f"\nNouvelle métrique: REVENUS basés sur le TEMPS PASSÉ")
    print(f"  - Publicités pop-up à intervalle régulier (N1, N2, N3, N4 minutes)")
    print(f"  - CPM pop-up: {CPM_POPUP}€")
    print(f"  - Simulation: 100,000 sessions/an")

    print(f"\n\nMEILLEUR SCÉNARIO (maximisation des revenus):")
    best_scenario = max(comparison.items(), key=lambda x: x[1]['gain_revenue'])
    print(f"  Fréquence: 1 pub toutes les {best_scenario[1]['interval_minutes']:.2f} minutes ({best_scenario[0]})")
    print(f"  Gain: +{best_scenario[1]['gain_revenue']:.2f}€ (+{best_scenario[1]['gain_pct']:.1f}%)")
    print(f"  Revenu SANS reco: {best_scenario[1]['baseline_revenue']:.2f}€")
    print(f"  Revenu AVEC reco: {best_scenario[1]['reco_revenue']:.2f}€")

    print(f"\n\n💡 RECOMMANDATION:")
    print(f"  Utiliser une fréquence de pub de {best_scenario[1]['interval_minutes']:.2f} minutes")
    print(f"  pour maximiser les revenus tout en préservant l'expérience utilisateur.")


if __name__ == "__main__":
    main()
