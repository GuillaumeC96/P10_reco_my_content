"""
VERSION AMÉLIORÉE: Diversité Proportionnelle

CHANGEMENT MAJEUR:
Au lieu de forcer un équilibre 50/50 entre catégories,
on respecte les PROPORTIONS NATURELLES des préférences utilisateur.

Exemple:
  User aime: 90% foot, 10% cuisine
  Recos: ~80-85% foot, ~15-20% cuisine (légère découverte)

  Au lieu de: 50% foot, 50% cuisine (forcé artificiellement)
"""

def _diversity_filtering_proportional(self, articles: List[Tuple[int, float]], n_final: int = 5,
                                     diversity_strength: float = 0.2) -> List[Tuple[int, float]]:
    """
    Filtre de diversité qui respecte les proportions naturelles de l'utilisateur

    Args:
        articles: Liste de tuples (article_id, score) déjà triés par score
        n_final: Nombre final d'articles à retourner
        diversity_strength: Force de la diversification (0 = aucune, 1 = max)
                           0.2 = 20% de découverte, 80% respect des proportions

    Returns:
        Liste filtrée qui respecte les proportions + légère diversité

    Exemple:
        User historique: 90% foot, 10% cuisine
        diversity_strength = 0.2

        Proportions cibles:
          - Foot: 90% × (1 - 0.2) + (100% / nb_categories) × 0.2
                = 72% + 10% = 82%
          - Cuisine: 10% × (1 - 0.2) + 10% × 0.2
                   = 8% + 2% = 10%

        → On respecte largement les préférences (82% foot)
          tout en gardant un peu de découverte
    """
    if len(articles) <= n_final:
        return articles

    # Récupérer l'historique utilisateur pour calculer les proportions
    user_id = None  # On doit passer user_id en paramètre
    # Pour l'instant, on calcule les proportions depuis les scores des candidats

    # Créer des groupes par catégorie
    category_articles = {}
    category_total_scores = {}

    for article_id, score in articles:
        article_info = self.metadata[self.metadata['article_id'] == article_id]
        if not article_info.empty:
            category = article_info.iloc[0]['category_id']
            if category not in category_articles:
                category_articles[category] = []
                category_total_scores[category] = 0.0

            category_articles[category].append((article_id, score))
            category_total_scores[category] += score

    # Calculer les proportions naturelles (basées sur les scores)
    total_score = sum(category_total_scores.values())
    category_proportions = {
        cat: score / total_score if total_score > 0 else 1.0 / len(category_articles)
        for cat, score in category_total_scores.items()
    }

    # Appliquer diversity_strength pour lisser légèrement
    num_categories = len(category_articles)
    uniform_proportion = 1.0 / num_categories if num_categories > 0 else 1.0

    category_target_proportions = {}
    for cat, natural_prop in category_proportions.items():
        # Mix entre proportion naturelle et uniforme
        target = natural_prop * (1 - diversity_strength) + uniform_proportion * diversity_strength
        category_target_proportions[cat] = target

    # Calculer le nombre cible d'articles par catégorie
    category_target_counts = {
        cat: max(1, round(prop * n_final))  # Au moins 1 article par catégorie présente
        for cat, prop in category_target_proportions.items()
    }

    # Ajuster pour que la somme = n_final exactement
    total_count = sum(category_target_counts.values())
    if total_count != n_final:
        # Ajuster la catégorie dominante
        dominant_cat = max(category_target_proportions, key=category_target_proportions.get)
        category_target_counts[dominant_cat] += (n_final - total_count)

    # Trier chaque groupe par score
    for category in category_articles:
        category_articles[category].sort(key=lambda x: x[1], reverse=True)

    # Sélectionner selon les proportions cibles
    selected = []
    for category, target_count in sorted(category_target_counts.items(),
                                        key=lambda x: x[1], reverse=True):
        count = min(target_count, len(category_articles[category]))
        selected.extend(category_articles[category][:count])

    # Trier le résultat final par score
    selected.sort(key=lambda x: x[1], reverse=True)

    return selected[:n_final]


def _diversity_filtering_proportional_with_history(self, articles: List[Tuple[int, float]],
                                                   user_id: int, n_final: int = 5,
                                                   diversity_strength: float = 0.15) -> List[Tuple[int, float]]:
    """
    Version améliorée qui utilise l'HISTORIQUE RÉEL de l'utilisateur

    Args:
        articles: Liste de tuples (article_id, score)
        user_id: ID de l'utilisateur
        n_final: Nombre final d'articles
        diversity_strength: Force de diversification (0.15 = 15% de découverte)

    Returns:
        Liste respectant les proportions historiques + légère découverte
    """
    if len(articles) <= n_final:
        return articles

    # Calculer les proportions de l'historique utilisateur
    user_history = self._get_user_history(user_id)

    if len(user_history) == 0:
        # Cold start: utiliser diversité équilibrée
        return self._diversity_filtering(articles, n_final)

    # Compter les catégories dans l'historique
    user_category_counts = {}
    for article_id in user_history:
        if article_id in self.article_categories:
            category = self.article_categories[article_id]
            user_category_counts[category] = user_category_counts.get(category, 0) + 1

    total_history = sum(user_category_counts.values())

    # Proportions historiques (ce que l'utilisateur aime VRAIMENT)
    user_category_proportions = {
        cat: count / total_history
        for cat, count in user_category_counts.items()
    }

    logger.info(f"Proportions historiques user {user_id}: {user_category_proportions}")

    # Créer des groupes par catégorie parmi les candidats
    category_articles = {}
    for article_id, score in articles:
        if article_id in self.article_categories:
            category = self.article_categories[article_id]
            if category not in category_articles:
                category_articles[category] = []
            category_articles[category].append((article_id, score))

    # Calculer les proportions cibles avec légère diversification
    all_candidate_categories = set(category_articles.keys())
    num_candidate_categories = len(all_candidate_categories)

    category_target_proportions = {}
    for cat in all_candidate_categories:
        # Proportion historique (0 si jamais vu)
        historical_prop = user_category_proportions.get(cat, 0.0)

        # Proportion uniforme (pour la découverte)
        uniform_prop = 1.0 / num_candidate_categories

        # Mix: principalement historique + un peu de découverte
        target_prop = historical_prop * (1 - diversity_strength) + uniform_prop * diversity_strength
        category_target_proportions[cat] = target_prop

    # Normaliser pour sommer à 1.0
    total_prop = sum(category_target_proportions.values())
    if total_prop > 0:
        category_target_proportions = {
            cat: prop / total_prop
            for cat, prop in category_target_proportions.items()
        }

    logger.info(f"Proportions cibles après diversification ({diversity_strength*100:.0f}%): {category_target_proportions}")

    # Calculer le nombre cible d'articles par catégorie
    category_target_counts = {}
    for cat, prop in category_target_proportions.items():
        # Au moins 0, arrondi selon la proportion
        count = round(prop * n_final)
        if count > 0 or (prop > 0 and len(category_target_counts) < n_final):
            category_target_counts[cat] = max(1, count)  # Au moins 1 si présent

    # Ajuster pour que la somme = n_final
    total_count = sum(category_target_counts.values())
    if total_count != n_final:
        # Ajuster la catégorie dominante
        if len(category_target_counts) > 0:
            dominant_cat = max(category_target_proportions, key=category_target_proportions.get)
            adjustment = n_final - total_count
            category_target_counts[dominant_cat] = max(0, category_target_counts.get(dominant_cat, 0) + adjustment)

    logger.info(f"Nombre d'articles cibles par catégorie: {category_target_counts}")

    # Trier chaque groupe par score
    for category in category_articles:
        category_articles[category].sort(key=lambda x: x[1], reverse=True)

    # Sélectionner selon les proportions cibles
    selected = []
    for category, target_count in sorted(category_target_counts.items(),
                                        key=lambda x: x[1], reverse=True):
        available = len(category_articles.get(category, []))
        count = min(target_count, available)
        if count > 0:
            selected.extend(category_articles[category][:count])

    # Si on n'a pas assez, compléter avec les meilleurs scores restants
    if len(selected) < n_final:
        remaining = [a for a in articles if a not in selected]
        selected.extend(remaining[:n_final - len(selected)])

    # Trier le résultat final par score (optionnel, selon si on veut garder l'ordre par catégorie)
    selected.sort(key=lambda x: x[1], reverse=True)

    return selected[:n_final]


# EXEMPLE D'UTILISATION dans recommend():
# Remplacer cette ligne:
#   final_articles = self._diversity_filtering(candidate_articles, n_final=n_recommendations)
# Par:
#   final_articles = self._diversity_filtering_proportional_with_history(
#       candidate_articles, user_id, n_final=n_recommendations, diversity_strength=0.15
#   )


"""
COMPARAISON DES APPROCHES:

1. ANCIENNE (Round-Robin forcé):
   User: 90% foot, 10% cuisine
   Top 10 candidats: 8 foot (scores élevés), 2 cuisine (scores moyens)
   Résultat: 5 foot, 5 cuisine (FORCÉ 50/50)
   ❌ Perd les meilleurs articles de foot
   ❌ Sur-représente la cuisine

2. NOUVELLE (Proportionnelle avec légère découverte):
   User: 90% foot, 10% cuisine
   diversity_strength = 0.15 (15% découverte)

   Proportions cibles:
     - Foot: 90% × 0.85 + 10% × 0.15 = 78%
     - Cuisine: 10% × 0.85 + 10% × 0.15 = 10%

   Sur 10 recos:
     - Foot: 8 articles (78% ≈ 8/10)
     - Cuisine: 1 article (10% ≈ 1/10)
     - Autre: 1 article (découverte)

   ✅ Respecte les préférences (8 foot sur 10)
   ✅ Garde les meilleurs scores
   ✅ Légère découverte (1-2 articles différents)

3. PARAMÈTRE diversity_strength:
   - 0.0: 100% respect des proportions (pas de découverte)
   - 0.15: 85% proportions + 15% découverte (RECOMMANDÉ)
   - 0.30: 70% proportions + 30% découverte
   - 1.0: 100% uniforme (comme round-robin)
"""
