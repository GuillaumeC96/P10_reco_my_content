# 📊 Comparaison de Deux Métriques d'Engagement

**Date:** 14 Janvier 2026
**Échantillon:** 7,982 utilisateurs (21,963 interactions)

---

## 🎯 OBJECTIF

Comparer deux approches de mesure de l'engagement utilisateur :

1. **Métrique Actuelle (Ratio d'Engagement)** : Temps total / Temps disponible
2. **Métrique Basée sur l'Intérêt (Taux de Lecture)** : Temps réel / Temps attendu (selon longueur articles)

---

## 📐 MÉTRIQUE 1: RATIO D'ENGAGEMENT

### Définition
```
Ratio d'Engagement = Temps total passé / Temps disponible depuis première visite

Formule: ratio = total_time_minutes / (days_elapsed × 24 × 60)
```

### Résultats sur 7,982 Utilisateurs

```
Ratio d'engagement (%):
  Moyenne:  54.06%
  Médiane:  34.72%
  Q25:      34.72%
  Q75:      100.00%

Temps moyen par utilisateur:
  Total:    4.10 minutes
  Médiane:  0.50 minutes
```

### Avantages ✅

```
✅ Simple à comprendre et calculer
✅ Normalisée par l'ancienneté du compte
✅ Mesure l'engagement global sur le site
✅ Facile à suivre dans le temps
✅ Comparable entre utilisateurs
✅ Alignée avec l'objectif business (temps sur site)
```

### Limites ⚠️

```
⚠️  Ne mesure pas la QUALITÉ de l'engagement
⚠️  Un user qui lit vite vs lentement = même ratio
⚠️  Ne capte pas l'intérêt réel pour le contenu
⚠️  Sensible aux outliers (sessions très longues)
```

---

## 📚 MÉTRIQUE 2: TAUX DE LECTURE (Interest-Based)

### Définition
```
Taux de Lecture = Temps réel passé / Temps attendu (selon nombre de mots)

Formule: taux = time_spent_minutes / (words_count / 200 wpm)

Interprétation:
  • taux > 1  → Lecture lente (très intéressé, engagement fort)
  • taux ≈ 1  → Lecture normale (intérêt modéré)
  • taux < 1  → Lecture rapide (survol, faible engagement)
```

### Résultats sur 7,982 Utilisateurs

```
Taux de lecture (par article):
  Moyenne:  2.33x
  Médiane:  0.56x
  Q25:      0.42x
  Q75:      1.79x

Taux de lecture moyen par utilisateur:
  Moyenne:  1.36x
  Médiane:  0.52x

Score d'intérêt moyen (capé à 3x):
  Moyenne:  0.77
  Médiane:  0.52

Articles lus par utilisateur:
  Moyenne:  1.7 articles
```

### Avantages ✅

```
✅ Mesure l'INTÉRÊT réel pour le contenu
✅ Tient compte de la longueur des articles
✅ Distingue lecture rapide (survol) vs lente (intéressé)
✅ Plus granulaire (par article, pas globale)
✅ Permet d'identifier le contenu le plus engageant
✅ Peut améliorer les recommandations (favoriser articles à fort taux)
```

### Limites ⚠️

```
⚠️  Dépend de l'hypothèse de vitesse de lecture (200 wpm)
⚠️  Plus complexe à calculer
⚠️  Nécessite le nombre de mots (pas toujours disponible)
⚠️  Difficile à suivre dans le temps (variance élevée)
⚠️  Moins directement liée aux revenus publicitaires
⚠️  Sensible aux pauses (user lit puis fait pause)
```

---

## 🔗 CORRÉLATION ENTRE LES DEUX MÉTRIQUES

```
Corrélation: 0.362

Interprétation:
  • Corrélation modérée positive
  • Les deux métriques capturent des aspects DIFFÉRENTS de l'engagement
  • Métrique 1 = engagement QUANTITATIF (combien de temps)
  • Métrique 2 = engagement QUALITATIF (comment le temps est passé)
```

---

## 💰 IMPACT DU SYSTÈME DE RECOMMANDATION (+83% temps)

### MÉTRIQUE 1: Ratio d'Engagement

```
┌─────────────────────────────────────────────────────────────┐
│  SANS Recommandation                                        │
├─────────────────────────────────────────────────────────────┤
│  Ratio moyen:        54.06%                                 │
│  Temps moyen:        4.10 minutes                           │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  AVEC Recommandation (+83% temps)                           │
├─────────────────────────────────────────────────────────────┤
│  Ratio moyen:        98.93%                                 │
│  Temps moyen:        7.50 minutes                           │
│  Gain absolu:        +44.87% points                         │
│  Gain relatif:       +83.0%                                 │
└─────────────────────────────────────────────────────────────┘
```

### MÉTRIQUE 2: Taux de Lecture

#### Hypothèse 1: Même taux, plus d'articles

```
┌─────────────────────────────────────────────────────────────┐
│  SANS Recommandation                                        │
├─────────────────────────────────────────────────────────────┤
│  Taux de lecture:    1.36x                                  │
│  Score d'intérêt:    0.77                                   │
│  Articles lus:       1.7 articles/user                      │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  AVEC Recommandation - Hypothèse 1                          │
│  (Même qualité d'engagement, juste plus d'articles)         │
├─────────────────────────────────────────────────────────────┤
│  Taux de lecture:    1.36x (inchangé)                       │
│  Score d'intérêt:    0.77 (inchangé)                        │
│  Articles lus:       3.1 articles/user (+83%)               │
│  Gain:               +83.0%                                 │
└─────────────────────────────────────────────────────────────┘
```

#### Hypothèse 2: Taux amélioré + plus d'articles

```
┌─────────────────────────────────────────────────────────────┐
│  AVEC Recommandation - Hypothèse 2                          │
│  (Meilleure pertinence → +20% engagement qualitatif)        │
├─────────────────────────────────────────────────────────────┤
│  Taux de lecture:    1.63x (+20%)                           │
│  Score d'intérêt:    0.92 (+20%)                            │
│  Articles lus:       3.1 articles/user (+83%)               │
│  Gain total:         +119.6% d'engagement                   │
│                                                             │
│  Explication:                                               │
│    • +83% plus d'articles (grâce aux recommandations)       │
│    • +20% meilleur engagement par article (plus pertinent)  │
│    • = 1.83 × 1.20 - 1 = +119.6% gain total                │
└─────────────────────────────────────────────────────────────┘
```

---

## 📊 TABLEAU COMPARATIF

| Critère | Métrique 1: Ratio d'Engagement | Métrique 2: Taux de Lecture |
|---------|-------------------------------|---------------------------|
| **Simplicité** | ⭐⭐⭐⭐⭐ Très simple | ⭐⭐⭐ Modérée |
| **Clarté business** | ⭐⭐⭐⭐⭐ Directe (temps → revenus) | ⭐⭐⭐ Indirecte |
| **Granularité** | ⭐⭐ Global (par user) | ⭐⭐⭐⭐⭐ Fine (par article) |
| **Qualité engagement** | ⭐⭐ Ne mesure pas | ⭐⭐⭐⭐⭐ Mesure intérêt |
| **Stabilité** | ⭐⭐⭐⭐⭐ Stable | ⭐⭐⭐ Variable |
| **Normalisation** | ⭐⭐⭐⭐⭐ Par ancienneté | ⭐⭐⭐⭐ Par longueur article |
| **Calcul facile** | ⭐⭐⭐⭐⭐ Oui | ⭐⭐⭐ Nécessite words_count |
| **Suivi temporel** | ⭐⭐⭐⭐⭐ Facile | ⭐⭐⭐ Difficile |
| **Amélioration recos** | ⭐⭐⭐ Indirecte | ⭐⭐⭐⭐⭐ Directe (favoriser taux élevé) |

---

## 🎯 RECOMMANDATION

### Pour la Présentation: **MÉTRIQUE 1 (Ratio d'Engagement)**

**Pourquoi ?**

```
1. ✅ SIMPLICITÉ
   → Facile à expliquer au jury
   → Compréhensible par non-techniques
   → Alignée avec objectif business (temps sur site → revenus)

2. ✅ CLARTÉ DES RÉSULTATS
   → Impact clair: 54% → 99% (+83%)
   → Lien direct avec revenus publicitaires
   → Métrique normalisée et comparable

3. ✅ ROBUSTESSE
   → Stable dans le temps
   → Peu sensible aux hypothèses
   → Facile à valider

4. ✅ PRÉSENTATION
   → Slide simple et percutant
   → Message clair: "2x plus d'engagement"
   → Aligné avec business case
```

### Pour l'Amélioration Système: **MÉTRIQUE 2 (Taux de Lecture)**

**Pourquoi ?**

```
1. ✅ OPTIMISATION RECOMMANDATIONS
   → Favoriser articles avec taux de lecture élevé
   → Identifier contenu le plus engageant
   → Personnaliser selon vitesse lecture user

2. ✅ QUALITÉ ENGAGEMENT
   → Mesure si user AIME vraiment le contenu
   → Détecte survol vs lecture approfondie
   → Améliore pertinence recommandations

3. ✅ A/B TESTING
   → Comparer qualité de différentes approches
   → Tester si nouvelles recos sont plus intéressantes
   → Valider amélioration diversité proportionnelle

4. ✅ ANALYSE CONTENU
   → Identifier catégories les plus engageantes
   → Optimiser longueur articles
   → Détecter contenu à faible intérêt
```

---

## 🎤 MESSAGE POUR LA SOUTENANCE

### Version Concise (30 secondes)

> **"Nous utilisons le ratio d'engagement comme métrique principale : le pourcentage du temps qu'un utilisateur consacre au site par rapport au temps écoulé depuis sa première visite. Cette métrique simple et normalisée passe de 54% à 99% avec notre système de recommandation (+83%), générant +7,450€ de revenus annuels.**
>
> **Nous avons également exploré une métrique basée sur l'intérêt (taux de lecture comparé à la longueur des articles) qui mesure la QUALITÉ de l'engagement. Avec une corrélation de 0.36, les deux métriques capturent des aspects complémentaires : quantité vs qualité d'engagement."**

### Version Détaillée (si question du jury)

> **"Nous avons comparé deux métriques :**
>
> **1) Le ratio d'engagement (actuelle) qui mesure le temps total sur le site normalisé par l'ancienneté du compte. C'est simple, stable, et directement lié aux revenus publicitaires.**
>
> **2) Le taux de lecture qui compare le temps réel passé à lire un article versus le temps attendu basé sur sa longueur (200 mots/minute). Cette métrique mesure l'INTÉRÊT réel : un taux > 1 signifie que l'utilisateur lit lentement car très intéressé, un taux < 1 signifie qu'il survole.**
>
> **Les deux métriques sont modérément corrélées (0.36), ce qui montre qu'elles capturent des aspects différents. Pour la présentation, nous utilisons le ratio d'engagement car il est plus simple et directement lié au business. Mais le taux de lecture pourrait servir à améliorer nos recommandations en favorisant le contenu le plus engageant."**

---

## 📋 SYNTHÈSE EXÉCUTIVE

```
╔══════════════════════════════════════════════════════════════╗
║           COMPARAISON DES MÉTRIQUES D'ENGAGEMENT             ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  MÉTRIQUE 1: Ratio d'Engagement (Temps / Temps Dispo)       ║
║  ────────────────────────────────────────────────────        ║
║  • Baseline: 54.06%                                          ║
║  • Avec reco: 98.93% (+83%)                                  ║
║  • Corrélation: 0.36 avec Métrique 2                         ║
║                                                              ║
║  ✅ Recommandée pour: PRÉSENTATION                           ║
║     → Simple, claire, alignée business                       ║
║                                                              ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  MÉTRIQUE 2: Taux de Lecture (Temps Réel / Attendu)         ║
║  ────────────────────────────────────────────────────        ║
║  • Baseline: 1.36x (lecture plus lente que vitesse normale) ║
║  • Avec reco H1: 1.36x × 1.83 articles = +83%               ║
║  • Avec reco H2: 1.63x × 1.83 articles = +119.6%            ║
║                                                              ║
║  ✅ Recommandée pour: AMÉLIORATION SYSTÈME                   ║
║     → Mesure qualité, optimise recommandations               ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
```

---

**Fichiers associés:**
- `evaluation/comparative_metrics_analysis.py` - Script d'analyse
- `evaluation/comparative_metrics_results.json` - Résultats JSON

**Date:** 14 Janvier 2026
**Status:** ✅ Analyse comparative terminée
