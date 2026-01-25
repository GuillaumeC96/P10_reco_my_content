# 📊 Métrique Finale: Ratio d'Engagement

**Date:** 14 Janvier 2026
**Métrique Cible:** Ratio d'Engagement = Temps Passé / Temps Disponible

---

## 🎯 DÉFINITION DE LA MÉTRIQUE

### Qu'est-ce que le Ratio d'Engagement ?

```
Ratio d'Engagement = Temps total passé sur le site / Temps écoulé depuis la première visite

Exemple concret:
  - Utilisateur inscrit il y a 31 jours
  - Temps total passé: 24 heures = 1440 minutes
  - Temps disponible: 31 jours × 24h × 60min = 44,640 minutes
  - Ratio = 1440 / 44,640 = 0.0323 = 3.23%

Interprétation:
  Cet utilisateur passe 3.23% de son temps disponible sur le site
```

### Pourquoi Cette Métrique ?

```
✅ MESURE DIRECTE DE L'ENGAGEMENT
   → Plus l'utilisateur revient et lit, plus le ratio augmente
   → Capture la fidélité ET l'intensité d'utilisation

✅ NORMALISATION PAR LA DURÉE
   → Compare équitablement un user inscrit hier vs il y a 1 an
   → Ratio indépendant de l'ancienneté du compte

✅ OBJECTIF CLAIR
   → Augmenter le % de temps que l'utilisateur passe avec nous
   → Métrique alignée avec la valeur business (plus de temps = plus de revenus)

✅ SIMPLE À COMPRENDRE
   → "Combien de % de son temps disponible l'utilisateur nous consacre-t-il ?"
   → Intuiti pour tous les stakeholders
```

---

## 📊 RÉSULTATS DE L'ANALYSE

### Données Analysées

```
🔢 Échantillon:
   - 322,897 utilisateurs
   - 2,840,016 interactions
   - Période moyenne: 5.20 jours par utilisateur
```

### Statistiques du Ratio d'Engagement (Baseline)

```
┌─────────────────────────────────────────────────────────────┐
│  DISTRIBUTION DU RATIO D'ENGAGEMENT (SANS RECOMMANDATION)  │
├─────────────────────────────────────────────────────────────┤
│  Moyenne:    0.2189%                                        │
│  Médiane:    0.0694%                                        │
│  Min:        0.0087%                                        │
│  Max:       17.2732%                                        │
│  Écart-type: 0.3709%                                        │
│                                                             │
│  Quantiles:                                                 │
│    Q25:  0.0694%  (25% des users ≤ 0.0694%)                │
│    Q50:  0.0694%  (50% des users ≤ 0.0694%, médiane)       │
│    Q75:  0.2175%  (75% des users ≤ 0.2175%)                │
│    Q90:  0.5511%  (90% des users ≤ 0.5511%)                │
│    Q95:  0.9179%  (95% des users ≤ 0.9179%)                │
└─────────────────────────────────────────────────────────────┘

Interprétation:
  - L'utilisateur MOYEN passe 0.22% de son temps disponible sur le site
  - La MÉDIANE à 0.07% montre que 50% des utilisateurs sont très peu engagés
  - Distribution asymétrique (moyenne > médiane) → quelques power users
```

---

## 💰 IMPACT DU SYSTÈME DE RECOMMANDATION

### Scénario 1: SANS Recommandation (Baseline)

```
📊 MÉTRIQUES:
   Ratio d'engagement moyen:  0.2189%
   Temps moyen passé:         16.45 minutes
   Période moyenne:            5.20 jours

💰 REVENUS (322,897 utilisateurs, fréquence N2: 3.55 min):
   Pubs par utilisateur:       4.63
   Revenu par utilisateur:     0.0278€
   REVENU TOTAL:              8,975€
```

### Scénario 2: AVEC Recommandation (+83% temps)

```
📊 MÉTRIQUES:
   Ratio d'engagement moyen:  0.4006%
   Temps moyen passé:         30.10 minutes (+83%)
   Période moyenne:            5.20 jours (inchangé)

💰 REVENUS (322,897 utilisateurs, fréquence N2: 3.55 min):
   Pubs par utilisateur:       8.48
   Revenu par utilisateur:     0.0509€
   REVENU TOTAL:             16,425€
```

### Gains

```
┌────────────────────────────────────────────────────────────┐
│  COMPARAISON SANS vs AVEC RECOMMANDATION                   │
├────────────────────────────────────────────────────────────┤
│  📊 RATIO D'ENGAGEMENT:                                    │
│     SANS reco:  0.2189%                                    │
│     AVEC reco:  0.4006%                                    │
│     GAIN:      +0.1817 points (+83.0%)                     │
│                                                            │
│  ⏱️  TEMPS PASSÉ:                                          │
│     SANS reco:  16.45 minutes                              │
│     AVEC reco:  30.10 minutes                              │
│     GAIN:      +13.65 minutes (+83.0%)                     │
│                                                            │
│  💰 REVENUS (pour 322,897 utilisateurs):                   │
│     SANS reco:  8,975€                                     │
│     AVEC reco: 16,425€                                     │
│     GAIN:      +7,450€ (+83.0%)                            │
└────────────────────────────────────────────────────────────┘
```

---

## 🔄 POURQUOI LE GAIN EST LINÉAIRE (+83%) ?

### Explication Mathématique

```
Ratio = Temps Passé / Temps Disponible

Si le temps passé augmente de X%:
  Nouveau Ratio = (Temps × 1.X) / Temps Disponible
                = Ratio × 1.X

Donc: +X% de temps → +X% de ratio

Dans notre cas:
  +83% de temps → +83% de ratio
  +83% de temps → +83% de pubs affichées
  +83% de pubs → +83% de revenus
```

### Relation Linéaire

```
┌────────────────────────────────────────────────────┐
│  RELATION: Temps ↔ Ratio ↔ Revenus                │
├────────────────────────────────────────────────────┤
│  Temps Passé  →  Ratio d'Engagement  →  Revenus   │
│     +83%              +83%                +83%     │
│                                                    │
│  Relation LINÉAIRE et PRÉDICTIBLE                  │
│  → Simple à modéliser                              │
│  → Facile à projeter                               │
│  → Alignement parfait des métriques                │
└────────────────────────────────────────────────────┘
```

---

## 💡 AVANTAGES DE CETTE MÉTRIQUE

### 1. Mesure Directe de l'Engagement

```
AVANT (Nombre d'articles):
  - Proxy indirect: "articles lus" ≠ engagement direct
  - Ne capture pas la durée de lecture
  - Ne mesure pas la récurrence

APRÈS (Ratio d'engagement):
  ✅ Mesure directe: temps réel passé sur le site
  ✅ Capture l'intensité: combien de temps par visite
  ✅ Capture la fidélité: revient-il souvent ?
  ✅ Normalisation: équitable quel que soit l'âge du compte
```

### 2. Alignement Avec les Objectifs Business

```
OBJECTIF BUSINESS: Augmenter le temps passé sur le site
MÉTRIQUE: Ratio d'engagement (temps / temps disponible)

→ Alignement PARFAIT
→ Optimiser la métrique = Optimiser l'objectif
→ Pas de proxy, pas de détour
```

### 3. Simplicité et Compréhension

```
Question CEO: "Comment mesurer notre succès ?"
Réponse: "% du temps que nos utilisateurs passent avec nous"

→ Intuitive pour tous
→ Comparable entre périodes
→ Benchmark possible (ex: "2% est excellent pour un média")
```

### 4. Prédictibilité

```
Relation linéaire:
  +X% de temps → +X% de ratio → +X% de revenus

→ Modélisation simple
→ Projections fiables
→ ROI calculable précisément
```

---

## 📈 COMPARAISON AVEC LES AUTRES MÉTRIQUES

### Ancienne Métrique (CPM Articles)

```
Définition: Revenus = (Articles × 6€) + (Pages × 2.7€)

Résultats (100,000 sessions):
  SANS reco:    870€
  AVEC reco:  1,816€
  GAIN:        +946€ (+109%)

Limites:
  ❌ Complexe (2 types de pubs, facteur visibilité)
  ❌ Proxy indirect (articles ≠ engagement)
  ❌ Pas flexible
```

### Métrique Temps Passé + Pop-ups

```
Définition: Revenus = (Temps / Fréquence) × CPM

Résultats (100,000 sessions, N2):
  SANS reco:  2,777€
  AVEC reco:  5,082€
  GAIN:      +2,305€ (+83%)

Avantages:
  ✅ Simple (1 type de pub)
  ✅ Mesure temps passé
  ✅ Flexible (4 fréquences)

Limites:
  ⚠️  Ne normalise pas par la durée du compte
```

### Métrique Ratio d'Engagement (NOUVELLE)

```
Définition: Ratio = Temps Passé / Temps Disponible

Résultats (322,897 utilisateurs, N2):
  SANS reco:  0.2189% → 8,975€
  AVEC reco:  0.4006% → 16,425€
  GAIN:      +0.1817 points (+83%) → +7,450€

Avantages:
  ✅ Mesure directe de l'engagement
  ✅ Normalisation par durée (équitable)
  ✅ Simple à comprendre (% de temps)
  ✅ Prédictible (relation linéaire)
  ✅ Alignée avec objectif business
  ✅ Comparable entre périodes et compétiteurs

RECOMMANDÉ ⭐
```

---

## 🎯 INTERPRÉTATION BUSINESS

### Que Signifie un Ratio de 0.22% ?

```
Ratio moyen: 0.2189% ≈ 0.22%

Traduction:
  → L'utilisateur passe environ 0.22% de son temps disponible sur notre site
  → Sur une journée (24h = 1440 min), cela représente: 1440 × 0.0022 = 3.16 minutes
  → Sur une semaine: 7 × 3.16 = 22 minutes
  → Sur un mois: 30 × 3.16 = 95 minutes ≈ 1h36

Est-ce bon ou mauvais?
  → Pour un média d'actualité: 0.22% est RAISONNABLE
  → Benchmark industrie: 0.1% à 0.5% selon le type de contenu
  → Réseaux sociaux: 5% à 15% (addiction par design)
  → Applications productivité: 0.5% à 2%
```

### Objectif avec le Système de Recommandation

```
OBJECTIF: Passer de 0.22% à 0.40%

Impact:
  ✅ +83% d'engagement
  ✅ +7,450€ de revenus (pour 322k users)
  ✅ Utilisateurs plus satisfaits (contenu pertinent)
  ✅ Cercle vertueux: plus de temps → meilleures recos → encore plus de temps
```

---

## 📊 FORMULE DE CALCUL

### Pour UN Utilisateur

```python
# Étape 1: Calculer le temps total passé
temps_passe_minutes = sum(durees_de_toutes_les_sessions)

# Étape 2: Calculer le temps écoulé depuis première visite
premiere_visite = timestamp_premiere_interaction
derniere_visite = timestamp_derniere_interaction
jours_ecoules = (derniere_visite - premiere_visite) / (24 * 3600)  # en jours

# Étape 3: Calculer le temps disponible
temps_disponible_minutes = jours_ecoules * 24 * 60

# Étape 4: Calculer le ratio
ratio_engagement = temps_passe_minutes / temps_disponible_minutes
ratio_engagement_pct = ratio_engagement * 100  # En pourcentage

print(f"Ratio d'engagement: {ratio_engagement_pct:.4f}%")
```

### Exemple Concret

```python
# Utilisateur A
premiere_visite = datetime(2024, 12, 1)   # 1er décembre
derniere_visite = datetime(2025, 1, 1)     # 1er janvier
jours_ecoules = 31 jours

temps_passe_total = 1440 minutes  # 24 heures sur 31 jours

temps_disponible = 31 × 24 × 60 = 44,640 minutes

ratio = 1440 / 44,640 = 0.0323 = 3.23%

→ Utilisateur très engagé (3.23% >> 0.22% moyenne)
```

---

## 💰 CALCUL DES REVENUS

### Avec Pubs Pop-up (Fréquence N2: 3.55 minutes)

```python
def calculate_revenue_from_engagement_ratio(
    num_users,
    avg_ratio,
    avg_days_elapsed,
    popup_interval_minutes=3.55,
    cpm=6.0
):
    """
    Calcule les revenus basés sur le ratio d'engagement

    Args:
        num_users: Nombre d'utilisateurs
        avg_ratio: Ratio d'engagement moyen (ex: 0.002189 pour 0.2189%)
        avg_days_elapsed: Nombre de jours moyen depuis première visite
        popup_interval_minutes: Intervalle entre pubs (défaut: 3.55 min)
        cpm: CPM des pubs (défaut: 6€)

    Returns:
        Revenus totaux en euros
    """
    # Temps disponible moyen par utilisateur
    avg_available_time_minutes = avg_days_elapsed * 24 * 60

    # Temps passé moyen par utilisateur
    avg_time_spent_minutes = avg_ratio * avg_available_time_minutes

    # Nombre de pubs par utilisateur
    avg_pubs_per_user = avg_time_spent_minutes / popup_interval_minutes

    # Revenu par utilisateur
    revenue_per_user = (avg_pubs_per_user / 1000.0) * cpm

    # Revenu total
    total_revenue = revenue_per_user * num_users

    return total_revenue

# Exemple: 322,897 utilisateurs, ratio 0.2189%
revenue = calculate_revenue_from_engagement_ratio(
    num_users=322897,
    avg_ratio=0.002189,  # 0.2189%
    avg_days_elapsed=5.20,
    popup_interval_minutes=3.55,
    cpm=6.0
)
print(f"Revenus: {revenue:.2f}€")  # Output: 8,975.47€
```

---

## 🚀 RECOMMANDATIONS

### 1. Adopter le Ratio d'Engagement comme Métrique Principale

```
✅ Métrique cible du système de recommandation
✅ KPI principal pour le dashboard business
✅ Critère d'optimisation pour Optuna
```

### 2. Objectifs par Segment d'Utilisateurs

```
┌──────────────────────┬─────────────────┬────────────────────┐
│  Segment             │  Ratio Actuel   │  Objectif (avec reco)│
├──────────────────────┼─────────────────┼────────────────────┤
│ Nouveaux (< 7 jours) │    0.05%        │    0.09% (+80%)    │
│ Actifs (7-30 jours)  │    0.15%        │    0.27% (+80%)    │
│ Réguliers (> 30 j)   │    0.30%        │    0.55% (+83%)    │
│ Power Users (top 10%)│    0.90%        │    1.65% (+83%)    │
└──────────────────────┴─────────────────┴────────────────────┘
```

### 3. Stratégie d'Optimisation

```
PHASE 1: Mesure (Mois 1)
  → Établir la baseline du ratio par segment
  → Identifier les utilisateurs à fort potentiel

PHASE 2: Test (Mois 2-3)
  → A/B test avec système de recommandation
  → Mesurer l'évolution du ratio
  → Ajuster les paramètres

PHASE 3: Déploiement (Mois 4+)
  → Rollout progressif (10% → 50% → 100%)
  → Monitoring continu du ratio
  → Optimisation continue
```

---

## 📋 RÉSUMÉ EXÉCUTIF

### La Métrique

```
RATIO D'ENGAGEMENT = Temps Passé / Temps Disponible

Exemple: 0.2189% = L'utilisateur moyen passe 0.22% de son temps avec nous
```

### Les Chiffres Clés (322,897 utilisateurs)

```
SANS recommandation:
  Ratio:    0.2189%
  Temps:    16.45 min
  Revenus:  8,975€

AVEC recommandation:
  Ratio:    0.4006%  (+83%)
  Temps:    30.10 min (+83%)
  Revenus: 16,425€   (+83%)

GAIN: +7,450€ (+83%)
```

### Pourquoi Cette Métrique ?

```
✅ Mesure directe de l'engagement
✅ Normalisation équitable (durée du compte)
✅ Simple à comprendre (% de temps)
✅ Prédictible (relation linéaire)
✅ Alignée avec objectif business
```

---

**Date:** 14 Janvier 2026
**Status:** ✅ Métrique Ratio d'Engagement validée et analysée
**Fichiers générés:**
- `evaluation/engagement_ratio_analysis.py` - Script d'analyse
- `evaluation/engagement_ratio_results.json` - Résultats JSON
- `evaluation/engagement_ratio_analysis.png` - Graphiques
- `METRIQUE_RATIO_ENGAGEMENT.md` - Cette documentation
