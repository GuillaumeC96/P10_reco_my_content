#!/usr/bin/env python3
"""
Script pour remplacer toutes les références AWS par Azure dans les livrables
"""

import os
import re
from pathlib import Path

# Dossier des livrables
LIVRABLES_DIR = "/home/ser/Bureau/P10_reco_new/LIVRABLES_PROJET10_Cassez_Guillaume_012026"

# Mappings de remplacement
REPLACEMENTS = [
    # Services AWS → Azure
    (r"AWS Lambda", "Azure Functions"),
    (r"Lambda Function", "Azure Function"),
    (r"Azure Functions Function", "Azure Function"),
    (r"lambda function", "Azure function"),
    (r"AWS S3", "Azure Blob Storage"),
    (r"Amazon S3", "Azure Blob Storage"),
    (r"AWS Kinesis", "Azure Event Hubs"),
    (r"AWS CloudWatch", "Azure Application Insights"),
    (r"AWS SageMaker", "Azure Machine Learning"),
    (r"AWS API Gateway", "Azure API Management"),
    (r"AWS ElastiCache", "Azure Cache for Redis"),
    (r"AWS Batch", "Azure Batch"),

    # Noms de fichiers et chemins
    (r"upload_to_s3\.py", "upload_to_azure.py"),
    (r"lambda_function\.py", "__init__.py"),
    (r"lambda/", "azure_function/"),

    # URLs et chemins S3
    (r"s3://my-content-reco-bucket", "mycontent-models"),
    (r"s3://my-content-datalake", "mycontent-datalake"),
    (r"https://[a-z0-9\-]+\.execute-api\.[a-z0-9\-]+\.amazonaws\.com", "https://func-mycontent-reco-1269.azurewebsites.net/api"),
    (r"https://your-lambda-url\.us-east-1\.on\.aws/", "https://func-mycontent-reco-1269.azurewebsites.net/api/recommend"),
    (r"https://[a-z0-9\-]+\.azurewebsites\.net\.us-east-1\.on\.aws/", "https://func-mycontent-reco-1269.azurewebsites.net/api/recommend"),

    # Commandes AWS CLI
    (r"aws s3 mb s3://my-content-reco-bucket", "az storage container create --name mycontent-models"),
    (r"aws s3", "az storage blob"),
    (r"aws lambda", "func azure functionapp"),
    (r"AWS CLI", "Azure CLI"),

    # SDKs et dépendances
    (r"boto3", "azure-storage-blob"),
    (r"Boto3", "Azure Storage SDK"),

    # Permissions et IAM
    (r"IAM role", "Managed Identity"),
    (r"IAM permissions", "Azure RBAC permissions"),
    (r"IAM", "Azure RBAC"),
    (r'"s3:GetObject"', '"Microsoft.Storage/storageAccounts/blobServices/containers/blobs/read"'),
    (r'"s3:ListBucket"', '"Microsoft.Storage/storageAccounts/blobServices/containers/read"'),
    (r"arn:aws:s3:::my-content-reco-bucket", "mycontent-models container"),
    (r"arn:aws:logs:\*:\*:\*", "Azure Application Insights workspace"),

    # Configurations
    (r"Azure Blob Storage_BUCKET", "AZURE_STORAGE_CONTAINER"),
    (r"Azure Blob Storage_MODELS_PREFIX", "MODELS_PREFIX"),
    (r"Function URL", "HTTP Trigger URL"),
    (r"Lambda URL", "Azure Function URL"),

    # Logs et monitoring
    (r"/aws/lambda/MyContentRecommendation", "func-mycontent-reco-logs"),

    # Architecture et structure
    (r"Bucket:", "Container:"),
    (r"bucket", "container"),
    (r"Region: us-east-1", "Region: France Central"),

    # Spécifique LAMBDA → Azure Functions
    (r"Azure LAMBDA", "AZURE FUNCTION"),
    (r"MODE LAMBDA", "MODE AZURE FUNCTION"),
    (r"LAMBDA \(", "AZURE FUNCTION ("),
    (r"la Lambda", "l'Azure Function"),
    (r"Le Lambda", "L'Azure Function"),
]

def fix_file(filepath):
    """Corrige les références AWS dans un fichier"""
    try:
        # Lire le contenu
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content

        # Appliquer tous les remplacements
        for pattern, replacement in REPLACEMENTS:
            content = re.sub(pattern, replacement, content, flags=re.IGNORECASE if pattern.islower() else 0)

        # Écrire seulement si modifié
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
    except Exception as e:
        print(f"❌ Erreur avec {filepath}: {e}")
        return False

    return False

def main():
    print("=" * 80)
    print("CORRECTION DES RÉFÉRENCES AWS → AZURE DANS LES LIVRABLES")
    print("=" * 80)
    print()

    # Extensions à traiter
    extensions = ['.md', '.txt', '.py', '.json']

    # Parcourir tous les fichiers
    modified_count = 0
    total_count = 0

    for root, dirs, files in os.walk(LIVRABLES_DIR):
        # Ignorer les dossiers cachés et __pycache__
        dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']

        for file in files:
            filepath = Path(root) / file

            # Vérifier l'extension
            if filepath.suffix not in extensions:
                continue

            total_count += 1

            # Corriger le fichier
            if fix_file(filepath):
                modified_count += 1
                print(f"✓ {filepath.relative_to(LIVRABLES_DIR)}")

    print()
    print("=" * 80)
    print(f"RÉSUMÉ: {modified_count}/{total_count} fichiers modifiés")
    print("=" * 80)

if __name__ == "__main__":
    main()
