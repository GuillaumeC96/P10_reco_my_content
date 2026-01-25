# Optimisation Mémoire - Version v8

## Problème
La v8 crashait à cause d'une consommation mémoire excessive (>30 Go).

## Solution: `compute_weights_memory_optimized.py`

### Optimisations Implémentées

1. **Filtrage des Interactions < 30 secondes** ⚡ NOUVEAU
   - Règle métier: Si temps de lecture < 30s, la 2ème pub ne s'affiche pas
   - Ces interactions sont **complètement supprimées** (article non lu)
   - Améliore la qualité des recommandations

2. **Traitement par Batches de Fichiers**
   - Au lieu de charger tous les 336 fichiers d'un coup
   - Traitement par batches de 50 fichiers
   - Libération mémoire entre chaque batch

3. **Réduction des Threads**
   - Passage de 28 à 12 threads
   - Moins de parallélisme = moins de mémoire consommée
   - Toujours efficace grâce aux batches

4. **Chunks d'Utilisateurs**
   - Traitement des profils par chunks de 5000 users
   - Évite de garder tous les profils en mémoire avant sauvegarde

5. **Libération Mémoire Agressive**
   - `del` + `gc.collect()` après chaque étape
   - Conversion en types économes (int32 au lieu de int64)

6. **Monitoring en Temps Réel**
   - Utilisation de `psutil` pour surveiller la RAM
   - Vérification automatique de la limite 30 Go
   - Arrêt automatique si dépassement

## Comment Utiliser

### Option 1: Lancement Simple
```bash
cd /home/ser/Bureau/P10_reco_new
python3 data_preparation/compute_weights_memory_optimized.py
```

### Option 2: Avec Script de Monitoring (Recommandé)
```bash
./lancer_compute_optimized.sh
```

### Option 3: Monitorer Pendant l'Exécution
Dans un terminal séparé:
```bash
# Voir la mémoire en temps réel
watch -n 5 'ps aux | grep compute_weights_memory_optimized | grep -v grep | awk "{print \$6/1024/1024 \" Go\"}"'

# Ou plus détaillé
watch -n 5 'free -h && ps aux | grep python | grep -v grep'
```

## Paramètres Ajustables

Dans `compute_weights_memory_optimized.py`:

```python
MAX_MEMORY_GB = 30      # Limite mémoire (défaut: 30 Go)
N_CORES = 12            # Threads (défaut: 12)
BATCH_SIZE = 50         # Fichiers par batch (défaut: 50)
USER_CHUNK_SIZE = 5000  # Users par chunk (défaut: 5000)
```

### Si vous avez moins de 30 Go disponibles:
- Réduire `MAX_MEMORY_GB` (ex: 20)
- Réduire `BATCH_SIZE` (ex: 30)
- Réduire `N_CORES` (ex: 8)
- Réduire `USER_CHUNK_SIZE` (ex: 3000)

### Si vous voulez aller plus vite (avec plus de RAM):
- Augmenter `BATCH_SIZE` (ex: 100)
- Augmenter `N_CORES` (ex: 16)
- ⚠️ **NE PAS** dépasser 30 Go ou ajuster `MAX_MEMORY_GB`

## Temps d'Exécution Estimé

- **v8 originale**: ~2-3h (crash si >30 Go)
- **Version optimisée**: ~3-4h (stable, <30 Go garanti)

Le léger ralentissement est compensé par la stabilité et l'absence de crash.

## Vérification après Exécution

```bash
# Vérifier les fichiers de sortie
ls -lh /home/ser/Bureau/P10_reco/models/user_profiles_enriched.*
ls -lh /home/ser/Bureau/P10_reco/models/interaction_stats_enriched.csv

# Vérifier le contenu
python3 -c "
import json
with open('/home/ser/Bureau/P10_reco/models/user_profiles_enriched.json') as f:
    profiles = json.load(f)
    print(f'Utilisateurs: {len(profiles):,}')
    print(f'Premier user:', list(profiles.keys())[0])
"
```

## En Cas de Problème

1. **Crash mémoire malgré l'optimisation**
   - Réduire `BATCH_SIZE` à 30
   - Réduire `N_CORES` à 8
   - Vérifier qu'aucun autre processus lourd ne tourne

2. **Trop lent**
   - Augmenter `N_CORES` (si RAM disponible)
   - Vérifier que les disques ne sont pas saturés

3. **Erreur de fichier manquant**
   - Vérifier que `/home/ser/Bureau/P10_reco/news-portal-user-interactions-by-globocom/clicks/` existe
   - Vérifier les permissions

## Comparaison v8 vs Optimisée

| Aspect | v8 Originale | Version Optimisée |
|--------|--------------|-------------------|
| Mémoire max | ~40-50 Go (crash) | <30 Go (garanti) |
| Threads | 28 | 12 |
| Chargement | Tout en mémoire | Par batches |
| Monitoring | Non | Oui (psutil) |
| Stabilité | Crash | Stable |
| Vitesse | ⚡⚡⚡ | ⚡⚡ |
| Fiabilité | ⚠️ | ✅ |
