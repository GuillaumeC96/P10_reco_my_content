"""
Application Streamlit AMÉLIORÉE pour My Content
Version 3 avec comparaison côte à côte et profil détaillé
"""

import streamlit as st
import requests
import json
import pandas as pd
import pickle
import numpy as np
from datetime import datetime
from pathlib import Path
import plotly.express as px
import plotly.graph_objects as go
from collections import Counter

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
        color: #2c3e50;
        text-align: center;
        margin-bottom: 1rem;
        font-weight: bold;
    }
    .sub-header {
        text-align: center;
        color: #7f8c8d;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .comparison-card {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 1rem;
    }
    .article-card {
        background: linear-gradient(135deg, #5a6c7d 0%, #3d4f5d 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .stMetric {
        background-color: rgba(255, 255, 255, 0.1);
        padding: 10px;
        border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)

# Paths
MODELS_PATH = Path("/home/ser/Bureau/P10_reco_new/models_lite")
API_URL = "https://func-mycontent-reco-1269.azurewebsites.net/api/recommend"

# Mapping des catégories (version complète)
CATEGORY_NAMES = {
    1: "Politique", 2: "International", 4: "Économie", 6: "Société",
    7: "Culture", 9: "Sport", 15: "Tech", 16: "Sciences",
    17: "Santé", 25: "Environnement", 26: "Justice", 29: "Éducation",
    32: "Mode", 36: "Gastronomie", 43: "Voyage", 48: "Auto-Moto",
    51: "Immobilier", 56: "People", 60: "Médias", 62: "Histoire",
    63: "Météo", 66: "Bourse", 67: "Entreprises", 68: "Consommation",
    69: "Emploi", 71: "Agriculture", 84: "Cinéma", 92: "Musique",
    97: "Livres", 99: "Théâtre", 101: "Arts", 102: "Photographie",
    104: "Télévision", 115: "Radio", 118: "Spectacles", 120: "Festivals",
    122: "Expositions", 123: "Concerts", 125: "Danse", 126: "Opéra",
    127: "Patrimoine", 132: "Archéologie", 133: "Astronomie", 134: "Biologie",
    135: "Chimie", 136: "Physique", 137: "Mathématiques", 138: "Recherche",
    140: "Innovation", 141: "Startups", 142: "Numérique", 146: "Cybersécurité",
    147: "IA", 148: "Robotique", 152: "Espace", 156: "Climat",
    160: "Écologie", 161: "Biodiversité", 163: "Énergie", 165: "Transports",
    166: "Urbanisme", 167: "Architecture", 172: "Design", 173: "Décoration",
    174: "Jardinage", 176: "Bricolage", 184: "Beauté", 186: "Bien-être",
    187: "Nutrition", 188: "Fitness", 195: "Psychologie", 196: "Médecine",
    197: "Pharmacie", 198: "Hôpitaux", 203: "Cardiologie", 207: "Oncologie",
    209: "Pédiatrie", 211: "Psychiatrie", 213: "Dentaire", 215: "Ophtalmologie",
    216: "Dermatologie", 219: "Allergies", 221: "Vaccins", 223: "Prévention",
    225: "Urgences", 226: "Seniors", 228: "Famille", 230: "Enfants",
    231: "Adolescents", 237: "Couples", 242: "Divorce", 247: "Adoption",
    249: "Grossesse", 250: "Naissance", 252: "Parentalité", 254: "Loisirs",
    255: "Jeux", 260: "Hobbies", 265: "Collections", 269: "Animaux",
    270: "Chiens", 271: "Chats", 276: "Équitation", 278: "Aquariophilie",
    281: "Football", 285: "Basketball", 288: "Tennis", 289: "Rugby",
    290: "Handball", 295: "Volleyball", 297: "Natation", 299: "Athlétisme",
    300: "Cyclisme", 301: "Formule 1", 302: "MotoGP", 304: "Rallye",
    305: "Sports mécaniques", 309: "Golf", 311: "Ski", 316: "Snowboard",
    317: "Surf", 320: "Voile", 323: "Aviron", 325: "Escalade",
    327: "Randonnée", 328: "Trail", 329: "Marathon", 331: "Fitness",
    332: "Musculation", 339: "Yoga", 340: "Pilates", 348: "Arts martiaux",
    351: "Boxe", 352: "Judo", 353: "Karaté", 354: "Taekwondo",
    355: "Escrime", 357: "Tir", 360: "Équitation sportive", 369: "Hippisme",
    371: "Courses", 374: "Paris sportifs", 375: "E-sports", 376: "Gaming",
    380: "Jeux vidéo", 382: "Consoles", 384: "PC Gaming", 385: "Mobile Gaming",
    388: "Streaming", 389: "YouTube", 390: "Twitch", 391: "TikTok",
    392: "Instagram", 393: "Facebook", 395: "Twitter", 396: "LinkedIn",
    398: "Snapchat", 399: "Réseaux sociaux", 402: "Influenceurs", 403: "Blogueurs",
    404: "Podcasts", 406: "Webinaires", 408: "MOOCs", 409: "Formations",
    410: "Certifications", 412: "Universités", 413: "Écoles", 418: "Collèges",
    420: "Lycées", 421: "Maternelle", 428: "Orientation", 429: "Examens",
    430: "Bac", 431: "Concours", 433: "Apprentissage", 434: "Alternance",
    435: "Stages", 436: "Premier emploi", 437: "Carrière", 438: "Management",
    442: "Entrepreneuriat", 443: "PME", 448: "Grande distribution", 450: "Commerce",
    454: "Marketing", 455: "Publicité", 458: "Communication", 460: "Relations publiques"
}

def get_category_name(cat_id):
    """Retourne le nom d'une catégorie"""
    return CATEGORY_NAMES.get(cat_id, f"Catégorie {cat_id}")

@st.cache_data
def load_user_profiles():
    """Charge les profils utilisateurs"""
    try:
        profile_path = MODELS_PATH / "user_profiles_enriched.pkl"
        if profile_path.exists():
            with open(profile_path, 'rb') as f:
                return pickle.load(f)
    except Exception as e:
        st.error(f"Erreur chargement profils: {e}")
    return {}

@st.cache_data
def load_articles_metadata():
    """Charge les métadonnées des articles"""
    try:
        metadata_path = MODELS_PATH / "articles_metadata.csv"
        if metadata_path.exists():
            return pd.read_csv(metadata_path)
    except Exception as e:
        st.error(f"Erreur chargement métadonnées: {e}")
    return pd.DataFrame()

def get_user_category_distribution(profile, articles_metadata):
    """Analyse la distribution des catégories pour un utilisateur"""
    # Récupérer la liste des articles lus
    articles_read = profile.get('articles_read', [])

    # Matcher avec les métadonnées pour obtenir les catégories
    articles_with_cat = articles_metadata[articles_metadata['article_id'].isin(articles_read)]

    # Compter les lectures par catégorie
    category_counts = Counter(articles_with_cat['category_id'].tolist())

    # Pondérer par engagement (nombre de clics et temps)
    article_stats = profile.get('article_stats', {})
    category_weights = {}

    for _, row in articles_with_cat.iterrows():
        article_id = row['article_id']
        cat_id = row['category_id']

        if article_id in article_stats:
            stats = article_stats[article_id]
            weight = stats.get('num_clicks', 1) * stats.get('total_time_seconds', 1)
            category_weights[cat_id] = category_weights.get(cat_id, 0) + weight

    return category_counts, category_weights

def format_time(seconds):
    """Formate un temps en secondes"""
    if seconds < 60:
        return f"{int(seconds)}s"
    elif seconds < 3600:
        return f"{int(seconds/60)}min {int(seconds%60)}s"
    else:
        hours = int(seconds / 3600)
        mins = int((seconds % 3600) / 60)
        return f"{hours}h {mins}min"

# Charger les données
user_profiles = load_user_profiles()
articles_metadata = load_articles_metadata()

# Obtenir la liste des utilisateurs disponibles
available_users = sorted(list(user_profiles.keys()))

# En-tête
st.markdown('<p class="main-header">📰 My Content - Système de Recommandation</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Analyse comparative : Habitudes VS Recommandations</p>', unsafe_allow_html=True)
st.markdown("---")

# Sidebar
st.sidebar.title("⚙️ Configuration")

# Info sur les utilisateurs disponibles
st.sidebar.info(f"📊 **{len(available_users):,} utilisateurs** disponibles dans les modèles Lite")

# Sélection utilisateur depuis une liste
st.sidebar.markdown("### 👤 Sélection Utilisateur")

# Proposer quelques utilisateurs recommandés
st.sidebar.markdown("**Utilisateurs recommandés :**")
recommended_users = available_users[:10]  # Les 10 premiers
selected_user_id = st.sidebar.selectbox(
    "Choisir un utilisateur",
    options=available_users,
    format_func=lambda x: f"User #{x}",
    index=0
)

# Ou recherche par ID
st.sidebar.markdown("**Ou rechercher par ID :**")
search_user_id = st.sidebar.number_input(
    "ID utilisateur",
    min_value=int(available_users[0]),
    max_value=int(available_users[-1]),
    value=int(selected_user_id),
    step=1
)

# Utiliser l'ID recherché s'il existe
if search_user_id in user_profiles:
    user_id = search_user_id
else:
    user_id = selected_user_id
    st.sidebar.warning(f"⚠️ User #{search_user_id} non disponible. Utilisation de #{user_id}")

# Configuration des recommandations
st.sidebar.markdown("---")
st.sidebar.markdown("### 🎯 Paramètres de Recommandation")

n_recommendations = st.sidebar.slider("Nombre de recommandations", 5, 20, 10)

# Stratégies prédéfinies
strategy = st.sidebar.selectbox(
    "Stratégie",
    ["Optimale (39/36/25)", "Personnalisée (50/30/20)", "Découverte (30/20/50)", "Collaborative (20/60/20)", "Personnalisé"]
)

if strategy == "Personnalisé":
    weight_content = st.sidebar.slider("Content-Based", 0.0, 1.0, 0.4, 0.05)
    weight_collab = st.sidebar.slider("Collaborative", 0.0, 1.0, 0.3, 0.05)
    weight_trend = st.sidebar.slider("Temporal/Trending", 0.0, 1.0, 0.3, 0.05)
else:
    weights_map = {
        "Optimale (39/36/25)": (0.39, 0.36, 0.25),
        "Personnalisée (50/30/20)": (0.5, 0.3, 0.2),
        "Découverte (30/20/50)": (0.3, 0.2, 0.5),
        "Collaborative (20/60/20)": (0.2, 0.6, 0.2)
    }
    weight_content, weight_collab, weight_trend = weights_map[strategy]

use_diversity = st.sidebar.checkbox("Activer la diversité", value=True)

# Afficher le profil utilisateur
if user_id in user_profiles:
    profile = user_profiles[user_id]

    # Section profil utilisateur détaillé
    st.markdown("## 👤 Profil Utilisateur Détaillé")

    # Métriques principales
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        num_articles = profile.get('num_articles', 0)
        st.metric("📰 Articles Lus", num_articles)

    with col2:
        total_clicks = sum(stats.get('num_clicks', 0) for stats in profile.get('article_stats', {}).values())
        st.metric("👆 Clics Totaux", total_clicks)

    with col3:
        total_time = profile.get('total_time_seconds', 0)
        st.metric("⏱️ Temps Total", format_time(total_time))

    with col4:
        avg_engagement = profile.get('avg_weight', 0)
        st.metric("💯 Engagement Moyen", f"{avg_engagement:.2f}")

    st.markdown("---")

    # SECTION COMPARATIVE : CÔTE À CÔTE
    st.markdown("## 📊 Comparaison : Habitudes VS Recommandations")

    # Bouton pour générer les recommandations
    if st.button("🎯 Générer les Recommandations", type="primary", use_container_width=True):
        with st.spinner("Génération des recommandations..."):
            try:
                # Appel API
                payload = {
                    "user_id": int(user_id),
                    "n": n_recommendations,
                    "weight_content": float(weight_content),
                    "weight_collab": float(weight_collab),
                    "weight_trend": float(weight_trend),
                    "use_diversity": use_diversity
                }

                response = requests.post(API_URL, json=payload, timeout=30)

                if response.status_code == 200:
                    result = response.json()
                    recommendations = result.get('recommendations', [])

                    # Analyser les habitudes utilisateur
                    category_counts, category_weights = get_user_category_distribution(profile, articles_metadata)

                    # Top catégories de l'utilisateur
                    top_user_categories = category_counts.most_common(10)

                    # Analyser les catégories recommandées
                    reco_categories = Counter()
                    for rec in recommendations:
                        cat_id = rec.get('category_id')
                        if cat_id:
                            reco_categories[cat_id] += 1

                    top_reco_categories = reco_categories.most_common(10)

                    # AFFICHAGE CÔTE À CÔTE
                    col_left, col_right = st.columns(2)

                    # COLONNE GAUCHE : HABITUDES UTILISATEUR
                    with col_left:
                        st.markdown("### 📚 Habitudes de Lecture")
                        st.markdown(f"**Basé sur {num_articles} articles lus**")

                        # Top 5 catégories préférées
                        if top_user_categories:
                            st.markdown("#### 🏆 Top Catégories Préférées")

                            for i, (cat_id, count) in enumerate(top_user_categories[:5], 1):
                                cat_name = get_category_name(cat_id)
                                pct = (count / num_articles) * 100
                                st.markdown(f"**{i}. {cat_name}**")
                                st.progress(pct / 100)
                                st.caption(f"{count} articles ({pct:.1f}%)")

                        # Statistiques détaillées
                        st.markdown("#### 📈 Statistiques Détaillées")

                        avg_clicks = total_clicks / num_articles if num_articles > 0 else 0
                        avg_time = total_time / num_articles if num_articles > 0 else 0

                        st.write(f"• **Clics moyens par article :** {avg_clicks:.1f}")
                        st.write(f"• **Temps moyen par article :** {format_time(avg_time)}")
                        st.write(f"• **Catégories différentes :** {len(category_counts)}")

                        # Graphique de distribution
                        if top_user_categories:
                            cat_labels = [get_category_name(cat_id) for cat_id, _ in top_user_categories[:8]]
                            cat_values = [count for _, count in top_user_categories[:8]]

                            fig_user = go.Figure(data=[
                                go.Bar(
                                    x=cat_values,
                                    y=cat_labels,
                                    orientation='h',
                                    marker=dict(color='rgb(102, 126, 234)')
                                )
                            ])
                            fig_user.update_layout(
                                title="Distribution des Lectures",
                                xaxis_title="Nombre d'articles",
                                yaxis_title="",
                                height=400,
                                margin=dict(l=150)
                            )
                            st.plotly_chart(fig_user, use_container_width=True)

                    # COLONNE DROITE : RECOMMANDATIONS
                    with col_right:
                        st.markdown("### 🎯 Recommandations Générées")
                        st.markdown(f"**{len(recommendations)} articles recommandés**")

                        # Top catégories recommandées
                        if top_reco_categories:
                            st.markdown("#### 🌟 Catégories Recommandées")

                            for i, (cat_id, count) in enumerate(top_reco_categories[:5], 1):
                                cat_name = get_category_name(cat_id)
                                pct = (count / len(recommendations)) * 100
                                st.markdown(f"**{i}. {cat_name}**")
                                st.progress(pct / 100)
                                st.caption(f"{count} articles ({pct:.1f}%)")

                        # Analyse de similarité
                        st.markdown("#### 🔍 Analyse de Pertinence")

                        # Catégories en commun
                        user_cats = set(category_counts.keys())
                        reco_cats = set(reco_categories.keys())
                        common_cats = user_cats & reco_cats

                        similarity = len(common_cats) / len(user_cats) * 100 if user_cats else 0

                        st.write(f"• **Similarité thématique :** {similarity:.1f}%")
                        st.write(f"• **Catégories en commun :** {len(common_cats)}/{len(user_cats)}")
                        st.write(f"• **Nouvelles catégories :** {len(reco_cats - user_cats)}")

                        # Graphique des recommandations
                        if top_reco_categories:
                            reco_labels = [get_category_name(cat_id) for cat_id, _ in top_reco_categories[:8]]
                            reco_values = [count for _, count in top_reco_categories[:8]]

                            fig_reco = go.Figure(data=[
                                go.Bar(
                                    x=reco_values,
                                    y=reco_labels,
                                    orientation='h',
                                    marker=dict(color='rgb(245, 87, 108)')
                                )
                            ])
                            fig_reco.update_layout(
                                title="Distribution des Recommandations",
                                xaxis_title="Nombre d'articles",
                                yaxis_title="",
                                height=400,
                                margin=dict(l=150)
                            )
                            st.plotly_chart(fig_reco, use_container_width=True)

                    st.markdown("---")

                    # Liste détaillée des recommandations
                    st.markdown("## 📋 Liste des Recommandations")

                    for i, rec in enumerate(recommendations, 1):
                        with st.expander(f"#{i} - Article {rec['article_id']} - Score: {rec['score']:.3f} ⭐", expanded=(i<=3)):
                            col1, col2, col3 = st.columns(3)

                            with col1:
                                st.write(f"**Catégorie :** {get_category_name(rec.get('category_id'))}")
                                st.write(f"**Score :** {rec['score']:.3f}")

                            with col2:
                                st.write(f"**Mots :** {rec.get('words_count', 'N/A')}")
                                created_ts = rec.get('created_at_ts')
                                if created_ts:
                                    date = datetime.fromtimestamp(created_ts / 1000).strftime('%d/%m/%Y')
                                    st.write(f"**Date :** {date}")

                            with col3:
                                # Vérifier si l'utilisateur a déjà lu cette catégorie
                                cat_id = rec.get('category_id')
                                if cat_id in category_counts:
                                    st.success(f"✅ Catégorie familière ({category_counts[cat_id]} lus)")
                                else:
                                    st.info("🆕 Nouvelle catégorie")

                    # Export
                    st.markdown("---")
                    st.markdown("### 💾 Exporter les Résultats")

                    col1, col2 = st.columns(2)
                    with col1:
                        df_reco = pd.DataFrame(recommendations)
                        csv = df_reco.to_csv(index=False)
                        st.download_button(
                            "📥 Télécharger CSV",
                            csv,
                            f"recommendations_user_{user_id}.csv",
                            "text/csv"
                        )

                    with col2:
                        json_str = json.dumps(result, indent=2, ensure_ascii=False)
                        st.download_button(
                            "📥 Télécharger JSON",
                            json_str,
                            f"recommendations_user_{user_id}.json",
                            "application/json"
                        )

                else:
                    st.error(f"❌ Erreur API : {response.status_code}")
                    st.code(response.text)

            except Exception as e:
                st.error(f"❌ Erreur : {str(e)}")

else:
    st.error(f"❌ Utilisateur #{user_id} introuvable dans les modèles")
    st.info(f"Utilisateurs disponibles : {available_users[:20]}...")
