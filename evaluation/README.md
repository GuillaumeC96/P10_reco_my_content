# Évaluation & Optimisation - Système de Recommandation

**Objectif:** Optimiser les hyperparamètres du système de recommandation pour maximiser les revenus publicitaires.

---

## 📁 Structure

```
evaluation/
├── tuning_12_parallel_progressive.py  # Script d'optimisation principal
├── improved_tuning.py                 # Évaluateur avec métriques
├── OPTIMISATION_V4_REVENUE.md         # Documentation complète
├── explications_visio.md              # Notes réunion
└── README.md                          # Ce fichier
```

---

## 🎯 Score Composite (Revenue-Optimized)

Le score est **proportionnel aux CPM publicitaires** (à 1% près):

```python
composite_score = (
    0.69 × Precision@10 +  # CTR → pubs interstitielles (6€ CPM = 69% revenus)
    0.31 × Recall@10       # Pages vues → pubs in-article (2.7€ CPM = 31% revenus)
)
```

**Ratio:** 6€/(6€+2.7€) = 69% | 2.7€/8.7€ = 31%

---

## 🚀 Lancer l'Optimisation

```bash
cd /home/ser/Bureau/P10_reco_new/evaluation

# Nettoyer cache
rm -f tuning_12_parallel_progressive_results.json
find . -type d -name "__pycache__" -exec rm -rf {} +

# Lancer (background, 3-4h)
python3 tuning_12_parallel_progressive.py 2>&1 | tee optimization_log_revenue.txt &

# Suivre progression
tail -f optimization_log_revenue.txt
```

---

## 📊 Configuration

- **30 trials** Optuna TPE (optimisation bayésienne)
- **50 users** max par trial
- **12 workers** parallèles
- **Early stopping:** phase1 < 0.05, phase2 < 0.08

### Contraintes Architecture Hybride (Level 2)
- Content: 30-50% (cible 40%)
- Collab: 20-40% (cible 30%)
- Temporal: 15-35% (cible 25%)

### Fenêtre Temporelle
- Articles > 60 jours: EXCLUS
- Decay: half-life 7 jours (λ = 0.099)

---

## 📖 Documentation Complète

Voir **[OPTIMISATION_V4_REVENUE.md](OPTIMISATION_V4_REVENUE.md)** pour:
- Détails du modèle de revenus
- Justification des poids CPM
- Validation des résultats
- Déploiement Azure

---

**Dernière mise à jour:** 27 Décembre 2024
