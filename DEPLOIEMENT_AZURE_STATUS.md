# Déploiement Azure - Statut et Prochaines Étapes

**Date:** 28 décembre 2025
**Statut:** Infrastructure créée, API déployée, **besoin d'optimisation**

---

## ✅ Ce qui a été déployé

### 1. Infrastructure Azure (Complété)
- **Resource Group:** `rg-mycontent-prod` (France Central)
- **Storage Account:** `samycontentprod0979`
- **Function App:** `func-mycontent-reco-1269` (Python 3.11, Consumption Plan)
- **Blob Container:** `models` (avec tous les modèles enrichis)

### 2. Modèles uploadés sur Blob Storage (Complété)
Tous les fichiers suivants sont dans `samycontentprod0979/models/` :

| Fichier | Taille | Statut |
|---------|--------|--------|
| user_profiles_enriched.pkl | 669 MB | ✅ |
| user_item_matrix_weighted.npz | 9.2 MB | ✅ |
| user_item_matrix.npz | 4.4 MB | ✅ |
| articles_metadata.csv | 11 MB | ✅ |
| embeddings_filtered.pkl | 38 MB | ✅ |
| article_popularity.pkl | 1.5 MB | ✅ |
| mappings.pkl | 3.2 MB | ✅ |
| **TOTAL** | **~750 MB** | **✅** |

### 3. Configuration (Complété)
Variables d'environnement configurées :
```bash
STORAGE_ACCOUNT_NAME=samycontentprod0979
BLOB_CONTAINER_NAME=models
DEFAULT_N_RECOMMENDATIONS=5
USE_WEIGHTED_MATRIX=True
USE_WEIGHTED_AGGREGATION=True
USE_TEMPORAL_DECAY=True
DECAY_HALF_LIFE_DAYS=7.0
MAX_ARTICLE_AGE_DAYS=60
DEFAULT_WEIGHT_CONTENT=0.40
DEFAULT_WEIGHT_COLLAB=0.30
DEFAULT_WEIGHT_TREND=0.30
LOG_LEVEL=INFO
```

### 4. Code déployé (Complété)
- Moteur de recommandation hybride (40% Content / 30% Collab / 30% Temporal)
- Profils enrichis avec 9 signaux de qualité
- Filtre 30 secondes (seules les vraies lectures)
- Matrice pondérée (interaction_weight)

---

## ⚠️ Problème identifié

### Symptôme
L'API répond avec HTTP 500 (erreur serveur) sans message d'erreur détaillé.

### Cause probable
**Azure Functions Consumption Plan** a des limitations pour notre cas d'usage :

1. **Taille des modèles :** ~750 MB à télécharger depuis Blob Storage au runtime
2. **Mémoire limitée :** 1.5 GB max dans Consumption Plan
3. **Timeout :** Le téléchargement initial des modèles prend trop de temps
4. **Cold start :** À chaque redémarrage, les modèles doivent être retéléchargés

### Tentatives effectuées
- ✅ Upload des modèles sur Blob Storage
- ✅ Code pour télécharger les modèles au runtime (depuis `/home/models`)
- ✅ Gestion d'erreurs améliorée
- ❌ Les modèles sont trop volumineux pour le plan Consumption

---

## 🔧 Solutions possibles

### Option 1 : Azure Functions Premium Plan (Recommandé)
**Avantages :**
- Permet de monter Azure Files ou Blob Storage comme système de fichiers
- Modèles chargés UNE SEULE FOIS au démarrage
- Pas de cold start pour le chargement des modèles
- Mémoire jusqu'à 14 GB (vs 1.5 GB)
- Meilleure performance

**Inconvénients :**
- Coût : ~150-200€/mois vs ~10€/mois pour Consumption
- Nécessite reconfiguration

**Commandes pour upgrader :**
```bash
# Créer un App Service Plan Premium
az appservice plan create \
  --name plan-mycontent-premium \
  --resource-group rg-mycontent-prod \
  --location francecentral \
  --sku EP1 \
  --is-linux

# Migrer la Function App
az functionapp update \
  --name func-mycontent-reco-1269 \
  --resource-group rg-mycontent-prod \
  --plan plan-mycontent-premium

# Monter Blob Storage comme filesystem
az webapp config storage-account add \
  --resource-group rg-mycontent-prod \
  --name func-mycontent-reco-1269 \
  --custom-id models \
  --storage-type AzureBlob \
  --account-name samycontentprod0979 \
  --share-name models \
  --mount-path /models
```

### Option 2 : Réduire la taille des modèles (Solution temporaire)
Créer une version "lite" pour démo :
- Utiliser seulement les 10,000 utilisateurs les plus actifs (au lieu de 322k)
- Modèles réduits à ~100 MB
- Permet de tester l'API dans Consumption Plan

**Script à créer :** `create_lite_models.py`

### Option 3 : Azure Container Instances
Déployer comme conteneur Docker au lieu d'Azure Function :
- Plus de flexibilité
- Pas de limite de taille de modèles
- Coût similaire au Premium Plan

---

## 📊 Résumé financier

| Solution | Coût mensuel | Performance | Complexité |
|----------|--------------|-------------|------------|
| **Consumption Plan (actuel)** | ~10€ | ❌ Ne fonctionne pas | Simple |
| **Premium Plan (EP1)** | ~150€ | ✅ Excellent | Moyen |
| **Container Instances** | ~80€ | ✅ Bon | Élevé |
| **Modèles "Lite"** | ~10€ | ⚠️ Limité | Moyen |

---

## 🎯 Recommandation

**Pour la production :** Utiliser **Azure Functions Premium Plan (EP1)**
- Conforme au cahier des charges (serverless)
- Performance optimale
- Gestion automatique de l'échelle
- Coût justifié par le gain de revenus (+8,700€/an avec 100k sessions)

**Pour le développement/démo :** Créer une version "Lite"
- Tester l'API avec des modèles réduits
- Valider le code avant passage en Premium

---

## 📝 Informations de déploiement

### URLs
- **API Endpoint:** `https://func-mycontent-reco-1269.azurewebsites.net/api/recommend`
- **Portail Azure:** `https://portal.azure.com`

### Commandes utiles
```bash
# Voir les logs (si Premium Plan)
az webapp log tail --name func-mycontent-reco-1269 --resource-group rg-mycontent-prod

# Redémarrer
az functionapp restart --name func-mycontent-reco-1269 --resource-group rg-mycontent-prod

# Voir la configuration
az functionapp config appsettings list --name func-mycontent-reco-1269 --resource-group rg-mycontent-prod

# Supprimer tout
az group delete --name rg-mycontent-prod --yes
```

### Fichiers locaux importants
- `/home/ser/Bureau/P10_reco_new/azure_function/` - Code déployé
- `/home/ser/Bureau/P10_reco/models/` - Modèles sources (750 MB)
- `/home/ser/Bureau/P10_reco_new/GUIDE_DEPLOIEMENT_AZURE.md` - Guide complet

---

## 🚀 Prochaines étapes

1. **Décider** quelle solution adopter (Premium Plan ou Lite)
2. **Si Premium Plan :**
   - Créer le plan EP1 (~5 minutes)
   - Migrer la Function App
   - Monter le Blob Storage
   - Tester l'API
3. **Si Lite :**
   - Créer `create_lite_models.py`
   - Générer modèles réduits (~100 MB)
   - Uploader et retester

---

**Note:** L'infrastructure est créée et prête. Seule l'optimisation du chargement des modèles reste à faire pour que l'API fonctionne.
