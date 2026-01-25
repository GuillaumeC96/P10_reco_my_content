#!/bin/bash
#
# Script de lancement de l'optimisation bayésienne FINALE
# avec plages ajustées pour éviter les extremums
#

set -e

BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  OPTIMISATION BAYÉSIENNE FINALE - PLAGES AJUSTÉES       ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""

# Vérifier qu'on est dans le bon dossier
if [ ! -f "tuning_12_parallel_progressive.py" ]; then
    echo -e "${YELLOW}Changement de répertoire vers evaluation/${NC}"
    cd /home/ser/Bureau/P10_reco_new/evaluation
fi

# Afficher les modifications
echo -e "${YELLOW}MODIFICATIONS APPLIQUÉES:${NC}"
echo ""
echo "NIVEAU 1 (9 features):"
echo "  w_time: [0.15-0.50] → [0.32-0.67]  (déplacé +0.17)"
echo "  Autres: inchangés"
echo ""
echo "NIVEAU 2 (3 stratégies):"
echo "  collab:  [1-5] → [0-10]"
echo "  content: [1-5] → [0-10]"
echo "  trend:   [0-3] → [0-5]"
echo ""
echo -e "${YELLOW}CONFIGURATION:${NC}"
echo "  Trials: 30"
echo "  Utilisateurs: 50"
echo "  Workers: 12 (parallèle)"
echo "  Early stopping: 10 → 30 → 50 users"
echo ""
echo -e "${YELLOW}TEMPS ESTIMÉ: ~45 minutes${NC}"
echo ""
echo -e "${GREEN}Appuyez sur ENTRÉE pour démarrer (Ctrl+C pour annuler)${NC}"
read

# Afficher l'heure de début
START_TIME=$(date +%s)
echo ""
echo -e "${BLUE}Début: $(date '+%H:%M:%S')${NC}"
echo "=" * 60
echo ""

# Lancer l'optimisation
python3 tuning_12_parallel_progressive.py

# Calculer le temps écoulé
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))
MINUTES=$((DURATION / 60))
SECONDS=$((DURATION % 60))

echo ""
echo "=" * 60
echo -e "${BLUE}Fin: $(date '+%H:%M:%S')${NC}"
echo -e "${GREEN}Durée: ${MINUTES}m ${SECONDS}s${NC}"
echo ""

# Vérifier que le fichier de résultats existe
if [ -f "tuning_12_parallel_progressive_results.json" ]; then
    echo -e "${GREEN}✓ Résultats sauvegardés dans tuning_12_parallel_progressive_results.json${NC}"

    # Afficher un aperçu rapide
    echo ""
    echo -e "${YELLOW}Aperçu des résultats:${NC}"
    python3 << 'EOF'
import json
with open('tuning_12_parallel_progressive_results.json', 'r') as f:
    results = json.load(f)

best = results['best_params']
score = results['best_score']

print(f"\nMeilleur score: {score:.6f}")
print(f"\nNIVEAU 1 (top 3):")
norm = results['normalized_weights_level1']
top3 = sorted(norm.items(), key=lambda x: x[1], reverse=True)[:3]
for key, val in top3:
    print(f"  {key:12s}: {val:.4f} ({val*100:.1f}%)")

print(f"\nNIVEAU 2:")
l2 = results['best_params_level2'] if 'best_params_level2' in results else best
if 'ratio' in l2:
    print(f"  Ratio: {l2['ratio']}")
else:
    print(f"  collab={best['collab']}, content={best['content']}, trend={best['trend']}")

# Vérifier extremums
if 'extremums_check' in results:
    check = results['extremums_check']
    if check['has_extremums']:
        print(f"\n⚠️ Encore des extremums: {check['level1']} {check['level2']}")
        print("   → Considérer d'ajuster à nouveau les plages")
    else:
        print(f"\n✓ Aucun paramètre aux extremums !")
        print("   → Les plages sont correctes")
EOF

    echo ""
    echo -e "${YELLOW}Pour voir les détails complets:${NC}"
    echo "  cat tuning_12_parallel_progressive_results.json | python3 -m json.tool"

else
    echo -e "${YELLOW}⚠️ Fichier de résultats non trouvé${NC}"
fi

echo ""
echo -e "${BLUE}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  OPTIMISATION TERMINÉE                                   ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""
