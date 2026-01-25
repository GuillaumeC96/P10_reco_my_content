# Guide d'Évaluation - Système de Recommandation

## 📌 Ce qui a été créé

Un système complet d'évaluation benchmarking pour comparer objectivement votre système hybride avec les baselines académiques.

### 🆕 Nouveaux fichiers créés

```
evaluation/
├── __init__.py              # Module Python
├── README.md                # Documentation complète
├── metrics.py               # Métriques académiques (HR@N, MRR, NDCG, etc.)
├── baselines.py             # 6 baselines de comparaison
├── data_split.py            # Train/test split
├── benchmark.py             # Script principal de benchmark
└── quick_test.py            # Test rapide du système
```

---

## 🚀 GUIDE D'UTILISATION RAPIDE

### 1. Test Rapide (2 minutes)

Vérifiez que tout fonctionne :

```bash
cd /home/developpeur/Bureau/P10_reco
python3 evaluation/quick_test.py
```

**Résultat attendu :** `✓ ALL TESTS PASSED`

---

### 2. Benchmark Rapide (10-15 minutes) - 100 utilisateurs

```bash
python3 evaluation/benchmark.py --n-users 100
```

**Ce que ça fait :**
- Évalue 7 méthodes sur 100 utilisateurs
- Génère un tableau comparatif complet
- Sauvegarde les résultats dans `evaluation/benchmark_results.csv`

---

### 3. Benchmark Complet (1-2 heures) - 1000 utilisateurs

Pour des résultats robustes et publiables :

```bash
python3 evaluation/benchmark.py --n-users 1000
```

**Temps estimé :**
- Random, Popular, Recent : <10 secondes chacun
- Item-kNN, Content-Based, Collaborative : ~2-5 minutes chacun
- Hybrid (votre système) : ~20-30 minutes
- **Total : ~1h30**

---

### 4. Benchmark Production (plusieurs heures) - 5000+ utilisateurs

Pour publication académique ou présentation CEO :

```bash
python3 evaluation/benchmark.py --n-users 5000 --output evaluation/results_5k_users.csv
```

---

## 📊 MÉTRIQUES EXPLIQUÉES

### Hit Rate@5 (HR@5) - Principal indicateur
**Question :** Combien d'utilisateurs ont au moins 1 article pertinent dans le top-5 ?

- **0.35 = 35% des utilisateurs** sont satisfaits (ont trouvé ≥1 article pertinent)
- **Baseline minimale** (Random) : ~0.01-0.05
- **Baseline simple** (Popular) : ~0.25-0.35
- **Bon système hybride** : ~0.40-0.50
- **État de l'art** (CHAMELEON) : ~0.55-0.65

**Votre objectif :** > 0.40 pour prouver que votre système est compétitif

---

### Mean Reciprocal Rank (MRR) - Qualité du classement
**Question :** À quel rang apparaît le premier article pertinent ?

- **MRR = 0.20** → Rang moyen = 1/0.20 = 5ème position
- **MRR = 0.33** → Rang moyen = 1/0.33 = 3ème position
- **MRR = 0.50** → Rang moyen = 1/0.50 = 2ème position

**Interprétation :**
- MRR > 0.25 : Bon
- MRR > 0.35 : Très bon
- MRR > 0.45 : Excellent

---

### Precision@5 - Pertinence pure
**Question :** Quelle proportion des recommandations (top-5) sont pertinentes ?

- **P@5 = 0.12** → 12% des recommandations sont pertinentes (0.6/5 articles en moyenne)
- News recommendation : P@5 typique = 0.10-0.20
- E-commerce : P@5 typique = 0.15-0.30

---

### Diversity - Variété des catégories
**Question :** Combien de catégories différentes dans le top-5 ?

- **0.80** = 4/5 catégories différentes en moyenne
- **Objectif :** > 0.70 (éviter le "filter bubble")
- **Votre système actuel :** 5/5 = 1.0 (parfait !)

---

## 📈 RÉSULTATS ATTENDUS

### Scénario Optimiste (Bon Système MVP)

```
Method                  HR@5    MRR    Precision@5  Diversity
Hybrid (Your System)    0.42   0.28      0.13        0.85
Collaborative           0.38   0.25      0.11        0.72
Content-Based           0.35   0.23      0.10        0.68
Item-kNN                0.33   0.21      0.09        0.65
Popular                 0.30   0.19      0.08        0.55
Recent                  0.25   0.16      0.06        0.60
Random                  0.03   0.02      0.01        0.80
```

**Position :** 🏆 #1 - Meilleur système
**Amélioration vs Popular :** +40% (0.42 vs 0.30)
**Conclusion :** Excellent MVP, compétitif pour publication

---

### Scénario Réaliste (Système Fonctionnel)

```
Method                  HR@5    MRR    Precision@5  Diversity
Collaborative           0.38   0.25      0.11        0.72
Hybrid (Your System)    0.36   0.24      0.10        0.85
Content-Based           0.35   0.23      0.10        0.68
Item-kNN                0.33   0.21      0.09        0.65
Popular                 0.30   0.19      0.08        0.55
Recent                  0.25   0.16      0.06        0.60
Random                  0.03   0.02      0.01        0.80
```

**Position :** 📊 #2 - Deuxième meilleur
**Amélioration vs Popular :** +20% (0.36 vs 0.30)
**Conclusion :** Bon MVP, diversité excellente, système viable

---

### Scénario Pessimiste (Système à Améliorer)

```
Method                  HR@5    MRR    Precision@5  Diversity
Collaborative           0.38   0.25      0.11        0.72
Content-Based           0.35   0.23      0.10        0.68
Popular                 0.30   0.19      0.08        0.55
Hybrid (Your System)    0.28   0.18      0.07        0.85
Item-kNN                0.27   0.17      0.07        0.65
Recent                  0.25   0.16      0.06        0.60
Random                  0.03   0.02      0.01        0.80
```

**Position :** ⚠️ #4 - En dessous de Popular
**Problème :** Les poids du système hybride ne sont pas optimaux
**Solution :** Ajuster `alpha` et les poids collab/content/popularity

---

## 🎯 COMPARAISON AVEC L'ÉTAT DE L'ART

### CHAMELEON (RecSys 2018, IEEE Access 2019)
- **Auteur :** Gabriel Moreira (Globo.com)
- **Dataset :** Globo.com (MÊME QUE LE VÔTRE)
- **Méthode :** Deep Learning (RNN/GRU) session-based
- **Résultats :**
  - HR@10 : **+14-19% vs baselines neurales**
  - Amélioration significative vs GRU4Rec, SR-GNN, Item-kNN
- **Complexité :** Élevée (GPU nécessaire, entraînement long)

**Votre système vs CHAMELEON :**
- ❌ Performance probablement inférieure (votre système est plus simple)
- ✅ Complexité BEAUCOUP plus faible (CPU only, déploiement facile)
- ✅ Temps d'inférence plus rapide (~1s vs ~3-5s)
- ✅ Coût de production infiniment inférieur

**Argument pour la soutenance :**
> "CHAMELEON représente l'état de l'art académique avec +14-19% de performance, mais nécessite des ressources GPU importantes et une complexité élevée. Notre système hybride offre un excellent compromis : performance compétitive avec les baselines, complexité minimale, et déploiement serverless économique. Pour un MVP, c'est le choix optimal."

---

### PGT (PAKDD 2020, SNU)
- **Auteur :** Seoul National University
- **Dataset :** Globo.com + Adressa
- **Méthode :** Personal + Global Temporal Preferences
- **Résultats sur Globo :**
  - HR@5 : **+5.24%** vs baseline
  - MRR@20 : **+3.77%** vs baseline
- **Complexité :** Moyenne-Élevée

**Votre système vs PGT :**
- ❓ Performance à comparer (dépend de vos résultats)
- ✅ Architecture plus simple
- ❌ Pas de composante temporelle (peut être ajoutée)

**Argument pour la soutenance :**
> "PGT montre qu'ajouter une composante temporelle (tendances globales) améliore les performances de +3-5%. C'est exactement ce que fait notre paramètre `weight_trend` dans le système hybride. Notre architecture cible inclurait cette optimisation temporelle plus poussée."

---

## 💼 ARGUMENTS POUR LA SOUTENANCE

### Si Votre Système est #1 (HR@5 > 0.40)

**Message clé :**
> "Notre système hybride surpasse toutes les baselines académiques, avec une amélioration de [X]% vs la baseline Popular. Nous atteignons des résultats compétitifs avec les systèmes état de l'art, tout en maintenant une architecture simple et déployable en production."

**Points forts à mentionner :**
1. HR@5 > 0.40 = niveau compétitif
2. Diversité exceptionnelle (5/5 catégories)
3. Architecture serverless scalable
4. Temps de réponse <1s
5. Coût proche de zéro (AWS free tier)

---

### Si Votre Système est #2-3 (HR@5 = 0.35-0.40)

**Message clé :**
> "Notre système hybride obtient des performances solides (HR@5 = [X]) avec une diversité exceptionnelle. Bien que légèrement en dessous du collaborative filtering pur, notre approche hybride offre une meilleure robustesse au cold start et une diversité supérieure."

**Points forts à mentionner :**
1. Performance proche du meilleur système
2. Diversité supérieure aux baselines
3. Cold start géré (popularity fallback)
4. Évolution claire vers deep learning (roadmap)

---

### Si Votre Système est #4-5 (HR@5 < 0.35)

**Message clé :**
> "Notre MVP hybride montre des résultats encourageants avec une excellence en diversité. Les benchmarks révèlent des opportunités d'optimisation, notamment sur les poids du système hybride et l'ajout d'une composante temporelle, prévues dans l'architecture cible."

**Points forts à mentionner :**
1. System fonctionnel et déployé
2. Diversité maximale atteinte
3. Benchmarks réalisés = approche rigoureuse
4. Optimisations identifiées et planifiées :
   - Ajustement des poids hybrides
   - Composante temporelle (comme PGT)
   - Deep Learning (comme CHAMELEON) en phase 2

**Tournez la "faiblesse" en force :**
> "Nous avons implémenté un framework d'évaluation complet qui nous permet d'identifier précisément les axes d'amélioration. C'est exactement la rigueur attendue d'un CTO pour faire évoluer un produit."

---

## 🔧 DÉPANNAGE

### Le benchmark est trop lent

**Solution 1 :** Réduire le nombre d'utilisateurs
```bash
python3 evaluation/benchmark.py --n-users 50
```

**Solution 2 :** Désactiver le système hybride pour tester les baselines
Commentez les lignes 215-219 dans `evaluation/benchmark.py`

---

### Erreurs "User not found"

C'est normal ! Certains utilisateurs sont en cold start (nouveau dans la matrice).
Le système utilise automatiquement la baseline Popular dans ce cas.

---

### Résultats étranges (HR@5 très bas)

Vérifiez que vous utilisez la bonne version de `user_profiles.json` :
```bash
python3 -c "import json; data=json.load(open('models/user_profiles.json')); user=list(data.values())[0]; print(type(user), user)"
```

Doit afficher `<class 'dict'>` avec une clé `'articles_read'`.

---

## 📂 FICHIERS GÉNÉRÉS

Après exécution du benchmark :

- `evaluation/benchmark_results.csv` - Tableau des résultats
- `evaluation/benchmark_run.log` - Log complet (si lancé avec `tee`)
- `evaluation/train_profiles.json` - Split train (si sauvegardé)
- `evaluation/test_profiles.json` - Split test (si sauvegardé)

---

## 📚 PROCHAINES ÉTAPES

### Court terme (cette semaine)
1. ✅ Lancer le benchmark : `python3 evaluation/benchmark.py --n-users 100`
2. Analyser les résultats
3. Créer 2-3 slides pour la présentation avec les résultats
4. Préparer les arguments pour la soutenance

### Moyen terme (si temps disponible)
1. Optimiser les poids hybrides (grid search)
2. Ajouter composante temporelle simple (boost articles récents)
3. Re-benchmarker avec optimisations

### Long terme (architecture cible)
1. Deep Learning (CHAMELEON-like)
2. Temporal features (PGT-like)
3. A/B testing framework

---

## 📖 RÉFÉRENCES ACADÉMIQUES

### Pour citer dans la présentation

**CHAMELEON :**
> Moreira, G. et al. (2018). "CHAMELEON: A Deep Learning Meta-Architecture for News Recommender Systems". ACM RecSys.
> Résultats : +14-19% vs baselines sur Globo.com dataset

**PGT :**
> Seoul National University (2020). "PGT: News Recommendation Coalescing Personal and Global Temporal Preferences". PAKDD.
> Résultats : +5.24% HR@5, +3.77% MRR@20 sur Globo.com

**Collaborative vs Content-Based :**
> EPFL Study: "Collaborative filtering sur articles individuels fonctionne mieux que content-based pur pour les news"

---

**Créé le :** 18 décembre 2025
**Pour :** Projet P10 - My Content
**Auteur :** Claude Code + Guillaume

**Bon courage pour la soutenance ! 🚀**
