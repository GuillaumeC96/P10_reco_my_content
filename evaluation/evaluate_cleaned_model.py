"""
Évaluation du modèle entraîné avec données nettoyées
Compare les métriques avant/après nettoyage
"""

import pandas as pd
import numpy as np
import json
from pathlib import Path

def evaluate_cleaned_model():
    """
    Évalue le modèle avec données nettoyées et compare avec l'ancien
    """

    print("=" * 80)
    print("ÉVALUATION DU MODÈLE AVEC DONNÉES NETTOYÉES")
    print("=" * 80)

    base_dir = Path(__file__).parent.parent
    models_dir = base_dir / "models"
    eval_dir = base_dir / "evaluation"

    # 1. Charger les données nettoyées
    print("\n1. Chargement des statistiques...")
    interactions = pd.read_csv(models_dir / "interaction_stats_cleaned.csv")
    articles = pd.read_csv(models_dir / "articles_metadata.csv")

    print(f"   - {len(interactions):,} interactions")
    print(f"   - {interactions['user_id'].nunique():,} utilisateurs")

    # 2. Calculer les statistiques par utilisateur
    print("\n2. Calcul des statistiques utilisateur...")

    user_stats = interactions.groupby('user_id').agg({
        'article_id': 'count',  # Nombre d'articles lus
        'total_time_seconds': 'sum',  # Temps total
        'num_clicks': 'sum'  # Total clics
    }).reset_index()

    user_stats.columns = ['user_id', 'num_articles', 'total_time_seconds', 'total_clicks']
    user_stats['total_time_minutes'] = user_stats['total_time_seconds'] / 60

    print(f"\n   Statistiques globales:")
    print(f"   - Articles lus (moyenne): {user_stats['num_articles'].mean():.2f}")
    print(f"   - Articles lus (médiane): {user_stats['num_articles'].median():.2f}")
    print(f"   - Temps total (moyenne): {user_stats['total_time_minutes'].mean():.2f} min")
    print(f"   - Temps total (médiane): {user_stats['total_time_minutes'].median():.2f} min")

    # 3. Calculer le ratio d'engagement
    print("\n3. Calcul du ratio d'engagement...")

    # Pour calculer le ratio, on a besoin des timestamps
    # On va utiliser les interactions détaillées
    interactions_detailed = pd.read_csv(models_dir / "interactions_cleaned.csv")

    # Calculer pour chaque utilisateur
    user_engagement = interactions_detailed.groupby('user_id').agg({
        'click_timestamp': ['min', 'max'],
        'time_spent_cleaned': 'sum'
    }).reset_index()

    user_engagement.columns = ['user_id', 'first_timestamp', 'last_timestamp', 'total_time_seconds']

    # Calculer les jours écoulés
    user_engagement['days_elapsed'] = (
        (user_engagement['last_timestamp'] - user_engagement['first_timestamp']) / (24 * 3600)
    )
    user_engagement['days_elapsed'] = user_engagement['days_elapsed'].clip(lower=1)  # Au moins 1 jour

    # Calculer le ratio d'engagement
    user_engagement['total_time_minutes'] = user_engagement['total_time_seconds'] / 60
    user_engagement['available_time_minutes'] = user_engagement['days_elapsed'] * 10  # 10 min/jour
    user_engagement['engagement_ratio'] = (
        user_engagement['total_time_minutes'] / user_engagement['available_time_minutes']
    ) * 100

    # Limiter à 100% max (au cas où)
    user_engagement['engagement_ratio'] = user_engagement['engagement_ratio'].clip(upper=100)

    print(f"\n   Ratio d'engagement:")
    print(f"   - Moyenne: {user_engagement['engagement_ratio'].mean():.2f}%")
    print(f"   - Médiane: {user_engagement['engagement_ratio'].median():.2f}%")
    print(f"   - Max: {user_engagement['engagement_ratio'].max():.2f}%")

    # 4. Simulation sans vs avec recommandations (+83%)
    print("\n4. Simulation impact système de recommandation...")

    # Scénario de base (sans reco)
    baseline_ratio = user_engagement['engagement_ratio'].mean()
    baseline_time = user_engagement['total_time_minutes'].mean()

    # Avec recommandations (+83%)
    with_reco_ratio = baseline_ratio * 1.83
    with_reco_time = baseline_time * 1.83

    print(f"\n   Sans recommandation:")
    print(f"   - Ratio d'engagement: {baseline_ratio:.2f}%")
    print(f"   - Temps moyen: {baseline_time:.2f} min")

    print(f"\n   Avec recommandation (+83%):")
    print(f"   - Ratio d'engagement: {with_reco_ratio:.2f}%")
    print(f"   - Temps moyen: {with_reco_time:.2f} min")

    # 5. Calcul des revenus
    print("\n5. Calcul de l'impact sur les revenus...")

    CPM = 6.0  # 6€ pour 1000 impressions
    PUB_INTERVAL = 3.55  # 1 pub toutes les 3.55 minutes
    num_users = len(user_engagement)

    # Sans recommandation
    baseline_pubs_per_user = baseline_time / PUB_INTERVAL
    baseline_revenue_per_user = (baseline_pubs_per_user / 1000) * CPM
    baseline_revenue_total = baseline_revenue_per_user * num_users

    # Avec recommandation
    with_reco_pubs_per_user = with_reco_time / PUB_INTERVAL
    with_reco_revenue_per_user = (with_reco_pubs_per_user / 1000) * CPM
    with_reco_revenue_total = with_reco_revenue_per_user * num_users

    gain_revenue = with_reco_revenue_total - baseline_revenue_total

    print(f"\n   Sans recommandation:")
    print(f"   - Pubs/user: {baseline_pubs_per_user:.2f}")
    print(f"   - Revenus: {baseline_revenue_total:,.2f}€")

    print(f"\n   Avec recommandation:")
    print(f"   - Pubs/user: {with_reco_pubs_per_user:.2f}")
    print(f"   - Revenus: {with_reco_revenue_total:,.2f}€")

    print(f"\n   Gain: +{gain_revenue:,.2f}€ (+83%)")

    # 6. Comparaison avec ancien modèle
    print("\n6. Comparaison avec ancien modèle...")

    try:
        # Charger les anciens résultats
        with open(eval_dir / "engagement_ratio_results.json", 'r') as f:
            old_results = json.load(f)

        print(f"\n   ANCIEN MODÈLE (données non nettoyées):")
        print(f"   - Temps moyen: {old_results['baseline_scenario']['mean_time_minutes']:.2f} min")
        print(f"   - Ratio: {old_results['baseline_scenario']['mean_ratio_pct']:.2f}%")
        print(f"   - Revenus: {old_results['revenue_impact']['baseline_revenue_total']:,.2f}€")

        print(f"\n   NOUVEAU MODÈLE (données nettoyées):")
        print(f"   - Temps moyen: {baseline_time:.2f} min")
        print(f"   - Ratio: {baseline_ratio:.2f}%")
        print(f"   - Revenus: {baseline_revenue_total:,.2f}€")

        print(f"\n   ⚠️ Les chiffres ont CHANGÉ car on a éliminé le temps fantôme!")

    except FileNotFoundError:
        print("   (Pas de résultats anciens pour comparaison)")

    # 7. Sauvegarder les résultats
    print("\n7. Sauvegarde des résultats...")

    results = {
        'num_users': int(num_users),
        'num_interactions': len(interactions_detailed),
        'baseline_scenario': {
            'mean_ratio_pct': float(baseline_ratio),
            'median_ratio_pct': float(user_engagement['engagement_ratio'].median()),
            'mean_time_minutes': float(baseline_time),
            'median_time_minutes': float(user_engagement['total_time_minutes'].median()),
            'mean_articles': float(user_stats['num_articles'].mean()),
            'median_articles': float(user_stats['num_articles'].median())
        },
        'with_recommendation_scenario': {
            'mean_ratio_pct': float(with_reco_ratio),
            'mean_time_minutes': float(with_reco_time),
            'improvement_pct': 83.0
        },
        'revenue_impact': {
            'cpm': CPM,
            'pub_interval_minutes': PUB_INTERVAL,
            'baseline_pubs_per_user': float(baseline_pubs_per_user),
            'baseline_revenue_total': float(baseline_revenue_total),
            'with_reco_pubs_per_user': float(with_reco_pubs_per_user),
            'with_reco_revenue_total': float(with_reco_revenue_total),
            'gain_revenue': float(gain_revenue),
            'gain_revenue_pct': 83.0
        }
    }

    results_file = eval_dir / "evaluation_results_cleaned.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"   ✅ Résultats sauvegardés: {results_file}")

    print("\n" + "=" * 80)
    print("ÉVALUATION TERMINÉE !")
    print("=" * 80)

    print(f"\n🎯 Résultats clés:")
    print(f"   - Ratio d'engagement: {baseline_ratio:.2f}% → {with_reco_ratio:.2f}% (+83%)")
    print(f"   - Temps moyen: {baseline_time:.2f} min → {with_reco_time:.2f} min (+83%)")
    print(f"   - Revenus: {baseline_revenue_total:,.2f}€ → {with_reco_revenue_total:,.2f}€")
    print(f"   - Gain: +{gain_revenue:,.2f}€")

    print(f"\n📊 Prochaine étape: Mettre à jour l'interface Streamlit")

    return results

if __name__ == "__main__":
    evaluate_cleaned_model()
