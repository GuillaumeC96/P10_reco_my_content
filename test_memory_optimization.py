#!/usr/bin/env python3
"""
Test rapide de la version optimisée mémoire
Vérifie que le script démarre et que le monitoring fonctionne
"""

import psutil
import os

print("="*60)
print("TEST OPTIMISATION MÉMOIRE")
print("="*60)

# Test 1: psutil
print("\n1. Test psutil...")
try:
    process = psutil.Process()
    mem_gb = process.memory_info().rss / (1024**3)
    print(f"   ✓ psutil OK - Mémoire actuelle: {mem_gb:.2f} Go")
except Exception as e:
    print(f"   ✗ Erreur psutil: {e}")
    exit(1)

# Test 2: Fichiers clicks
print("\n2. Test accès fichiers clicks...")
clicks_path = "/home/ser/Bureau/P10_reco/news-portal-user-interactions-by-globocom/clicks/"
if os.path.exists(clicks_path):
    import glob
    click_files = glob.glob(f"{clicks_path}clicks_hour_*.csv")
    print(f"   ✓ Répertoire OK - {len(click_files)} fichiers trouvés")
else:
    print(f"   ✗ Répertoire non trouvé: {clicks_path}")
    exit(1)

# Test 3: Répertoire de sortie
print("\n3. Test répertoire sortie...")
output_path = "/home/ser/Bureau/P10_reco/models/"
os.makedirs(output_path, exist_ok=True)
if os.path.exists(output_path) and os.access(output_path, os.W_OK):
    print(f"   ✓ Répertoire OK: {output_path}")
else:
    print(f"   ✗ Répertoire non accessible: {output_path}")
    exit(1)

# Test 4: RAM disponible
print("\n4. Test RAM disponible...")
mem = psutil.virtual_memory()
total_gb = mem.total / (1024**3)
available_gb = mem.available / (1024**3)
used_gb = mem.used / (1024**3)
print(f"   Total: {total_gb:.1f} Go")
print(f"   Utilisée: {used_gb:.1f} Go ({mem.percent}%)")
print(f"   Disponible: {available_gb:.1f} Go")

if available_gb < 30:
    print(f"   ⚠️  Attention: moins de 30 Go disponibles!")
    print(f"   Conseil: libérer de la RAM ou réduire MAX_MEMORY_GB dans le script")
else:
    print(f"   ✓ Suffisamment de RAM pour la limite de 30 Go")

# Test 5: Nombre de cores
print("\n5. Test CPU...")
import multiprocessing
n_cores = multiprocessing.cpu_count()
print(f"   ✓ {n_cores} cores disponibles (script utilise 12)")

# Test 6: Test de chargement d'un fichier
print("\n6. Test chargement d'un fichier...")
try:
    import pandas as pd
    test_file = click_files[0]
    df = pd.read_csv(test_file)
    print(f"   ✓ Fichier chargé: {len(df):,} lignes")
    mem_after = process.memory_info().rss / (1024**3)
    print(f"   Mémoire après chargement: {mem_after:.2f} Go")
    del df
    import gc
    gc.collect()
    mem_released = process.memory_info().rss / (1024**3)
    print(f"   Mémoire après libération: {mem_released:.2f} Go")
except Exception as e:
    print(f"   ✗ Erreur: {e}")
    exit(1)

print("\n" + "="*60)
print("✅ TOUS LES TESTS PASSÉS")
print("="*60)
print("\nVous pouvez lancer le calcul complet:")
print("  ./lancer_compute_optimized.sh")
print("\nOu directement:")
print("  python3 data_preparation/compute_weights_memory_optimized.py")
print("")
