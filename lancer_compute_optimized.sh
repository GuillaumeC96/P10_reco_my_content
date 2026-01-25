#!/bin/bash
# Script de lancement avec monitoring mémoire

echo "========================================="
echo "LANCEMENT CALCUL POIDS - VERSION OPTIMISÉE"
echo "Limite: 30 Go de RAM"
echo "========================================="
echo ""

# Afficher la mémoire disponible
echo "Mémoire système:"
free -h
echo ""

# Vérifier que le répertoire de sortie existe
mkdir -p /home/ser/Bureau/P10_reco/models

echo "Démarrage du script..."
echo "Pour monitorer en temps réel, ouvrir un autre terminal et lancer:"
echo "  watch -n 5 'ps aux | grep compute_weights_memory_optimized | grep -v grep'"
echo ""

# Lancer le script
python3 /home/ser/Bureau/P10_reco_new/data_preparation/compute_weights_memory_optimized.py 2>&1 | tee compute_weights_$(date +%Y%m%d_%H%M%S).log

echo ""
echo "========================================="
echo "TERMINÉ"
echo "========================================="
