#!/usr/bin/env python3
"""
Script pour remplacer les listes à puces par texte en gras + tabulations
"""

import re

def transform_bullets(content):
    """Transforme les listes à puces en format gras + tabulation"""

    lines = content.split('\n')
    result = []

    for line in lines:
        # Détecter les puces simples (- xxx)
        match = re.match(r'^(\s*)- (.+)$', line)
        if match:
            indent = match.group(1)
            text = match.group(2)

            # Essayer de détecter si c'est un format "Label: texte"
            colon_match = re.match(r'^(.+?):\s*(.+)$', text)
            if colon_match:
                label = colon_match.group(1).strip()
                value = colon_match.group(2).strip()
                result.append(f"{indent}**{label}:**\t{value}")
            else:
                # Sinon, mettre juste le texte en gras suivi de tab
                result.append(f"{indent}**{text}**")

        # Détecter les puces numérotées (1. xxx)
        elif re.match(r'^(\s*)\d+\.\s+\*\*(.+?)\*\*(.*)$', line):
            # Format déjà avec gras, on le laisse
            result.append(line)

        # Détecter les sous-puces avec tiret (   - xxx)
        elif re.match(r'^(\s{3,})- (.+)$', line):
            match = re.match(r'^(\s+)- (.+)$', line)
            indent = match.group(1)
            text = match.group(2)
            result.append(f"{indent}**{text}**")

        else:
            result.append(line)

    return '\n'.join(result)

def main():
    file_path = "/home/ser/Bureau/P10_reco_new/LIVRABLES_PROJET10_Cassez_Guillaume_012026/3_Cassez_Guillaume_3_presentation_122024/CONTENU_PRESENTATION.md"

    print(f"Lecture de {file_path}...")
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    print("Transformation des listes à puces...")
    new_content = transform_bullets(content)

    print(f"Écriture du fichier...")
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

    print("✅ Transformation terminée!")

if __name__ == "__main__":
    main()
