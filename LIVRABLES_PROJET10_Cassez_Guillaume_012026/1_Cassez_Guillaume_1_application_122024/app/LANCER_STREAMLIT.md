# Guide de lancement - Application Streamlit

## Application Streamlit pour l'API Azure

Une interface graphique simple et élégante pour interagir avec l'API de recommandation déployée sur Azure Functions.

---

## 🚀 Lancement rapide

### Étape 1: Installer les dépendances

```bash
cd /home/ser/Bureau/P10_reco_new/app
pip install streamlit requests pandas
```

### Étape 2: Lancer l'application

```bash
streamlit run streamlit_api.py
```

**L'application s'ouvrira automatiquement dans votre navigateur à:** `http://localhost:8501`

---

## 📋 Utilisation

### Interface

**Panneau latéral gauche:**
- 👤 **ID utilisateur** - Entrez l'ID de l'utilisateur (essayez 58 pour commencer)
- 📊 **Nombre de recommandations** - De 1 à 20 articles
- 🎛️ **Stratégies prédéfinies:**
  - Optimale (39% content / 36% collab / 25% trend - Optuna)
  - Personnalisée (60% collab)
  - Trending (60% temporal)
  - Similaires (70% content)
- 🔧 **Mode avancé** - Ajustez les poids manuellement
- ✨ **Diversité** - Active la diversification MMR

**Zone principale:**
- 🚀 **Bouton Générer** - Lance la requête API
- 🎯 **Articles recommandés** - Cartes colorées avec scores
- 📊 **Vue d'ensemble** - Tableau et statistiques
- 📈 **Graphiques** - Visualisations (scores, catégories, temporalité)
- 📥 **Téléchargements** - Export CSV et JSON

### Exemple d'utilisation

1. **Sélectionner l'utilisateur 58** (disponible dans les modèles Lite)
2. **Choisir 5 recommandations**
3. **Sélectionner la stratégie "Équilibrée"**
4. **Cliquer sur "🚀 Générer"**
5. **Observer les résultats** en cartes colorées
6. **Explorer les statistiques** et graphiques
7. **Télécharger les résultats** si souhaité

---

## 🎨 Fonctionnalités

### Visualisations

- **Cartes colorées** - Chaque recommandation dans un gradient différent
- **Scores visuels** - Badge rond avec le score de chaque article
- **Tableau interactif** - Avec gradient de couleur sur les scores
- **Graphiques dynamiques:**
  - Scores par article (bar chart)
  - Distribution par catégorie
  - Évolution temporelle

### Métriques en temps réel

- ✅ Nombre de recommandations générées
- ⚡ Latence de l'API (en ms)
- 🎯 Score maximum
- ☁️ Platform (Azure)

### Exports

- **CSV** - Tableau formaté avec toutes les colonnes
- **JSON** - Réponse complète de l'API

---

## 🔧 Configuration avancée

### Modifier l'endpoint API

Par défaut, l'application utilise:
```python
API_URL = "https://func-mycontent-reco-1269.azurewebsites.net/api/recommend"
```

Pour changer l'endpoint, modifiez la ligne 48 dans `streamlit_api.py`.

### Ajouter des stratégies personnalisées

Modifiez la section "Stratégies prédéfinies" (lignes 127-141):

```python
if strategy == "Ma Stratégie":
    weight_content, weight_collab, weight_trend = 0.5, 0.3, 0.2
    st.sidebar.caption("📌 Description de ma stratégie")
```

---

## 🐛 Résolution de problèmes

### Erreur: "Module not found: streamlit"

```bash
pip install streamlit
```

### Erreur: "Connection refused" ou "Timeout"

- Vérifiez que l'API Azure est accessible
- Testez avec curl:
  ```bash
  curl -X POST https://func-mycontent-reco-1269.azurewebsites.net/api/recommend \
    -H 'Content-Type: application/json' \
    -d '{"user_id": 58, "n": 5}'
  ```

### Aucune recommandation pour un utilisateur

- Les modèles Lite contiennent seulement 10,000 utilisateurs
- **Utilisateur 58 garanti disponible**
- Essayez avec d'autres IDs: 100, 500, 1000, 5000, 10000
- Si aucun ne fonctionne, vérifiez l'API

### L'application ne se lance pas

```bash
# Vérifier la version de Streamlit
streamlit --version

# Réinstaller si nécessaire
pip install --upgrade streamlit
```

---

## 📸 Captures d'écran (description)

**Interface principale:**
- En-tête bleu avec titre "My Content - Recommandations Personnalisées"
- Panneau latéral avec tous les paramètres
- Zone centrale avec bouton "Générer" et métriques
- Cartes colorées pour chaque recommandation
- Tableau avec gradient de couleurs
- Graphiques interactifs en onglets

**Exemples de cartes:**
- Gradient violet pour la 1ère recommandation
- Gradient rose pour la 2ème
- Gradient bleu pour la 3ème
- Badge doré rond avec le score

---

## 🎯 Cas d'usage

### 1. Démonstration pour la soutenance

**Scénario:**
1. Ouvrir l'application pendant la présentation
2. Montrer l'interface intuitive
3. Générer des recommandations en direct
4. Changer les stratégies pour montrer l'impact
5. Afficher les graphiques et métriques

**Temps:** 2-3 minutes

### 2. Tests de différentes stratégies

**Objectif:** Comparer l'impact des poids

**Procédure:**
1. User 58, 10 recommandations
2. Tester "Équilibrée" - Noter les résultats
3. Tester "Personnalisée" - Comparer
4. Tester "Trending" - Analyser les dates
5. Tester "Similaires" - Observer les catégories

### 3. Validation avec plusieurs utilisateurs

**Objectif:** Tester la couverture des modèles

**Procédure:**
1. Créer une liste d'IDs à tester
2. Pour chaque ID, générer 5 recommandations
3. Noter lesquels retournent des résultats
4. Documenter les patterns

---

## 📊 Métriques affichées

### Métriques principales

| Métrique | Description | Exemple |
|----------|-------------|---------|
| **Recommandations** | Nombre d'articles générés | 5 |
| **Latence** | Temps de réponse API | 650 ms |
| **Score max** | Score du meilleur article | 0.300 |
| **Platform** | Origine de la réponse | Azure |

### Statistiques détaillées

| Statistique | Description |
|-------------|-------------|
| **Articles** | Nombre total de recommandations |
| **Catégories** | Nombre de catégories uniques |
| **Mots moyen** | Longueur moyenne des articles |
| **Score moyen** | Score moyen des recommandations |
| **Âge moyen** | Âge moyen en jours |

---

## 🎨 Personnalisation

### Changer les couleurs

Modifier la section CSS (lignes 14-55):

```css
.main-header {
    color: #0078D4;  /* Changer cette couleur */
}
```

### Ajouter des graphiques

Utiliser Streamlit charts:

```python
import matplotlib.pyplot as plt
import plotly.express as px

# Exemple avec Plotly
fig = px.scatter(df, x='created_at', y='score', size='words_count')
st.plotly_chart(fig)
```

---

## 💡 Conseils

### Performance

- **Première requête lente ?** C'est le cold start d'Azure Functions (~700ms)
- **Requêtes suivantes rapides** - Les modèles sont en cache (~650ms)
- **Activer le mode compact** - `?embed=true` dans l'URL

### Expérience utilisateur

- **Commencer avec user 58** - Garanti de fonctionner
- **5 recommandations** - Bon équilibre affichage/pertinence
- **Stratégie équilibrée** - Valeurs par défaut optimisées
- **Diversité activée** - Meilleure variété

### Démonstration

- **Préparer plusieurs scénarios** avant la présentation
- **Tester la connexion** quelques minutes avant
- **Avoir un backup** (captures d'écran) si problème réseau
- **Expliquer la latence** (normal pour serverless)

---

## 🔗 Ressources

**Documentation:**
- PROJET_COMPLET.md - Documentation technique
- DEMO_SCRIPT.md - Scripts de test
- RAPPORT_TESTS_API.md - Résultats des tests

**API:**
- Endpoint: https://func-mycontent-reco-1269.azurewebsites.net/api/recommend
- Resource Group: rg-mycontent-prod
- Region: France Central

**Streamlit:**
- Documentation: https://docs.streamlit.io/
- Gallery: https://streamlit.io/gallery
- Cheat Sheet: https://docs.streamlit.io/library/cheatsheet

---

## 📝 Notes

### Version Lite

L'application utilise l'API avec les modèles Lite (86 MB):
- 10,000 utilisateurs
- 7,732 articles
- 78,553 interactions

Tous les utilisateurs ne sont pas disponibles. User 58 est garanti.

### Latence attendue

- **Cold start:** ~700ms
- **Warm:** ~650ms
- **Objectif à terme:** <200ms (avec optimisations)

### Limitations connues

- Couverture utilisateurs limitée (10k users)
- Pas de fallback pour utilisateurs inconnus (retourne liste vide)
- Latence plus élevée qu'espéré (acceptable pour MVP)

---

## 🚀 Prochaines améliorations

### Court terme
- [ ] Ajouter un système de cache côté client
- [ ] Implémenter la recherche d'utilisateurs disponibles
- [ ] Ajouter plus de visualisations (word clouds, etc.)

### Moyen terme
- [ ] Mode comparaison de stratégies côte à côte
- [ ] Historique des requêtes dans la session
- [ ] Export PDF des recommandations

### Long terme
- [ ] Authentification utilisateur
- [ ] Feedback sur les recommandations
- [ ] Tableau de bord analytics

---

**Document créé le:** 29 décembre 2025
**Dernière mise à jour:** 29 décembre 2025

**Besoin d'aide ?** Consultez la documentation complète dans PROJET_COMPLET.md
