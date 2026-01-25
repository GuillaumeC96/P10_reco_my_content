#!/usr/bin/env python3
"""
Exploration de données - Diagnostic scores 0.0

Calcule l'âge des articles par rapport à la DATE DE BASCULE TRAIN/TEST
pour chaque utilisateur, pas par rapport à la date max du dataset.
"""

import json
import pickle
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path

# Configuration
MODELS_DIR = Path("../models")
MAX_ARTICLE_AGE_DAYS = 60
TEMPORAL_DECAY_LAMBDA = 0.099

print("="*80)
print("DIAGNOSTIC - EXPLORATION DE DONNÉES (Calcul âge correct)")
print("="*80)

# ============================================================================
# 1. CHARGEMENT DES DONNÉES
# ============================================================================
print("\n[1/5] Chargement des données...")

# Articles metadata
articles_df = pd.read_csv(MODELS_DIR / "articles_metadata.csv")
print(f"  ✓ {len(articles_df):,} articles chargés")

# Convertir timestamps (millisecondes)
articles_df['created_at'] = pd.to_datetime(articles_df['created_at_ts'], unit='ms')

# User profiles
with open(MODELS_DIR / "user_profiles_enriched.pkl", "rb") as f:
    user_profiles = pickle.load(f)
print(f"  ✓ {len(user_profiles):,} profils utilisateurs")

# Interaction stats (contient les timestamps)
interaction_stats = pd.read_csv(MODELS_DIR / "interaction_stats_enriched.csv")
print(f"  ✓ {len(interaction_stats):,} stats d'interaction")

# ============================================================================
# 2. CRÉER LE SPLIT TEMPOREL
# ============================================================================
print("\n[2/5] Création du split temporel...")

train_dict = {}
test_dict = {}
user_split_dates = {}  # Stocker la date de bascule pour chaque user

train_ratio = 0.8
min_interactions = 10

for user_id, profile in user_profiles.items():
    articles = profile['articles_read']

    if len(articles) < min_interactions:
        continue

    # Split temporel
    split_idx = int(len(articles) * train_ratio)

    if split_idx > 0 and split_idx < len(articles):
        train_dict[user_id] = articles[:split_idx]
        test_dict[user_id] = articles[split_idx:]

        # Récupérer la date du dernier article train (= date de bascule)
        last_train_article_id = articles[split_idx - 1]
        last_train_date = articles_df[articles_df['article_id'] == last_train_article_id]['created_at'].iloc[0]
        user_split_dates[user_id] = last_train_date

print(f"  ✓ Split créé: {len(test_dict):,} users (80% train / 20% test)")
print(f"  ✓ Total train: {sum(len(v) for v in train_dict.values()):,} interactions")
print(f"  ✓ Total test: {sum(len(v) for v in test_dict.values()):,} interactions")

# ============================================================================
# 3. ANALYSE DES ÂGES PAR RAPPORT À LA DATE DE SPLIT
# ============================================================================
print("\n[3/5] Analyse des âges des articles PAR RAPPORT À LA DATE DE BASCULE...")

sample_users = list(test_dict.keys())[:10]

total_test_articles = 0
total_valid_test_articles = 0

print(f"\n  Analyse de 10 utilisateurs échantillon:\n")

for user_id in sample_users:
    test_articles = test_dict[user_id]
    train_articles = train_dict.get(user_id, [])
    split_date = user_split_dates[user_id]

    # Calculer l'âge des articles de test PAR RAPPORT À LA DATE DE SPLIT
    test_article_ids = test_articles
    test_articles_df = articles_df[articles_df['article_id'].isin(test_article_ids)].copy()
    test_articles_df['age_days_at_split'] = (split_date - test_articles_df['created_at']).dt.days

    valid_test = len(test_articles_df[test_articles_df['age_days_at_split'] <= MAX_ARTICLE_AGE_DAYS])
    total_test_articles += len(test_articles)
    total_valid_test_articles += valid_test

    ages = test_articles_df['age_days_at_split'].values

    print(f"    User {user_id}:")
    print(f"      Train: {len(train_articles)} articles | Test: {len(test_articles)} articles")
    print(f"      Date de split: {split_date.strftime('%Y-%m-%d')}")
    print(f"      Test ≤60j (à la date split): {valid_test}/{len(test_articles)} articles")
    if len(ages) > 0:
        print(f"      Âges à la date split: min={ages.min():.0f}j, max={ages.max():.0f}j, moy={ages.mean():.0f}j")
    print()

# ============================================================================
# 4. STATISTIQUES GLOBALES
# ============================================================================
print("\n[4/5] Statistiques globales sur TOUS les utilisateurs de test...")

all_test_article_ages = []
all_valid_count = 0
all_total_count = 0

for user_id in test_dict.keys():
    test_articles = test_dict[user_id]
    split_date = user_split_dates[user_id]

    test_articles_df = articles_df[articles_df['article_id'].isin(test_articles)].copy()
    test_articles_df['age_days_at_split'] = (split_date - test_articles_df['created_at']).dt.days

    ages = test_articles_df['age_days_at_split'].values
    all_test_article_ages.extend(ages)

    valid = len(test_articles_df[test_articles_df['age_days_at_split'] <= MAX_ARTICLE_AGE_DAYS])
    all_valid_count += valid
    all_total_count += len(test_articles)

all_test_article_ages = np.array(all_test_article_ages)

print(f"\n  Total articles de test: {all_total_count:,}")
print(f"  Articles ≤60j à leur date de split: {all_valid_count:,} ({100.0*all_valid_count/all_total_count:.2f}%)")

print(f"\n  Distribution des âges (à la date de split):")
print(f"    Min: {all_test_article_ages.min():.0f} jours")
print(f"    Max: {all_test_article_ages.max():.0f} jours")
print(f"    Moyenne: {all_test_article_ages.mean():.1f} jours")
print(f"    Médiane: {np.median(all_test_article_ages):.1f} jours")

# Quantiles
quantiles = [0.10, 0.25, 0.50, 0.75, 0.90, 0.95, 0.99]
print(f"\n  Quantiles:")
for q in quantiles:
    age = np.quantile(all_test_article_ages, q)
    print(f"    {int(q*100):2d}%: {age:6.1f} jours")

# Par tranches
tranches = [
    (0, 7, "0-7 jours"),
    (8, 14, "8-14 jours"),
    (15, 30, "15-30 jours"),
    (31, 60, "31-60 jours"),
    (61, 90, "61-90 jours"),
    (91, 180, "91-180 jours"),
    (181, 365, "181-365 jours"),
    (366, 10000, ">365 jours")
]

print(f"\n  Articles de test par tranche d'âge (à la date split):")
for min_age, max_age, label in tranches:
    count = len([age for age in all_test_article_ages if min_age <= age <= max_age])
    pct = 100.0 * count / len(all_test_article_ages)
    print(f"    {label:20s}: {count:6,} ({pct:5.2f}%)")

# ============================================================================
# 5. DIAGNOSTIC FINAL
# ============================================================================
print("\n" + "="*80)
print("DIAGNOSTIC FINAL")
print("="*80)

pct_valid = 100.0 * all_valid_count / all_total_count if all_total_count > 0 else 0

print(f"\n1. VALIDATION SET:")
print(f"   - Total articles de test: {all_total_count:,}")
print(f"   - Articles ≤60j (à leur date de split): {all_valid_count:,} ({pct_valid:.2f}%)")
print(f"   - Âge médian: {np.median(all_test_article_ages):.0f} jours")

print(f"\n2. FENÊTRE TEMPORELLE:")
print(f"   - MAX_ARTICLE_AGE_DAYS: {MAX_ARTICLE_AGE_DAYS} jours")

if pct_valid < 5:
    print(f"\n❌ PROBLÈME CRITIQUE:")
    print(f"\nSeulement {pct_valid:.2f}% des articles du test set sont ≤{MAX_ARTICLE_AGE_DAYS}j")
    print(f"à leur date de split respective.")
    print(f"\nLe moteur ne peut recommander que des articles ≤{MAX_ARTICLE_AGE_DAYS}j,")
    print(f"mais {100-pct_valid:.1f}% du ground truth est plus vieux.")
    print(f"\n→ Score Precision@10 et Recall@10 forcément très faibles (proche de 0)")

    # Calculer la fenêtre nécessaire
    for threshold in [50, 75, 90, 95]:
        needed_days = np.percentile(all_test_article_ages, threshold)
        print(f"\nPour couvrir {threshold}% du test set → MAX_ARTICLE_AGE_DAYS ≥ {needed_days:.0f} jours")

elif pct_valid < 20:
    print(f"\n⚠️  PROBLÈME:")
    print(f"\nSeulement {pct_valid:.2f}% des articles du test set sont éligibles.")
    print(f"Couverture insuffisante pour des métriques fiables.")

    for threshold in [75, 90, 95]:
        needed_days = np.percentile(all_test_article_ages, threshold)
        print(f"\nPour couvrir {threshold}% du test set → MAX_ARTICLE_AGE_DAYS ≥ {needed_days:.0f} jours")

else:
    print(f"\n✓ OK: {pct_valid:.2f}% des articles du test set sont éligibles")
    print(f"La fenêtre temporelle permet une évaluation raisonnable.")

print("\n" + "="*80)

# ============================================================================
# 6. DÉTERMINATION DE LA FENÊTRE TEMPORELLE OPTIMALE
# ============================================================================
print("\n" + "="*80)
print("CALCUL DE LA FENÊTRE TEMPORELLE OPTIMALE")
print("="*80)

# Filtrer les âges positifs uniquement (articles plus vieux que la date de split)
positive_ages = all_test_article_ages[all_test_article_ages >= 0]

print(f"\n1. ANALYSE DES ÂGES POSITIFS UNIQUEMENT:")
print(f"   Total articles avec âge ≥ 0: {len(positive_ages):,} / {len(all_test_article_ages):,} ({100.0*len(positive_ages)/len(all_test_article_ages):.2f}%)")

if len(positive_ages) > 0:
    print(f"   Min: {positive_ages.min():.1f} jours")
    print(f"   Max: {positive_ages.max():.1f} jours")
    print(f"   Médiane: {np.median(positive_ages):.1f} jours")
    print(f"   Moyenne: {positive_ages.mean():.1f} jours")

    # Calculer les quantiles sur les âges positifs
    print(f"\n2. QUANTILES (âges positifs uniquement):")
    quantiles_to_check = [0.50, 0.75, 0.90, 0.95, 0.99]
    for q in quantiles_to_check:
        age = np.percentile(positive_ages, q*100)
        count = len(positive_ages[positive_ages <= age])
        pct_positive = 100.0 * count / len(positive_ages)
        pct_total = 100.0 * count / len(all_test_article_ages)
        print(f"   P{int(q*100):2d}: {age:6.1f} jours (couvre {pct_positive:5.1f}% des âges+, {pct_total:5.1f}% du total)")

# Calculer la fenêtre recommandée basée sur les quantiles
print(f"\n3. RECOMMANDATIONS BASÉES SUR LES DONNÉES:")

# Option 1: P95 des âges positifs
if len(positive_ages) > 0:
    p95_positive = np.percentile(positive_ages, 95)
    coverage_p95 = 100.0 * len(all_test_article_ages[all_test_article_ages <= p95_positive]) / len(all_test_article_ages)

    p99_positive = np.percentile(positive_ages, 99)
    coverage_p99 = 100.0 * len(all_test_article_ages[all_test_article_ages <= p99_positive]) / len(all_test_article_ages)

    print(f"\n   A. P95 (âges positifs) = {p95_positive:.0f} jours")
    print(f"      → Couvre {coverage_p95:.2f}% du test set total")
    print(f"      → Exclut {100-coverage_p95:.2f}% des articles (outliers très vieux)")

    print(f"\n   B. P99 (âges positifs) = {p99_positive:.0f} jours")
    print(f"      → Couvre {coverage_p99:.2f}% du test set total")
    print(f"      → Exclut {100-coverage_p99:.2f}% des articles")

    # Recommandation finale
    print(f"\n" + "="*80)
    print("RECOMMANDATION FINALE")
    print("="*80)

    # Arrondir à la dizaine supérieure pour avoir une valeur propre
    recommended_window = int(np.ceil(p95_positive / 10) * 10)

    print(f"\n✓ FENÊTRE TEMPORELLE RECOMMANDÉE: {recommended_window} jours")
    print(f"\n  Justification:")
    print(f"    - Basé sur P95 des âges positifs ({p95_positive:.1f}j)")
    print(f"    - Arrondi à la dizaine supérieure: {recommended_window}j")
    print(f"    - Couverture estimée: {coverage_p95:.2f}% du test set")
    print(f"    - Exclut seulement {100-coverage_p95:.2f}% (outliers)")

    # Calculer la couverture exacte avec la fenêtre recommandée
    actual_coverage = 100.0 * len(all_test_article_ages[all_test_article_ages <= recommended_window]) / len(all_test_article_ages)
    print(f"    - Couverture réelle avec {recommended_window}j: {actual_coverage:.2f}%")

    print(f"\n  Alternative (plus conservatrice):")
    recommended_window_p99 = int(np.ceil(p99_positive / 10) * 10)
    actual_coverage_p99 = 100.0 * len(all_test_article_ages[all_test_article_ages <= recommended_window_p99]) / len(all_test_article_ages)
    print(f"    - P99: {recommended_window_p99} jours (couvre {actual_coverage_p99:.2f}%)")

else:
    recommended_window = 0
    print(f"\n⚠️  Pas d'articles avec âge positif → Pas de fenêtre temporelle nécessaire")

# Sauvegarder les stats
output_stats = {
    "total_test_articles": int(all_total_count),
    "valid_test_articles_60d": int(all_valid_count),
    "pct_valid": float(pct_valid),
    "age_min": float(all_test_article_ages.min()),
    "age_max": float(all_test_article_ages.max()),
    "age_mean": float(all_test_article_ages.mean()),
    "age_median": float(np.median(all_test_article_ages)),
    "age_p75": float(np.percentile(all_test_article_ages, 75)),
    "age_p90": float(np.percentile(all_test_article_ages, 90)),
    "age_p95": float(np.percentile(all_test_article_ages, 95)),
    "age_p99": float(np.percentile(all_test_article_ages, 99)),
    "positive_ages_count": int(len(positive_ages)) if len(positive_ages) > 0 else 0,
    "positive_ages_p95": float(np.percentile(positive_ages, 95)) if len(positive_ages) > 0 else 0,
    "positive_ages_p99": float(np.percentile(positive_ages, 99)) if len(positive_ages) > 0 else 0,
    "recommended_window_days": int(recommended_window),
    "recommended_window_coverage_pct": float(actual_coverage) if len(positive_ages) > 0 else 100.0,
}

with open("exploration_stats.json", "w") as f:
    json.dump(output_stats, f, indent=2)

print(f"\n✓ Statistiques sauvegardées dans: exploration_stats.json")
