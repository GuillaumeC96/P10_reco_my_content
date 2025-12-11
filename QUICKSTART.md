# Guide de Démarrage Rapide - My Content

## 🚀 Démarrage en 3 minutes

### Prérequis

```bash
python3 --version  # Python 3.9+
pip3 --version
```

### 1. Installation des dépendances

```bash
pip install -r requirements.txt
```

### 2. Les modèles sont déjà prêts!

Le preprocessing LITE a déjà été exécuté. Les modèles sont dans `models/`:
- ✅ 59,879 utilisateurs
- ✅ 7,484 articles
- ✅ 326,929 interactions

### 3. Tester localement

```bash
# Test rapide du moteur
python3 test_local.py

# Test de diversité
python3 test_diversity.py
```

### 4. Lancer l'application Streamlit

```bash
cd app
streamlit run streamlit_app.py
```

L'application s'ouvrira sur `http://localhost:8501`

**Configuration:**
- Cocher "Mode local" dans la sidebar
- Entrer un user_id (essayez 5, 8, 18, 22, 24, 50, etc.)
- Cliquer sur "Générer des recommandations"

---

## 📊 Résultats attendus

**Diversité:** 5/5 catégories uniques (testé sur 10 utilisateurs)

**Temps de réponse:**
- Premier appel: ~2-3s (chargement modèles)
- Appels suivants: ~0.5-1s (cache)

**Scores de recommandation:** Entre 0.3 et 1.0

---

## 🔧 Paramètres ajustables

### Dans Streamlit

**user_id:** ID de l'utilisateur (0 à 117,184)

**n_recommendations:** Nombre d'articles (1-20)

**alpha:** Poids collaborative filtering
- 0.0 = 100% Content-based
- 0.6 = 60% Collaborative + 40% Content (défaut)
- 1.0 = 100% Collaborative

**use_diversity:** Activer/désactiver filtre de diversité

---

## 🧪 Tests recommandés

### Test 1: Utilisateur avec historique riche
```python
user_id = 5  # 10+ interactions
```
→ Devrait retourner 5 catégories différentes

### Test 2: Variation de alpha
```python
# Plus de collaborative
alpha = 0.8  # Recommandations basées sur utilisateurs similaires

# Plus de content-based
alpha = 0.3  # Recommandations basées sur similarité de contenu
```

### Test 3: Cold start
```python
user_id = 999999  # Utilisateur inexistant
```
→ Devrait retourner articles populaires

---

## 📈 Statistiques du dataset (version LITE)

```json
{
  "version": "lite",
  "num_users": 59879,
  "num_articles": 7484,
  "num_interactions": 326929,
  "matrix_sparsity": 99.93,
  "sample_size": "50/385 fichiers"
}
```

---

## 🐛 Troubleshooting

### Erreur: Module not found

```bash
pip install -r requirements.txt
cd app && pip install -r requirements.txt
```

### Erreur: Models not loaded

```bash
# Vérifier que les modèles existent
ls -lh models/

# Si vide, relancer le preprocessing
python3 data_preparation/data_preprocessing_lite.py
```

### Streamlit ne se lance pas

```bash
# Installer Streamlit
pip install streamlit

# Vérifier l'installation
streamlit --version
```

---

## 🚀 Prochaines étapes

### Pour déployer sur AWS Lambda

1. **Créer un bucket S3**
```bash
aws s3 mb s3://my-content-reco-bucket
```

2. **Uploader les modèles**
```bash
python3 data_preparation/upload_to_s3.py --bucket my-content-reco-bucket
```

3. **Déployer la Lambda**
```bash
cd lambda
./deploy.sh
```

4. **Tester la Lambda**
```bash
curl "https://your-lambda-url/?user_id=5&n_recommendations=5"
```

5. **Configurer Streamlit pour utiliser Lambda**
- Décocher "Mode local"
- Entrer l'URL de la Lambda

---

## 📚 Documentation complète

- **README.md** - Guide complet
- **cahier_des_charges.md** - Spécifications du projet
- **docs/architecture_technique.md** - Architecture détaillée
- **docs/architecture_cible.md** - Vision scalabilité

---

## ✅ Checklist de validation

- [x] Preprocessing LITE exécuté (68s)
- [x] Modèles générés dans `models/`
- [x] Tests locaux passés
- [x] Diversité validée (5/5 catégories)
- [x] Cold start fonctionnel
- [ ] Application Streamlit testée
- [ ] Lambda déployée (optionnel)
- [ ] Tests end-to-end (optionnel)

---

## 🎯 Objectifs atteints

✅ **Système hybride** (Collaborative + Content-based)
✅ **Gestion cold start** (Popularity-based)
✅ **Diversité maximale** (Round-robin par catégorie)
✅ **Performance** (<1s après warmup)
✅ **CPU uniquement** (Pas de GPU requis)

---

**Version:** 1.0.0 (LITE)
**Dataset:** 50/385 fichiers (~13% du dataset complet)
**Temps total:** ~70 secondes de preprocessing
**Status:** ✅ Opérationnel
