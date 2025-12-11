#!/bin/bash
# Script pour vérifier l'avancement du preprocessing

echo "=========================================="
echo "STATUT DU PREPROCESSING"
echo "=========================================="
echo ""

# Vérifier si le processus tourne
if ps aux | grep -v grep | grep data_preprocessing.py > /dev/null; then
    echo "✓ Processus en cours d'exécution"

    # Afficher l'utilisation CPU et mémoire
    ps aux | grep data_preprocessing.py | grep -v grep | awk '{print "  CPU: "$3"% | RAM: "$4"% ("$6/1024" MB)"}'

    # Temps écoulé
    ELAPSED=$(ps -o etime= -p $(pgrep -f data_preprocessing.py) 2>/dev/null)
    echo "  Temps écoulé: $ELAPSED"
else
    echo "✗ Processus terminé ou non trouvé"
fi

echo ""
echo "Fichiers dans models/:"
ls -lh models/ 2>/dev/null | tail -n +2 | awk '{print "  "$9" - "$5}'

echo ""
echo "Taille totale models/:"
du -sh models/ 2>/dev/null

echo ""
echo "=========================================="
