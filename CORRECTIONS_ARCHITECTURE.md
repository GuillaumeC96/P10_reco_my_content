# Corrections Architecture - 26 Décembre 2024

## RÉSUMÉ DES CHANGEMENTS

Suite à la révision basée sur l'état de l'art (voir `REVISION_ARCHITECTURE.md`), les corrections suivantes ont été appliquées:

---

## 1. ✅ FENÊTRE TEMPORELLE DE HYPE (14 JOURS)

### Fichiers modifiés:
- `lambda/recommendation_engine.py`
- `azure_function/recommendation_engine.py`

### Changements:

**Constantes ajoutées:**
```python
class RecommendationEngine:
    # CONFIGURATION TEMPORELLE (State-of-Art pour News Recommendation)
    MAX_ARTICLE_AGE_DAYS = 14  # 2 semaines max pour recommandations
    TEMPORAL_HALF_LIFE_DAYS = 7  # Half-life: après 7 jours, score divisé par 2
    TEMPORAL_DECAY_LAMBDA = 0.099  # ln(2)/7 ≈ 0.099
```

**Méthode `_popularity_based()` modifiée:**
- Ajout paramètre `max_age_days` (défaut: 14 jours)
- Filtrage STRICT: articles > 14 jours sont EXCLUS
- Decay exponentiel maintenu pour articles dans la fenêtre
- Logging du nombre d'articles exclus

**Impact:**
- ✅ Aucun article > 14 jours ne sera recommandé
- ✅ Articles frais (0-7j) favorisés
- ✅ Articles 7-14j: score réduit progressivement
- ✅ Conforme état de l'art news recommendation

---

## 2. ✅ ARCHITECTURE HYBRIDE FORCÉE

### Fichiers modifiés:
- `lambda/config.py`
- `azure_function/config.py`

### Changements:

**AVANT (Trial 17 - DÉFAILLANT):**
```python
DEFAULT_WEIGHT_COLLAB = 0.0     # 0% - Trend pur
DEFAULT_WEIGHT_CONTENT = 0.0    # 0%
DEFAULT_WEIGHT_TREND = 1.0      # 100%
```

**APRÈS (State-of-Art):**
```python
DEFAULT_WEIGHT_CONTENT = 0.40   # 40% Content-Based (thématiques, cold-start)
DEFAULT_WEIGHT_COLLAB = 0.30    # 30% Collaborative (personnalisation)
DEFAULT_WEIGHT_TREND = 0.30     # 30% Temporal/Popularity (fraîcheur + diversité)
```

**Nouveaux paramètres ajoutés:**
```python
MAX_ARTICLE_AGE_DAYS = 14          # Fenêtre de hype: 2 semaines max
TEMPORAL_DECAY_LAMBDA = 0.099      # ln(2)/7 ≈ 0.099 (half-life 7 jours)
```

**Impact:**
- ✅ Personnalisation restaurée (vs trend-only)
- ✅ Résout le problème de bulle de filtre
- ✅ Cold-start géré par content-based
- ✅ Diversité améliorée

---

## 3. ✅ MÉTRIQUES D'ÉVALUATION ENRICHIES

### Fichiers modifiés:
- `evaluation/improved_tuning.py`

### Nouvelles métriques ajoutées:

**1. MRR@10 (Mean Reciprocal Rank)**
- Mesure vitesse à trouver un article pertinent
- Déjà existait, maintenant utilisé dans composite score

**2. Gini Coefficient**
```python
def gini_coefficient(self, all_recommendations):
    """
    Mesure l'inégalité de distribution des articles recommandés
    - 0 = parfaitement équilibré
    - 1 = bulle de filtre extrême

    State-of-Art: Gini < 0.5 acceptable, < 0.3 bon
    """
```

**3. Intra-User Diversity**
```python
def intra_user_diversity(self, recommended_articles):
    """
    Mesure variété thématique et de publishers pour un utilisateur

    Combine:
    - 70% diversité de catégories
    - 30% diversité de publishers

    State-of-Art: > 0.6 bon pour news
    """
```

**4. Temporal Diversity**
```python
def temporal_diversity(self, recommended_articles):
    """
    Mesure équilibre articles récents vs moins récents

    Utilise coefficient de variation de l'âge des articles
    Évite de recommander que du "breaking news"
    """
```

**Impact:**
- ✅ Détection des bulles de filtre (Gini)
- ✅ Mesure de la diversité individuelle
- ✅ Mesure de l'équilibre temporel
- ✅ Conforme état de l'art 2024

---

## 4. ✅ NOUVEAU COMPOSITE SCORE

### Fichiers modifiés:
- `evaluation/tuning_12_parallel_progressive.py`

### Changements:

**AVANT:**
```python
composite_score = (
    0.4 × NDCG@10 +
    0.3 × Recall@10 +
    0.2 × Diversity +
    0.1 × Novelty
)
```

**APRÈS (State-of-Art):**
```python
composite_score = (
    0.30 × NDCG@10 +          # Qualité ranking
    0.20 × MRR@10 +           # Vitesse pertinence
    0.20 × Recall@10 +        # Couverture
    0.20 × Intra_diversity +  # Variété individuelle
    0.10 × Temporal_div       # Diversité temporelle
)
```

**Impact:**
- ✅ Pénalise les systèmes sans diversité
- ✅ Favorise personnalisation
- ✅ Équilibre accuracy et diversité
- ✅ Conforme état de l'art

---

## 5. 🔄 PROCHAINES ÉTAPES

### Immédiat:
- [ ] **Créer script de tuning contraint** (`tuning_13_constrained.py`)
  - Level 2 contraint: content [0.30-0.50], collab [0.20-0.40], temporal [0.10-0.30]
  - Empêcher convergence vers extremums
  - Utiliser nouveau composite score

- [ ] **Lancer re-optimisation**
  - 30 trials avec contraintes
  - 50 users
  - Nouvelles métriques

- [ ] **Valider résultats**
  - Vérifier Gini < 0.5
  - Vérifier Intra-diversity > 0.6
  - Vérifier aucun article > 14j

### Court terme:
- [ ] Déployer version corrigée sur Azure
- [ ] Créer présentation des résultats
- [ ] Documenter trade-offs (score vs. diversité)

---

## 📊 COMPARAISON AVANT/APRÈS

| Aspect | AVANT (Trial 17) | APRÈS (Corrections) |
|--------|------------------|---------------------|
| **Architecture** | Trend 100% | Hybride 40:30:30 |
| **Personnalisation** | ❌ Aucune | ✅ Content + Collab |
| **Fenêtre temporelle** | ⚠️ Illimitée | ✅ Max 14 jours |
| **Métriques diversité** | ❌ Basique | ✅ Gini + Intra + Temporal |
| **Composite score** | 4 métriques | 5 métriques (MRR ajouté) |
| **Bulle de filtre** | ❌ Extrême | ✅ Contrôlée |
| **Cold-start** | ⚠️ Popularity seule | ✅ Content-based |

---

## ⚠️ TRADE-OFFS ACCEPTÉS

**Score composite attendu:**
- Trial 17: 0.2673 (+25.9% vs baseline)
- Avec contraintes: ~0.23-0.25 (estimation)
- **Baisse de ~5-10%**

**MAIS:**
- ✅ Système réellement personnalisé
- ✅ Bulle de filtre contrôlée
- ✅ Fraîcheur garantie (14j max)
- ✅ Conforme état de l'art académique
- ✅ Meilleure expérience utilisateur long terme

**Conclusion:** Sacrifice marginal de score pour gain substantiel de qualité métier

---

## 📚 RÉFÉRENCES

1. **Métriques:** Bauer et al. (2024) - "Exploring the Landscape of Recommender Systems Evaluation"
2. **Temporalité:** "Accurate News Recommendation Coalescing Personal and Global Temporal Preferences" (2020)
3. **Hybride:** "A Survey of Personalized News Recommendation" (2023)
4. **Diversité:** "Beyond-accuracy: a review on diversity, serendipity, and fairness" (2023)
5. **Bulle filtre:** "Filter Bubbles in Recommender Systems: Fact or Fallacy" (2024)

---

**Créé:** 26 Décembre 2024
**Status:** ✅ Corrections code terminées, re-optimisation nécessaire
**Priorité:** HAUTE
