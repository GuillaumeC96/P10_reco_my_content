"""
TUNING PARALLÉLISÉ AVEC CONTRAINTES STATE-OF-ART (v8 - 27 DEC 2024)
- Parallélisation des évaluations utilisateurs (adapté pour 16 cores / 30GB RAM)
- Early stopping progressif: 10 → 30 → 50 users
- 13 HYPERPARAMÈTRES: 9 niveau 1 (signaux) + 3 niveau 2 (stratégies) + 1 fenêtre temporelle

CHANGEMENTS v8 (27 Déc 2024):
- FACTEUR DE VISIBILITÉ PUB IN-ARTICLE basé sur temps de lecture
  * Temps ≥30s → Facteur 1.0 (pub interstitielle + in-article vues)
  * Temps <30s → Facteur 0.6 (probablement seulement pub interstitielle vue)
  * Transition douce (sigmoid) entre 20s et 40s
  * Justification: 96% du dataset a temps ≥30s, médiane à 30s
- FENÊTRE TEMPORELLE DATA-DRIVEN: max_article_age_days devient un hyperparamètre Optuna
  * Range [30-365 jours] basé sur analyse quantiles (P95=120j couvre 99.12% val set)
  * Permet à Optuna de trouver l'optimum business (maximiser revenus publicitaires)
- Reference timestamp corrigé: calcul d'âge relatif à la date de split train/val
- Niveau 2 CONTRAINT selon état de l'art News Recommendation 2024
  * Content: [0.30-0.50] cible 40%
  * Collab: [0.20-0.40] cible 30%
  * Temporal: [0.15-0.35] cible 25%
- Composite score optimisé revenus: 69% Precision@10 + 31% Recall@10 (proportionnel CPM)
"""

import sys
sys.path.append('../lambda')

import os
import json
import numpy as np
import pandas as pd
import multiprocessing
from functools import partial
from improved_tuning import ImprovedRecommendationEvaluator
import optuna
from optuna.samplers import TPESampler

# Configuration adaptée pour Ryzen 7 Pro 7735U (16 threads, 30GB RAM)
N_TRIALS = 30
N_USERS = 50
N_WORKERS = 12  # 30GB RAM / 2.5GB par worker = 12 workers max (garder marge)
BASELINE_SCORE = 0.2124

# Seuils early stopping
THRESHOLD_PHASE1 = 0.05  # Ajusté pour score revenue-optimized (Precision-based)
THRESHOLD_PHASE2 = 0.08  # Ajusté pour score revenue-optimized (Precision-based)

# Charger les stats une seule fois (avant spawn)
STATS_PATH = "../models/interaction_stats_enriched.csv"


def init_worker():
    """Initialise chaque worker avec son propre evaluator"""
    global worker_evaluator
    worker_evaluator = ImprovedRecommendationEvaluator(models_path="../models")
    worker_evaluator.load_engine()
    worker_evaluator.create_temporal_split(train_ratio=0.8, min_interactions=15)


def evaluate_one_user(args):
    """Évalue UN utilisateur (appelé en parallèle)"""
    user_id, new_profiles, collab, content, temporal, max_age_days = args
    try:
        global worker_evaluator

        # Injecter les nouveaux profils
        worker_evaluator.engine.user_profiles = new_profiles
        worker_evaluator.original_user_profiles = new_profiles.copy()

        # Évaluer ce user
        metrics = worker_evaluator.evaluate_user(
            user_id=user_id,
            weight_collab=float(collab),
            weight_content=float(content),
            weight_trend=float(temporal),  # weight_trend dans API, temporal ici
            k=10,
            max_article_age_days=float(max_age_days)
        )
        return metrics
    except Exception as e:
        return None


def recompute_profiles_fast(weight_params, stats_df):
    """
    Recalcule rapidement les poids avec nouveaux coefficients

    Applique un facteur de visibilité de pub in-article basé sur le temps de lecture:
    - Temps ≥30s → Facteur 1.0 (pub interstitielle + in-article vues)
    - Temps <30s → Facteur 0.6 (probablement seulement pub interstitielle vue)

    Justification: 96% du dataset a temps ≥30s, médiane à 30s
    """
    stats = stats_df.copy()

    # Normaliser les features
    max_clicks = stats['num_clicks'].max()
    max_time = stats['total_time_seconds'].quantile(0.99)

    stats['clicks_norm'] = np.log1p(stats['num_clicks']) / np.log1p(max_clicks)
    stats['time_norm'] = stats['total_time_seconds'].clip(0, max_time) / max_time

    # Calculer les poids de base avec les nouveaux coefficients
    stats['interaction_weight'] = (
        weight_params['w_time'] * stats['time_norm'] +
        weight_params['w_clicks'] * stats['clicks_norm'] +
        weight_params['w_session'] * stats['avg_session_quality'] +
        weight_params['w_device'] * stats['avg_device_quality'] +
        weight_params['w_env'] * stats['avg_env_quality'] +
        weight_params['w_referrer'] * stats['avg_referrer_quality'] +
        weight_params['w_os'] * stats['avg_os_quality'] +
        weight_params['w_country'] * stats['avg_country_quality'] +
        weight_params['w_region'] * stats['avg_region_quality']
    )

    # Facteur de visibilité pub in-article basé sur temps de lecture
    # Transition douce entre 20s et 40s (sigmoid)
    SEUIL_PUB_INARTICLE = 30  # secondes (temps pour scroller jusqu'à la pub)
    TRANSITION_WIDTH = 5       # largeur de la transition

    # Facteur varie de 0.6 (temps court) à 1.0 (temps suffisant)
    # 0.6 = seulement pub interstitielle (6€), 1.0 = interstitielle + in-article (6€ + 2.7€)
    pub_visibility_factor = 0.6 + 0.4 / (1 + np.exp(-(stats['total_time_seconds'] - SEUIL_PUB_INARTICLE) / TRANSITION_WIDTH))

    # Appliquer le facteur et clipper
    stats['interaction_weight'] = (stats['interaction_weight'] * pub_visibility_factor).clip(0.1, 1.0)

    # Construire dictionnaire des profils
    new_profiles = {}
    for user_id in stats['user_id'].unique():
        user_data = stats[stats['user_id'] == user_id]
        article_weights = dict(zip(
            user_data['article_id'].astype(int),
            user_data['interaction_weight']
        ))
        new_profiles[int(user_id)] = {
            'articles_read': user_data['article_id'].astype(int).tolist(),
            'article_weights': article_weights
        }

    return new_profiles


def compute_composite_score(metrics_list):
    """
    Calcule le score composite à partir d'une liste de métriques

    FORMULE OPTIMISÉE POUR REVENUS PUBLICITAIRES (Proportionnel CPM exact):
    - 69% Precision@10 → CTR → pubs interstitielles (6€ CPM)
    - 31% Recall@10 → Pages vues → pubs in-article (2.7€ CPM)

    Modèle de revenus:
    Revenus = (Clics × 6€) + (Pages vues × 2.7€)
    Ratio CPM: 6€/(6€+2.7€) = 69% | 2.7€/8.7€ = 31%

    Coefficients proportionnels aux CPM à 1% près.
    """
    if len(metrics_list) == 0:
        return 0.0
    return (
        0.69 * np.mean([m['precision@10'] for m in metrics_list]) +
        0.31 * np.mean([m['recall@10'] for m in metrics_list])
    )


def evaluate_users_parallel(user_ids, new_profiles, collab, content, temporal, max_age_days, pool):
    """Évalue une liste d'utilisateurs en parallèle"""
    args_list = [(uid, new_profiles, collab, content, temporal, max_age_days) for uid in user_ids]
    results = pool.map(evaluate_one_user, args_list)
    return [r for r in results if r is not None]


def create_objective(stats_df, all_users, pool):
    """Crée la fonction objective avec closure sur les données"""

    def objective_progressive_parallel(trial):
        """Objective avec évaluation progressive ET parallèle"""

        # Suggérer les 9 paramètres niveau 1
        # PLAGES AJUSTÉES: 4 paramètres déplacés pour éviter les extremums
        w_time = trial.suggest_float('w_time', 0.32, 0.67)          # ← DÉPLACÉ (était 0.15-0.50, optimal 0.496 = 98.9%)
        w_clicks = trial.suggest_float('w_clicks', 0.16, 0.46)      # ← DÉPLACÉ (était 0.05-0.35, optimal 0.314 = 88.1%)
        w_session = trial.suggest_float('w_session', 0.05, 0.25)
        w_device = trial.suggest_float('w_device', 0.07, 0.20)      # ← DÉPLACÉ (était 0.02-0.15, optimal 0.133 = 86.8%)
        w_env = trial.suggest_float('w_env', 0.01, 0.10)
        w_referrer = trial.suggest_float('w_referrer', 0.01, 0.07)  # ← DÉPLACÉ (était 0.01-0.10, optimal 0.023 = 14.4%)
        w_os = trial.suggest_float('w_os', 0.01, 0.10)
        w_country = trial.suggest_float('w_country', 0.01, 0.10)
        w_region = trial.suggest_float('w_region', 0.01, 0.10)

        # Normaliser pour somme = 1.0
        total = w_time + w_clicks + w_session + w_device + w_env + w_referrer + w_os + w_country + w_region
        weight_params = {k: v/total for k, v in {
            'w_time': w_time, 'w_clicks': w_clicks, 'w_session': w_session,
            'w_device': w_device, 'w_env': w_env, 'w_referrer': w_referrer,
            'w_os': w_os, 'w_country': w_country, 'w_region': w_region
        }.items()}

        # Suggérer les 3 paramètres niveau 2 - CONTRAINTS (State-of-Art 2024)
        # Empêche convergence vers extremums (0% ou 100%)
        # Références: "A Survey of Personalized News Recommendation" (2023)
        #             "Beyond-accuracy: a review on diversity" (2023)
        content = trial.suggest_float('content', 0.30, 0.50)    # 30-50%, cible 40%
        collab = trial.suggest_float('collab', 0.20, 0.40)      # 20-40%, cible 30%
        temporal = trial.suggest_float('temporal', 0.15, 0.35)  # 15-35%, cible 25%

        # Normaliser niveau 2 pour somme = 1.0
        total_l2 = content + collab + temporal
        content_norm = content / total_l2
        collab_norm = collab / total_l2
        temporal_norm = temporal / total_l2

        # Suggérer la fenêtre temporelle (DATA-DRIVEN, orienté business)
        # Basé sur l'analyse des quantiles: P95=120j couvre 99.12% du val set
        # Range 30-365j permet à Optuna de trouver l'optimum revenus publicitaires
        max_article_age_days = trial.suggest_int('max_article_age_days', 30, 365)

        # Recalculer les profils avec nouveaux poids
        new_profiles = recompute_profiles_fast(weight_params, stats_df)

        # PHASE 1: Évaluer 10 users en parallèle
        metrics_10 = evaluate_users_parallel(all_users[:10], new_profiles, collab_norm, content_norm, temporal_norm, max_article_age_days, pool)
        score_10 = compute_composite_score(metrics_10)

        # Early stopping phase 1
        if score_10 < THRESHOLD_PHASE1:
            trial.set_user_attr('phase', 1)
            trial.set_user_attr('users_evaluated', 10)
            return score_10

        # PHASE 2: Évaluer 20 users de plus en parallèle
        metrics_20 = evaluate_users_parallel(all_users[10:30], new_profiles, collab_norm, content_norm, temporal_norm, max_article_age_days, pool)
        all_metrics_30 = metrics_10 + metrics_20
        score_30 = compute_composite_score(all_metrics_30)

        # Early stopping phase 2
        if score_30 < THRESHOLD_PHASE2:
            trial.set_user_attr('phase', 2)
            trial.set_user_attr('users_evaluated', 30)
            return score_30

        # PHASE 3: Candidat prometteur, évaluer les 20 derniers
        metrics_20_final = evaluate_users_parallel(all_users[30:50], new_profiles, collab_norm, content_norm, temporal_norm, max_article_age_days, pool)
        all_metrics_50 = all_metrics_30 + metrics_20_final
        score_50 = compute_composite_score(all_metrics_50)

        trial.set_user_attr('phase', 3)
        trial.set_user_attr('users_evaluated', 50)

        return score_50

    return objective_progressive_parallel


if __name__ == '__main__':
    # Force 'spawn' pour éviter les problèmes de fork avec numpy/pandas
    multiprocessing.set_start_method('spawn', force=True)

    print("="*80)
    print("TUNING PARALLÉLISÉ + EARLY STOPPING - 13 PARAMÈTRES (v8)")
    print("="*80)

    print(f"\nConfiguration (adapté Ryzen 7 Pro / 30GB RAM):")
    print(f"  - {N_TRIALS} trials (optimisation bayésienne)")
    print(f"  - {N_USERS} users max par trial")
    print(f"  - {N_WORKERS} workers parallèles")
    print(f"  - Early stopping: phase1 < {THRESHOLD_PHASE1}, phase2 < {THRESHOLD_PHASE2}")
    print(f"  - Baseline: {BASELINE_SCORE}")

    # Charger les stats
    print("\nChargement des données...")
    stats_df = pd.read_csv(STATS_PATH)
    print(f"✓ Stats chargés: {len(stats_df)} interactions")

    # Charger la liste des utilisateurs
    print("Chargement des utilisateurs de validation...")
    temp_evaluator = ImprovedRecommendationEvaluator(models_path="../models")
    temp_evaluator.load_engine()
    temp_evaluator.create_temporal_split(train_ratio=0.8, min_interactions=15)
    ALL_USERS = list(temp_evaluator.val_interactions.keys())[:N_USERS]
    del temp_evaluator
    print(f"✓ {len(ALL_USERS)} utilisateurs sélectionnés")

    # Créer le pool de workers
    print(f"\nCréation du pool de {N_WORKERS} workers...")
    pool = multiprocessing.Pool(N_WORKERS, initializer=init_worker)
    print("✓ Pool créé")

    # Créer la fonction objective
    objective = create_objective(stats_df, ALL_USERS, pool)

    # Lancer l'optimisation
    print("\n" + "="*80)
    print("OPTIMISATION EN COURS")
    print("="*80)

    study = optuna.create_study(
        direction='maximize',
        sampler=TPESampler(seed=42)
    )

    try:
        study.optimize(objective, n_trials=N_TRIALS, show_progress_bar=True)
    finally:
        pool.close()
        pool.join()

    # Résultats
    print("\n" + "="*80)
    print("RÉSULTATS")
    print("="*80)

    best_params = study.best_params
    best_score = study.best_value

    print(f"\n🏆 Meilleur score: {best_score:.6f}")

    # Normaliser niveau 1
    level1_keys = ['w_time', 'w_clicks', 'w_session', 'w_device', 'w_env', 'w_referrer', 'w_os', 'w_country', 'w_region']
    total = sum(best_params[k] for k in level1_keys)
    normalized = {k: best_params[k]/total for k in level1_keys}

    print("\nNiveau 1 (Signaux):")
    for key, val in normalized.items():
        name = key.replace('w_', '').capitalize()
        print(f"  {name:12s}: {val:.3f} ({val*100:.1f}%)")

    # Normaliser niveau 2
    level2_keys = ['collab', 'content', 'temporal']
    total_l2 = sum(best_params[k] for k in level2_keys)
    normalized_l2 = {k: best_params[k]/total_l2 for k in level2_keys}

    print("\nNiveau 2 (Stratégies):")
    for key, val in normalized_l2.items():
        name = key.capitalize()
        print(f"  {name:12s}: {val:.3f} ({val*100:.1f}%)")

    # Statistiques d'efficacité
    phase_stats = {}
    for trial in study.trials:
        if trial.value is not None:
            phase = trial.user_attrs.get('phase', 3)
            users = trial.user_attrs.get('users_evaluated', 50)
            if phase not in phase_stats:
                phase_stats[phase] = []
            phase_stats[phase].append(users)

    print("\n📊 Statistiques d'efficacité:")
    total_users_evaluated = sum([sum(users) for users in phase_stats.values()])
    max_possible = N_TRIALS * 50
    efficiency = (1 - total_users_evaluated / max_possible) * 100

    for phase in sorted(phase_stats.keys()):
        count = len(phase_stats[phase])
        print(f"  Phase {phase}: {count} trials ({count/N_TRIALS*100:.1f}%)")

    print(f"\n  Total users évalués: {total_users_evaluated}")
    print(f"  Économie vs full: {efficiency:.1f}%")

    # Amélioration
    improvement = ((best_score - BASELINE_SCORE) / BASELINE_SCORE) * 100
    print(f"\n📈 Amélioration vs baseline ({BASELINE_SCORE}): {improvement:+.1f}%")

    # Sauvegarder
    results = {
        'best_score': best_score,
        'best_params': best_params,
        'normalized_weights_level1': normalized,
        'normalized_weights_level2': normalized_l2,
        'config': {
            'n_trials': N_TRIALS,
            'n_users': N_USERS,
            'n_workers': N_WORKERS,
            'baseline': BASELINE_SCORE
        },
        'efficiency_stats': {
            'phase_distribution': {str(k): len(v) for k, v in phase_stats.items()},
            'total_users': total_users_evaluated,
            'max_possible': max_possible,
            'efficiency_gain': f"{efficiency:.1f}%"
        },
        'all_trials': [{
            'number': t.number,
            'value': t.value,
            'params': t.params,
            'phase': t.user_attrs.get('phase', 3),
            'users_evaluated': t.user_attrs.get('users_evaluated', 50)
        } for t in study.trials if t.value is not None]
    }

    with open('tuning_12_parallel_progressive_v2_results.json', 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n✓ Résultats: tuning_12_parallel_progressive_v2_results.json")

    # Top 5
    print("\n" + "="*80)
    print("TOP 5 TRIALS")
    print("="*80)
    sorted_trials = sorted([t for t in study.trials if t.value], key=lambda t: t.value, reverse=True)[:5]
    for i, t in enumerate(sorted_trials, 1):
        phase = t.user_attrs.get('phase', 3)
        users = t.user_attrs.get('users_evaluated', 50)
        # Normaliser niveau 2 pour ce trial
        t_total = t.params['collab'] + t.params['content'] + t.params['temporal']
        t_collab = t.params['collab'] / t_total * 100
        t_content = t.params['content'] / t_total * 100
        t_temporal = t.params['temporal'] / t_total * 100
        print(f"\n{i}. Score: {t.value:.6f} (phase {phase}, {users} users)")
        print(f"   Niveau 2: Collab {t_collab:.1f}% | Content {t_content:.1f}% | Temporal {t_temporal:.1f}%")

    print("\n" + "="*80)
    print("✅ TERMINÉ")
    print("="*80)
