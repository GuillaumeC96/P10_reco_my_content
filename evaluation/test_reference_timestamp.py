#!/usr/bin/env python3
"""
Test rapide pour vérifier que reference_timestamp fonctionne
"""

import sys
sys.path.append('../lambda')

from improved_tuning import ImprovedRecommendationEvaluator

print("="*80)
print("TEST: Reference Timestamp")
print("="*80)

# Créer l'évaluateur
evaluator = ImprovedRecommendationEvaluator(models_path="../models")

# Charger le moteur
print("\n[1/3] Chargement du moteur...")
evaluator.load_engine()
print("✓ Moteur chargé")

# Créer le split temporel (cela calcule aussi les reference_timestamps)
print("\n[2/3] Création du split temporel...")
evaluator.create_temporal_split(train_ratio=0.8, min_interactions=10)
print(f"✓ {len(evaluator.user_reference_timestamps)} timestamps de référence calculés")

# Tester sur un utilisateur
print("\n[3/3] Test sur un utilisateur...")
test_users = list(evaluator.val_interactions.keys())[:5]

for user_id in test_users:
    print(f"\n  User {user_id}:")

    # Vérifier qu'on a un timestamp de référence
    if user_id in evaluator.user_reference_timestamps:
        ref_ts = evaluator.user_reference_timestamps[user_id]
        print(f"    Reference timestamp: {ref_ts}")

        # Date de référence
        import datetime
        ref_date = datetime.datetime.fromtimestamp(ref_ts / 1000)
        print(f"    Reference date: {ref_date.strftime('%Y-%m-%d')}")
    else:
        print(f"    ❌ Pas de timestamp de référence!")
        continue

    # Évaluer
    try:
        metrics = evaluator.evaluate_user(
            user_id=user_id,
            weight_collab=0.30,
            weight_content=0.40,
            weight_trend=0.30,
            k=10
        )

        if metrics:
            print(f"    Precision@10: {metrics['precision@10']:.4f}")
            print(f"    Recall@10: {metrics['recall@10']:.4f}")
            print(f"    ✓ Recommandations générées avec succès!")
        else:
            print(f"    ⚠️  Pas de métriques (pas de relevant articles?)")

    except Exception as e:
        print(f"    ❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

print("\n" + "="*80)
print("FIN DU TEST")
print("="*80)
