# Rapport d'Avancement - Projet My Content
## Système de Recommandation d'Articles

**Date:** 11 décembre 2024
**Développeur:** Guillaume Cassez
**Projet:** P10 - OpenClassrooms
**Statut:** MVP opérationnel (2/3 livrables complétés)

---

## 📋 Contexte du Projet

### Objectif Business
My Content est un projet de start-up visant à **encourager la lecture** en recommandant des contenus pertinents et personnalisés aux utilisateurs. L'objectif du MVP était de valider la faisabilité technique d'un système de recommandation avant un déploiement à grande échelle.

### Besoin Fonctionnel Principal
> "En tant qu'utilisateur de l'application, je vais recevoir une sélection de **5 articles personnalisés**"

### Contraintes Identifiées
1. **Cold Start:** Gérer les nouveaux utilisateurs sans historique
2. **Scalabilité:** Architecture capable de gérer l'ajout continu de nouveaux utilisateurs et articles
3. **Performance:** Recommandations en temps raisonnable (< 5 secondes)
4. **Coût:** Solution économique pour un MVP

---

## ✅ Ce Qui a Été Réalisé

### 1. Système de Recommandation Hybride

**Approche retenue:** Combinaison de deux techniques de Machine Learning

#### A. Filtrage Collaboratif (User-Based)
- **Principe:** Recommande des articles appréciés par des utilisateurs similaires
- **Implémentation:** Calcul de similarité cosinus entre utilisateurs via leurs interactions
- **Avantages:** Découvre des contenus inattendus (serendipity), capture les tendances collectives
- **Limites:** Problème de Cold Start pour nouveaux utilisateurs, sensible à la sparsité des données

#### B. Filtrage Basé sur le Contenu (Content-Based)
- **Principe:** Recommande des articles similaires à ceux déjà lus par l'utilisateur
- **Implémentation:** Utilise les embeddings (vecteurs de 250 dimensions) pré-calculés des articles
- **Avantages:** Fonctionne immédiatement pour nouveaux articles, pas de Cold Start utilisateur
- **Limites:** Risque de "filter bubble" (manque de diversité)

#### C. Approche Hybride (Solution Finale)
```
Score_final = α × Score_collaborative + (1-α) × Score_content
```
- **Paramètre alpha = 0.6** (60% collaborative, 40% content-based)
- **Justification:** Combine les forces des deux approches, atténue leurs faiblesses respectives
- **Résultat:** Meilleures recommandations tout en gérant le Cold Start

#### D. Composants Additionnels
- **Filtre de diversité:** Garantit une variété de catégories dans les recommandations
- **Gestion Cold Start:** Fallback sur recommandations par popularité pour nouveaux utilisateurs
- **Exclusion des articles lus:** Évite de recommander des articles déjà consultés

---

### 2. Architecture Serverless Opérationnelle

**Choix technique:** AWS Lambda + S3

#### Pourquoi Serverless ?
1. **Coût minimal:** Pas de serveur à payer 24/7, facturation à l'usage
2. **Auto-scaling:** Gère automatiquement la montée en charge (0 → N instances)
3. **Maintenance zéro:** Pas de gestion d'infrastructure
4. **Time-to-market:** Déploiement rapide pour valider le MVP
5. **Free tier:** 1 million de requêtes gratuites/mois

#### Architecture Implémentée
```
[Utilisateur]
    ↓
[Application Streamlit] ← Interface web locale
    ↓ (HTTPS)
[AWS Lambda Function] ← Compute serverless (Python 3.9, 1024 MB)
    ↓ (Download models)
[AWS S3 Bucket] ← Stockage cloud (~350 MB de modèles)
```

**Temps de réponse:**
- Cold Start: 3-5 secondes (première invocation)
- Warm: 1-2 secondes (invocations suivantes)

---

### 3. Application Utilisateur (Streamlit)

**Technologie:** Streamlit (framework Python pour interfaces web rapides)

**Fonctionnalités développées:**
- Sélection d'un utilisateur parmi la base
- Configuration des paramètres de recommandation (nombre, poids collaborative/content, diversité)
- Affichage des résultats avec métadonnées complètes (catégorie, publisher, nombre de mots)
- Export CSV des recommandations
- **Deux modes:** Local (calcul sur la machine) ou Distant (appel API Lambda)

**Justification du choix Streamlit:**
- Développement rapide (MVP en quelques heures)
- Parfait pour démonstration et prototypage
- Facile à déployer

---

### 4. Pipeline de Données et Déploiement

#### Preprocessing des Données
**Dataset utilisé:** Globo.com News Portal User Interactions
- 364 047 articles avec métadonnées
- ~845 000 interactions utilisateurs (clics)
- Embeddings pré-calculés de 250 dimensions

**Scripts développés:**
- `data_preprocessing.py`: Génère les matrices user-item, calcule les popularités, filtre les embeddings
- `upload_to_s3.py`: Upload automatisé des modèles vers S3
- **Résultat:** 6 fichiers optimisés (~350 MB) prêts pour la production

#### Déploiement Automatisé
- **Script `deploy.sh`:** Automatise 100% du déploiement Lambda
  - Création du rôle IAM avec permissions S3
  - Package des dépendances Python (NumPy, Scikit-learn, Pandas)
  - Création/mise à jour de la Lambda Function
  - Configuration de la Function URL (API HTTP publique)
- **Versioning Git:** Tout le code est versionné sur GitHub
- **Documentation:** README complet avec instructions de déploiement

---

## 🎯 Justifications des Choix Techniques

### Pourquoi l'Approche Hybride ?

**Comparaison des approches testées:**

| Critère | Collaborative | Content-Based | **Hybride** |
|---------|--------------|---------------|-------------|
| Nouveaux utilisateurs | ❌ Faible | ✅ Bon | ✅ **Bon** |
| Nouveaux articles | ⚠️ Moyen | ✅ Excellent | ✅ **Excellent** |
| Diversité | ✅ Bonne | ❌ Faible | ✅ **Bonne** |
| Serendipity | ✅ Excellente | ❌ Faible | ✅ **Bonne** |
| Performance globale | ⚠️ Moyenne | ⚠️ Moyenne | ✅ **Meilleure** |

**Conclusion:** L'hybride offre le meilleur compromis pour un MVP évolutif.

### Pourquoi AWS Lambda plutôt qu'un Serveur Traditionnel ?

**Comparaison:**

| Aspect | Serveur (EC2/VM) | **Lambda (Serverless)** |
|--------|------------------|-------------------------|
| Coût fixe | Oui (~$10-50/mois) | ✅ **Non (à l'usage)** |
| Maintenance | Forte | ✅ **Nulle** |
| Scalabilité | Manuelle | ✅ **Automatique** |
| Disponibilité | À gérer | ✅ **Native** |
| Adapté MVP | Moyen | ✅ **Excellent** |

**Conclusion:** Lambda est optimal pour un MVP avec charge variable et budget limité.

### Pourquoi Streamlit plutôt que React/Vue.js ?

**Pour un MVP:**
- Streamlit: **2-3 heures** de développement
- React: **2-3 jours** de développement

**Objectif MVP:** Valider le concept rapidement avant d'investir dans une interface production.

---

## 📦 État des Livrables

### ✅ Livrable 1: Application Fonctionnelle (COMPLET)
**Contenu:**
- Application Streamlit opérationnelle
- Lambda Function déployable
- Scripts de déploiement automatisés
- Moteur de recommandation hybride

**Démonstration:** Peut générer des recommandations en quelques clics

---

### ✅ Livrable 2: Code sur GitHub (COMPLET)
**Dépôt:** https://github.com/GuillaumeC96/P10_reco_my_content

**Contenu versionné:**
- 32 fichiers de code et documentation
- Scripts de déploiement end-to-end
- Documentation complète (README, architecture technique, architecture cible)
- Tests et utilitaires

**Statistiques:**
- 370 529 lignes de code/documentation
- 3 commits (initialisation + documentation + sécurité)
- Branche principale: `main`

---

### ⚠️ Livrable 3: Présentation PDF (EN COURS)
**Status:** Contenu préparé, création du PDF en attente

**Fichier préparé:** `CONTENU_PRESENTATION.md` (27 slides structurées)

**Contenu couvrant:**
- Description fonctionnelle de l'application
- Analyse comparative des 3 approches (collaborative, content-based, hybride)
- Avantages et inconvénients de chaque méthode
- Schémas d'architecture MVP
- Détail du système de recommandation
- Architecture cible pour production (gestion nouveaux users/articles)
- Roadmap d'évolution

**Action requise:** Création du PowerPoint/Google Slides et export PDF

---

## 🔮 Architecture Cible (Évolution Future)

### Problématiques à Résoudre pour la Production

1. **Mise à jour temps réel:** Les données actuelles sont statiques
2. **Latence:** Cold start Lambda de 3-5 secondes trop lent
3. **Scalabilité:** Doit supporter millions d'utilisateurs
4. **Nouveaux contenus:** Intégration continue de nouveaux articles

### Solution Proposée

**Architecture microservices avec:**

```
[CloudFront CDN] → [API Gateway] → [Lambda/ECS] → [Cache Redis]
                                           ↓
                                    [DynamoDB + RDS]
                                           ↓
                          [Kinesis Streaming] → [SageMaker Training]
```

**Composants clés:**
1. **API Gateway:** Gestion avancée des APIs (throttling, auth, versioning)
2. **Cache Redis:** Temps de réponse < 100ms
3. **Kinesis:** Streaming des interactions en temps réel
4. **DynamoDB:** Base NoSQL pour métadonnées utilisateurs
5. **SageMaker:** Retraining automatisé des modèles

**Gestion nouveaux utilisateurs:**
- Phase 1 (0 interaction): Recommandations populaires + catégories choisies à l'inscription
- Phase 2 (1-5 interactions): Hybride avec fort poids content-based
- Phase 3 (5+ interactions): Hybride équilibré
- Cache des profils utilisateurs (TTL: 1h)

**Gestion nouveaux articles:**
- Pipeline d'ingestion automatique (S3 → Lambda → Embedding → Indexation)
- Disponibilité immédiate via content-based
- A/B Testing pour exposition contrôlée
- Retraining incrémental quotidien

---

## 📊 Métriques et Performance Actuelles

### Données Traitées
- **Utilisateurs actifs:** ~38 000 (≥5 interactions)
- **Articles actifs:** ~312 000
- **Sparsité matrice:** >99% (optimisée via format sparse CSR)
- **Taille modèles:** ~350 MB (S3)

### Performance
- **Temps de réponse:** 1-5 secondes selon cold/warm start
- **Consommation Lambda:** 512-1024 MB RAM
- **Scalabilité actuelle:** Centaines de requêtes/jour sans problème

### Améliorations ML Futures Identifiées
1. **Deep Learning:** Neural Collaborative Filtering (NCF) pour patterns complexes
2. **BERT/Transformers:** Embeddings contextuels multilingues
3. **LSTM/GRU:** Modélisation des séquences temporelles de lecture
4. **Multi-Armed Bandits:** Équilibre exploration/exploitation

---

## 🚀 Prochaines Étapes

### Immédiat (Cette Semaine)
1. ✅ Finaliser la présentation PowerPoint à partir du contenu préparé
2. ✅ Réviser les points clés pour la soutenance
3. ✅ Préparer la démonstration live de l'application

### Court Terme (Si Production Décidée)
1. Déploiement API Gateway pour gestion professionnelle des APIs
2. Mise en place cache Redis pour latence < 100ms
3. Frontend React moderne (remplacement Streamlit)
4. Authentification utilisateurs (AWS Cognito)
5. Tracking interactions temps réel (Kinesis)

### Moyen Terme (3-6 mois)
1. Application mobile (React Native/Flutter)
2. Système de feedback explicite (likes/dislikes)
3. Notifications push
4. A/B Testing framework
5. Modèles Deep Learning

---

## 💡 Enseignements du Projet

### Ce Qui a Bien Fonctionné
- ✅ **Approche hybride:** Excellente décision, meilleures performances que les approches isolées
- ✅ **Serverless:** Rapidité de déploiement et coût minimal validés
- ✅ **Automatisation:** Scripts de déploiement font gagner énormément de temps
- ✅ **Documentation:** README complet facilite la reprise du projet

### Défis Rencontrés
- ⚠️ **Taille des données:** Fichier user_profiles.json de 63 MB (proche limite GitHub)
- ⚠️ **Cold Start Lambda:** 3-5 secondes (acceptable pour MVP, pas pour production)
- ⚠️ **Sparsité:** 99%+ de la matrice user-item est vide (géré par format sparse)

### Solutions Mises en Place
- ✅ Format sparse (CSR) pour matrices → Réduit consommation mémoire de 90%
- ✅ Cache Lambda → Modèles chargés une fois, réutilisés entre invocations
- ✅ Filtre de diversité → Évite la sur-recommandation d'une seule catégorie
- ✅ Architecture cible documentée → Vision claire pour scale-up

---

## 📈 Valeur Apportée par le Projet

### Technique
1. **Système opérationnel:** MVP fonctionnel en moins de 2 semaines
2. **Code industrialisable:** Versionné, documenté, déployable automatiquement
3. **Scalabilité pensée:** Architecture cible claire pour passage en production
4. **Best practices:** Git, CI/CD, documentation, tests

### Business
1. **Validation concept:** Le système de recommandation fonctionne
2. **Coût minimal:** < $5/mois avec usage MVP
3. **Time-to-market:** Prêt pour démonstration investisseurs/clients
4. **Roadmap claire:** Plan d'évolution sur 12 mois défini

### Personnel (Compétences Acquises)
1. **ML/IA:** Systèmes de recommandation hybrides, embeddings, gestion Cold Start
2. **Cloud:** AWS Lambda, S3, IAM, serverless architecture
3. **DevOps:** Scripts de déploiement, Git, CI/CD
4. **Product:** Vision MVP → Production, compromis techniques vs business

---

## 🎯 Conclusion

Le projet **My Content** a atteint ses objectifs de MVP :

✅ **Un système de recommandation fonctionnel** combinant collaborative filtering et content-based filtering

✅ **Une architecture serverless scalable** déployée sur AWS (Lambda + S3)

✅ **Une application utilisable** avec interface Streamlit intuitive

✅ **Un code professionnel** versionné sur GitHub avec déploiement automatisé

✅ **Une vision claire** pour le passage en production via l'architecture cible

**État:** 2/3 livrables complétés, dernier livrable (présentation) en finalisation

**Prêt pour:** Démonstration, soutenance, éventuel déploiement production

---

## 📎 Annexes

**Dépôt GitHub:** https://github.com/GuillaumeC96/P10_reco_my_content

**Documentation Complète:**
- `README.md` - Guide technique complet
- `docs/architecture_technique.md` - Architecture MVP détaillée
- `docs/architecture_cible.md` - Vision production
- `CONTENU_PRESENTATION.md` - 27 slides de présentation
- `LIVRABLES_CHECKLIST.md` - État des livrables et préparation soutenance

**Contact:** guillaumecassezwork@gmail.com

---

**Rapport généré le:** 11 décembre 2024
**Projet:** P10 - My Content - Système de Recommandation d'Articles
