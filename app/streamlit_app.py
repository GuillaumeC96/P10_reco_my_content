"""
Application Streamlit pour le système de recommandation My Content
Version Cloud - Sans graphe de réseau
Updated: 2026-01-25 - Azure API fix for temporal filter
"""

import streamlit as st
import requests
import json
import pandas as pd
import plotly.express as px
from datetime import datetime
from collections import Counter

# Configuration de la page
st.set_page_config(
    page_title="My Content - Recommandation d'articles",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configuration
AZURE_API_URL = "https://func-mycontent-reco-1269.azurewebsites.net/api/recommend"

# PARAMÈTRES OPTIMAUX (Optuna TPE - 23 Jan 2026)
OPTIMAL_WEIGHT_CONTENT = 0.39
OPTIMAL_WEIGHT_COLLAB = 0.36
OPTIMAL_WEIGHT_TREND = 0.25

# NOMS DE CATÉGORIES
CATEGORY_NAMES = {
    281: "Actualités Générales",
    375: "Divertissement & Célébrités",
    412: "Sport",
    437: "Économie & Finance",
    250: "Politique",
    399: "Culture & Arts",
    209: "Technologie",
    331: "Société & Faits Divers",
    418: "International & Monde",
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
    """Retourne le nom de la catégorie"""
    if cat_id in CATEGORY_NAMES:
        return f"{CATEGORY_NAMES[cat_id]} #{cat_id}"
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

@st.cache_data
def load_user_profiles():
    """Charge les profils utilisateurs"""
    try:
        with open('data/user_profiles.json', 'r') as f:
            return json.load(f)
    except:
        return {}

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

# ===== INTERFACE =====

# Sidebar
st.sidebar.title("📰 My Content")
st.sidebar.markdown("---")
st.sidebar.header("👤 Configuration")

# Sélection utilisateur - défaut 58
user_id = st.sidebar.number_input(
    "ID de l'utilisateur",
    min_value=1,
    max_value=1000000,
    value=58,
    step=1,
    help="Exemples: 58, 389, 408, 443"
)

# Nombre de recommandations fixé à 5
n_recommendations = 5

# Poids
weight_content = OPTIMAL_WEIGHT_CONTENT
weight_collab = OPTIMAL_WEIGHT_COLLAB
weight_trend = OPTIMAL_WEIGHT_TREND

st.sidebar.markdown("---")
st.sidebar.markdown("### ⚙️ Paramètres du Modèle")
st.sidebar.markdown(f"""
**Architecture Hybride 39/36/25:**
- Content-Based: **{weight_content*100:.0f}%**
- Collaborative: **{weight_collab*100:.0f}%**
- Temporal: **{weight_trend*100:.0f}%**

*(Optuna TPE - 23 Jan 2026)*
""")

st.sidebar.markdown("---")
use_diversity = st.sidebar.checkbox(
    "🎨 Activer le filtre de diversité",
    value=False,
    help="Force la diversité des catégories"
)

# ===== PAGE PRINCIPALE =====
st.title("🎯 Recommandations Personnalisées")

# Afficher le profil utilisateur
profile = get_user_profile(user_id)

if profile:
    st.markdown("---")
    st.subheader(f"📊 Profil de l'utilisateur #{user_id}")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📚 Articles lus", profile.get('num_articles', 0))
    with col2:
        st.metric("🔄 Interactions", profile.get('num_interactions', 0))
    with col3:
        st.metric("📝 Mots moyens", f"{profile.get('avg_words', 0):.0f}")
    with col4:
        top_cats = profile.get('top_categories', [])
        st.metric("🏷️ Catégories favorites", len(top_cats))
else:
    st.info(f"ℹ️ Nouvel utilisateur #{user_id} (pas d'historique)")

# Détecter le changement d'utilisateur
if 'last_user_id' not in st.session_state or st.session_state.last_user_id != user_id:
    st.session_state.last_user_id = user_id
    st.session_state.generate = True
    if 'last_recommendations' in st.session_state:
        del st.session_state.last_recommendations

# Bouton de génération
st.markdown("---")
if st.button("🔄 Générer des recommandations", type="primary", use_container_width=True):
    st.session_state.generate = True

# Générer les recommandations
if st.session_state.get('generate', False) or 'last_recommendations' not in st.session_state:
    with st.spinner("🔄 Génération des recommandations en cours..."):
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
            st.success(f"✅ {result['n_recommendations']} recommandations générées!")
        with col2:
            if 'latency_ms' in result:
                latency = result['latency_ms']
                if latency < 100:
                    st.metric("⚡ Latence", f"{latency:.0f} ms", delta="Excellent")
                elif latency < 500:
                    st.metric("⚡ Latence", f"{latency:.0f} ms", delta="Bon")
                else:
                    st.metric("⚡ Latence", f"{latency:.0f} ms", delta="Lent", delta_color="inverse")

        # Graphiques de comparaison
        rec_categories = [r['category_id'] for r in result['recommendations']]
        rec_cat_counter = Counter(rec_categories)

        if profile:
            st.markdown("---")
            st.subheader("📊 Comparaison Profil vs Recommandations")

            col1, col2 = st.columns(2)

            with col1:
                st.markdown("#### 🏷️ Catégories Recommandées")
                rec_cat_names = [(get_category_name(cat_id), count) for cat_id, count in rec_cat_counter.most_common()]
                rec_cat_df = pd.DataFrame(rec_cat_names, columns=['Catégorie', 'Count'])
                fig = px.pie(rec_cat_df, values='Count', names='Catégorie',
                            color_discrete_sequence=px.colors.sequential.RdBu)
                fig.update_layout(height=300)
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                st.markdown("#### 🌟 Catégories Favorites")
                top_cats = profile.get('top_categories', [])
                if top_cats:
                    fav_df = pd.DataFrame({
                        'Catégorie': [get_category_name(cat_id) for cat_id in top_cats[:5]],
                        'Rang': list(range(1, min(6, len(top_cats)+1)))
                    })
                    fig = px.pie(fav_df, values='Rang', names='Catégorie',
                                color_discrete_sequence=px.colors.sequential.Viridis)
                    fig.update_layout(height=300)
                    st.plotly_chart(fig, use_container_width=True)

            # Analyse de cohérence
            st.markdown("---")
            st.subheader("🎯 Analyse de Cohérence")

            matching_cats = set(rec_categories) & set(top_cats)
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
                    - **Longueur:** {rec['words_count']} mots (≈ {rec['words_count']//200 + 1} min)
                    - **Date:** {datetime.fromtimestamp(rec['created_at_ts']/1000).strftime('%Y-%m-%d %H:%M')}
                    """)

                    if profile and rec['category_id'] in profile.get('top_categories', []):
                        st.success("✅ Catégorie favorite!")
                    elif profile:
                        st.info("💡 Nouvelle catégorie")

                with col2:
                    st.markdown(f"""
                    <div style="text-align: center; padding: 2rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 10px; color: white;">
                        <h2 style="margin: 0;">🎯 {rec['score']:.3f}</h2>
                        <p style="margin: 0;">Score</p>
                    </div>
                    """, unsafe_allow_html=True)

        # Export CSV
        st.markdown("---")
        df = pd.DataFrame(result['recommendations'])
        df['created_at'] = pd.to_datetime(df['created_at_ts'], unit='ms')
        df['category_name'] = df['category_id'].apply(get_category_name)
        csv = df.to_csv(index=False)
        st.download_button(
            label="📥 Télécharger (CSV)",
            data=csv,
            file_name=f"recommendations_user_{user_id}.csv",
            mime="text/csv"
        )

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666;">
    <p>My Content - Système de recommandation MVP v1.0</p>
    <p>Powered by Azure Functions & Streamlit</p>
</div>
""", unsafe_allow_html=True)
