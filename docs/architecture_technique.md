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
│                    AZURE FUNCTION                               │
│  ┌──────────────────────────────────────────────────────┐      │
│  │ __init__.py (HTTP Trigger Handler)                   │      │
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
│  │ /tmp/models/ (Cache local Azure Functions)                    │      │
│  │ - user_item_matrix.npz                                │      │
│  │ - embeddings_filtered.pkl                             │      │
│  │ - article_popularity.pkl                              │      │
│  │ - mappings.pkl                                        │      │
│  │ - user_profiles.json                                  │      │
│  └─────────────────┬────────────────────────────────────┘      │
└────────────────────┼─────────────────────────────────────────────┘
                     │
                     │ Download on cold start (Azure Blob Storage → /tmp/)
                     │
┌────────────────────▼─────────────────────────────────────────────┐
│                    AZURE BLOB STORAGE                            │
│  Container: mycontent-models/                                    │
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
- Communication avec Azure Function via HTTP ou moteur local
- Affichage formaté des recommandations
- Export CSV des résultats

#### Fichiers
- `app/streamlit_app.py`: Application principale
- `app/requirements.txt`: Dépendances

#### Configuration
```python
AZURE_FUNCTION_URL = "https://func-mycontent-reco-1269.azurewebsites.net/api/recommend"
USE_LOCAL = True/False  # Mode local ou distant
```

---

### 2. Azure Function

**Runtime:** Python 3.10
**Memory:** 512-1024 MB
**Timeout:** 30 seconds
**Architecture:** x86_64
**Trigger:** HTTP Trigger

#### Responsabilités
- Réception des requêtes HTTP (HTTP Trigger)
- Validation des paramètres
- Initialisation du moteur de recommandation (réutilisé entre invocations)
- Téléchargement des modèles depuis Azure Blob Storage (uniquement au cold start)
- Génération des recommandations
- Retour de réponse JSON formatée

#### Fichiers
- `azure_function/__init__.py`: Handler principal (HTTP Trigger)
- `azure_function/recommendation_engine.py`: Moteur de recommandation
- `azure_function/config.py`: Configuration
- `azure_function/utils.py`: Fonctions utilitaires
- `azure_function/requirements.txt`: Dépendances
- `azure_function/function.json`: Configuration du trigger
- `azure_function/host.json`: Configuration hôte

#### Variables d'environnement
```
AZURE_STORAGE_CONNECTION_STRING=<connection_string>
BLOB_CONTAINER_NAME=mycontent-models
MODELS_PREFIX=models/
MODELS_PATH=/tmp/models
LOG_LEVEL=INFO
```

#### Dépendances principales
- numpy 1.24.3
- scipy 1.10.1
- scikit-learn 1.3.0
- pandas 2.0.3
- azure-functions 1.18.0
- azure-storage-blob 12.19.0

---

### 3. Moteur de Recommandation

**Classe:** `RecommendationEngine`
**Localisation:** `azure_function/recommendation_engine.py`

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

### 4. Azure Blob Storage

**Container:** mycontent-models
**Region:** France Central
**Tier:** Hot
**Redundancy:** LRS (Locally Redundant Storage)

#### Structure
```
mycontent-models/
└── models/
    ├── user_item_matrix.npz          (~50-100 MB)
    ├── embeddings_filtered.pkl       (~100-200 MB)
    ├── article_popularity.pkl        (~1-5 MB)
    ├── mappings.pkl                  (~1-5 MB)
    ├── user_profiles.json            (~5-10 MB)
    └── articles_metadata.csv         (~15 MB)
```

**Taille totale:** ~200-350 MB (modèles complets) ou ~86 MB (modèles lite)

#### Permissions Azure RBAC
La Azure Function utilise **Managed Identity** pour accéder au Blob Storage :
```
Role: Storage Blob Data Reader
Scope: Container mycontent-models
Principal: func-mycontent-reco-1269 (Managed Identity)
```

Permissions requises :
- `Microsoft.Storage/storageAccounts/blobServices/containers/read`
- `Microsoft.Storage/storageAccounts/blobServices/containers/blobs/read`

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

3. **upload_to_azure.py**
   - Upload des modèles vers Azure Blob Storage
   - Validation du transfert

#### Temps d'exécution estimé
- Exploration: ~1 minute
- Preprocessing: ~10-15 minutes
- Upload Azure Blob Storage: ~2-5 minutes (selon bande passante)

---

## Flux de données

### Requête de recommandation

```
1. User saisit user_id=123 dans Streamlit
   ↓
2. Streamlit envoie GET https://azurewebsites.net?user_id=123&n_recommendations=5
   ↓
3. Azure Functions parse la requête
   ↓
4. Azure Functions initialise le moteur (si cold start)
   ↓
5. Moteur télécharge modèles depuis Azure Blob Storage (si nécessaire)
   ↓
6. Moteur calcule:
   - Collaborative filtering scores
   - Content-based filtering scores
   - Hybrid combination
   - Diversity filtering
   ↓
7. Azure Functions retourne JSON avec 5 recommandations
   ↓
8. Streamlit affiche les résultats formatés
```

### Cold Start vs Warm Start

**Cold Start (première invocation)**
```
Request → Azure Functions init (5-10s) → Download Azure Blob Storage (3-5s) → Load models (2-3s)
       → Compute (0.5-1s) → Response
Total: ~10-20s
```

**Warm Start (invocations suivantes)**
```
Request → Azure Functions reuse container → Load from memory → Compute (0.5-1s)
       → Response
Total: ~1-2s
```

---

## Performance et optimisations

### Optimisations actuelles

1. **Matrice sparse (CSR)**
   - Économie mémoire: ~99% d'espace économisé
   - Opérations optimisées pour matrices creuses

2. **Réutilisation container Azure Functions**
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

**Mémoire Azure Functions:**
- Minimum: 512 MB
- Recommandé: 1024 MB
- Maximum testé: 1536 MB

**Coûts Azure (estimés, Free Tier):**
- Azure Functions invocations: 1M gratuits/mois
- Azure Functions compute: 400,000 GB-secondes gratuits/mois
- Azure Blob Storage storage: 5 GB gratuits
- Azure Blob Storage requests: 20,000 GET gratuits/mois

---

## Sécurité

### Azure Function

1. **HTTP Trigger URL**
   - Auth Type: NONE (public pour MVP)
   - CORS: Activé (Access-Control-Allow-Origin: *)

2. **Azure RBAC Role**
   - Principe du moindre privilège
   - Read-only access à Azure Blob Storage
   - CloudWatch Logs pour monitoring

3. **Validation des entrées**
   - user_id: entier positif
   - n_recommendations: 1-50
   - alpha: 0.0-1.0
   - Protection contre injection

### Azure Blob Storage container

1. **Accès**
   - Privé par défaut
   - Accès Azure Functions via Managed Identity uniquement

2. **Encryption**
   - Server-side encryption (SSE-Azure Blob Storage)
   - Pas de données sensibles utilisateurs

---

## Monitoring et logging

### Azure Application Insights

**Logs:**
- Log Analytics Workspace: func-mycontent-reco-logs
- Retention: 30 jours
- Integration: Automatique via Azure Function

**Logs générés:**
```python
INFO: Événement reçu: {user_id: 123}
INFO: Initialisation du moteur de recommandation
INFO: Génération de 5 recommandations pour user 123
INFO: ✓ 5 recommandations générées
```

**Métriques automatiques:**
- Invocations (executions)
- Duration (response time)
- Errors (failures)
- Availability
- Performance counters
- Dependencies

### Dashboard recommandé

- Invocations par heure
- Latence moyenne (p50, p95, p99)
- Taux d'erreur
- Cold start ratio
- Coût estimé (Consumption Plan)
- Memory usage

---

## Limitations techniques

### Azure Functions (Consumption Plan)

1. **Package size**
   - Recommandé: < 100 MB pour cold start rapide
   - Actuel: ~86 MB (modèles lite) avec dépendances

2. **Timeout**
   - Max 5 minutes (Consumption Plan)
   - Configuré: 30 secondes

3. **Memory**
   - Max 1.5 GB (Consumption Plan)
   - Allouée dynamiquement: 512-1024 MB

4. **Cold start**
   - Première invocation lente (~3s pour modèles lite)
   - Mitigations: Premium Plan avec Always Ready instances (coût supplémentaire)

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
# Tester la Azure Functions déployée
curl "https://azurewebsites.net/?user_id=0&n_recommendations=5"
```

### Tests de performance

```bash
# Load testing avec Apache Bench
ab -n 100 -c 10 "https://azurewebsites.net/?user_id=0&n_recommendations=5"
```

---

## Déploiement

### Checklist

- [x] Preprocessing terminé
- [x] Modèles uploadés sur Azure Blob Storage
- [x] Container Azure Blob Storage créé et accessible
- [x] Azure Function déployée (func-mycontent-reco-1269)
- [x] Managed Identity configurée
- [x] HTTP Trigger activé
- [x] Variables d'environnement configurées
- [x] Tests de validation passés
- [x] Application Streamlit Enhanced testée

### Commandes

```bash
# 1. Preprocessing
python3 data_preparation/data_preprocessing.py

# 2. Upload Azure Blob Storage
az storage blob upload-batch \
  --account-name mycontentstorage \
  --destination mycontent-models \
  --source ./models/

# 3. Déployer Azure Function
cd azure_function
func azure functionapp publish func-mycontent-reco-1269

# 4. Tester
curl -X POST https://func-mycontent-reco-1269.azurewebsites.net/api/recommend \
  -H "Content-Type: application/json" \
  -d '{"user_id": 58, "n": 5}'

# 5. Lancer Streamlit Enhanced
cd app && streamlit run streamlit_app_enhanced.py
```

---

## Support et troubleshooting

### Problèmes courants

**1. Azure Functions timeout**
- Solution: Augmenter la mémoire (plus de mémoire = plus de CPU)
- Solution: Optimiser les modèles (réduire embeddings)

**2. Cold start trop long**
- Solution: Utiliser Provisioned Concurrency (coût supplémentaire)
- Solution: Réduire la taille du package

**3. Out of memory**
- Solution: Augmenter la mémoire Azure Functions
- Solution: Réduire la dimension des embeddings (PCA)

**4. Azure Blob Storage access denied**
- Solution: Vérifier les permissions Azure RBAC
- Solution: Vérifier le nom du container

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
