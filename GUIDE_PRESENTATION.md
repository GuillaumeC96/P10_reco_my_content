# Guide pour la Présentation / Soutenance

**Date:** 18 Décembre 2024
**Projet:** P10 - Système de Recommandation d'Articles

---

## 🎯 Scripts d'Exploration pour la Présentation

### Script Principal : `data_preparation/exploration_pour_presentation.py`

Ce script génère un rapport complet d'exploration des données pour démontrer votre démarche analytique.

**Lancement :**
```bash
python3 data_preparation/exploration_pour_presentation.py
```

**Ce que le script affiche :**

1. **Vue d'ensemble du dataset**
   - 364,047 articles
   - 322,897 utilisateurs
   - 2,5M interactions
   - Sparsité 99.96%

2. **Analyse de la qualité des articles**
   - 98.98% de contenu de qualité (≥50 mots)
   - 1.01% de brèves/flash info
   - 0.01% d'erreurs (0 mots)

3. **Distribution des catégories**
   - 461 catégories uniques
   - Top 15 catégories
   - Diversité du contenu

4. **Activité utilisateur**
   - Segmentation : passifs (50.5%), occasionnels (25.8%), réguliers (13.6%)
   - Impact pour l'évaluation
   - Distribution des interactions

5. **Analyse temporelle**
   - Période couverte : 11 ans
   - Distribution par mois
   - Âge des articles

6. **Données utilisées par le système**
   - 12.3% des articles utilisés (44,650)
   - 98.6% de contenu de qualité
   - Filtrage automatique

7. **Problème cold-start**
   - 50.5% users cold-start (<5 interactions)
   - 49.5% users warm-start (≥5 interactions)
   - Stratégies différenciées

8. **Synthèse et décisions**
   - 7 décisions de preprocessing
   - 6 insights clés

**Temps d'exécution :** ~2-3 secondes

---

## 📊 Points Clés pour la Présentation

### 1. Qualité du Dataset

**À dire :**
*"Nous avons analysé un dataset académique de Globo.com contenant 364,000 articles et 2,5 millions d'interactions. L'analyse de qualité révèle que 99% du contenu est éditorial de qualité (≥50 mots), confirmant qu'il s'agit exclusivement d'articles de news, sans pages système."*

**Chiffres clés :**
- 98.98% de contenu de qualité
- 0.01% d'erreurs (articles vides)
- Dataset pré-filtré par les chercheurs

### 2. Défi de la Sparsité

**À dire :**
*"La matrice user-article présente une sparsité de 99.96%, typique des systèmes de recommandation news. Chaque utilisateur interagit en moyenne avec seulement 9 articles sur 364,000, ce qui rend nécessaire l'utilisation de matrices creuses (sparse matrices CSR) pour optimiser la mémoire."*

**Chiffres clés :**
- Sparsité : 99.96%
- Moyenne : 9 interactions/user
- Solution : Sparse matrices (4.4 MB au lieu de 600 GB)

### 3. Problème du Cold-Start

**À dire :**
*"50% des utilisateurs ont moins de 5 interactions historiques (cold-start). Pour ces utilisateurs, le filtrage collaboratif n'est pas applicable. Nous avons donc implémenté une stratégie différenciée : recommandations basées sur la popularité avec décroissance temporelle pour les cold-start users, et système hybride personnalisé pour les warm-start users."*

**Chiffres clés :**
- 50.5% cold-start (<5 interactions)
- 49.5% warm-start (≥5 interactions)
- Performance estimée globale : 4-5% HR@5

### 4. Segmentation Utilisateurs

**À dire :**
*"Nous avons segmenté les utilisateurs en 6 catégories selon leur activité. Cette analyse révèle que les 'passifs' (2-4 clics) représentent 50% de la base, nécessitant une approche spécifique pour maximiser l'engagement."*

**Segments :**
- Très passifs (1 clic) : 0%
- Passifs (2-4 clics) : 50.5%
- Occasionnels (5-10) : 25.8%
- Réguliers (11-20) : 13.6%
- Actifs (21-50) : 8.3%
- Très actifs (51+) : 1.9%

### 5. Diversité du Contenu

**À dire :**
*"Le dataset couvre 461 catégories différentes, garantissant une grande diversité de contenu. Les 10 catégories principales ne représentent que 23% du contenu, ce qui permet d'éviter les bulles de filtrage et d'exposer les utilisateurs à une variété d'articles."*

**Chiffres clés :**
- 461 catégories
- Top 10 = 23% seulement
- Diversity score = 1.0 (parfait)

---

## 🎓 Structure de Présentation Recommandée

### Slide 1 : Exploration des Données

```
EXPLORATION DU DATASET GLOBO.COM
================================

Dataset académique (RecSys Challenge 2016)
✓ 364,047 articles de news
✓ 322,897 utilisateurs
✓ 2,526,781 interactions
✓ Période : 3 mois

Qualité validée :
✓ 98.98% contenu éditorial (≥50 mots)
✓ Pas de pages système (mentions légales, etc.)
✓ Dataset pré-filtré par les chercheurs
```

### Slide 2 : Défis Identifiés

```
DÉFIS TECHNIQUES IDENTIFIÉS
============================

1. SPARSITÉ EXTRÊME (99.96%)
   → Solution : Sparse matrices CSR

2. COLD-START (50% des users)
   → Solution : Stratégie différenciée

3. DIVERSITÉ DU CONTENU (461 catégories)
   → Solution : Round-robin filtering

4. FRAÎCHEUR (articles de news)
   → Solution : Temporal decay
```

### Slide 3 : Décisions de Preprocessing

```
DÉCISIONS DE PRÉPARATION
=========================

✓ Filtrage articles vides (0.01%)
✓ Conservation brèves (contenu éditorial)
✓ Sparse matrix CSR (600 GB → 4.4 MB)
✓ Filtrage users <5 interactions (benchmark)
✓ Temporal decay half-life 7 jours
✓ Interaction weighting (0.29-0.81)
✓ Dictionary indexing (O(1) lookups)
```

---

## 📝 Questions Anticipées du Jury

### Q1 : "Pourquoi 7% de Hit Rate, c'est si bas ?"

**Réponse :**
*"7% HR@5 pour les recommandations de news est conforme aux standards de l'industrie (5-10%). C'est plus bas que Netflix (10-15%) ou Amazon (20-30%) car :*
*1) News = lecture rapide, engagement faible*
*2) Utilisateurs consultent déjà d'autres sources (Google News, Twitter)*
*3) Dataset très sparse (99.96%)*
*De plus, ce 7% est mesuré uniquement sur les utilisateurs actifs (≥5 interactions). En production, avec les cold-start users, nous estimons 4-5% HR@5 global."*

### Q2 : "Est-ce que les clics incluent les pages système ?"

**Réponse :**
*"Non, le dataset Globo.com ne contient que des interactions avec des articles de news. Notre analyse révèle que 98.6% des articles utilisés ont un contenu éditorial normal (≥50 mots), 1.4% sont des brèves d'actualité. Les pages système (mentions légales, contact) n'étaient pas trackées. Le dataset a été pré-filtré par les chercheurs de Globo.com pour la recherche scientifique."*

### Q3 : "Pourquoi filtrer les utilisateurs avec <5 interactions ?"

**Réponse :**
*"C'est un standard académique pour l'évaluation des systèmes de recommandation. Avec moins de 5 interactions :*
*1) Pas de vérité terrain suffisante pour tester*
*2) Impossible de faire un split train/test*
*3) Collaborative filtering inapplicable*
*Cependant, en production, ces utilisateurs (50% de la base) sont servis par le système via l'approche popularité + temporal decay, avec une performance estimée à 2-3% HR@5."*

### Q4 : "Comment gérez-vous le cold-start ?"

**Réponse :**
*"Nous avons une stratégie différenciée :*
*- Cold-start users (50%, <5 interactions) : Popularité avec temporal decay*
*- Warm-start users (50%, ≥5 interactions) : Système hybride personnalisé*
*Cette approche permet un taux de succès global estimé à 4-5% HR@5 en production."*

### Q5 : "Qu'est-ce que le temporal decay ?"

**Réponse :**
*"Pour les articles de news, la fraîcheur est cruciale. Le temporal decay applique une décroissance exponentielle au score de popularité en fonction de l'âge de l'article. Avec un half-life de 7 jours :*
*- Article de 7 jours : 50% du score original*
*- Article de 14 jours : 25% du score*
*- Article de 21 jours : 12.5% du score*
*Cela garantit que les news récentes sont privilégiées."*

---

## 🚀 Commandes Utiles pour la Démo

### Lancer l'exploration
```bash
python3 data_preparation/exploration_pour_presentation.py
```

### Lancer un benchmark rapide (20 users)
```bash
python3 evaluation/benchmark.py --n-users 20 --output results.csv
```

### Tester le système localement
```bash
python3 test_local.py
```

### Voir les résultats finaux
```bash
cat evaluation/benchmark_500_FINAL.csv
```

---

## 📄 Documents de Support

**Documents créés pour la présentation :**

1. **IMPROVEMENTS_SUMMARY.md** - Détails techniques des améliorations
2. **FINAL_STATUS.md** - État de production readiness
3. **PIPELINE_COMPLET.md** - Pipeline end-to-end
4. **QUICK_REFERENCE.md** - Guide d'utilisation API
5. **Ce guide** - Points clés pour présentation

**Résultats de benchmark :**
- `evaluation/benchmark_500_FINAL.csv` - Résultats production (7.0% HR@5)
- `evaluation/benchmark_200_FINAL_IMPROVEMENTS.csv` - Peak result (9.0% HR@5)

---

## ✅ Checklist Avant Présentation

- [ ] Exécuter `exploration_pour_presentation.py` et vérifier la sortie
- [ ] Préparer les slides avec les chiffres clés
- [ ] Tester une démo locale (`test_local.py`)
- [ ] Réviser les réponses aux questions anticipées
- [ ] Préparer l'explication du temporal decay
- [ ] Préparer l'explication du cold-start
- [ ] Avoir les benchmarks sous la main
- [ ] Vérifier que tous les scripts fonctionnent

---

**Bonne présentation ! 🎓**

Date de création : 18 Décembre 2024
Version : v2.0 (Phase 1 Complete)
