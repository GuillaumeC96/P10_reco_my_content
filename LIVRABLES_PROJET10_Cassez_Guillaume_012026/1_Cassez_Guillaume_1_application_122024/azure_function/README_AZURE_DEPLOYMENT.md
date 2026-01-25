# Guide de Déploiement Azure - My Content Recommendation System

**Date:** 25 Décembre 2024
**Platform:** Microsoft Azure Functions
**Converted from:** Azure Functions

---

## 📋 Vue d'ensemble

Ce guide vous accompagne pas à pas pour déployer le système de recommandation My Content sur **Microsoft Azure** en utilisant :
- **Azure Functions** (équivalent Azure Functions)
- **Azure Blob Storage** (équivalent Azure Blob Storage)
- **Consumption Plan** (gratuit jusqu'à 1M exécutions/mois)

---

## 🎯 Prérequis

### 1. Compte Azure
```bash
# Créer un compte gratuit (12 mois + 200$ de crédit)
https://azure.microsoft.com/fr-fr/free/
```

### 2. Azure CLI
```bash
# Installation sur Linux/Ubuntu
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

# Vérification
az --version

# Connexion
az login
```

### 3. Azure Functions Core Tools
```bash
# Installation sur Linux/Ubuntu
wget -q https://packages.microsoft.com/config/ubuntu/$(lsb_release -rs)/packages-microsoft-prod.deb
sudo dpkg -i packages-microsoft-prod.deb
sudo apt-get update
sudo apt-get install azure-functions-core-tools-4

# Vérification
func --version
```

### 4. Python 3.9+
```bash
python3 --version
# Doit afficher: Python 3.9.x ou supérieur
```

---

## 🚀 ÉTAPE 1 : Créer les ressources Azure (DÉJÀ FAIT ✅)

Le code Azure Functions a été converti en Azure Function. Tous les fichiers sont dans `azure_function/`.

### Structure créée
```
azure_function/
├── RecommendationFunction/
│   ├── __init__.py              # Handler principal (converti depuis __init__.py)
│   └── function.json            # Configuration HTTP trigger
├── recommendation_engine.py     # Moteur de recommandation (copié)
├── utils.py                     # Utilitaires (copié)
├── config.py                    # Configuration Azure (adapté)
├── requirements.txt             # Dépendances Azure
├── host.json                    # Config globale
├── local.settings.json          # Config locale (test)
├── .gitignore
└── .funcignore
```

### Différences clés Azure → Azure

| Azure Functions | Azure Function | Changement |
|------------|----------------|------------|
| `main(event, context)` | `main(req: func.HttpRequest)` | Signature fonction |
| `event['body']` | `req.get_json()` | Parsing body |
| `event['queryStringParameters']` | `req.params.get()` | Query params |
| `return {'statusCode': 200, ...}` | `func.HttpResponse(status_code=200, ...)` | Format réponse |
| `azure-storage-blob` (Azure Blob Storage) | `azure-storage-blob` | Client storage |
| `/tmp/models` | `/home/site/wwwroot/models` | Path modèles |

---

## 🚀 ÉTAPE 2 : Créer Azure Function App

### Option A : Via Azure CLI (Recommandé)

```bash
# 1. Créer un resource group
az group create \
  --name rg-mycontent \
  --location westeurope

# 2. Créer un storage account
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

# 4. Vérifier la création
az functionapp list --resource-group rg-mycontent --output table
```

### Option B : Via Portail Azure (Interface graphique)

1. **Accéder au portail** : https://portal.azure.com
2. **Créer une ressource** → Rechercher "Function App"
3. **Configuration** :
   - Resource Group : `rg-mycontent` (créer nouveau)
   - Nom : `func-mycontent-reco`
   - Publier : **Code**
   - Runtime : **Python 3.9**
   - Région : **West Europe**
   - Plan : **Consumption (Serverless)**
4. **Créer** et attendre le déploiement (~2 min)

---

## 🚀 ÉTAPE 3 : Upload modèles vers Blob Storage

### Créer le conteneur Blob

```bash
# Récupérer la connection string
CONNECTION_STRING=$(az storage account show-connection-string \
  --name samycontent \
  --resource-group rg-mycontent \
  --query connectionString \
  --output tsv)

# Créer le conteneur "models"
az storage container create \
  --name models \
  --connection-string "$CONNECTION_STRING" \
  --public-access off

# Vérifier
az storage container list \
  --connection-string "$CONNECTION_STRING" \
  --output table
```

### Upload des modèles

```bash
# Se placer dans le dossier du projet
cd /home/ser/Bureau/P10_reco_new

# Upload tous les fichiers du dossier models/
az storage blob upload-batch \
  --destination models \
  --source ./models \
  --connection-string "$CONNECTION_STRING" \
  --pattern "*.npz" \
  --pattern "*.pkl" \
  --pattern "*.json" \
  --pattern "*.csv"

# Vérifier les fichiers uploadés
az storage blob list \
  --container-name models \
  --connection-string "$CONNECTION_STRING" \
  --output table

# Afficher la taille totale
az storage blob list \
  --container-name models \
  --connection-string "$CONNECTION_STRING" \
  --query "[].{name:name, size:properties.contentLength}" \
  --output table
```

**Fichiers attendus** (~121 MB total) :
- `user_item_matrix.npz` (4.4 MB)
- `user_item_matrix_weighted.npz` (9.2 MB)
- `embeddings_filtered.pkl` (38 MB)
- `article_popularity.pkl` (1.5 MB)
- `mappings.pkl` (3.2 MB)
- `user_profiles.json` (64 MB)
- `user_profiles_enriched.json` (64 MB)
- `articles_metadata.csv` (11 MB)
- `preprocessing_stats.json` (247 B)

---

## 🚀 ÉTAPE 4 : Déployer Azure Function

### Option A : Déploiement direct depuis le code

```bash
# Se placer dans le dossier azure_function
cd /home/ser/Bureau/P10_reco_new/azure_function

# Installer les dépendances localement (test)
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Déployer sur Azure
func azure functionapp publish func-mycontent-reco

# Récupérer l'URL de la fonction
FUNCTION_URL=$(az functionapp function show \
  --resource-group rg-mycontent \
  --name func-mycontent-reco \
  --function-name RecommendationFunction \
  --query invokeUrlTemplate \
  --output tsv)

echo "HTTP Trigger URL: $FUNCTION_URL"
```

### Option B : Déploiement via ZIP

```bash
# Créer un package ZIP
cd /home/ser/Bureau/P10_reco_new/azure_function
zip -r ../function-app.zip .

# Déployer le ZIP
az functionapp deployment source config-zip \
  --resource-group rg-mycontent \
  --name func-mycontent-reco \
  --src ../function-app.zip
```

---

## 🚀 ÉTAPE 5 : Configuration des variables d'environnement

```bash
# Configurer les variables d'environnement
az functionapp config appsettings set \
  --name func-mycontent-reco \
  --resource-group rg-mycontent \
  --settings \
    STORAGE_ACCOUNT_NAME=samycontent \
    BLOB_CONTAINER_NAME=models \
    MODELS_PATH="/home/site/wwwroot/models" \
    LOG_LEVEL=INFO \
    ALLOWED_ORIGINS="*"

# Vérifier la configuration
az functionapp config appsettings list \
  --name func-mycontent-reco \
  --resource-group rg-mycontent \
  --output table
```

---

## 🧪 ÉTAPE 6 : Tester le déploiement

### Test 1 : Health Check

```bash
# Récupérer l'URL complète
FUNCTION_URL=$(az functionapp function show \
  --resource-group rg-mycontent \
  --name func-mycontent-reco \
  --function-name RecommendationFunction \
  --query invokeUrlTemplate \
  --output tsv)

# Test health check
curl -X GET "$FUNCTION_URL"
```

**Réponse attendue :**
```json
{
  "error": "Le paramètre user_id est requis",
  "example_url": "/api/RecommendationFunction?user_id=123&n_recommendations=5"
}
```

### Test 2 : Recommandation simple

```bash
# Test avec user_id=5
curl -X GET "$FUNCTION_URL?user_id=5&n_recommendations=5"
```

**Réponse attendue :**
```json
{
  "user_id": 5,
  "n_recommendations": 5,
  "recommendations": [
    {
      "article_id": 123456,
      "score": 0.87,
      "category_id": 789,
      ...
    },
    ...
  ],
  "parameters": {
    "weight_collab": 3.0,
    "weight_content": 2.0,
    "weight_trend": 1.0,
    "weights_ratio": "3.0:2.0:1.0",
    "use_diversity": true
  },
  "metadata": {
    "engine_loaded": true,
    "platform": "Azure Functions"
  }
}
```

### Test 3 : Recommandation avec paramètres optimaux

```bash
# Utiliser les paramètres optimaux identifiés (5:1:1)
curl -X GET "$FUNCTION_URL?user_id=5&n_recommendations=5&weight_collab=5&weight_content=1&weight_trend=1"
```

### Test 4 : Requête POST (JSON body)

```bash
curl -X POST "$FUNCTION_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 100,
    "n_recommendations": 10,
    "weight_collab": 5,
    "weight_content": 1,
    "weight_trend": 1
  }'
```

---

## 📊 ÉTAPE 7 : Monitoring avec Application Insights

### Activer Application Insights

```bash
# Créer Application Insights
az monitor app-insights component create \
  --app mycontent-insights \
  --location westeurope \
  --resource-group rg-mycontent \
  --application-type web

# Récupérer l'instrumentation key
INSTRUMENTATION_KEY=$(az monitor app-insights component show \
  --app mycontent-insights \
  --resource-group rg-mycontent \
  --query instrumentationKey \
  --output tsv)

# Connecter à la Function App
az functionapp config appsettings set \
  --name func-mycontent-reco \
  --resource-group rg-mycontent \
  --settings APPINSIGHTS_INSTRUMENTATIONKEY=$INSTRUMENTATION_KEY
```

### Consulter les logs

1. **Portail Azure** → Function App → Monitor → Logs
2. **Application Insights** → Logs → Query

**Exemple de query :**
```kusto
requests
| where timestamp > ago(1h)
| summarize count() by resultCode
| order by count_ desc
```

---

## 💰 Vérifier les coûts (IMPORTANT !)

### Option 1 : CLI

```bash
# Voir la consommation du resource group
az consumption usage list \
  --start-date $(date -d '7 days ago' +%Y-%m-%d) \
  --end-date $(date +%Y-%m-%d) \
  --query "[?contains(instanceName, 'mycontent')]" \
  --output table
```

### Option 2 : Portail Azure

1. **Portail** → Cost Management + Billing
2. **Cost Analysis** → Filtrer par resource group `rg-mycontent`
3. **Vérifier quotidiennement** pendant la première semaine

### **IMPORTANT - Limites gratuites Azure :**
- **Function App (Consumption)** : 1M exécutions/mois GRATUITES
- **Blob Storage** : 5 GB GRATUITS
- **Bandwidth** : 5 GB sortant/mois GRATUITS

**Au-delà :**
- Exécutions supplémentaires : ~0.17€ par million
- Storage : ~0.02€ par GB/mois
- Bandwidth : ~0.08€ par GB

### Configurer des alertes de coût

```bash
# Créer une alerte si coût > 5€
az monitor metrics alert create \
  --name alert-cost-5euros \
  --resource-group rg-mycontent \
  --condition "total cost > 5" \
  --description "Alerte si coût dépasse 5€"
```

---

## 🛑 ARRÊTER / SUPPRIMER les ressources

### Arrêter temporairement (conserve les données)

```bash
# Arrêter la Function App
az functionapp stop \
  --name func-mycontent-reco \
  --resource-group rg-mycontent
```

### Supprimer complètement (TOUT effacer)

```bash
# ATTENTION : Supprime TOUTES les ressources du resource group
az group delete \
  --name rg-mycontent \
  --yes \
  --no-wait
```

---

## 🔧 Dépannage

### Erreur : "Module 'azure.functions' not found"

```bash
# Vérifier requirements.txt dans le déploiement
func azure functionapp list-functions func-mycontent-reco
```

### Erreur : "Models not found"

1. Vérifier que les modèles sont dans Blob Storage
```bash
az storage blob list --container-name models --connection-string "$CONNECTION_STRING"
```

2. Vérifier les permissions
```bash
az storage container show-permission --name models --connection-string "$CONNECTION_STRING"
```

### Performance lente (> 5s)

- **Cold start** : Première invocation prend ~3-5s (normal)
- **Warmup** : Après 1ère invocation, descend à ~0.8s
- **Solution** : Utiliser Azure Functions Premium Plan (pas gratuit)

---

## 📱 Intégration avec Streamlit

Modifier `app/streamlit_app.py` pour pointer vers Azure :

```python
# Remplacer
AZURE_FUNCTION_URL = "https://func-mycontent-reco.azurewebsites.net/api/recommend"

# Dans la fonction call_recommendation()
response = requests.get(
    AZURE_FUNCTION_URL,
    params={
        'user_id': user_id,
        'n_recommendations': n,
        'weight_collab': collab,
        'weight_content': content,
        'weight_trend': trend
    }
)
```

---

## 📚 Ressources supplémentaires

**Documentation officielle :**
- [Azure Functions Python](https://learn.microsoft.com/en-us/azure/azure-functions/functions-reference-python)
- [Azure Blob Storage Python SDK](https://learn.microsoft.com/en-us/azure/storage/blobs/storage-quickstart-blobs-python)
- [Azure Cost Management](https://learn.microsoft.com/en-us/azure/cost-management-billing/)

**Tutoriels :**
- [Déployer une fonction Python](https://learn.microsoft.com/en-us/azure/azure-functions/create-first-function-cli-python)
- [Configurer Consumption Plan](https://learn.microsoft.com/en-us/azure/azure-functions/consumption-plan)

---

## ✅ Checklist finale

- [ ] Compte Azure créé (gratuit)
- [ ] Azure CLI installé
- [ ] Azure Functions Core Tools installé
- [ ] Resource group créé (`rg-mycontent`)
- [ ] Storage account créé (`samycontent`)
- [ ] Function App créée (`func-mycontent-reco`)
- [ ] Conteneur Blob créé (`models`)
- [ ] Modèles uploadés vers Blob Storage (121 MB)
- [ ] Code déployé vers Function App
- [ ] Variables d'environnement configurées
- [ ] Test 1 : Health check OK
- [ ] Test 2 : Recommandation simple OK
- [ ] Test 3 : Paramètres optimaux (5:1:1) OK
- [ ] Application Insights activé
- [ ] Alerte de coût configurée (5€)
- [ ] Streamlit modifié pour pointer vers Azure
- [ ] Monitoring quotidien configuré

---

**Créé le :** 25 Décembre 2024
**Status :** Guide complet prêt pour déploiement
**Temps estimé :** 30-45 minutes pour déploiement complet
**Coût estimé :** 0€ (dans les limites gratuites)
