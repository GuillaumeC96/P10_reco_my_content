"""
Script de test local du moteur de recommandation
"""

import sys
sys.path.append('lambda')

from recommendation_engine import RecommendationEngine
import json

def test_engine():
    """Test du moteur de recommandation"""
    print("=" * 80)
    print("TEST DU MOTEUR DE RECOMMANDATION")
    print("=" * 80)

    # 1. Initialiser le moteur
    print("\n[1/4] Initialisation du moteur...")
    engine = RecommendationEngine(models_path='./models')

    # 2. Charger les modèles
    print("\n[2/4] Chargement des modèles...")
    engine.load_models()

    # 3. Tester avec un utilisateur existant
    print("\n[3/4] Test avec un utilisateur existant (user_id=0)...")
    try:
        recs = engine.recommend(user_id=0, n_recommendations=5)
        print(f"\n✓ {len(recs)} recommandations générées:")
        for i, rec in enumerate(recs, 1):
            print(f"\n  {i}. Article {rec['article_id']}")
            print(f"     Score: {rec['score']:.4f}")
            print(f"     Catégorie: {rec['category_id']}")
            print(f"     Mots: {rec['words_count']}")
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

    # 4. Tester avec différents paramètres
    print("\n[4/4] Test avec différents paramètres...")

    # Test avec alpha différent
    print("\n  → Alpha = 0.8 (plus de collaborative)")
    recs_high_alpha = engine.recommend(user_id=0, n_recommendations=3, alpha=0.8)
    print(f"    {len(recs_high_alpha)} recommandations")

    # Test avec alpha faible
    print("\n  → Alpha = 0.3 (plus de content-based)")
    recs_low_alpha = engine.recommend(user_id=0, n_recommendations=3, alpha=0.3)
    print(f"    {len(recs_low_alpha)} recommandations")

    # Test sans diversité
    print("\n  → Sans filtre de diversité")
    recs_no_div = engine.recommend(user_id=0, n_recommendations=5, use_diversity=False)
    print(f"    {len(recs_no_div)} recommandations")

    # 5. Test cold start (nouvel utilisateur)
    print("\n[5/5] Test cold start (utilisateur inexistant)...")
    try:
        recs_cold = engine.recommend(user_id=999999, n_recommendations=5)
        print(f"\n✓ {len(recs_cold)} recommandations (popularity-based):")
        for i, rec in enumerate(recs_cold, 1):
            print(f"  {i}. Article {rec['article_id']} (score: {rec['score']:.4f})")
    except Exception as e:
        print(f"❌ Erreur: {e}")

    print("\n" + "=" * 80)
    print("✅ TESTS TERMINÉS")
    print("=" * 80)

if __name__ == "__main__":
    test_engine()
