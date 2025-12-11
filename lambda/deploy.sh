#!/bin/bash

# Script de déploiement de la Lambda Function AWS
# Ce script package et déploie la Lambda Function

set -e  # Arrêter en cas d'erreur

echo "=================================================="
echo "  DÉPLOIEMENT DE LA LAMBDA FUNCTION AWS"
echo "=================================================="

# Configuration
FUNCTION_NAME="MyContentRecommendation"
RUNTIME="python3.9"
HANDLER="lambda_function.lambda_handler"
ROLE_NAME="MyContentLambdaRole"
MEMORY_SIZE=1024
TIMEOUT=30
REGION="us-east-1"

# Couleurs pour l'affichage
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo ""
echo -e "${YELLOW}[1/6] Vérification des prérequis...${NC}"

# Vérifier que AWS CLI est installé
if ! command -v aws &> /dev/null; then
    echo -e "${RED}❌ AWS CLI n'est pas installé${NC}"
    echo "Installez-le avec: pip install awscli"
    exit 1
fi

# Vérifier les credentials AWS
if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}❌ Credentials AWS non configurés${NC}"
    echo "Configurez-les avec: aws configure"
    exit 1
fi

echo -e "${GREEN}✓ AWS CLI configuré${NC}"

echo ""
echo -e "${YELLOW}[2/6] Installation des dépendances...${NC}"

# Créer un dossier temporaire pour le package
rm -rf package deployment-package.zip
mkdir -p package

# Installer les dépendances dans le dossier package
pip install -r requirements.txt -t package/ --upgrade

echo -e "${GREEN}✓ Dépendances installées${NC}"

echo ""
echo -e "${YELLOW}[3/6] Création du package de déploiement...${NC}"

# Copier les fichiers de code dans package
cp lambda_function.py package/
cp recommendation_engine.py package/
cp config.py package/
cp utils.py package/

# Créer le fichier zip
cd package
zip -r ../deployment-package.zip . -q
cd ..

# Vérifier la taille du package
PACKAGE_SIZE=$(du -h deployment-package.zip | cut -f1)
echo -e "${GREEN}✓ Package créé: ${PACKAGE_SIZE}${NC}"

echo ""
echo -e "${YELLOW}[4/6] Vérification/Création du rôle IAM...${NC}"

# Créer le rôle IAM si nécessaire
if ! aws iam get-role --role-name $ROLE_NAME &> /dev/null; then
    echo "Création du rôle IAM..."

    # Créer le trust policy
    cat > trust-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

    # Créer le rôle
    aws iam create-role \
        --role-name $ROLE_NAME \
        --assume-role-policy-document file://trust-policy.json

    # Attacher les policies nécessaires
    aws iam attach-role-policy \
        --role-name $ROLE_NAME \
        --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

    aws iam attach-role-policy \
        --role-name $ROLE_NAME \
        --policy-arn arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess

    rm trust-policy.json

    echo -e "${GREEN}✓ Rôle IAM créé${NC}"

    # Attendre que le rôle soit prêt
    echo "Attente de la propagation du rôle (10 secondes)..."
    sleep 10
else
    echo -e "${GREEN}✓ Rôle IAM existant trouvé${NC}"
fi

# Récupérer l'ARN du rôle
ROLE_ARN=$(aws iam get-role --role-name $ROLE_NAME --query 'Role.Arn' --output text)

echo ""
echo -e "${YELLOW}[5/6] Déploiement de la Lambda Function...${NC}"

# Vérifier si la fonction existe déjà
if aws lambda get-function --function-name $FUNCTION_NAME &> /dev/null; then
    echo "Mise à jour de la fonction existante..."

    aws lambda update-function-code \
        --function-name $FUNCTION_NAME \
        --zip-file fileb://deployment-package.zip \
        --region $REGION

    aws lambda update-function-configuration \
        --function-name $FUNCTION_NAME \
        --runtime $RUNTIME \
        --handler $HANDLER \
        --memory-size $MEMORY_SIZE \
        --timeout $TIMEOUT \
        --region $REGION

    echo -e "${GREEN}✓ Fonction mise à jour${NC}"
else
    echo "Création de la fonction..."

    aws lambda create-function \
        --function-name $FUNCTION_NAME \
        --runtime $RUNTIME \
        --role $ROLE_ARN \
        --handler $HANDLER \
        --zip-file fileb://deployment-package.zip \
        --memory-size $MEMORY_SIZE \
        --timeout $TIMEOUT \
        --region $REGION

    echo -e "${GREEN}✓ Fonction créée${NC}"
fi

echo ""
echo -e "${YELLOW}[6/6] Configuration de la Function URL...${NC}"

# Créer ou récupérer la Function URL
if aws lambda get-function-url-config --function-name $FUNCTION_NAME --region $REGION &> /dev/null; then
    FUNCTION_URL=$(aws lambda get-function-url-config --function-name $FUNCTION_NAME --region $REGION --query 'FunctionUrl' --output text)
    echo -e "${GREEN}✓ Function URL existante${NC}"
else
    echo "Création de la Function URL..."

    FUNCTION_URL=$(aws lambda create-function-url-config \
        --function-name $FUNCTION_NAME \
        --auth-type NONE \
        --region $REGION \
        --query 'FunctionUrl' \
        --output text)

    # Ajouter les permissions publiques
    aws lambda add-permission \
        --function-name $FUNCTION_NAME \
        --statement-id FunctionURLAllowPublicAccess \
        --action lambda:InvokeFunctionUrl \
        --principal "*" \
        --function-url-auth-type NONE \
        --region $REGION

    echo -e "${GREEN}✓ Function URL créée${NC}"
fi

# Nettoyage
echo ""
echo "Nettoyage..."
rm -rf package deployment-package.zip

# Résumé
echo ""
echo "=================================================="
echo "  DÉPLOIEMENT TERMINÉ!"
echo "=================================================="
echo ""
echo -e "${GREEN}✓ Function Name:${NC} $FUNCTION_NAME"
echo -e "${GREEN}✓ Region:${NC} $REGION"
echo -e "${GREEN}✓ Runtime:${NC} $RUNTIME"
echo -e "${GREEN}✓ Memory:${NC} ${MEMORY_SIZE}MB"
echo -e "${GREEN}✓ Timeout:${NC} ${TIMEOUT}s"
echo ""
echo -e "${GREEN}✓ Function URL:${NC} $FUNCTION_URL"
echo ""
echo "📝 Pour tester:"
echo "  curl \"${FUNCTION_URL}?user_id=123&n_recommendations=5\""
echo ""
echo "⚠️  N'oubliez pas d'uploader les modèles vers S3 avec:"
echo "  python3 data_preparation/upload_to_s3.py --bucket your-bucket-name"
echo ""
