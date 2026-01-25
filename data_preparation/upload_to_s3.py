"""
Script pour uploader les modèles vers AWS S3
À exécuter après le preprocessing
"""

import boto3
import os
from pathlib import Path
import json
import argparse

def upload_to_s3(models_dir: str, bucket_name: str, prefix: str = 'models/'):
    """
    Upload les fichiers de modèles vers S3

    Args:
        models_dir: Chemin local du dossier models
        bucket_name: Nom du bucket S3
        prefix: Préfixe dans S3 (ex: 'models/')
    """
    print("=" * 80)
    print("UPLOAD DES MODÈLES VERS S3")
    print("=" * 80)

    # Initialiser le client S3
    try:
        s3_client = boto3.client('s3')
        print(f"\n✓ Connexion à AWS S3 établie")
    except Exception as e:
        print(f"\n❌ Erreur de connexion à AWS: {e}")
        print("Vérifiez vos credentials AWS (aws configure)")
        return False

    # Vérifier que le bucket existe
    try:
        s3_client.head_bucket(Bucket=bucket_name)
        print(f"✓ Bucket '{bucket_name}' trouvé")
    except Exception as e:
        print(f"\n❌ Bucket '{bucket_name}' non trouvé: {e}")
        print(f"\nPour créer le bucket, exécutez:")
        print(f"  aws s3 mb s3://{bucket_name}")
        return False

    # Lister les fichiers à uploader
    models_path = Path(models_dir)
    if not models_path.exists():
        print(f"\n❌ Le dossier '{models_dir}' n'existe pas")
        return False

    files_to_upload = list(models_path.glob('*'))
    model_files = [f for f in files_to_upload if f.is_file()]

    if not model_files:
        print(f"\n❌ Aucun fichier trouvé dans '{models_dir}'")
        return False

    print(f"\n📁 {len(model_files)} fichiers à uploader:")
    for f in model_files:
        size_mb = f.stat().st_size / (1024 * 1024)
        print(f"  - {f.name} ({size_mb:.2f} MB)")

    # Confirmation
    total_size = sum(f.stat().st_size for f in model_files) / (1024 * 1024)
    print(f"\nTaille totale: {total_size:.2f} MB")

    confirm = input("\n⚠️  Confirmer l'upload vers S3? (oui/non): ")
    if confirm.lower() not in ['oui', 'yes', 'y', 'o']:
        print("Upload annulé")
        return False

    # Upload des fichiers
    print("\n🚀 Upload en cours...")
    uploaded = []
    failed = []

    for local_file in model_files:
        s3_key = f"{prefix}{local_file.name}"

        try:
            print(f"\n  Uploading {local_file.name} -> s3://{bucket_name}/{s3_key}")

            # Upload avec progress
            file_size = local_file.stat().st_size
            s3_client.upload_file(
                str(local_file),
                bucket_name,
                s3_key,
                Callback=lambda bytes_transferred: print(f"\r    Progress: {bytes_transferred}/{file_size} bytes", end='')
            )

            print(f"\r    ✓ {local_file.name} uploadé avec succès")
            uploaded.append(s3_key)

        except Exception as e:
            print(f"\r    ❌ Erreur pour {local_file.name}: {e}")
            failed.append(local_file.name)

    # Résumé
    print("\n" + "=" * 80)
    print("RÉSUMÉ DE L'UPLOAD")
    print("=" * 80)
    print(f"\n✓ Fichiers uploadés: {len(uploaded)}/{len(model_files)}")

    if uploaded:
        print("\nFichiers disponibles sur S3:")
        for key in uploaded:
            print(f"  - s3://{bucket_name}/{key}")

    if failed:
        print(f"\n❌ Échecs: {len(failed)}")
        for name in failed:
            print(f"  - {name}")

    # Instructions pour la Lambda
    if len(uploaded) == len(model_files):
        print("\n✅ Tous les fichiers ont été uploadés avec succès!")
        print("\n📝 Prochaines étapes:")
        print(f"  1. Configurer la variable d'environnement de la Lambda:")
        print(f"     S3_BUCKET={bucket_name}")
        print(f"     S3_MODELS_PREFIX={prefix}")
        print(f"  2. Ajouter les permissions IAM pour que la Lambda puisse lire depuis S3")
        print(f"  3. Déployer la Lambda Function")

        return True
    else:
        return False

def main():
    parser = argparse.ArgumentParser(description='Upload des modèles vers S3')
    parser.add_argument(
        '--bucket',
        type=str,
        required=True,
        help='Nom du bucket S3'
    )
    parser.add_argument(
        '--prefix',
        type=str,
        default='models/',
        help='Préfixe dans S3 (défaut: models/)'
    )
    parser.add_argument(
        '--models-dir',
        type=str,
        default='../models',
        help='Chemin du dossier models local (défaut: ../models)'
    )

    args = parser.parse_args()

    print("\n")
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 25 + "UPLOAD VERS AWS S3" + " " * 35 + "║")
    print("╚" + "═" * 78 + "╝")

    # Résoudre le chemin absolu
    base_dir = Path(__file__).parent.parent
    models_dir = (base_dir / args.models_dir).resolve()

    success = upload_to_s3(
        models_dir=str(models_dir),
        bucket_name=args.bucket,
        prefix=args.prefix
    )

    if success:
        print("\n✅ Upload terminé avec succès!")
        exit(0)
    else:
        print("\n❌ Upload échoué")
        exit(1)

if __name__ == "__main__":
    main()
