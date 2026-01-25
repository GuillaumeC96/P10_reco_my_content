#!/bin/bash
# Pipeline complet du système de recommandation My Content
# Auteur: Projet P10
# Date: 31 Décembre 2025

set -e  # Arrêter en cas d'erreur

# Couleurs pour l'affichage
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Répertoires
PROJECT_ROOT="/home/ser/Bureau/P10_reco_new"
DATA_PREP="$PROJECT_ROOT/data_preparation"
MODELS_DIR="$PROJECT_ROOT/models"
MODELS_LITE_DIR="$PROJECT_ROOT/models_lite"
DATA_DIR="$PROJECT_ROOT/news-portal-user-interactions-by-globocom"
LOG_DIR="$PROJECT_ROOT/logs"

# Créer le répertoire de logs
mkdir -p "$LOG_DIR"

# Timestamp pour les logs
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="$LOG_DIR/pipeline_${TIMESTAMP}.log"

# Fonction de logging
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] ✓${NC} $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ✗${NC} $1" | tee -a "$LOG_FILE"
}

log_step() {
    echo -e "\n${YELLOW}╔════════════════════════════════════════════════════════════════╗${NC}" | tee -a "$LOG_FILE"
    echo -e "${YELLOW}║${NC}  $1" | tee -a "$LOG_FILE"
    echo -e "${YELLOW}╚════════════════════════════════════════════════════════════════╝${NC}\n" | tee -a "$LOG_FILE"
}

# Fonction pour mesurer le temps
timer_start=$(date +%s)

# Banner
echo -e "${BLUE}"
cat << "EOF"
╔═══════════════════════════════════════════════════════════════════╗
║                                                                   ║
║   PIPELINE COMPLET - SYSTÈME DE RECOMMANDATION MY CONTENT        ║
║                                                                   ║
║   Dataset: Globo.com (322k users, 2.8M interactions)            ║
║   Approche: Hybride (Content + Collaborative + Temporal)         ║
║   Optimisation: Weighted matrix + 9 signaux de qualité          ║
║                                                                   ║
╚═══════════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

log "Pipeline démarré"
log "Logs sauvegardés dans: $LOG_FILE"

# ============================================================================
# ÉTAPE 0 : Vérification des prérequis
# ============================================================================

log_step "ÉTAPE 0: Vérification des prérequis"

# Vérifier Python
if ! command -v python3 &> /dev/null; then
    log_error "Python3 n'est pas installé"
    exit 1
fi
log_success "Python3: $(python3 --version)"

# Vérifier les dépendances Python
log "Vérification des dépendances Python..."
python3 -c "import pandas, numpy, scipy, sklearn" 2>/dev/null
if [ $? -eq 0 ]; then
    log_success "Dépendances Python OK"
else
    log_error "Dépendances manquantes. Installation..."
    pip install pandas numpy scipy scikit-learn -q
fi

# Vérifier l'existence des données brutes
if [ ! -d "$DATA_DIR" ]; then
    log_error "Dataset introuvable: $DATA_DIR"
    exit 1
fi
log_success "Dataset trouvé: $DATA_DIR"

# Compter les fichiers de clics
CLICK_FILES=$(find "$DATA_DIR/clicks" -name "*.csv" 2>/dev/null | wc -l)
log_success "Fichiers de clics trouvés: $CLICK_FILES"

# Créer les répertoires de sortie
mkdir -p "$MODELS_DIR"
mkdir -p "$MODELS_LITE_DIR"
log_success "Répertoires de sortie créés"

# ============================================================================
# ÉTAPE 1 : Exploration des données (optionnel, rapide)
# ============================================================================

log_step "ÉTAPE 1: Exploration des données"

if [ -f "$DATA_PREP/data_exploration.py" ]; then
    log "Analyse exploratoire du dataset..."
    START_TIME=$(date +%s)

    python3 "$DATA_PREP/data_exploration.py" 2>&1 | tee -a "$LOG_FILE"

    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))
    log_success "Exploration terminée en ${DURATION}s"
else
    log "Script d'exploration non trouvé, passage à l'étape suivante"
fi

# ============================================================================
# ÉTAPE 2 : Preprocessing des données
# ============================================================================

log_step "ÉTAPE 2: Preprocessing - Création des matrices et profils utilisateurs"

log "Traitement de $CLICK_FILES fichiers de clics..."
log "Opérations: Agrégation, matrices sparse, profils utilisateurs"
START_TIME=$(date +%s)

cd "$PROJECT_ROOT"

if [ -f "$DATA_PREP/data_preprocessing_optimized.py" ]; then
    python3 "$DATA_PREP/data_preprocessing_optimized.py" 2>&1 | tee -a "$LOG_FILE"

    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))
    log_success "Preprocessing terminé en ${DURATION}s"

    # Vérifier les outputs
    if [ -f "$MODELS_DIR/user_item_matrix.npz" ]; then
        SIZE=$(du -h "$MODELS_DIR/user_item_matrix.npz" | cut -f1)
        log_success "Matrice user-item créée: $SIZE"
    fi

    if [ -f "$MODELS_DIR/user_profiles.json" ]; then
        SIZE=$(du -h "$MODELS_DIR/user_profiles.json" | cut -f1)
        log_success "Profils utilisateurs créés: $SIZE"
    fi
else
    log_error "Script de preprocessing non trouvé: data_preprocessing_optimized.py"
    exit 1
fi

# ============================================================================
# ÉTAPE 3 : Calcul des poids d'interaction (enrichissement)
# ============================================================================

log_step "ÉTAPE 3: Enrichissement - Calcul des poids d'interaction (9 signaux)"

log "Calcul des poids de qualité d'engagement..."
log "Signaux: temps, clicks, session, device, OS, region, referrer, country, environment"
START_TIME=$(date +%s)

if [ -f "$DATA_PREP/compute_weights_memory_optimized.py" ]; then
    # Vérifier si le fichier de sortie existe déjà
    if [ -f "$MODELS_DIR/interaction_stats_enriched.csv" ]; then
        log "⚠️  Le fichier interaction_stats_enriched.csv existe déjà"
        log "Étape 3 ignorée (fichier existant conservé) - mode automatique"
        # Mode automatique: on garde le fichier existant et on continue
    else
        python3 "$DATA_PREP/compute_weights_memory_optimized.py" 2>&1 | tee -a "$LOG_FILE"
    fi

    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))
    log_success "Enrichissement terminé en ${DURATION}s"

    if [ -f "$MODELS_DIR/interaction_stats_enriched.csv" ]; then
        SIZE=$(du -h "$MODELS_DIR/interaction_stats_enriched.csv" | cut -f1)
        LINES=$(wc -l < "$MODELS_DIR/interaction_stats_enriched.csv")
        log_success "Stats enrichies créées: $SIZE ($LINES interactions)"
    fi
else
    log_error "Script d'enrichissement non trouvé: compute_weights_memory_optimized.py"
    exit 1
fi

# ============================================================================
# ÉTAPE 4 : Création de la matrice pondérée
# ============================================================================

log_step "ÉTAPE 4: Matrice pondérée - Remplacement des counts par les weights"

log "Création de la matrice sparse pondérée..."
START_TIME=$(date +%s)

if [ -f "$DATA_PREP/create_weighted_matrix.py" ]; then
    python3 "$DATA_PREP/create_weighted_matrix.py" 2>&1 | tee -a "$LOG_FILE"

    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))
    log_success "Matrice pondérée créée en ${DURATION}s"

    if [ -f "$MODELS_DIR/user_item_matrix_weighted.npz" ]; then
        SIZE=$(du -h "$MODELS_DIR/user_item_matrix_weighted.npz" | cut -f1)
        log_success "Matrice pondérée: $SIZE"
    fi
else
    log_error "Script de création matrice non trouvé: create_weighted_matrix.py"
    exit 1
fi

# ============================================================================
# ÉTAPE 5 : Création des modèles Lite (pour déploiement)
# ============================================================================

log_step "ÉTAPE 5: Modèles Lite - Échantillonnage pour déploiement cloud"

log "Création des modèles Lite (10k users)..."
START_TIME=$(date +%s)

if [ -f "$DATA_PREP/create_lite_models.py" ]; then
    python3 "$DATA_PREP/create_lite_models.py" 2>&1 | tee -a "$LOG_FILE"

    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))
    log_success "Modèles Lite créés en ${DURATION}s"

    # Vérifier la taille totale
    if [ -d "$MODELS_LITE_DIR" ]; then
        SIZE=$(du -sh "$MODELS_LITE_DIR" | cut -f1)
        log_success "Modèles Lite: $SIZE (vs ~750 MB pour modèles complets)"
    fi
else
    log "Script create_lite_models.py non trouvé (optionnel)"
fi

# ============================================================================
# ÉTAPE 6 : Tests et validation
# ============================================================================

log_step "ÉTAPE 6: Tests et validation"

log "Test de chargement des modèles..."

python3 << 'PYEOF' 2>&1 | tee -a "$LOG_FILE"
import sys
import pickle
from pathlib import Path
from scipy.sparse import load_npz

models_dir = Path("/home/ser/Bureau/P10_reco_new/models")

try:
    # Test matrice
    matrix = load_npz(models_dir / "user_item_matrix_weighted.npz")
    print(f"✓ Matrice chargée: {matrix.shape} ({matrix.nnz:,} valeurs non-nulles)")

    # Test profils
    with open(models_dir / "user_profiles_enriched.pkl", 'rb') as f:
        profiles = pickle.load(f)
    print(f"✓ Profils chargés: {len(profiles):,} utilisateurs")

    # Test mappings
    with open(models_dir / "mappings.pkl", 'rb') as f:
        mappings = pickle.load(f)
    print(f"✓ Mappings chargés: {len(mappings['user_to_idx']):,} users, {len(mappings['article_to_idx']):,} articles")

    print("\n✓ Tous les modèles se chargent correctement !")

except Exception as e:
    print(f"✗ Erreur lors du chargement: {e}")
    sys.exit(1)
PYEOF

if [ $? -eq 0 ]; then
    log_success "Validation des modèles réussie"
else
    log_error "Erreur lors de la validation"
    exit 1
fi

# ============================================================================
# ÉTAPE 7 : Résumé et rapport final
# ============================================================================

log_step "ÉTAPE 7: Génération du rapport final"

# Calculer le temps total
timer_end=$(date +%s)
total_duration=$((timer_end - timer_start))
minutes=$((total_duration / 60))
seconds=$((total_duration % 60))

# Générer le rapport
REPORT_FILE="$PROJECT_ROOT/PIPELINE_REPORT_${TIMESTAMP}.md"

cat > "$REPORT_FILE" << EOF
# Rapport d'exécution du Pipeline - My Content

**Date:** $(date '+%Y-%m-%d %H:%M:%S')
**Durée totale:** ${minutes}m ${seconds}s

---

## Résumé de l'exécution

### ✅ Étapes complétées

1. ✓ Vérification des prérequis
2. ✓ Exploration des données
3. ✓ Preprocessing (matrices + profils)
4. ✓ Enrichissement (poids d'interaction)
5. ✓ Création matrice pondérée
6. ✓ Modèles Lite (déploiement)
7. ✓ Validation des modèles

---

## Fichiers générés

### Modèles complets (\`$MODELS_DIR\`)

\`\`\`
$(ls -lh "$MODELS_DIR" | tail -n +2)
\`\`\`

**Taille totale:** $(du -sh "$MODELS_DIR" | cut -f1)

### Modèles Lite (\`$MODELS_LITE_DIR\`)

\`\`\`
$(ls -lh "$MODELS_LITE_DIR" 2>/dev/null | tail -n +2 || echo "Non générés")
\`\`\`

**Taille totale:** $(du -sh "$MODELS_LITE_DIR" 2>/dev/null | cut -f1 || echo "N/A")

---

## Statistiques du dataset

$(python3 << 'PYEOF'
import pickle
from pathlib import Path
from scipy.sparse import load_npz

models_dir = Path("/home/ser/Bureau/P10_reco_new/models")

# Charger les données
matrix = load_npz(models_dir / "user_item_matrix_weighted.npz")
with open(models_dir / "user_profiles_enriched.pkl", 'rb') as f:
    profiles = pickle.load(f)
with open(models_dir / "mappings.pkl", 'rb') as f:
    mappings = pickle.load(f)

# Statistiques
n_users = matrix.shape[0]
n_articles = matrix.shape[1]
n_interactions = matrix.nnz
sparsity = (1 - n_interactions / (n_users * n_articles)) * 100

print(f"- **Utilisateurs:** {n_users:,}")
print(f"- **Articles:** {n_articles:,}")
print(f"- **Interactions:** {n_interactions:,}")
print(f"- **Sparsité:** {sparsity:.4f}%")
print(f"- **Profils enrichis:** {len(profiles):,}")

# Calculer le score moyen
import numpy as np
avg_weight = np.mean([p['avg_weight'] for p in profiles.values()])
print(f"- **Score moyen d'engagement:** {avg_weight:.3f}")
PYEOF
)

---

## Prochaines étapes

1. **Déploiement:** Upload des modèles Lite sur Azure/AWS
2. **API:** Tester l'endpoint de recommandation
3. **Évaluation:** Benchmark avec 500 utilisateurs test
4. **Interface:** Application Streamlit pour démonstration
5. **Présentation:** Slides et démonstration en direct

---

## Commandes utiles

### Tester l'API localement
\`\`\`bash
cd $PROJECT_ROOT/app
streamlit run streamlit_api_v2.py
\`\`\`

### Voir les logs
\`\`\`bash
cat $LOG_FILE
\`\`\`

### Lancer l'évaluation (optionnel)
\`\`\`bash
cd $PROJECT_ROOT/evaluation
python3 benchmark.py
\`\`\`

---

**Pipeline généré automatiquement**
**Logs complets:** \`$LOG_FILE\`
EOF

log_success "Rapport généré: $REPORT_FILE"

# ============================================================================
# AFFICHAGE FINAL
# ============================================================================

echo -e "\n${GREEN}"
cat << "EOF"
╔═══════════════════════════════════════════════════════════════════╗
║                                                                   ║
║                    ✓ PIPELINE TERMINÉ AVEC SUCCÈS                ║
║                                                                   ║
╚═══════════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

log_success "Temps total: ${minutes}m ${seconds}s"
log_success "Modèles générés dans: $MODELS_DIR"
log_success "Rapport disponible: $REPORT_FILE"
log_success "Logs complets: $LOG_FILE"

echo -e "\n${BLUE}Prochaines étapes:${NC}"
echo "  1. Consulter le rapport: cat $REPORT_FILE"
echo "  2. Tester l'API: cd app && streamlit run streamlit_api_v2.py"
echo "  3. Déployer sur Azure: Voir AZURE_SUCCESS.md"

exit 0
