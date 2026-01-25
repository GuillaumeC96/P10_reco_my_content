# Cahier des charges - Système de recommandation My Content

## 1. Contexte du projet

### 1.1 Présentation
**My Content** est une start-up dont la mission est d'encourager la lecture en recommandant des contenus pertinents aux utilisateurs. Le projet consiste à développer un MVP (Minimum Viable Product) d'application de recommandation d'articles et de livres.

### 1.2 Objectif
Construire une première version fonctionnelle d'un système de recommandation capable de suggérer 5 articles pertinents à un utilisateur.

### 1.3 Équipe
- **Vous** : CTO et cofondateur
- **Samia** : CEO et cofondatrice
- **Julien** : Développeur web freelance (conseil architecture)

### 1.4 Contraintes techniques
- **Infrastructure cloud** : Azure (Microsoft Azure)
- **GPU** : non disponible (déjà utilisé par un autre programme)
- **Compute** : CPU uniquement pour le traitement

---

## 2. Données disponibles

### 2.1 Source des données
Dataset Globo.com : **news-portal-user-interactions-by-globocom**

### 2.2 Composition du dataset
- **articles_metadata.csv** : 364 047 articles
  - `article_id` : identifiant unique de l'article
  - `category_id` : catégorie de l'article
  - `created_at_ts` : timestamp de création
  - `publisher_id` : identifiant de l'éditeur
  - `words_count` : nombre de mots

- **articles_embeddings.pickle** : 364 MB
  - Embeddings pré-calculés des articles
  - Représentations vectorielles des contenus

- **clicks/** : 387 fichiers CSV horaires
  - `user_id` : identifiant de l'utilisateur
  - `session_id` : identifiant de session
  - `session_start` : début de session (timestamp)
  - `session_size` : nombre de clics dans la session
  - `click_article_id` : article cliqué
  - `click_timestamp` : moment du clic
  - `click_environment` : environnement (desktop/mobile/etc.)
  - `click_deviceGroup` : type d'appareil
  - `click_os` : système d'exploitation
  - `click_country` : pays
  - `click_region` : région
  - `click_referrer_type` : type de référent

---

## 3. Fonctionnalités MVP

### 3.1 User Story principale
```
En tant qu'utilisateur de l'application,
Je veux recevoir une sélection de cinq articles pertinents,
Afin de découvrir du contenu qui correspond à mes intérêts.
```

### 3.2 Fonctionnalités de l'application

#### 3.2.1 Fonctionnalités principales
1. **Sélection d'un utilisateur**
   - Input numérique pour sélectionner un user_id (0 à 1 000 000)
   - Détection automatique du changement d'utilisateur

2. **Génération de recommandations**
   - Appel à l'Azure Function pour obtenir 5 recommandations
   - Affichage des 5 articles recommandés avec métadonnées complètes
   - Mesure et affichage de la latence API en temps réel

3. **Profil utilisateur**
   - Statistiques de lecture basées sur le temps passé
   - Métriques : articles lus, temps total, temps moyen/article, catégories lues
   - Camemberts comparatifs : catégories favorites vs recommandations

#### 3.2.2 Fonctionnalités avancées
4. **Analyse de cohérence**
   - Comparaison profil utilisateur vs recommandations
   - Taux de cohérence avec les catégories favorites
   - Score de nouveauté (découverte de nouvelles catégories)

5. **Graphe de réseau global**
   - Visualisation interactive des relations entre catégories
   - Analyse basée sur tous les utilisateurs (322k+)
   - Filtrage intelligent des connexions significatives
   - Identification des clusters thématiques

6. **Paramètres optimisés**
   - Architecture hybride 39/36/25 (Content/Collaborative/Temporal)
   - Filtre de diversité optionnel (checkbox)
   - Nombre de recommandations ajustable (3-20)

---

## 4. Architecture technique

### 4.1 Architecture retenue : Serverless avec Azure Functions

#### Architecture déployée
```
[Application Streamlit] → [Azure Functions HTTP Trigger] → [Système de recommandation]
       (Local/Cloud)              (func-mycontent-reco-1269)         (Modèles chargés)
                                          ↓
                                 [Azure Blob Storage]
                            (embeddings, modèles, data)
```

**Déploiement actuel** :
- **Azure Function** : func-mycontent-reco-1269.azurewebsites.net
- **Region** : France Central
- **Plan** : Consumption (~10€/mois)
- **Resource Group** : rg-mycontent-prod
- **Endpoint** : https://func-mycontent-reco-1269.azurewebsites.net/api/recommend

### 4.2 Composants techniques

#### 4.2.1 Azure Functions
- **Langage** : Python 3.10+ (CPU uniquement, pas de GPU)
- **Trigger** : HTTP Trigger (POST /api/recommend)
- **Input** : JSON avec user_id, n, weights, use_diversity
- **Output** : JSON avec liste d'articles et métadonnées
- **Timeout** : 30 secondes
- **Memory** : 512-1024 MB
- **Latence mesurée** : 50-200ms (warm), 1-3s (cold start)

#### 4.2.2 Azure Blob Storage
- **Container structure** :
  - `/models/` : modèles lite (10k users, 86 MB) et complets (160k users)
  - `/data/` : métadonnées articles, matrices de similarité
  - `/cache/` : profils utilisateurs pré-calculés
- **Configuration** : Managed Identity pour accès Functions → Blob

#### 4.2.3 Application Streamlit Enhanced
- **Type** : Interface web interactive multipage
- **Fonctionnalités Page 1 (Recommandations)** :
  - Input user_id avec détection automatique de changement
  - Profil utilisateur avec métriques de temps de lecture
  - Camemberts comparatifs (profil vs recommandations)
  - Analyse de cohérence et score de nouveauté
  - Affichage latence API en temps réel
  - Export CSV des résultats

- **Fonctionnalités Page 2 (Graphe de Réseau)** :
  - Visualisation interactive des relations catégories
  - Analyse globale sur 322k+ utilisateurs
  - Filtrage intelligent (percentile 60)
  - Identification clusters thématiques
  - Debug info détaillée

- **Communication** : Requêtes HTTP POST vers Azure Functions API

---

## 5. Système de recommandation

### 5.1 Approche retenue : Système Hybride

#### 5.1.1 Justification
D'après les recherches récentes (2025), les systèmes hybrides combinent les avantages de :
- **Collaborative Filtering** : exploite les patterns d'utilisateurs similaires
- **Content-Based Filtering** : utilise les embeddings pour similarité de contenu
- **Résolution du Cold Start** : permet de gérer nouveaux utilisateurs/articles

#### 5.1.2 Composantes du système

**A. Filtrage collaboratif (User-based)**
- Calcul de similarité entre utilisateurs basé sur leur historique de clics
- Identification des k utilisateurs les plus similaires
- Agrégation de leurs préférences

**B. Filtrage par contenu (Content-based)**
- Utilisation des embeddings pré-calculés
- Réduction de dimension via PCA (si nécessaire pour limites Azure)
- Calcul de similarité cosinus entre articles

**C. Approche hybride (Architecture 39/36/25 - Optimisée par Optuna)**
- **39% Content-Based** : Similarité de contenu via embeddings
- **36% Collaborative** : Patterns d'utilisateurs similaires
- **25% Temporal/Trending** : Fraîcheur et popularité temporelle
- Score final = 0.39 × score_content + 0.36 × score_collab + 0.25 × score_trend
- Poids optimisés par Optuna TPE (30 trials, objectif: temps de lecture)

### 5.2 Algorithme de recommandation

```python
def recommend_articles(user_id, n_recommendations=5):
    """
    1. Récupérer l'historique de l'utilisateur
    2. Si utilisateur connu (cold start = False):
       a. Trouver k utilisateurs similaires (collaborative)
       b. Récupérer articles lus par l'utilisateur
       c. Calculer similarités content-based
       d. Combiner les scores
    3. Si nouvel utilisateur (cold start = True):
       a. Recommander articles populaires (+ diversité)
       b. Utiliser content-based sur catégories populaires
    4. Filtrer articles déjà lus
    5. Retourner top 5
    """
```

### 5.3 Métriques d'évaluation
- **Precision@5** : proportion d'articles pertinents dans les 5 recommandations
- **Recall@5** : proportion d'articles pertinents retrouvés
- **Coverage** : diversité des articles recommandés
- **Diversity** : variété des catégories dans les recommandations

### 5.4 Amélirations techniques implémentées

#### 5.4.1 Détection des temps fantômes
**Problématique** : Onglets ouverts, multiples onglets simultanés créent des durées artificielles

**Solutions implémentées** :
1. **Filtre 30 secondes** : Seuil critique pour affichage 2ème publicité
2. **Détection clics accidentels** : Temps < 10s = poids 0
3. **Gestion changements de session** : Détection ruptures temporelles
4. **Plafonnement temps de lecture** : Maximum basé sur words_count

#### 5.4.2 9 Signaux de qualité d'interaction
Pondération des interactions basée sur :
1. Temps passé ajusté (≥ 30s)
2. Nombre de clics
3. Qualité de session
4. Type de device
5. Environnement
6. Type de referrer
7. Système d'exploitation
8. Pays
9. Région

#### 5.4.3 Temporal decay
- Favorise contenu récent et frais
- Décroissance exponentielle basée sur `created_at_ts`
- Boost pour articles < 7 jours

---

## 6. Gestion du Cold Start Problem

### 6.1 Définition
**Cold Start User** : nouvel utilisateur sans historique de clics
**Cold Start Item** : nouvel article sans interactions

### 6.2 Stratégies implémentées

#### 6.2.1 Pour nouveaux utilisateurs
1. **Approche popularity-based** : recommander articles populaires récents
2. **Diversification** : assurer variété des catégories
3. **Contextual information** : exploiter device, région, timestamp si disponible
4. **Progressive learning** : collecter feedback pour affiner rapidement

#### 6.2.2 Pour nouveaux articles
1. **Content-based pure** : utiliser embeddings et métadonnées
2. **Category-based** : comparer aux articles similaires de même catégorie
3. **Publisher-based** : exploiter l'historique de l'éditeur

---

## 7. Architecture cible (évolution du MVP)

### 7.1 Scalabilité

#### 7.1.1 Gestion des nouveaux utilisateurs
```
[User Registration] → [Profile Collection (optionnel)]
                            ↓
                [Initial Recommendations (Popular + Diverse)]
                            ↓
                [Click Tracking] → [Progressive Profile Building]
                            ↓
                [Hybrid Recommendations (Collaborative + Content)]
```

#### 7.1.2 Gestion des nouveaux articles
```
[New Article] → [Content Extraction] → [Embedding Generation]
                            ↓
                [Metadata Indexing] → [Content-Based Pool]
                            ↓
                [Progressive Popularity Tracking] → [Collaborative Pool]
```

### 7.2 Améliorations futures

#### 7.2.1 Infrastructure
- **Real-time recommendations** : streaming des interactions (Azure Event Hubs)
- **Model retraining** : pipeline automatisé (Azure Azure ML ou Azure Batch)
- **A/B Testing** : framework d'expérimentation
- **Monitoring** : Azure Azure Monitor pour performance et logs
- **API Management** : Azure Azure API Management pour production
- **Cache** : Azure Azure Cache (Redis) pour réponses rapides

#### 7.2.2 Machine Learning avancé
- **Deep Learning** : Neural Collaborative Filtering (NCF)
- **Embeddings contextuels** : BERT pour améliorer représentations
- **Sequential patterns** : RNN/LSTM pour capturer séquences de lecture
- **LLMs** : extraction de features sémantiques avancées

#### 7.2.3 Fonctionnalités métier
- **Feedback explicite** : système de rating (like/dislike)
- **Preferences utilisateur** : sélection de catégories favorites
- **Temporal patterns** : recommandations selon heure/jour
- **Social features** : partage, commentaires, following

---

## 8. Livrables

### 8.1 Code
1. **Azure Functions Function**
   - `lambda_function.py` : handler principal (point d'entrée)
   - `recommendation_engine.py` : logique de recommandation
   - `utils.py` : fonctions utilitaires
   - `requirements.txt` : dépendances Python
   - `config.py` : configuration (container Azure Blob Storage, paramètres)

2. **Application locale**
   - Interface Streamlit
   - Script de test de la Azure Function

3. **Scripts de préparation**
   - `data_preprocessing.py` : nettoyage et préparation données
   - `embeddings_reduction.py` : PCA sur embeddings (CPU uniquement)
   - `model_training.py` : calcul matrices de similarité
   - `upload_to_s3.py` : upload des modèles vers Azure Blob Storage

### 8.2 Documentation
1. **README.md** : instructions de déploiement et utilisation
2. **architecture_technique.md** : détail architecture MVP
3. **architecture_cible.md** : vision scalabilité et évolutions
4. **user_guide.md** : guide utilisateur application
5. **azure_setup.md** : guide de configuration Azure

### 8.3 Repository GitHub
```
reco-my-content/
├── lambda/
│   ├── lambda_function.py
│   ├── recommendation_engine.py
│   ├── utils.py
│   ├── config.py
│   ├── requirements.txt
│   └── deploy.sh
├── app/
│   ├── streamlit_app.py
│   └── requirements.txt
├── data_preparation/
│   ├── data_preprocessing.py
│   ├── embeddings_reduction.py
│   ├── model_training.py
│   └── upload_to_s3.py
├── models/
│   └── (modèles et embeddings réduits - local avant upload Azure Blob Storage)
├── docs/
│   ├── architecture_technique.md
│   ├── architecture_cible.md
│   └── azure_setup.md
├── tests/
│   └── test_recommendations.py
└── README.md
```

---

## 9. Planning de développement

### Phase 1 : Préparation des données
- Exploration et analyse du dataset
- Nettoyage des données de clics
- Réduction de dimension des embeddings (PCA)
- Création des matrices user-item

### Phase 2 : Développement système de recommandation
- Implémentation collaborative filtering
- Implémentation content-based filtering
- Développement système hybride
- Tests et validation

### Phase 3 : Développement Azure Functions
- Configuration Azure account et ressources (Azure Functions, Azure Blob Storage, IAM)
- Développement de la Azure Function
- Upload des modèles vers Azure Blob Storage
- Configuration Azure Function URL
- Tests et déploiement

### Phase 4 : Application locale
- Développement interface Streamlit
- Intégration avec Azure Functions Function URL
- Tests end-to-end

### Phase 5 : Documentation et livraison
- Rédaction documentation technique
- Documentation architecture cible
- Préparation présentation pour Samia
- Push final sur GitHub

---

## 10. Technologies et outils

### 10.1 Backend
- **Python 3.9+** (CPU uniquement)
- **Azure Functions** (serverless compute)
- **Azure Blob Storage** (stockage objets)
- **azure-storage-blob** : SDK Azure pour Python

### 10.2 Data Science
- **pandas** : manipulation de données
- **numpy** : calculs numériques (CPU uniquement)
- **scikit-learn** : PCA, métriques, similarités (CPU)
- **scipy** : calculs de similarité avancés
- **pickle** : sérialisation modèles

### 10.3 Frontend
- **Streamlit** : interface web simple (recommandé)
- **requests** : appels HTTP vers Azure Functions

### 10.4 DevOps
- **Git/GitHub** : versioning
- **Azure CLI** : déploiement et gestion
- **pytest** : tests unitaires
- **zip** : packaging Azure Functions deployment

---

## 11. Contraintes et limitations

### 11.1 Contraintes techniques
- **Pas de GPU** : GPU déjà utilisé par un autre programme → CPU uniquement
- **Taille des embeddings** : 364 MB → réduction nécessaire (PCA sur CPU)
- **Azure Free Tier** : limitations de stockage Azure Blob Storage et invocations Azure Functions
- **Azure Functions Limits** :
  - Package size max 250 MB (unzipped)
  - Timeout max 15 minutes
  - Memory max 10 GB
- **Cold start Azure Functions** : première invocation peut être lente (warmup)
- **Cold start utilisateur** : performance limitée pour nouveaux utilisateurs

### 11.2 Contraintes fonctionnelles
- **MVP** : fonctionnalités minimales uniquement
- **Données statiques** : pas de mise à jour temps réel
- **Interface simple** : pas de design élaboré

### 11.3 Limitations du dataset
- **Données historiques** : pas de nouvelles interactions
- **Langue** : articles en portugais (Globo.com)
- **Domaine spécifique** : actualités uniquement

---

## 12. Critères de succès

### 12.1 Critères techniques
- ✅ Azure Functions déployée et fonctionnelle
- ✅ Temps de réponse < 5 secondes (après warmup)
- ✅ Application locale opérationnelle
- ✅ 5 recommandations générées pour tout utilisateur
- ✅ Traitement CPU uniquement (sans GPU)

### 12.2 Critères qualité
- ✅ Recommandations diversifiées (plusieurs catégories)
- ✅ Pertinence des suggestions (basée sur historique)
- ✅ Gestion du cold start fonctionnelle
- ✅ Code propre et documenté

### 12.3 Critères métier
- ✅ Documentation complète pour présentation à Samia
- ✅ Architecture cible claire et réaliste
- ✅ Repository GitHub bien structuré
- ✅ MVP démontrable en conditions réelles

---

## 13. Références

### 13.1 Recherches académiques
- [Personalized News Recommendation: Methods and Challenges](https://arxiv.org/pdf/2106.08934)
- [A Survey of Personalized News Recommendation](https://link.springer.com/article/10.1007/s41019-023-00228-5)
- [Embedding in Recommender Systems: A Survey](https://arxiv.org/pdf/2310.18608)

### 13.2 Solutions au Cold Start
- [Cold Start Problem in Recommender Systems (FreeCodeCamp)](https://www.freecodecamp.org/news/cold-start-problem-in-recommender-systems/)
- [User Cold Start Problem: A Systematic Review (IEEE)](https://ieeexplore.ieee.org/document/10339320/)
- [Addressing Cold Start with GANs](https://link.springer.com/chapter/10.1007/978-981-96-6034-6_10)

### 13.3 Systèmes hybrides et embeddings
- [A Deep Learning Based Hybrid Recommendation Model](https://www.nature.com/articles/s41598-024-79011-z)
- [Introduction to Embedding-Based Recommender Systems](https://towardsdatascience.com/introduction-to-embedding-based-recommender-systems-956faceb1919/)
- [Improving Recommendation Systems in the Age of LLMs](https://eugeneyan.com/writing/recsys-llm/)

### 13.4 Implémentations GitHub
- [News Recommender - User Communities](https://github.com/huangy22/NewsRecommender)
- [News Articles Recommendation - Hybrid Filtering](https://github.com/archd3sai/News-Articles-Recommendation)

---

## 14. Glossaire

- **MVP** : Minimum Viable Product - version minimale fonctionnelle
- **Cold Start** : problème de recommandation pour utilisateurs/articles sans historique
- **Embedding** : représentation vectorielle dense d'un élément (article, utilisateur)
- **PCA** : Principal Component Analysis - réduction de dimensionnalité
- **Serverless** : architecture sans gestion de serveurs (scaling automatique)
- **Collaborative Filtering** : recommandation basée sur utilisateurs similaires
- **Content-Based Filtering** : recommandation basée sur similarité de contenu
- **Hybrid System** : système combinant plusieurs approches de recommandation
- **Azure Functions** : service serverless de Microsoft Azure
- **Blob Storage** : stockage d'objets dans le cloud Azure
