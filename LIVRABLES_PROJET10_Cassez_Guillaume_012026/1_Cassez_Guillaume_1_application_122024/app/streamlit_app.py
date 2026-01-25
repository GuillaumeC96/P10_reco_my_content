"""
Application Streamlit pour le système de recommandation My Content
Interface simple pour tester les recommandations
"""

import streamlit as st
import requests
import json
import pandas as pd
from datetime import datetime

# Configuration de la page
st.set_page_config(
    page_title="My Content - Recommandation d'articles",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Styles CSS personnalisés avec thème sombre
st.markdown("""
<style>
    /* Force le thème sombre */
    .stApp {
        background-color: #0E1117;
        color: #FAFAFA;
    }

    .main-header {
        font-size: 2.5rem;
        color: #58A6FF;
        text-align: center;
        margin-bottom: 2rem;
        text-shadow: 0 0 10px rgba(88, 166, 255, 0.3);
    }

    .article-card {
        background-color: #1C1F26;
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        border-left: 4px solid #58A6FF;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
    }

    .article-card h3 {
        color: #58A6FF !important;
        margin-bottom: 0.5rem;
    }

    .article-card p {
        color: #C9D1D9 !important;
        margin: 0.3rem 0;
    }

    .score-badge {
        background: linear-gradient(135deg, #58A6FF, #1E88E5);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 0.5rem;
        font-size: 1.1rem;
        font-weight: bold;
        box-shadow: 0 2px 8px rgba(88, 166, 255, 0.3);
    }

    /* Améliorer la lisibilité des dataframes */
    .stDataFrame {
        background-color: #1C1F26;
    }

    /* Texte des métriques */
    [data-testid="stMetricValue"] {
        color: #58A6FF !important;
    }

    /* Boutons */
    .stButton button {
        background: linear-gradient(135deg, #58A6FF, #1E88E5);
        color: white;
        font-weight: bold;
        border: none;
        box-shadow: 0 2px 8px rgba(88, 166, 255, 0.3);
    }

    /* Info boxes */
    .stAlert {
        background-color: #1C1F26;
        color: #C9D1D9;
        border: 1px solid #30363D;
    }
</style>
""", unsafe_allow_html=True)

# En-tête
st.markdown('<p class="main-header">📰 My Content - Système de Recommandation</p>', unsafe_allow_html=True)
st.markdown("---")

# Configuration - Paramètres optimaux trouvés lors de l'entraînement
USE_LOCAL = True
AZURE_API_URL = "https://func-mycontent-reco-1269.azurewebsites.net/api/recommend"

# PARAMÈTRES OPTIMAUX (Optuna TPE - 23 Jan 2026)
# Fonction objectif: Maximiser temps de lecture (sans temps fantômes < 30s)
# Architecture hybride 39/36/25 (Content/Collaborative/Temporal)
OPTIMAL_WEIGHT_CONTENT = 0.39  # Content-Based : 39%
OPTIMAL_WEIGHT_COLLAB = 0.36   # Collaborative : 36%
OPTIMAL_WEIGHT_TREND = 0.25    # Temporal/Trending : 25%

# Sidebar - Configuration
st.sidebar.header("👤 Utilisateur")

# Sélection de l'utilisateur
user_id = st.sidebar.number_input(
    "ID de l'utilisateur",
    min_value=0,
    max_value=1000000,
    value=0,
    step=1,
    help="ID de l'utilisateur pour lequel générer des recommandations"
)

# Nombre de recommandations (fixé)
n_recommendations = 5

# Utiliser les poids optimaux (fixés)
weight_collab = OPTIMAL_WEIGHT_COLLAB
weight_content = OPTIMAL_WEIGHT_CONTENT
weight_trend = OPTIMAL_WEIGHT_TREND

# Paramètres du modèle
st.sidebar.markdown("---")
st.sidebar.markdown("### ⚙️ Paramètres du Modèle")

# Afficher les poids (non modifiables)
st.sidebar.markdown("**Architecture Hybride 39/36/25:**")
st.sidebar.markdown(f"""
- Content-Based: **{weight_content*100:.0f}%**
- Collaborative: **{weight_collab*100:.0f}%**
- Temporal: **{weight_trend*100:.0f}%**

*(Optuna TPE - 23 Jan 2026)*
""")

# Contrôle de la diversité (modifiable)
st.sidebar.markdown("---")
use_diversity = st.sidebar.checkbox(
    "🎨 Activer le filtre de diversité",
    value=True,
    help="Force la diversité des catégories dans les recommandations"
)

st.sidebar.markdown(f"**Recommandations:** {n_recommendations} articles")

# Section principale
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader(f"👤 Recommandations pour l'utilisateur #{user_id}")

with col2:
    if st.button("🔄 Générer des recommandations", type="primary", use_container_width=True):
        st.session_state.generate = True

# Fonction pour appeler l'API Azure
def get_recommendations_from_azure(user_id, n_recommendations, weight_collab, weight_content, weight_trend, use_diversity):
    """Appelle l'API Azure Functions"""
    try:
        # Calculer les poids en pourcentage (Azure utilise 0.3, 0.4, 0.3)
        total_weight = weight_collab + weight_content + weight_trend
        payload = {
            'user_id': int(user_id),
            'n': int(n_recommendations),
            'weight_collab': round(weight_collab / total_weight, 2),
            'weight_content': round(weight_content / total_weight, 2),
            'weight_trend': round(weight_trend / total_weight, 2),
            'use_diversity': use_diversity
        }

        response = requests.post(AZURE_API_URL, json=payload, headers={'Content-Type': 'application/json'}, timeout=30)
        response.raise_for_status()

        result = response.json()

        # Adapter le format de réponse
        return {
            'user_id': result['user_id'],
            'n_recommendations': result['n_recommendations'],
            'recommendations': result['recommendations'],
            'parameters': result['parameters']
        }

    except requests.exceptions.RequestException as e:
        st.error(f"❌ Erreur de connexion à l'API Azure: {e}")
        return None
    except Exception as e:
        st.error(f"❌ Erreur: {e}")
        return None

# Fonction pour le mode local
def get_recommendations_local(user_id, n_recommendations, weight_collab, weight_content, weight_trend, use_diversity):
    """Utilise le moteur local"""
    try:
        import sys
        sys.path.append('../azure_function')
        from recommendation_engine import RecommendationEngine

        # Initialiser le moteur
        if 'engine' not in st.session_state:
            with st.spinner("Chargement des modèles..."):
                st.session_state.engine = RecommendationEngine(models_path='../models')
                st.session_state.engine.load_models()

        # Générer les recommandations
        recommendations = st.session_state.engine.recommend(
            user_id=user_id,
            n_recommendations=n_recommendations,
            weight_collab=weight_collab,
            weight_content=weight_content,
            weight_trend=weight_trend,
            use_diversity=use_diversity
        )

        return {
            'user_id': user_id,
            'n_recommendations': len(recommendations),
            'recommendations': recommendations,
            'parameters': {
                'weight_collab': weight_collab,
                'weight_content': weight_content,
                'weight_trend': weight_trend,
                'weights_ratio': f"{weight_collab}:{weight_content}:{weight_trend}",
                'use_diversity': use_diversity
            }
        }

    except Exception as e:
        st.error(f"❌ Erreur avec le moteur local: {e}")
        import traceback
        st.code(traceback.format_exc())
        return None

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
        st.success(f"✅ {result['n_recommendations']} recommandations générées avec succès!")

        # Informations sur les paramètres utilisés
        with st.expander("ℹ️ Paramètres utilisés"):
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("User ID", result['user_id'])
            with col2:
                st.metric("Content-Based", f"{result['parameters']['weight_content']*100:.0f}%")
            with col3:
                st.metric("Collaborative", f"{result['parameters']['weight_collab']*100:.0f}%")
            with col4:
                st.metric("Temporal", f"{result['parameters']['weight_trend']*100:.0f}%")

            st.info(f"**Architecture:** Hybride 39/36/25 (Optuna TPE) | **Diversité:** {'✓ Activée' if result['parameters']['use_diversity'] else '✗ Désactivée'}")

        st.markdown("---")

        # Afficher les recommandations
        for i, rec in enumerate(result['recommendations'], 1):
            with st.container():
                col1, col2 = st.columns([4, 1])

                with col1:
                    st.markdown(f"""
                    <div class="article-card">
                        <h3>#{i} - Article ID: {rec['article_id']}</h3>
                        <p><strong>Catégorie:</strong> {rec['category_id']} |
                           <strong>Éditeur:</strong> {rec['publisher_id']} |
                           <strong>Mots:</strong> {rec['words_count']}</p>
                        <p><strong>Date:</strong> {datetime.fromtimestamp(rec['created_at_ts']/1000).strftime('%Y-%m-%d')}</p>
                    </div>
                    """, unsafe_allow_html=True)

                with col2:
                    st.markdown(f"""
                    <div style="text-align: center; padding-top: 1rem;">
                        <span class="score-badge">Score: {rec['score']:.3f}</span>
                    </div>
                    """, unsafe_allow_html=True)

        # Tableau récapitulatif
        st.markdown("---")
        st.subheader("📊 Vue d'ensemble")

        df = pd.DataFrame(result['recommendations'])
        df['created_at'] = pd.to_datetime(df['created_at_ts'], unit='ms')
        df = df[['article_id', 'category_id', 'publisher_id', 'words_count', 'score', 'created_at']]

        st.dataframe(df, use_container_width=True)

        # Statistiques
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Articles uniques", len(df))
        with col2:
            st.metric("Catégories uniques", df['category_id'].nunique())
        with col3:
            st.metric("Mots moyen", f"{df['words_count'].mean():.0f}")
        with col4:
            st.metric("Score moyen", f"{df['score'].mean():.3f}")

        # Télécharger les résultats
        st.markdown("---")
        csv = df.to_csv(index=False)
        st.download_button(
            label="📥 Télécharger les résultats (CSV)",
            data=csv,
            file_name=f"recommendations_user_{user_id}.csv",
            mime="text/csv"
        )

    elif 'error' in result:
        st.error(f"❌ Erreur: {result['error']}")
    else:
        st.warning("⚠️ Aucune recommandation générée")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666;">
    <p>My Content - Système de recommandation MVP v1.0</p>
    <p>Powered by Azure Functions & Streamlit</p>
</div>
""", unsafe_allow_html=True)
