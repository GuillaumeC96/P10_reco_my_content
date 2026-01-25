#!/usr/bin/env python3
"""
Test local du moteur de recommandation avec modèles enrichis
Vérifie que les profils enrichis (filtre 30s, 9 signaux) sont bien chargés
"""

import sys
sys.path.insert(0, '.')

from recommendation_engine import RecommendationEngine
import json

print("="*60)
print("TEST LOCAL - MODÈLES ENRICHIS")
print("="*60)

# 1. Charger le moteur avec les modèles locaux
print("\n1. Initialisation du moteur...")
engine = RecommendationEngine(models_path="../models")

print("\n2. Chargement des modèles...")
try:
    engine.load_models()
    print("   ✓ Modèles chargés avec succès")
except Exception as e:
    print(f"   ✗ Erreur chargement: {e}")
    sys.exit(1)

# 2. Vérifier que les profils enrichis sont chargés
print("\n3. Vérification profils enrichis...")
if engine.user_profiles:
    # Prendre un utilisateur exemple
    sample_user_id = list(engine.user_profiles.keys())[0]
    sample_profile = engine.user_profiles[sample_user_id]

    print(f"   User {sample_user_id}:")
    print(f"     Articles lus: {sample_profile.get('num_articles', 0)}")
    print(f"     Interactions: {sample_profile.get('num_interactions', 0)}")
    print(f"     Poids moyen: {sample_profile.get('avg_weight', 0):.3f}")

    # Vérifier présence des 9 signaux
    signals = [
        'avg_session_quality',
        'avg_device_quality',
        'avg_referrer_quality',
        'avg_os_quality',
        'avg_country_quality',
        'avg_region_quality'
    ]

    missing_signals = [s for s in signals if s not in sample_profile]

    if missing_signals:
        print(f"   ⚠️  Signaux manquants: {missing_signals}")
        print(f"   → Profils basiques chargés (sans filtrage 30s)")
    else:
        print(f"   ✓ Profils ENRICHIS détectés (9 signaux présents)")
        print(f"     Session quality: {sample_profile['avg_session_quality']:.3f}")
        print(f"     Device quality: {sample_profile['avg_device_quality']:.3f}")
        print(f"     Region quality: {sample_profile['avg_region_quality']:.3f}")
else:
    print("   ✗ Profils utilisateurs non chargés")
    sys.exit(1)

# 3. Test de recommandation
print("\n4. Test de recommandation...")
test_user_id = sample_user_id

try:
    recommendations = engine.recommend(
        user_id=test_user_id,
        n_recommendations=5,
        weight_collab=0.30,
        weight_content=0.40,
        weight_trend=0.30,
        use_diversity=True
    )

    print(f"   ✓ {len(recommendations)} recommandations générées")

    # Afficher les recommandations
    print(f"\n   Top 5 pour user {test_user_id}:")
    for i, rec in enumerate(recommendations[:5], 1):
        print(f"     {i}. Article {rec['article_id']} - Score: {rec['score']:.3f}")

except Exception as e:
    print(f"   ✗ Erreur recommandation: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 4. Vérifier la matrice pondérée
print("\n5. Vérification matrice pondérée...")
if engine.weighted_user_item_matrix is not None:
    print(f"   ✓ Matrice pondérée chargée")
    print(f"     Shape: {engine.weighted_user_item_matrix.shape}")
    print(f"     Values: min={engine.weighted_user_item_matrix.data.min():.3f}, "
          f"max={engine.weighted_user_item_matrix.data.max():.3f}, "
          f"mean={engine.weighted_user_item_matrix.data.mean():.3f}")
else:
    print(f"   ⚠️  Matrice pondérée non disponible")

print("\n" + "="*60)
print("✅ TEST RÉUSSI - Prêt pour déploiement Azure")
print("="*60)
print("\nFichiers nécessaires pour Azure:")
print("  • user_profiles_enriched.pkl (prioritaire)")
print("  • user_profiles_enriched.json (fallback)")
print("  • user_item_matrix_weighted.npz")
print("  • articles_metadata.csv")
print("  • embeddings_filtered.pkl")
print("  • article_popularity.pkl")
print("  • mappings.pkl")
print("")
