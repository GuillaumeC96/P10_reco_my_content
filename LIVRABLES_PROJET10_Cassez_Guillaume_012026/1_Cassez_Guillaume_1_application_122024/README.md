# My Content - Système de Recommandation d'Articles

## 🌐 API Azure Déployée

**Endpoint:** https://func-mycontent-reco-1269.azurewebsites.net/api/recommend

**Resource Group:** rg-mycontent-prod
**Region:** France Central
**Plan:** Consumption Plan

### Test de l'API
```bash
curl -X POST https://func-mycontent-reco-1269.azurewebsites.net/api/recommend \
  -H 'Content-Type: application/json' \
  -d '{"user_id": 58, "n": 5}'
```


## 📋 Description

My Content est un système de recommandation hybride d'articles de presse développé dans le cadre d'un MVP pour encourager la lecture. Le système combine le filtrage collaboratif et le filtrage basé sur le contenu pour recommander 5 articles pertinents à chaque utilisateur.

**Technologies:** Python, Azure Functions, Azure Blob Storage, Streamlit, Scikit-learn, NumPy, Pandas

## 🏗️ Architecture

### Architecture MVP (actuelle)

```
┌──────────────────┐
│  Application     │
│  Streamlit       │ ← Interface utilisateur locale
└────────┬─────────┘
         │ HTTP
         ▼
┌──────────────────┐
│  Azure Functions      │
│  Function        │ ← Serverless compute (Azure Functions)
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Azure Blob Storage          │ ← Stockage des modèles
│  (container)        │   et embeddings
└──────────────────┘
```

### Composants

1. **Moteur de recommandation hybride**
   - Collaborative Filtering (user-based)
   - Content-Based Filtering (embeddings)
   - Gestion du Cold Start (popularity-based)
   - Filtre de diversité des catégories

2. **Azure Function**
   - Runtime: Python 3.9
   - Memory: 1024 MB
   - Timeout: 30s
   - Trigger: HTTP Trigger URL (HTTP)

3. **Application Streamlit**
   - Interface web simple
   - Sélection d'utilisateur
   - Paramètres configurables
   - Affichage des recommandations

## 📊 Dataset

**Source:** Globo.com News Portal User Interactions

- **Articles:** 364 047 articles avec métadonnées
- **Embeddings:** 250 dimensions pré-calculés (347 MB)
- **Interactions:** ~845 000 clics utilisateurs
- **Catégories:** 461 catégories d'articles
- **Période:** Données historiques de sessions utilisateurs

### Structure des données

- `articles_metadata.csv`: article_id, category_id, publisher_id, words_count, created_at_ts
- `articles_embeddings.pickle`: Vecteurs de 250 dimensions pour chaque article
- `clicks/*.csv`: user_id, session_id, click_article_id, timestamps, device info

## 🚀 Installation et Configuration

### Prérequis

- Python 3.9+
- Azure CLI configuré avec credentials
- Compte Azure avec accès à Azure Functions et Azure Blob Storage
- pip et virtualenv

### 1. Cloner le repository

```bash
git clone https://github.com/votre-username/reco-my-content.git
cd reco-my-content
```

### 2. Installer les dépendances

```bash
# Pour le preprocessing
pip install -r requirements.txt

# Pour l'application Streamlit
cd app
pip install -r requirements.txt
cd ..
```

### 3. Préparer les données

```bash
# Explorer les données
python3 data_preparation/data_exploration.py

# Preprocessing (peut prendre 10-15 minutes)
python3 data_preparation/data_preprocessing.py
```

Les fichiers générés seront dans le dossier `models/`:
- `user_item_matrix.npz` - Matrice sparse user-article
- `mappings.pkl` - Mappings user_id/article_id vers indices
- `article_popularity.pkl` - Scores de popularité
- `user_profiles.json` - Profils utilisateurs
- `embeddings_filtered.pkl` - Embeddings des articles actifs
- `articles_metadata.csv` - Métadonnées des articles
- `preprocessing_stats.json` - Statistiques du preprocessing

### 4. Créer un container Azure Blob Storage

```bash
az storage blob mb mycontent-models
```

### 5. Uploader les modèles vers Azure Blob Storage

```bash
python3 data_preparation/upload_to_azure.py --container my-content-reco-container
```

### 6. Déployer la Azure Function

```bash
cd azure_function
./deploy_azure.sh
```

Le script va:
- Créer le rôle Azure RBAC nécessaire
- Packager les dépendances
- Créer/mettre à jour la Azure Function
- Configurer la HTTP Trigger URL
- Afficher l'URL d'accès

### 7. Lancer l'application Streamlit

```bash
cd app
streamlit run streamlit_app.py
```

L'application sera accessible sur `http://localhost:8501`

## 🎯 Utilisation

### Via l'application Streamlit

1. Ouvrir l'application dans le navigateur
2. Entrer l'URL de la Azure Function (ou cocher "Mode local")
3. Sélectionner un user_id
4. Ajuster les paramètres (nombre de recommandations, alpha, diversité)
5. Cliquer sur "Générer des recommandations"
6. Visualiser les résultats et télécharger en CSV

### Via API (Azure HTTP Trigger URL)

```bash
# Exemple de requête simple
curl -X POST https://func-mycontent-reco-1269.azurewebsites.net/api/recommend \
  -H "Content-Type: application/json" \
  -d '{"user_id": 123, "n": 5}'

# Avec tous les paramètres personnalisés
curl -X POST https://func-mycontent-reco-1269.azurewebsites.net/api/recommend \
  -H "Content-Type: application/json" \
  -d '{"user_id": 123, "n": 5, "weights": {"collab": 0.4, "content": 0.3, "trend": 0.3}, "use_diversity": true}'

# Exemple avec priorité sur les tendances
curl -X POST https://func-mycontent-reco-1269.azurewebsites.net/api/recommend \
  -H "Content-Type: application/json" \
  -d '{"user_id": 123, "n": 5, "weights": {"collab": 0.25, "content": 0.25, "trend": 0.5}}'
```

### Réponse JSON

```json
{
  "user_id": 123,
  "n_recommendations": 5,
  "recommendations": [
    {
      "article_id": 45678,
      "score": 0.892,
      "category_id": 281,
      "publisher_id": 0,
      "words_count": 215,
      "created_at_ts": 1489422000000
    },
    ...
  ],
  "parameters": {
    "weight_collab": 0.36,
    "weight_content": 0.39,
    "weight_trend": 0.25,
    "weights_ratio": "39:36:25",
    "use_diversity": true
  }
}
```

## ⚙️ Paramètres

- **user_id** (requis): ID de l'utilisateur (0 à N)
- **n_recommendations** (optionnel): Nombre de recommandations (1-50, défaut: 5)
- **weight_collab** (optionnel): Poids du collaborative filtering (défaut: 0.36 = 36%)
- **weight_content** (optionnel): Poids du content-based filtering (défaut: 0.39 = 39%)
- **weight_trend** (optionnel): Poids du trend/popularity filtering (défaut: 0.25 = 25%)
  - Les poids sont normalisés automatiquement pour sommer à 1.0
  - Ratio par défaut: 3:2:1 (50% Collaborative, 33% Content, 17% Trend)
- **use_diversity** (optionnel): Activer la diversité des catégories (défaut: true)

## 🧪 Tests

### Test local du moteur de recommandation

```bash
cd azure_function
python3 -c "
from recommendation_engine import RecommendationEngine
engine = RecommendationEngine(models_path='../models')
engine.load_models()
recs = engine.recommend(user_id=123, n_recommendations=5)
print(recs)
"
```

### Test de la Azure Function

```bash
# Après déploiement
curl "https://your-azurewebsites.net/?user_id=0&n_recommendations=5"
```

## 📁 Structure du Projet

```
reco-my-content/
├── cahier_des_charges.md          # Spécifications complètes
├── README.md                        # Ce fichier
├── requirements.txt                 # Dépendances Python globales
│
├── news-portal-user-interactions-by-globocom/  # Dataset
│   ├── articles_metadata.csv
│   ├── articles_embeddings.pickle
│   └── clicks/                      # 385 fichiers CSV
│
├── data_preparation/                # Scripts de preprocessing
│   ├── data_exploration.py          # Exploration du dataset
│   ├── data_preprocessing.py        # Préparation des données
│   └── upload_to_azure.py              # Upload vers Azure Blob Storage
│
├── models/                          # Modèles générés (après preprocessing)
│   ├── user_item_matrix.npz
│   ├── mappings.pkl
│   ├── article_popularity.pkl
│   ├── user_profiles.json
│   ├── embeddings_filtered.pkl
│   ├── articles_metadata.csv
│   └── preprocessing_stats.json
│
├── azure_function/                          # Azure Function
│   ├── __init__.py           # Handler principal
│   ├── recommendation_engine.py     # Moteur de recommandation
│   ├── config.py                    # Configuration
│   ├── utils.py                     # Utilitaires
│   ├── requirements.txt             # Dépendances Azure Functions
│   └── deploy.sh                    # Script de déploiement
│
├── app/                             # Application Streamlit
│   ├── streamlit_app.py             # Interface utilisateur
│   └── requirements.txt             # Dépendances Streamlit
│
└── docs/                            # Documentation
    ├── architecture_technique.md
    └── architecture_cible.md
```

## 🔧 Configuration Azure

### Variables d'environnement Azure Functions

Configurez ces variables dans votre Azure Function:

```
AZURE_STORAGE_CONTAINER=my-content-reco-container
MODELS_PREFIX=models/
LOG_LEVEL=INFO
```

### Permissions Azure RBAC

La Azure Function nécessite les permissions suivantes:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "Microsoft.Storage/storageAccounts/blobServices/containers/blobs/read",
        "Microsoft.Storage/storageAccounts/blobServices/containers/read"
      ],
      "Resource": [
        "mycontent-models container/*",
        "mycontent-models container"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "Azure Application Insights workspace"
    }
  ]
}
```

## 🎓 Algorithme de Recommandation

### 1. Filtrage Collaboratif (User-based)
- Calcule la similarité cosinus entre utilisateurs
- Identifie les k=50 utilisateurs les plus similaires
- Agrège leurs articles avec pondération par similarité

### 2. Filtrage Basé sur le Contenu
- Calcule l'embedding moyen des articles lus par l'utilisateur
- Trouve les articles similaires via similarité cosinus
- Exclut les articles déjà lus

### 3. Filtrage par Tendances/Popularité
- Recommande les articles les plus populaires globalement
- Basé sur le nombre total de clics/interactions
- Exclut les articles déjà lus par l'utilisateur

### 4. Approche Hybride à 3 Coefficients
Le système combine les trois approches avec des poids configurables:

```
score_final = w_collab × score_collab + w_content × score_content + w_trend × score_trend
```

**Valeurs par défaut:** `w_collab=3, w_content=2, w_trend=1`
- Les poids sont normalisés automatiquement (ratio 3:2:1 = 50%:33%:17%)
- Permet d'équilibrer personnalisation (collaborative/content) et découverte (tendances)
- Les articles populaires/récents sont toujours présents dans les recommandations

### 5. Gestion du Cold Start
- Nouveaux utilisateurs: recommandations basées sur la popularité (100%)
- Nouveaux articles: utilisation pure du content-based

### 6. Filtre de Diversité
- Assure une variété de catégories dans les recommandations
- Évite la sur-représentation d'une catégorie
- Applique une sélection round-robin par catégorie

## 📈 Métriques et Performance

### Temps de réponse
- **Cold start Azure Functions:** ~3-5 secondes (première invocation)
- **Warm Azure Functions:** ~1-2 secondes (invocations suivantes)
- **Local:** ~0.5-1 seconde

### Consommation ressources
- **Azure Functions Memory:** 512-1024 MB recommandé
- **Azure Blob Storage Storage:** ~350 MB (modèles)
- **Package Azure Functions:** ~150 MB (avec dépendances)

### Sparsité de la matrice
- **Utilisateurs actifs:** Dépend du seuil (défaut: ≥5 interactions)
- **Sparsité:** Généralement >99%
- **Matrice stockée:** Format sparse (CSR) pour optimisation mémoire

## 🚧 Limitations Actuelles

1. **Données statiques:** Pas de mise à jour en temps réel des interactions
2. **Cold start Azure Functions:** Première invocation lente (~5s)
3. **Langue:** Dataset en portugais (Globo.com Brésil)
4. **Scalabilité:** MVP conçu pour démonstration, pas production à grande échelle
5. **CPU uniquement:** Pas d'utilisation de GPU pour le moment

## 🔮 Architecture Cible (Évolutions Futures)

### Améliorations techniques
- **Streaming:** Azure Kinesis pour interactions temps réel
- **Cache:** ElastiCache (Redis) pour réponses instantanées
- **API Gateway:** Gestion avancée des APIs (throttling, auth)
- **Retraining:** Pipeline automatisé (Azure SageMaker)
- **Monitoring:** CloudWatch Dashboards et alertes

### Améliorations ML
- **Deep Learning:** Neural Collaborative Filtering (NCF)
- **Contextual Embeddings:** BERT/transformers pour meilleure représentation
- **Sequential Patterns:** LSTM/GRU pour modéliser séquences de lecture
- **Multi-armed Bandits:** Exploration-exploitation pour nouveaux contenus
- **A/B Testing:** Framework d'expérimentation

### Nouvelles fonctionnalités
- **Feedback explicite:** Système de ratings (like/dislike)
- **Profil utilisateur:** Sélection de catégories favorites
- **Temporal features:** Recommandations selon heure/jour
- **Social features:** Partage, commentaires, following
- **Multi-device:** Synchronisation entre appareils
- **Notifications:** Push notifications pour nouveaux contenus

## 🤝 Contribution

Ce projet est un MVP développé dans un contexte éducatif. Pour toute question ou suggestion:

1. Ouvrir une issue sur GitHub
2. Proposer une pull request
3. Contacter l'équipe My Content

## 📄 Licence

Ce projet est développé dans le cadre d'un projet éducatif.

## 👥 Équipe

- **CTO & Co-fondateur:** Développement système et architecture
- **Samia (CEO):** Vision produit et stratégie
- **Julien:** Conseil architecture serverless

## 📚 Références

### Articles académiques
- [Personalized News Recommendation: Methods and Challenges](https://arxiv.org/pdf/2106.08934)
- [A Survey of Personalized News Recommendation](https://link.springer.com/article/10.1007/s41019-023-00228-5)
- [Embedding in Recommender Systems: A Survey](https://arxiv.org/pdf/2310.18608)

### Cold Start Problem
- [Cold Start Problem in Recommender Systems](https://www.freecodecamp.org/news/cold-start-problem-in-recommender-systems/)
- [User Cold Start Problem: A Systematic Review (IEEE)](https://ieeexplore.ieee.org/document/10339320/)

### Systèmes hybrides
- [Deep Learning Based Hybrid Recommendation Model](https://www.nature.com/articles/s41598-024-79011-z)
- [Introduction to Embedding-Based Recommender Systems](https://towardsdatascience.com/introduction-to-embedding-based-recommender-systems-956faceb1919/)

## 🔗 Liens Utiles

- [Azure Functions Documentation](https://learn.microsoft.com/en-us/azure/azure-functions/)
- [Azure Blob Storage Documentation](https://learn.microsoft.com/en-us/azure/storage/blobs/)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [Scikit-learn Documentation](https://scikit-learn.org/)

---

**Version:** 1.0.0 (MVP)
**Dernière mise à jour:** Décembre 2025
**Status:** ✅ Opérationnel
