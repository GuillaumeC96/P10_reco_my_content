# Pipeline Complet - Système de Recommandation P10

**Date:** 18 Décembre 2024
**Version:** v2.0 (Phase 1 Complete)

---

## Vue d'ensemble simplifiée

```
DONNÉES BRUTES → PREPROCESSING → ENRICHISSEMENT → MODÈLES → RECO ENGINE → DÉPLOIEMENT → ÉVALUATION
   (500 MB)         (15 sec)        (2 min)       (130 MB)   (0.77s/user)    (AWS Lambda)  (7.0% HR@5)
```

---

## Étape 1 : Données Brutes (Point de départ)

### Source : Dataset Globo.com

```
clicks/
├── clicks_hour_0.csv
├── clicks_hour_1.csv
├── ... (385 fichiers au total)
└── clicks_hour_384.csv

articles_metadata.csv
```

**Contenu :**
- 160,377 utilisateurs
- 37,891 articles de news
- 2,526,781 interactions (clics)
- Sparsité : 99.96%

**Colonnes clés des clics :**
- `user_id` : Identifiant utilisateur
- `article_id` : Article cliqué
- `created_at_ts` : Timestamp de l'article
- `click_timestamp` : Quand le clic a eu lieu
- `session_id`, `session_size`, `session_start`
- `category_id` : Catégorie de l'article

---

## Étape 2 : Preprocessing (15 secondes)

### Script : `data_preparation/data_preprocessing_optimized.py`

**Opérations :**

1. **Chargement par batches** (50 fichiers à la fois)
   - Évite de charger 385 DataFrames en mémoire
   - Traitement streaming

2. **Agrégation des clics**
   ```python
   interactions = df.groupby(['user_id', 'article_id']).size()
   # user_1 → article_5 : 3 clics
   # user_1 → article_12 : 1 clic
   # ...
   ```

3. **Création matrice sparse user-item**
   ```
   Format : CSR (Compressed Sparse Row)
   Shape : (160,377 users × 37,891 articles)
   Valeurs : nombre de clics
   Taille : 4.4 MB (au lieu de 600 GB dense!)
   ```

4. **Calcul popularité**
   ```python
   article_popularity = df['article_id'].value_counts()
   # article_160974 : 12,543 clics
   # article_272143 : 8,921 clics
   ```

5. **Profils utilisateurs**
   ```json
   {
     "12345": {
       "articles_read": [160974, 272143, 336221],
       "categories": [1, 3, 5],
       "last_interaction": 1634567890
     }
   }
   ```

**Outputs générés :**
- `user_item_matrix.npz` (4.4 MB)
- `mappings.pkl` (3.2 MB)
- `article_popularity.pkl` (1.5 MB)
- `user_profiles.json` (64 MB)
- `embeddings_filtered.pkl` (38 MB)
- `articles_metadata.csv` (11 MB)

---

## Étape 3 : Enrichissement (2 minutes) - Phase 1 Improvements

### Étape 3A : Calcul interaction_weight

**Script :** `data_preparation/compute_interaction_weights.py`

**Objectif :** Transformer clics simples en scores de qualité d'engagement

```python
# AVANT (count-based)
user_1 → article_5 : 3 clics

# APRÈS (weighted)
user_1 → article_5 : 0.67 (poids de qualité)
```

**Formule :**
```python
interaction_weight = normalize(
    0.3 * click_frequency +      # Combien de fois cliqué
    0.4 * time_spent_norm +      # Temps passé sur l'article
    0.1 * session_size_norm +    # Taille de la session
    0.1 * device_quality +       # Desktop (high) vs Mobile (low)
    0.05 * environment_score +   # App vs Web
    0.05 * referrer_score        # Source du trafic
)
```

**Range :** 0.29 (faible engagement) → 0.81 (fort engagement)

**Output :**
- `interaction_stats_enriched.csv` (426 MB)

### Étape 3B : Création matrice pondérée

**Script :** `data_preparation/create_weighted_matrix.py`

```python
# Charger les poids enrichis
df = pd.read_csv('interaction_stats_enriched.csv')

# Créer sparse matrix avec weights
weighted_matrix = csr_matrix(
    (weights, (user_indices, article_indices)),
    shape=(160377, 37891)
)
```

**Output :**
- `user_item_matrix_weighted.npz` (9.2 MB)

---

## Étape 4 : Moteur de Recommandation (Hybride)

### Script : `lambda/recommendation_engine.py`

**Architecture en 3 composants :**

### 4A. Collaborative Filtering (15% du score final)

```python
def _collaborative_filtering(user_id):
    # 1. Charger vecteur de l'utilisateur
    user_vector = weighted_matrix[user_idx]

    # 2. Calculer similarité avec TOUS les autres users
    similarities = cosine_similarity(user_vector, weighted_matrix)

    # 3. Top 50 utilisateurs similaires
    top_users = similarities.argsort()[-50:]

    # 4. Agréger leurs articles
    for similar_user in top_users:
        for article in similar_user.articles:
            score[article] += similarity * interaction_weight

    return top_articles
```

**Exemple :**
- User 12345 similaire à User 98765 (sim=0.82)
- User 98765 a lu article 336221 (weight=0.75)
- Score pour 336221 = 0.82 × 0.75 = 0.615

### 4B. Content-Based Filtering (5% du score final)

```python
def _content_based_filtering(user_id):
    # 1. Créer profil utilisateur = moyenne pondérée des embeddings
    user_articles = [160974, 272143, 336221]  # Lus par user
    weights = [0.81, 0.67, 0.54]  # interaction_weight

    embeddings = [embedding_160974, embedding_272143, embedding_336221]
    user_profile = np.average(embeddings, axis=0, weights=weights)
    # → vecteur 250D représentant les goûts de l'user

    # 2. Similarité avec tous les articles
    similarities = cosine_similarity(user_profile, all_embeddings)

    # 3. Category boost (+10% max)
    if article.category in user.preferred_categories:
        similarity *= (1.0 + 0.1 * category_frequency)

    return top_articles
```

### 4C. Popularity-Based (80% du score final)

```python
def _popularity_based():
    # 1. Charger popularité brute
    popularity = article_popularity  # Nombre de clics

    # 2. Appliquer temporal decay (CRUCIAL pour news!)
    now = time.time()
    age_days = (now - article.created_at) / 86400
    decay = exp(-age_days * ln(2) / 7.0)  # Half-life = 7 jours

    adjusted_score = popularity * decay

    # Exemple :
    # Article vieux de 7 jours → decay = 0.5 (50% de la popularité)
    # Article vieux de 14 jours → decay = 0.25 (25% de la popularité)

    return top_articles
```

### 4D. Hybridation

```python
def recommend(user_id, n=5):
    # 1. Générer candidats de chaque composant
    collab_recs = _collaborative_filtering(user_id)
    content_recs = _content_based_filtering(user_id)
    trend_recs = _popularity_based()

    # 2. Agréger avec poids
    final_scores = {}
    for article in all_articles:
        final_scores[article] = (
            0.15 * collab_recs.get(article, 0) +
            0.05 * content_recs.get(article, 0) +
            0.80 * trend_recs.get(article, 0)
        )

    # 3. Trier et prendre top N
    top_n = sorted(final_scores.items(), key=lambda x: x[1], reverse=True)

    # 4. Diversity filter (round-robin par catégorie)
    diverse_recs = apply_diversity_filter(top_n)

    return diverse_recs[:n]
```

**Exemple de résultat :**
```python
[
    (article_160974, 0.85),  # Tech
    (article_272143, 0.78),  # Politique
    (article_336221, 0.61),  # Auto
    (article_184532, 0.42),  # Lifestyle
    (article_295847, 0.35)   # Météo
]
```

---

## Étape 5 : Déploiement AWS Lambda

### Architecture Cloud

```
User Request (HTTP)
    ↓
API Gateway
    ↓
AWS Lambda Function (Python 3.9)
    ├── Load models from S3 (cached in /tmp)
    │   └── models/ (130 MB)
    ├── Initialize RecommendationEngine (once)
    └── Process requests (warm: 0.77s per user)
    ↓
JSON Response
    {
        "user_id": 12345,
        "recommendations": [
            {"article_id": 160974, "score": 0.85, "title": "IA générative..."},
            {"article_id": 272143, "score": 0.78, "title": "Élections..."},
            ...
        ]
    }
```

### Fichiers Lambda

**1. lambda_function.py** - Entry point
```python
engine = None

def handler(event, context):
    global engine

    # Init once (cold start)
    if engine is None:
        engine = RecommendationEngine("/tmp/models")
        engine.load_models()

    # Parse request
    user_id = event['queryStringParameters']['user_id']

    # Generate recommendations
    recs = engine.recommend(user_id, n=5)

    return {
        'statusCode': 200,
        'body': json.dumps(recs)
    }
```

**2. config.py** - Configuration
```python
S3_BUCKET = "my-content-reco-models"
MODEL_PATH = "/tmp/models"
DEFAULT_N_RECOMMENDATIONS = 5
```

**3. utils.py** - S3 utilities
```python
def download_models_from_s3():
    s3 = boto3.client('s3')
    for file in model_files:
        s3.download_file(S3_BUCKET, file, f"/tmp/models/{file}")
```

### Déploiement

```bash
# 1. Upload models to S3
python data_preparation/upload_to_s3.py

# 2. Package Lambda
cd lambda/
zip -r function.zip *.py requirements.txt

# 3. Deploy
aws lambda update-function-code \
    --function-name my-content-reco \
    --zip-file fileb://function.zip

# 4. Configure
aws lambda update-function-configuration \
    --function-name my-content-reco \
    --memory-size 3008 \
    --timeout 30
```

---

## Étape 6 : Interface Streamlit (Tests locaux)

### Script : `app/streamlit_app.py`

**Interface web interactive :**

```python
import streamlit as st
from lambda.recommendation_engine import RecommendationEngine

# Load engine
engine = RecommendationEngine("./models")
engine.load_models()

# UI
user_id = st.number_input("User ID", value=12345)
n_recs = st.slider("Nombre de recommandations", 1, 10, 5)

if st.button("Recommander"):
    recs = engine.recommend(user_id, n=n_recs)

    for i, (article_id, score) in enumerate(recs):
        st.write(f"{i+1}. Article {article_id} - Score: {score:.2f}")
```

**Lancement :**
```bash
streamlit run app/streamlit_app.py
# → http://localhost:8501
```

---

## Étape 7 : Évaluation & Benchmarking

### Script : `evaluation/benchmark.py`

**Process :**

1. **Split train/test**
   ```python
   # 80% interactions pour entraînement
   # 20% interactions pour test (ground truth)
   ```

2. **Pour chaque méthode (7 baselines + hybrid) :**
   - Popular (top articles)
   - Random
   - Recent
   - Item-kNN
   - Content-Based
   - Collaborative
   - **Hybrid (votre système)**

3. **Pour chaque utilisateur test (500) :**
   ```python
   # Générer 5 recommandations
   recs = method.recommend(user_id, n=5)

   # Comparer avec ground truth
   ground_truth = test_interactions[user_id]

   # Calculer métriques
   hr_5 = 1 if any(r in ground_truth for r in recs) else 0
   mrr = 1 / position_of_first_hit if hit else 0
   ndcg = calculate_ndcg(recs, ground_truth)
   diversity = len(set(categories_of(recs))) / 5
   ```

4. **Agréger résultats**
   ```python
   avg_hr_5 = sum(hr_5_per_user) / 500
   # → 7.0% pour Hybrid
   ```

**Métriques calculées :**
- **HR@5** (Hit Rate) : % users avec ≥1 article pertinent dans top 5
- **MRR** (Mean Reciprocal Rank) : Position moyenne du 1er hit
- **NDCG@5** : Qualité du classement
- **Diversity** : Variété des catégories
- **Coverage** : % du catalogue recommandé

**Résultats finaux (500 users) :**

| Méthode | HR@5 | MRR | NDCG@5 | Diversity | Time (s) |
|---------|------|-----|--------|-----------|----------|
| Popular | 8.6% | 3.21% | 2.79% | 0.932 | 0.04 |
| **Hybrid (amélioré)** | **7.0%** | **2.50%** | **2.20%** | **1.000** | **384** |
| Content-Based | 1.2% | 0.62% | 0.47% | 0.465 | 28.2 |
| Collaborative | 0.0% | 0.0% | 0.0% | 0.816 | 21.9 |
| Random | 0.0% | 0.0% | 0.0% | 0.971 | 0.65 |

---

## Étape 8 : Hyperparameter Tuning (Optionnel)

### Script : `evaluation/bayesian_optimization.py`

**Paramètres optimisés :**
- `collab_weight` : 0.0 → 1.0
- `content_weight` : 0.0 → 1.0
- `trend_weight` : 0.0 → 1.0
- `decay_half_life_days` : 3.0 → 14.0

**Méthode :** Optimisation Bayésienne (Gaussian Process)

**Résultats :**
```
Meilleure configuration trouvée :
    collab_weight = 0.15
    content_weight = 0.05
    trend_weight = 0.80
    decay_half_life_days = 7.0

Best HR@5 : 7.0%
```

---

## Résumé Timeline

| Étape | Script | Durée | Output |
|-------|--------|-------|--------|
| 1. Exploration | data_exploration.py | 30s | Statistiques |
| 2. Preprocessing | data_preprocessing_optimized.py | 15s | 7 fichiers (127 MB) |
| 3A. Weights | compute_interaction_weights.py | 2 min | interaction_stats_enriched.csv |
| 3B. Weighted Matrix | create_weighted_matrix.py | 30s | user_item_matrix_weighted.npz |
| 4. Engine | recommendation_engine.py | 0.77s/user | Recommandations |
| 5. Deploy | upload_to_s3.py + deploy.sh | 5 min | Lambda function |
| 6. Interface | streamlit_app.py | instant | Web UI |
| 7. Benchmark | benchmark.py | 7 min | 7.0% HR@5 |
| 8. Tuning | bayesian_optimization.py | 2-4h | Optimal params |

**Total développement :** ~15 minutes (sans tuning)
**Total production :** 0.77s par utilisateur

---

## Fichiers Générés (models/)

| Fichier | Taille | Description |
|---------|--------|-------------|
| user_item_matrix.npz | 4.4 MB | Matrice sparse counts |
| user_item_matrix_weighted.npz | 9.2 MB | Matrice sparse weighted |
| mappings.pkl | 3.2 MB | ID → index mappings |
| article_popularity.pkl | 1.5 MB | Popularité des articles |
| user_profiles.json | 64 MB | Historiques utilisateurs |
| embeddings_filtered.pkl | 38 MB | Embeddings articles (250D) |
| articles_metadata.csv | 11 MB | Métadonnées articles |
| interaction_stats_enriched.csv | 426 MB | Stats enrichies |
| preprocessing_stats.json | 247 B | Statistiques preprocessing |

**Total :** ~130 MB (compressed) vs 600 GB si matrice dense !

---

## Flow de Production (Requête Utilisateur)

```
1. User visite le site
   ↓
2. Frontend fait requête HTTP
   GET /recommendations?user_id=12345
   ↓
3. API Gateway route vers Lambda
   ↓
4. Lambda (si cold start) :
   - Download models from S3 → /tmp
   - Load recommendation_engine
   - Cache in memory
   ↓
5. Lambda (warm) :
   - Extract user_id=12345
   - engine.recommend(12345, n=5)
     ├─ Collaborative (15%) → 0.77s
     ├─ Content-Based (5%)
     └─ Popularity+Decay (80%)
   - Aggregate scores
   - Apply diversity filter
   ↓
6. Return JSON response
   {
     "recommendations": [
       {"article_id": 160974, "score": 0.85},
       ...
     ]
   }
   ↓
7. Frontend affiche les articles
```

**Latence totale :**
- Cold start : ~1.5s (première requête)
- Warm : ~0.77s (requêtes suivantes)

---

## Technologies Utilisées

### Data Processing
- **Pandas** : Manipulation DataFrames
- **NumPy** : Calculs vectoriels
- **SciPy** : Matrices sparse (CSR)

### Machine Learning
- **scikit-learn** : Cosine similarity, metrics
- **Word2Vec** : Embeddings pré-entraînés (250D)

### Infrastructure
- **AWS Lambda** : Compute serverless
- **AWS S3** : Storage modèles
- **AWS API Gateway** : HTTP endpoints

### Interface
- **Streamlit** : Web UI pour tests

### Evaluation
- **Custom metrics** : HR@K, MRR, NDCG, Diversity
- **Bayesian Optimization** : Hyperparameter tuning

---

## Points Clés du Pipeline

### ✅ Points Forts

1. **Rapide** : 15 minutes preprocessing pour 2.5M interactions
2. **Efficient** : Sparse matrices (4.4 MB vs 600 GB)
3. **Scalable** : Serverless AWS Lambda
4. **Hybride** : Combine 3 approches (collaborative + content + trend)
5. **Amélioré** : Weighted matrix (+27% vs baseline)
6. **Diverse** : Perfect diversity score (1.0)

### 🎯 Résultats

- **HR@5 : 7.0%** (7 users sur 100 cliquent)
- **81% du Popular baseline** (8.6%)
- **Latence : 0.77s** par utilisateur
- **Amélioration : +27%** vs version originale (5.5%)

### 🚀 Améliorations Futures

- Phase 2 : Session features, geo, device (+2-4% HR@5)
- Learning-to-Rank : LightGBM (+3-5% HR@5)
- Deep Learning : BERT4Rec, Transformers (+5-10% HR@5)
- Real-time updates : Streaming pipeline

---

**Généré le :** 18 Décembre 2024
**Projet :** P10_reco - Système de Recommandation Globo.com
**Status :** ✅ Production Ready
