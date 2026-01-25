#!/usr/bin/env python3
"""
Script de correction complète : AWS → Azure
Supprime toutes les références AWS et les remplace par Azure
"""

import os
import shutil
from pathlib import Path
import re

# Couleurs pour affichage
GREEN = '\033[0;32m'
BLUE = '\033[0;34m'
YELLOW = '\033[1;33m'
RED = '\033[0;31m'
NC = '\033[0m'  # No Color

def print_section(title):
    print(f"\n{BLUE}{'='*70}{NC}")
    print(f"{BLUE}{title}{NC}")
    print(f"{BLUE}{'='*70}{NC}\n")

def print_success(msg):
    print(f"{GREEN}✅ {msg}{NC}")

def print_warning(msg):
    print(f"{YELLOW}⚠️  {msg}{NC}")

def print_error(msg):
    print(f"{RED}❌ {msg}{NC}")

def replace_in_file(filepath, replacements):
    """Remplace des patterns dans un fichier"""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        original_content = content
        for old, new in replacements.items():
            content = content.replace(old, new)

        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        return False
    except Exception as e:
        print_error(f"Erreur avec {filepath}: {e}")
        return False

def main():
    print_section("CORRECTION AWS → AZURE - PROJET P10")

    base_dir = Path("/home/ser/Bureau/P10_reco_new")
    livrables_dir = base_dir / "LIVRABLES_PROJET10_Cassez_Guillaume_012026"

    # Dictionnaire de remplacements
    replacements = {
        # AWS → Azure
        "AWS Lambda": "Azure Functions",
        "AWS S3": "Azure Blob Storage",
        "Lambda Function": "Azure Function",
        "lambda/lambda_function.py": "azure_function/RecommendationFunction/__init__.py",
        "lambda/recommendation_engine.py": "azure_function/recommendation_engine.py",
        "lambda/deploy.sh": "azure_function/deploy_azure.sh",
        "Lambda": "Azure Functions",
        "S3": "Azure Blob Storage",
        "AWS": "Azure",

        # URLs et chemins
        "lambda-url": "azurewebsites.net",
        "https://your-lambda-url": "https://func-mycontent-reco-1269.azurewebsites.net/api/recommend",

        # Code et commandes
        "cd lambda": "cd azure_function",
        "./deploy.sh": "./deploy_azure.sh",
        "lambda_handler": "main",

        # Architecture
        "Warm Lambda": "Warm Azure Function",
        "Cold Start Lambda": "Cold Start Azure Function",
        "Lambda Memory": "Azure Function Memory",
        "Package Lambda": "Azure Function Package",

        # Descriptions
        "Handler AWS Lambda": "Handler Azure Functions",
        "Handler Lambda": "Handler Azure",
        "Déploiement Lambda": "Déploiement Azure Functions",
        "Serverless compute": "Serverless compute (Azure Functions)",
        "Lambda auto-scaling": "Azure Functions auto-scaling",
    }

    # 1. SUPPRIMER LE DOSSIER LAMBDA DES LIVRABLES
    print_section("1. SUPPRESSION DOSSIER LAMBDA/ DES LIVRABLES")

    lambda_livrable1 = livrables_dir / "1_Cassez_Guillaume_1_application_122024" / "lambda"
    if lambda_livrable1.exists():
        shutil.rmtree(lambda_livrable1)
        print_success(f"Supprimé: {lambda_livrable1}")
    else:
        print_warning(f"Déjà supprimé: {lambda_livrable1}")

    # 2. COPIER AZURE_FUNCTION DANS LIVRABLE 1
    print_section("2. COPIE AZURE_FUNCTION DANS LIVRABLE 1")

    azure_source = base_dir / "azure_function"
    azure_dest = livrables_dir / "1_Cassez_Guillaume_1_application_122024" / "azure_function"

    if azure_dest.exists():
        shutil.rmtree(azure_dest)

    shutil.copytree(azure_source, azure_dest,
                    ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '.python_packages', 'models'))
    print_success(f"Copié azure_function → {azure_dest}")

    # 3. REMPLACER DANS TOUS LES FICHIERS DES LIVRABLES
    print_section("3. REMPLACEMENT AWS → AZURE DANS LES FICHIERS")

    files_to_process = []
    for ext in ['*.md', '*.txt', '*.py']:
        files_to_process.extend(livrables_dir.rglob(ext))

    files_modified = 0
    for filepath in files_to_process:
        if replace_in_file(filepath, replacements):
            files_modified += 1
            print_success(f"Modifié: {filepath.name}")

    print(f"\n{BLUE}Total fichiers modifiés: {files_modified}{NC}")

    # 4. MISE À JOUR DU README LIVRABLE 1
    print_section("4. MISE À JOUR README LIVRABLE 1")

    readme_livrable1 = livrables_dir / "1_Cassez_Guillaume_1_application_122024" / "README.md"
    if readme_livrable1.exists():
        with open(readme_livrable1, 'r', encoding='utf-8') as f:
            content = f.read()

        # Remplacement de la section Lambda par Azure
        new_content = content

        # Remplacer la structure
        structure_old = """├── lambda/                          # AWS Lambda Function"""
        structure_new = """├── azure_function/                 # Azure Functions"""
        new_content = new_content.replace(structure_old, structure_new)

        # Ajouter informations Azure
        if "func-mycontent-reco-1269" not in new_content:
            azure_info = """
## 🌐 API Azure Déployée

**Endpoint:** https://func-mycontent-reco-1269.azurewebsites.net/api/recommend

**Resource Group:** rg-mycontent-prod
**Region:** France Central
**Plan:** Consumption Plan

### Test de l'API
```bash
curl -X POST https://func-mycontent-reco-1269.azurewebsites.net/api/recommend \\
  -H 'Content-Type: application/json' \\
  -d '{"user_id": 58, "n": 5}'
```
"""
            # Insérer après le titre
            new_content = new_content.replace(
                "# My Content - Système de Recommandation d'Articles\n",
                f"# My Content - Système de Recommandation d'Articles\n{azure_info}\n"
            )

        with open(readme_livrable1, 'w', encoding='utf-8') as f:
            f.write(new_content)

        print_success("README Livrable 1 mis à jour")

    # 5. MISE À JOUR LIEN GITHUB (LIVRABLE 2)
    print_section("5. MISE À JOUR INSTRUCTIONS GITHUB (LIVRABLE 2)")

    github_instructions = livrables_dir / "2_Cassez_Guillaume_2_scripts_122024" / "LIEN_GITHUB_ET_INSTRUCTIONS.txt"
    if github_instructions.exists():
        with open(github_instructions, 'r', encoding='utf-8') as f:
            content = f.read()

        # Appliquer les remplacements
        for old, new in replacements.items():
            content = content.replace(old, new)

        with open(github_instructions, 'w', encoding='utf-8') as f:
            f.write(content)

        print_success("Instructions GitHub mises à jour")

    # 6. RAPPORT FINAL
    print_section("RAPPORT FINAL")

    print_success("✅ Dossier lambda/ supprimé des livrables")
    print_success("✅ Dossier azure_function/ copié dans livrable 1")
    print_success(f"✅ {files_modified} fichiers modifiés (AWS → Azure)")
    print_success("✅ README et instructions mis à jour")

    print(f"\n{YELLOW}{'─'*70}{NC}")
    print(f"{YELLOW}⚠️  PROCHAINES ÉTAPES :{NC}")
    print(f"{YELLOW}1. Mettre à jour le PowerPoint{NC}")
    print(f"{YELLOW}2. Regénérer le PowerPoint avec les corrections{NC}")
    print(f"{YELLOW}3. Tester l'application Streamlit avec Azure{NC}")
    print(f"{YELLOW}4. Faire le test de charge{NC}")
    print(f"{YELLOW}{'─'*70}{NC}\n")

if __name__ == "__main__":
    main()
