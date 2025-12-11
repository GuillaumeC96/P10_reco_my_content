# My Content - Système de Recommandation d'Articles
## Contenu de la Présentation (15-25 slides)

---

## SLIDE 1 - PAGE DE TITRE
**My Content - Système de Recommandation d'Articles**

Encourager la lecture par des recommandations pertinentes

Guillaume Cassez - CTO & Co-fondateur
Décembre 2024

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

## SLIDE 5 - DESCRIPTION FONCTIONNELLE DE L'APPLICATION

**Architecture MVP - 3 composants principaux**

1. **Application Streamlit** (Interface utilisateur)
   - Sélection d'un utilisateur
   - Configuration des paramètres
   - Affichage des 5 articles recommandés
   - Export des résultats

2. **AWS Lambda Function** (Serverless compute)
   - Traitement des requêtes HTTP
   - Génération des recommandations
   - API accessible via Function URL

3. **AWS S3** (Stockage)
   - Modèles de Machine Learning
   - Embeddings des articles
   - Métadonnées

---

## SLIDE 6 - DÉMONSTRATION APPLICATION

**Interface Streamlit**

Fonctionnalités démontrées:
- Saisie d'un user_id
- Choix du nombre de recommandations (1-50)
- Réglage du paramètre alpha (collaborative vs content-based)
- Activation/désactivation du filtre de diversité
- Affichage des résultats avec métadonnées complètes
- Téléchargement CSV

**Deux modes disponibles**
- Mode Local: Calcul en local sur la machine
- Mode Lambda: Appel API AWS Lambda (serverless)

---

## SLIDE 7 - APPROCHES DE RECOMMANDATION ANALYSÉES

**3 approches principales étudiées**

1. **Filtrage Collaboratif (Collaborative Filtering)**
   - Basé sur les similarités entre utilisateurs
   - "Les utilisateurs similaires aiment des contenus similaires"

2. **Filtrage Basé sur le Contenu (Content-Based)**
   - Basé sur les caractéristiques des articles
   - "Recommander des articles similaires à ceux déjà lus"

3. **Approche Hybride** ⭐ (Solution retenue)
   - Combine les deux approches précédentes
   - Tire parti des forces de chaque méthode

---

## SLIDE 8 - FILTRAGE COLLABORATIF

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

## SLIDE 9 - FILTRAGE BASÉ SUR LE CONTENU

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

## SLIDE 10 - APPROCHE HYBRIDE (SOLUTION RETENUE)

**Formule de scoring**

```
Score_final = α × Score_collaborative + (1-α) × Score_content
```

**Paramètre α (poids du collaboratif)**
- α = 0.6 par défaut (60% collaborative, 40% content)
- Ajustable selon les besoins

**Pourquoi l'hybride ?**
- ✅ Combine les forces des deux approches
- ✅ Atténue les faiblesses respectives
- ✅ Meilleure performance globale
- ✅ Flexibilité via le paramètre alpha

**Composants additionnels**
- Filtre de diversité des catégories
- Gestion du Cold Start (fallback sur popularité)
- Exclusion des articles déjà lus

---

## SLIDE 11 - COMPARAISON DES APPROCHES

| Critère | Collaborative | Content-Based | **Hybride** |
|---------|--------------|---------------|-------------|
| Nouveaux utilisateurs | ❌ Faible | ✅ Bon | ✅ **Bon** |
| Nouveaux articles | ⚠️ Moyen | ✅ Excellent | ✅ **Excellent** |
| Diversité | ✅ Bonne | ❌ Faible | ✅ **Bonne** |
| Serendipity | ✅ Excellente | ❌ Faible | ✅ **Bonne** |
| Scalabilité | ❌ Difficile | ✅ Facile | ⚠️ **Moyen** |
| Sparsité | ❌ Problème | ✅ Robuste | ✅ **Robuste** |
| **Performance** | ⚠️ Moyenne | ⚠️ Moyenne | ✅ **Meilleure** |

**Verdict:** L'approche hybride offre le meilleur compromis pour un MVP évolutif

---

## SLIDE 12 - ARCHITECTURE TECHNIQUE MVP

**Schéma de l'architecture retenue**

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
│  AWS LAMBDA     │ ← Serverless Compute
│   FUNCTION      │   - Python 3.9, 1024 MB
└────────┬────────┘   - Timeout 30s
         │
         │ Download (Cold Start)
         ▼
┌─────────────────┐
│    AWS S3       │ ← Stockage Cloud
│    BUCKET       │   - Modèles ML (~350 MB)
└─────────────────┘   - Embeddings, matrices
```

**Temps de réponse**
- Cold Start: 3-5 secondes
- Warm: 1-2 secondes

---

## SLIDE 13 - COMPOSANTS TECHNIQUES DÉTAILLÉS

**1. Application Streamlit**
- Framework: Streamlit 1.28+
- Langage: Python 3.9
- Port: 8501
- Fichier: `app/streamlit_app.py`

**2. Lambda Function**
- Runtime: Python 3.9
- Memory: 1024 MB
- Timeout: 30s
- Handler: `lambda_function.lambda_handler`
- Trigger: Function URL (HTTP public)

**3. Stockage S3**
- Bucket: `my-content-reco-bucket`
- Taille: ~350 MB (modèles + embeddings)
- Accès: IAM Role (Lambda → S3)

---

## SLIDE 14 - SYSTÈME DE RECOMMANDATION - ALGORITHME

**Pipeline de recommandation (6 étapes)**

1. **Vérification utilisateur**
   - Utilisateur connu → Collaborative + Content-Based
   - Nouvel utilisateur → Popularité (Cold Start)

2. **Collaborative Filtering**
   - Calcul similarité cosinus entre utilisateurs
   - Sélection top-50 utilisateurs similaires
   - Agrégation articles pondérée par similarité

3. **Content-Based Filtering**
   - Calcul profil utilisateur (embedding moyen)
   - Similarité cosinus avec tous les articles
   - Filtrage articles déjà lus

4. **Scoring Hybride**
   - Combinaison α × collaborative + (1-α) × content
   - Normalisation des scores

5. **Filtre de diversité** (optionnel)
   - Garantit variété des catégories
   - Évite sur-représentation d'une catégorie

6. **Retour Top-N**
   - Sélection des N meilleurs articles
   - Ajout métadonnées (catégorie, publisher, etc.)

---

## SLIDE 15 - GESTION DU COLD START

**Problématique**
- Nouveaux utilisateurs: pas d'historique
- Nouveaux articles: pas d'interactions

**Solutions implémentées**

1. **Nouveaux utilisateurs**
   - Fallback sur recommandations par popularité
   - Calcul basé sur nombre total d'interactions
   - Permet de démarrer immédiatement

2. **Nouveaux articles**
   - Content-Based fonctionne immédiatement
   - Utilise l'embedding de l'article
   - Pas besoin d'interactions

3. **Utilisateurs avec peu d'historique**
   - Hybride avec alpha ajusté
   - Plus de poids sur content-based
   - Transition progressive vers collaborative

---

## SLIDE 16 - DÉPLOIEMENT SERVERLESS

**Pourquoi Serverless (AWS Lambda) ?**

**Avantages techniques** ✅
- ✅ Pas de serveur à gérer
- ✅ Auto-scaling automatique (0 → N instances)
- ✅ Paiement à l'usage (pas de coût fixe)
- ✅ Haute disponibilité native

**Avantages business** 💰
- Coût minimal pour un MVP
- Free tier: 1M requêtes/mois gratuites
- Adapté à charge variable
- Time-to-market rapide

**Déploiement automatisé**
- Script `deploy.sh` fourni
- Création IAM Role automatique
- Package des dépendances
- Configuration Function URL

---

## SLIDE 17 - SCRIPTS DE DÉPLOIEMENT

**Pipeline de déploiement end-to-end**

**1. Préparation des données**
```bash
python3 data_preparation/data_preprocessing.py
```
- Génère matrices user-item (sparse)
- Filtre embeddings actifs
- Calcule popularités
- Crée mappings user/article

**2. Upload vers S3**
```bash
python3 data_preparation/upload_to_s3.py
```
- Upload modèles vers S3
- Vérification intégrité

**3. Déploiement Lambda**
```bash
cd lambda && ./deploy.sh
```
- Package dépendances (NumPy, Scikit-learn)
- Création/mise à jour Lambda Function
- Configuration Function URL

**Tout le code est versionné sur GitHub** 🔗

---

## SLIDE 18 - MÉTRIQUES & PERFORMANCE

**Temps de réponse**
- Cold Start Lambda: 3-5 secondes (première invocation)
- Warm Lambda: 1-2 secondes (invocations suivantes)
- Mode Local: 0.5-1 seconde

**Consommation ressources**
- Lambda Memory: 1024 MB (optimal)
- S3 Storage: ~350 MB
- Package Lambda: ~150 MB (avec dépendances)

**Scalabilité actuelle**
- Utilisateurs actifs: ~38 000 (après filtrage ≥5 interactions)
- Articles actifs: ~312 000
- Sparsité matrice: >99%
- Format sparse (CSR) pour optimisation mémoire

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
- Monitoring & observabilité

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
         │ Lambda  │     │  Cache   │    │  Auth    │
         │ Reco    │     │  Redis   │    │ Cognito  │
         └────┬────┘     └────┬─────┘    └──────────┘
              │               │
              └───────┬───────┘
                      ▼
         ┌────────────────────────┐
         │  Data Storage Layer    │
         │  - DynamoDB (Users)    │
         │  - S3 (Models)         │
         │  - RDS (Metadata)      │
         └───────────┬────────────┘
                     │
                     ▼
         ┌────────────────────────┐
         │  ML Pipeline           │
         │  - Kinesis (Streaming) │
         │  - SageMaker (Training)│
         └────────────────────────┘
```

---

## SLIDE 21 - NOUVEAUX UTILISATEURS - ARCHITECTURE CIBLE

**Gestion en temps réel des nouveaux utilisateurs**

**1. Onboarding**
```
Inscription → Cognito → User Profile créé dans DynamoDB
```
- Collecte préférences initiales (catégories favorites)
- Optionnel: Sélection de topics d'intérêt

**2. Premières recommandations**
- **Phase 1** (0 interaction): Recommandations populaires + catégories choisies
- **Phase 2** (1-5 interactions): Hybride avec fort poids content-based
- **Phase 3** (5+ interactions): Hybride équilibré avec collaborative

**3. Streaming des interactions**
```
Clic article → Kinesis Stream → Lambda → DynamoDB + S3
```
- Capture en temps réel des clics
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
Nouvel article → S3 Landing → Lambda Trigger → Processing
```

**Étapes:**
- Extraction métadonnées (titre, catégorie, publisher)
- Génération embedding (BERT/Sentence Transformers)
- Stockage DynamoDB + S3
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
- Streaming: Mise à jour profils utilisateurs
- SageMaker: Retraining modèles complexes (hebdomadaire)

---

## SLIDE 23 - AMÉLIORATION ML - ARCHITECTURE CIBLE

**Évolutions des algorithmes de recommandation**

**1. Deep Learning**
- **Neural Collaborative Filtering (NCF)**
  - Réseau de neurones pour apprendre interactions complexes
  - Meilleure capture des patterns non-linéaires

- **Two-Tower Model**
  - Encodeur utilisateur + Encodeur article
  - Scalable à millions d'items

**2. Embeddings Contextuels**
- **BERT/Transformers** pour représentation sémantique
- Prise en compte du contexte (titre + contenu)
- Multilingual pour internationalisation

**3. Séquences Temporelles**
- **LSTM/GRU** pour modéliser séquences de lecture
- Prédit le prochain article basé sur session
- Capture les patterns temporels

**4. Multi-Armed Bandits**
- **Exploration vs Exploitation**
- Équilibre entre contenus connus et nouveaux
- Personnalisation dynamique de α

---

## SLIDE 24 - MONITORING & AMÉLIORATIONS CONTINUES

**Observabilité de l'architecture cible**

**1. Métriques Business**
- Click-Through Rate (CTR)
- Dwell Time (temps passé sur article)
- Taux de retour utilisateurs
- Diversité des recommandations consommées

**2. Métriques Techniques**
- Latence P50, P95, P99
- Taux d'erreur 5XX
- Cache Hit Ratio
- Coût par recommandation

**3. Métriques ML**
- Precision@K / Recall@K
- NDCG (Normalized Discounted Cumulative Gain)
- Coverage (% articles recommandés)
- Novelty & Serendipity

**4. Outils**
- CloudWatch Dashboards
- X-Ray (tracing distribué)
- Grafana pour visualisations
- Alertes automatiques

---

## SLIDE 25 - ROADMAP & NEXT STEPS

**Phase 1 - MVP ✅ (ACTUEL)**
- ✅ Système de recommandation hybride
- ✅ Déploiement serverless (Lambda)
- ✅ Application Streamlit fonctionnelle
- ✅ Code versionné sur GitHub

**Phase 2 - Alpha (3 mois)**
- 🔄 Déploiement API Gateway
- 🔄 Cache Redis pour latence < 100ms
- 🔄 Frontend React moderne
- 🔄 Authentification utilisateurs (Cognito)
- 🔄 Tracking interactions temps réel (Kinesis)

**Phase 3 - Beta (6 mois)**
- 📋 Application mobile (React Native)
- 📋 Système de feedback explicite (likes/dislikes)
- 📋 Notifications push
- 📋 A/B Testing framework
- 📋 Modèles Deep Learning (NCF)

**Phase 4 - Production (12 mois)**
- 📋 Scale à 1M+ utilisateurs
- 📋 Pipeline ML automatisé
- 📋 Multilingue & international
- 📋 Recommandations contextuelles (temps, lieu, device)

---

## SLIDE 26 - CONCLUSION

**Accomplissements du MVP**

✅ **Système de recommandation opérationnel**
- Approche hybride performante
- Gestion du Cold Start
- Filtre de diversité

✅ **Architecture serverless scalable**
- AWS Lambda + S3
- Déploiement automatisé
- Coût minimal

✅ **Application utilisable**
- Interface Streamlit intuitive
- Mode local et distant
- Export des résultats

✅ **Code industrialisable**
- Versionné sur GitHub
- Scripts de déploiement
- Documentation complète

**Vision claire pour le scale-up**
- Architecture cible définie
- Roadmap en phases
- Prêt pour la production

---

## SLIDE 27 - QUESTIONS & DÉMO

**Démo en direct**

Nous pouvons maintenant démontrer:
- L'application Streamlit en action
- Génération de recommandations pour différents utilisateurs
- Ajustement des paramètres (alpha, diversité)
- Appel à la Lambda Function AWS

**Questions ?**

**Liens utiles**
- 🔗 GitHub: https://github.com/GuillaumeC96/P10_reco_my_content
- 📧 Contact: guillaumecassezwork@gmail.com
- 🏢 My Content - Encourager la lecture

---

**FIN DE LA PRÉSENTATION**

*Merci de votre attention !*
