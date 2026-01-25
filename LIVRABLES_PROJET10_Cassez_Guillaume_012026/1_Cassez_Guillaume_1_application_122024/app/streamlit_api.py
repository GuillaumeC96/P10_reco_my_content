"""
Application Streamlit pour interagir avec l'API de recommandation My Content
Déployée sur Azure Functions
"""

import streamlit as st
import requests
import json
import pandas as pd
from datetime import datetime
import time

# Configuration de la page
st.set_page_config(
    page_title="My Content - Recommandations",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Styles CSS personnalisés
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #0078D4;
        text-align: center;
        margin-bottom: 1rem;
        font-weight: bold;
    }
    .sub-header {
        text-align: center;
        color: #666;
        margin-bottom: 2rem;
    }
    .article-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        transition: transform 0.2s;
    }
    .article-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
    }
    .score-badge {
        background-color: #FFD700;
        color: #333;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-size: 1.1rem;
        font-weight: bold;
        display: inline-block;
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #0078D4;
    }
    .stButton>button {
        background-color: #0078D4;
        color: white;
        font-weight: bold;
        border-radius: 8px;
        padding: 0.5rem 2rem;
        border: none;
    }
    .stButton>button:hover {
        background-color: #005a9e;
    }
</style>
""", unsafe_allow_html=True)

# API Configuration
API_URL = "https://func-mycontent-reco-1269.azurewebsites.net/api/recommend"

# En-tête
st.markdown('<p class="main-header">📰 My Content - Recommandations Personnalisées</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Système de recommandation hybride déployé sur Azure Functions</p>', unsafe_allow_html=True)
st.markdown("---")

# Sidebar avec les paramètres
st.sidebar.image("https://img.icons8.com/fluency/96/000000/artificial-intelligence.png", width=80)
st.sidebar.title("⚙️ Configuration")

# Sélection de l'utilisateur
st.sidebar.markdown("### 👤 Utilisateur")
user_id = st.sidebar.number_input(
    "ID de l'utilisateur",
    min_value=1,
    max_value=10000,
    value=58,
    step=1,
    help="ID de l'utilisateur pour lequel générer des recommandations"
)

# Info sur l'utilisateur de test
st.sidebar.info("💡 **User 58** est disponible dans les modèles Lite pour les tests.")

# Nombre de recommandations
st.sidebar.markdown("### 📊 Paramètres")
n_recommendations = st.sidebar.slider(
    "Nombre de recommandations",
    min_value=1,
    max_value=20,
    value=5,
    help="Nombre d'articles à recommander"
)

# Poids des 3 approches de recommandation
st.sidebar.markdown("### 🎛️ Poids des algorithmes")
st.sidebar.caption("Ajustez les poids pour chaque approche de recommandation")

# Mode simple ou avancé
advanced_mode = st.sidebar.checkbox("Mode avancé", value=False)

if advanced_mode:
    weight_content = st.sidebar.slider(
        "Content-Based (similitude)",
        min_value=0.0,
        max_value=1.0,
        value=0.4,
        step=0.05,
        help="Recommandations basées sur le contenu des articles"
    )

    weight_collab = st.sidebar.slider(
        "Collaborative Filtering (utilisateurs)",
        min_value=0.0,
        max_value=1.0,
        value=0.3,
        step=0.05,
        help="Recommandations basées sur les utilisateurs similaires"
    )

    weight_trend = st.sidebar.slider(
        "Temporal/Trending (actualité)",
        min_value=0.0,
        max_value=1.0,
        value=0.3,
        step=0.05,
        help="Recommandations basées sur la popularité et la fraîcheur"
    )

    # Normalisation
    total = weight_content + weight_collab + weight_trend
    if total > 0:
        weight_content = weight_content / total
        weight_collab = weight_collab / total
        weight_trend = weight_trend / total

    st.sidebar.caption(f"📊 Ratio: {weight_content:.0%} / {weight_collab:.0%} / {weight_trend:.0%}")
else:
    # Stratégies prédéfinies
    strategy = st.sidebar.radio(
        "Stratégie de recommandation",
        ["Équilibrée (défaut)", "Personnalisée", "Trending", "Similaires"],
        help="Choisissez une stratégie de recommandation"
    )

    if strategy == "Équilibrée (défaut)":
        weight_content, weight_collab, weight_trend = 0.39, 0.36, 0.25
        st.sidebar.caption("⚖️ 39% contenu / 36% collab / 25% trending (Optuna)")
    elif strategy == "Personnalisée":
        weight_content, weight_collab, weight_trend = 0.2, 0.6, 0.2
        st.sidebar.caption("👥 60% basé sur utilisateurs similaires")
    elif strategy == "Trending":
        weight_content, weight_collab, weight_trend = 0.2, 0.2, 0.6
        st.sidebar.caption("🔥 60% articles populaires récents")
    else:  # Similaires
        weight_content, weight_collab, weight_trend = 0.7, 0.2, 0.1
        st.sidebar.caption("📄 70% basé sur le contenu lu")

# Diversité
use_diversity = st.sidebar.checkbox(
    "Activer la diversité",
    value=True,
    help="Assurer une variété de catégories dans les recommandations"
)

st.sidebar.markdown("---")

# Info sur l'API
with st.sidebar.expander("ℹ️ Informations API"):
    st.caption(f"**Endpoint:** `{API_URL[:50]}...`")
    st.caption("**Platform:** Azure Functions")
    st.caption("**Region:** France Central")
    st.caption("**Version:** Lite (10k users)")

# Section principale
col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    st.subheader(f"👤 Recommandations pour l'utilisateur #{user_id}")

with col2:
    show_json = st.checkbox("Afficher JSON", value=False)

with col3:
    if st.button("🚀 Générer", type="primary", use_container_width=True):
        st.session_state.generate = True

# Fonction pour appeler l'API
def get_recommendations(user_id, n, weight_content, weight_collab, weight_trend, use_diversity):
    """Appelle l'API Azure Functions"""
    try:
        payload = {
            'user_id': user_id,
            'n': n,
            'weight_content': weight_content,
            'weight_collab': weight_collab,
            'weight_trend': weight_trend,
            'use_diversity': use_diversity
        }

        start_time = time.time()
        response = requests.post(API_URL, json=payload, timeout=30)
        latency = (time.time() - start_time) * 1000  # en ms

        response.raise_for_status()
        result = response.json()
        result['latency_ms'] = latency

        return result, None

    except requests.exceptions.Timeout:
        return None, "⏱️ Timeout: L'API met trop de temps à répondre (>30s)"
    except requests.exceptions.ConnectionError:
        return None, "🔌 Erreur de connexion: Impossible de joindre l'API"
    except requests.exceptions.HTTPError as e:
        return None, f"❌ Erreur HTTP {response.status_code}: {response.text}"
    except Exception as e:
        return None, f"❌ Erreur: {str(e)}"

# Générer les recommandations
if st.session_state.get('generate', False):
    with st.spinner("🔄 Génération des recommandations en cours..."):
        result, error = get_recommendations(
            user_id,
            n_recommendations,
            weight_content,
            weight_collab,
            weight_trend,
            use_diversity
        )

        if error:
            st.error(error)
        elif result:
            st.session_state.last_result = result
            st.session_state.generate = False

# Afficher les résultats
if 'last_result' in st.session_state:
    result = st.session_state.last_result

    # Vérifier si des recommandations ont été générées
    if result.get('n_recommendations', 0) > 0:
        # Bannière de succès avec métriques
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "✅ Recommandations",
                result['n_recommendations'],
                delta="Générées avec succès"
            )

        with col2:
            st.metric(
                "⚡ Latence",
                f"{result.get('latency_ms', 0):.0f} ms",
                delta="Performance"
            )

        with col3:
            st.metric(
                "🎯 Score max",
                f"{result['recommendations'][0]['score']:.3f}" if result['recommendations'] else "N/A"
            )

        with col4:
            platform = result.get('metadata', {}).get('platform', 'Unknown')
            st.metric(
                "☁️ Platform",
                "Azure" if "Azure" in platform else platform
            )

        # Afficher JSON si demandé
        if show_json:
            with st.expander("📄 Réponse JSON complète", expanded=False):
                st.json(result)

        st.markdown("---")

        # Paramètres utilisés
        with st.expander("🔧 Paramètres appliqués", expanded=False):
            params = result.get('parameters', {})
            col1, col2, col3 = st.columns(3)

            with col1:
                st.markdown(f"""
                **Content-Based:** {params.get('weight_content', 0):.1%}
                **Collaborative:** {params.get('weight_collab', 0):.1%}
                **Temporal:** {params.get('weight_trend', 0):.1%}
                """)

            with col2:
                st.markdown(f"""
                **Diversité:** {'✅ Activée' if params.get('use_diversity', False) else '❌ Désactivée'}
                **Version:** {result.get('metadata', {}).get('version', 'N/A')}
                """)

            with col3:
                st.markdown(f"""
                **Engine Status:** {'✅ Chargé' if result.get('metadata', {}).get('engine_loaded', False) else '❌ Non chargé'}
                **User ID:** {result.get('user_id', 'N/A')}
                """)

        st.markdown("---")
        st.subheader("🎯 Articles recommandés")

        # Afficher les recommandations sous forme de cartes
        recommendations = result.get('recommendations', [])

        for i, rec in enumerate(recommendations, 1):
            # Couleurs de gradient variées
            gradients = [
                "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                "linear-gradient(135deg, #f093fb 0%, #f5576c 100%)",
                "linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)",
                "linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)",
                "linear-gradient(135deg, #fa709a 0%, #fee140 100%)",
            ]
            gradient = gradients[i % len(gradients)]

            col1, col2 = st.columns([5, 1])

            with col1:
                # Calculer l'âge de l'article
                created_at = datetime.fromtimestamp(rec['created_at_ts'] / 1000)
                age_days = (datetime.now() - created_at).days

                st.markdown(f"""
                <div style="background: {gradient}; color: white; padding: 1.5rem; border-radius: 10px; margin-bottom: 1rem;">
                    <h3 style="margin: 0 0 0.5rem 0;">#{i} - Article {rec['article_id']}</h3>
                    <div style="display: flex; gap: 1rem; flex-wrap: wrap; font-size: 0.9rem;">
                        <span>📁 Catégorie: {rec['category_id']}</span>
                        <span>📰 Éditeur: {rec['publisher_id']}</span>
                        <span>📝 Mots: {rec['words_count']}</span>
                    </div>
                    <div style="margin-top: 0.5rem; font-size: 0.85rem; opacity: 0.9;">
                        📅 {created_at.strftime('%d/%m/%Y')} ({age_days} jours)
                    </div>
                </div>
                """, unsafe_allow_html=True)

            with col2:
                st.markdown(f"""
                <div style="text-align: center; padding-top: 2rem;">
                    <div style="background: #FFD700; color: #333; padding: 1rem; border-radius: 50%;
                                width: 80px; height: 80px; margin: auto; display: flex;
                                align-items: center; justify-content: center; font-weight: bold;
                                font-size: 1rem; box-shadow: 0 4px 8px rgba(0,0,0,0.2);">
                        {rec['score']:.3f}
                    </div>
                    <div style="margin-top: 0.5rem; font-size: 0.8rem; color: #666;">Score</div>
                </div>
                """, unsafe_allow_html=True)

        # Tableau récapitulatif
        st.markdown("---")
        st.subheader("📊 Vue d'ensemble")

        df = pd.DataFrame(recommendations)
        df['created_at'] = pd.to_datetime(df['created_at_ts'], unit='ms')
        df['age_days'] = (pd.Timestamp.now() - df['created_at']).dt.days

        # Colonnes à afficher
        display_df = df[['article_id', 'score', 'category_id', 'publisher_id',
                         'words_count', 'created_at', 'age_days']].copy()
        display_df.columns = ['Article ID', 'Score', 'Catégorie', 'Éditeur',
                              'Mots', 'Date', 'Âge (jours)']

        st.dataframe(
            display_df.style.background_gradient(subset=['Score'], cmap='YlGn')
                           .format({'Score': '{:.3f}', 'Date': lambda x: x.strftime('%Y-%m-%d')}),
            use_container_width=True,
            height=300
        )

        # Statistiques
        st.markdown("### 📈 Statistiques")
        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            st.metric("Articles", len(df))

        with col2:
            st.metric("Catégories", df['category_id'].nunique())

        with col3:
            st.metric("Mots moyen", f"{df['words_count'].mean():.0f}")

        with col4:
            st.metric("Score moyen", f"{df['score'].mean():.3f}")

        with col5:
            st.metric("Âge moyen", f"{df['age_days'].mean():.0f}j")

        # Graphiques
        st.markdown("---")
        tab1, tab2, tab3 = st.tabs(["📊 Scores", "📁 Catégories", "📅 Temporalité"])

        with tab1:
            st.bar_chart(df.set_index('article_id')['score'])

        with tab2:
            category_counts = df['category_id'].value_counts()
            st.bar_chart(category_counts)

        with tab3:
            st.line_chart(df.set_index('created_at')['score'])

        # Téléchargement
        st.markdown("---")
        col1, col2 = st.columns(2)

        with col1:
            csv = display_df.to_csv(index=False)
            st.download_button(
                label="📥 Télécharger CSV",
                data=csv,
                file_name=f"recommendations_user_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )

        with col2:
            json_str = json.dumps(result, indent=2, ensure_ascii=False)
            st.download_button(
                label="📥 Télécharger JSON",
                data=json_str,
                file_name=f"recommendations_user_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True
            )

    else:
        # Aucune recommandation
        st.warning(f"""
        ⚠️ **Aucune recommandation générée pour l'utilisateur #{user_id}**

        **Raisons possibles:**
        - L'utilisateur n'est pas dans les modèles Lite (10,000 users)
        - Essayez avec l'utilisateur **#58** qui est garanti disponible
        - Vérifiez que l'API fonctionne correctement
        """)

        if show_json:
            with st.expander("📄 Réponse JSON complète"):
                st.json(result)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 2rem;">
    <p style="font-size: 1.2rem; font-weight: bold; color: #0078D4;">My Content - Système de Recommandation</p>
    <p style="font-size: 0.9rem;">Version Lite MVP | Déployé sur Azure Functions</p>
    <p style="font-size: 0.8rem;">Algorithme hybride: Content-Based + Collaborative + Temporal</p>
    <p style="font-size: 0.8rem; margin-top: 1rem;">
        🔗 <a href="https://func-mycontent-reco-1269.azurewebsites.net/api/recommend" target="_blank">API Endpoint</a>
    </p>
</div>
""", unsafe_allow_html=True)

# Sidebar footer
st.sidebar.markdown("---")
st.sidebar.markdown("""
<div style="text-align: center; font-size: 0.8rem; color: #666;">
    <p>📚 <strong>Documentation</strong></p>
    <p>Voir PROJET_COMPLET.md</p>
    <p>et DEMO_SCRIPT.md</p>
</div>
""", unsafe_allow_html=True)
