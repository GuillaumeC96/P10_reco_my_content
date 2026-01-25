#!/bin/bash
echo "=== TUNING PROGRESSIF - MONITORING ==="
echo ""
echo "Process status:"
ps aux | grep "tuning_12_progressive" | grep -v grep | awk '{print "  PID: "$2", CPU: "$3"%, RAM: "$4"%, Time: "$10}'
echo ""
echo "Latest progress:"
tail -3 tuning_12_progressive.log | grep -E "trial|Best"
echo ""
echo "Estimated completion time:"
uptime_sec=$(ps -p $(pgrep -f "tuning_12_progressive") -o etimes= 2>/dev/null | tr -d ' ')
if [ ! -z "$uptime_sec" ]; then
    trials_done=$(grep -c "Best trial:" tuning_12_progressive.log)
    if [ "$trials_done" -gt 0 ]; then
        avg_time=$((uptime_sec / trials_done))
        remaining=$((30 - trials_done))
        eta_sec=$((avg_time * remaining))
        eta_min=$((eta_sec / 60))
        echo "  Trials completed: $trials_done/30"
        echo "  Avg time per trial: ${avg_time}s"
        echo "  ETA: ${eta_min} minutes"
    fi
fi
