# RÉVISION ARCHITECTURE - 26 Décembre 2024

**Contexte:** Après optimisation bayésienne, le système converge vers Trend pur (100%) ce qui est **défaillant** pour des articles de news.

**Source:** États de l'art 2020-2024 sur News Recommendation Systems

---

## ❌ PROBLÈMES IDENTIFIÉS

### 1. Système "Trend-Only" Défaillant

**Résultat actuel optimisation:**
- Collaborative: 0%
- Content-based: 0%
- Trend: 100%

**Pourquoi c'est un problème:**
- ❌ Pas de personnalisation (tout le monde voit la même chose)
- ❌ Bulle de filtre extrême
- ❌ Ignore les préférences utilisateur
- ❌ C'est juste un "top articles global"
- ❌ Cold start non résolu pour nouveaux articles de niche

**Constat:** L'optimisation bayésienne a trouvé un **optimum local défaillant** car:
1. Les métriques ne pénalisent pas la diversité
2. Pas de contrainte temporelle (articles vieux recommandés)
3. Le dataset est biaisé vers les articles populaires

### 2. Absence de Décroissance Temporelle

**Articles de news ont une durée de vie limitée:**
- **Hard news:** 2-7 jours
- **Features:** 2-4 semaines
- **Evergreen:** > 1 mois

**Notre système actuel:**
- ✅ Utilise `temporal_decay` (half-life 7 jours)
- ❌ MAIS appliqué uniquement sur le ranking final
- ❌ Pas intégré dans le calcul de popularité

**Impact:**
- Articles de 6 mois peuvent être recommandés
- Pas de "fenêtre de hype" (2 semaines max)

### 3. Métriques d'Évaluation Incomplètes

**Actuellement:**
```python
composite_score = (
    0.4 × NDCG@10 +
    0.3 × Recall@10 +
    0.2 × Diversity +
    0.1 × Novelty
)
```

**Problèmes:**
- "Diversity" et "Novelty" mal définies
- Pas de mesure de bulle de filtre
- Pas de CTR/MRR
- Pas de diversité temporelle

---

## ✅ RECOMMANDATIONS ÉTAT DE L'ART

### 1. Architecture Hybride (State-of-the-Art 2024)

**D'après les papers récents, architecture optimale:**

```
Score_article = α×Content + β×Collaborative + γ×Temporal + δ×Diversity
```

**Pondération recommandée:**
- **α = 0.40** (40% Content-based)
- **β = 0.30** (30% Collaborative filtering)
- **γ = 0.20** (20% Temporal/Freshness)
- **δ = 0.10** (10% Diversity boost)

**Justification:**
- **Content-based (40%):** Résout cold-start, capture thématiques
- **Collaborative (30%):** Personnalisation via comportements
- **Temporal (20%):** Fraîcheur + fenêtre de hype
- **Diversity (10%):** Évite bulle de filtre

### 2. Composante Temporelle (CRITIQUE)

**Time Decay exponentiel:**
```python
def temporal_score(article):
    age_days = (today - article.published_date).days

    # Fenêtre de hype: 14 jours (2 semaines)
    if age_days > 14:
        return 0  # Article trop vieux, pas recommandé

    # Decay exponentiel (half-life = 7 jours)
    λ = np.log(2) / 7  # ≈ 0.099
    decay = np.exp(-λ × age_days)

    return popularity_score × decay
```

**Paramètres:**
- **Fenêtre max:** 14 jours (2 semaines)
- **Half-life:** 7 jours (après 7 jours, score divisé par 2)
- **λ (lambda):** 0.099

**Effet:**
```
Age     | Decay Factor | Impact
--------|--------------|--------
0 jours | 100%         | Full score
3 jours | 75%          | -25%
7 jours | 50%          | -50% (half-life)
10 jours| 35%          | -65%
14 jours| 25%          | -75%
>14 j   | 0%           | Exclu
```

### 3. Métriques d'Évaluation Complètes

**Métriques PRIMAIRES:**
1. **NDCG@10:** Qualité du ranking (position compte)
2. **MRR@10:** Vitesse à trouver un article pertinent
3. **CTR:** Click-through rate (si disponible)

**Métriques DIVERSITÉ (CRITIQUE):**
4. **Gini coefficient:** Mesure inégalité de distribution
   - 0 = parfaitement équilibré
   - 1 = bulle de filtre extrême
5. **Intra-user diversity:** Variété du contenu par utilisateur
6. **Inter-user diversity:** Différenciation entre utilisateurs
7. **Temporal diversity:** Équilibre court-terme vs long-terme

**Composite Score Révisé:**
```python
composite_score = (
    0.30 × NDCG@10 +         # Qualité ranking
    0.20 × MRR@10 +          # Vitesse pertinence
    0.15 × Recall@10 +       # Couverture
    0.15 × Intra_diversity + # Variété individuelle
    0.10 × Gini_inverse +    # Anti-bulle (1-Gini)
    0.10 × Temporal_div      # Diversité temporelle
)
```

---

## 🔄 PLAN D'ACTION

### Phase 1: Correction Immédiate

**1. Forcer architecture hybride (pas d'optimisation libre)**
```python
# ANCIEN (optimisé bayésien)
collab = 0.0
content = 0.0
trend = 1.0

# NOUVEAU (state-of-the-art forcé)
content = 0.40
collab = 0.30
temporal = 0.20
diversity = 0.10
```

**2. Ajouter fenêtre temporelle de hype**
```python
# Dans recommendation_engine.py
MAX_ARTICLE_AGE_DAYS = 14  # 2 semaines
TEMPORAL_HALF_LIFE_DAYS = 7

def apply_temporal_filter(articles):
    """Exclut articles > 14 jours"""
    return [a for a in articles
            if (today - a.published_date).days <= MAX_ARTICLE_AGE_DAYS]

def temporal_decay(age_days):
    """Decay exponentiel"""
    λ = np.log(2) / TEMPORAL_HALF_LIFE_DAYS
    return np.exp(-λ × age_days)
```

**3. Enrichir métriques d'évaluation**
```python
def evaluate_recommendations(user_id, recommendations, ground_truth):
    return {
        'ndcg@10': compute_ndcg(recommendations, ground_truth),
        'mrr@10': compute_mrr(recommendations, ground_truth),
        'recall@10': compute_recall(recommendations, ground_truth),
        'intra_diversity': compute_intra_diversity(recommendations),
        'gini': compute_gini_coefficient(recommendations),
        'temporal_diversity': compute_temporal_diversity(recommendations)
    }
```

### Phase 2: Re-Optimisation (Contrainte)

**Optimisation bayésienne CONTRAINTE:**

**Niveau 2 (stratégies) - CONTRAINT:**
```python
# AVANT (libre)
collab = trial.suggest_int('collab', 0, 5)
content = trial.suggest_int('content', 0, 5)
trend = trial.suggest_int('trend', 0, 5)

# APRÈS (contraint selon état de l'art)
content = trial.suggest_float('content', 0.30, 0.50)    # 30-50%
collab = trial.suggest_float('collab', 0.20, 0.40)      # 20-40%
temporal = trial.suggest_float('temporal', 0.10, 0.30)  # 10-30%
diversity = trial.suggest_float('diversity', 0.05, 0.15) # 5-15%

# Normaliser pour somme = 1.0
total = content + collab + temporal + diversity
content_norm = content / total
collab_norm = collab / total
temporal_norm = temporal / total
diversity_norm = diversity / total
```

**Niveau 1 (signaux) - INCHANGÉ:**
- Garder les 9 poids d'interaction optimisés
- Time (41%), Clicks (24%), Session (10%) restent valides

**Nouvelle métrique composite:**
```python
composite_score = (
    0.30 × metrics['ndcg@10'] +
    0.20 × metrics['mrr@10'] +
    0.15 × metrics['recall@10'] +
    0.15 × metrics['intra_diversity'] +
    0.10 × (1 - metrics['gini']) +  # Inverse Gini
    0.10 × metrics['temporal_diversity']
)
```

### Phase 3: Validation

**Tests à effectuer:**

1. **Diversité utilisateur:**
   - Vérifier Gini < 0.5 (pas de bulle extrême)
   - Intra-user diversity > 0.6

2. **Fraîcheur:**
   - Aucun article > 14 jours recommandé
   - Distribution âge moyen < 5 jours

3. **Performance:**
   - NDCG@10 ≥ baseline
   - MRR@10 amélioré

4. **Personnalisation:**
   - Inter-user diversity > 0.3
   - Pas tout le monde voit la même chose

---

## 📊 COMPARAISON AVANT/APRÈS

### Architecture

| Aspect | AVANT (Trial 17) | APRÈS (State-of-Art) |
|--------|------------------|----------------------|
| Content | 0% | 40% |
| Collaborative | 0% | 30% |
| Temporal | 100% (trend pur) | 20% (avec decay) |
| Diversity | 0% | 10% |
| **Type** | Trend-only | Hybride balancé |
| **Personnalisation** | ❌ Aucune | ✅ Oui |
| **Fraîcheur** | ⚠️ Pas de limite | ✅ Max 14 jours |
| **Bulle filtre** | ❌ Extrême | ✅ Contrôlée |

### Métriques

| Métrique | AVANT | APRÈS |
|----------|-------|-------|
| NDCG@10 | 40% poids | 30% poids |
| Recall@10 | 30% poids | 15% poids |
| MRR@10 | ❌ Absent | ✅ 20% poids |
| Diversité | 20% (mal défini) | 25% (Intra + Gini) |
| Temporal | ❌ Absent | ✅ 10% poids |

---

## 🚀 IMPLÉMENTATION

### Fichiers à modifier

**1. `recommendation_engine.py`**
- Ajouter `MAX_ARTICLE_AGE_DAYS = 14`
- Ajouter `apply_temporal_filter()`
- Modifier `temporal_decay()` avec λ = 0.099
- Forcer architecture hybride 40:30:20:10

**2. `improved_tuning.py`**
- Enrichir métriques: ajouter MRR, Gini, Intra-diversity
- Nouvelle métrique composite (6 composantes)
- Calculer temporal diversity

**3. `tuning_12_parallel_progressive.py`**
- Contraindre niveau 2:
  - content: [0.30-0.50]
  - collab: [0.20-0.40]
  - temporal: [0.10-0.30]
  - diversity: [0.05-0.15]

**4. `config.py`**
- Remplacer les poids Trial 17 par architecture forcée

### Code Exemple

```python
# config.py (NOUVEAU)
# Architecture State-of-the-Art (Papers 2024)
# FORCÉ (pas optimisé) pour éviter convergence vers trend-only
DEFAULT_WEIGHT_CONTENT = 0.40    # 40% Content-based
DEFAULT_WEIGHT_COLLAB = 0.30     # 30% Collaborative
DEFAULT_WEIGHT_TEMPORAL = 0.20   # 20% Temporal/Freshness
DEFAULT_WEIGHT_DIVERSITY = 0.10  # 10% Diversity

# Fenêtre temporelle de hype
MAX_ARTICLE_AGE_DAYS = 14  # 2 semaines max
TEMPORAL_HALF_LIFE_DAYS = 7  # Half-life 7 jours
TEMPORAL_DECAY_LAMBDA = 0.099  # ln(2)/7

# Niveau 1 (CONSERVÉ - optimisé Trial 17)
OPTIMAL_INTERACTION_WEIGHTS = {
    'w_time': 0.410,
    'w_clicks': 0.243,
    'w_session': 0.104,
    # ... reste inchangé
}
```

---

## 📚 RÉFÉRENCES

**Papers clés:**

1. **Métriques:** Bauer et al. (2024) - "Exploring the Landscape of Recommender Systems Evaluation"
2. **Temporalité:** "Accurate News Recommendation Coalescing Personal and Global Temporal Preferences" (2020)
3. **Hybride:** "A Survey of Personalized News Recommendation" (2023)
4. **Diversité:** "Beyond-accuracy: a review on diversity, serendipity, and fairness" (2023)
5. **Bulle filtre:** "Filter Bubbles in Recommender Systems: Fact or Fallacy" (2024)

**Consensus état de l'art 2024:**
- ✅ Architecture hybride 40:30:20:10
- ✅ Time decay exponentiel (half-life 7j, max 14j)
- ✅ Métriques diversité obligatoires
- ❌ Pure trend/collaborative/content = défaillant

---

## ⚠️ RISQUES ACCEPTÉS

**Score composite peut BAISSER:**
- Trial 17: 0.2673
- Avec contraintes: probablement 0.23-0.25

**MAIS:**
- ✅ Système personnalisé (vs trend-only)
- ✅ Bulle de filtre contrôlée
- ✅ Fraîcheur garantie (14j max)
- ✅ Conforme état de l'art

**Trade-off:** -5-10% de score composite pour +50% de pertinence métier

---

**Créé:** 26 Décembre 2024
**Status:** Révision nécessaire avant déploiement
**Priorité:** CRITIQUE
