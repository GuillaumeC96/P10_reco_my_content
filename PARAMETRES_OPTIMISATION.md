# Plages de Paramètres - Optimisation Bayésienne

**Date:** 18 Décembre 2024
**Méthode:** Optuna TPE Sampler (Tree-structured Parzen Estimator)
**Essais:** 30 trials
**Early Stopping:** 10 → 30 → 50 utilisateurs progressifs

---

## NIVEAU 1 : 9 Poids des Interactions (Features)

Ces paramètres pondèrent l'importance de chaque signal d'engagement dans le calcul de `interaction_weight`.

| Paramètre | Plage Min | Plage Max | Type | Interprétation |
|-----------|-----------|-----------|------|----------------|
| **w_time** | 0.15 | 0.50 | float | Temps passé sur article (15%-50%) |
| **w_clicks** | 0.05 | 0.35 | float | Nombre de clics (5%-35%) |
| **w_session** | 0.05 | 0.25 | float | Qualité de session (5%-25%) |
| w_device | 0.02 | 0.15 | float | Qualité du device (2%-15%) |
| w_env | 0.01 | 0.10 | float | Environnement (desktop/mobile) (1%-10%) |
| w_referrer | 0.01 | 0.10 | float | Type de référent (1%-10%) |
| w_os | 0.01 | 0.10 | float | Système d'exploitation (1%-10%) |
| w_country | 0.01 | 0.10 | float | Pays (1%-10%) |
| w_region | 0.01 | 0.10 | float | Région (1%-10%) |

**Normalisation :** Les 9 paramètres sont normalisés pour que leur somme = 1.0

**Formule finale :**
```python
interaction_weight = (
    w_time * time_norm +
    w_clicks * clicks_norm +
    w_session * session_quality +
    w_device * device_quality +
    w_env * env_quality +
    w_referrer * referrer_quality +
    w_os * os_quality +
    w_country * country_quality +
    w_region * region_quality
).clip(0.1, 1.0)
```

---

## NIVEAU 2 : 3 Poids Stratégie Hybride

Ces paramètres pondèrent les 3 approches de recommandation.

| Paramètre | Plage Min | Plage Max | Type | Interprétation |
|-----------|-----------|-----------|------|----------------|
| **w_collab** | 0.30 | 0.80 | float | Collaborative Filtering (30%-80%) |
| **w_content** | 0.05 | 0.40 | float | Content-Based Filtering (5%-40%) |
| **w_trend** | 0.00 | 0.30 | float | Popularity/Trending (0%-30%) |

**Normalisation :** Les 3 paramètres sont normalisés pour que leur somme = 1.0

**Formule finale :**
```python
final_score = (
    w_collab * collaborative_score +
    w_content * content_based_score +
    w_trend * popularity_score
)
```

---

## RÉSULTATS OPTIMAUX TROUVÉS

### Niveau 1 : Poids des Interactions

| Paramètre | Valeur Brute | Valeur Normalisée | % du Total |
|-----------|--------------|-------------------|------------|
| **w_time** | 0.4960 | **0.3690** | **36.9%** 🥇 |
| **w_clicks** | 0.3144 | **0.2339** | **23.4%** 🥈 |
| **w_session** | 0.1683 | **0.1252** | **12.5%** 🥉 |
| w_device | 0.1328 | 0.0988 | 9.9% |
| w_region | 0.0816 | 0.0607 | 6.1% |
| w_env | 0.0574 | 0.0427 | 4.3% |
| w_country | 0.0386 | 0.0288 | 2.9% |
| w_os | 0.0320 | 0.0238 | 2.4% |
| w_referrer | 0.0230 | 0.0171 | 1.7% |

**Somme normalisée :** 1.0000 (100%)

### Niveau 2 : Poids Stratégie Hybride

| Paramètre | Valeur Integer | Valeur Normalisée | % du Total |
|-----------|----------------|-------------------|------------|
| **collab** | 5 | **0.714** | **71.4%** 🥇 |
| **content** | 1 | **0.143** | **14.3%** |
| **trend** | 1 | **0.143** | **14.3%** |

**Ratio :** 5:1:1
**Somme normalisée :** 1.0000 (100%)

---

## INTERPRÉTATION DES RÉSULTATS

### Niveau 1 : Signaux d'Engagement

**Top 3 Features (72% du poids total) :**

1. **Temps passé (37%)**
   - Signal le plus fort d'engagement qualité
   - Un utilisateur qui passe du temps lit vraiment l'article

2. **Nombre de clics (23%)**
   - Quantité d'interactions reste importante
   - Corrélation avec l'intérêt

3. **Qualité de session (13%)**
   - Sessions longues = engagement élevé
   - Indicateur de découverte active

**Features secondaires (28%)** : Device, région, environnement, pays, OS, referrer
- Apportent contexte et personnalisation
- Moins prédictifs mais utiles pour diversité

### Niveau 2 : Balance des Stratégies

**Collaborative Filtering dominant (71%)**
- Les comportements d'utilisateurs similaires sont le meilleur prédicteur
- Exploite les patterns collectifs

**Content + Trend (29%)**
- Content-Based (14%) : Assure diversité et exploration
- Popularity (14%) : Gère le cold start et les tendances

**Trade-off pertinence/diversité :**
- 71% collaborative = focus pertinence
- 29% content+trend = focus découverte et robustesse

---

## SCORE COMPOSITE OBTENU

**Meilleur score : 0.2135**

**Formule du score composite :**
```python
composite_score = (
    0.4 * NDCG@10 +      # Qualité du classement (40%)
    0.3 * Recall@10 +    # Couverture des pertinents (30%)
    0.2 * Diversity +    # Diversité des catégories (20%)
    0.1 * Novelty        # Nouveauté des recommandations (10%)
)
```

**Performance vs Baseline :**
- Baseline (config 3:2:1) : 0.2010
- **Optimal (config 5:1:1) : 0.2135** (+6.2% relatif)

---

## MÉTHODE D'OPTIMISATION

**Algorithme :** Optuna avec TPE Sampler (Tree-structured Parzen Estimator)

**Avantages de TPE :**
- Plus intelligent que grid search
- Explore intelligemment l'espace des paramètres
- Converge plus vite vers optimum

**Early Stopping Progressif :**
```
Phase 1 : 10 users → Si score < 0.15 : STOP
Phase 2 : 30 users → Si score < 0.18 : STOP
Phase 3 : 50 users → Évaluation complète
```

**Parallélisation :**
- 12 workers simultanés
- Évaluation de N utilisateurs en parallèle
- Temps total : ~45 minutes pour 30 trials × 50 users

---

## COMPARAISON AVEC AUTRES CONFIGURATIONS

| Config | w_collab | w_content | w_trend | Score | Rang |
|--------|----------|-----------|---------|-------|------|
| **5:1:1 (OPTIMAL)** | 71.4% | 14.3% | 14.3% | **0.2135** | 🥇 #1 |
| 5:1:2 | 62.5% | 12.5% | 25.0% | 0.2122 | #2 |
| 4:1:2 | 57.1% | 14.3% | 28.6% | 0.2126 | #3 |
| 3:2:3 | 37.5% | 25.0% | 37.5% | 0.2053 | #4 |
| 3:3:2 | 37.5% | 37.5% | 25.0% | 0.1936 | #5 |

**Pattern identifié :** Plus le collaborative est fort, meilleur est le score (jusqu'à 71%)

---

## LIMITATIONS DES PLAGES

### Pourquoi ces plages spécifiques ?

**Niveau 1 :**
- **w_time [15%-50%]** : Éviter domination totale du temps (biais articles longs)
- **w_clicks [5%-35%]** : Garder importance clicks mais pas exclusif
- **Signaux secondaires [1%-10%]** : Éviter bruit, garder signal informatif

**Niveau 2 :**
- **w_collab [30%-80%]** : Collaborative ne doit pas être < 30% (trop faible)
- **w_content [5%-40%]** : Minimum 5% pour diversité
- **w_trend [0%-30%]** : Peut être 0% si collaborative+content suffisent

### Plages alternatives possibles (non testées)

**Plus large (exploration):**
```python
w_time: 0.10 → 0.60      # +10% range
w_collab: 0.20 → 0.90    # +10% range
```

**Plus étroit (exploitation):**
```python
w_time: 0.35 → 0.50      # Focus autour de l'optimum
w_collab: 0.60 → 0.80    # Focus autour de l'optimum
```

---

## FICHIERS GÉNÉRÉS

**Code d'optimisation :**
- `evaluation/tuning_12_parallel_progressive.py` (script principal)
- `evaluation/improved_tuning.py` (evaluator)

**Résultats :**
- `evaluation/tuning_12_parallel_progressive_results.json` (30 trials complets)
- `evaluation/ultra_quick_results.json` (test rapide 9 configs)
- `evaluation/tuning_weighted_9signals_results.json` (configurations manuelles)

**Logs :**
- `evaluation/tuning_12_parallel_progressive.log` (détails exécution)

---

## UTILISATION DES PARAMÈTRES OPTIMAUX

### Dans recommendation_engine.py

```python
# Charger user_item_matrix_weighted.npz avec ces poids optimaux
interaction_weights = (
    0.3690 * time_norm +
    0.2339 * clicks_norm +
    0.1252 * session_quality +
    0.0988 * device_quality +
    0.0607 * region_quality +
    0.0427 * env_quality +
    0.0288 * country_quality +
    0.0238 * os_quality +
    0.0171 * referrer_quality
)

# Recommandations avec ratio 5:1:1
recommendations = engine.recommend(
    user_id=user_id,
    collab_weight=0.714,   # 71.4%
    content_weight=0.143,  # 14.3%
    trend_weight=0.143     # 14.3%
)
```

---

**Création:** 18 Décembre 2024
**Auteur:** Optimisation Bayésienne (Optuna TPE)
**Validation:** 30 trials × 50 utilisateurs = 1500 évaluations
**Temps total:** ~45 minutes (12 workers parallèles)
