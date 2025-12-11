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
- **Infrastructure cloud** : AWS (Amazon Web Services)
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
1. **Affichage de la liste des utilisateurs**
   - Interface listant les user_id disponibles dans le dataset

2. **Sélection d'un utilisateur**
   - Possibilité de sélectionner un user_id spécifique

3. **Génération de recommandations**
   - Appel à l'Azure Function pour obtenir 5 recommandations
   - Affichage des 5 articles recommandés avec leurs métadonnées

---

## 4. Architecture technique

### 4.1 Architecture retenue : Serverless avec AWS Lambda

#### Option 1 : Architecture avec API Gateway
```
[Application locale] → [API Gateway] → [AWS Lambda] → [Système de recommandation]
                                           ↓
                                      [AWS S3]
                              (embeddings, modèles, data)
```

#### Option 2 : Architecture sans API Gateway (recommandée pour MVP)
```
[Application locale] → [AWS Lambda (Function URL)] → [Système de recommandation]
                              ↓
                        [AWS S3 Integration]
                   (embeddings, modèles, data)
```

**Choix pour le MVP** : Option 2 (plus simple, moins de couches, Lambda Function URL direct)

### 4.2 Composants techniques

#### 4.2.1 AWS Lambda
- **Langage** : Python 3.9+ (CPU uniquement, pas de GPU)
- **Trigger** : Lambda Function URL (HTTP)
- **Input** : user_id via requête HTTP
- **Output** : JSON avec liste de 5 article_id et scores
- **Timeout** : 30 secondes (ajustable si nécessaire)
- **Memory** : 512-1024 MB (selon taille embeddings réduits)

#### 4.2.2 AWS S3 (Simple Storage Service)
- **Bucket structure** :
  - `/models/` : embeddings réduits (PCA), matrices de similarité
  - `/data/` : métadonnées articles, historiques clics agrégés
  - `/cache/` : résultats précalculés (optionnel)
- **Configuration** : IAM role pour accès Lambda → S3

#### 4.2.3 Application locale
- **Type** : Interface web simple (Streamlit recommandé)
- **Fonctionnalités** :
  - Liste déroulante ou recherche user_id
  - Bouton "Obtenir recommandations"
  - Affichage résultats (article_id, category, publisher, words_count)
- **Communication** : Requêtes HTTP vers Lambda Function URL

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

**C. Approche hybride**
- Pondération des deux approches (ex: 60% collaborative + 40% content-based)
- Score final = α × score_collaborative + (1-α) × score_content
- Valeur α ajustable selon performance

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
- **Real-time recommendations** : streaming des interactions (AWS Kinesis)
- **Model retraining** : pipeline automatisé (AWS SageMaker ou AWS Batch)
- **A/B Testing** : framework d'expérimentation
- **Monitoring** : AWS CloudWatch pour performance et logs
- **API Management** : AWS API Gateway pour production
- **Cache** : AWS ElastiCache (Redis) pour réponses rapides

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
1. **AWS Lambda Function**
   - `lambda_function.py` : handler principal (point d'entrée)
   - `recommendation_engine.py` : logique de recommandation
   - `utils.py` : fonctions utilitaires
   - `requirements.txt` : dépendances Python
   - `config.py` : configuration (bucket S3, paramètres)

2. **Application locale**
   - Interface Streamlit
   - Script de test de la Lambda Function

3. **Scripts de préparation**
   - `data_preprocessing.py` : nettoyage et préparation données
   - `embeddings_reduction.py` : PCA sur embeddings (CPU uniquement)
   - `model_training.py` : calcul matrices de similarité
   - `upload_to_s3.py` : upload des modèles vers S3

### 8.2 Documentation
1. **README.md** : instructions de déploiement et utilisation
2. **architecture_technique.md** : détail architecture MVP
3. **architecture_cible.md** : vision scalabilité et évolutions
4. **user_guide.md** : guide utilisateur application
5. **aws_setup.md** : guide de configuration AWS

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
│   └── (modèles et embeddings réduits - local avant upload S3)
├── docs/
│   ├── architecture_technique.md
│   ├── architecture_cible.md
│   └── aws_setup.md
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

### Phase 3 : Développement AWS Lambda
- Configuration AWS account et ressources (Lambda, S3, IAM)
- Développement de la Lambda Function
- Upload des modèles vers S3
- Configuration Lambda Function URL
- Tests et déploiement

### Phase 4 : Application locale
- Développement interface Streamlit
- Intégration avec AWS Lambda Function URL
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
- **AWS Lambda** (serverless compute)
- **AWS S3** (stockage objets)
- **boto3** : SDK AWS pour Python

### 10.2 Data Science
- **pandas** : manipulation de données
- **numpy** : calculs numériques (CPU uniquement)
- **scikit-learn** : PCA, métriques, similarités (CPU)
- **scipy** : calculs de similarité avancés
- **pickle** : sérialisation modèles

### 10.3 Frontend
- **Streamlit** : interface web simple (recommandé)
- **requests** : appels HTTP vers Lambda

### 10.4 DevOps
- **Git/GitHub** : versioning
- **AWS CLI** : déploiement et gestion
- **pytest** : tests unitaires
- **zip** : packaging Lambda deployment

---

## 11. Contraintes et limitations

### 11.1 Contraintes techniques
- **Pas de GPU** : GPU déjà utilisé par un autre programme → CPU uniquement
- **Taille des embeddings** : 364 MB → réduction nécessaire (PCA sur CPU)
- **AWS Free Tier** : limitations de stockage S3 et invocations Lambda
- **Lambda Limits** :
  - Package size max 250 MB (unzipped)
  - Timeout max 15 minutes
  - Memory max 10 GB
- **Cold start Lambda** : première invocation peut être lente (warmup)
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
- ✅ AWS Lambda déployée et fonctionnelle
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
