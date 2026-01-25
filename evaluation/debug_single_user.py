#!/usr/bin/env python3
"""
Debug détaillé pour un utilisateur
"""

import sys
sys.path.append('../lambda')

from improved_tuning import ImprovedRecommendationEvaluator
import pandas as pd

# Créer l'évaluateur
evaluator = ImprovedRecommendationEvaluator(models_path="../models")
evaluator.load_engine()
evaluator.create_temporal_split(train_ratio=0.8, min_interactions=10)

# Prendre le premier utilisateur
user_id = list(evaluator.val_interactions.keys())[0]

print("="*80)
print(f"DEBUG USER {user_id}")
print("="*80)

# Articles de train
train_articles = evaluator.train_interactions[user_id]
print(f"\nTrain articles: {len(train_articles)}")
print(f"  IDs: {train_articles[:5]}... (showing first 5)")

# Articles de test (ground truth)
test_articles = evaluator.val_interactions[user_id]
print(f"\nTest articles (ground truth): {len(test_articles)}")
print(f"  IDs: {test_articles}")

# Timestamp de référence
ref_ts = evaluator.user_reference_timestamps[user_id]
print(f"\nReference timestamp: {ref_ts}")

import datetime
ref_date = datetime.datetime.fromtimestamp(ref_ts / 1000)
print(f"Reference date: {ref_date.strftime('%Y-%m-%d %H:%M:%S')}")

# Vérifier l'âge des articles de test par rapport à la date de référence
articles_df = pd.read_csv("../models/articles_metadata.csv")

print(f"\n" + "="*80)
print("ÂGES DES ARTICLES DE TEST (par rapport à la date de split)")
print("="*80)

for test_article_id in test_articles:
    article_row = articles_df[articles_df['article_id'] == test_article_id]
    if not article_row.empty:
        created_ts = article_row.iloc[0]['created_at_ts']
        age_days = (ref_ts - created_ts) / (1000 * 86400)
        created_date = datetime.datetime.fromtimestamp(created_ts / 1000)

        status = "✓ Éligible" if age_days <= 60 else "❌ Trop vieux"
        print(f"  Article {test_article_id}: {age_days:6.1f} jours ({created_date.strftime('%Y-%m-%d')}) - {status}")

# Générer les recommandations
print(f"\n" + "="*80)
print("RECOMMANDATIONS GÉNÉRÉES")
print("="*80)

evaluator._mask_user_profile(user_id)

recommendations = evaluator.engine.recommend(
    user_id=user_id,
    n_recommendations=10,
    weight_collab=0.30,
    weight_content=0.40,
    weight_trend=0.30,
    use_diversity=False,
    reference_timestamp=ref_ts
)

evaluator._restore_user_profile(user_id)

print(f"\n{len(recommendations)} recommandations:")
recommended_ids = [rec['article_id'] for rec in recommendations]

for i, rec in enumerate(recommendations, 1):
    article_id = rec['article_id']
    score = rec['score']

    article_row = articles_df[articles_df['article_id'] == article_id]
    if not article_row.empty:
        created_ts = article_row.iloc[0]['created_at_ts']
        age_days = (ref_ts - created_ts) / (1000 * 86400)
        created_date = datetime.datetime.fromtimestamp(created_ts / 1000)

        in_ground_truth = "✓ IN GROUND TRUTH" if article_id in test_articles else ""
        print(f"  {i}. Article {article_id} (score={score:.4f}, âge={age_days:.1f}j, {created_date.strftime('%Y-%m-%d')}) {in_ground_truth}")

# Intersection
hits = set(recommended_ids).intersection(set(test_articles))
print(f"\n" + "="*80)
print(f"RÉSULTAT")
print("="*80)
print(f"\nRecommandations: {len(recommended_ids)}")
print(f"Ground truth: {len(test_articles)}")
print(f"Intersection: {len(hits)}")
print(f"\nPrecision@10: {len(hits)}/10 = {len(hits)/10:.4f}")
print(f"Recall@10: {len(hits)}/{len(test_articles)} = {len(hits)/len(test_articles):.4f}" if len(test_articles) > 0 else "N/A")

if len(hits) == 0:
    print("\n❌ PROBLÈME: Aucun article recommandé ne matche le ground truth!")
    print("\nHYPOTHÈSES:")
    print("  1. Les articles du ground truth sont tous exclus par la fenêtre temporelle")
    print("  2. Le moteur ne recommande que des articles populaires qui ne sont pas dans le ground truth")
    print("  3. Le collaborative/content-based ne trouve pas les articles du ground truth")
else:
    print(f"\n✓ {len(hits)} articles matchent!")

print("\n" + "="*80)
