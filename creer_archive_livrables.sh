#!/bin/bash

# Script de création de l'archive des livrables
# Projet P10 - My Content

echo "============================================================="
echo "CRÉATION ARCHIVE LIVRABLES - PROJET P10"
echo "============================================================="
echo ""

# Couleurs
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Dossier source
SOURCE_DIR="LIVRABLES_PROJET10_Cassez_Guillaume_012026"
ARCHIVE_NAME="LIVRABLES_PROJET10_Cassez_Guillaume_012026.zip"

# Vérifier que le dossier existe
if [ ! -d "$SOURCE_DIR" ]; then
    echo "❌ Erreur: Le dossier $SOURCE_DIR n'existe pas"
    exit 1
fi

echo -e "${BLUE}📁 Dossier source:${NC} $SOURCE_DIR"
echo ""

# Compter les fichiers
FILE_COUNT=$(find "$SOURCE_DIR" -type f | wc -l)
echo -e "${BLUE}📊 Statistiques:${NC}"
echo "   - Fichiers: $FILE_COUNT"
echo "   - Taille: $(du -sh "$SOURCE_DIR" | cut -f1)"
echo ""

# Créer l'archive
echo -e "${YELLOW}📦 Création de l'archive...${NC}"
if zip -r "$ARCHIVE_NAME" "$SOURCE_DIR" -x "*.pyc" "*__pycache__*" "*.DS_Store" > /dev/null; then
    echo -e "${GREEN}✅ Archive créée avec succès!${NC}"
    echo ""
    echo -e "${BLUE}📄 Fichier créé:${NC}"
    echo "   - Nom: $ARCHIVE_NAME"
    echo "   - Taille: $(du -sh "$ARCHIVE_NAME" | cut -f1)"
    echo "   - Emplacement: $(pwd)/$ARCHIVE_NAME"
    echo ""
    echo -e "${GREEN}✅ PRÊT POUR SOUMISSION${NC}"
    echo ""
    echo "📌 Prochaines étapes:"
    echo "   1. Vérifier le contenu de l'archive (optionnel)"
    echo "   2. Se connecter à la plateforme OpenClassrooms"
    echo "   3. Uploader le fichier $ARCHIVE_NAME"
    echo "   4. Valider la soumission"
    echo ""
else
    echo -e "❌ Erreur lors de la création de l'archive"
    exit 1
fi

echo "============================================================="
