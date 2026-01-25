"""
Application Streamlit AMÉLIORÉE pour le système de recommandation My Content
Interface enrichie avec visualisations et profil utilisateur
"""

import streamlit as st
import requests
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import networkx as nx
from collections import Counter

# Configuration de la page
st.set_page_config(
    page_title="My Content - Recommandation d'articles",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configuration
USE_LOCAL = False  # False pour Streamlit Cloud (utilise API Azure)
AZURE_API_URL = "https://func-mycontent-reco-1269.azurewebsites.net/api/recommend"

# PARAMÈTRES OPTIMAUX (Optuna TPE - 23 Jan 2026)
# Fonction objectif: Maximiser temps de lecture (sans temps fantômes < 30s)
OPTIMAL_WEIGHT_CONTENT = 0.39  # Content-Based : 39%
OPTIMAL_WEIGHT_COLLAB = 0.36   # Collaborative : 36%
OPTIMAL_WEIGHT_TREND = 0.25    # Temporal/Trending : 25%

# NOMS DE CATÉGORIES (basés sur la structure du réseau)
# Super hubs (très connectés, larges audiences) = catégories généralistes
# Medium hubs = catégories thématiques populaires
# Peripheral = niches spécialisées
CATEGORY_NAMES = {
    # Super hubs (19 connexions, 98-120k users)
    281: "Actualités Générales",
    375: "Divertissement & Célébrités",

    # Major hubs (16-17 connexions, 64-71k users)
    412: "Sport",
    437: "Économie & Finance",

    # Medium connectivity (7-9 connexions)
    250: "Politique",
    399: "Culture & Arts",
    209: "Technologie",
    331: "Société & Faits Divers",
    418: "International & Monde",

    # Peripheral categories (3-4 connexions) - niches spécialisées
    26: "Sciences",
    118: "Santé & Bien-être",
    136: "Gastronomie",
    186: "Loisirs & Hobbies",
    252: "Voyages & Tourisme",
    327: "Éducation",
    409: "Automobile",
    421: "Mode & Style",
    428: "Immobilier",
    431: "Environnement",
    442: "Livres & Littérature"
}

def get_category_name(cat_id):
    """Retourne le nom de la catégorie avec son ID (format: Nom #ID)"""
    if cat_id in CATEGORY_NAMES:
        # Catégories nommées explicitement
        return f"{CATEGORY_NAMES[cat_id]} #{cat_id}"

    # Générer un nom générique basé sur l'ID pour les catégories non mappées
    # Les catégories < 100 sont souvent des catégories principales
    if cat_id < 100:
        return f"Actualités Diverses #{cat_id}"
    elif cat_id < 200:
        return f"Société & Vie Quotidienne #{cat_id}"
    elif cat_id < 300:
        return f"Sport & Compétitions #{cat_id}"
    elif cat_id < 400:
        return f"Culture & Médias #{cat_id}"
    else:
        return f"Thématique #{cat_id}"

# ===== FONCTIONS UTILITAIRES =====

@st.cache_data
def load_user_profiles():
    """Charge les profils utilisateurs"""
    try:
        with open('data/user_profiles.json', 'r') as f:
            return json.load(f)
    except:
        return {}

@st.cache_data
def load_articles_metadata():
    """Charge les métadonnées des articles"""
    try:
        return pd.read_csv('data/articles_metadata.csv')
    except:
        return pd.DataFrame()

@st.cache_data
def load_interactions_data():
    """Charge les données d'interactions avec temps de lecture"""
    try:
        # Essayer d'abord la version v3 (la plus récente)
        return pd.read_csv('data/interactions_cleaned_v3.csv')
    except:
        try:
            return pd.read_csv('data/interactions_cleaned.csv')
        except:
            return pd.DataFrame()

def get_user_profile(user_id):
    """Récupère le profil d'un utilisateur"""
    profiles = load_user_profiles()
    return profiles.get(str(user_id), None)

def get_recommendations_from_azure(user_id, n_recommendations, weight_collab, weight_content, weight_trend, use_diversity):
    """Appelle l'API Azure Functions"""
    try:
        import time
        total_weight = weight_collab + weight_content + weight_trend
        payload = {
            'user_id': int(user_id),
            'n': int(n_recommendations),
            'weight_collab': round(weight_collab / total_weight, 2),
            'weight_content': round(weight_content / total_weight, 2),
            'weight_trend': round(weight_trend / total_weight, 2),
            'use_diversity': use_diversity
        }

        # Mesurer le temps de latence
        start_time = time.time()
        response = requests.post(AZURE_API_URL, json=payload, headers={'Content-Type': 'application/json'}, timeout=30)
        response.raise_for_status()
        result = response.json()
        latency_ms = (time.time() - start_time) * 1000

        return {
            'user_id': result['user_id'],
            'n_recommendations': result['n_recommendations'],
            'recommendations': result['recommendations'],
            'latency_ms': latency_ms,
            'parameters': result['parameters']
        }
    except Exception as e:
        st.error(f"❌ Erreur API Azure: {e}")
        return None

def get_recommendations_local(user_id, n_recommendations, weight_collab, weight_content, weight_trend, use_diversity):
    """Utilise le moteur local"""
    try:
        import sys
        import time
        sys.path.append('../azure_function')
        from recommendation_engine import RecommendationEngine

        if 'engine' not in st.session_state:
            with st.spinner("Chargement des modèles..."):
                st.session_state.engine = RecommendationEngine(models_path='../models')
                st.session_state.engine.load_models()

        # Mesurer le temps de latence
        start_time = time.time()
        recommendations = st.session_state.engine.recommend(
            user_id=user_id,
            n_recommendations=n_recommendations,
            weight_collab=weight_collab,
            weight_content=weight_content,
            weight_trend=weight_trend,
            use_diversity=use_diversity
        )
        latency_ms = (time.time() - start_time) * 1000

        return {
            'user_id': user_id,
            'n_recommendations': len(recommendations),
            'recommendations': recommendations,
            'latency_ms': latency_ms,
            'parameters': {
                'weight_collab': weight_collab,
                'weight_content': weight_content,
                'weight_trend': weight_trend,
                'use_diversity': use_diversity
            }
        }
    except Exception as e:
        st.error(f"❌ Erreur moteur local: {e}")
        import traceback
        st.code(traceback.format_exc())
        return None

# ===== INTERFACE PRINCIPALE =====

# Sidebar
st.sidebar.title("📰 My Content")
st.sidebar.markdown("---")

# Navigation
page = st.sidebar.radio(
    "Navigation",
    ["🕸️ Graphe de Réseau", "🎯 Recommandations"],
    label_visibility="collapsed"
)

st.sidebar.markdown("---")
st.sidebar.header("👤 Configuration")

# Sélection utilisateur
user_id = st.sidebar.number_input(
    "ID de l'utilisateur",
    min_value=0,
    max_value=1000000,
    value=0,
    step=1,
    help="ID de l'utilisateur pour lequel générer des recommandations"
)

# Nombre de recommandations
n_recommendations = st.sidebar.slider(
    "Nombre de recommandations",
    min_value=3,
    max_value=20,
    value=5,
    step=1
)

# Poids (fixés)
weight_content = OPTIMAL_WEIGHT_CONTENT
weight_collab = OPTIMAL_WEIGHT_COLLAB
weight_trend = OPTIMAL_WEIGHT_TREND

# Paramètres du modèle
st.sidebar.markdown("---")
st.sidebar.markdown("### ⚙️ Paramètres du Modèle")
st.sidebar.markdown(f"""
**Architecture Hybride 39/36/25:**
- Content-Based: **{weight_content*100:.0f}%**
- Collaborative: **{weight_collab*100:.0f}%**
- Temporal: **{weight_trend*100:.0f}%**

*(Optuna TPE - 23 Jan 2026)*
""")

# Contrôle diversité
st.sidebar.markdown("---")
use_diversity = st.sidebar.checkbox(
    "🎨 Activer le filtre de diversité",
    value=False,
    help="Force la diversité des catégories"
)

# ===== PAGE 1: RECOMMANDATIONS =====
if page == "🎯 Recommandations":
    st.title("🎯 Recommandations Personnalisées")

    # Afficher le profil utilisateur
    profile = get_user_profile(user_id)
    interactions_df = load_interactions_data()
    articles_meta = load_articles_metadata()

    if profile:
        st.markdown("---")
        st.subheader(f"📊 Profil de l'utilisateur #{user_id}")

        # Filtrer les interactions de cet utilisateur
        user_interactions = interactions_df[interactions_df['user_id'] == user_id].copy() if not interactions_df.empty else pd.DataFrame()

        if not user_interactions.empty and not articles_meta.empty:
            # Joindre avec les métadonnées des articles
            user_interactions = user_interactions.merge(
                articles_meta[['article_id', 'category_id']],
                on='article_id',
                how='left'
            )

            # Calculer les statistiques
            total_time = user_interactions['time_spent_cleaned'].sum() / 60  # en minutes
            avg_time_per_article = user_interactions['time_spent_cleaned'].mean() / 60
            n_categories = user_interactions['category_id'].nunique()
            n_articles = user_interactions['article_id'].nunique()

            # Temps par catégorie
            time_by_category = user_interactions.groupby('category_id')['time_spent_cleaned'].sum().sort_values(ascending=False) / 60
            articles_by_category = user_interactions.groupby('category_id')['article_id'].nunique()

            # Métriques principales
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("📚 Articles lus", n_articles)
            with col2:
                st.metric("⏱️ Temps total", f"{total_time:.1f} min")
            with col3:
                st.metric("⌛ Temps/article", f"{avg_time_per_article:.1f} min")
            with col4:
                st.metric("🏷️ Catégories lues", n_categories)

            # Stocker les stats pour l'analyse de cohérence plus tard
            st.session_state.user_interactions = user_interactions
            st.session_state.time_by_category = time_by_category
        else:
            # Fallback sur les anciennes métriques si pas d'interactions
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("📚 Articles lus", profile['num_articles'])
            with col2:
                st.metric("🔄 Interactions", profile['num_interactions'])
            with col3:
                st.metric("📝 Mots moyens", f"{profile['avg_words']:.0f}")
            with col4:
                st.metric("🏷️ Catégories favorites", len(profile['top_categories']))
    else:
        st.info(f"ℹ️ Nouvel utilisateur #{user_id} (pas d'historique)")

    # Détecter le changement d'utilisateur
    if 'last_user_id' not in st.session_state or st.session_state.last_user_id != user_id:
        st.session_state.last_user_id = user_id
        st.session_state.generate = True
        # Effacer les anciennes recommandations
        if 'last_recommendations' in st.session_state:
            del st.session_state.last_recommendations

    # Bouton de génération
    st.markdown("---")
    if st.button("🔄 Générer des recommandations", type="primary", use_container_width=True):
        st.session_state.generate = True

    # Générer les recommandations
    if st.session_state.get('generate', False) or 'last_recommendations' not in st.session_state:
        with st.spinner("🔄 Génération des recommandations en cours..."):
            if USE_LOCAL:
                result = get_recommendations_local(user_id, n_recommendations, weight_collab, weight_content, weight_trend, use_diversity)
            else:
                result = get_recommendations_from_azure(user_id, n_recommendations, weight_collab, weight_content, weight_trend, use_diversity)

            if result:
                st.session_state.last_recommendations = result
                st.session_state.generate = False

    # Afficher les résultats
    if 'last_recommendations' in st.session_state:
        result = st.session_state.last_recommendations

        if 'recommendations' in result and result['recommendations']:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.success(f"✅ {result['n_recommendations']} recommandations générées avec succès!")
            with col2:
                if 'latency_ms' in result:
                    latency = result['latency_ms']
                    if latency < 100:
                        st.metric("⚡ Latence API", f"{latency:.0f} ms", delta="Excellent", delta_color="normal")
                    elif latency < 500:
                        st.metric("⚡ Latence API", f"{latency:.0f} ms", delta="Bon", delta_color="normal")
                    else:
                        st.metric("⚡ Latence API", f"{latency:.0f} ms", delta="Lent", delta_color="inverse")

            # Graphique de comparaison d'abord
            rec_categories = [r['category_id'] for r in result['recommendations']]
            rec_cat_counter = Counter(rec_categories)

            if profile:
                st.markdown("---")
                st.subheader("📊 Comparaison Profil vs Recommandations")

                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("#### 🏷️ Catégories Recommandées")
                    # Convertir les IDs en noms de catégories
                    rec_cat_names = [(get_category_name(cat_id), count) for cat_id, count in rec_cat_counter.most_common()]
                    rec_cat_df = pd.DataFrame(rec_cat_names, columns=['Catégorie', 'Count'])
                    fig = px.pie(rec_cat_df, values='Count', names='Catégorie',
                                color_discrete_sequence=px.colors.sequential.RdBu)
                    fig.update_layout(height=300)
                    st.plotly_chart(fig, use_container_width=True)

                with col2:
                    st.markdown("#### 🌟 Catégories Favorites (Temps de lecture)")
                    # Utiliser les temps de lecture par catégorie
                    if 'time_by_category' in st.session_state and len(st.session_state.time_by_category) > 0:
                        time_cats = st.session_state.time_by_category.head(10)
                        # Convertir les IDs en noms de catégories
                        fav_df = pd.DataFrame({
                            'Catégorie': [get_category_name(cat_id) for cat_id in time_cats.index],
                            'Temps (min)': time_cats.values
                        })
                        # Utiliser la même palette de couleurs (RdBu) pour cohérence visuelle
                        fig = px.pie(fav_df, values='Temps (min)', names='Catégorie',
                                    color_discrete_sequence=px.colors.sequential.RdBu)
                        fig.update_layout(height=300)
                        st.plotly_chart(fig, use_container_width=True)
                    elif profile['top_categories']:
                        # Fallback sur les catégories favorites si pas de données de temps
                        # Convertir les IDs en noms de catégories
                        fav_df = pd.DataFrame({
                            'Catégorie': [get_category_name(cat_id) for cat_id in profile['top_categories'][:5]],
                            'Rang': list(range(1, min(6, len(profile['top_categories'])+1)))
                        })
                        fig = px.pie(fav_df, values='Rang', names='Catégorie',
                                    color_discrete_sequence=px.colors.sequential.Viridis)
                        fig.update_layout(height=300)
                        st.plotly_chart(fig, use_container_width=True)

                # Analyse de cohérence après les camemberts
                st.markdown("---")
                st.subheader("🎯 Analyse de Cohérence")

                matching_cats = set(rec_categories) & set(profile['top_categories'])
                coherence = len(matching_cats) / len(set(rec_categories)) * 100 if rec_categories else 0

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("🎯 Cohérence", f"{coherence:.0f}%",
                             help="% de recommandations dans vos catégories favorites")
                with col2:
                    st.metric("🎨 Diversité", f"{len(set(rec_categories))}/{len(rec_categories)}")
                with col3:
                    st.metric("✨ Nouveauté", f"{100-coherence:.0f}%",
                             help="% de recommandations dans de nouvelles catégories")

            # Afficher les recommandations
            st.markdown("---")
            st.subheader("📰 Articles Recommandés")

            articles_meta = load_articles_metadata()

            for i, rec in enumerate(result['recommendations'], 1):
                cat_name = get_category_name(rec['category_id'])
                with st.expander(f"#{i} - Article {rec['article_id']} | Score: {rec['score']:.3f} | {cat_name}"):
                    col1, col2 = st.columns([2, 1])

                    with col1:
                        st.markdown(f"""
                        **📊 Métadonnées:**
                        - **Article ID:** {rec['article_id']}
                        - **Catégorie:** {cat_name}
                        - **Éditeur:** {rec['publisher_id']}
                        - **Longueur:** {rec['words_count']} mots (≈ {rec['words_count']//200 + 1} min de lecture)
                        - **Date:** {datetime.fromtimestamp(rec['created_at_ts']/1000).strftime('%Y-%m-%d %H:%M')}
                        """)

                        # Indicateur si dans les catégories favorites
                        if profile and rec['category_id'] in profile['top_categories']:
                            st.success("✅ Catégorie favorite de l'utilisateur!")
                        elif profile:
                            st.info("💡 Nouvelle catégorie à découvrir")

                    with col2:
                        st.markdown(f"""
                        <div style="text-align: center; padding: 2rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 10px; color: white;">
                            <h2 style="margin: 0;">🎯 {rec['score']:.3f}</h2>
                            <p style="margin: 0;">Score de pertinence</p>
                        </div>
                        """, unsafe_allow_html=True)

            # Section Debug
            st.markdown("---")
            st.markdown("### 🔍 Informations de Debug")

            # Créer le texte de debug
            debug_text = f"""=== RECOMMANDATIONS - DEBUG INFO ===
Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

PARAMÈTRES DE REQUÊTE:
- User ID: {result['user_id']}
- Nombre de recommandations demandées: {result['n_recommendations']}
- Architecture: Hybride {result['parameters']['weight_content']*100:.0f}/{result['parameters']['weight_collab']*100:.0f}/{result['parameters']['weight_trend']*100:.0f}
  - Content-Based: {result['parameters']['weight_content']*100:.0f}%
  - Collaborative Filtering: {result['parameters']['weight_collab']*100:.0f}%
  - Temporal/Trending: {result['parameters']['weight_trend']*100:.0f}%
- Filtre de diversité: {'✓ Activé' if result['parameters']['use_diversity'] else '✗ Désactivé'}
"""

            # Ajouter latence si disponible
            if 'latency_ms' in result:
                latency = result['latency_ms']
                debug_text += f"- Latence API: {latency:.0f} ms"
                if latency < 100:
                    debug_text += " (Excellent)\n"
                elif latency < 500:
                    debug_text += " (Bon)\n"
                else:
                    debug_text += " (Lent)\n"

            # Profil utilisateur si disponible
            if profile:
                debug_text += f"\nPROFIL UTILISATEUR:\n"
                debug_text += f"- Articles lus: {profile.get('num_articles', 'N/A')}\n"
                if 'top_categories' in profile and profile['top_categories']:
                    debug_text += f"- Catégories favorites: {[get_category_name(cat_id) for cat_id in profile['top_categories'][:5]]}\n"

            # Statistiques sur les interactions si disponibles
            if 'user_interactions' in st.session_state:
                user_int = st.session_state.user_interactions
                debug_text += f"- Temps total de lecture: {user_int['time_spent_cleaned'].sum() / 60:.1f} minutes\n"
                debug_text += f"- Temps moyen/article: {user_int['time_spent_cleaned'].mean() / 60:.1f} minutes\n"
                debug_text += f"- Catégories lues: {user_int['category_id'].nunique()}\n"

            # Résultats
            debug_text += f"\nRÉSULTATS:\n"
            debug_text += f"- Nombre de recommandations générées: {len(result['recommendations'])}\n"

            # Statistiques sur les recommandations
            rec_categories = [r['category_id'] for r in result['recommendations']]
            rec_scores = [r['score'] for r in result['recommendations']]

            debug_text += f"- Catégories uniques: {len(set(rec_categories))}\n"
            debug_text += f"- Score moyen: {sum(rec_scores)/len(rec_scores):.3f}\n"
            debug_text += f"- Score min: {min(rec_scores):.3f}\n"
            debug_text += f"- Score max: {max(rec_scores):.3f}\n"

            # Liste des catégories recommandées
            from collections import Counter
            cat_counter = Counter(rec_categories)
            debug_text += f"\nCATÉGORIES RECOMMANDÉES:\n"
            for cat_id, count in cat_counter.most_common():
                debug_text += f"- {get_category_name(cat_id)}: {count} article(s)\n"

            # Détail des articles
            debug_text += f"\nDÉTAIL DES ARTICLES RECOMMANDÉS:\n"
            for i, rec in enumerate(result['recommendations'], 1):
                debug_text += f"\n{i}. Article {rec['article_id']}\n"
                debug_text += f"   - Catégorie: {get_category_name(rec['category_id'])}\n"
                debug_text += f"   - Score: {rec['score']:.3f}\n"
                debug_text += f"   - Éditeur: {rec['publisher_id']}\n"
                debug_text += f"   - Nombre de mots: {rec['words_count']}\n"
                debug_text += f"   - Date: {datetime.fromtimestamp(rec['created_at_ts']/1000).strftime('%Y-%m-%d %H:%M')}\n"

            # Afficher le texte avec possibilité de copier
            st.text_area("📋 Copier ce texte pour debug", debug_text, height=400)

            # Export CSV
            st.markdown("---")
            df = pd.DataFrame(result['recommendations'])
            df['created_at'] = pd.to_datetime(df['created_at_ts'], unit='ms')
            # Ajouter les noms de catégories
            df['category_name'] = df['category_id'].apply(get_category_name)
            csv = df.to_csv(index=False)
            st.download_button(
                label="📥 Télécharger les résultats (CSV)",
                data=csv,
                file_name=f"recommendations_user_{user_id}.csv",
                mime="text/csv"
            )

# ===== PAGE 2: GRAPHE DE RÉSEAU =====
elif page == "🕸️ Graphe de Réseau":
    st.title("🕸️ Graphe de Réseau Global des Catégories")
    st.markdown("**Analyse globale** - Visualisation des relations entre catégories basée sur **tous les utilisateurs**")

    # Charger toutes les interactions
    interactions_df = load_interactions_data()
    articles_meta = load_articles_metadata()

    if not interactions_df.empty and not articles_meta.empty:
        with st.spinner("Construction du graphe de réseau global..."):
            # Joindre interactions avec métadonnées pour obtenir les catégories
            interactions_full = interactions_df.merge(
                articles_meta[['article_id', 'category_id']],
                on='article_id',
                how='left'
            )

            # Filtrer les NaN dans category_id
            interactions_full = interactions_full[interactions_full['category_id'].notna()]

            # Pour chaque utilisateur, obtenir les catégories qu'il a lues
            user_categories = interactions_full.groupby('user_id')['category_id'].apply(lambda x: set(x.dropna())).to_dict()

            # Compter combien d'utilisateurs lisent chaque catégorie
            category_users = {}
            for user, cats in user_categories.items():
                for cat in cats:
                    if pd.notna(cat):  # Vérifier que ce n'est pas NaN
                        if cat not in category_users:
                            category_users[cat] = set()
                        category_users[cat].add(user)

            # Prendre les top 20 catégories les plus lues
            top_categories = sorted(category_users.items(), key=lambda x: len(x[1]), reverse=True)[:20]
            top_cat_ids = [cat for cat, _ in top_categories]

            # Créer le graphe
            G = nx.Graph()

            # Ajouter les nœuds avec taille = nombre d'utilisateurs
            for cat, users in top_categories:
                G.add_node(cat, size=len(users))

            # Créer des liens entre catégories lues par les mêmes utilisateurs
            from itertools import combinations
            for user, cats in user_categories.items():
                # Filtrer pour ne garder que les top catégories
                user_top_cats = [c for c in cats if c in top_cat_ids]

                # Créer des liens entre toutes les paires de catégories lues par cet utilisateur
                for cat1, cat2 in combinations(user_top_cats, 2):
                    if G.has_edge(cat1, cat2):
                        G[cat1][cat2]['weight'] += 1
                    else:
                        G.add_edge(cat1, cat2, weight=1)

            # FILTRAGE: Ne garder que les connexions significatives (au-dessus du percentile 60)
            weights = [G[e[0]][e[1]]['weight'] for e in G.edges()]
            threshold = sorted(weights)[int(len(weights) * 0.60)]  # Percentile 60

            # Supprimer les arêtes faibles
            edges_to_remove = [(e[0], e[1]) for e in G.edges() if G[e[0]][e[1]]['weight'] < threshold]
            G.remove_edges_from(edges_to_remove)

            # Vérifier qu'on a des nœuds
            if len(G.nodes()) == 0:
                st.error("❌ Aucun nœud dans le graphe!")
                st.stop()

            # Calculer le layout de base
            try:
                pos = nx.kamada_kawai_layout(G, scale=2.0)
            except:
                pos = nx.spring_layout(G, k=3, iterations=100, seed=42)

            # Anti-collision proportionnelle aux tailles des bulles
            # Plus les bulles sont grosses, plus elles doivent être espacées
            node_sizes_dict = {node: G.nodes[node]['size'] for node in G.nodes()}
            max_size = max(node_sizes_dict.values())

            # Normaliser les tailles pour calculer les rayons (entre 0.1 et 1.0)
            node_radius = {node: 0.1 + 0.9 * (size / max_size) for node, size in node_sizes_dict.items()}

            # Appliquer un algorithme de répulsion sur 50 itérations
            for iteration in range(50):
                moves = {}
                for node1 in G.nodes():
                    dx_total, dy_total = 0, 0
                    x1, y1 = pos[node1]

                    for node2 in G.nodes():
                        if node1 == node2:
                            continue

                        x2, y2 = pos[node2]
                        dx = x1 - x2
                        dy = y1 - y2
                        dist = (dx**2 + dy**2)**0.5

                        if dist < 0.001:
                            dist = 0.001

                        # Distance minimale = somme des rayons * facteur d'espace
                        min_dist = (node_radius[node1] + node_radius[node2]) * 0.4

                        # Si trop proche, repousser proportionnellement aux tailles
                        if dist < min_dist:
                            repulsion = (min_dist - dist) / dist
                            dx_total += dx * repulsion
                            dy_total += dy * repulsion

                    moves[node1] = (dx_total * 0.1, dy_total * 0.1)  # Amortissement

                # Appliquer les déplacements
                for node, (dx, dy) in moves.items():
                    x, y = pos[node]
                    pos[node] = (x + dx, y + dy)

            # Créer les arêtes avec épaisseur proportionnelle au poids (LINÉAIRE)
            edge_traces = []
            edge_weights = [G[edge[0]][edge[1]]['weight'] for edge in G.edges()]
            min_weight = min(edge_weights) if edge_weights else 0
            max_weight = max(edge_weights) if edge_weights else 1
            weight_range = max_weight - min_weight if max_weight > min_weight else 1

            for edge in G.edges():
                x0, y0 = pos[edge[0]]
                x1, y1 = pos[edge[1]]
                weight = G[edge[0]][edge[1]]['weight']

                # Épaisseur LINÉAIRE normalisée entre 1px et 10px
                width = 1.0 + 9.0 * ((weight - min_weight) / weight_range)

                # Opacité proportionnelle
                opacity = 0.4 + 0.5 * ((weight - min_weight) / weight_range)

                edge_traces.append(
                    go.Scatter(
                        x=[x0, x1, None],
                        y=[y0, y1, None],
                        mode='lines',
                        line=dict(width=width, color=f'rgba(100, 100, 100, {opacity})'),
                        hoverinfo='text',
                        text=f'{weight} utilisateurs en commun',
                        showlegend=False
                    )
                )

            # Créer les nœuds avec couleurs variées
            node_sizes = [G.nodes[node]['size'] for node in G.nodes()]
            node_degrees = [G.degree(node) for node in G.nodes()]

            # Normaliser les tailles des nœuds (entre 20 et 80)
            max_size = max(node_sizes) if node_sizes else 1
            min_size = min(node_sizes) if node_sizes else 1
            normalized_sizes = [20 + 60 * ((s - min_size) / (max_size - min_size)) if max_size > min_size else 40 for s in node_sizes]

            node_trace = go.Scatter(
                x=[pos[node][0] for node in G.nodes()],
                y=[pos[node][1] for node in G.nodes()],
                mode='markers+text',
                text=[get_category_name(node) for node in G.nodes()],
                textposition="top center",
                textfont=dict(size=15, color='white'),
                marker=dict(
                    size=normalized_sizes,
                    color=node_degrees,
                    colorscale='Viridis',  # Palette plus fiable
                    showscale=True,
                    colorbar=dict(
                        title=dict(text="Connexions"),
                        thickness=15,
                        xanchor='left'
                    ),
                    line=dict(width=2, color='white')
                ),
                hovertemplate='<b>Catégorie %{text}</b><br>' +
                             'Utilisateurs: %{customdata[0]}<br>' +
                             'Connexions: %{marker.color}<extra></extra>',
                customdata=[[G.nodes[node]['size']] for node in G.nodes()],
                showlegend=False
            )

            # Créer la figure
            fig = go.Figure(data=edge_traces + [node_trace])
            fig.update_layout(
                title=dict(
                    text="Réseau Global des Catégories - Analyse de tous les utilisateurs",
                    font=dict(size=18)
                ),
                showlegend=False,
                hovermode='closest',
                margin=dict(b=20,l=20,r=20,t=60),
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                height=700,
                plot_bgcolor='#0E1117',
                paper_bgcolor='#0E1117'
            )

            st.plotly_chart(fig, use_container_width=True)

            # Statistiques
            st.markdown("---")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("🏷️ Catégories analysées", len(G.nodes()))
            with col2:
                st.metric("🔗 Connexions totales", len(G.edges()))
            with col3:
                st.metric("👥 Utilisateurs analysés", len(user_categories))
            with col4:
                avg_degree = sum(node_degrees) / len(node_degrees) if node_degrees else 0
                st.metric("📊 Connexions/catégorie", f"{avg_degree:.1f}")


        # Légende
        st.markdown("---")
        st.markdown("""
        ### 📖 Comment lire ce graphe ?

        - **Nœuds (cercles)** : Catégories d'articles (les 20 plus populaires)
        - **Taille des nœuds** : Nombre d'utilisateurs ayant lu cette catégorie
        - **Couleur des nœuds** : Nombre de connexions avec d'autres catégories (arc-en-ciel)
        - **Liens (lignes)** : Catégories lues par les mêmes utilisateurs
        - **Épaisseur des liens** : Force de la connexion (nombre d'utilisateurs en commun)

        Ce graphe montre comment vos habitudes de lecture créent des "clusters" de catégories liées.
        """)

        # Statistiques du réseau
        st.markdown("---")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("🔗 Nœuds", G.number_of_nodes())
        with col2:
            st.metric("📊 Liens", G.number_of_edges())
        with col3:
            density = nx.density(G) if G.number_of_nodes() > 1 else 0
            st.metric("🌐 Densité", f"{density:.2%}")
        with col4:
            if G.number_of_nodes() > 0:
                most_connected = max(dict(G.degree()).items(), key=lambda x: x[1])
                st.metric("⭐ Plus connectée", get_category_name(most_connected[0]))
    else:
        st.warning("⚠️ Pas assez de données pour construire le graphe de réseau")
        st.info("💡 Essayez avec un utilisateur ayant plus d'historique (par ex: user_id > 50)")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666;">
    <p>My Content - Système de recommandation MVP v1.0</p>
    <p>Powered by Azure Functions & Streamlit</p>
</div>
""", unsafe_allow_html=True)
