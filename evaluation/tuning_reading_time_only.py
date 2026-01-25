"""
OPTIMISATION BASÉE SUR LE TEMPS DE LECTURE UNIQUEMENT
=====================================================

Fonction objectif: Maximiser le temps de lecture total
- Utilise les données filtrées (sans temps fantômes < 30s)
- Optimise uniquement les 3 poids hybrides (Content/Collab/Temporal)
- Les 9 signaux de qualité sont des features fixes (non optimisées)

Date: 23 Janvier 2026
"""

import sys
sys.path.append('../lambda')
sys.path.append('..')

import os
import json
import numpy as np
import pandas as pd
import optuna
from optuna.samplers import TPESampler
from pathlib import Path
from datetime import datetime

# Configuration
N_TRIALS = 30
N_USERS_SAMPLE = 60  # 20 users par strate × 3 strates (compromis vitesse/représentativité)
RANDOM_SEED = 42

# Chemins
BASE_DIR = Path(__file__).parent.parent
MODELS_DIR = BASE_DIR / "models"
OUTPUT_DIR = BASE_DIR / "evaluation"

def load_data():
    """Charge les données nécessaires"""
    print("📂 Chargement des données...")

    # Charger les stats d'interactions (déjà filtrées > 30s)
    stats_path = MODELS_DIR / "interaction_stats_enriched.csv"
    stats_df = pd.read_csv(stats_path)
    print(f"  ✓ {len(stats_df):,} interactions chargées")

    # Charger les profils utilisateurs enrichis
    profiles_path = MODELS_DIR / "user_profiles_enriched.json"
    with open(profiles_path, 'r') as f:
        user_profiles = json.load(f)
    user_profiles = {int(k): v for k, v in user_profiles.items()}
    print(f"  ✓ {len(user_profiles):,} profils utilisateurs chargés")

    return stats_df, user_profiles


def calculate_expected_reading_time(user_id, recommendations, stats_df, user_profiles):
    """
    Calcule le temps de lecture attendu pour un utilisateur donné des recommandations

    Logique:
    - Pour chaque article recommandé, on regarde le temps de lecture moyen de cet article
    - Si l'article est dans les préférences de l'utilisateur, bonus de temps
    """
    if user_id not in user_profiles:
        return 0.0

    user_profile = user_profiles[user_id]
    user_categories = set(user_profile.get('top_categories', []))

    total_expected_time = 0.0

    for rec in recommendations:
        article_id = rec.get('article_id', rec) if isinstance(rec, dict) else rec

        # Temps moyen de lecture pour cet article
        article_stats = stats_df[stats_df['article_id'] == article_id]
        if len(article_stats) > 0:
            avg_time = article_stats['total_time_seconds'].mean()
        else:
            avg_time = 60.0  # Défaut: 1 minute

        # Bonus si l'article est dans une catégorie préférée
        article_category = rec.get('category_id') if isinstance(rec, dict) else None
        if article_category and article_category in user_categories:
            avg_time *= 1.2  # +20% si catégorie préférée

        total_expected_time += avg_time

    return total_expected_time


def load_engine():
    """Charge le moteur de recommandation (une seule fois)"""
    from azure_function.recommendation_engine import RecommendationEngine

    print("📦 Chargement du moteur de recommandation...")
    engine = RecommendationEngine(models_path=str(MODELS_DIR))
    engine.load_models()
    print("  ✓ Moteur chargé")
    return engine


def evaluate_weights(engine, weight_content, weight_collab, weight_trend,
                    stats_df, user_profiles, sample_users):
    """
    Évalue une combinaison de poids en calculant le temps de lecture attendu
    """
    total_reading_time = 0.0
    valid_users = 0

    for user_id in sample_users:
        try:
            recommendations = engine.recommend(
                user_id=user_id,
                n_recommendations=10,
                weight_content=weight_content,
                weight_collab=weight_collab,
                weight_trend=weight_trend,
                use_diversity=True
            )

            if recommendations:
                expected_time = calculate_expected_reading_time(
                    user_id, recommendations, stats_df, user_profiles
                )
                total_reading_time += expected_time
                valid_users += 1

        except Exception:
            continue

    if valid_users > 0:
        return total_reading_time / valid_users
    return 0.0


def objective(trial, engine, stats_df, user_profiles, sample_users):
    """Fonction objectif Optuna: maximiser le temps de lecture"""

    # Suggérer les poids hybrides (contraints selon état de l'art)
    weight_content = trial.suggest_float('weight_content', 0.30, 0.50)  # 30-50%
    weight_collab = trial.suggest_float('weight_collab', 0.20, 0.40)    # 20-40%
    weight_trend = trial.suggest_float('weight_trend', 0.15, 0.35)      # 15-35%

    # Normaliser pour que la somme = 1
    total = weight_content + weight_collab + weight_trend
    weight_content /= total
    weight_collab /= total
    weight_trend /= total

    # Évaluer cette combinaison
    avg_reading_time = evaluate_weights(
        engine, weight_content, weight_collab, weight_trend,
        stats_df, user_profiles, sample_users
    )

    print(f"  Trial {trial.number}: Content={weight_content:.2%}, "
          f"Collab={weight_collab:.2%}, Trend={weight_trend:.2%} "
          f"→ Temps lecture: {avg_reading_time:.1f}s")

    return avg_reading_time  # On veut MAXIMISER


def main():
    print("="*80)
    print("OPTIMISATION BASÉE SUR LE TEMPS DE LECTURE")
    print("="*80)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Trials: {N_TRIALS}")
    print(f"Utilisateurs par trial: {N_USERS_SAMPLE}")
    print()

    # Charger les données
    stats_df, user_profiles = load_data()

    # Charger le moteur de recommandation (une seule fois!)
    engine = load_engine()

    # Échantillonnage STRATIFIÉ par niveau d'activité
    print("\n📊 Échantillonnage stratifié par niveau d'activité...")
    np.random.seed(RANDOM_SEED)

    # Créer un DataFrame avec user_id et num_interactions
    user_activity = pd.DataFrame([
        {'user_id': uid, 'num_interactions': profile.get('num_interactions', 0)}
        for uid, profile in user_profiles.items()
    ])

    # Créer 4 strates (quartiles) basées sur le nombre d'interactions
    try:
        user_activity['strata'] = pd.qcut(
            user_activity['num_interactions'],
            q=4,
            duplicates='drop'
        )
    except ValueError:
        # Si pas assez de valeurs uniques, utiliser cut au lieu de qcut
        user_activity['strata'] = pd.cut(
            user_activity['num_interactions'],
            bins=4
        )

    n_strates = user_activity['strata'].nunique()
    samples_per_strata = N_USERS_SAMPLE // n_strates

    # Échantillonner de manière égale dans chaque strate
    sample_users = []

    for i, strata_val in enumerate(user_activity['strata'].unique()):
        strata_users = user_activity[user_activity['strata'] == strata_val]['user_id'].values
        n_sample = min(samples_per_strata, len(strata_users))
        sampled = np.random.choice(strata_users, n_sample, replace=False)
        sample_users.extend(sampled)
        print(f"  Strate {i+1}/{n_strates}: {n_sample} utilisateurs")

    sample_users = np.array(sample_users)
    print(f"  ✓ Total: {len(sample_users)} utilisateurs (stratifié par activité)")

    # Créer l'étude Optuna (maximisation)
    study = optuna.create_study(
        direction='maximize',
        sampler=TPESampler(seed=RANDOM_SEED)
    )

    print("\n🚀 Lancement de l'optimisation...\n")

    # Optimiser
    study.optimize(
        lambda trial: objective(trial, engine, stats_df, user_profiles, sample_users),
        n_trials=N_TRIALS,
        show_progress_bar=True
    )

    # Résultats
    print("\n" + "="*80)
    print("🏆 RÉSULTATS OPTIMAUX")
    print("="*80)

    best_params = study.best_params

    # Normaliser les poids
    total = best_params['weight_content'] + best_params['weight_collab'] + best_params['weight_trend']
    weight_content = best_params['weight_content'] / total
    weight_collab = best_params['weight_collab'] / total
    weight_trend = best_params['weight_trend'] / total

    print(f"\nPoids optimaux (normalisés):")
    print(f"  Content:  {weight_content:.1%}")
    print(f"  Collab:   {weight_collab:.1%}")
    print(f"  Trend:    {weight_trend:.1%}")
    print(f"\nTemps de lecture moyen optimal: {study.best_value:.1f} secondes")

    # Sauvegarder les résultats
    results = {
        'best_score': study.best_value,
        'best_params_raw': best_params,
        'best_params_normalized': {
            'weight_content': weight_content,
            'weight_collab': weight_collab,
            'weight_trend': weight_trend
        },
        'config': {
            'n_trials': N_TRIALS,
            'n_users_sample': N_USERS_SAMPLE,
            'objective': 'maximize_reading_time',
            'timestamp': datetime.now().isoformat()
        }
    }

    output_file = OUTPUT_DIR / "tuning_reading_time_results.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\n✅ Résultats sauvegardés: {output_file}")

    print("\n" + "="*80)
    print("✅ OPTIMISATION TERMINÉE")
    print("="*80)


if __name__ == "__main__":
    main()
