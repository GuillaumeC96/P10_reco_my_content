# Configuration du Projet P10 - My Content

## Informations du Projet

**Nom du projet:** My Content - Système de Recommandation d'Articles
**Type:** MVP (Minimum Viable Product)
**Date de démarrage:** Décembre 2024
**Status:** En développement

---

## GitHub Configuration

**Username:** guillaumec96
**Email Git:** guillaumecassezwork@gmail.com
**Dépôt GitHub:** https://github.com/GuillaumeC96/P10_reco_my_content
**Branche principale:** main

### Personal Access Token (PAT)
**IMPORTANT SÉCURITÉ:** Le token GitHub est stocké dans `.git/config` (non versionné).

**Configuration du token:**
Le token est déjà configuré localement dans `.git/config`. Pour les futures sessions :
1. Le token est récupéré automatiquement depuis la configuration Git locale
2. Si besoin de reconfigurer : voir le fichier `.git/config` (non versionné)

**Permissions du token:**
- ✅ `repo` (accès complet aux dépôts)
- ✅ `workflow`

**Créer un nouveau token:** https://github.com/settings/tokens
- Sélectionner "Generate new token (classic)"
- Permissions : `repo` + `workflow`
- Copier le token (format: `ghp_...`)
- Utiliser pour git remote: `https://TOKEN@github.com/USERNAME/REPO.git`

---

## AWS Configuration

**Service utilisé:** AWS Lambda + S3
**Région:** À définir (ex: us-east-1)
**Bucket S3:** my-content-reco-bucket (à créer)

### Lambda Function
- **Nom:** MyContent-Recommendation-Function
- **Runtime:** Python 3.9
- **Memory:** 1024 MB
- **Timeout:** 30s

**Note:** Credentials AWS non stockés ici - utiliser `aws configure`

---

## Structure des Livrables

### Livrable 1: Application + Système Serverless ✅
- Application Streamlit: `app/streamlit_app.py`
- Lambda Function: `lambda/lambda_function.py`
- Script de déploiement: `lambda/deploy.sh`

### Livrable 2: Scripts sur GitHub ✅
- Dépôt: https://github.com/GuillaumeC96/P10_reco_my_content
- Commit initial: 754d959

### Livrable 3: Présentation PDF ❌ (EN COURS)
- Format: PowerPoint/PDF
- Pages: 15-25 slides
- Fichier cible: `Cassez_Guillaume_3_presentation_122024.pdf`

---

## Nomenclature des Livrables

Selon les instructions OpenClassrooms:

```
Nom_Prénom_n°_livrable_mmaaaa
```

**Vos livrables:**
1. `Cassez_Guillaume_1_application_122024` (dossier avec app + lambda)
2. `Cassez_Guillaume_2_scripts_122024` (lien GitHub)
3. `Cassez_Guillaume_3_presentation_122024.pdf`

---

## Dataset

**Source:** Globo.com News Portal User Interactions
**Localisation:** `news-portal-user-interactions-by-globocom/`
**Taille totale:** ~1.5 GB (non versionné sur Git)

**Fichiers principaux:**
- `articles_metadata.csv` - Métadonnées des 364 047 articles
- `articles_embeddings.pickle` - Embeddings 250D (347 MB)
- `clicks/*.csv` - 385 fichiers de clics utilisateurs

---

## Modèles Générés

**Localisation:** `models/` (fichiers volumineux non versionnés sur Git)

**Fichiers:**
- `user_item_matrix.npz` - Matrice sparse user-article
- `mappings.pkl` - Mappings indices
- `article_popularity.pkl` - Scores de popularité
- `user_profiles.json` - Profils utilisateurs (63 MB)
- `embeddings_filtered.pkl` - Embeddings filtrés
- `articles_metadata.csv` - Métadonnées filtrées
- `preprocessing_stats.json` - Statistiques (versionné)

---

## Commandes Utiles

### Git
```bash
# Vérifier le status
git status

# Commit et push
git add .
git commit -m "Description des changements"
git push origin main

# Voir l'historique
git log --oneline
```

### AWS Lambda Déploiement
```bash
cd lambda
./deploy.sh
```

### Application Streamlit
```bash
cd app
streamlit run streamlit_app.py
```

### Preprocessing des données
```bash
python3 data_preparation/data_preprocessing.py
python3 data_preparation/upload_to_s3.py --bucket my-content-reco-bucket
```

---

## Contacts & Ressources

**CEO:** Samia (cofondatrice)
**CTO:** Vous (Guillaume Cassez)
**Conseiller technique:** Julien (freelance - architecture serverless)

**Documentation:**
- Cahier des charges: `cahier_des_charges.md`
- Architecture technique: `docs/architecture_technique.md`
- Architecture cible: `docs/architecture_cible.md`
- README principal: `README.md`

---

## Notes pour Futures Sessions

1. **Git est déjà configuré** - les informations d'identification sont dans `.git/config`
2. **Le premier commit est fait** - commit hash: 754d959
3. **Le dépôt GitHub est créé et synchronisé**
4. **Reste à faire:** Présentation PowerPoint/PDF (Livrable 3)

---

**Dernière mise à jour:** 11 décembre 2024
**Fichier géré par:** Claude Code
