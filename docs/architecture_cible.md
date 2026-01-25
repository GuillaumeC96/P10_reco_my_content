# Architecture Cible - My Content

## Vision

Cette documentation présente l'architecture cible du système de recommandation My Content pour une mise en production à grande échelle, capable de gérer l'ajout continu de nouveaux utilisateurs et articles.

## Évolution MVP → Production

### Architecture MVP (actuelle)

```
[Streamlit Local] → [Azure Function] → [Azure Blob Storage Models (statiques)]
```

**Limitations:**
- Données statiques
- Pas de mise à jour en temps réel
- Cold start Azure Functions
- Pas de cache
- Scalabilité limitée

### Architecture Production (cible)

```
┌─────────────────────────────────────────────────────────────────────┐
│                           UTILISATEURS                               │
└──────────┬──────────────────────────────────────┬───────────────────┘
           │                                       │
           │ Web App                               │ Mobile App
           ▼                                       ▼
┌─────────────────────┐                 ┌──────────────────────┐
│   CloudFront CDN    │                 │    API Gateway       │
│   (Static Assets)   │                 │   (REST/GraphQL)     │
└──────────┬──────────┘                 └──────────┬───────────┘
           │                                       │
           │                         ┌─────────────┴────────────┐
           │                         │                          │
           │                         ▼                          ▼
┌──────────┴──────────┐    ┌────────────────┐      ┌─────────────────┐
│  Azure Blob Storage Static Website  │    │  Azure Functions/ECS    │      │  Azure Functions/Fargate │
│  (Frontend)         │    │  Auth Service  │      │  Reco Service   │
└─────────────────────┘    └────────┬───────┘      └─────┬───────────┘
                                    │                     │
                     ┌──────────────┴─────────────────────┴──────────┐
                     │                                                │
                     ▼                                                ▼
          ┌──────────────────────┐                    ┌──────────────────────┐
          │  ElastiCache Redis   │←───────────────────│  Real-time Engine    │
          │  (Cache)             │                    │  (Kafka/Kinesis)     │
          └──────────┬───────────┘                    └──────────┬───────────┘
                     │                                           │
                     ▼                                           ▼
          ┌──────────────────────┐                    ┌──────────────────────┐
          │  RDS/DynamoDB        │←───────────────────│  Data Lake (Azure Blob Storage)      │
          │  (Metadata, Users)   │                    │  (Raw Interactions)  │
          └──────────────────────┘                    └──────────┬───────────┘
                                                                  │
                                                                  ▼
                                                       ┌──────────────────────┐
                                                       │  SageMaker/Batch     │
                                                       │  (Model Training)    │
                                                       └──────────────────────┘
```

---

## Composants de l'architecture cible

### 1. Frontend

#### Web Application
- **Framework:** React/Next.js ou Vue.js
- **Hébergement:** Azure Blob Storage + CloudFront
- **Features:**
  - Interface utilisateur moderne
  - Personnalisation du profil
  - Feed d'articles recommandés
  - Système de feedback (like/dislike)
  - Partage social

#### Mobile Application
- **Framework:** React Native ou Flutter
- **Features:**
  - Notifications push
  - Mode offline
  - Synchronisation multi-devices
  - Géolocalisation pour recommandations contextuelles

---

### 2. API Layer

#### API Gateway
- **Service:** Azure API Gateway
- **Type:** REST ou GraphQL
- **Features:**
  - Rate limiting (throttling)
  - Authentication (Cognito/JWT)
  - API versioning
  - Request/Response transformation
  - CORS handling

#### Endpoints principaux
```
GET  /api/v1/recommendations?user_id={id}&n={n}
POST /api/v1/feedback {user_id, article_id, rating}
GET  /api/v1/user/profile?user_id={id}
POST /api/v1/user/preferences {user_id, categories[]}
GET  /api/v1/articles/trending
GET  /api/v1/articles/{id}
```

---

### 3. Authentication & Authorization

#### Azure Cognito
- **User Pools:** Gestion des utilisateurs
- **Identity Pools:** Accès temporaire aux ressources Azure
- **Features:**
  - Sign up/Sign in
  - OAuth 2.0 / OIDC
  - MFA (Multi-Factor Authentication)
  - Social login (Google, Facebook, Apple)

#### JWT Tokens
- Access token: 1 heure
- Refresh token: 30 jours
- Stockage sécurisé (HttpOnly cookies)

---

### 4. Services Backend

#### A. Recommendation Service

**Compute:**
- **Azure Functions:** Pour requêtes légères (< 1s)
- **ECS Fargate:** Pour modèles complexes (> 1s)
- **Auto-scaling:** Basé sur charge

**Algorithmes:**

##### 1. Collaborative Filtering Avancé
```python
# Matrix Factorization (SVD++)
R ≈ U × V^T + biases

# Neural Collaborative Filtering
embedding_user = Embedding(user_id)
embedding_item = Embedding(article_id)
interaction = concat(embedding_user, embedding_item)
prediction = MLP(interaction)
```

##### 2. Deep Learning Models
```python
# Wide & Deep Learning
wide_part = LinearModel(sparse_features)
deep_part = DNN(dense_embeddings)
output = sigmoid(wide_part + deep_part)

# BERT-based Content Similarity
article_embedding = BERT(article_text)
similarity = cosine_similarity(user_profile, article_embedding)
```

##### 3. Sequential Models
```python
# LSTM pour séquences de lecture
user_sequence = [article_1, article_2, ..., article_n]
hidden_state = LSTM(user_sequence)
next_articles = softmax(Dense(hidden_state))

# Transformer pour attention
attention_weights = Attention(articles_read)
recommendation = WeightedSum(attention_weights, article_pool)
```

##### 4. Multi-Armed Bandits
```python
# Exploration-Exploitation
if random() < epsilon:
    # Explore: Nouveaux contenus
    article = sample_random_articles()
else:
    # Exploit: Meilleurs contenus connus
    article = top_recommended_article()

# Mise à jour des récompenses (Thompson Sampling)
```

#### B. Personalization Service
- Gestion des profils utilisateurs
- Préférences de catégories
- Historique de lecture
- Settings de notifications

#### C. Analytics Service
- Tracking des interactions
- Métriques de performance
- A/B testing
- Tableau de bord pour product team

---

### 5. Caching Layer

#### ElastiCache (Redis)
- **Purpose:** Réduire latence et coût
- **TTL:** 5-15 minutes selon type de contenu

**Cache stratégies:**
```python
# Cache des recommandations
key = f"reco:{user_id}:{timestamp_hour}"
ttl = 900  # 15 minutes

# Cache des profils utilisateurs
key = f"profile:{user_id}"
ttl = 3600  # 1 heure

# Cache des articles populaires
key = f"trending:{category}:{date}"
ttl = 300  # 5 minutes

# Cache des embeddings
key = f"embedding:{article_id}"
ttl = 86400  # 24 heures
```

---

### 6. Data Storage

#### A. Bases de données relationnelles (RDS)

**PostgreSQL ou MySQL**
- Métadonnées des articles
- Profils utilisateurs
- Relations sociales
- Transactions

**Schéma:**
```sql
-- Users
CREATE TABLE users (
    user_id BIGSERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE,
    created_at TIMESTAMP,
    preferences JSONB
);

-- Articles
CREATE TABLE articles (
    article_id BIGSERIAL PRIMARY KEY,
    title TEXT,
    content TEXT,
    category_id INT,
    publisher_id INT,
    created_at TIMESTAMP,
    embedding_id VARCHAR(255)
);

-- Interactions
CREATE TABLE interactions (
    interaction_id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(user_id),
    article_id BIGINT REFERENCES articles(article_id),
    interaction_type VARCHAR(50), -- click, like, share, read
    timestamp TIMESTAMP,
    duration_seconds INT
);

-- Indexes
CREATE INDEX idx_interactions_user ON interactions(user_id, timestamp DESC);
CREATE INDEX idx_interactions_article ON interactions(article_id, timestamp DESC);
```

#### B. Base de données NoSQL (DynamoDB)

**Use cases:**
- Session tracking (haute vélocité)
- Événements en temps réel
- Compteurs (vues, likes)

**Tables:**
```
UserSessions
- PK: user_id
- SK: session_timestamp
- Attributes: device, location, duration

ArticleStats
- PK: article_id
- SK: date
- Attributes: views, clicks, likes, shares

RealtimeEvents
- PK: event_id
- SK: timestamp
- Attributes: user_id, article_id, event_type
```

#### C. Data Lake (Azure Data Lake Storage Gen2)

**Organisation:**
```
mycontent-datalake/
├── raw/
│   ├── interactions/
│   │   └── year=2025/month=12/day=09/hour=10/*.parquet
│   ├── articles/
│   │   └── year=2025/month=12/day=09/*.json
│   └── embeddings/
│       └── version=v1/*.pkl
├── processed/
│   ├── user_profiles/
│   ├── article_features/
│   └── aggregates/
└── models/
    ├── collaborative/
    ├── content_based/
    └── hybrid/
```

---

### 7. Real-time Data Pipeline

#### Architecture Streaming

```
┌─────────────┐
│   Events    │ (Clicks, Likes, Reads)
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│ Azure Event Hubs│ (Data ingestion)
└──────┬──────────┘
       │
       ├─────────────────────────┬────────────────────┐
       ▼                         ▼                    ▼
┌──────────────┐      ┌──────────────────┐    ┌─────────────┐
│ Azure Function│      │ Stream Analytics │    │Azure Function│
│  (Real-time  │      │ (Archive to ADLS)│    │  (Triggers) │
│   Update)    │      └──────────────────┘    └─────────────┘
└──────┬───────┘
       │
       ▼
┌──────────────┐
│   DynamoDB   │
│   (Hot data) │
└──────────────┘
```

#### Kinesis Data Streams
- **Shards:** Auto-scaling basé sur throughput
- **Retention:** 24-168 heures
- **Consumers:**
  - Real-time recommendation updates
  - Analytics pipeline
  - Archivage Azure Blob Storage

#### Azure Functions Event Processors
```python
def process_interaction_event(event):
    """
    Traite une interaction utilisateur en temps réel
    """
    user_id = event['user_id']
    article_id = event['article_id']
    event_type = event['type']  # click, like, read

    # 1. Mettre à jour le profil utilisateur
    update_user_profile(user_id, article_id)

    # 2. Invalider le cache des recommandations
    invalidate_cache(f"reco:{user_id}:*")

    # 3. Mettre à jour les stats de l'article
    increment_article_stat(article_id, event_type)

    # 4. Déclencher recalcul si nécessaire
    if should_recompute(user_id):
        trigger_recomputation(user_id)
```

---

### 8. Machine Learning Pipeline

#### Azure SageMaker

**Training Pipeline:**
```
┌──────────────┐
│  Data Lake   │ (Azure Blob Storage)
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  SageMaker   │
│  Processing  │ (Feature engineering)
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  SageMaker   │
│  Training    │ (Model training)
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  SageMaker   │
│  Evaluation  │ (Model validation)
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  Model       │
│  Registry    │ (Versioning)
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  Deploy to   │
│  Production  │ (Blue/Green deployment)
└──────────────┘
```

#### Scheduled Retraining
- **Fréquence:** Hebdomadaire ou basée sur drift detection
- **Métriques surveillées:**
  - Click-Through Rate (CTR)
  - Conversion Rate
  - Diversity Score
  - Coverage

#### A/B Testing Framework
```python
# Définition d'une expérience
experiment = {
    'name': 'alpha_tuning_v2',
    'variants': {
        'control': {'alpha': 0.6},  # 50% trafic
        'variant_a': {'alpha': 0.7}, # 25% trafic
        'variant_b': {'alpha': 0.5}  # 25% trafic
    },
    'metrics': ['ctr', 'engagement_time', 'diversity'],
    'duration_days': 14
}

# Assignment utilisateur
def get_variant(user_id, experiment_name):
    hash_value = hash(f"{user_id}:{experiment_name}")
    return variants[hash_value % len(variants)]
```

---

### 9. Monitoring & Observability

#### CloudWatch

**Dashboards:**
- Latence API (p50, p95, p99)
- Taux d'erreur
- Throughput (req/s)
- Cache hit ratio
- Coût par requête

**Alarms:**
- Latence > 2s (p95)
- Error rate > 1%
- Cache hit ratio < 80%
- Azure Functions throttling

#### X-Ray
- Distributed tracing
- Analyse des goulets d'étranglement
- Visualisation des dépendances

#### Custom Metrics
```python
cloudwatch.put_metric_data(
    Namespace='MyContent/Recommendations',
    MetricData=[
        {
            'MetricName': 'RecommendationDiversity',
            'Value': diversity_score,
            'Unit': 'None',
            'Timestamp': datetime.now()
        },
        {
            'MetricName': 'ColdStartRate',
            'Value': cold_start_ratio,
            'Unit': 'Percent'
        }
    ]
)
```

---

### 10. Gestion des Nouveaux Utilisateurs

#### Progressive Profiling

**Étape 1: Onboarding**
```python
def onboard_new_user(user_id):
    # 1. Demander préférences initiales
    categories = ask_user_preferences()

    # 2. Créer un profil de base
    profile = {
        'user_id': user_id,
        'preferred_categories': categories,
        'exploration_rate': 0.3,  # Plus d'exploration au début
        'is_new': True
    }

    # 3. Recommandations initiales
    # - 60% articles populaires des catégories préférées
    # - 30% articles populaires généraux
    # - 10% articles divers (exploration)
    return initial_recommendations(profile)
```

**Étape 2: Apprentissage rapide (premières sessions)**
```python
def quick_learning_phase(user_id, interactions):
    """
    Phase d'apprentissage accélérée pour nouveaux utilisateurs
    """
    if len(interactions) < 10:
        # Poids plus élevé sur les premières interactions
        weights = [2.0] * len(interactions)

        # Mise à jour rapide du profil
        update_user_profile(user_id, interactions, weights)

        # Réduire l'exploration
        adjust_exploration_rate(user_id, reduce=0.05)

    # Transition vers recommandations hybrides après 10+ interactions
    if len(interactions) >= 10:
        enable_collaborative_filtering(user_id)
```

**Étape 3: Maturation du profil**
```python
def mature_user_recommendations(user_id):
    """
    Recommandations pour utilisateurs avec historique établi
    """
    # Mélange optimal
    recommendations = {
        'collaborative': 0.4,  # Utilisateurs similaires
        'content_based': 0.3,  # Similarité de contenu
        'sequential': 0.2,      # Patterns temporels
        'exploration': 0.1      # Découverte
    }

    return hybrid_recommend(user_id, recommendations)
```

---

### 11. Gestion des Nouveaux Articles

#### Pipeline d'ingestion

**Étape 1: Ingestion**
```python
def ingest_new_article(article):
    """
    Pipeline d'ingestion d'un nouvel article
    """
    # 1. Validation et nettoyage
    cleaned_article = clean_and_validate(article)

    # 2. Extraction de features
    features = extract_features(cleaned_article)

    # 3. Génération d'embeddings
    embedding = generate_embedding(cleaned_article.content)

    # 4. Stockage
    save_to_database(cleaned_article, features, embedding)

    # 5. Indexation pour recherche
    index_article(cleaned_article)

    return article_id
```

**Étape 2: Bootstrapping**
```python
def bootstrap_new_article(article_id):
    """
    Stratégie de démarrage pour un nouvel article
    """
    # 1. Trouver articles similaires (content-based)
    similar_articles = find_similar_by_content(article_id)

    # 2. Identifier utilisateurs cibles
    # Utilisateurs qui ont aimé des articles similaires
    target_users = get_users_who_liked(similar_articles)

    # 3. Recommandation progressive
    # Commencer par un petit groupe d'utilisateurs
    initial_exposure = sample(target_users, k=100)

    # 4. Collecter feedback
    track_engagement(article_id, initial_exposure)

    # 5. Ajuster en fonction des performances
    if high_engagement(article_id):
        increase_exposure(article_id)
    else:
        maintain_limited_exposure(article_id)
```

**Étape 3: Expansion progressive**
```python
def expand_article_reach(article_id):
    """
    Expansion progressive basée sur performance
    """
    # Métriques de performance
    metrics = get_article_metrics(article_id)

    # Score de qualité
    quality_score = (
        0.4 * metrics['ctr'] +
        0.3 * metrics['avg_read_time'] +
        0.2 * metrics['share_rate'] +
        0.1 * metrics['like_rate']
    )

    # Stratégie d'expansion
    if quality_score > 0.7:
        # Excellent: expansion rapide
        expansion_rate = 0.5
    elif quality_score > 0.5:
        # Bon: expansion modérée
        expansion_rate = 0.3
    else:
        # Faible: expansion limitée
        expansion_rate = 0.1

    # Augmenter le pool d'utilisateurs
    current_reach = get_current_reach(article_id)
    new_reach = current_reach * (1 + expansion_rate)
    update_article_reach(article_id, new_reach)
```

---

### 12. Coûts et ROI

#### Estimation des coûts mensuels (100k utilisateurs actifs)

**Compute:**
- Azure Functions: $50-100 (1M invocations, 1s avg)
- ECS Fargate: $200-400 (modèles complexes)
- EC2 (si nécessaire): $100-300

**Storage:**
- Azure Blob Storage: $50-100 (5 TB data lake)
- RDS: $200-500 (db.r5.large)
- DynamoDB: $100-200 (on-demand)

**Cache:**
- ElastiCache: $150-300 (cache.r5.large)

**Data Transfer:**
- CloudFront: $100-200
- Inter-service: $50-100

**ML:**
- SageMaker training: $100-300/mois
- SageMaker inference: $200-400

**Total estimé:** $1,300 - $2,800/mois

**ROI attendu:**
- Augmentation engagement: +30-50%
- Augmentation temps de lecture: +40-60%
- Réduction churn: -20-30%
- Augmentation revenus publicitaires: +25-45%

---

### 13. Sécurité et Compliance

#### Security Best Practices

1. **Encryption**
   - At rest: Azure Blob Storage (SSE-Azure Blob Storage/SSE-KMS), RDS (AES-256)
   - In transit: TLS 1.3, Certificate Manager

2. **Access Control**
   - Managed Identitys avec principe du moindre privilège
   - VPC pour isolation réseau
   - Security Groups restrictifs

3. **Secrets Management**
   - Azure Secrets Manager pour credentials
   - Parameter Store pour configuration
   - Rotation automatique des secrets

4. **Audit & Compliance**
   - CloudTrail pour tous les appels API
   - Config Rules pour compliance
   - GuardDuty pour détection menaces

#### GDPR Compliance

```python
# Droit à l'oubli
def delete_user_data(user_id):
    # 1. Anonymiser les interactions
    anonymize_interactions(user_id)

    # 2. Supprimer le profil
    delete_user_profile(user_id)

    # 3. Supprimer du cache
    delete_cache_entries(user_id)

    # 4. Supprimer des archives
    schedule_archive_deletion(user_id)

# Export des données
def export_user_data(user_id):
    data = {
        'profile': get_user_profile(user_id),
        'interactions': get_user_interactions(user_id),
        'preferences': get_user_preferences(user_id)
    }
    return json.dumps(data, indent=2)
```

---

### 14. Migration MVP → Production

#### Phase 1: Préparation (Mois 1-2)
- [ ] Setup infrastructure Azure (Terraform/CloudFormation)
- [ ] Migration des données vers RDS/DynamoDB
- [ ] Configuration du streaming (Kinesis)
- [ ] Setup du cache (ElastiCache)
- [ ] Développement API Gateway
- [ ] Tests de charge

#### Phase 2: Backend (Mois 3-4)
- [ ] Refactoring du moteur de recommandation
- [ ] Implémentation des nouveaux algorithmes (NCF, Deep Learning)
- [ ] Pipeline ML sur SageMaker
- [ ] Monitoring et alertes
- [ ] A/B testing framework

#### Phase 3: Frontend (Mois 5-6)
- [ ] Développement Web App (React/Vue)
- [ ] Développement Mobile App
- [ ] Integration avec backend
- [ ] Tests utilisateurs (Beta)

#### Phase 4: Launch (Mois 7)
- [ ] Migration progressive des utilisateurs
- [ ] Monitoring renforcé
- [ ] Support utilisateurs
- [ ] Optimisations post-launch

---

### 15. Métriques de succès

#### Business Metrics
- **DAU/MAU ratio:** >20%
- **Session duration:** +50% vs baseline
- **Articles per session:** +40% vs baseline
- **Return rate:** >60% (J+7)
- **Revenue per user:** +30% vs baseline

#### Technical Metrics
- **Latence p95:** <500ms
- **Availability:** >99.9%
- **Error rate:** <0.1%
- **Cache hit ratio:** >85%
- **Model performance:** AUC >0.75

#### ML Metrics
- **Precision@5:** >0.3
- **Recall@5:** >0.15
- **Diversity:** Coverage >40% des catégories
- **Novelty:** >20% articles découverts
- **Serendipity:** Surprises positives

---

## Conclusion

Cette architecture cible permet:

✅ **Scalabilité:** Millions d'utilisateurs et d'articles
✅ **Temps réel:** Mise à jour continue des recommandations
✅ **Cold start:** Gestion efficace des nouveaux utilisateurs/articles
✅ **Performance:** Latence <500ms
✅ **Coûts:** Optimisés via cache et serverless
✅ **ML avancé:** Deep Learning, sequential models
✅ **Monitoring:** Observabilité complète
✅ **Sécurité:** Encryption, access control, GDPR

**Timeline:** 6-7 mois pour migration complète
**Investissement:** ~$10k-20k/mois infrastructure + équipe dev
**ROI attendu:** +30-50% engagement, rentabilité en 12-18 mois

---

**Version:** 1.0.0
**Date:** Décembre 2025
**Status:** Vision (Architecture Cible)
