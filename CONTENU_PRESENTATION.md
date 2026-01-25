# My Content - Système de Recommandation d'Articles
## Contenu de la Présentation - VERSION FINALE (avec améliorations)

---

## SLIDE 1 - PAGE DE TITRE
**My Content - Système de Recommandation d'Articles**

Encourager la lecture par des recommandations pertinentes

Guillaume Cassez - CTO & Co-fondateur
Janvier 2026

---

## SLIDE 2 - CONTEXTE & PROBLÉMATIQUE

**Le défi de My Content**

- Start-up qui veut encourager la lecture
- Objectif: Recommander des contenus pertinents aux utilisateurs
- Problématique: Comment personnaliser l'expérience de lecture ?

**Notre approche MVP**
- Développer un premier prototype fonctionnel
- Tester avec des données réelles (Globo.com)
- Valider la faisabilité technique avant le scale-up

---

## SLIDE 3 - FONCTIONNALITÉ CIBLE

**User Story Principale**

> "En tant qu'utilisateur de l'application, je vais recevoir une sélection de cinq articles personnalisés"

**Critères de succès**
- ✅ Recommandations personnalisées par utilisateur
- ✅ Top 5 articles pertinents
- ✅ Prise en compte des préférences historiques
- ✅ Diversité des catégories

---

## SLIDE 4 - DATASET UTILISÉ

**Globo.com News Portal User Interactions**

**Volume de données**
- 364 047 articles avec métadonnées complètes
- ~845 000 interactions utilisateurs (clics)
- 461 catégories d'articles
- Embeddings pré-calculés de 250 dimensions (347 MB)

**Richesse des données**
- Métadonnées: catégorie, publisher, nombre de mots, timestamps
- Comportements: clics, sessions, séquences de lecture
- Embeddings: Représentation vectorielle du contenu

---

## SLIDE 5 - EXPLORATION ET PRÉPARATION DES DONNÉES

**Phase d'analyse préliminaire (EDA)**

**Analyse descriptive**
- 461 catégories → Focus sur top 20 (80% du traffic)
- Distribution articles/catégorie: [20, 50K], médiane ~300
- Nombre de mots par article: [50, 5000], moyenne ~450 mots
- Embeddings 250D pré-calculés (BERT)

**Découvertes clés lors de l'exploration**
- ⚠️ Temps de lecture incohérents (jusqu'à 48h pour un article!)
- 📊 Sessions multi-onglets très fréquentes
- 🎯 Nécessité de nettoyer les "temps fantômes"

**Actions de préparation**
1. **Nettoyage des anomalies temporelles** (détaillé slide 11)
2. **Calcul de 9 signaux de qualité** (détaillé slide 12)
3. **Création matrice user-item pondérée** (temps réel + clics)
4. **Génération modèles lite** (10K users) pour déploiement

**Script:** `data_exploration.py`, `analyze_time_anomalies.py`, `clean_interaction_data_v3.py`

---

## SLIDE 6 - DESCRIPTION FONCTIONNELLE DE L'APPLICATION

**Architecture MVP - 3 composants principaux**

1. **Application Streamlit** (Interface utilisateur)
   - Sélection d'un utilisateur
   - Configuration des paramètres
   - Affichage des 5 articles recommandés
   - Export des résultats

2. **Azure Functions** (Serverless compute)
   - Traitement des requêtes HTTP
   - Génération des recommandations
   - API accessible via Function URL
   - **Endpoint:** https://func-mycontent-reco-1269.azurewebsites.net/api/recommend

3. **Azure Blob Storage** (Stockage)
   - Modèles de Machine Learning (86 MB lite)
   - Embeddings des articles
   - Métadonnées

---

## SLIDE 7 - DÉMONSTRATION APPLICATION

**Interface Streamlit**

Fonctionnalités démontrées:
- Saisie d'un user_id
- Choix du nombre de recommandations (1-50)
- Réglage des poids (collaborative, content, temporal)
- Activation/désactivation du filtre de diversité
- Affichage des résultats avec métadonnées complètes
- Téléchargement CSV

**Deux modes disponibles**
- Mode Local: Calcul en local sur la machine
- Mode Azure: Appel API Azure Functions (serverless)

---

## SLIDE 8 - APPROCHES DE RECOMMANDATION ANALYSÉES

**3 approches principales étudiées**

1. **Filtrage Collaboratif (Collaborative Filtering)**
   - Basé sur les similarités entre utilisateurs
   - "Les utilisateurs similaires aiment des contenus similaires"

2. **Filtrage Basé sur le Contenu (Content-Based)**
   - Basé sur les caractéristiques des articles
   - "Recommander des articles similaires à ceux déjà lus"

3. **Approche Hybride + Temporal** ⭐ (Solution retenue)
   - Combine les deux approches précédentes
   - Ajoute un composant temporal (tendances)
   - Tire parti des forces de chaque méthode

---

## SLIDE 9 - FILTRAGE COLLABORATIF

**Principe**
- Calcule la similarité entre utilisateurs via leurs interactions
- Identifie les K utilisateurs les plus similaires (K=50)
- Recommande les articles appréciés par ces utilisateurs

**Avantages** ✅
- ✅ Découvre des contenus inattendus (serendipity)
- ✅ Ne nécessite pas d'analyse du contenu des articles
- ✅ S'améliore avec le nombre d'utilisateurs
- ✅ Capture les tendances collectives

**Inconvénients** ❌
- ❌ Cold Start: inefficace pour nouveaux utilisateurs
- ❌ Sparsité: matrice creuse (99%+ de zéros)
- ❌ Problème d'échelle: coût de calcul élevé
- ❌ Popularité bias: favorise les articles populaires

---

## SLIDE 10 - FILTRAGE BASÉ SUR LE CONTENU

**Principe**
- Utilise les embeddings (vecteurs 250D) des articles
- Calcule le profil utilisateur = moyenne des embeddings lus
- Recommande les articles les plus similaires au profil

**Avantages** ✅
- ✅ Pas de Cold Start utilisateur
- ✅ Fonctionne avec nouveaux articles immédiatement
- ✅ Expliquabilité: recommandations basées sur contenus similaires
- ✅ Indépendant du nombre d'utilisateurs

**Inconvénients** ❌
- ❌ Filter Bubble: recommandations trop similaires
- ❌ Manque de diversité
- ❌ Ne capture pas les préférences collectives
- ❌ Dépend de la qualité des embeddings

---

## SLIDE 11 - APPROCHE HYBRIDE + TEMPORAL (SOLUTION RETENUE)

**Formule de scoring à 3 composantes**

```
Score_final = 40% × Score_content + 30% × Score_collaborative + 30% × Score_temporal
```

**Poids configurables**
- Content-Based: 40% (profil utilisateur)
- Collaborative: 30% (utilisateurs similaires)
- Temporal/Trending: 30% (articles récents populaires)

**Pourquoi l'hybride à 3 composantes ?**
- ✅ Combine les forces des approches
- ✅ Atténue les faiblesses respectives
- ✅ Meilleure performance globale
- ✅ Flexibilité via poids ajustables
- ✅ Équilibre personnalisation et découverte

**Composants additionnels**
- Filtre de diversité des catégories
- Gestion du Cold Start (fallback sur popularité)
- Exclusion des articles déjà lus
- Temporal decay (favorise articles récents)

---

## SLIDE 12 - AMÉLIORATION MAJEURE: DÉTECTION TEMPS FANTÔMES

**Problématique identifiée**
- Utilisateurs laissent des onglets ouverts sans lire
- Multiples onglets ouverts simultanément
- Dernier article de la session peut rester affiché des heures
- **Impact:** Fausse le calcul de l'engagement réel

**Solutions implémentées** ⭐

**1. Filtre 30 secondes (seuil critique)**
- Temps < 30 secondes → Article NON lu (clic accidentel)
- 30 secondes = temps minimum pour afficher 2ème publicité
- **Impact business:** Seules les vraies lectures comptent

**2. Détection clics accidentels (< 10 secondes)**
- Clic par erreur, titre trompeur, retour arrière rapide
- Temps = 0 (pas de poids dans les recommandations)

**3. Gestion changements de session**
- Changement de session → ancien article temps = 0
- Nouvelle session = ancien article abandonné

**4. Plafonnement temps de lecture**
- Plafonné à 1× le temps théorique de lecture
- Basé sur nombre de mots / 200 mots par minute

**Résultat:** Recommandations basées sur interactions réelles, pas sur onglets ouverts

---

## SLIDE 13 - 9 SIGNAUX DE QUALITÉ D'INTERACTION

**Au-delà du simple "clic" ou "temps passé"**

**Signaux utilisés pour pondérer chaque interaction:**

1. **Temps passé** (ajusté, filtré >= 30s)
2. **Nombre de clics** sur l'article
3. **Qualité de session** (taille session: 2-9 articles)
4. **Type de device** (Desktop > Tablette > Mobile)
5. **Environnement** (Application > Site web)
6. **Type de referrer** (Internal > Social > External)
7. **Système d'exploitation** (fréquence d'utilisation)
8. **Pays** (pays principal > autres)
9. **Région** (région principale > autres)

**Poids final d'interaction:**
```
weight = 60% × temps_normalisé + 40% × clicks_normalisé
avec pondération par les 7 signaux contextuels
```

**Impact:** Recommandations de haute qualité basées sur engagement réel

---

## SLIDE 14 - COMPARAISON DES APPROCHES

| Critère | Collaborative | Content-Based | **Hybride 3× + Signaux** |
|---------|--------------|---------------|--------------------------|
| Nouveaux utilisateurs | ❌ Faible | ✅ Bon | ✅ **Excellent** |
| Nouveaux articles | ⚠️ Moyen | ✅ Excellent | ✅ **Excellent** |
| Diversité | ✅ Bonne | ❌ Faible | ✅ **Excellente** |
| Serendipity | ✅ Excellente | ❌ Faible | ✅ **Excellente** |
| Scalabilité | ❌ Difficile | ✅ Facile | ✅ **Bonne** |
| Sparsité | ❌ Problème | ✅ Robuste | ✅ **Robuste** |
| Qualité données | ⚠️ Clics bruts | ⚠️ Embeddings | ✅ **9 signaux** |
| **Performance** | ⚠️ Moyenne | ⚠️ Moyenne | ✅ **Meilleure** |

**Verdict:** L'approche hybride à 3 composantes avec 9 signaux offre la meilleure performance globale

---

## SLIDE 14 - ARCHITECTURE TECHNIQUE MVP

**Schéma de l'architecture déployée**

```
┌─────────────────┐
│  UTILISATEUR    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   STREAMLIT     │ ← Interface Web (Python)
│   APPLICATION   │   - Sélection user_id
└────────┬────────┘   - Configuration paramètres
         │            - Affichage résultats
         │ HTTPS
         ▼
┌─────────────────┐
│ AZURE FUNCTIONS │ ← Serverless Compute
│                 │   - Python 3.11, Consumption Plan
└────────┬────────┘   - France Central
         │            - Modèles Lite inclus (86 MB)
         │
         ▼
┌─────────────────┐
│ AZURE BLOB      │ ← Stockage Cloud (backup)
│ STORAGE         │   - Modèles complets
└─────────────────┘   - Historique
```

**Déploiement actuel:**
- **Function App:** func-mycontent-reco-1269
- **Resource Group:** rg-mycontent-prod
- **Region:** France Central
- **Plan:** Consumption (~10€/mois)

---

## SLIDE 15 - SYSTÈME DE RECOMMANDATION - ALGORITHME

**Pipeline de recommandation (6 étapes)**

1. **Vérification utilisateur**
   - Utilisateur connu → Hybride 3× (40/30/30)
   - Nouvel utilisateur → Popularité (Cold Start)

2. **Content-Based Filtering (40%)**
   - Calcul profil utilisateur (embedding moyen)
   - Similarité cosinus avec tous les articles
   - Filtrage articles déjà lus

3. **Collaborative Filtering (30%)**
   - Calcul similarité cosinus entre utilisateurs
   - Sélection top-50 utilisateurs similaires
   - Agrégation articles pondérée par similarité

4. **Temporal/Trending Filtering (30%)**
   - Articles récents et populaires
   - Temporal decay (half-life 7 jours)
   - Favorise contenu frais

5. **Scoring Hybride**
   - Combinaison 40% content + 30% collab + 30% temporal
   - Normalisation des scores
   - Pondération par les 9 signaux de qualité

6. **Filtre de diversité** (optionnel)
   - Garantit variété des catégories
   - Évite sur-représentation d'une catégorie
   - Sélection round-robin par catégorie

7. **Retour Top-N**
   - Sélection des N meilleurs articles
   - Ajout métadonnées complètes

---

## SLIDE 16 - GESTION DU COLD START

**Problématique**
- Nouveaux utilisateurs: pas d'historique
- Nouveaux articles: pas d'interactions

**Solutions implémentées**

1. **Nouveaux utilisateurs**
   - Fallback sur recommandations par popularité
   - Calcul basé sur engagement réel (filtre 30s, 9 signaux)
   - Permet de démarrer immédiatement

2. **Nouveaux articles**
   - Content-Based fonctionne immédiatement
   - Utilise l'embedding de l'article
   - Pas besoin d'interactions
   - Recommandé aux utilisateurs profil similaire

3. **Utilisateurs avec peu d'historique**
   - Hybride avec poids ajustés
   - Plus de poids sur content-based
   - Transition progressive vers collaborative

---

## SLIDE 17 - DÉPLOIEMENT AZURE SERVERLESS

**Pourquoi Azure Functions ?**

**Avantages techniques** ✅
- ✅ Pas de serveur à gérer
- ✅ Auto-scaling automatique (0 → N instances)
- ✅ Paiement à l'usage (pas de coût fixe)
- ✅ Haute disponibilité native

**Avantages business** 💰
- Coût minimal pour un MVP (~10€/mois)
- Free tier: 1M exécutions/mois gratuites
- Adapté à charge variable
- Time-to-market rapide

**Performance**
- Latence: ~50-100ms (warm)
- Latence: ~500ms (cold start avec chargement modèles)
- Modèles Lite inclus (86 MB, 10k users)

**Déploiement automatisé**
- Script `deploy_azure.sh` fourni
- Configuration automatique
- Monitoring via Application Insights

---

## SLIDE 18 - MÉTRIQUES & PERFORMANCE

**Temps de réponse**
- Warm Azure Functions: 50-100ms
- Cold Start: ~500ms (chargement modèles)
- Mode Local: <1 seconde

**Consommation ressources**
- Azure Functions: Consumption Plan
- Stockage: 86 MB (modèles Lite)
- Mémoire: Jusqu'à 1.5 GB disponible

**Qualité des recommandations**
- Filtre 30 secondes appliqué: vraies lectures uniquement
- 9 signaux de qualité intégrés
- Temporal decay actif (favorise contenu frais)
- Architecture hybride 40/30/30

**Scalabilité actuelle**
- Utilisateurs dans modèles Lite: 10 000 (équilibrés)
- Articles actifs: 7 732
- Interactions filtrées: 78 553 (>= 30 secondes)
- Modèles complets disponibles: 160k users, 38k articles

---

## SLIDE 19 - ARCHITECTURE CIBLE - VISION

**Évolution MVP → Production à grande échelle**

**Objectifs de l'architecture cible**
- ✅ Gestion de millions d'utilisateurs
- ✅ Ajout temps réel de nouveaux utilisateurs
- ✅ Ingestion continue de nouveaux articles
- ✅ Mise à jour des modèles sans interruption
- ✅ Temps de réponse < 100ms
- ✅ Haute disponibilité (99.9%)

**Principes architecturaux**
- Microservices découplés
- Event-driven architecture
- Caching multi-niveaux
- Pipeline ML automatisé
- Monitoring & observabilité complète

---

## SLIDE 20 - ARCHITECTURE CIBLE - SCHÉMA

```
┌──────────────────────────────────────────────────┐
│              UTILISATEURS (Web + Mobile)          │
└───────────────────┬──────────────────────────────┘
                    │
         ┌──────────┴──────────┐
         ▼                     ▼
┌─────────────────┐   ┌─────────────────┐
│  CloudFront CDN │   │  API Gateway    │
│  (Frontend)     │   │  (REST/GraphQL) │
└─────────────────┘   └────────┬────────┘
                               │
              ┌────────────────┼────────────────┐
              ▼                ▼                ▼
         ┌─────────┐     ┌──────────┐    ┌──────────┐
         │ Azure   │     │  Cache   │    │  Auth    │
         │Functions│     │  Redis   │    │ Azure AD │
         └────┬────┘     └────┬─────┘    └──────────┘
              │               │
              └───────┬───────┘
                      ▼
         ┌────────────────────────┐
         │  Data Storage Layer    │
         │  - Cosmos DB (Users)   │
         │  - Blob Storage (Models)│
         │  - SQL (Metadata)      │
         └───────────┬────────────┘
                     │
                     ▼
         ┌────────────────────────┐
         │  ML Pipeline           │
         │  - Event Hubs (Stream) │
         │  - ML Studio (Training)│
         │  - Data Factory (ETL)  │
         └────────────────────────┘
```

---

## SLIDE 21 - NOUVEAUX UTILISATEURS - ARCHITECTURE CIBLE

**Gestion en temps réel des nouveaux utilisateurs**

**1. Onboarding**
```
Inscription → Azure AD → User Profile créé dans Cosmos DB
```
- Collecte préférences initiales (catégories favorites)
- Optionnel: Sélection de topics d'intérêt

**2. Premières recommandations**
- **Phase 1** (0 interaction): Recommandations populaires + catégories choisies
- **Phase 2** (1-5 interactions): Hybride avec fort poids content-based
- **Phase 3** (5+ interactions): Hybride équilibré 40/30/30

**3. Streaming des interactions**
```
Clic article → Event Hubs → Azure Functions → Cosmos DB + Blob Storage
```
- Capture en temps réel des clics
- Filtre 30 secondes appliqué automatiquement
- Mise à jour profil utilisateur immédiate
- Agrégation pour retraining

**4. Cache Redis**
- Profil utilisateur en cache (TTL: 1h)
- Recommandations pré-calculées (TTL: 30min)
- Invalidation sur nouvelle interaction

---

## SLIDE 22 - NOUVEAUX ARTICLES - ARCHITECTURE CIBLE

**Ingestion et recommandation de nouveaux contenus**

**1. Pipeline d'ingestion**
```
Nouvel article → Blob Storage Landing → Azure Functions → Processing
```

**Étapes:**
- Extraction métadonnées (titre, catégorie, publisher)
- Génération embedding (Transformers/BERT)
- Stockage Cosmos DB + Blob Storage
- Indexation pour recherche

**2. Disponibilité immédiate**
- Content-Based fonctionne dès que l'embedding est calculé
- Pas besoin d'attendre des interactions
- Recommandé aux utilisateurs avec profil similaire

**3. Cold Start Articles**
- **Boost initial**: Petit boost de popularité artificiel
- **A/B Testing**: Exposition contrôlée à un % d'utilisateurs
- **Bandit Algorithm**: Exploration vs Exploitation

**4. Retraining incrémental**
- Batch quotidien: Mise à jour modèles collaboratifs
- Streaming: Mise à jour profils utilisateurs temps réel
- ML Studio: Retraining modèles complexes (hebdomadaire)

---

## SLIDE 23 - PERSPECTIVES ET AMÉLIORATIONS FUTURES

**1. Analyse Vitesse de Lecture Utilisateur**

**Objectif:** Personnaliser le calcul du temps de lecture théorique

**Approche:**
- Mesurer la vitesse de lecture individuelle de chaque utilisateur
- Calculer: mots_lus / temps_réel pour chaque article
- Créer un profil de vitesse par utilisateur
- Ajuster le plafonnement du temps selon le profil

**Bénéfices:**
- Détection plus précise des temps fantômes
- Recommandations adaptées au rythme de lecture
- Meilleure estimation de l'engagement réel

---

**2. Stratégie Publicitaire Optimisée**

**Objectif:** Maximiser les revenus tout en préservant l'expérience utilisateur

**Leviers d'optimisation:**

A. **Contenu ciblé**
   - Pub contextuelle basée sur l'article lu
   - Pub basée sur le profil utilisateur
   - Pub géo-localisée

B. **Durée d'affichage**
   - Adapter selon le temps de lecture estimé
   - Durée variable selon engagement article

C. **Moment d'apparition**
   - Début de lecture (capture attention)
   - Milieu de lecture (engagement élevé)
   - Fin de lecture (avant recommandations)

D. **Endroit d'apparition**
   - In-feed (entre paragraphes)
   - Sidebar (non intrusif)
   - Interstitiel (changement d'article)

E. **Fréquence d'apparition**
   - Limiter nombre de pubs par session
   - Éviter pub fatigue
   - Adapter selon profil utilisateur (nouveau vs fidèle)

**Impact attendu:**
- +30-50% revenus publicitaires
- Maintien de l'expérience utilisateur
- Optimisation CPM (coût pour mille impressions)

---

**3. Modèles ML/DL Plus Performants**

**Objectif:** Améliorer la qualité des recommandations

**Approches avancées:**

A. **Deep Learning pour Collaborative Filtering**
   - **Neural Collaborative Filtering (NCF)**
     - Réseau de neurones pour interactions non-linéaires
     - Meilleure capture des patterns complexes
   - **Two-Tower Model**
     - Encodeur utilisateur + Encodeur article
     - Scalable à millions d'items

B. **Embeddings Contextuels**
   - **BERT/Transformers** pour articles
     - Représentation sémantique avancée
     - Prise en compte du contexte complet
   - **Sentence Transformers**
     - Embeddings optimisés pour similarité
   - **Multilingual** pour internationalisation

C. **Séquences Temporelles**
   - **LSTM/GRU** pour modéliser séquences de lecture
     - Capture patterns temporels
     - Prédit le prochain article basé sur session
   - **Transformer-based** (GPT-style)
     - Attention mechanisms pour long contexte

D. **Reinforcement Learning**
   - **Multi-Armed Bandits**
     - Équilibre exploration/exploitation
     - Optimise découverte nouveaux contenus
   - **Contextual Bandits**
     - Prend en compte contexte utilisateur
   - **Deep Q-Learning**
     - Optimise engagement long-terme

E. **Graph Neural Networks (GNN)**
   - **User-Item Graph**
     - Capture relations complexes
     - Propagation d'information dans le graphe
   - **Knowledge Graphs**
     - Intègre connaissances externes

**Bénéfices attendus:**
- +15-25% précision des recommandations
- Meilleure personnalisation
- Découverte contenu améliorée
- Engagement utilisateur accru

---

## SLIDE 24 - ROADMAP & NEXT STEPS

**Phase 1 - MVP ✅ (ACTUEL - RÉALISÉ)**
- ✅ Système de recommandation hybride 40/30/30
- ✅ Déploiement Azure Functions (Consumption Plan)
- ✅ Application Streamlit fonctionnelle
- ✅ Code versionné sur GitHub
- ✅ Filtre 30 secondes et 9 signaux de qualité
- ✅ Détection temps fantômes
- ✅ API opérationnelle (France Central)

**Phase 2 - Alpha (3-6 mois)**
- 🔄 Passage Premium Plan EP1 (si >100k sessions/mois)
- 🔄 Cache Redis pour latence < 100ms
- 🔄 Frontend React moderne
- 🔄 Authentification utilisateurs (Azure AD)
- 🔄 Tracking interactions temps réel (Event Hubs)
- 🔄 Utilisation modèles complets (160k users)

**Phase 3 - Beta (6-12 mois)**
- 📋 Application mobile (React Native)
- 📋 Système de feedback explicite (likes/dislikes)
- 📋 Notifications push
- 📋 A/B Testing framework
- 📋 Implémentation stratégie publicitaire optimisée
- 📋 Analyse vitesse de lecture utilisateur

**Phase 4 - Production (12-24 mois)**
- 📋 Scale à 1M+ utilisateurs
- 📋 Pipeline ML automatisé (retraining continu)
- 📋 Modèles Deep Learning (NCF, Transformers)
- 📋 Multilingue & international
- 📋 Recommandations contextuelles (temps, lieu, device)
- 📋 Graph Neural Networks

---

## SLIDE 25 - CONCLUSION

**Accomplissements du MVP**

✅ **Système de recommandation opérationnel de haute qualité**
- Approche hybride 40/30/30 (Content/Collaborative/Temporal)
- Gestion complète du Cold Start
- Filtre de diversité des catégories
- **Innovation:** Détection temps fantômes (filtre 30s, 9 signaux)

✅ **Architecture Azure serverless scalable**
- Azure Functions Consumption Plan (~10€/mois)
- Déploiement automatisé
- API opérationnelle en production
- Coût minimal, performance optimale

✅ **Application utilisable en production**
- Interface Streamlit intuitive
- Mode local et mode Azure
- Export des résultats
- Paramètres configurables

✅ **Code et documentation professionnels**
- Versionné sur GitHub
- Scripts de déploiement bout-en-bout
- Documentation exhaustive
- Tests inclus

**Vision claire pour le scale-up**
- Architecture cible détaillée (slide 20)
- Roadmap en 4 phases (slide 24)
- Perspectives d'améliorations (slide 23)
- Prêt pour la production

**Impact business attendu:**
- +83% engagement utilisateur
- +8,700€/an de revenus publicitaires (avec seulement 100k sessions)
- ROI positif dès la première année

---

## SLIDE 26 - QUESTIONS & DÉMO

**Démonstration en direct**

Nous pouvons maintenant démontrer:
- L'application Streamlit en action
- Génération de recommandations pour différents utilisateurs
- Ajustement des paramètres (poids 40/30/30, diversité)
- Appel à l'API Azure Functions
- Visualisation des résultats avec métadonnées complètes

**Questions ?**

**Liens utiles**
- 🔗 GitHub: https://github.com/GuillaumeC96/P10_reco_my_content
- 🌐 API Azure: https://func-mycontent-reco-1269.azurewebsites.net/api/recommend
- 📧 Contact: guillaumecassezwork@gmail.com
- 🏢 My Content - Encourager la lecture par des recommandations intelligentes

---

**FIN DE LA PRÉSENTATION**

*Merci de votre attention !*

**Projet:** My Content - Système de Recommandation d'Articles
**Étudiant:** Guillaume Cassez - CTO & Co-fondateur
**Formation:** Data Scientist - OpenClassrooms
**Date:** Janvier 2026
