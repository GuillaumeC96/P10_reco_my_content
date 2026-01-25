# 🎯 Guide de Choix de la Fréquence de Publicité

**Objectif:** Aider à choisir la fréquence optimale (N1, N2, N3, N4) selon le profil business

---

## 📊 LES 4 FRÉQUENCES DISPONIBLES

```
┌──────────┬─────────────┬──────────────┬─────────────────┬─────────────┐
│ Quantile │  Fréquence  │ Pubs/session │  Gain/an        │  Trade-off  │
│          │             │ (avec reco)  │ (100k sessions) │             │
├──────────┼─────────────┼──────────────┼─────────────────┼─────────────┤
│ N1 (Q25) │  1.00 min   │    30.10     │  +8,190€        │ Max revenus │
│          │ 1 pub/min   │              │                 │ Risque UX   │
├──────────┼─────────────┼──────────────┼─────────────────┼─────────────┤
│ N2 (Q50) │  3.55 min   │     8.47     │  +2,305€ ⭐     │ Équilibre   │
│          │ 1 pub/3.5m  │              │                 │ RECOMMANDÉ  │
├──────────┼─────────────┼──────────────┼─────────────────┼─────────────┤
│ N3 (Q75) │ 15.75 min   │     1.91     │    +520€        │ Priorité UX │
│          │ 1 pub/16m   │              │                 │ Moins de $  │
├──────────┼─────────────┼──────────────┼─────────────────┼─────────────┤
│ N4 (Q90) │ 38.38 min   │     0.78     │    +213€        │ UX premium  │
│          │ 1 pub/38m   │              │                 │ Mini revenus│
└──────────┴─────────────┴──────────────┴─────────────────┴─────────────┘
```

---

## 🏢 QUEL PROFIL BUSINESS ÊTES-VOUS ?

### Profil 1: Start-up en Phase de Croissance

**Objectif:** Maximiser les revenus rapidement pour financer la croissance

```
✅ FRÉQUENCE RECOMMANDÉE: N1 (1 pub/minute)

Pourquoi?
  • Gain maximal: +8,190€/an (100k sessions)
  • Besoin de cash flow important en phase d'amorçage
  • Utilisateurs moins sensibles (en construction de base)
  • Possibilité de réduire plus tard (N2 ou N3)

⚠️  Points de vigilance:
  • Surveiller le taux de rebond de près
  • Implémenter un système de feedback utilisateur
  • Prévoir une transition vers N2 à moyen terme
  • Tester sur un segment (A/B test 10% vs 90%)

📊 Métriques à suivre:
  • Taux de rebond: ≤ 45% acceptable
  • Temps moyen: ≥ 25 minutes OK
  • Taux de retour: ≥ 30% OK
```

**Exemple d'entreprise:** Nouveau média d'actualité, blog lifestyle en phase de monétisation

---

### Profil 2: Média Établi avec Audience Fidèle

**Objectif:** Équilibre entre revenus et satisfaction utilisateur

```
✅ FRÉQUENCE RECOMMANDÉE: N2 (1 pub/3.55 minutes) ⭐

Pourquoi?
  • Gain solide: +2,305€/an (100k sessions)
  • Fréquence médiane = compromis naturel
  • 50% des utilisateurs habitués à ce rythme
  • Excellente base pour optimisation future

✅ Points forts:
  • Risque faible pour la fidélisation
  • Facilement ajustable (vers N1 ou N3)
  • UX acceptable pour la majorité
  • Revenus suffisants pour couvrir les coûts

📊 Métriques à suivre:
  • Taux de rebond: ≤ 40% excellent
  • Temps moyen: ≥ 28 minutes excellent
  • Taux de retour: ≥ 40% excellent
  • NPS (Net Promoter Score): ≥ 30 bon
```

**Exemple d'entreprise:** Site d'actualité régional, magazine en ligne, blog lifestyle mature

---

### Profil 3: Média Premium avec Audience Exigeante

**Objectif:** Priorité à l'expérience utilisateur, revenus secondaires

```
✅ FRÉQUENCE RECOMMANDÉE: N3 (1 pub/15.75 minutes)

Pourquoi?
  • Gain modéré: +520€/an (100k sessions)
  • Très peu intrusif (1 pub tous les 16 min)
  • Excellente UX préservée
  • Positionnement premium maintenu

✅ Points forts:
  • Taux de satisfaction élevé
  • Fidélisation maximale
  • Image de marque préservée
  • Possibilité de freemium (N3 gratuit, N4 premium)

📊 Métriques à suivre:
  • Taux de rebond: ≤ 35% excellent
  • Temps moyen: ≥ 30 minutes excellent
  • Taux de retour: ≥ 50% excellent
  • NPS: ≥ 50 excellent
```

**Exemple d'entreprise:** Magazine premium, média d'investigation, plateforme éditoriale haut de gamme

---

### Profil 4: Média d'Elite / Paywall Partiel

**Objectif:** UX irréprochable, monétisation par abonnement principalement

```
✅ FRÉQUENCE RECOMMANDÉE: N4 (1 pub/38.38 minutes)

Pourquoi?
  • Gain minimal: +213€/an (100k sessions)
  • Quasiment invisible (1 pub tous les 38 min)
  • UX premium garantie
  • Complémentaire à un modèle d'abonnement

✅ Points forts:
  • Aucun impact sur la satisfaction
  • Différenciation forte vs concurrence
  • Argument de vente pour abonnement (0 pub)
  • Revenus pub = bonus, pas objectif principal

📊 Métriques à suivre:
  • Taux de conversion abonnement: ≥ 5%
  • Taux de rétention abonnés: ≥ 80%
  • Taux de rebond: ≤ 30%
  • NPS: ≥ 60
```

**Exemple d'entreprise:** Le Monde, The New York Times, Financial Times

---

## 🔄 STRATÉGIE D'OPTIMISATION PROGRESSIVE

### Phase 1: Démarrage (Mois 1-3)

```
🎯 OBJECTIF: Établir une baseline et comprendre l'audience

ACTION:
  1. Commencer avec N2 (3.55 min) - Équilibre optimal
  2. Collecter les métriques pendant 3 mois:
     • Taux de rebond
     • Temps moyen par session
     • Taux de retour
     • Feedback qualitatif (si disponible)

DÉCISION APRÈS 3 MOIS:
  ✅ Taux de rebond ≤ 40% → Tester N1 (phase 2)
  ⚠️  Taux de rebond > 40% → Tester N3 (phase 2)
  ✅ Temps moyen ≥ 28 min → Bon signe, continuer
```

### Phase 2: A/B Testing (Mois 4-6)

```
🎯 OBJECTIF: Optimiser la fréquence pour VOTRE audience

SCÉNARIO A: Baseline positive (rebond ≤ 40%)
  ACTION:
    • 10% du trafic → N1 (1 min)
    • 90% du trafic → N2 (3.55 min)

  MESURER:
    • Différence de taux de rebond
    • Différence de temps moyen
    • Différence de revenus

  DÉCISION:
    ✅ Rebond N1 ≤ 45% → Déployer N1 sur 100%
    ❌ Rebond N1 > 45% → Garder N2

SCÉNARIO B: Baseline négative (rebond > 40%)
  ACTION:
    • 10% du trafic → N3 (16 min)
    • 90% du trafic → N2 (3.55 min)

  MESURER:
    • Amélioration du taux de rebond?
    • Impact sur les revenus?

  DÉCISION:
    ✅ Rebond N3 < Rebond N2 → Déployer N3
    ❌ Pas d'amélioration → Garder N2
```

### Phase 3: Optimisation Continue (Mois 7+)

```
🎯 OBJECTIF: Affiner la fréquence optimale

ACTIONS:
  1. Tester des fréquences intermédiaires:
     • 2 minutes (entre N1 et N2)
     • 5 minutes (entre N2 et N3)
     • 10 minutes (entre N2 et N3)

  2. Segmentation par profil utilisateur:
     • Nouveaux visiteurs → N3 (UX premium)
     • Visiteurs réguliers → N2 (équilibre)
     • Super users (>10 visites) → N1 (plus tolérants)

  3. Adaptation temporelle:
     • Heures creuses (nuit) → N1 (max revenus)
     • Heures de pointe (jour) → N2 (équilibre)
     • Weekend → N3 (meilleure UX)
```

---

## 📊 TABLEAU DE DÉCISION RAPIDE

### Selon Vos Métriques Actuelles

```
┌──────────────────────┬───────────────────────────────────────┐
│  Taux de Rebond      │  Fréquence Recommandée                │
├──────────────────────┼───────────────────────────────────────┤
│  ≤ 35%               │  N1 (1 min) - Vous pouvez pousser    │
│  36-40%              │  N2 (3.5 min) - Équilibre optimal ⭐ │
│  41-50%              │  N3 (16 min) - Réduire l'intrusion   │
│  > 50%               │  N4 (38 min) - UX critique            │
└──────────────────────┴───────────────────────────────────────┘

┌──────────────────────┬───────────────────────────────────────┐
│  Temps Moyen/Session │  Fréquence Recommandée                │
├──────────────────────┼───────────────────────────────────────┤
│  ≥ 30 min            │  N1 (1 min) - Audience très engagée  │
│  20-30 min           │  N2 (3.5 min) - Engagement correct ⭐ │
│  10-20 min           │  N3 (16 min) - Engagement faible      │
│  < 10 min            │  N4 (38 min) - Problème d'engagement  │
└──────────────────────┴───────────────────────────────────────┘

┌──────────────────────┬───────────────────────────────────────┐
│  Taux de Retour      │  Fréquence Recommandée                │
├──────────────────────┼───────────────────────────────────────┤
│  ≥ 50%               │  N1 (1 min) - Audience fidèle         │
│  30-50%              │  N2 (3.5 min) - Fidélisation OK ⭐    │
│  15-30%              │  N3 (16 min) - Fidélisation faible    │
│  < 15%               │  N4 (38 min) - Aucune fidélisation    │
└──────────────────────┴───────────────────────────────────────┘
```

---

## 💡 CAS D'USAGE CONCRETS

### Cas 1: E-commerce avec Blog de Contenu

**Contexte:**
- Site e-commerce avec blog lifestyle
- Objectif: Augmenter le temps passé avant achat
- Budget pub pour financer le blog

**Recommandation:**
```
✅ FRÉQUENCE: N2 (3.55 minutes)

Pourquoi?
  • Blog = Engagement moyen (articles 5-10 min)
  • Utilisateurs viennent pour acheter, pas lire
  • N2 = Bon compromis revenus/UX
  • Évite de détourner de l'achat (vs N1)

Stratégie:
  • Page produit: N4 (38 min) - Pas de distraction
  • Blog: N2 (3.55 min) - Monétisation
  • Page catégorie: N3 (16 min) - Équilibre
```

### Cas 2: Site d'Actualité Pure Player

**Contexte:**
- Actualité en continu (breaking news)
- Audience volatile (pic de trafic)
- Revenus 100% publicité

**Recommandation:**
```
✅ FRÉQUENCE: N1 (1 minute) ou N2 (3.55 minutes)

Pourquoi?
  • Breaking news = Visites courtes (2-5 min)
  • N1 permet de monétiser les visites rapides
  • Audience habituée aux pubs (gratuit)

Stratégie:
  • Breaking news: N1 (1 min) - Max revenus
  • Articles longs (analyses): N2 (3.5 min)
  • Page d'accueil: N2 (3.5 min)
```

### Cas 3: Média d'Investigation / Long-Form

**Contexte:**
- Articles très longs (15-30 min de lecture)
- Audience engagée et fidèle
- Mix revenus: pubs + abonnements

**Recommandation:**
```
✅ FRÉQUENCE: N3 (15.75 minutes)

Pourquoi?
  • Articles longs = Lecture immersive
  • N3 permet 1-2 pubs par article (non intrusif)
  • Préserve la qualité éditoriale
  • Encourage l'abonnement ("0 pub si abonné")

Stratégie:
  • Articles longs: N3 (16 min)
  • Abonnés: N4 (38 min) ou 0 pub
  • Visiteurs premium: N4 (38 min)
```

---

## 🎯 FORMULES DE CALCUL POUR VOTRE CAS

### Calculer Votre Gain Potentiel

```python
# Vos données
nb_sessions_an = 100000  # Nombre de sessions/an
temps_moyen_actuel = 16.45  # Minutes/session (avant reco)
augmentation_temps = 83  # % d'augmentation espérée

# Calculer le nouveau temps moyen
temps_moyen_reco = temps_moyen_actuel * (1 + augmentation_temps/100)

# Pour chaque fréquence
frequences = {
    'N1': 1.00,
    'N2': 3.55,
    'N3': 15.75,
    'N4': 38.38
}

for nom, intervalle in frequences.items():
    # Revenus AVANT reco
    pubs_avant = temps_moyen_actuel / intervalle
    revenus_avant = (pubs_avant / 1000) * 6 * nb_sessions_an

    # Revenus APRÈS reco
    pubs_apres = temps_moyen_reco / intervalle
    revenus_apres = (pubs_apres / 1000) * 6 * nb_sessions_an

    # Gain
    gain = revenus_apres - revenus_avant

    print(f"{nom}: +{gain:.0f}€/an")
```

---

## 📋 CHECKLIST DE DÉCISION

```
□ J'ai analysé mes métriques actuelles (rebond, temps, retour)
□ J'ai identifié mon profil business (start-up, média établi, premium)
□ J'ai choisi une fréquence de départ (N2 recommandé)
□ J'ai prévu un plan d'A/B testing (phase 2)
□ J'ai défini mes KPIs de succès
□ J'ai une stratégie de sortie si ça ne marche pas
□ J'ai communiqué le changement à l'équipe
□ J'ai prévu un monitoring des métriques clés
```

---

## 🎯 RÉSUMÉ: 3 QUESTIONS POUR DÉCIDER

### Question 1: Quel est mon objectif principal ?

```
A. Maximiser revenus rapidement     → N1 (1 min)
B. Équilibre revenus/satisfaction   → N2 (3.5 min) ⭐
C. Priorité expérience utilisateur  → N3 (16 min)
D. UX premium, revenus secondaires  → N4 (38 min)
```

### Question 2: Quel est mon taux de rebond actuel ?

```
A. ≤ 35% (excellent)                → N1 ou N2
B. 36-40% (bon)                     → N2 ⭐
C. 41-50% (moyen)                   → N3
D. > 50% (problème)                 → N4 + analyse UX
```

### Question 3: Quel est mon modèle économique ?

```
A. 100% publicité                   → N1 ou N2
B. Mix pub + autre revenus          → N2 ⭐
C. Priorité abonnements             → N3 ou N4
D. Freemium (pub gratuit, 0 payant) → N3 gratuit, N4 payant
```

---

**Recommandation par défaut si vous hésitez: N2 (3.55 minutes) ⭐**

**Pourquoi?** C'est le compromis optimal qui fonctionne pour 80% des cas d'usage.

---

**Date:** 14 Janvier 2026
**Prochaine étape:** Implémenter la fréquence choisie et surveiller les métriques
