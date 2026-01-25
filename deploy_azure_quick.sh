#!/bin/bash
# Script de déploiement rapide Azure - My Content
# Conforme au cahier des charges (équivalent AWS Lambda)

set -e  # Arrêter en cas d'erreur

echo "========================================"
echo "DÉPLOIEMENT AZURE - MY CONTENT"
echo "Conforme cahier des charges"
echo "========================================"
echo ""

# Vérifier les prérequis
echo "1. Vérification des prérequis..."
command -v az >/dev/null 2>&1 || { echo "✗ Azure CLI non installé"; exit 1; }
command -v func >/dev/null 2>&1 || { echo "✗ Azure Functions Core Tools non installé"; exit 1; }
echo "   ✓ Azure CLI OK"
echo "   ✓ Azure Functions Core Tools OK"

# Connexion Azure
echo ""
echo "2. Connexion à Azure..."
az account show >/dev/null 2>&1 || {
    echo "   Connexion requise..."
    az login
}
echo "   ✓ Connecté à Azure"

# Configuration
echo ""
echo "3. Configuration du déploiement..."
echo ""
echo "Entrez les informations suivantes:"
read -p "   Resource Group [rg-mycontent-prod]: " RESOURCE_GROUP
RESOURCE_GROUP=${RESOURCE_GROUP:-rg-mycontent-prod}

read -p "   Location [francecentral]: " LOCATION
LOCATION=${LOCATION:-francecentral}

read -p "   Storage Account [samycontentprod]: " STORAGE_ACCOUNT
STORAGE_ACCOUNT=${STORAGE_ACCOUNT:-samycontentprod}

read -p "   Function App [func-mycontent-reco]: " FUNCTION_APP
FUNCTION_APP=${FUNCTION_APP:-func-mycontent-reco}

echo ""
echo "Configuration:"
echo "  Resource Group: $RESOURCE_GROUP"
echo "  Location: $LOCATION"
echo "  Storage: $STORAGE_ACCOUNT"
echo "  Function: $FUNCTION_APP"
echo ""
read -p "Confirmer ? (y/N): " CONFIRM

if [ "$CONFIRM" != "y" ] && [ "$CONFIRM" != "Y" ]; then
    echo "Déploiement annulé"
    exit 0
fi

# Créer Resource Group
echo ""
echo "4. Création Resource Group..."
az group create \
  --name $RESOURCE_GROUP \
  --location $LOCATION \
  >/dev/null 2>&1 || echo "   (Groupe existant)"
echo "   ✓ Resource Group prêt"

# Créer Storage Account
echo ""
echo "5. Création Storage Account..."
az storage account create \
  --name $STORAGE_ACCOUNT \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --sku Standard_LRS \
  --kind StorageV2 \
  --access-tier Hot \
  >/dev/null 2>&1 || echo "   (Storage existant)"
echo "   ✓ Storage Account prêt"

# Créer Function App
echo ""
echo "6. Création Function App..."
az functionapp create \
  --name $FUNCTION_APP \
  --resource-group $RESOURCE_GROUP \
  --storage-account $STORAGE_ACCOUNT \
  --consumption-plan-location $LOCATION \
  --runtime python \
  --runtime-version 3.9 \
  --functions-version 4 \
  --os-type Linux \
  --disable-app-insights false \
  >/dev/null 2>&1 || echo "   (Function existante)"
echo "   ✓ Function App prête"

# Récupérer connection string
echo ""
echo "7. Configuration du stockage..."
CONN_STRING=$(az storage account show-connection-string \
  --name $STORAGE_ACCOUNT \
  --resource-group $RESOURCE_GROUP \
  --output tsv)

# Créer conteneur
az storage container create \
  --name models \
  --connection-string "$CONN_STRING" \
  --public-access off \
  >/dev/null 2>&1 || echo "   (Conteneur existant)"
echo "   ✓ Conteneur 'models' prêt"

# Upload modèles
echo ""
echo "8. Upload des modèles enrichis..."
echo "   (Cela peut prendre quelques minutes - 2.5 Go)"
cd /home/ser/Bureau/P10_reco/models

# Fichiers essentiels
FILES=(
  "user_profiles_enriched.pkl"
  "user_item_matrix_weighted.npz"
  "articles_metadata.csv"
  "embeddings_filtered.pkl"
  "article_popularity.pkl"
  "mappings.pkl"
)

for file in "${FILES[@]}"; do
  if [ -f "$file" ]; then
    echo "   Uploading $file..."
    az storage blob upload \
      --container-name models \
      --file "$file" \
      --name "$file" \
      --connection-string "$CONN_STRING" \
      --overwrite \
      >/dev/null 2>&1
    echo "     ✓ $file"
  else
    echo "     ⚠️  $file non trouvé"
  fi
done

echo "   ✓ Modèles uploadés"

# Configurer variables
echo ""
echo "9. Configuration variables d'environnement..."
az functionapp config appsettings set \
  --name $FUNCTION_APP \
  --resource-group $RESOURCE_GROUP \
  --settings \
    "STORAGE_ACCOUNT_NAME=$STORAGE_ACCOUNT" \
    "BLOB_CONTAINER_NAME=models" \
    "BLOB_MODELS_PREFIX=" \
    "DEFAULT_N_RECOMMENDATIONS=5" \
    "USE_WEIGHTED_MATRIX=True" \
    "USE_WEIGHTED_AGGREGATION=True" \
    "USE_TEMPORAL_DECAY=True" \
    "DECAY_HALF_LIFE_DAYS=7.0" \
    "MAX_ARTICLE_AGE_DAYS=60" \
    "DEFAULT_WEIGHT_CONTENT=0.40" \
    "DEFAULT_WEIGHT_COLLAB=0.30" \
    "DEFAULT_WEIGHT_TREND=0.30" \
    "LOG_LEVEL=INFO" \
  >/dev/null 2>&1
echo "   ✓ Variables configurées"

# Déployer code
echo ""
echo "10. Déploiement du code..."
cd /home/ser/Bureau/P10_reco_new/azure_function
func azure functionapp publish $FUNCTION_APP --python

# Récupérer URL
FUNCTION_URL=$(az functionapp show \
  --name $FUNCTION_APP \
  --resource-group $RESOURCE_GROUP \
  --query "defaultHostName" \
  --output tsv)

echo ""
echo "========================================"
echo "✅ DÉPLOIEMENT RÉUSSI"
echo "========================================"
echo ""
echo "URL de votre API:"
echo "  https://$FUNCTION_URL/api/RecommendationFunction"
echo ""
echo "Tester avec:"
echo "  curl -X POST https://$FUNCTION_URL/api/RecommendationFunction \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"user_id\": 123, \"n\": 5}'"
echo ""
echo "Voir les logs:"
echo "  az functionapp log tail --name $FUNCTION_APP --resource-group $RESOURCE_GROUP"
echo ""
echo "========================================"
echo ""

# Sauvegarder configuration
cat > /home/ser/Bureau/P10_reco_new/azure_deployment_info.txt << EOF
DÉPLOIEMENT AZURE - MY CONTENT
Date: $(date)

Configuration:
  Resource Group: $RESOURCE_GROUP
  Location: $LOCATION
  Storage Account: $STORAGE_ACCOUNT
  Function App: $FUNCTION_APP

URL API:
  https://$FUNCTION_URL/api/RecommendationFunction

Commandes utiles:
  # Logs
  az functionapp log tail --name $FUNCTION_APP --resource-group $RESOURCE_GROUP

  # Restart
  az functionapp restart --name $FUNCTION_APP --resource-group $RESOURCE_GROUP

  # Supprimer
  az group delete --name $RESOURCE_GROUP --yes
EOF

echo "Configuration sauvegardée: azure_deployment_info.txt"
echo ""
