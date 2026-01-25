# Guide d'exécution du Pipeline Local

## Pourquoi en local plutôt que Kaggle ?

✅ **Avantages du pipeline local:**
1. **Contrôle total** - Pas de limite de temps (6h sur Kaggle)
2. **Debugging facile** - Accès direct aux logs et fichiers
3. **Présentation** - Démo en direct possible
4. **Livrables propres** - Fichiers organisés et documentés
5. **Reproductibilité** - Script automatisé et versionné

## Étapes du Pipeline

Le script `run_pipeline_complet.sh` exécute automatiquement:

### 1. Vérification des prérequis
- Python 3.x
- Dépendances (pandas, numpy, scipy, sklearn)
- Dataset Globo.com

### 2. Exploration des données (optionnel)
- Statistiques descriptives
- Analyse de la distribution
- Détection des anomalies

### 3. Preprocessing
- Chargement de 385 fichiers de clics (streaming)
- Agrégation des interactions
- Création matrice sparse user-item (CSR)
- Génération profils utilisateurs
- Filtrage règle 30s

**Sortie:** `user_item_matrix.npz`, `user_profiles.json`, `mappings.pkl`

### 4. Enrichissement
- Calcul des 9 signaux de qualité:
  1. Temps de lecture
  2. Nombre de clicks
  3. Qualité de session
  4. Type de device
  5. Système d'exploitation
  6. Pays
  7. Région
  8. Referrer
  9. Environnement (app/web)

**Sortie:** `interaction_stats_enriched.csv` (426 MB)

### 5. Matrice pondérée
- Remplacement des counts par les weights
- Création matrice sparse pondérée

**Sortie:** `user_item_matrix_weighted.npz` (9.2 MB)

### 6. Modèles Lite
- Échantillonnage 10,000 utilisateurs
- Réduction de 750 MB → 86 MB
- Pour déploiement cloud (Azure Functions)

**Sortie:** Répertoire `models_lite/`

### 7. Validation
- Test de chargement des modèles
- Vérification de l'intégrité
- Statistiques finales

## Utilisation

### Lancement du pipeline complet

```bash
cd /home/ser/Bureau/P10_reco_new
./run_pipeline_complet.sh
```

### Options disponibles

Le script est **interactif** pour certaines étapes:
- Si les fichiers existent déjà, il demande confirmation avant de les régénérer
- Vous pouvez arrêter à tout moment avec `Ctrl+C`

### Temps d'exécution estimé

| Étape | Durée | Matériel |
|-------|-------|----------|
| Exploration | 30s | CPU |
| Preprocessing | 15s | CPU + RAM (8 GB) |
| Enrichissement | **2-5 min** | CPU intensive |
| Matrice pondérée | 30s | CPU + RAM |
| Modèles Lite | 10s | CPU |
| **Total** | **5-10 min** | Variable |

### Ressources nécessaires

- **RAM:** 8 GB minimum (16 GB recommandé)
- **Stockage:** 2 GB libre
- **CPU:** Multi-core recommandé (parallélisation)

## Outputs générés

### Fichiers modèles

```
/home/ser/Bureau/P10_reco/models/
├── user_item_matrix.npz              # 4.4 MB
├── user_item_matrix_weighted.npz     # 9.2 MB
├── mappings.pkl                      # 3.2 MB
├── article_popularity.pkl            # 1.5 MB
├── user_profiles.json                # 64 MB
├── user_profiles_enriched.pkl        # Plus compact
├── embeddings_filtered.pkl           # 38 MB
├── articles_metadata.csv             # 11 MB
├── interaction_stats_enriched.csv    # 426 MB
└── preprocessing_stats.json          # < 1 KB

Total: ~560 MB
```

### Fichiers Lite (déploiement)

```
/home/ser/Bureau/P10_reco/models_lite/
├── user_item_matrix_weighted.npz     # ~2 MB
├── mappings.pkl                      # ~300 KB
├── article_popularity.pkl            # ~150 KB
├── user_profiles_enriched.pkl        # ~5 MB
├── embeddings_filtered.pkl           # ~4 MB
└── articles_metadata.csv             # ~1 MB

Total: ~86 MB (réduction de 96%)
```

### Logs et rapports

```
/home/ser/Bureau/P10_reco_new/logs/
└── pipeline_20251231_143022.log      # Logs complets

/home/ser/Bureau/P10_reco_new/
└── PIPELINE_REPORT_20251231_143022.md  # Rapport d'exécution
```

## Vérification des résultats

### Test rapide des modèles

```python
import pickle
from pathlib import Path
from scipy.sparse import load_npz

models_dir = Path("/home/ser/Bureau/P10_reco/models")

# Charger matrice
matrix = load_npz(models_dir / "user_item_matrix_weighted.npz")
print(f"Matrice: {matrix.shape} - {matrix.nnz:,} interactions")

# Charger profils
with open(models_dir / "user_profiles_enriched.pkl", 'rb') as f:
    profiles = pickle.load(f)
print(f"Profils: {len(profiles):,} utilisateurs")

# Test sur un utilisateur
user = profiles[58]
print(f"\nUser 58:")
print(f"  - Articles lus: {user['num_articles']}")
print(f"  - Score moyen: {user['avg_weight']:.3f}")
```

### Test de l'API localement

```bash
cd app/
streamlit run streamlit_api_v2.py
# → http://localhost:8501
```

## Résolution de problèmes

### Erreur: Mémoire insuffisante

**Symptôme:** `MemoryError` ou `Killed`

**Solutions:**
1. Fermer les applications inutiles
2. Utiliser la version optimisée: `compute_weights_memory_optimized.py` (déjà utilisée)
3. Augmenter le swap: `sudo swapon -s`

### Erreur: Dataset introuvable

**Symptôme:** `Dataset introuvable: /home/ser/Bureau/P10_reco/news-portal-user-interactions-by-globocom`

**Solution:**
```bash
# Vérifier le chemin
ls /home/ser/Bureau/P10_reco/news-portal-user-interactions-by-globocom

# Si nécessaire, modifier dans le script:
# Ligne 12: DATA_DIR="/chemin/vers/dataset"
```

### Erreur: Dépendances manquantes

**Symptôme:** `ModuleNotFoundError: No module named 'pandas'`

**Solution:**
```bash
pip install pandas numpy scipy scikit-learn
```

### Fichiers déjà existants

Le script demande confirmation avant d'écraser les fichiers existants (étape 3).

**Options:**
- `o` (oui) : Recalculer
- `n` (non) : Conserver l'existant et continuer

## Comparaison Kaggle vs Local

| Aspect | Kaggle | Local |
|--------|--------|-------|
| **Temps max** | 6h | Illimité |
| **RAM** | 16 GB | Variable |
| **GPU** | Disponible | Non (pas nécessaire) |
| **Stockage** | 20 GB temporaire | Permanent |
| **Debugging** | Limité | Total |
| **Démo live** | ❌ | ✅ |
| **Coût** | Gratuit | Gratuit |
| **Contrôle** | Moyen | Total |

## Pour la présentation

### Préparation

1. **Exécuter le pipeline complet** (une fois)
   ```bash
   ./run_pipeline_complet.sh
   ```

2. **Vérifier les modèles**
   ```bash
   cat PIPELINE_REPORT_*.md
   ```

3. **Tester l'API Streamlit**
   ```bash
   cd app/
   ./lancer_app.sh
   ```

### Démonstration

**Option 1: Montrer les logs**
```bash
# Afficher le dernier rapport
cat PIPELINE_REPORT_*.md | less
```

**Option 2: Exécution partielle**
```bash
# Montrer juste l'étape de preprocessing (rapide)
python3 data_preparation/data_preprocessing_optimized.py
```

**Option 3: Application Streamlit**
- Lancer l'app
- Générer des recommandations en direct
- Montrer l'interprétabilité (catégories, profils, etc.)

## Avantages pour les livrables

✅ **Script reproductible** - Un seul fichier à exécuter
✅ **Logs détaillés** - Traçabilité complète
✅ **Rapport automatique** - Statistiques + fichiers générés
✅ **Validation incluse** - Tests de chargement
✅ **Modulaire** - Peut relancer une seule étape
✅ **Documentation** - Commentaires + bannières claires

## Prochaines étapes

Après exécution du pipeline:

1. ✅ Modèles générés et validés
2. 📤 Upload sur Azure/AWS (optionnel)
3. 🧪 Évaluation (benchmark 500 users)
4. 📊 Application Streamlit prête
5. 🎓 Présentation devant le jury

---

**Créé le:** 31 Décembre 2025
**Version:** 1.0
**Statut:** ✅ Prêt pour exécution
