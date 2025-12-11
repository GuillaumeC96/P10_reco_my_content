# Architecture Technique MVP - My Content

## Vue d'ensemble

Cette documentation décrit l'architecture technique du MVP du système de recommandation My Content.

## Schéma d'architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      UTILISATEUR FINAL                          │
└─────────────────┬───────────────────────────────────────────────┘
                  │
                  │ HTTP (Browser)
                  │
┌─────────────────▼───────────────────────────────────────────────┐
│                  APPLICATION STREAMLIT                          │
│  ┌──────────────────────────────────────────────────────┐      │
│  │ Interface Web                                         │      │
│  │ - Sélection utilisateur                              │      │
│  │ - Configuration paramètres                           │      │
│  │ - Affichage résultats                                │      │
│  └──────────────────────────────────────────────────────┘      │
│                          │                                       │
│                          │ Mode Local OU HTTP                   │
│                          ▼                                       │
│  ┌──────────────────────────────────────────────────────┐      │
│  │ Moteur Local (option)                                │      │
│  │ recommendation_engine.py                             │      │
│  └──────────────────────────────────────────────────────┘      │
└───────────────┬─────────────────────────────────────────────────┘
                │
                │ HTTPS (API Call)
                │
┌───────────────▼─────────────────────────────────────────────────┐
│                    AWS LAMBDA FUNCTION                          │
│  ┌──────────────────────────────────────────────────────┐      │
│  │ lambda_function.py (Handler)                         │      │
│  │ - Parse HTTP request                                  │      │
│  │ - Validate parameters                                 │      │
│  │ - Call recommendation engine                          │      │
│  │ - Format JSON response                                │      │
│  └─────────────────┬────────────────────────────────────┘      │
│                    │                                             │
│                    ▼                                             │
│  ┌──────────────────────────────────────────────────────┐      │
│  │ recommendation_engine.py                             │      │
│  │ - Collaborative Filtering                            │      │
│  │ - Content-Based Filtering                            │      │
│  │ - Hybrid Scoring                                      │      │
│  │ - Diversity Filter                                    │      │
│  └─────────────────┬────────────────────────────────────┘      │
│                    │                                             │
│                    │ Read models/data                            │
│                    ▼                                             │
│  ┌──────────────────────────────────────────────────────┐      │
│  │ /tmp/models/ (Cache local Lambda)                    │      │
│  │ - user_item_matrix.npz                                │      │
│  │ - embeddings_filtered.pkl                             │      │
│  │ - article_popularity.pkl                              │      │
│  │ - mappings.pkl                                        │      │
│  │ - user_profiles.json                                  │      │
│  └─────────────────┬────────────────────────────────────┘      │
└────────────────────┼─────────────────────────────────────────────┘
                     │
                     │ Download on cold start (S3 → /tmp/)
                     │
┌────────────────────▼─────────────────────────────────────────────┐
│                        AWS S3 BUCKET                             │
│  my-content-reco-bucket/                                         │
│  └── models/                                                     │
│      ├── user_item_matrix.npz                                   │
│      ├── embeddings_filtered.pkl                                │
│      ├── article_popularity.pkl                                 │
│      ├── mappings.pkl                                            │
│      ├── user_profiles.json                                      │
│      └── articles_metadata.csv                                   │
└──────────────────────────────────────────────────────────────────┘
```

## Composants Techniques

### 1. Application Streamlit

**Technologie:** Streamlit 1.28+
**Langage:** Python 3.9+
**Port:** 8501 (par défaut)

#### Responsabilités
- Interface utilisateur web interactive
- Saisie des paramètres (user_id, n_recommendations, alpha, diversité)
- Communication avec Lambda Function via HTTP ou moteur local
- Affichage formaté des recommandations
- Export CSV des résultats

#### Fichiers
- `app/streamlit_app.py`: Application principale
- `app/requirements.txt`: Dépendances

#### Configuration
```python
LAMBDA_URL = "https://xxxx.lambda-url.region.on.aws/"
USE_LOCAL = True/False  # Mode local ou distant
```

---

### 2. AWS Lambda Function

**Runtime:** Python 3.9
**Memory:** 1024 MB
**Timeout:** 30 seconds
**Architecture:** x86_64
**Handler:** lambda_function.lambda_handler

#### Responsabilités
- Réception des requêtes HTTP (Function URL)
- Validation des paramètres
- Initialisation du moteur de recommandation (réutilisé entre invocations)
- Téléchargement des modèles depuis S3 (uniquement au cold start)
- Génération des recommandations
- Retour de réponse JSON formatée

#### Fichiers
- `lambda/lambda_function.py`: Handler principal
- `lambda/recommendation_engine.py`: Moteur de recommandation
- `lambda/config.py`: Configuration
- `lambda/utils.py`: Fonctions utilitaires
- `lambda/requirements.txt`: Dépendances

#### Variables d'environnement
```
S3_BUCKET=my-content-reco-bucket
S3_MODELS_PREFIX=models/
MODELS_PATH=/tmp/models
LOG_LEVEL=INFO
```

#### Dépendances principales
- numpy 1.24.3
- scipy 1.10.1
- scikit-learn 1.3.0
- pandas 2.0.3
- boto3 1.28.0

---

### 3. Moteur de Recommandation

**Classe:** `RecommendationEngine`
**Localisation:** `lambda/recommendation_engine.py`

#### Algorithmes implémentés

##### A. Collaborative Filtering (User-based)
```python
def _collaborative_filtering(user_id, n_recommendations):
    # 1. Récupérer le vecteur de l'utilisateur
    user_vector = user_item_matrix[user_idx]

    # 2. Calculer similarités cosinus avec tous les utilisateurs
    similarities = cosine_similarity(user_vector, user_item_matrix)

    # 3. Sélectionner les k=50 utilisateurs les plus similaires
    similar_users = top_k_similar(similarities, k=50)

    # 4. Agréger articles avec pondération
    for sim_user in similar_users:
        score = similarity[sim_user] * interactions[sim_user, article]

    # 5. Retourner top N
    return sorted_by_score[:n_recommendations]
```

**Complexité:** O(n_users × n_articles) pour le calcul de similarité

##### B. Content-Based Filtering
```python
def _content_based_filtering(user_id, n_recommendations):
    # 1. Récupérer historique de l'utilisateur
    user_articles = get_user_history(user_id)

    # 2. Calculer embedding moyen du profil utilisateur
    user_profile = mean([embeddings[article] for article in user_articles])

    # 3. Calculer similarité cosinus avec tous les articles
    for article, embedding in all_embeddings:
        score = 1 - cosine_distance(user_profile, embedding)

    # 4. Retourner top N (excluant articles déjà lus)
    return sorted_by_score[:n_recommendations]
```

**Dimension embeddings:** 250
**Complexité:** O(n_articles × embedding_dim)

##### C. Hybrid Scoring
```python
def recommend(user_id, alpha=0.6):
    # Combiner les scores
    collab_scores = collaborative_filtering(user_id)
    content_scores = content_based_filtering(user_id)

    # Normaliser
    collab_normalized = normalize(collab_scores)
    content_normalized = normalize(content_scores)

    # Score final
    final_score = alpha * collab_normalized + (1-alpha) * content_normalized

    return top_k(final_score)
```

**Paramètre alpha:**
- α = 1.0 → 100% Collaborative
- α = 0.6 → 60% Collaborative, 40% Content-based (défaut)
- α = 0.0 → 100% Content-based

##### D. Cold Start Handling
```python
def _popularity_based(n_recommendations):
    # Pour nouveaux utilisateurs sans historique
    # Retourner les articles les plus populaires

    popularity_score = (
        0.7 * (num_clicks / max_clicks) +
        0.3 * (num_sessions / max_sessions)
    )

    return sorted_by_popularity[:n_recommendations]
```

##### E. Diversity Filter
```python
def _diversity_filtering(articles, n_final):
    # Assurer variété de catégories
    selected = []
    categories_used = set()

    for article in articles:
        if article.category not in categories_used:
            selected.append(article)
            categories_used.add(article.category)

        if len(selected) >= n_final:
            break

    return selected
```

---

### 4. AWS S3 Storage

**Bucket:** my-content-reco-bucket
**Region:** us-east-1 (configurable)
**Storage Class:** Standard

#### Structure
```
s3://my-content-reco-bucket/
└── models/
    ├── user_item_matrix.npz          (~50-100 MB)
    ├── embeddings_filtered.pkl       (~100-200 MB)
    ├── article_popularity.pkl        (~1-5 MB)
    ├── mappings.pkl                  (~1-5 MB)
    ├── user_profiles.json            (~5-10 MB)
    └── articles_metadata.csv         (~15 MB)
```

**Taille totale:** ~200-350 MB

#### Permissions IAM
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::my-content-reco-bucket/*",
        "arn:aws:s3:::my-content-reco-bucket"
      ]
    }
  ]
}
```

---

### 5. Preprocessing Pipeline

**Localisation:** `data_preparation/`
**Exécution:** Une fois, en local

#### Étapes

1. **data_exploration.py**
   - Analyse du dataset
   - Statistiques descriptives
   - Validation des données

2. **data_preprocessing.py**
   - Agrégation des clics (385 fichiers CSV)
   - Filtrage des utilisateurs actifs (≥5 interactions)
   - Création de la matrice user-item (format sparse CSR)
   - Calcul de la popularité des articles
   - Génération des profils utilisateurs
   - Filtrage des embeddings
   - Sauvegarde dans `models/`

3. **upload_to_s3.py**
   - Upload des modèles vers S3
   - Validation du transfert

#### Temps d'exécution estimé
- Exploration: ~1 minute
- Preprocessing: ~10-15 minutes
- Upload S3: ~2-5 minutes (selon bande passante)

---

## Flux de données

### Requête de recommandation

```
1. User saisit user_id=123 dans Streamlit
   ↓
2. Streamlit envoie GET https://lambda-url?user_id=123&n_recommendations=5
   ↓
3. Lambda parse la requête
   ↓
4. Lambda initialise le moteur (si cold start)
   ↓
5. Moteur télécharge modèles depuis S3 (si nécessaire)
   ↓
6. Moteur calcule:
   - Collaborative filtering scores
   - Content-based filtering scores
   - Hybrid combination
   - Diversity filtering
   ↓
7. Lambda retourne JSON avec 5 recommandations
   ↓
8. Streamlit affiche les résultats formatés
```

### Cold Start vs Warm Start

**Cold Start (première invocation)**
```
Request → Lambda init (5-10s) → Download S3 (3-5s) → Load models (2-3s)
       → Compute (0.5-1s) → Response
Total: ~10-20s
```

**Warm Start (invocations suivantes)**
```
Request → Lambda reuse container → Load from memory → Compute (0.5-1s)
       → Response
Total: ~1-2s
```

---

## Performance et optimisations

### Optimisations actuelles

1. **Matrice sparse (CSR)**
   - Économie mémoire: ~99% d'espace économisé
   - Opérations optimisées pour matrices creuses

2. **Réutilisation container Lambda**
   - Variables globales pour le moteur
   - Cache en mémoire entre invocations
   - Réduction du temps de réponse après warm-up

3. **Préfiltre des embeddings**
   - Seulement les articles avec interactions
   - Réduction de ~364k à ~50-100k articles
   - Gain en vitesse de calcul

4. **Normalisation des scores**
   - Scores collaborative et content-based normalisés [0, 1]
   - Combinaison équitable via alpha

### Métriques de performance

**Temps de réponse:**
- Cold start: 10-20 secondes
- Warm start: 1-2 secondes
- Local: 0.5-1 seconde

**Mémoire Lambda:**
- Minimum: 512 MB
- Recommandé: 1024 MB
- Maximum testé: 1536 MB

**Coûts AWS (estimés, Free Tier):**
- Lambda invocations: 1M gratuits/mois
- Lambda compute: 400,000 GB-secondes gratuits/mois
- S3 storage: 5 GB gratuits
- S3 requests: 20,000 GET gratuits/mois

---

## Sécurité

### Lambda Function

1. **Function URL**
   - Auth Type: NONE (public pour MVP)
   - CORS: Activé (Access-Control-Allow-Origin: *)

2. **IAM Role**
   - Principe du moindre privilège
   - Read-only access à S3
   - CloudWatch Logs pour monitoring

3. **Validation des entrées**
   - user_id: entier positif
   - n_recommendations: 1-50
   - alpha: 0.0-1.0
   - Protection contre injection

### S3 Bucket

1. **Accès**
   - Privé par défaut
   - Accès Lambda via IAM role uniquement

2. **Encryption**
   - Server-side encryption (SSE-S3)
   - Pas de données sensibles utilisateurs

---

## Monitoring et logging

### AWS CloudWatch

**Logs:**
- Log group: `/aws/lambda/MyContentRecommendation`
- Retention: 7 jours (configurable)

**Logs générés:**
```python
INFO: Événement reçu: {user_id: 123}
INFO: Initialisation du moteur de recommandation
INFO: Génération de 5 recommandations pour user 123
INFO: ✓ 5 recommandations générées
```

**Métriques automatiques:**
- Invocations
- Duration
- Errors
- Throttles
- Concurrent executions

### Dashboard recommandé

- Invocations par heure
- Latence moyenne (p50, p95, p99)
- Taux d'erreur
- Cold start ratio
- Coût estimé

---

## Limitations techniques

### Lambda

1. **Package size**
   - Max 250 MB (unzipped)
   - Actuel: ~150 MB avec dépendances

2. **Timeout**
   - Max 15 minutes
   - Configuré: 30 secondes

3. **Memory**
   - Max 10 GB
   - Configuré: 1024 MB

4. **Cold start**
   - Première invocation lente
   - Mitigations: Provisioned Concurrency (non gratuit)

### Algorithmes

1. **Matrice user-item**
   - Sparsité élevée (>99%)
   - Mise à jour manuelle nécessaire

2. **Embeddings statiques**
   - Pas de fine-tuning dynamique
   - Dimension fixe: 250

3. **CPU uniquement**
   - Pas d'accélération GPU
   - Calculs matriciels en NumPy optimisé

---

## Tests et validation

### Tests unitaires

```bash
# Tester le moteur localement
python3 -c "
from recommendation_engine import RecommendationEngine
engine = RecommendationEngine('../models')
engine.load_models()
recs = engine.recommend(user_id=0, n_recommendations=5)
assert len(recs) == 5
print('✓ Tests passed')
"
```

### Tests d'intégration

```bash
# Tester la Lambda déployée
curl "https://lambda-url/?user_id=0&n_recommendations=5"
```

### Tests de performance

```bash
# Load testing avec Apache Bench
ab -n 100 -c 10 "https://lambda-url/?user_id=0&n_recommendations=5"
```

---

## Déploiement

### Checklist

- [ ] Preprocessing terminé
- [ ] Modèles uploadés sur S3
- [ ] Bucket S3 créé et accessible
- [ ] Lambda Function déployée
- [ ] IAM role configuré
- [ ] Function URL activée
- [ ] Variables d'environnement configurées
- [ ] Tests de validation passés
- [ ] Application Streamlit testée

### Commandes

```bash
# 1. Preprocessing
python3 data_preparation/data_preprocessing.py

# 2. Upload S3
python3 data_preparation/upload_to_s3.py --bucket my-content-reco-bucket

# 3. Déployer Lambda
cd lambda && ./deploy.sh

# 4. Tester
curl "https://lambda-url/?user_id=0&n_recommendations=5"

# 5. Lancer Streamlit
cd app && streamlit run streamlit_app.py
```

---

## Support et troubleshooting

### Problèmes courants

**1. Lambda timeout**
- Solution: Augmenter la mémoire (plus de mémoire = plus de CPU)
- Solution: Optimiser les modèles (réduire embeddings)

**2. Cold start trop long**
- Solution: Utiliser Provisioned Concurrency (coût supplémentaire)
- Solution: Réduire la taille du package

**3. Out of memory**
- Solution: Augmenter la mémoire Lambda
- Solution: Réduire la dimension des embeddings (PCA)

**4. S3 access denied**
- Solution: Vérifier les permissions IAM
- Solution: Vérifier le nom du bucket

---

## Annexes

### A. Format des fichiers modèles

**user_item_matrix.npz**
- Type: scipy.sparse.csr_matrix
- Shape: (n_users, n_articles)
- Dtype: int64
- Format: Compressed Sparse Row

**embeddings_filtered.pkl**
- Type: dict {article_id: np.array}
- Embedding shape: (250,)
- Dtype: float32

**mappings.pkl**
- Type: dict avec clés:
  - user_to_idx: {user_id: idx}
  - article_to_idx: {article_id: idx}
  - idx_to_user: {idx: user_id}
  - idx_to_article: {idx: article_id}

**article_popularity.pkl**
- Type: pandas.DataFrame
- Colonnes: num_clicks, num_sessions, popularity_score
- Index: article_id

**user_profiles.json**
- Type: dict {user_id: profile}
- Profile: {num_interactions, num_articles, top_categories, avg_words, articles_read}

---

**Version:** 1.0.0
**Date:** Décembre 2025
**Status:** Production (MVP)
