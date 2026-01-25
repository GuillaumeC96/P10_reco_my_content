# Optimisation Revenue-Optimized - Système de Recommandation

**Objectif:** Maximiser les revenus publicitaires du journal My Content

---

## 💰 MODÈLE DE REVENUS

```
Revenus = (Clics articles × CPM_interstitiel) + (Pages vues × CPM_in-article)
        = (Clics × 6€) + (Pages vues × 2.7€)
```

### CPM Moyens (2024)
- **Pub interstitielle** (plein écran à l'ouverture): **6€** pour 1000 affichages
- **Pub in-article** (native dans le texte): **2.7€** pour 1000 affichages

### Ratio de Revenus
- Interstitiel: 6€/(6€+2.7€) = **70%** des revenus
- In-article: 2.7€/8.7€ = **30%** des revenus

---

## 🎯 SCORE COMPOSITE

```python
composite_score = (
    0.69 × Precision@10 +  # CTR → pubs interstitielles (6€ CPM)
    0.31 × Recall@10       # Pages vues → pubs in-article (2.7€ CPM)
)
```

**Ratio CPM exact:**
- 6€ / (6€ + 2.7€) = **69%** → Precision@10
- 2.7€ / 8.7€ = **31%** → Recall@10

**Rationale:**
- **Precision@10 (69%)**: Articles pertinents en top-10 = CTR élevé = pub interstitielle (6€ CPM)
- **Recall@10 (31%)**: Couverture articles pertinents = pages vues multiples = pubs in-article (2.7€ CPM)

**Coefficients proportionnels aux CPM à 1% près.**

---

## ⚙️ CONFIGURATION OPTIMISATION

### Contraintes Level 2 (Architecture Hybride)
```python
content = [0.30-0.50]    # Content-based: 30-50%, cible 40%
collab = [0.20-0.40]     # Collaborative: 20-40%, cible 30%
temporal = [0.15-0.35]   # Temporal/Popularity: 15-35%, cible 25%
```

**Garantit:** Pas de convergence vers trend pur (100% temporal)

### Fenêtre Temporelle
- Articles > **60 jours**: EXCLUS des recommandations
- Decay exponentiel: half-life 7 jours (λ = 0.099)

### Paramètres Optuna
- **30 trials** (optimisation bayésienne TPE)
- **50 users** max par trial
- **12 workers** parallèles
- **Early stopping**: phase1 < 0.05, phase2 < 0.08

---

## 🚀 LANCER L'OPTIMISATION

```bash
cd /home/ser/Bureau/P10_reco_new/evaluation

# Nettoyer cache Optuna
rm -f tuning_12_parallel_progressive_results.json
find . -type d -name "__pycache__" -exec rm -rf {} +

# Lancer optimisation (background)
python3 tuning_12_parallel_progressive.py 2>&1 | tee optimization_log_revenue.txt &

# Suivre progression (autre terminal)
tail -f optimization_log_revenue.txt
grep "Best trial" optimization_log_revenue.txt
```

**Durée estimée:** 3-4 heures

---

## 📊 RÉSULTATS ATTENDUS

### Score Composite
- **Baseline:** 0.2124
- **Attendu avec revenue-optimized:** ~0.10-0.12

**Note:** Score plus faible car Precision@10 << NDCG@10, mais aligné sur revenus business

### Architecture
| Stratégie | Attendu |
|-----------|---------|
| Content | 35-45% |
| Collab | 25-35% |
| Temporal | 20-30% |

### Critères de Succès
- ✅ Precision@10 maximisé (priority 70%)
- ✅ Architecture hybride équilibrée
- ✅ Aucun article > 60 jours recommandé
- ✅ Pas de 0% ou 100% sur Level 2

---

## 🔍 APRÈS L'OPTIMISATION

### 1. Validation Résultats
```bash
cd /home/ser/Bureau/P10_reco_new/evaluation

# Voir meilleur trial
grep "Best trial" optimization_log_revenue.txt | tail -1

# Extraire paramètres optimaux
python3 << EOF
import json
with open('tuning_12_parallel_progressive_results.json') as f:
    results = json.load(f)
    best = results['best_params']
    print(f"Content: {best['content']:.3f}")
    print(f"Collab: {best['collab']:.3f}")
    print(f"Temporal: {best['temporal']:.3f}")
EOF
```

### 2. Mise à Jour Configuration Production
```python
# lambda/config.py et azure_function/config.py
DEFAULT_WEIGHT_CONTENT = <valeur optimale>
DEFAULT_WEIGHT_COLLAB = <valeur optimale>
DEFAULT_WEIGHT_TREND = <valeur optimale>
```

### 3. Déploiement Azure
```bash
# Upload modèles
az storage blob upload-batch --source ../models --destination models

# Déployer fonction
cd ../azure_function
func azure functionapp publish <APP_NAME>
```

---

## 📚 RÉFÉRENCES

**CPM Tarifs:**
- [Les vrais prix de la publicité en ligne](https://blog.mistralmedia.fr/les-vrais-prix-de-la-publicite-en-ligne/)
- [Native ads cost 2024](https://www.stackedmarketer.com/data-stories/native-ads-cost/)

**Architecture:**
- Fenêtre temporelle: 60 jours (adapté dataset)
- Decay exponentiel: ln(2)/7 ≈ 0.099
- Contraintes: Content [0.30-0.50], Collab [0.20-0.40], Temporal [0.15-0.35]

---

**Dernière mise à jour:** 27 Décembre 2024
**Script:** `tuning_12_parallel_progressive.py`
**Thresholds:** Phase1=0.05, Phase2=0.08 (calibrés pour Precision-based score)
