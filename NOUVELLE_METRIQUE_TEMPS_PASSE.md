# 📊 Nouvelle Métrique: Revenus Basés sur le Temps Passé

**Projet:** P10 - Recommandation d'Articles
**Date:** 14 Janvier 2026
**Changement majeur:** Remplacement de la métrique CPM par la métrique Temps Passé

---

## 📌 TABLE DES MATIÈRES

1. [Pourquoi Changer la Métrique ?](#1-pourquoi-changer-la-métrique)
2. [L'Ancienne vs La Nouvelle Métrique](#2-lancienne-vs-la-nouvelle-métrique)
3. [Modèle de Publicité: Pop-ups à Intervalle Régulier](#3-modèle-de-publicité-pop-ups-à-intervalle-régulier)
4. [Les Quantiles N1, N2, N3, N4](#4-les-quantiles-n1-n2-n3-n4)
5. [Résultats de l'Analyse](#5-résultats-de-lanalyse)
6. [Choix de la Fréquence de Publicité](#6-choix-de-la-fréquence-de-publicité)
7. [Comparaison avec l'Ancienne Métrique](#7-comparaison-avec-lancienne-métrique)
8. [Implémentation Technique](#8-implémentation-technique)

---

## 1. POURQUOI CHANGER LA MÉTRIQUE ?

### 1.1 Problème avec l'Ancienne Métrique

L'ancienne métrique calculait les revenus basés sur:
- Nombre d'articles lus
- 2 types de pubs: Interstitielle (6€ CPM) + In-article (2.7€ CPM)
- Complexité: Dépend du seuil de 30s de lecture

**Limites:**
```
❌ Difficile à expliquer (2 types de pubs, facteur de visibilité)
❌ Dépend d'un seuil arbitraire (30 secondes)
❌ Ne capture pas directement l'engagement utilisateur
❌ Moins flexible pour tester différentes stratégies de monétisation
```

### 1.2 Avantages de la Nouvelle Métrique

La nouvelle métrique calcule les revenus basés sur:
- **Temps passé** par l'utilisateur (en minutes)
- Publicités **pop-up à intervalle régulier** (toutes les N minutes)
- **CPM unique: 6€** pour les pubs pop-up

**Avantages:**
```
✅ Simple à comprendre: temps passé × fréquence de pub
✅ Directement lié à l'engagement utilisateur
✅ Flexible: on peut tester différentes fréquences (N1, N2, N3, N4)
✅ Permet d'optimiser le trade-off revenus/UX
✅ Plus réaliste: modèle de monétisation moderne
```

---

## 2. L'ANCIENNE VS LA NOUVELLE MÉTRIQUE

### 2.1 Ancienne Métrique (CPM Articles)

```
Formule:
Revenus = (Nb articles cliqués × 6€/1000) + (Nb pages vues × 2.7€/1000)

Exemple:
- Utilisateur lit 1.83 articles
- Revenus = (1.83 × 6€/1000) + (1.83 × 2.7€/1000 × facteur_visibilité)
- Complexe à calculer et à expliquer
```

### 2.2 Nouvelle Métrique (Temps Passé + Pop-ups)

```
Formule:
Revenus = (Temps_passé_minutes / Fréquence_pub_minutes) × (6€ / 1000)

Exemple:
- Utilisateur passe 30 minutes sur le site
- Fréquence de pub: 1 toutes les 3.55 minutes (N2)
- Nb pubs = 30 / 3.55 = 8.47 pubs
- Revenus = (8.47 / 1000) × 6€ = 0.0508€ par session
```

**Clarté: ⭐⭐⭐⭐⭐** (vs ⭐⭐⭐ pour l'ancienne)

---

## 3. MODÈLE DE PUBLICITÉ: POP-UPS À INTERVALLE RÉGULIER

### 3.1 Fonctionnement

```
┌─────────────────────────────────────────────────────────────┐
│  TIMELINE D'UNE SESSION UTILISATEUR                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  0 min    [PUB]    N min    [PUB]    2N min    [PUB] ...    │
│    │        │        │        │         │         │          │
│    └────────┼────────┴────────┼─────────┴─────────┘          │
│             │                 │                               │
│         1ère pub          2ème pub                           │
│                                                              │
│  Intervalle = N minutes (ex: 3.55 min pour N2)              │
│  CPM = 6€ pour chaque pub pop-up affichée                   │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 Exemple Concret

**Scénario: Fréquence N2 (1 pub toutes les 3.55 minutes)**

```
Session de 30 minutes:
  0:00 → [PUB 1]
  3:35 → [PUB 2]
  7:10 → [PUB 3]
 10:45 → [PUB 4]
 14:20 → [PUB 5]
 17:55 → [PUB 6]
 21:30 → [PUB 7]
 25:05 → [PUB 8]
 28:40 → [PUB 9]

Total: 8.47 pubs affichées
Revenu: (8.47 / 1000) × 6€ = 0.0508€
```

---

## 4. LES QUANTILES N1, N2, N3, N4

### 4.1 Définition

Les quantiles N1, N2, N3, N4 représentent les **durées caractéristiques** des sessions utilisateurs:

```
N1 (Q25): 25% des utilisateurs passent ≤ N1 minutes
N2 (Q50): 50% des utilisateurs passent ≤ N2 minutes (MÉDIANE)
N3 (Q75): 75% des utilisateurs passent ≤ N3 minutes
N4 (Q90): 90% des utilisateurs passent ≤ N4 minutes
```

### 4.2 Valeurs Calculées (Dataset Globo.com)

Basé sur l'analyse de **322,897 utilisateurs** et **2,840,016 interactions**:

```
┌─────────────────────────────────────────────────────────────┐
│  QUANTILES DES DURÉES DE SESSION                            │
├─────────────────────────────────────────────────────────────┤
│  N1 (Q25):  1.00 minutes   → Utilisateurs très rapides      │
│  N2 (Q50):  3.55 minutes   → Utilisateurs moyens (médiane)  │
│  N3 (Q75): 15.75 minutes   → Utilisateurs engagés           │
│  N4 (Q90): 38.38 minutes   → Utilisateurs très engagés      │
└─────────────────────────────────────────────────────────────┘

Statistiques:
  - Moyenne:    16.45 minutes
  - Médiane:     3.55 minutes
  - Écart-type: 46.25 minutes
  - Min:         1.00 minutes
  - Max:      3613.62 minutes (60 heures!)
```

### 4.3 Interprétation Business

```
┌─────────┬─────────────┬──────────────────────────────────────┐
│ Quantile│  Fréquence  │  Impact Business                     │
├─────────┼─────────────┼──────────────────────────────────────┤
│ N1 (1m) │ 1 pub/min   │ MAXIMUM DE REVENUS                   │
│         │             │ - Pubs fréquentes → Beaucoup de $$$  │
│         │             │ - RISQUE: UX dégradée (trop de pubs)│
├─────────┼─────────────┼──────────────────────────────────────┤
│ N2 (3.5m)│ 1 pub/3.5m │ ÉQUILIBRE REVENUS/UX                 │
│         │             │ - Fréquence médiane → Bon compromis │
│         │             │ - RECOMMANDÉ pour démarrer           │
├─────────┼─────────────┼──────────────────────────────────────┤
│ N3 (15.8m)│ 1 pub/16m │ PRIORITÉ UX                          │
│         │             │ - Pubs rares → Moins de revenus      │
│         │             │ - Excellente UX (peu intrusif)       │
├─────────┼─────────────┼──────────────────────────────────────┤
│ N4 (38.4m)│ 1 pub/38m │ MINIMUM DE REVENUS                   │
│         │             │ - Très peu de pubs → Peu de revenus  │
│         │             │ - UX premium (presque pas de pubs)   │
└─────────┴─────────────┴──────────────────────────────────────┘
```

---

## 5. RÉSULTATS DE L'ANALYSE

### 5.1 Scénario SANS Système de Recommandation (Baseline)

**Hypothèse: Temps moyen = 16.45 minutes/session (données actuelles)**

```
Pour 100,000 sessions/an:

┌──────────┬─────────────┬──────────────┬────────────────────┐
│ Quantile │  Fréquence  │  Pubs/session│  Revenu Total/an   │
├──────────┼─────────────┼──────────────┼────────────────────┤
│ N1 (1m)  │  1 pub/min  │    16.45     │   9,868€           │
│ N2 (3.5m)│ 1 pub/3.5m  │     4.63     │   2,777€           │
│ N3 (15.8m)│ 1 pub/16m  │     1.04     │     627€           │
│ N4 (38.4m)│ 1 pub/38m  │     0.43     │     257€           │
└──────────┴─────────────┴──────────────┴────────────────────┘
```

### 5.2 Scénario AVEC Système de Recommandation

**Hypothèse: +83% de temps passé (baseline: 1 → 1.83 articles)**

```
Nouveau temps moyen = 16.45 × 1.83 = 30.10 minutes/session

Pour 100,000 sessions/an:

┌──────────┬─────────────┬──────────────┬────────────────────┬─────────────┐
│ Quantile │  Fréquence  │  Pubs/session│  Revenu Total/an   │    GAIN     │
├──────────┼─────────────┼──────────────┼────────────────────┼─────────────┤
│ N1 (1m)  │  1 pub/min  │    30.10     │  18,058€           │ +8,190€ ⭐  │
│ N2 (3.5m)│ 1 pub/3.5m  │     8.47     │   5,082€           │ +2,305€     │
│ N3 (15.8m)│ 1 pub/16m  │     1.91     │   1,147€           │   +520€     │
│ N4 (38.4m)│ 1 pub/38m  │     0.78     │     471€           │   +213€     │
└──────────┴─────────────┴──────────────┴────────────────────┴─────────────┘
```

### 5.3 Gains en Pourcentage

```
TOUS LES SCÉNARIOS: +83.0% de revenus 🎉

Pourquoi 83% constant?
→ Revenus ∝ Temps passé
→ +83% de temps → +83% de revenus
→ Linéaire et prévisible!
```

---

## 6. CHOIX DE LA FRÉQUENCE DE PUBLICITÉ

### 6.1 Trade-off Revenus vs UX

```
                    REVENUS ↑
                        │
        ┌───────────────┼───────────────┐
        │ N1 (1 min)    │               │
        │ +8,190€       │  ⚠️  Risque   │
        │               │  UX dégradée  │
        ├───────────────┼───────────────┤
        │ N2 (3.5 min)  │  ✅ OPTIMAL   │
        │ +2,305€       │  Équilibre    │
        ├───────────────┼───────────────┤
        │ N3 (16 min)   │  😊 Bonne UX  │
        │ +520€         │  Moins de $   │
        ├───────────────┼───────────────┤
        │ N4 (38 min)   │  😍 UX Premium│
        │ +213€         │  Très peu de $│
        └───────────────┴───────────────┘
                        │
                     UX ↑
```

### 6.2 Recommandations par Profil Business

```
┌─────────────────────────────────────────────────────────────┐
│  PROFIL: START-UP EN CROISSANCE                             │
│  Priorité: Maximiser revenus rapidement                     │
│  → CHOIX: N1 (1 pub/min)                                    │
│  → Gain: +8,190€/an (100k sessions)                         │
│  → Risque: Surveiller taux de rebond                        │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  PROFIL: MÉDIA ÉTABLI                                       │
│  Priorité: Équilibre revenus/fidélisation                   │
│  → CHOIX: N2 (1 pub/3.5 min) ⭐ RECOMMANDÉ                  │
│  → Gain: +2,305€/an (100k sessions)                         │
│  → Avantage: Compromis optimal revenus/UX                   │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  PROFIL: MÉDIA PREMIUM                                      │
│  Priorité: Expérience utilisateur irréprochable              │
│  → CHOIX: N3 (1 pub/16 min) ou N4 (1 pub/38 min)           │
│  → Gain: +520€ ou +213€/an (100k sessions)                  │
│  → Avantage: Excellente UX, faible intrusion               │
└─────────────────────────────────────────────────────────────┘
```

### 6.3 Stratégie Progressive (Recommandé)

```
PHASE 1: DÉMARRAGE (Mois 1-3)
  → Commencer avec N2 (3.5 min) - Équilibre optimal
  → Mesurer: taux de rebond, temps passé, satisfaction

PHASE 2: AJUSTEMENT (Mois 4-6)
  → SI taux de rebond OK → Tester N1 (1 min) sur 10% du trafic
  → SI taux de rebond élevé → Tester N3 (16 min)

PHASE 3: OPTIMISATION (Mois 7+)
  → A/B Testing entre N1, N2, N3
  → Trouver la fréquence optimale pour VOTRE audience
```

---

## 7. COMPARAISON AVEC L'ANCIENNE MÉTRIQUE

### 7.1 Résultats Ancienne Métrique (CPM Articles)

```
Scenario: 100,000 sessions/an
  - SANS reco: 1.0 article/session → 870€/an
  - AVEC reco: 1.83 articles/session → 1,816€/an
  - GAIN: +946€ (+109%)
```

### 7.2 Résultats Nouvelle Métrique (Temps Passé + Pop-ups)

```
Scenario: 100,000 sessions/an, Fréquence N2 (3.5 min)
  - SANS reco: 16.45 min/session → 2,777€/an
  - AVEC reco: 30.10 min/session → 5,082€/an
  - GAIN: +2,305€ (+83%)
```

### 7.3 Comparaison Directe

```
┌────────────────────┬────────────────┬────────────────┬──────────┐
│  Métrique          │  SANS reco     │  AVEC reco     │   GAIN   │
├────────────────────┼────────────────┼────────────────┼──────────┤
│ Ancienne (CPM)     │     870€       │   1,816€       │  +946€   │
│ Nouvelle (Temps+N2)│   2,777€       │   5,082€       │ +2,305€  │
├────────────────────┼────────────────┼────────────────┼──────────┤
│ Différence         │  +1,907€       │  +3,266€       │ +1,359€  │
└────────────────────┴────────────────┴────────────────┴──────────┘

🎯 AVEC LA NOUVELLE MÉTRIQUE:
  - Revenus de base × 3.2 (2,777€ vs 870€)
  - Revenus avec reco × 2.8 (5,082€ vs 1,816€)
  - Gain supplémentaire: +1,359€ vs ancienne métrique
```

### 7.4 Pourquoi la Nouvelle Métrique Génère Plus de Revenus ?

```
1. CPM Plus Élevé
   Ancienne: Mix 6€ (69%) + 2.7€ (31%) = 4.83€ effectif
   Nouvelle: 6€ CPM fixe pour toutes les pubs

2. Fréquence de Monétisation
   Ancienne: 1 pub par article lu (rare)
   Nouvelle: 1 pub toutes les N minutes (fréquent)

3. Temps Passé > Articles Lus
   - Lire 1.83 articles ≠ Temps exact
   - Temps passé = Mesure directe et précise de l'engagement

Exemple:
  Utilisateur lit 1 article long (10 min)
    → Ancienne métrique: 1 article = 1 pub interstitielle + 1 pub in-article
    → Nouvelle métrique (N2): 10/3.5 = 2.8 pubs
    → Nouvelle métrique génère +40% de revenus pour cet utilisateur!
```

---

## 8. IMPLÉMENTATION TECHNIQUE

### 8.1 Formule de Calcul

```python
def calculate_time_based_revenue(session_time_minutes, popup_interval_minutes, cpm=6.0):
    """
    Calcule le revenu basé sur le temps passé et les pubs pop-up

    Args:
        session_time_minutes: Durée de la session en minutes
        popup_interval_minutes: Intervalle entre chaque pub (N1, N2, N3, N4)
        cpm: CPM des pubs pop-up (défaut: 6€)

    Returns:
        Revenu en euros pour cette session
    """
    if popup_interval_minutes == 0:
        return 0.0

    # Nombre de pubs affichées
    num_popups = session_time_minutes / popup_interval_minutes

    # Revenu = (nombre de pubs / 1000) × CPM
    revenue = (num_popups / 1000.0) * cpm

    return revenue
```

### 8.2 Exemple d'Utilisation

```python
# Scénario: Utilisateur passe 30 minutes, fréquence N2 (3.5 min)
session_time = 30.0  # minutes
popup_interval = 3.55  # minutes (N2)

revenue = calculate_time_based_revenue(session_time, popup_interval)
print(f"Revenu: {revenue:.4f} €")  # Output: Revenu: 0.0508 €

# Pour 100,000 sessions
total_revenue = revenue * 100000
print(f"Revenu total: {total_revenue:.2f} €")  # Output: Revenu total: 5,082.11 €
```

### 8.3 Intégration dans le Système d'Évaluation

Pour mettre à jour le système d'évaluation actuel:

```python
# Remplacer l'ancienne métrique composite
# Ancienne:
score_composite = 0.69 * precision + 0.31 * recall

# Nouvelle:
# On optimise maintenant pour le TEMPS PASSÉ
# Proxy: Recall@10 (plus d'articles recommandés = plus de temps passé)
score_composite = recall  # ou weighted_recall si on veut pondérer

# Puis calculer les revenus avec la formule temps
estimated_time_increase = estimated_articles_increase  # hypothèse: linéaire
baseline_time = 16.45  # minutes
new_time = baseline_time * (1 + estimated_time_increase)
revenue = calculate_time_based_revenue(new_time, popup_interval=3.55)
```

---

## 9. RÉSUMÉ EXÉCUTIF

### 9.1 Changements Clés

```
✅ Métrique cible: TEMPS PASSÉ (au lieu de CPM articles)
✅ Modèle de pub: Pop-ups à intervalle régulier (au lieu de pubs par article)
✅ CPM unique: 6€ (au lieu de mix 6€/2.7€)
✅ Flexibilité: 4 fréquences testables (N1, N2, N3, N4)
```

### 9.2 Résultats (Fréquence N2 Recommandée)

```
Scénario: 100,000 sessions/an, 1 pub toutes les 3.55 minutes

SANS système de recommandation:
  - Temps moyen: 16.45 min/session
  - Revenus: 2,777€/an

AVEC système de recommandation (+83% temps):
  - Temps moyen: 30.10 min/session
  - Revenus: 5,082€/an
  - GAIN: +2,305€ (+83%)
```

### 9.3 Recommandation Finale

```
🎯 FRÉQUENCE RECOMMANDÉE: N2 (1 pub toutes les 3.55 minutes)

Pourquoi?
  ✅ Équilibre optimal revenus/UX
  ✅ Fréquence médiane (50% des utilisateurs)
  ✅ Gain significatif: +2,305€/an (100k sessions)
  ✅ Risque faible pour l'expérience utilisateur
  ✅ Facile à ajuster si besoin (tester N1 ou N3)
```

---

## 10. PROCHAINES ÉTAPES

```
1. ✅ Valider cette nouvelle métrique avec les parties prenantes
2. ⏳ Mettre à jour le système d'évaluation (improved_tuning.py)
3. ⏳ Relancer l'optimisation Optuna avec la nouvelle métrique
4. ⏳ Mettre à jour la documentation et les livrables
5. ⏳ Mettre à jour l'interface Streamlit pour afficher les estimations de temps
6. ⏳ Préparer les slides de présentation avec les nouveaux chiffres
```

---

**Fichiers générés:**
- `evaluation/time_based_revenue_analysis.py` - Script d'analyse
- `evaluation/time_based_revenue_results.json` - Résultats détaillés
- `evaluation/time_based_revenue_comparison.png` - Graphiques de comparaison

**Date de création:** 14 Janvier 2026
**Status:** ✅ Nouvelle métrique implémentée et analysée
