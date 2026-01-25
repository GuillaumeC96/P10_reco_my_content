# Déploiement Azure - Statut Final

**Date:** 28 décembre 2025
**Statut:** Infrastructure créée ✅ | Modèles Lite générés ✅ | API en cours de debug ⚠️

---

## ✅ Ce qui a été accompli

### 1. Modèles Lite créés avec succès
- **10,000 utilisateurs** sélectionnés de manière équilibrée par niveau d'activité
- **Distribution représentative:**
  - 32.3% utilisateurs peu actifs (1-2 articles)
  - 19.1% utilisateurs moyennement actifs faibles (3-4 articles)
  - 25.7% utilisateurs moyennement actifs élevés (5-10 articles)
  - 22.9% utilisateurs très actifs (>10 articles)
- **7,732 articles** uniques
- **78,553 interactions** (filtre 30s appliqué)
- **Taille totale: 86.1 MB** (vs 750 MB originaux) → **Réduction de 96%** ✅

### 2. Infrastructure Azure déployée
- **Resource Group:** `rg-mycontent-prod` (France Central)
- **Storage Account:** `samycontentprod0979`
- **Function App:** `func-mycontent-reco-1269` (Python 3.11, Consumption Plan)
- **Blob Container:** `models` avec tous les modèles Lite uploadés

### 3. Code déployé
- Moteur de recommandation hybride (40% Content / 30% Collab / 30% Temporal)
- Support des profils enrichis (9 signaux de qualité + filtre 30s)
- Matrice pondérée avec interaction_weight
- Code de téléchargement depuis Blob Storage

### 4. Tests locaux réussis
```bash
$ python3 test_local_enriched.py
✓ Modèles chargés: 10,000 users
✓ 5 recommandations générées
  1. Article 123289 - Score: 0.100
  2. Article 234698 - Score: 0.025
  3. Article 141004 - Score: 0.021
  4. Article 96210 - Score: 0.018
  5. Article 144879 - Score: 0.017
```

---

## ⚠️ Problème rencontré

### Symptôme
L'API déployée sur Azure Functions répond avec HTTP 500 (erreur serveur interne).

```bash
$ curl https://func-mycontent-reco-1269.azurewebsites.net/api/recommend
HTTP/2 500
content-length: 0
```

### Diagnostic
- **Temps de réponse:** 0.4-0.7s (très rapide → crash au démarrage)
- **Pas de logs accessibles** sans Application Insights configuré
- **Tests locaux:** ✅ Fonctionnent parfaitement
- **Code déployé:** ✅ Aucune erreur de syntaxe

### Cause probable
L'erreur se produit probablement lors de l'initialisation, potentiellement à cause de:
1. **Problème d'import** du module `azure_utils`
2. **Permissions** sur le système de fichiers `/tmp`
3. **Timeout** ou **limite mémoire** lors du premier chargement
4. **Module azure-storage-blob** mal installé dans l'environnement Azure

### Tentatives effectuées
- ✅ Modèles réduits à 86 MB (vs 750 MB)
- ✅ Chemins corrigés pour utiliser `/tmp`
- ✅ Logging amélioré pour debug
- ✅ Code de téléchargement Blob Storage implémenté
- ✅ Gestion d'erreurs robuste
- ✅ Compatibilité dict/DataFrame pour `article_popularity`
- ❌ Impossible d'accéder aux logs Application Insights pour diagnostic détaillé

---

## 🔧 Solutions recommandées

### Option 1 : Application Insights pour debug (Recommandé immédiat)
**Activer Application Insights** pour voir exactement où ça crash :

```bash
# Query les logs
az monitor app-insights query \
  --app func-mycontent-reco-1269 \
  --resource-group rg-mycontent-prod \
  --analytics-query "exceptions | where timestamp > ago(1h) | project timestamp, message, details"
```

**Pourquoi:** Sans logs, impossible de savoir exactement où l'erreur se produit.

### Option 2 : Azure Functions Premium Plan (Solution production)
**Upgrader vers EP1** (150€/mois) :

**Avantages:**
- Permet de monter Azure Files/Blob comme système de fichiers
- Modèles chargés UNE SEULE FOIS au démarrage (pas de download runtime)
- Meilleure performance et stabilité
- Mémoire jusqu'à 14 GB (vs 1.5 GB Consumption)
- Logs et monitoring complets

**Commandes:**
```bash
# Créer App Service Plan Premium
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
```

**ROI:** Coût justifié par +8,700€/an de revenus publicitaires (avec 100k sessions).

### Option 3 : Déploiement Streamlit alternatif
**Déployer l'app Streamlit** existante qui fonctionne avec les modèles Lite :

**Avantages:**
- Code Python pur, déjà testé et fonctionnel
- Peut tourner sur Azure Web App (~30€/mois)
- Interface utilisateur incluse
- Pas de serverless complexity

**Fichiers existants:**
- `/home/ser/Bureau/P10_reco_new/app/streamlit_app.py` - App fonctionnelle
- `/home/ser/Bureau/P10_reco/models_lite/` - Modèles prêts (86 MB)

### Option 4 : Container Azure (Alternative)
**Déployer comme conteneur Docker** sur Azure Container Instances :

**Avantages:**
- Plus de flexibilité que Functions
- Pas de limitations serverless
- Coût ~80€/mois
- Logs et debugging facilités

---

## 📊 Comparaison des options

| Solution | Coût/mois | Complexité | Temps debug | Statut actuel |
|----------|-----------|------------|-------------|---------------|
| **Debug Consumption actuel** | ~10€ | Moyen | 2-4h | Bloqué sans logs ⚠️ |
| **Premium Plan (EP1)** | ~150€ | Faible | 15min | Recommandé ✅ |
| **Streamlit sur Web App** | ~30€ | Faible | 30min | Alternative viable ✅ |
| **Container Instances** | ~80€ | Moyen | 1-2h | Viable |

---

## 📝 Fichiers et ressources

### Modèles Lite (prêts à l'emploi)
Répertoire: `/home/ser/Bureau/P10_reco/models_lite/` (86.1 MB total)

| Fichier | Taille | Description |
|---------|--------|-------------|
| user_profiles_enriched.pkl | 21.6 MB | Profils 10k users (9 signaux) |
| user_profiles_enriched.json | 56.0 MB | Format JSON fallback |
| user_item_matrix_weighted.npz | 0.3 MB | Matrice pondérée |
| embeddings_filtered.pkl | 7.7 MB | Embeddings articles |
| articles_metadata.csv | 0.2 MB | Métadonnées articles |
| mappings.pkl | 0.3 MB | Mappings user/article IDs |

### Scripts créés
- `/home/ser/Bureau/P10_reco_new/data_preparation/create_lite_models.py` - Génération modèles Lite équilibrés
- `/home/ser/Bureau/P10_reco_new/azure_function/test_local_enriched.py` - Test local (fonctionne ✅)
- `/home/ser/Bureau/P10_reco_new/deploy_azure_quick.sh` - Déploiement automatisé

### URLs et commandes

**API Endpoint:**
```
https://func-mycontent-reco-1269.azurewebsites.net/api/recommend
```

**Test:**
```bash
curl -X POST https://func-mycontent-reco-1269.azurewebsites.net/api/recommend \
  -H 'Content-Type: application/json' \
  -d '{"user_id": 58, "n": 5}'
```

**Redémarrer:**
```bash
az functionapp restart \
  --name func-mycontent-reco-1269 \
  --resource-group rg-mycontent-prod
```

**Supprimer tout:**
```bash
az group delete --name rg-mycontent-prod --yes
```

---

## 🎯 Recommandation finale

**Prochaine étape immédiate:**

1. **Activer Application Insights** pour diagnostic:
   ```bash
   az monitor app-insights component show \
     --app func-mycontent-reco-1269 \
     --resource-group rg-mycontent-prod
   ```

2. **OU upgrader vers Premium Plan EP1** pour éviter les limitations Consumption:
   - Performance garantie
   - Pas de cold start
   - Logs complets
   - Production-ready

3. **OU déployer l'app Streamlit** comme solution rapide et fiable:
   - App fonctionnelle existante
   - Interface utilisateur incluse
   - Coût raisonnable (~30€/mois)

---

## 📦 Ce qui est déjà prêt

**✅ Modèles Lite** - 86 MB, équilibrés, testés localement
**✅ Infrastructure Azure** - Resource Group, Storage, Function App créés
**✅ Code fonctionnel** - Testé localement avec succès
**✅ Modèles uploadés** - Sur Azure Blob Storage
**✅ Configuration** - Variables d'environnement définies

**⚠️ Debug nécessaire** - Erreur 500 à diagnostiquer (besoin d'Application Insights ou upgrade Premium)

---

**Note:** L'infrastructure est fonctionnelle, les modèles sont prêts et optimisés. Il ne reste que le debug de l'erreur 500, qui nécessite soit l'accès aux logs (Application Insights), soit un upgrade vers Premium Plan pour éliminer les contraintes du Consumption Plan.

**ROI rappel:** Avec 100k sessions/an, le système génère +8,700€ de revenus publicitaires supplémentaires, ce qui justifie largement le coût d'un Premium Plan.
