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
    layout="wide"
)

# Styles CSS personnalisés
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E88E5;
        text-align: center;
        margin-bottom: 2rem;
    }
    .article-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        border-left: 4px solid #1E88E5;
    }
    .score-badge {
        background-color: #1E88E5;
        color: white;
        padding: 0.25rem 0.5rem;
        border-radius: 0.25rem;
        font-size: 0.9rem;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# En-tête
st.markdown('<p class="main-header">📰 My Content - Système de Recommandation</p>', unsafe_allow_html=True)
st.markdown("---")

# Configuration
# Remplacer par l'URL de votre Lambda Function
LAMBDA_URL = st.sidebar.text_input(
    "URL de la Lambda Function AWS",
    value="https://your-lambda-url.lambda-url.us-east-1.on.aws/",
    help="URL de votre Lambda Function (avec Function URL activé)"
)

USE_LOCAL = st.sidebar.checkbox(
    "Mode local (sans Lambda)",
    value=True,
    help="Utiliser le moteur local au lieu de la Lambda (pour tests)"
)

# Sidebar avec les paramètres
st.sidebar.header("⚙️ Paramètres")

# Sélection de l'utilisateur
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
    min_value=1,
    max_value=20,
    value=5,
    help="Nombre d'articles à recommander"
)

# Poids du collaborative filtering
alpha = st.sidebar.slider(
    "Poids Collaborative Filtering (alpha)",
    min_value=0.0,
    max_value=1.0,
    value=0.6,
    step=0.1,
    help="0 = 100% Content-based, 1 = 100% Collaborative"
)

# Diversité
use_diversity = st.sidebar.checkbox(
    "Activer la diversité",
    value=True,
    help="Assurer une variété de catégories dans les recommandations"
)

# Section principale
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader(f"👤 Recommandations pour l'utilisateur #{user_id}")

with col2:
    if st.button("🔄 Générer des recommandations", type="primary", use_container_width=True):
        st.session_state.generate = True

# Fonction pour appeler la Lambda
def get_recommendations_from_lambda(user_id, n_recommendations, alpha, use_diversity):
    """Appelle la Lambda Function AWS"""
    try:
        params = {
            'user_id': user_id,
            'n_recommendations': n_recommendations,
            'alpha': alpha,
            'use_diversity': str(use_diversity).lower()
        }

        response = requests.get(LAMBDA_URL, params=params, timeout=30)
        response.raise_for_status()

        return response.json()

    except requests.exceptions.RequestException as e:
        st.error(f"❌ Erreur de connexion à la Lambda: {e}")
        return None
    except Exception as e:
        st.error(f"❌ Erreur: {e}")
        return None

# Fonction pour le mode local
def get_recommendations_local(user_id, n_recommendations, alpha, use_diversity):
    """Utilise le moteur local"""
    try:
        import sys
        sys.path.append('../lambda')
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
            alpha=alpha,
            use_diversity=use_diversity
        )

        return {
            'user_id': user_id,
            'n_recommendations': len(recommendations),
            'recommendations': recommendations,
            'parameters': {
                'alpha': alpha,
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
            result = get_recommendations_local(user_id, n_recommendations, alpha, use_diversity)
        else:
            result = get_recommendations_from_lambda(user_id, n_recommendations, alpha, use_diversity)

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
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("User ID", result['user_id'])
            with col2:
                st.metric("Alpha (Collaborative)", f"{result['parameters']['alpha']:.1f}")
            with col3:
                st.metric("Diversité", "✓" if result['parameters']['use_diversity'] else "✗")

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
    <p>Powered by AWS Lambda & Streamlit</p>
</div>
""", unsafe_allow_html=True)
