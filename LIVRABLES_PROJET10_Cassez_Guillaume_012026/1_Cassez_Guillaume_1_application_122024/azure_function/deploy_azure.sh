#!/bin/bash
#
# Script de déploiement automatisé - Azure Functions
# My Content Recommendation System
# Date: 25 Décembre 2024
#

set -e  # Arrêter en cas d'erreur

# Couleurs pour affichage
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔══════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Déploiement Azure - My Content Reco System     ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════╝${NC}"
echo ""

# Configuration
RESOURCE_GROUP="rg-mycontent"
LOCATION="westeurope"
STORAGE_ACCOUNT="samycontent"
FUNCTION_APP="func-mycontent-reco"
BLOB_CONTAINER="models"
MODELS_PATH="../models"

# Étape 1 : Vérifier les prérequis
echo -e "${YELLOW}[1/8]${NC} Vérification des prérequis..."

if ! command -v az &> /dev/null; then
    echo -e "${RED}❌ Azure CLI non installé${NC}"
    echo "Installation: curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash"
    exit 1
fi
echo -e "${GREEN}✓${NC} Azure CLI installé"

if ! command -v func &> /dev/null; then
    echo -e "${RED}❌ Azure Functions Core Tools non installé${NC}"
    echo "Installation: https://learn.microsoft.com/en-us/azure/azure-functions/functions-run-local"
    exit 1
fi
echo -e "${GREEN}✓${NC} Azure Functions Core Tools installé"

echo -e "${BLUE}Connexion à Azure...${NC}"
az login --output none
echo -e "${GREEN}✓${NC} Connecté à Azure"

# Étape 2 : Créer le resource group
echo ""
echo -e "${YELLOW}[2/8]${NC} Création du resource group '$RESOURCE_GROUP'..."
if az group exists --name $RESOURCE_GROUP | grep -q "true"; then
    echo -e "${YELLOW}⚠${NC}  Resource group existe déjà (skip)"
else
    az group create --name $RESOURCE_GROUP --location $LOCATION --output none
    echo -e "${GREEN}✓${NC} Resource group créé"
fi

# Étape 3 : Créer le storage account
echo ""
echo -e "${YELLOW}[3/8]${NC} Création du storage account '$STORAGE_ACCOUNT'..."
if az storage account show --name $STORAGE_ACCOUNT --resource-group $RESOURCE_GROUP &> /dev/null; then
    echo -e "${YELLOW}⚠${NC}  Storage account existe déjà (skip)"
else
    az storage account create \
        --name $STORAGE_ACCOUNT \
        --resource-group $RESOURCE_GROUP \
        --location $LOCATION \
        --sku Standard_LRS \
        --output none
    echo -e "${GREEN}✓${NC} Storage account créé"
fi

# Récupérer la connection string
CONNECTION_STRING=$(az storage account show-connection-string \
    --name $STORAGE_ACCOUNT \
    --resource-group $RESOURCE_GROUP \
    --query connectionString \
    --output tsv)

# Étape 4 : Créer le conteneur Blob
echo ""
echo -e "${YELLOW}[4/8]${NC} Création du conteneur Blob '$BLOB_CONTAINER'..."
if az storage container exists \
    --name $BLOB_CONTAINER \
    --connection-string "$CONNECTION_STRING" \
    --query exists \
    --output tsv | grep -q "True"; then
    echo -e "${YELLOW}⚠${NC}  Conteneur existe déjà (skip)"
else
    az storage container create \
        --name $BLOB_CONTAINER \
        --connection-string "$CONNECTION_STRING" \
        --public-access off \
        --output none
    echo -e "${GREEN}✓${NC} Conteneur Blob créé"
fi

# Étape 5 : Upload des modèles
echo ""
echo -e "${YELLOW}[5/8]${NC} Upload des modèles vers Blob Storage..."
echo -e "${BLUE}Ceci peut prendre plusieurs minutes (121 MB)...${NC}"

if [ -d "$MODELS_PATH" ]; then
    az storage blob upload-batch \
        --destination $BLOB_CONTAINER \
        --source $MODELS_PATH \
        --connection-string "$CONNECTION_STRING" \
        --output none \
        --only-show-errors

    # Compter les fichiers uploadés
    FILE_COUNT=$(az storage blob list \
        --container-name $BLOB_CONTAINER \
        --connection-string "$CONNECTION_STRING" \
        --query "length(@)" \
        --output tsv)

    echo -e "${GREEN}✓${NC} $FILE_COUNT fichiers uploadés"
else
    echo -e "${RED}❌ Dossier models/ introuvable à $MODELS_PATH${NC}"
    exit 1
fi

# Étape 6 : Créer Function App
echo ""
echo -e "${YELLOW}[6/8]${NC} Création de la Function App '$FUNCTION_APP'..."
if az functionapp show --name $FUNCTION_APP --resource-group $RESOURCE_GROUP &> /dev/null; then
    echo -e "${YELLOW}⚠${NC}  Function App existe déjà (skip)"
else
    az functionapp create \
        --name $FUNCTION_APP \
        --resource-group $RESOURCE_GROUP \
        --storage-account $STORAGE_ACCOUNT \
        --runtime python \
        --runtime-version 3.9 \
        --functions-version 4 \
        --os-type Linux \
        --consumption-plan-location $LOCATION \
        --output none

    echo -e "${GREEN}✓${NC} Function App créée"
    echo -e "${BLUE}Attente de la disponibilité (30s)...${NC}"
    sleep 30
fi

# Étape 7 : Configuration des variables d'environnement
echo ""
echo -e "${YELLOW}[7/8]${NC} Configuration des variables d'environnement..."
az functionapp config appsettings set \
    --name $FUNCTION_APP \
    --resource-group $RESOURCE_GROUP \
    --settings \
        STORAGE_ACCOUNT_NAME=$STORAGE_ACCOUNT \
        BLOB_CONTAINER_NAME=$BLOB_CONTAINER \
        MODELS_PATH="/home/site/wwwroot/models" \
        LOG_LEVEL=INFO \
        ALLOWED_ORIGINS="*" \
        STORAGE_CONNECTION_STRING="$CONNECTION_STRING" \
    --output none

echo -e "${GREEN}✓${NC} Variables configurées"

# Étape 8 : Déploiement du code
echo ""
echo -e "${YELLOW}[8/8]${NC} Déploiement du code vers Azure..."
echo -e "${BLUE}Ceci peut prendre 2-3 minutes...${NC}"

func azure functionapp publish $FUNCTION_APP --python

# Récupérer l'URL
FUNCTION_URL=$(az functionapp function show \
    --resource-group $RESOURCE_GROUP \
    --name $FUNCTION_APP \
    --function-name RecommendationFunction \
    --query invokeUrlTemplate \
    --output tsv 2>/dev/null || echo "")

if [ -z "$FUNCTION_URL" ]; then
    FUNCTION_URL="https://$FUNCTION_APP.azurewebsites.net/api/recommend"
fi

# Résumé final
echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║          DÉPLOIEMENT RÉUSSI ! ✓                  ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}Resource Group:${NC}   $RESOURCE_GROUP"
echo -e "${BLUE}Storage Account:${NC}  $STORAGE_ACCOUNT"
echo -e "${BLUE}Function App:${NC}     $FUNCTION_APP"
echo -e "${BLUE}Blob Container:${NC}   $BLOB_CONTAINER"
echo ""
echo -e "${GREEN}URL de l'API:${NC}"
echo -e "${YELLOW}$FUNCTION_URL${NC}"
echo ""
echo -e "${BLUE}Test rapide:${NC}"
echo -e "curl -X GET \"$FUNCTION_URL?user_id=5&n_recommendations=5\""
echo ""
echo -e "${YELLOW}⚠ IMPORTANT - Coûts:${NC}"
echo -e "Surveillez vos coûts sur: https://portal.azure.com/#blade/Microsoft_Azure_CostManagement"
echo ""
echo -e "${BLUE}Pour arrêter la Function App (STOP BILLING):${NC}"
echo -e "az functionapp stop --name $FUNCTION_APP --resource-group $RESOURCE_GROUP"
echo ""
echo -e "${BLUE}Pour supprimer TOUTES les ressources:${NC}"
echo -e "${RED}az group delete --name $RESOURCE_GROUP --yes${NC}"
echo ""
