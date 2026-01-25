"""
My Content - Système de Recommandation
Version minimale pour Streamlit Cloud
"""

import streamlit as st

# Configuration de la page
st.set_page_config(
    page_title="My Content - Recommandation",
    page_icon="📰",
    layout="wide"
)

# Titre
st.title("📰 My Content - Système de Recommandation")
st.markdown("---")

# Message d'accueil
st.info("Bienvenue sur My Content ! Cette application permet de générer des recommandations d'articles personnalisées.")

# Sidebar
st.sidebar.header("👤 Configuration")
user_id = st.sidebar.number_input("ID Utilisateur", min_value=0, max_value=1000000, value=0)
n_reco = st.sidebar.slider("Nombre de recommandations", 1, 10, 5)

# Paramètres optimaux
st.sidebar.markdown("---")
st.sidebar.markdown("### Poids optimaux (Optuna)")
st.sidebar.markdown("""
- Content-Based: **39%**
- Collaborative: **36%**
- Temporal: **25%**
""")

# Bouton
col1, col2 = st.columns([3, 1])
with col1:
    st.subheader(f"Recommandations pour l'utilisateur #{user_id}")
with col2:
    generate = st.button("🔄 Générer", type="primary")

# Si bouton cliqué
if generate:
    st.spinner("Génération en cours...")

    # Appel API Azure
    import requests
    try:
        response = requests.post(
            "https://func-mycontent-reco-1269.azurewebsites.net/api/recommend",
            json={
                'user_id': int(user_id),
                'n': int(n_reco),
                'weight_collab': 0.36,
                'weight_content': 0.39,
                'weight_trend': 0.25,
                'use_diversity': True
            },
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()
            st.success(f"✅ {len(data.get('recommendations', []))} recommandations générées!")

            for i, rec in enumerate(data.get('recommendations', []), 1):
                st.write(f"**#{i}** - Article {rec.get('article_id')} (Score: {rec.get('score', 0):.3f})")
        else:
            st.error(f"Erreur API: {response.status_code}")

    except Exception as e:
        st.error(f"Erreur: {e}")

# Footer
st.markdown("---")
st.caption("My Content MVP v1.0 - Powered by Azure Functions & Streamlit")
