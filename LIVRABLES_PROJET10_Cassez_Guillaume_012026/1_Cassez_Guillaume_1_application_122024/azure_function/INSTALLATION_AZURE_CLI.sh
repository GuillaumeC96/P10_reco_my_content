#!/bin/bash
#
# Installation d'Azure CLI et Azure Functions Core Tools
# Pour Ubuntu/Debian
#

set -e

BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  INSTALLATION AZURE CLI + FUNCTIONS CORE TOOLS          ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""

# 1. Azure CLI
echo -e "${YELLOW}ÉTAPE 1/3: Installation d'Azure CLI${NC}"
echo ""

if command -v az &> /dev/null; then
    echo -e "${GREEN}✓ Azure CLI déjà installé${NC}"
    az --version | head -1
else
    echo "Installation d'Azure CLI..."
    curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

    if command -v az &> /dev/null; then
        echo -e "${GREEN}✓ Azure CLI installé avec succès${NC}"
        az --version | head -1
    else
        echo -e "${YELLOW}⚠️ Erreur lors de l'installation d'Azure CLI${NC}"
        exit 1
    fi
fi

echo ""
echo "─────────────────────────────────────────────────────────"
echo ""

# 2. Azure Functions Core Tools
echo -e "${YELLOW}ÉTAPE 2/3: Installation d'Azure Functions Core Tools${NC}"
echo ""

if command -v func &> /dev/null; then
    echo -e "${GREEN}✓ Azure Functions Core Tools déjà installé${NC}"
    func --version
else
    echo "Installation d'Azure Functions Core Tools v4..."

    # Télécharger et installer le paquet Microsoft
    wget -q https://packages.microsoft.com/config/ubuntu/$(lsb_release -rs)/packages-microsoft-prod.deb -O /tmp/packages-microsoft-prod.deb
    sudo dpkg -i /tmp/packages-microsoft-prod.deb
    rm /tmp/packages-microsoft-prod.deb

    # Mettre à jour et installer
    sudo apt-get update
    sudo apt-get install -y azure-functions-core-tools-4

    if command -v func &> /dev/null; then
        echo -e "${GREEN}✓ Azure Functions Core Tools installé avec succès${NC}"
        func --version
    else
        echo -e "${YELLOW}⚠️ Erreur lors de l'installation d'Azure Functions Core Tools${NC}"
        exit 1
    fi
fi

echo ""
echo "─────────────────────────────────────────────────────────"
echo ""

# 3. Connexion Azure
echo -e "${YELLOW}ÉTAPE 3/3: Connexion à Azure${NC}"
echo ""
echo "Exécutez la commande suivante pour vous connecter:"
echo ""
echo -e "${GREEN}  az login${NC}"
echo ""
echo "Une fenêtre de navigateur s'ouvrira pour l'authentification."
echo ""
echo "Après connexion, vérifiez votre subscription:"
echo -e "${GREEN}  az account list --output table${NC}"
echo ""

echo -e "${BLUE}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  INSTALLATION TERMINÉE                                   ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""
echo "Prochaines étapes:"
echo "  1. Connectez-vous: az login"
echo "  2. Suivez le guide: DEPLOIEMENT_RAPIDE.md"
echo ""
