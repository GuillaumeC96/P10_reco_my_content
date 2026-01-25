# Application Streamlit Enhanced - My Content Recommandations

Interface graphique interactive multipage avec profil utilisateur, analyses avancées et graphe de réseau pour tester l'API de recommandation déployée sur Azure Functions.

---

## 🚀 Lancement rapide

### Méthode 1: Script automatique (recommandé)

```bash
cd /home/ser/Bureau/P10_reco_new/app
./lancer_app.sh
```

L'application s'ouvrira automatiquement dans votre navigateur à `http://localhost:8501`

### Méthode 2: Commande directe

```bash
cd /home/ser/Bureau/P10_reco_new/app
streamlit run streamlit_app_enhanced.py
```

---

## ✨ Fonctionnalités

### Navigation multipage

- **🕸️ Graphe de Réseau** (Page par défaut) - Analyse globale des relations entre catégories
- **🎯 Recommandations** - Recommandations personnalisées avec profil utilisateur

### Page 1: Graphe de Réseau Global

**Visualisation interactive:**
- Analyse de 322k+ utilisateurs
- 20 catégories les plus populaires
- Filtrage intelligent (percentile 60)
- Bulles colorées par connectivité (palette Viridis)
- Tailles proportionnelles aux utilisateurs

**Clusters identifiés:**
- Super hubs: Cat 281, 375, 412, 437
- Hubs moyens: Cat 250, 399, 209
- Catégories périphériques: 3-4 connexions

**Debug info détaillée:**
- Statistiques globales (nœuds, arêtes, densité)
- Détail par catégorie (utilisateurs, connexions, voisins)
- Top 10 connexions les plus fortes
- Distribution des poids (min, max, moyenne, médiane)

### Page 2: Recommandations Personnalisées

**Profil utilisateur (basé sur temps de lecture):**
- Articles lus, temps total/moyen
- Catégories lues
- Temps de lecture par catégorie

**Comparaison visuelle:**
- Camembert catégories favorites (temps de lecture)
- Camembert catégories recommandées
- Analyse de cohérence avec score
- Taux de nouveauté (nouvelles catégories)

**Recommandations:**
- 5 articles avec métadonnées complètes
- Score de pertinence pour chaque article
- Badge indiquant catégorie favorite/nouvelle
- Temps de lecture estimé
- Export CSV

**Métriques en temps réel:**
- Latence API (⚡ Excellent < 100ms, Bon < 500ms)
- Nombre de recommandations
- Score moyen
- Catégories uniques

---

## 💡 Utilisation

### Premier test

1. Laissez les paramètres par défaut (User 58, 5 recommandations, Stratégie équilibrée)
2. Cliquez sur **"🚀 Générer"**
3. Observez les résultats en cartes colorées
4. Explorez les onglets de graphiques
5. Téléchargez les résultats si souhaité

### Tester différentes stratégies

**Équilibrée (défaut):**
- 40% Content-Based (similitude)
- 30% Collaborative (utilisateurs)
- 30% Temporal (actualité)

**Personnalisée:**
- 60% Collaborative (recommandations basées sur utilisateurs similaires)

**Trending:**
- 60% Temporal (articles populaires récents)

**Similaires:**
- 70% Content-Based (articles similaires à ceux lus)

### Mode avancé

Cochez **"Mode avancé"** dans la sidebar pour ajuster manuellement les poids avec des sliders.

---

## 📊 Informations API

**Endpoint:** `https://func-mycontent-reco-1269.azurewebsites.net/api/recommend`
**Platform:** Azure Functions Consumption Plan
**Region:** France Central
**Version:** Lite (10k users, 86 MB)

**Latence attendue:**
- Cold start: ~700ms
- Warm: ~650ms

---

## 🐛 Résolution de problèmes

### L'application ne démarre pas

```bash
# Vérifier Streamlit
streamlit --version

# Réinstaller si nécessaire
pip install --upgrade streamlit
```

### Aucune recommandation pour un utilisateur

Les modèles Lite contiennent seulement 10,000 utilisateurs échantillonnés.

**Utilisateurs garantis disponibles:**
- User 58 (recommandé pour tests)

**Autres IDs à essayer:**
- 100, 500, 1000, 5000, 10000

Si aucun ne fonctionne, vérifiez que l'API est accessible avec curl.

### Erreur de connexion API

Testez l'API directement:
```bash
curl -X POST https://func-mycontent-reco-1269.azurewebsites.net/api/recommend \
  -H 'Content-Type: application/json' \
  -d '{"user_id": 58, "n": 5}'
```

---

## 📁 Fichiers

- `streamlit_app_enhanced.py` - **Application principale multipage** (recommandée)
- `streamlit_app.py` - Version simple (recommandations uniquement)
- `streamlit_api.py` - Version API pure
- `lancer_app.sh` - Script de lancement automatique
- `requirements.txt` - Dépendances Python
- `LANCER_STREAMLIT.md` - Documentation détaillée
- `README.md` - Ce fichier

---

## 🎯 Cas d'usage

### Démonstration pour soutenance

1. Ouvrir l'app pendant la présentation
2. Montrer l'interface intuitive
3. Générer des recommandations en direct
4. Changer les stratégies pour montrer l'impact
5. Afficher les graphiques (2-3 minutes)

### Tests de stratégies

1. Sélectionner User 58
2. Générer avec "Équilibrée"
3. Comparer avec "Trending"
4. Observer les différences de dates et scores
5. Analyser les catégories

---

## 🔗 Documentation

- **PROJET_COMPLET.md** - Documentation technique complète
- **PRESENTATION_SOUTENANCE.md** - Slides pour la soutenance
- **DEMO_SCRIPT.md** - Scripts de démonstration API
- **RAPPORT_TESTS_API.md** - Résultats des tests
- **LANCER_STREAMLIT.md** - Guide détaillé Streamlit

---

## 📸 Aperçu

**Interface:**
- Header bleu avec titre
- Sidebar avec paramètres
- Zone centrale avec métriques
- Cartes colorées pour recommandations
- Graphiques interactifs
- Export CSV/JSON

**Couleurs:**
- Cartes en dégradé (violet, rose, bleu, vert, orange)
- Badges dorés pour les scores
- Graphiques avec gradients

---

## 💬 Support

Pour toute question, consultez:
- LANCER_STREAMLIT.md - Guide complet
- PROJET_COMPLET.md - Documentation technique
- DEMO_SCRIPT.md - Scripts et tests

---

**Version:** 1.0
**Date:** 29 décembre 2025
**Statut:** ✅ Prêt pour démonstration
