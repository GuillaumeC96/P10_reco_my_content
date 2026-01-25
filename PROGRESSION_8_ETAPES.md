# Progression des 8 Étapes - Déploiement Azure & Optimisations

**Date de début:** 25 Décembre 2024
**Projet:** P10 My Content - Système de Recommandation

---

## 📊 Vue d'ensemble

| # | Étape | Status | Temps estimé | Dépendances |
|---|-------|--------|--------------|-------------|
| 1 | Adapter code Lambda → Azure Function | ✅ **TERMINÉ** | 30 min | - |
| 2 | Créer Azure Function App | ⏳ **EN COURS** | 10 min | Étape 1 |
| 3 | Upload modèles vers Blob Storage | ⏸️ Pending | 15 min | Étape 2 |
| 4 | Tester déploiement Azure | ⏸️ Pending | 10 min | Étape 3 |
| 5 | Créer présentation PowerPoint PDF | ⏸️ Pending | 60 min | - |
| 6 | A/B testing (paramètres niveau 2) | ⏸️ Pending | 30 min | Étape 4 |
| 7 | Monitoring Azure Application Insights | ⏸️ Pending | 20 min | Étape 4 |
| 8 | Cache Redis pour latency | ⏸️ Pending | 45 min | Étape 4 |

**Temps total estimé:** ~3h 40min
**Progression:** 12.5% (1/8 étapes)

---

## ✅ ÉTAPE 1 : Adapter code Lambda → Azure Function (TERMINÉ)

### Ce qui a été fait

**1. Structure Azure Function créée**
```
azure_function/
├── RecommendationFunction/
│   ├── __init__.py              ✅ Converti depuis lambda_function.py
│   └── function.json            ✅ Config HTTP trigger
├── recommendation_engine.py     ✅ Copié depuis lambda/
├── utils.py                     ✅ Copié depuis lambda/
├── config.py                    ✅ Adapté pour Azure
├── requirements.txt             ✅ Dépendances Azure
├── host.json                    ✅ Config globale
├── local.settings.json          ✅ Config locale
├── .gitignore                   ✅ Fichiers ignorés
├── .funcignore                  ✅ Exclusions déploiement
├── deploy_azure.sh              ✅ Script automatisé
└── README_AZURE_DEPLOYMENT.md   ✅ Guide complet
```

**2. Conversions effectuées**

| AWS Lambda | Azure Function | Status |
|------------|----------------|--------|
| `lambda_handler(event, context)` | `main(req: func.HttpRequest)` | ✅ |
| `event['body']` | `req.get_json()` | ✅ |
| `event['queryStringParameters']` | `req.params.get()` | ✅ |
| `boto3` (S3) | `azure-storage-blob` | ✅ |
| `/tmp/models` | `/home/site/wwwroot/models` | ✅ |
| `requirements.txt` (boto3) | `requirements.txt` (azure-functions) | ✅ |

**3. Paramètres optimaux intégrés**

```python
# config.py - Paramètres optimaux du 18 Décembre 2024
DEFAULT_WEIGHT_COLLAB = 0.714   # 71.4% (5/7)
DEFAULT_WEIGHT_CONTENT = 0.143  # 14.3% (1/7)
DEFAULT_WEIGHT_TREND = 0.143    # 14.3% (1/7)

# Amélioration Phase 1
USE_WEIGHTED_MATRIX = True
USE_WEIGHTED_AGGREGATION = True
USE_TEMPORAL_DECAY = True
DECAY_HALF_LIFE_DAYS = 7.0
```

**4. Documentation créée**
- ✅ `README_AZURE_DEPLOYMENT.md` (guide complet 500+ lignes)
- ✅ `PARAMETRES_OPTIMISATION.md` (détail optimisation bayésienne)
- ✅ `deploy_azure.sh` (script automatisé 8 étapes)

---

## ⏳ ÉTAPE 2 : Créer Azure Function App (EN COURS)

### Prérequis

**À installer sur votre machine :**

1. **Azure CLI**
```bash
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
az --version
az login
```

2. **Azure Functions Core Tools**
```bash
wget -q https://packages.microsoft.com/config/ubuntu/$(lsb_release -rs)/packages-microsoft-prod.deb
sudo dpkg -i packages-microsoft-prod.deb
sudo apt-get update
sudo apt-get install azure-functions-core-tools-4
func --version
```

3. **Compte Azure**
- Créer compte gratuit : https://azure.microsoft.com/fr-fr/free/
- 12 mois gratuits + 200$ de crédit

### Méthode automatisée (RECOMMANDÉ)

```bash
cd /home/ser/Bureau/P10_reco_new/azure_function
./deploy_azure.sh
```

**Le script fait automatiquement :**
1. ✓ Vérification des prérequis
2. ✓ Création resource group `rg-mycontent`
3. ✓ Création storage account `samycontent`
4. ✓ Création conteneur Blob `models`
5. ✓ Upload modèles (121 MB)
6. ✓ Création Function App `func-mycontent-reco`
7. ✓ Configuration variables environnement
8. ✓ Déploiement du code

**Temps estimé :** 10-15 minutes

### Méthode manuelle (étape par étape)

```bash
# 1. Créer resource group
az group create --name rg-mycontent --location westeurope

# 2. Créer storage account
az storage account create \
  --name samycontent \
  --resource-group rg-mycontent \
  --location westeurope \
  --sku Standard_LRS

# 3. Créer Function App (Consumption Plan = GRATUIT)
az functionapp create \
  --name func-mycontent-reco \
  --resource-group rg-mycontent \
  --storage-account samycontent \
  --runtime python \
  --runtime-version 3.9 \
  --functions-version 4 \
  --os-type Linux \
  --consumption-plan-location westeurope
```

**Coût estimé :** 0€ (dans les limites gratuites)

---

## ⏸️ ÉTAPE 3 : Upload modèles vers Blob Storage

### Fichiers à uploader (121 MB total)

```bash
models/
├── user_item_matrix.npz              4.4 MB   ✓ Requis
├── user_item_matrix_weighted.npz     9.2 MB   ✓ Requis (OPTIMAL)
├── embeddings_filtered.pkl           38 MB    ✓ Requis
├── article_popularity.pkl            1.5 MB   ✓ Requis
├── mappings.pkl                      3.2 MB   ✓ Requis
├── user_profiles.json                64 MB    ✓ Requis
├── user_profiles_enriched.json       64 MB    ✓ Requis (OPTIMAL)
├── articles_metadata.csv             11 MB    ✓ Requis
└── preprocessing_stats.json          247 B    ✓ Requis
```

### Commande d'upload

```bash
# Récupérer connection string
CONNECTION_STRING=$(az storage account show-connection-string \
  --name samycontent \
  --resource-group rg-mycontent \
  --query connectionString \
  --output tsv)

# Upload batch
cd /home/ser/Bureau/P10_reco_new
az storage blob upload-batch \
  --destination models \
  --source ./models \
  --connection-string "$CONNECTION_STRING"

# Vérifier
az storage blob list \
  --container-name models \
  --connection-string "$CONNECTION_STRING" \
  --output table
```

**Temps estimé :** 5-15 minutes (selon connexion)

---

## ⏸️ ÉTAPE 4 : Tester déploiement Azure

### Tests à effectuer

**1. Health Check**
```bash
FUNCTION_URL="https://func-mycontent-reco.azurewebsites.net/api/recommend"
curl -X GET "$FUNCTION_URL"
```

**2. Recommandation simple (user_id=5)**
```bash
curl -X GET "$FUNCTION_URL?user_id=5&n_recommendations=5"
```

**3. Recommandation avec paramètres optimaux (5:1:1)**
```bash
curl -X GET "$FUNCTION_URL?user_id=100&n_recommendations=10&weight_collab=5&weight_content=1&weight_trend=1"
```

**4. Requête POST (JSON)**
```bash
curl -X POST "$FUNCTION_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 100,
    "n_recommendations": 5,
    "weight_collab": 5,
    "weight_content": 1,
    "weight_trend": 1
  }'
```

**5. Test de performance (latency)**
```bash
for i in {1..10}; do
  time curl -s -X GET "$FUNCTION_URL?user_id=$i&n_recommendations=5" > /dev/null
done
```

**Métriques attendues :**
- Cold start (1ère requête) : 3-5 secondes
- Warm (requêtes suivantes) : 0.7-1.0 seconde
- HR@5 : 7.0% (500 users)
- Diversity : 1.0 (5/5 catégories)

**Temps estimé :** 10 minutes

---

## ⏸️ ÉTAPE 5 : Créer présentation PowerPoint PDF

### Contenu préparé

✅ **Fichier source :** `CONTENU_PRESENTATION.md` (27 slides)

### Structure des slides

**Introduction (3 slides)**
1. Page de titre
2. Contexte & problématique
3. Fonctionnalité cible

**Dataset & Application (3 slides)**
4. Dataset Globo.com
5. Description fonctionnelle
6. Démo interface

**Analyse des Modèles (6 slides)** ⭐ EXIGENCE CLÉ
7. Approches analysées
8. Collaborative Filtering
9. Content-Based Filtering
10. Approche Hybride
11. Comparaison tableau
12. Architecture MVP

**Architecture & Système (6 slides)** ⭐ EXIGENCE CLÉ
13. Composants techniques
14. Algorithme recommandation
15. Gestion Cold Start
16. Déploiement serverless
17. Scripts déploiement
18. Métriques & performance

**Architecture Cible (6 slides)** ⭐ EXIGENCE CLÉ
19. Vision architecture
20. Schéma architecture cible
21. Nouveaux utilisateurs
22. Nouveaux articles
23. Améliorations ML
24. Monitoring

**Conclusion (3 slides)**
25. Roadmap
26. Accomplissements
27. Questions & Démo

### Actions à faire

1. **Ouvrir PowerPoint / Google Slides**
2. **Copier-coller** le contenu de `CONTENU_PRESENTATION.md`
3. **Ajouter visuels** (schémas, graphiques, icônes)
4. **Exporter en PDF** : `Cassez_Guillaume_3_presentation_122024.pdf`

### Visuels à créer

**Schéma 1 : Architecture MVP**
```
[Streamlit App] → [Azure Function] → [Recommendation Engine]
                         ↓
                  [Blob Storage]
              (models, embeddings)
```

**Schéma 2 : Système Hybride**
```
Input: user_id
   ↓
[Collaborative 71%] ─┐
[Content-Based 14%] ─┼→ [Hybrid Score] → Top 5
[Popularity 14%]    ─┘
   ↓
[Diversity Filter (Round-Robin)]
   ↓
Output: 5 articles (5 catégories différentes)
```

**Graphique : Résultats Benchmark**
```
HR@5 (500 users):
Popular:     ████████ 8.6%
Hybrid:      ███████  7.0%  ← NOTRE SYSTÈME
Content:     █        1.2%
Collaborative:        0.0%
```

**Temps estimé :** 45-60 minutes

---

## ⏸️ ÉTAPE 6 : A/B testing (paramètres niveau 2)

### Objectif

Comparer les performances de **3 configurations** en production :

| Config | Collab | Content | Trend | Score théorique |
|--------|--------|---------|-------|-----------------|
| **A (OPTIMAL)** | 5 | 1 | 1 | 0.2135 🥇 |
| B (Alternatif 1) | 5 | 1 | 2 | 0.2122 |
| C (Équilibré) | 3 | 3 | 2 | 0.1936 |

### Méthode

**1. Créer 3 versions de l'API**
```python
# Azure Function - Ajouter routing A/B
@app.route('/api/recommend_v1')  # Config A (5:1:1)
@app.route('/api/recommend_v2')  # Config B (5:1:2)
@app.route('/api/recommend_v3')  # Config C (3:3:2)
```

**2. Implémenter split trafic**
```python
import random

def get_ab_config(user_id):
    # Split 50% A, 25% B, 25% C
    variant = hash(user_id) % 4
    if variant == 0 or variant == 1:
        return "A", (5, 1, 1)
    elif variant == 2:
        return "B", (5, 1, 2)
    else:
        return "C", (3, 3, 2)
```

**3. Logger les métriques**
```python
# Application Insights custom metrics
from applicationinsights import TelemetryClient
tc = TelemetryClient('YOUR_INSTRUMENTATION_KEY')

tc.track_metric('recommendation_click_rate', click_rate, properties={
    'ab_variant': variant,
    'user_id': user_id
})
```

**4. Analyser résultats (7 jours)**
```kusto
customMetrics
| where name == "recommendation_click_rate"
| summarize avg(value) by tostring(customDimensions.ab_variant)
| order by avg_value desc
```

**Temps estimé :** 30 minutes setup + 7 jours collecte

---

## ⏸️ ÉTAPE 7 : Monitoring Azure Application Insights

### Créer Application Insights

```bash
# Créer ressource
az monitor app-insights component create \
  --app mycontent-insights \
  --location westeurope \
  --resource-group rg-mycontent \
  --application-type web

# Récupérer instrumentation key
INSTRUMENTATION_KEY=$(az monitor app-insights component show \
  --app mycontent-insights \
  --resource-group rg-mycontent \
  --query instrumentationKey \
  --output tsv)

# Connecter à Function App
az functionapp config appsettings set \
  --name func-mycontent-reco \
  --resource-group rg-mycontent \
  --settings APPINSIGHTS_INSTRUMENTATIONKEY=$INSTRUMENTATION_KEY
```

### Dashboards à créer

**1. Performance Dashboard**
- Temps de réponse moyen (target: <1s)
- Taux de réussite (target: >99%)
- Latency P50, P95, P99
- Cold start frequency

**2. Business Metrics Dashboard**
- Nombre de recommandations/jour
- Utilisateurs actifs
- Distribution des paramètres (collab/content/trend)
- Taux de diversité

**3. Alertes**
```bash
# Alerte si latency > 3s
az monitor metrics alert create \
  --name alert-latency-3s \
  --resource-group rg-mycontent \
  --scopes /subscriptions/.../func-mycontent-reco \
  --condition "avg ResponseTime > 3000" \
  --description "Latence > 3s"

# Alerte si erreurs > 5%
az monitor metrics alert create \
  --name alert-errors-5pct \
  --resource-group rg-mycontent \
  --condition "total FailedRequests / total TotalRequests > 0.05"
```

**Temps estimé :** 20 minutes

---

## ⏸️ ÉTAPE 8 : Cache Redis pour latency

### Objectif

Réduire latency de 0.77s → **0.1s** pour utilisateurs fréquents

### Architecture

```
Request → [Azure Function] → [Redis Cache] ?
                                  ↓ HIT (0.1s)
                                  ↓ MISS (0.8s)
                             [Recommendation Engine]
                                  ↓
                             [Store in Redis]
```

### Implémentation

**1. Créer Azure Cache for Redis**
```bash
az redis create \
  --name mycontent-redis \
  --resource-group rg-mycontent \
  --location westeurope \
  --sku Basic \
  --vm-size c0

# Récupérer connection string
REDIS_HOST=$(az redis show --name mycontent-redis --resource-group rg-mycontent --query hostName --output tsv)
REDIS_KEY=$(az redis list-keys --name mycontent-redis --resource-group rg-mycontent --query primaryKey --output tsv)
```

**2. Modifier Azure Function**
```python
import redis

# Connexion Redis
redis_client = redis.Redis(
    host=os.environ['REDIS_HOST'],
    port=6380,
    password=os.environ['REDIS_KEY'],
    ssl=True
)

def recommend_with_cache(user_id, params):
    # Clé unique par configuration
    cache_key = f"reco:{user_id}:{params['collab']}:{params['content']}:{params['trend']}"

    # Vérifier cache
    cached = redis_client.get(cache_key)
    if cached:
        logging.info(f"Cache HIT for {cache_key}")
        return json.loads(cached)

    # Cache MISS → Générer reco
    logging.info(f"Cache MISS for {cache_key}")
    recommendations = engine.recommend(user_id, **params)

    # Stocker dans cache (TTL 1 heure)
    redis_client.setex(cache_key, 3600, json.dumps(recommendations))

    return recommendations
```

**3. Configurer TTL par use case**
```python
TTL_CONFIG = {
    'frequent_users': 1800,    # 30 minutes
    'normal_users': 3600,      # 1 heure
    'cold_start': 7200,        # 2 heures (plus stable)
}
```

**4. Monitoring cache**
```python
# Métriques Redis
cache_hits = redis_client.info('stats')['keyspace_hits']
cache_misses = redis_client.info('stats')['keyspace_misses']
hit_rate = cache_hits / (cache_hits + cache_misses)

tc.track_metric('cache_hit_rate', hit_rate)
```

**Gains attendus :**
- Cache HIT : 0.1s (87% plus rapide)
- Cache MISS : 0.8s (identique)
- Hit rate attendu : 60-70% (utilisateurs fréquents)
- Latency moyenne : 0.3s (61% amélioration)

**Coût :** ~10€/mois (Redis Basic C0)

**Temps estimé :** 45 minutes

---

## 📊 Récapitulatif Final

### Temps total estimé

| Étape | Temps | Cumul |
|-------|-------|-------|
| 1. Adapter code | 30 min | 0h30 |
| 2. Créer Azure Function | 10 min | 0h40 |
| 3. Upload modèles | 15 min | 0h55 |
| 4. Tester déploiement | 10 min | 1h05 |
| 5. PowerPoint PDF | 60 min | 2h05 |
| 6. A/B testing | 30 min | 2h35 |
| 7. Monitoring | 20 min | 2h55 |
| 8. Redis cache | 45 min | 3h40 |

**TOTAL : ~3h40**

### Coûts Azure estimés

| Ressource | Plan | Coût/mois |
|-----------|------|-----------|
| Function App | Consumption | **0€** (1M exec gratuits) |
| Blob Storage | Standard | **0€** (5GB gratuits) |
| Application Insights | Basic | **0€** (5GB logs gratuits) |
| Redis Cache | Basic C0 | 10€ |
| **TOTAL** | | **~10€/mois** |

---

## ✅ Checklist Globale

**Étape 1 : Code Adapté**
- [x] Structure Azure Function créée
- [x] __init__.py converti
- [x] requirements.txt adapté
- [x] config.py avec paramètres optimaux
- [x] Guide déploiement créé
- [x] Script automatisé créé

**Étape 2-4 : Déploiement Azure**
- [ ] Compte Azure créé
- [ ] Azure CLI installé
- [ ] Resource group créé
- [ ] Function App créée
- [ ] Modèles uploadés (121 MB)
- [ ] Tests réussis (HR@5 = 7%)

**Étape 5 : Présentation**
- [ ] PowerPoint créé (27 slides)
- [ ] Visuels ajoutés (schémas)
- [ ] Export PDF
- [ ] Nomenclature OK (`Cassez_Guillaume_3_presentation_122024.pdf`)

**Étape 6-8 : Optimisations**
- [ ] A/B testing configuré
- [ ] Application Insights actif
- [ ] Redis cache implémenté
- [ ] Métriques collectées

---

**Dernière mise à jour :** 25 Décembre 2024
**Progression :** 1/8 étapes (12.5%)
**Prochaine étape :** Installer Azure CLI et déployer
