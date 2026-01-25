#!/bin/bash
# Script de monitoring pour tuning_12 (parallel ou progressive)

echo "=== MONITORING OPTIMISATION 12 PARAMS ==="
echo "Date: $(date)"
echo ""

# Vérifier si un processus tourne
PID=$(pgrep -f "tuning_12.*\.py" | head -1)
if [ -z "$PID" ]; then
    echo "❌ Processus non trouvé - peut-être terminé?"

    # Chercher les fichiers résultats
    for f in tuning_12*_results.json; do
        if [ -f "$f" ]; then
            echo "✅ Fichier résultats trouvé: $f"
            cat "$f" | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(f\"Best score: {d['best_score']:.6f}\")
print(f\"Collab: {d['best_params']['collab']}, Content: {d['best_params']['content']}, Trend: {d['best_params']['trend']}\")
if 'efficiency_stats' in d:
    print(f\"Efficacité: {d['efficiency_stats'].get('efficiency_gain', 'N/A')}\")
"
            break
        fi
    done
    exit 0
fi

# Stats processus principal
echo "📊 Processus principal:"
ps -p $PID -o pid,rss,etime,%cpu --no-headers | while read pid rss etime cpu; do
    rss_mb=$((rss / 1024))
    echo "   PID: $pid | RAM: ${rss_mb}MB | Temps: $etime | CPU: ${cpu}%"
done

# Workers parallèles
N_WORKERS=$(pgrep -f "spawn_main" | wc -l)
if [ "$N_WORKERS" -gt 0 ]; then
    echo "   Workers actifs: $N_WORKERS"
fi

echo ""

# RAM totale
echo "💾 Mémoire système:"
free -h | grep Mem | awk '{print "   Total: "$2" | Utilisé: "$3" | Libre: "$4}'
echo ""

# Trouver le bon fichier log
for LOG in tuning_12_parallel_progressive.log tuning_12_progressive_RUN.log tuning_12_progressive.log; do
    if [ -f "$LOG" ]; then
        SIZE=$(ls -lh "$LOG" | awk '{print $5}')
        MODIFIED=$(stat -c %y "$LOG" | cut -d'.' -f1)
        echo "📄 Log: $LOG ($SIZE, modifié: $MODIFIED)"
        echo ""
        echo "--- Progression ---"
        grep -E "(Best trial|/30|RÉSULTATS|Meilleur)" "$LOG" | tail -5
        break
    fi
done
