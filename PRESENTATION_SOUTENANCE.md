# Système de Recommandation My Content
## Présentation de Soutenance

**Formation:** Data Scientist - OpenClassrooms
**Projet:** P10 - Système de recommandation hybride
**Date:** Décembre 2025

---

## SLIDE 1: Introduction

### Le contexte

**My Content:** Plateforme éditoriale financée par la publicité

**Problème business:**
- Utilisateurs lisent **1 seul article** par session en moyenne
- **Revenus publicitaires limités**
- Besoin d'augmenter l'engagement

**Ma mission:**
Concevoir et déployer un système de recommandation pour augmenter le nombre d'articles lus par session

---

## SLIDE 2: Objectifs du projet

### Objectifs techniques

✅ Recommandations personnalisées et pertinentes
✅ Latence < 200ms
✅ Scalable (100k+ sessions/mois)
✅ Déployé sur le cloud (Azure)

### Objectifs business

📈 Augmenter l'engagement (+83% d'articles/session visé)
💰 Augmenter les revenus publicitaires
⚡ Solution opérationnelle rapidement (MVP en 3 semaines)

---

## SLIDE 3: Les données

### Dataset

- **322,897 utilisateurs**
- **2,987,181 interactions** (avant filtre)
- **44,692 articles** uniques
- **385 fichiers CSV** (données distribuées)

### Règle business critique : Filtre 30 secondes

**Principe:** Si lecture < 30s, la 2ème pub ne s'affiche pas

**Impact:**
- ❌ Suppression de 114,282 interactions < 30s
- ✅ **2,872,899 interactions validées** (vraies lectures)

**Justification:** Seules les lectures générant 2 pubs comptent pour les revenus

---

## SLIDE 4: Approche - Signaux de qualité

### Innovation : 9 signaux comportementaux

Au lieu de juste compter les lectures, j'évalue la **qualité de l'engagement** :

| Signal | Description | Poids moyen |
|--------|-------------|-------------|
| **time_quality** | Durée de lecture | Variable |
| **click_quality** | Nombre de clicks | 0.1/click |
| **session_quality** | Position dans session | 0.252 |
| **device_quality** | Desktop vs Mobile | 0.688 |
| **environment_quality** | Environnement | 0.992 |
| **referrer_quality** | Source trafic | 0.864 |
| **os_quality** | Système d'exploitation | 0.848 |
| **country_quality** | Géolocalisation | 0.897 |
| **region_quality** | Région | 0.859 |

**Résultat:** `interaction_weight` (mean: 0.396) utilisé pour pondérer toutes les interactions

---

## SLIDE 5: Architecture - Algorithme hybride

### 3 composantes complémentaires

```
┌─────────────────┐  ┌──────────────────┐  ┌─────────────────┐
│  Content-Based  │  │ Collaborative    │  │ Temporal/       │
│      40%        │  │  Filtering 30%   │  │ Trending 30%    │
│                 │  │                  │  │                 │
│ Similarité      │  │ Utilisateurs     │  │ Articles        │
│ articles lus    │  │ similaires       │  │ récents         │
└────────┬────────┘  └────────┬─────────┘  └────────┬────────┘
         │                    │                     │
         └────────────────────┼─────────────────────┘
                              ↓
                    Fusion pondérée des scores
                              ↓
                    Diversification (MMR λ=0.7)
                              ↓
                    Top N recommandations
```

### Pourquoi hybride ?

- **Content:** Pas de cold start utilisateur
- **Collaborative:** Découverte de contenu inattendu
- **Temporal:** Favorise l'actualité récente

---

## SLIDE 6: Défis techniques - Optimisation mémoire

### Problème : Mémoire insuffisante

**Contexte:**
- Serveur: 66 GB RAM
- Limite fixée: 30 GB
- Besoin: Calculer 322k profils enrichis avec 9 signaux

**Versions 1-7:** ❌ Crash >40 GB RAM

### Solution V8 : Stratégie d'optimisation

1. **Chargement par batches** (50 fichiers à la fois)
2. **Agrégation incrémentale** (pas tout en mémoire)
3. **Construction par chunks** (5,000 users à la fois)
4. **Calcul vectorisé** (NumPy vs boucles Python)
5. **Garbage collection agressif**

**Résultat:** ✅ **4.99 GB / 30 GB** (réduction de 87.5%)

---

## SLIDE 7: Déploiement cloud - Azure Functions

### Choix d'architecture : Consumption Plan

**Avantages:**
- Coût très faible (~10€/mois MVP)
- Scalabilité automatique
- Pas de gestion serveur
- Paiement à l'usage

**Challenge:** Limites strictes (1.5 GB mémoire, 5 min timeout)

### Solution : Modèles Lite avec échantillonnage stratifié

**Stratégie:** Sélection équilibrée de 10,000 utilisateurs

| Niveau d'activité | % du dataset | Échantillon |
|-------------------|--------------|-------------|
| Peu actif (1-2 articles) | 32.3% | 3,230 users |
| Moyen-faible (3-4) | 19.1% | 1,910 users |
| Moyen-élevé (5-10) | 25.7% | 2,570 users |
| Très actif (>10) | 22.9% | 2,290 users |

**Résultats:**
- Modèles complets: 750 MB
- **Modèles Lite: 86 MB** (réduction 96%)
- Distribution représentative maintenue ✅

---

## SLIDE 8: Déploiement - Problème résolu

### Erreur HTTP 500 initiale

**Symptôme:** API retournait erreur 500 sans détails

**Cause:** Tentative de téléchargement des modèles depuis Blob Storage au runtime
- Dépassement timeout
- Problèmes de permissions
- Trop de latence

**Solution finale:** Inclure les modèles dans le package de déploiement

**Avantages:**
- Plus simple et fiable
- Pas de latence de téléchargement
- Les 86 MB tiennent dans les limites
- Modèles chargés une fois, réutilisés entre invocations

---

## SLIDE 9: Résultats - API fonctionnelle

### Endpoint déployé

```
https://func-mycontent-reco-1269.azurewebsites.net/api/recommend
```

### Test réussi

**Requête:**
```json
{
  "user_id": 58,
  "n": 5
}
```

**Réponse:** 5 recommandations avec scores, métadonnées

**Performance:**
- Premier appel (cold start): ~500ms
- Appels suivants: **~50-100ms** ✅ (objectif <200ms)

**Qualité:**
- Diversité: ✅ (MMR activé)
- Fraîcheur: ✅ (temporal decay 7 jours)
- Pertinence: ✅ (basée sur 9 signaux)

---

## SLIDE 10: Impact business quantifié

### Modèle de revenus publicitaires

**Publicités:**
- Interstitial (après 30s): 6€ CPM
- In-article: 2.7€ CPM

### Calcul de l'impact (100k sessions/an)

| Métrique | Sans reco | Avec reco | Gain |
|----------|-----------|-----------|------|
| Sessions/an | 100,000 | 100,000 | - |
| Articles/session | 1.0 | **1.83** | **+83%** |
| Pubs/session | 2.0 | 3.66 | +83% |
| **Revenus/an** | **10,440€** | **19,140€** | **+8,700€** |

### ROI (Return on Investment)

**Coûts:**
- Infrastructure MVP: 120€/an
- Infrastructure production (Premium): 1,800€/an

**ROI:**
- MVP: **+7,150%** (8,700€ - 120€)
- Production: **+383%** (8,700€ - 1,800€)

**Avec 1M sessions/an: +85,200€/an de gain net**

---

## SLIDE 11: Livrables

### Code et modèles

✅ **Code source complet** (GitHub ready)
✅ **Modèles complets** (322k users, 750 MB)
✅ **Modèles Lite** (10k users, 86 MB)
✅ **Pipeline de preprocessing** (optimisé mémoire)
✅ **API déployée** (Azure Functions)

### Documentation

✅ **PROJET_COMPLET.md** - Vue d'ensemble technique complète
✅ **AZURE_SUCCESS.md** - Guide de déploiement
✅ **GUIDE_DEPLOIEMENT_AZURE.md** - Procédure pas-à-pas
✅ **DEMO_SCRIPT.md** - Script de démonstration
✅ **README.md** - Introduction au projet

### Application démo

✅ **Streamlit app** - Interface interactive locale
✅ **Test scripts** - Validation qualité des recommandations

---

## SLIDE 12: Démonstration en direct

### Ce que je vais montrer

1. **API en production** - Requête curl en temps réel
2. **Recommandations générées** - Affichage JSON
3. **Paramètres ajustables** - Poids content/collab/trend
4. **Streamlit app** (optionnel) - Interface utilisateur

### Scénario de test

```bash
# Test simple
curl -X POST https://func-mycontent-reco-1269.azurewebsites.net/api/recommend \
  -H 'Content-Type: application/json' \
  -d '{"user_id": 58, "n": 5}'

# Test avec paramètres personnalisés
curl -X POST [...] \
  -d '{
    "user_id": 58,
    "n": 10,
    "weight_content": 0.5,
    "weight_collab": 0.3,
    "weight_trend": 0.2,
    "use_diversity": true
  }'
```

---

## SLIDE 13: Difficultés rencontrées et solutions

### 1. Mémoire insuffisante (V1-V7)

**Problème:** >40 GB RAM nécessaire
**Solution:** Batching + chunking + vectorisation → **4.99 GB**

### 2. Déploiement Azure - Erreur 500

**Problème:** Téléchargement modèles depuis Blob Storage échoue
**Solution:** Inclure modèles dans le package de déploiement

### 3. Taille des modèles (750 MB)

**Problème:** Trop volumineux pour Consumption Plan
**Solution:** Modèles Lite avec échantillonnage stratifié → **86 MB**

### 4. Compatibilité des formats

**Problème:** `article_popularity` dict vs DataFrame
**Solution:** Code robuste gérant les deux formats

### Apprentissage clé

**Toujours tester localement avant de déployer, et avoir un plan B!**

---

## SLIDE 14: Améliorer futures

### Court terme (1-3 mois)

1. **A/B testing** - Valider l'impact réel (+83% engagement)
2. **Application Insights** - Monitoring détaillé
3. **Alerting** - Notifications erreurs
4. **Tests utilisateurs réels** - Feedback qualitatif

### Moyen terme (3-6 mois)

1. **Premium Plan** - Si >100k sessions/mois
2. **Modèles complets** - Utiliser tous les 322k users
3. **Optimisation des poids** - Tuning basé sur métriques réelles
4. **Cache Redis** - Pré-calcul recommandations populaires

### Long terme (6-12 mois)

1. **Ré-entraînement automatique** - Pipeline hebdomadaire
2. **Bandits multi-armed** - Exploration/exploitation
3. **Deep Learning** - Neural Collaborative Filtering
4. **Explainability** - "Recommandé car vous avez lu X"

---

## SLIDE 15: Conclusion

### Ce que j'ai réalisé

✅ **Système hybride robuste** (3 approches complémentaires)
✅ **Innovation qualité** (9 signaux comportementaux)
✅ **Optimisations mémoire** (87.5% de réduction)
✅ **Déploiement cloud** (API production-ready)
✅ **Impact business** (+8,700€/an quantifié)
✅ **Documentation complète** (reproductible)

### Compétences mobilisées

**Data Science:**
- Recommender systems (content, collaborative, hybrid)
- Feature engineering (9 signaux de qualité)
- Optimisation mémoire et performance

**MLOps:**
- Déploiement cloud (Azure Functions)
- CI/CD et versioning
- Monitoring et debugging

**Business:**
- Analyse CPM et revenus publicitaires
- Calcul ROI et impact quantifié
- Communication stakeholders

---

## SLIDE 16: Questions ?

### Points clés à retenir

1. **Approche hybride** pour combiner le meilleur de 3 méthodes
2. **Filtre 30s** pour fidélité au business model réel
3. **9 signaux de qualité** pour engagement réel
4. **Optimisation mémoire** (87.5% réduction)
5. **Déploiement Azure** production-ready
6. **ROI exceptionnel** (+7,150% pour MVP)

### Ressources

**API endpoint:**
```
https://func-mycontent-reco-1269.azurewebsites.net/api/recommend
```

**Documentation:**
- PROJET_COMPLET.md - Vue d'ensemble technique
- AZURE_SUCCESS.md - Guide déploiement
- DEMO_SCRIPT.md - Script de démonstration

---

**Merci pour votre attention !**

**Questions ?**

---

## ANNEXE: Backup slides

### BACKUP 1: Architecture détaillée

```
┌─────────────────────────────────────────────────────────────┐
│                    PIPELINE DE DONNÉES                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Données brutes → Exploration → Prétraitement              │
│       ↓              ↓              ↓                       │
│  385 CSV       Analyse stats   Filtre 30s                  │
│  2.98M inter.  Visualisations  Calcul poids                │
│                                                             │
│  → Profils enrichis (9 signaux)                            │
│  → Matrice pondérée (interaction_weight)                   │
│  → Embeddings TF-IDF                                       │
│  → Modèles complets (750 MB)                               │
│  → Modèles Lite (86 MB)                                    │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                  MOTEUR DE RECOMMANDATION                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Input: user_id, n_recommendations, weights                │
│         ↓                                                   │
│  Profil utilisateur (articles lus + poids)                 │
│         ↓                                                   │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Content     │  │ Collaborative│  │ Temporal     │      │
│  │ Cosine sim  │  │ User-user    │  │ Decay 7j     │      │
│  │ TF-IDF      │  │ Weighted     │  │ Popularity   │      │
│  └──────┬──────┘  └──────┬───────┘  └──────┬───────┘      │
│         └─────────────────┼──────────────────┘             │
│                           ↓                                │
│              Fusion: 0.4C + 0.3Collab + 0.3T              │
│                           ↓                                │
│              Diversification MMR (λ=0.7)                   │
│                           ↓                                │
│              Top N articles (scores + metadata)            │
└─────────────────────────────────────────────────────────────┘
```

### BACKUP 2: Formules mathématiques

**Interaction weight:**
```
w = 0.3*time_q + 0.2*click_q + 0.1*session_q +
    0.1*device_q + 0.05*env_q + 0.1*referrer_q +
    0.05*os_q + 0.05*country_q + 0.05*region_q
```

**Content score:**
```
score_content = cosine_similarity(
    user_profile_vector,
    article_embedding
)
```

**Collaborative score:**
```
score_collab = Σ(similarity[neighbor] * weight[neighbor, article])
               for neighbor in top_k_neighbors
```

**Temporal score:**
```
age_days = (now - article_created_at) / 86400
decay = 2^(-age_days / 7.0)
score_temporal = popularity * decay
```

**MMR:**
```
MMR = λ * Relevance - (1-λ) * max(Similarity with selected)
```

### BACKUP 3: Statistiques détaillées

**Dataset complet:**
- Users: 322,897
- Interactions (après 30s): 2,872,899
- Articles: 44,692
- Mémoire V8: 4.99 GB / 30 GB

**Modèles Lite:**
- Users: 10,000 (stratifié)
- Interactions: 78,553
- Articles: 7,732
- Taille: 86 MB

**Distribution interaction_weight:**
- Mean: 0.396
- Median: 0.340
- Std: 0.15 (estimé)
- Min: 0.050
- Max: 1.000

**Performance API:**
- Cold start: ~500ms
- Warm: ~50-100ms
- Throughput: >1000 req/min (estimé)

### BACKUP 4: Comparaison des approches

| Approche | Avantages | Inconvénients |
|----------|-----------|---------------|
| **Content-Based** | • Pas de cold start user<br>• Explainable<br>• Diversité contrôlée | • Bulle de filtre<br>• Besoin métadonnées |
| **Collaborative** | • Serendipity<br>• Pas de métadonnées | • Cold start user/item<br>• Biais popularité |
| **Temporal** | • Fraîcheur<br>• Adaptation actualité | • Favorise trop le récent<br>• Pas personnalisé |
| **Hybride (notre choix)** | ✅ **Combine avantages** | Configuration complexe |

### BACKUP 5: Technologies alternatives considérées

**Infrastructure:**
- ❌ AWS Lambda - Coût plus élevé, moins d'expérience
- ❌ Azure Container Instances - Plus complexe, coût ~80€/mois
- ❌ Azure App Service - Pas serverless, coût fixe
- ✅ **Azure Functions Consumption** - Optimal MVP

**Algorithmes:**
- ❌ Matrix Factorization (SVD) - Cold start problématique
- ❌ Deep Learning (NCF) - Complexité et coût GPU
- ❌ Content-only - Manque de diversité
- ✅ **Hybride 40/30/30** - Équilibre optimal

**Stockage modèles:**
- ❌ Téléchargement Blob Storage - Timeout et latence
- ❌ Azure Files mount - Nécessite Premium Plan
- ✅ **Inclus dans package** - Simple et fiable
