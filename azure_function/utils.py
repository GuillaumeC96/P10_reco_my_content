"""
Fonctions utilitaires pour la Lambda Function
"""

import boto3
import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def download_models_from_s3(bucket_name: str, prefix: str, local_path: str = '/tmp/models'):
    """
    Télécharge les modèles depuis S3 vers le système de fichiers local Lambda

    Args:
        bucket_name: Nom du bucket S3
        prefix: Préfixe des objets S3 (ex: 'models/')
        local_path: Chemin local où sauvegarder les fichiers

    Returns:
        bool: True si succès, False sinon
    """
    try:
        s3_client = boto3.client('s3')

        # Créer le dossier local
        Path(local_path).mkdir(parents=True, exist_ok=True)

        # Lister les objets dans S3
        logger.info(f"Téléchargement des modèles depuis s3://{bucket_name}/{prefix}")
        response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=prefix)

        if 'Contents' not in response:
            logger.error(f"Aucun fichier trouvé dans s3://{bucket_name}/{prefix}")
            return False

        # Télécharger chaque fichier
        for obj in response['Contents']:
            key = obj['Key']
            if key.endswith('/'):  # Skip directories
                continue

            # Créer le chemin local
            local_file = os.path.join(local_path, os.path.basename(key))

            logger.info(f"Téléchargement {key} vers {local_file}")
            s3_client.download_file(bucket_name, key, local_file)

        logger.info("✓ Tous les modèles ont été téléchargés")
        return True

    except Exception as e:
        logger.error(f"Erreur lors du téléchargement depuis S3: {e}")
        return False

def upload_models_to_s3(local_path: str, bucket_name: str, prefix: str):
    """
    Upload les modèles locaux vers S3

    Args:
        local_path: Chemin local des fichiers
        bucket_name: Nom du bucket S3
        prefix: Préfixe des objets S3

    Returns:
        bool: True si succès, False sinon
    """
    try:
        s3_client = boto3.client('s3')

        # Lister tous les fichiers locaux
        local_files = list(Path(local_path).glob('*'))

        if not local_files:
            logger.error(f"Aucun fichier trouvé dans {local_path}")
            return False

        logger.info(f"Upload de {len(local_files)} fichiers vers s3://{bucket_name}/{prefix}")

        for local_file in local_files:
            if local_file.is_file():
                key = f"{prefix}{local_file.name}"
                logger.info(f"Upload {local_file} vers {key}")
                s3_client.upload_file(str(local_file), bucket_name, key)

        logger.info("✓ Tous les modèles ont été uploadés")
        return True

    except Exception as e:
        logger.error(f"Erreur lors de l'upload vers S3: {e}")
        return False

def format_article_info(article_id: int, metadata_df):
    """
    Formate les informations d'un article pour l'affichage

    Args:
        article_id: ID de l'article
        metadata_df: DataFrame des métadonnées

    Returns:
        dict: Informations formatées
    """
    article = metadata_df[metadata_df['article_id'] == article_id]

    if article.empty:
        return {
            'article_id': article_id,
            'error': 'Article non trouvé'
        }

    row = article.iloc[0]

    return {
        'article_id': int(article_id),
        'category_id': int(row['category_id']),
        'publisher_id': int(row['publisher_id']),
        'words_count': int(row['words_count']),
        'created_at': int(row['created_at_ts'])
    }
