"""
Fonctions utilitaires pour Azure Functions
Équivalent de utils.py pour Azure Blob Storage
"""

import os
import logging
from pathlib import Path
from azure.storage.blob import BlobServiceClient

logger = logging.getLogger(__name__)


def download_models_from_blob(storage_account_name: str, container_name: str,
                                prefix: str = '', local_path: str = '/tmp/models'):
    """
    Télécharge les modèles depuis Azure Blob Storage vers le système de fichiers local

    Args:
        storage_account_name: Nom du Storage Account Azure
        container_name: Nom du conteneur Blob
        prefix: Préfixe des objets (ex: 'models/')
        local_path: Chemin local où sauvegarder les fichiers

    Returns:
        bool: True si succès, False sinon
    """
    try:
        # Créer le dossier local
        Path(local_path).mkdir(parents=True, exist_ok=True)

        # Récupérer la connection string depuis les variables d'environnement
        # Azure Functions définit automatiquement AzureWebJobsStorage
        conn_string = os.environ.get('AzureWebJobsStorage')

        if not conn_string:
            logger.error("AzureWebJobsStorage non défini dans les variables d'environnement")
            return False

        # Créer le BlobServiceClient
        blob_service_client = BlobServiceClient.from_connection_string(conn_string)
        container_client = blob_service_client.get_container_client(container_name)

        # Lister les blobs dans le conteneur
        logger.info(f"Téléchargement des modèles depuis {storage_account_name}/{container_name}")
        blobs = container_client.list_blobs(name_starts_with=prefix)

        downloaded_count = 0
        for blob in blobs:
            if blob.name.endswith('/'):  # Skip directories
                continue

            # Créer le chemin local (garder juste le nom du fichier)
            blob_name = os.path.basename(blob.name)
            local_file = os.path.join(local_path, blob_name)

            logger.info(f"Téléchargement {blob.name} vers {local_file} ({blob.size / 1024 / 1024:.1f} MB)")

            # Télécharger le blob
            blob_client = container_client.get_blob_client(blob.name)
            with open(local_file, "wb") as f:
                download_stream = blob_client.download_blob()
                f.write(download_stream.readall())

            downloaded_count += 1

        logger.info(f"✓ {downloaded_count} fichiers téléchargés depuis Blob Storage")
        return True

    except Exception as e:
        logger.error(f"Erreur lors du téléchargement depuis Blob Storage: {e}", exc_info=True)
        return False


def list_blobs(storage_account_name: str, container_name: str, prefix: str = ''):
    """
    Liste les blobs dans un conteneur Azure Blob Storage

    Args:
        storage_account_name: Nom du Storage Account
        container_name: Nom du conteneur
        prefix: Préfixe des blobs

    Returns:
        list: Liste des noms de blobs
    """
    try:
        conn_string = os.environ.get('AzureWebJobsStorage')

        if not conn_string:
            logger.error("AzureWebJobsStorage non défini")
            return []

        blob_service_client = BlobServiceClient.from_connection_string(conn_string)
        container_client = blob_service_client.get_container_client(container_name)

        blobs = container_client.list_blobs(name_starts_with=prefix)
        return [blob.name for blob in blobs]

    except Exception as e:
        logger.error(f"Erreur lors du listing des blobs: {e}")
        return []
