"""
Test de la diversité des recommandations avec plusieurs utilisateurs
"""

import sys
sys.path.append('lambda')

from recommendation_engine import RecommendationEngine
import json

def test_diversity():
    """Test de diversité avec plusieurs utilisateurs"""
    print("=" * 80)
    print("TEST DE DIVERSITÉ DES RECOMMANDATIONS")
    print("=" * 80)

    # Initialiser
    engine = RecommendationEngine(models_path='./models')
    engine.load_models()

    # Lire quelques user_ids du fichier de profils
    with open('models/user_profiles.json', 'r') as f:
        profiles = json.load(f)

    # Prendre les 10 premiers utilisateurs avec plus de 10 interactions
    test_users = []
    for user_id_str, profile in profiles.items():
        if profile['num_interactions'] >= 10:
            test_users.append(int(user_id_str))
            if len(test_users) >= 10:
                break

    print(f"\n📊 Test avec {len(test_users)} utilisateurs\n")

    # Tester chaque utilisateur
    for user_id in test_users:
        try:
            recs = engine.recommend(user_id=user_id, n_recommendations=5, use_diversity=True)
            categories = [r['category_id'] for r in recs]
            unique_categories = len(set(categories))

            print(f"User {user_id:6d}: {unique_categories}/5 catégories uniques - {categories}")

            # Afficher détails si bonne diversité
            if unique_categories >= 3:
                print("  ✓ Bonne diversité!")
                for rec in recs:
                    print(f"    - Article {rec['article_id']:6d} (cat {rec['category_id']:3d}, score {rec['score']:.3f})")

        except Exception as e:
            print(f"User {user_id:6d}: ❌ Erreur - {e}")

    print("\n" + "=" * 80)
    print("✅ TEST TERMINÉ")
    print("=" * 80)

if __name__ == "__main__":
    test_diversity()
