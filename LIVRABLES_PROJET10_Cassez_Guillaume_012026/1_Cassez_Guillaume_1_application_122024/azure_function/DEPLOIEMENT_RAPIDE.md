# Déploiement Rapide Azure - 26 Décembre 2024

**Configuration optimale:** Trial 17 (+25.9% vs baseline)
**Paramètres:** Trend pur à 100% (collaborative et content inutiles)

---

## 🎯 PRÉREQUIS

### 1. Azure CLI installé et connecté
```bash
az --version
az login
```

### 2. Azure Functions Core Tools
```bash
func --version
```

### 3. Compte Azure actif
- Subscription ID disponible
- Ressource Group créé (ou à créer)

---

## 🚀 DÉPLOIEMENT EN 5 ÉTAPES

### ÉTAPE 1: Créer les ressources Azure

```bash
# Variables
RESOURCE_GROUP="rg-mycontent-reco"
LOCATION="francecentral"  # Ou "westeurope"
STORAGE_ACCOUNT="samycontent"  # Doit être unique globalement
FUNCTION_APP="func-mycontent-reco"

# 1. Créer le Resource Group
az group create \
  --name $RESOURCE_GROUP \
  --location $LOCATION

# 2. Créer le Storage Account (pour les modèles)
az storage account create \
  --name $STORAGE_ACCOUNT \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --sku Standard_LRS \
  --kind StorageV2

# 3. Créer le Function App (Consumption Plan)
az functionapp create \
  --name $FUNCTION_APP \
  --resource-group $RESOURCE_GROUP \
  --storage-account $STORAGE_ACCOUNT \
  --consumption-plan-location $LOCATION \
  --runtime python \
  --runtime-version 3.9 \
  --functions-version 4 \
  --os-type Linux
```

### ÉTAPE 2: Créer le conteneur Blob

```bash
# Récupérer la connection string
CONN_STRING=$(az storage account show-connection-string \
  --name $STORAGE_ACCOUNT \
  --resource-group $RESOURCE_GROUP \
  --output tsv)

# Créer le conteneur
az storage container create \
  --name models \
  --connection-string $CONN_STRING \
  --public-access off
```

### ÉTAPE 3: Upload des modèles (121 MB)

```bash
# Depuis le dossier P10_reco_new/
cd /home/ser/Bureau/P10_reco_new

# Upload tous les fichiers du dossier models/
az storage blob upload-batch \
  --destination models \
  --source ./models \
  --connection-string $CONN_STRING \
  --pattern "*.csv" \
  --pattern "*.json" \
  --pattern "*.npz"

# Vérifier
az storage blob list \
  --container-name models \
  --connection-string $CONN_STRING \
  --output table
```

**Fichiers à uploader:**
- user_item_matrix.npz (82 MB)
- user_item_matrix_weighted.npz (82 MB) ← **IMPORTANT**
- user_profiles_enriched.json (19 MB)
- articles_embeddings.npz (11 MB)
- articles_metadata.csv (34 MB)
- popularity_scores.json (8 MB)
- user_mapping.json, item_mapping.json

### ÉTAPE 4: Configurer les variables d'environnement

```bash
# Configurer le Storage Account dans la Function App
az functionapp config appsettings set \
  --name $FUNCTION_APP \
  --resource-group $RESOURCE_GROUP \
  --settings \
    "STORAGE_ACCOUNT_NAME=$STORAGE_ACCOUNT" \
    "BLOB_CONTAINER_NAME=models" \
    "BLOB_MODELS_PREFIX="
```

### ÉTAPE 5: Déployer le code

```bash
# Depuis le dossier azure_function/
cd /home/ser/Bureau/P10_reco_new/azure_function

# Déployer
func azure functionapp publish $FUNCTION_APP

# Récupérer l'URL
FUNCTION_URL=$(az functionapp show \
  --name $FUNCTION_APP \
  --resource-group $RESOURCE_GROUP \
  --query "defaultHostName" \
  --output tsv)

echo "HTTP Trigger URL: https://$FUNCTION_URL"
```

---

## 🧪 TESTER LE DÉPLOIEMENT

### Test 1: Health Check

```bash
curl https://$FUNCTION_URL/api/RecommendationFunction \
  -H "Content-Type: application/json" \
  -d '{}'
```

**Réponse attendue:** Erreur 400 (normal, user_id manquant)

### Test 2: Recommandation pour utilisateur

```bash
curl https://$FUNCTION_URL/api/RecommendationFunction \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 123,
    "n": 5
  }'
```

**Réponse attendue:**
```json
{
  "user_id": 123,
  "recommendations": [
    {"article_id": 456, "score": 0.95, "title": "..."},
    {"article_id": 789, "score": 0.92, "title": "..."},
    ...
  ],
  "weights": {
    "collaborative": 0.0,
    "content": 0.0,
    "trend": 1.0
  }
}
```

### Test 3: Vérifier les logs

```bash
az functionapp log tail \
  --name $FUNCTION_APP \
  --resource-group $RESOURCE_GROUP
```

---

## ⚙️ CONFIGURATION OPTIMALE (déjà dans config.py)

**Niveau 2 - Stratégie hybride:**
```python
DEFAULT_WEIGHT_COLLAB = 0.0   # Collaborative inutile
DEFAULT_WEIGHT_CONTENT = 0.0  # Content inutile
DEFAULT_WEIGHT_TREND = 1.0    # Trend optimal à 100%
```

**Niveau 1 - Interaction weights:**
```python
OPTIMAL_INTERACTION_WEIGHTS = {
    'w_time': 0.410,      # 41% - Plus important
    'w_clicks': 0.243,    # 24%
    'w_session': 0.104,   # 10%
    'w_region': 0.066,    # 7% - Important
    'w_device': 0.060,    # 6%
    'w_env': 0.046,       # 5%
    'w_os': 0.034,        # 3%
    'w_referrer': 0.031,  # 3%
    'w_country': 0.007    # 1% - Quasi inutile
}
```

---

## 📊 MÉTRIQUES ATTENDUES

Avec les nouveaux paramètres optimaux:
- **Score composite:** 0.2673 (+25.9% vs baseline)
- **HR@5 attendu:** ~8.8% (vs 7.0% baseline)
- **NDCG@10 attendu:** ~0.35 (vs ~0.28)

---

## 🔧 DÉPANNAGE

### Problème: Function App ne démarre pas

```bash
# Vérifier les logs
az functionapp log tail \
  --name $FUNCTION_APP \
  --resource-group $RESOURCE_GROUP

# Vérifier la configuration
az functionapp config show \
  --name $FUNCTION_APP \
  --resource-group $RESOURCE_GROUP
```

### Problème: Modèles non trouvés

```bash
# Vérifier que les blobs existent
az storage blob list \
  --container-name models \
  --connection-string $CONN_STRING \
  --output table

# Vérifier les permissions
az storage container show-permission \
  --name models \
  --connection-string $CONN_STRING
```

### Problème: Out of memory

**Solution:** Augmenter le plan (actuellement Consumption)
```bash
# Passer à Premium plan (plus cher mais plus de RAM)
az functionapp plan create \
  --name premium-plan \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --sku EP1  # Elastic Premium 1 (3.5GB RAM)
```

---

## 💰 COÛTS ESTIMÉS

**Consumption Plan (actuel):**
- 1M exécutions gratuites/mois
- GB-s gratuits: 400,000
- **Coût estimé:** 0€ pour usage modéré

**Storage Account:**
- Stockage: 121 MB × 0.02€/GB/mois = ~0.002€/mois
- Transactions: ~0.01€/mois
- **Total:** < 0.05€/mois

**TOTAL:** < 1€/mois pour usage normal

---

## 🎓 COMMANDES UTILES

```bash
# Lister toutes les Function Apps
az functionapp list --output table

# Supprimer tout (cleanup)
az group delete --name $RESOURCE_GROUP --yes

# Restart la Function App
az functionapp restart \
  --name $FUNCTION_APP \
  --resource-group $RESOURCE_GROUP

# Afficher l'URL
az functionapp show \
  --name $FUNCTION_APP \
  --resource-group $RESOURCE_GROUP \
  --query "defaultHostName" \
  --output tsv
```

---

## ✅ CHECKLIST DE DÉPLOIEMENT

- [ ] Azure CLI installé et connecté
- [ ] Resource Group créé
- [ ] Storage Account créé
- [ ] Function App créée (Consumption Plan)
- [ ] Conteneur Blob "models" créé
- [ ] 121 MB de modèles uploadés vers Blob
- [ ] Variables d'environnement configurées
- [ ] Code déployé avec `func azure functionapp publish`
- [ ] Test health check réussi
- [ ] Test recommandation réussi
- [ ] Logs vérifiés (pas d'erreurs)
- [ ] URL de production documentée

---

**Créé:** 26 Décembre 2024
**Optimisation:** Trial 17 (Trend pur 100%)
**Score:** 0.2673 (+25.9% vs baseline)
