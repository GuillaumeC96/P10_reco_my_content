#!/bin/bash
# Script pour suivre la progression du pipeline

PIPELINE_PID=2815691
LOG_FILE="pipeline_output.log"
INTERNAL_LOG=$(ls -t logs/pipeline_*.log 2>/dev/null | head -1)

echo "========================================="
echo "  SUIVI DU PIPELINE - My Content"
echo "========================================="
echo ""

# Vérifier si le processus tourne
if ps -p $PIPELINE_PID > /dev/null 2>&1; then
    echo "✓ Pipeline en cours (PID: $PIPELINE_PID)"
    echo ""
else
    echo "✗ Pipeline terminé ou arrêté"
    echo ""
fi

# Afficher les dernières lignes du log
echo "--- Dernières lignes du log ---"
if [ -f "$LOG_FILE" ]; then
    tail -30 "$LOG_FILE" | sed 's/\x1b\[[0-9;]*m//g'  # Supprimer les couleurs ANSI
else
    echo "Fichier de log non trouvé"
fi

echo ""
echo "========================================="
echo "Commandes utiles:"
echo "  - Voir tout le log: cat $LOG_FILE"
echo "  - Suivre en temps réel: tail -f $LOG_FILE"
if [ -n "$INTERNAL_LOG" ]; then
    echo "  - Log interne: cat $INTERNAL_LOG"
fi
echo "  - Tuer le pipeline: kill $PIPELINE_PID"
echo "========================================="
