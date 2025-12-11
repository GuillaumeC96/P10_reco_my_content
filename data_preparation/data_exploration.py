"""
Script d'exploration et analyse du dataset Globo.com
Permet de comprendre la structure des données avant preprocessing
"""

import pandas as pd
import numpy as np
import pickle
import glob
import os
from pathlib import Path

# Configuration des chemins
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "news-portal-user-interactions-by-globocom"
CLICKS_DIR = DATA_DIR / "clicks"

def explore_metadata():
    """Explore les métadonnées des articles"""
    print("=" * 80)
    print("EXPLORATION DES MÉTADONNÉES ARTICLES")
    print("=" * 80)

    metadata_path = DATA_DIR / "articles_metadata.csv"
    df_metadata = pd.read_csv(metadata_path)

    print(f"\nNombre total d'articles : {len(df_metadata):,}")
    print(f"\nPremières lignes :")
    print(df_metadata.head(10))

    print(f"\nInformations sur les colonnes :")
    print(df_metadata.info())

    print(f"\nStatistiques descriptives :")
    print(df_metadata.describe())

    print(f"\nNombre de catégories uniques : {df_metadata['category_id'].nunique()}")
    print(f"Nombre d'éditeurs uniques : {df_metadata['publisher_id'].nunique()}")

    print(f"\nDistribution des catégories (top 10) :")
    print(df_metadata['category_id'].value_counts().head(10))

    print(f"\nDistribution du nombre de mots :")
    print(f"  Min: {df_metadata['words_count'].min()}")
    print(f"  Max: {df_metadata['words_count'].max()}")
    print(f"  Moyenne: {df_metadata['words_count'].mean():.1f}")
    print(f"  Médiane: {df_metadata['words_count'].median():.1f}")

    # Valeurs manquantes
    print(f"\nValeurs manquantes :")
    print(df_metadata.isnull().sum())

    return df_metadata

def explore_embeddings():
    """Explore les embeddings pré-calculés"""
    print("\n" + "=" * 80)
    print("EXPLORATION DES EMBEDDINGS")
    print("=" * 80)

    embeddings_path = DATA_DIR / "articles_embeddings.pickle"

    print(f"\nTaille du fichier : {os.path.getsize(embeddings_path) / (1024**2):.2f} MB")

    # Charger les embeddings
    print("\nChargement des embeddings (peut prendre du temps)...")
    with open(embeddings_path, 'rb') as f:
        embeddings = pickle.load(f)

    print(f"\nType : {type(embeddings)}")

    if isinstance(embeddings, dict):
        print(f"Nombre d'entrées : {len(embeddings)}")
        # Examiner un embedding
        first_key = list(embeddings.keys())[0]
        first_embedding = embeddings[first_key]
        print(f"Exemple de clé : {first_key}")
        print(f"Dimension d'un embedding : {len(first_embedding) if hasattr(first_embedding, '__len__') else 'N/A'}")
        print(f"Type de valeur : {type(first_embedding)}")
    elif isinstance(embeddings, np.ndarray):
        print(f"Shape : {embeddings.shape}")
        print(f"Dtype : {embeddings.dtype}")
        print(f"Taille en mémoire : {embeddings.nbytes / (1024**2):.2f} MB")

    return embeddings

def explore_clicks_sample():
    """Explore le fichier d'exemple de clics"""
    print("\n" + "=" * 80)
    print("EXPLORATION DES CLICS (SAMPLE)")
    print("=" * 80)

    sample_path = DATA_DIR / "clicks_sample.csv"
    df_sample = pd.read_csv(sample_path)

    print(f"\nNombre de lignes dans le sample : {len(df_sample):,}")
    print(f"\nPremières lignes :")
    print(df_sample.head(10))

    print(f"\nInformations sur les colonnes :")
    print(df_sample.info())

    print(f"\nStatistiques descriptives :")
    print(df_sample.describe())

    print(f"\nNombre d'utilisateurs uniques : {df_sample['user_id'].nunique():,}")
    print(f"Nombre de sessions uniques : {df_sample['session_id'].nunique():,}")
    print(f"Nombre d'articles cliqués uniques : {df_sample['click_article_id'].nunique():,}")

    print(f"\nDistribution des tailles de session :")
    print(df_sample['session_size'].value_counts().sort_index().head(10))

    print(f"\nDistribution des environnements :")
    print(df_sample['click_environment'].value_counts())

    print(f"\nDistribution des types d'appareils :")
    print(df_sample['click_deviceGroup'].value_counts())

    print(f"\nTop 10 utilisateurs les plus actifs :")
    user_activity = df_sample['user_id'].value_counts().head(10)
    print(user_activity)

    # Valeurs manquantes
    print(f"\nValeurs manquantes :")
    print(df_sample.isnull().sum())

    return df_sample

def explore_clicks_all():
    """Explore tous les fichiers de clics"""
    print("\n" + "=" * 80)
    print("EXPLORATION DE TOUS LES FICHIERS DE CLICS")
    print("=" * 80)

    click_files = sorted(glob.glob(str(CLICKS_DIR / "clicks_hour_*.csv")))
    print(f"\nNombre de fichiers de clics : {len(click_files)}")

    if len(click_files) > 0:
        print(f"\nExemple de nom de fichier : {os.path.basename(click_files[0])}")

        # Charger le premier fichier pour examiner la structure
        print(f"\nExamen du premier fichier...")
        df_first = pd.read_csv(click_files[0])
        print(f"Nombre de lignes : {len(df_first):,}")
        print(f"Colonnes : {list(df_first.columns)}")

        # Estimer le nombre total de lignes
        print(f"\nEstimation du nombre total de lignes...")
        total_lines = 0
        for i, file in enumerate(click_files[:10]):  # Charger seulement les 10 premiers
            df = pd.read_csv(file)
            total_lines += len(df)
            if i == 0:
                print(f"  Fichier {i+1}: {len(df):,} lignes")

        estimated_total = (total_lines / min(10, len(click_files))) * len(click_files)
        print(f"\nEstimation totale (basée sur {min(10, len(click_files))} fichiers) : ~{estimated_total:,.0f} interactions")

    return click_files

def analyze_user_behavior():
    """Analyse le comportement des utilisateurs"""
    print("\n" + "=" * 80)
    print("ANALYSE DU COMPORTEMENT UTILISATEUR")
    print("=" * 80)

    sample_path = DATA_DIR / "clicks_sample.csv"
    df_sample = pd.read_csv(sample_path)

    # Statistiques par utilisateur
    user_stats = df_sample.groupby('user_id').agg({
        'click_article_id': 'count',
        'session_id': 'nunique',
        'click_timestamp': lambda x: (x.max() - x.min()) / 1000 / 60  # durée en minutes
    }).rename(columns={
        'click_article_id': 'num_clicks',
        'session_id': 'num_sessions',
        'click_timestamp': 'duration_minutes'
    })

    print(f"\nStatistiques par utilisateur :")
    print(user_stats.describe())

    print(f"\nDistribution du nombre de clics par utilisateur :")
    print(user_stats['num_clicks'].value_counts().sort_index().head(10))

    return user_stats

def main():
    """Fonction principale d'exploration"""
    print("\n")
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 20 + "EXPLORATION DU DATASET GLOBO.COM" + " " * 26 + "║")
    print("╚" + "═" * 78 + "╝")

    try:
        # 1. Explorer les métadonnées
        df_metadata = explore_metadata()

        # 2. Explorer les embeddings
        embeddings = explore_embeddings()

        # 3. Explorer le sample de clics
        df_sample = explore_clicks_sample()

        # 4. Explorer tous les fichiers de clics
        click_files = explore_clicks_all()

        # 5. Analyser le comportement utilisateur
        user_stats = analyze_user_behavior()

        # Résumé final
        print("\n" + "=" * 80)
        print("RÉSUMÉ DE L'EXPLORATION")
        print("=" * 80)
        print(f"\n✓ Articles : {len(df_metadata):,}")
        print(f"✓ Catégories : {df_metadata['category_id'].nunique()}")
        print(f"✓ Éditeurs : {df_metadata['publisher_id'].nunique()}")
        print(f"✓ Fichiers de clics : {len(click_files)}")
        print(f"✓ Utilisateurs (sample) : {df_sample['user_id'].nunique():,}")
        print(f"✓ Dimension embeddings : À vérifier après chargement complet")

        print("\n✅ Exploration terminée avec succès!")

    except Exception as e:
        print(f"\n❌ Erreur lors de l'exploration : {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
