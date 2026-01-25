#!/usr/bin/env python3
"""
Exploration de données complète pour diagnostiquer le problème de scores = 0.0

Analyse:
1. Distribution des âges des articles
2. Articles disponibles après filtrage 60 jours
3. Composition du validation set
4. Test recommandations sur utilisateurs échantillon
5. Vérification Precision@10/Recall@10 étape par étape
"""

import json
import pickle
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Configuration
MODELS_DIR = Path("../models")
MAX_ARTICLE_AGE_DAYS = 60
TEMPORAL_DECAY_LAMBDA = 0.099

print("="*80)
print("DIAGNOSTIC - EXPLORATION DE DONNÉES")
print("="*80)

# ============================================================================
# 1. CHARGEMENT DES DONNÉES
# ============================================================================
print("\n[1/6] Chargement des données...")

# Articles metadata
articles_df = pd.read_csv(MODELS_DIR / "articles_metadata.csv")
print(f"  ✓ {len(articles_df):,} articles chargés")

# User profiles (format pickle car enriched)
with open(MODELS_DIR / "user_profiles_enriched.pkl", "rb") as f:
    user_profiles = pickle.load(f)
print(f"  ✓ {len(user_profiles):,} profils utilisateurs")

# Interaction stats
interaction_stats = pd.read_csv(MODELS_DIR / "interaction_stats_enriched.csv")
print(f"  ✓ {len(interaction_stats):,} stats d'interaction")

# ============================================================================
# 2. ANALYSE DES ÂGES DES ARTICLES
# ============================================================================
print("\n[2/6] Analyse des âges des articles...")

# Convertir created_at_ts en dates (timestamps en MILLISECONDES)
articles_df['created_at'] = pd.to_datetime(articles_df['created_at_ts'], unit='ms')

# Date de référence (date la plus récente dans le dataset)
reference_date = articles_df['created_at'].max()
print(f"  📅 Date de référence (article le plus récent): {reference_date.strftime('%Y-%m-%d')}")

# Calculer l'âge de chaque article
articles_df['age_days'] = (reference_date - articles_df['created_at']).dt.days

# Distribution des âges
print(f"\n  Distribution des âges des articles:")
print(f"    Min: {articles_df['age_days'].min()} jours")
print(f"    Max: {articles_df['age_days'].max()} jours")
print(f"    Moyenne: {articles_df['age_days'].mean():.1f} jours")
print(f"    Médiane: {articles_df['age_days'].median():.1f} jours")

# Quantiles
quantiles = [0.10, 0.25, 0.50, 0.75, 0.90, 0.95, 0.99]
print(f"\n  Quantiles:")
for q in quantiles:
    age = articles_df['age_days'].quantile(q)
    print(f"    {int(q*100)}%: {age:.1f} jours")

# Articles par tranche d'âge
tranches = [
    (0, 7, "0-7 jours (semaine)"),
    (8, 14, "8-14 jours (2 semaines)"),
    (15, 30, "15-30 jours (mois)"),
    (31, 60, "31-60 jours"),
    (61, 90, "61-90 jours"),
    (91, 180, "91-180 jours"),
    (181, 365, "181-365 jours"),
    (366, 10000, ">365 jours")
]

print(f"\n  Articles par tranche d'âge:")
for min_age, max_age, label in tranches:
    count = len(articles_df[(articles_df['age_days'] >= min_age) & (articles_df['age_days'] <= max_age)])
    pct = 100.0 * count / len(articles_df)
    print(f"    {label:20s}: {count:6,} ({pct:5.2f}%)")

# Articles disponibles après filtrage 60 jours
articles_valid = articles_df[articles_df['age_days'] <= MAX_ARTICLE_AGE_DAYS]
print(f"\n  🔍 CRITIQUE: Articles ≤ {MAX_ARTICLE_AGE_DAYS} jours: {len(articles_valid):,} / {len(articles_df):,} ({100.0*len(articles_valid)/len(articles_df):.2f}%)")

if len(articles_valid) == 0:
    print("  ❌ PROBLÈME IDENTIFIÉ: Aucun article ≤ 60 jours dans le dataset!")
    print("     → Tous les articles sont trop vieux pour la fenêtre temporelle")
    print("     → Score 0.0 attendu car aucune recommandation possible")

# ============================================================================
# 3. ANALYSE DU VALIDATION SET
# ============================================================================
print("\n[3/6] Analyse du validation set...")

# Créer le split temporel comme dans improved_tuning.py
train_dict = {}
test_dict = {}
train_ratio = 0.8
min_interactions = 10

for user_id, profile in user_profiles.items():
    articles = profile['articles_read']

    if len(articles) < min_interactions:
        continue

    # Split temporel : les articles sont déjà triés chronologiquement
    split_idx = int(len(articles) * train_ratio)

    # S'assurer qu'on a au moins 1 article dans chaque split
    if split_idx > 0 and split_idx < len(articles):
        train_dict[user_id] = articles[:split_idx]
        test_dict[user_id] = articles[split_idx:]

print(f"  ✓ Split créé: {len(test_dict):,} users (80% train / 20% test)")
print(f"  ✓ Total train: {sum(len(v) for v in train_dict.values()):,} interactions")
print(f"  ✓ Total test: {sum(len(v) for v in test_dict.values()):,} interactions")

# Analyser quelques utilisateurs de test
sample_users = list(test_dict.keys())[:5]
print(f"\n  Analyse de 5 utilisateurs échantillon:")

for user_id in sample_users:
    test_articles = test_dict[user_id]
    train_articles = train_dict.get(user_id, [])

    # articles_read est une liste d'IDs (int), pas de tuples
    test_article_ids = test_articles
    test_ages = articles_df[articles_df['article_id'].isin(test_article_ids)]['age_days'].values

    valid_test = sum(1 for age in test_ages if age <= MAX_ARTICLE_AGE_DAYS)

    print(f"    User {user_id}:")
    print(f"      Train: {len(train_articles)} articles | Test: {len(test_articles)} articles")
    print(f"      Test ≤60j: {valid_test}/{len(test_articles)} articles")
    if len(test_ages) > 0:
        print(f"      Âges test: min={test_ages.min():.0f}j, max={test_ages.max():.0f}j, moy={test_ages.mean():.0f}j")

# ============================================================================
# 4. TEST RECOMMANDATION SUR UN UTILISATEUR
# ============================================================================
print("\n[4/6] Test de recommandation détaillé sur un utilisateur...")

# Importer le moteur
sys.path.insert(0, str(Path("../lambda").resolve()))
from recommendation_engine import RecommendationEngine

# Charger le moteur
print("  Chargement du moteur de recommandation...")
engine = RecommendationEngine(models_path=str(MODELS_DIR))

# Prendre un utilisateur de test
test_user_id = sample_users[0]
print(f"\n  Test avec user_id: {test_user_id}")

# Paramètres de test
test_params = {
    'weight_content': 0.40,
    'weight_collab': 0.30,
    'weight_trend': 0.30,
    'top_n': 10
}

print(f"  Paramètres: Content={test_params['weight_content']}, Collab={test_params['weight_collab']}, Trend={test_params['weight_trend']}")

try:
    recommendations = engine.get_recommendations(
        user_id=test_user_id,
        top_n=test_params['top_n'],
        weight_content=test_params['weight_content'],
        weight_collab=test_params['weight_collab'],
        weight_trend=test_params['weight_trend']
    )

    print(f"\n  Recommandations générées: {len(recommendations)}")

    if len(recommendations) > 0:
        # Analyser les âges des articles recommandés
        rec_article_ids = [r['article_id'] for r in recommendations]
        rec_ages = articles_df[articles_df['article_id'].isin(rec_article_ids)]['age_days'].values

        print(f"  Âges des articles recommandés:")
        print(f"    Min: {rec_ages.min():.0f} jours")
        print(f"    Max: {rec_ages.max():.0f} jours")
        print(f"    Moyenne: {rec_ages.mean():.1f} jours")

        # Afficher top 5
        print(f"\n  Top 5 recommandations:")
        for i, rec in enumerate(recommendations[:5], 1):
            article = articles_df[articles_df['article_id'] == rec['article_id']].iloc[0]
            age = article['age_days']
            print(f"    {i}. Article {rec['article_id']} (score={rec['score']:.4f}, âge={age:.0f}j)")
    else:
        print("  ❌ PROBLÈME: Aucune recommandation générée!")
        print("     → Vérifier pourquoi le moteur ne retourne rien")

except Exception as e:
    print(f"  ❌ ERREUR lors de la génération: {e}")
    import traceback
    traceback.print_exc()

# ============================================================================
# 5. CALCUL MÉTRIQUE DÉTAILLÉ
# ============================================================================
print("\n[5/6] Calcul de Precision@10 et Recall@10 étape par étape...")

if len(recommendations) > 0:
    # Ground truth (articles du test set)
    test_articles = test_dict[test_user_id]
    relevant_articles = set([a[0] for a in test_articles])

    # Articles recommandés
    recommended_articles = set([r['article_id'] for r in recommendations[:10]])

    # Intersection
    hits = recommended_articles.intersection(relevant_articles)

    # Métriques
    precision_10 = len(hits) / 10 if len(recommended_articles) > 0 else 0.0
    recall_10 = len(hits) / len(relevant_articles) if len(relevant_articles) > 0 else 0.0

    print(f"\n  Ground truth (test set): {len(relevant_articles)} articles pertinents")
    print(f"  Recommandations: {len(recommended_articles)} articles")
    print(f"  Hits (intersection): {len(hits)} articles")
    print(f"\n  Precision@10: {precision_10:.4f} ({len(hits)}/10)")
    print(f"  Recall@10: {recall_10:.4f} ({len(hits)}/{len(relevant_articles)})")

    # Vérifier si les articles pertinents sont ≤60j
    relevant_ages = articles_df[articles_df['article_id'].isin(relevant_articles)]['age_days'].values
    valid_relevant = sum(1 for age in relevant_ages if age <= MAX_ARTICLE_AGE_DAYS)

    print(f"\n  Articles pertinents ≤60j: {valid_relevant}/{len(relevant_articles)}")
    if valid_relevant == 0:
        print("  ❌ PROBLÈME: Aucun article pertinent ≤60 jours!")
        print("     → Impossible d'avoir Precision/Recall > 0 avec fenêtre 60j")

else:
    print("  ⚠️ Impossible de calculer les métriques (aucune recommandation)")

# ============================================================================
# 6. RÉSUMÉ DIAGNOSTIC
# ============================================================================
print("\n" + "="*80)
print("RÉSUMÉ DIAGNOSTIC")
print("="*80)

total_articles = len(articles_df)
valid_articles = len(articles_valid)
pct_valid = 100.0 * valid_articles / total_articles if total_articles > 0 else 0

print(f"\n1. DATASET:")
print(f"   - Total articles: {total_articles:,}")
print(f"   - Articles ≤60j: {valid_articles:,} ({pct_valid:.2f}%)")
print(f"   - Date référence: {reference_date.strftime('%Y-%m-%d')}")
print(f"   - Âge médian: {articles_df['age_days'].median():.0f} jours")

print(f"\n2. VALIDATION SET:")
print(f"   - Users test: {len(test_dict):,}")
print(f"   - Analysé: {len(sample_users)} users échantillon")

print(f"\n3. RECOMMANDATIONS:")
if len(recommendations) > 0:
    print(f"   - Générées: {len(recommendations)} articles")
    print(f"   - Âge moyen: {rec_ages.mean():.1f} jours")
    print(f"   ✓ Moteur fonctionne")
else:
    print(f"   ❌ Aucune recommandation générée")

print(f"\n4. MÉTRIQUES:")
if len(recommendations) > 0:
    print(f"   - Precision@10: {precision_10:.4f}")
    print(f"   - Recall@10: {recall_10:.4f}")
    print(f"   - Composite (69%P+31%R): {0.69*precision_10 + 0.31*recall_10:.4f}")
else:
    print(f"   ❌ Impossible à calculer")

# DIAGNOSTIC FINAL
print(f"\n" + "="*80)
print("DIAGNOSTIC FINAL")
print("="*80)

if valid_articles == 0:
    print("\n❌ CAUSE RACINE IDENTIFIÉE: Dataset trop ancien")
    print("\nTOUS les articles ont > 60 jours.")
    print("La fenêtre temporelle de 60 jours exclut 100% du dataset.")
    print("\nSOLUTIONS:")
    print("  A. Augmenter MAX_ARTICLE_AGE_DAYS (ex: 365 jours)")
    print("  B. Utiliser la date de validation au lieu de la date max")
    print("  C. Désactiver complètement le filtrage temporel")

elif valid_articles < 1000:
    print(f"\n⚠️  PROBLÈME: Dataset trop restreint après filtrage")
    print(f"\nSeulement {pct_valid:.1f}% des articles passent le filtre 60 jours.")
    print("Pas assez d'articles pour faire des recommandations de qualité.")
    print("\nSOLUTION: Augmenter MAX_ARTICLE_AGE_DAYS à 180-365 jours")

elif len(recommendations) == 0:
    print("\n❌ PROBLÈME: Moteur ne génère pas de recommandations")
    print("\nLe dataset a des articles valides mais le moteur ne retourne rien.")
    print("SOLUTION: Investiguer le code du moteur de recommandation")

elif precision_10 == 0 and recall_10 == 0:
    print("\n❌ PROBLÈME: Recommandations ne matchent pas le ground truth")
    print("\nLe moteur génère des recommandations mais aucune n'est pertinente.")
    if valid_relevant == 0:
        print("Les articles du test set ont tous > 60 jours.")
        print("SOLUTION: Ajuster la fenêtre temporelle ou revoir le split train/test")
    else:
        print("SOLUTION: Vérifier l'algorithme de recommandation")

else:
    print("\n✓ Système fonctionne (métriques > 0)")
    print(f"\nComposite score: {0.69*precision_10 + 0.31*recall_10:.4f}")

print("\n" + "="*80)
