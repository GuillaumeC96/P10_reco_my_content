# 📊 Tableau Comparatif: Ancienne vs Nouvelle Métrique

**Date:** 14 Janvier 2026

---

## 🎯 COMPARAISON VISUELLE

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      ANCIENNE MÉTRIQUE (CPM)                            │
│                                                                         │
│  Principe:   Revenus basés sur le NOMBRE D'ARTICLES lus                │
│  Pubs:       2 types (Interstitielle 6€ + In-article 2.7€)             │
│  Formule:    Revenus = (Articles × 6€/1000) + (Pages × 2.7€/1000)      │
│  Complexité: Élevée (facteur de visibilité, seuil 30s)                 │
│                                                                         │
│  Résultats (100k sessions/an):                                         │
│    SANS reco:    870€/an                                                │
│    AVEC reco:  1,816€/an                                                │
│    GAIN:        +946€ (+109%)                                           │
│                                                                         │
│  Limites:                                                               │
│    ❌ Difficile à expliquer                                             │
│    ❌ Seuil arbitraire (30s)                                            │
│    ❌ Proxy indirect (articles ≠ engagement direct)                     │
│    ❌ Pas flexible (1 seul modèle)                                      │
└─────────────────────────────────────────────────────────────────────────┘

                            ⬇️  TRANSITION  ⬇️

┌─────────────────────────────────────────────────────────────────────────┐
│                   NOUVELLE MÉTRIQUE (TEMPS PASSÉ)                       │
│                                                                         │
│  Principe:   Revenus basés sur le TEMPS PASSÉ (minutes)                │
│  Pubs:       1 type (Pop-up 6€ CPM)                                    │
│  Formule:    Revenus = (Temps / Fréquence) × (6€ / 1000)               │
│  Complexité: Simple (relation linéaire)                                │
│                                                                         │
│  Résultats (100k sessions/an, Fréquence N2: 3.55 min):                 │
│    SANS reco:  2,777€/an                                                │
│    AVEC reco:  5,082€/an                                                │
│    GAIN:      +2,305€ (+83%)                                            │
│                                                                         │
│  Avantages:                                                             │
│    ✅ Simple à comprendre et à expliquer                                │
│    ✅ Mesure directe de l'engagement (temps)                            │
│    ✅ Flexible (4 fréquences testables: N1, N2, N3, N4)                │
│    ✅ Prédictible (+X% temps = +X% revenus)                             │
│    ✅ +1,359€ de revenus vs ancienne métrique                           │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 📈 TABLEAU COMPARATIF DÉTAILLÉ

### Caractéristiques

| Critère | Ancienne Métrique (CPM) | Nouvelle Métrique (Temps) |
|---------|-------------------------|---------------------------|
| **Métrique cible** | Nombre d'articles lus | Temps passé (minutes) |
| **Types de pubs** | 2 (Interstitielle + In-article) | 1 (Pop-up) |
| **CPM** | Mix 6€ + 2.7€ (≈4.83€ effectif) | 6€ fixe |
| **Complexité** | Élevée | Simple |
| **Formule** | `(Articles × 6€) + (Pages × 2.7€)` | `(Temps / Fréquence) × 6€` |
| **Flexibilité** | 1 modèle unique | 4 fréquences (N1-N4) |
| **Prédictibilité** | Complexe (facteur visibilité) | Linéaire (+X% temps = +X% €) |

### Résultats Financiers (100,000 sessions/an)

| Scénario | Ancienne Métrique | Nouvelle Métrique (N2) | Différence |
|----------|-------------------|------------------------|------------|
| **SANS reco** | 870€ | 2,777€ | +1,907€ (+219%) |
| **AVEC reco** | 1,816€ | 5,082€ | +3,266€ (+180%) |
| **GAIN** | +946€ (+109%) | +2,305€ (+83%) | +1,359€ (+144%) |

### Avantages / Inconvénients

| | Ancienne Métrique | Nouvelle Métrique |
|---------|-------------------|-------------------|
| **Avantages** | • Modèle établi<br>• Basé sur actions concrètes (articles lus) | • Simple à comprendre<br>• Mesure directe engagement<br>• Flexible (4 fréquences)<br>• Prédictible<br>• Revenus supérieurs (+144%) |
| **Inconvénients** | • Complexe à expliquer<br>• Seuil arbitraire (30s)<br>• Proxy indirect<br>• Moins de revenus | • Nouveau modèle (à valider)<br>• Nécessite choix fréquence |

---

## 💰 IMPACT FINANCIER PAR FRÉQUENCE (Nouvelle Métrique)

### 100,000 sessions/an

```
┌──────────┬─────────────┬──────────────┬─────────────┬─────────────┬─────────────┐
│ Quantile │  Fréquence  │ SANS reco    │ AVEC reco   │    GAIN     │  vs Ancienne│
├──────────┼─────────────┼──────────────┼─────────────┼─────────────┼─────────────┤
│ N1 (Q25) │  1.00 min   │   9,868€     │  18,058€    │  +8,190€    │  +7,244€ ⭐ │
│          │ 1 pub/min   │              │             │  (+83%)     │  (+866%)    │
├──────────┼─────────────┼──────────────┼─────────────┼─────────────┼─────────────┤
│ N2 (Q50) │  3.55 min   │   2,777€     │   5,082€    │  +2,305€ ⭐ │  +1,359€    │
│          │ 1 pub/3.5m  │              │             │  (+83%)     │  (+144%)    │
├──────────┼─────────────┼──────────────┼─────────────┼─────────────┼─────────────┤
│ N3 (Q75) │ 15.75 min   │     627€     │   1,147€    │    +520€    │    -426€    │
│          │ 1 pub/16m   │              │             │  (+83%)     │   (-45%)    │
├──────────┼─────────────┼──────────────┼─────────────┼─────────────┼─────────────┤
│ N4 (Q90) │ 38.38 min   │     257€     │     471€    │    +213€    │    -733€    │
│          │ 1 pub/38m   │              │             │  (+83%)     │   (-77%)    │
└──────────┴─────────────┴──────────────┴─────────────┴─────────────┴─────────────┘

Ancienne métrique (CPM): +946€

⭐ N2 recommandé: Meilleur équilibre revenus/UX avec +1,359€ vs ancienne
⭐ N1 max revenus: +7,244€ vs ancienne mais risque UX
```

---

## 🎯 RECOMMANDATIONS PAR PROFIL

| Profil Business | Ancienne Métrique | Nouvelle Métrique | Fréquence | Gain vs Ancienne |
|----------------|-------------------|-------------------|-----------|------------------|
| **Start-up croissance** | 1,816€ | 18,058€ | N1 (1 min) | +16,242€ (+894%) |
| **Média établi** | 1,816€ | 5,082€ | N2 (3.55 min) ⭐ | +3,266€ (+180%) |
| **Média premium** | 1,816€ | 1,147€ | N3 (16 min) | -669€ (-37%) |
| **Média d'élite** | 1,816€ | 471€ | N4 (38 min) | -1,345€ (-74%) |

**Note:** Les profils premium et élite compensent par abonnements/autres revenus

---

## 📊 GRAPHIQUE DE POSITIONNEMENT

```
Revenus
   │
20k│                    ● N1 (Start-up)
   │                    │
   │                    │
15k│                    │
   │                    │
   │                    │
10k│                    │
   │                    │
   │                    │
 5k│              ● N2 (Média établi) ⭐ RECOMMANDÉ
   │          ╱
   │      ╱
   │  ● Ancienne Métrique
   │╱
 1k● N3 (Premium)
   │
   │● N4 (Élite)
   │
   └─────────────────────────────────────────────────────────── UX
   Mauvaise                  Bonne                      Excellente
```

---

## ✅ CONCLUSION

### Ce qui change

```
AVANT (Ancienne Métrique)        APRÈS (Nouvelle Métrique)
─────────────────────────────────────────────────────────
Articles lus           →         Temps passé
2 types de pubs        →         1 type de pub
6€ + 2.7€ CPM         →         6€ CPM fixe
Complexe              →         Simple
+946€                 →         +2,305€ (N2)
1 modèle              →         4 fréquences (N1-N4)
```

### Pourquoi changer ?

```
✅ +144% de revenus supplémentaires (N2 vs Ancienne)
✅ Simplicité: formule linéaire facile à comprendre
✅ Flexibilité: 4 fréquences testables selon le profil
✅ Prédictibilité: relation linéaire temps/revenus
✅ Alignement: métrique = objectif (temps passé)
```

### Recommandation

```
🎯 FRÉQUENCE N2 (1 pub/3.55 minutes)

Pourquoi?
  • +2,305€/an (vs +946€ ancienne) = +144%
  • Équilibre optimal revenus/UX
  • Fréquence médiane (50% utilisateurs)
  • Facile à ajuster (N1 ou N3 si besoin)
  • Risque faible pour la fidélisation
```

---

**Date:** 14 Janvier 2026
**Status:** ✅ Tableau comparatif prêt pour présentation
**Utilisation:** Slide de présentation, document décisionnel
