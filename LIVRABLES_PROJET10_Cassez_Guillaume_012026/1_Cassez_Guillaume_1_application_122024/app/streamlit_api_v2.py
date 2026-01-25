"""
Application Streamlit pour interagir avec l'API de recommandation My Content
Version 2 avec interprétabilité améliorée
"""

import streamlit as st
import requests
import json
import pandas as pd
import pickle
from datetime import datetime
from pathlib import Path
import time
import plotly.express as px
import plotly.graph_objects as go

# Configuration de la page
st.set_page_config(
    page_title="My Content - Recommandations",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Styles CSS personnalisés - Palette sobre et professionnelle
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
    .article-card {
        background: linear-gradient(135deg, #5a6c7d 0%, #3d4f5d 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .profile-card {
        background: linear-gradient(135deg, #6c7a89 0%, #576574 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 1rem;
    }
    .score-badge {
        background-color: #3498db;
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-size: 1.1rem;
        font-weight: bold;
        display: inline-block;
    }
</style>
""", unsafe_allow_html=True)

# API Configuration
API_URL = "https://func-mycontent-reco-1269.azurewebsites.net/api/recommend"
MODELS_PATH = Path("/home/ser/Bureau/P10_reco/models_lite")

# Mapping étendu des catégories (basé sur portail d'actualités)
CATEGORY_NAMES = {
    # Catégories principales (1-99)
    1: "Politique", 2: "International", 4: "Économie", 6: "Société",
    7: "Culture", 9: "Sport", 15: "Tech", 16: "Sciences",
    17: "Santé", 25: "Environnement", 26: "Justice", 29: "Éducation",
    32: "Mode", 36: "Gastronomie", 43: "Voyage", 48: "Auto-Moto",
    51: "Immobilier", 56: "People", 60: "Médias", 62: "Histoire",
    63: "Météo", 66: "Bourse", 67: "Entreprises", 68: "Consommation",
    69: "Emploi", 71: "Agriculture", 84: "Cinéma", 92: "Musique",
    97: "Livres", 99: "Théâtre",

    # Catégories 100-200
    101: "Arts", 102: "Photographie", 104: "Télévision", 115: "Radio",
    118: "Spectacles", 120: "Festivals", 122: "Expositions", 123: "Concerts",
    125: "Danse", 126: "Opéra", 127: "Patrimoine", 132: "Archéologie",
    133: "Astronomie", 134: "Biologie", 135: "Chimie", 136: "Physique",
    137: "Mathématiques", 138: "Recherche", 140: "Innovation", 141: "Startups",
    142: "Numérique", 146: "Cybersécurité", 147: "IA", 148: "Robotique",
    152: "Espace", 156: "Climat", 160: "Écologie", 161: "Biodiversité",
    163: "Énergie", 165: "Transports", 166: "Urbanisme", 167: "Architecture",
    172: "Design", 173: "Décoration", 174: "Jardinage", 176: "Bricolage",
    184: "Beauté", 186: "Bien-être", 187: "Nutrition", 188: "Fitness",
    195: "Psychologie", 196: "Médecine", 197: "Pharmacie", 198: "Hôpitaux",

    # Catégories 200-300
    203: "Cardiologie", 207: "Oncologie", 209: "Pédiatrie", 211: "Psychiatrie",
    213: "Dentaire", 215: "Ophtalmologie", 216: "Dermatologie", 219: "Allergies",
    221: "Vaccins", 223: "Prévention", 225: "Urgences", 226: "Seniors",
    228: "Famille", 230: "Enfants", 231: "Adolescents", 237: "Couples",
    242: "Divorce", 247: "Adoption", 249: "Grossesse", 250: "Naissance",
    252: "Parentalité", 254: "Loisirs", 255: "Jeux", 260: "Hobbies",
    265: "Collections", 269: "Animaux", 270: "Chiens", 271: "Chats",
    276: "Équitation", 278: "Aquariophilie", 281: "Football", 285: "Basketball",
    288: "Tennis", 289: "Rugby", 290: "Handball", 295: "Volleyball",
    297: "Natation", 299: "Athlétisme",

    # Catégories 300-400
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
    398: "Snapchat", 399: "Réseaux sociaux",

    # Catégories 400-460
    402: "Influenceurs", 403: "Blogueurs", 404: "Podcasts", 406: "Webinaires",
    408: "MOOCs", 409: "Formations", 410: "Certifications", 412: "Universités",
    413: "Écoles", 418: "Collèges", 420: "Lycées", 421: "Maternelle",
    428: "Orientation", 429: "Examens", 430: "Bac", 431: "Concours",
    433: "Apprentissage", 434: "Alternance", 435: "Stages", 436: "Premier emploi",
    437: "Carrière", 438: "Management", 442: "Entrepreneuriat", 443: "PME",
    448: "Grande distribution", 450: "Commerce", 454: "Marketing", 455: "Publicité",
    458: "Communication", 460: "Relations publiques"
}

def get_category_name(cat_id):
    """Retourne le nom d'une catégorie"""
    if cat_id in CATEGORY_NAMES:
        return CATEGORY_NAMES[cat_id]
    # Catégorie générique pour les IDs non mappés
    return f"Catégorie {cat_id}"

@st.cache_data
def load_user_profiles():
    """Charge les profils utilisateurs depuis le fichier pickle"""
    try:
        profile_path = MODELS_PATH / "user_profiles_enriched.pkl"
        if profile_path.exists():
            with open(profile_path, 'rb') as f:
                return pickle.load(f)
    except Exception as e:
        st.warning(f"Impossible de charger les profils: {e}")
    return {}

@st.cache_data
def load_articles_metadata():
    """Charge les métadonnées des articles"""
    try:
        metadata_path = MODELS_PATH / "articles_metadata.csv"
        if metadata_path.exists():
            return pd.read_csv(metadata_path)
    except Exception as e:
        st.warning(f"Impossible de charger les métadonnées: {e}")
    return pd.DataFrame()

# Charger les données
user_profiles = load_user_profiles()
articles_metadata = load_articles_metadata()

# En-tête
st.markdown('<p class="main-header">📰 My Content - Recommandations Intelligentes</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Système hybride avec interprétabilité complète</p>', unsafe_allow_html=True)
st.markdown("---")

# Sidebar
st.sidebar.image("https://img.icons8.com/fluency/96/000000/artificial-intelligence.png", width=80)
st.sidebar.title("⚙️ Configuration")

# Sélection utilisateur
st.sidebar.markdown("### 👤 Utilisateur")
user_id = st.sidebar.number_input(
    "ID de l'utilisateur",
    min_value=1,
    max_value=10000,
    value=58,
    step=1
)

# Afficher le profil utilisateur si disponible
if user_id in user_profiles:
    profile = user_profiles[user_id]
    st.sidebar.success(f"✅ Profil trouvé")

    with st.sidebar.expander("👤 Profil utilisateur", expanded=True):
        st.metric("Articles lus", profile.get('num_articles', 0))

        # Calculer le total de clicks à partir des article_stats
        total_clicks = sum(
            stats.get('num_clicks', 0)
            for stats in profile.get('article_stats', {}).values()
        )
        st.metric("Clicks totaux", total_clicks)

        # Temps de lecture
        total_time = profile.get('total_time_seconds', 0)
        if total_time > 0:
            hours = int(total_time // 3600)
            minutes = int((total_time % 3600) // 60)
            st.metric("Temps total", f"{hours}h {minutes}min")
else:
    st.sidebar.warning("⚠️ Utilisateur non trouvé dans les modèles Lite")

# Paramètres
st.sidebar.markdown("### 📊 Paramètres")
n_recommendations = st.sidebar.slider("Nombre de recommandations", 1, 20, 5)

# Mode simple ou avancé
advanced_mode = st.sidebar.checkbox("Mode avancé", value=False)

if advanced_mode:
    weight_content = st.sidebar.slider("Content-Based", 0.0, 1.0, 0.4, 0.05)
    weight_collab = st.sidebar.slider("Collaborative", 0.0, 1.0, 0.3, 0.05)
    weight_trend = st.sidebar.slider("Temporal/Trending", 0.0, 1.0, 0.3, 0.05)

    total = weight_content + weight_collab + weight_trend
    if total > 0:
        weight_content = weight_content / total
        weight_collab = weight_collab / total
        weight_trend = weight_trend / total

    st.sidebar.caption(f"📊 {weight_content:.0%} / {weight_collab:.0%} / {weight_trend:.0%}")
else:
    strategy = st.sidebar.radio(
        "Stratégie",
        ["Équilibrée", "Personnalisée", "Trending", "Similaires"]
    )

    strategies = {
        "Équilibrée": (0.4, 0.3, 0.3),
        "Personnalisée": (0.2, 0.6, 0.2),
        "Trending": (0.2, 0.2, 0.6),
        "Similaires": (0.7, 0.2, 0.1)
    }
    weight_content, weight_collab, weight_trend = strategies[strategy]

use_diversity = st.sidebar.checkbox("Diversité", value=True)

st.sidebar.markdown("---")

# Section principale
col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    st.subheader(f"👤 Recommandations pour l'utilisateur #{user_id}")

with col2:
    show_json = st.checkbox("Voir JSON", value=False)

with col3:
    if st.button("🚀 Générer", type="primary", use_container_width=True):
        st.session_state.generate = True

def get_recommendations(user_id, n, weight_content, weight_collab, weight_trend, use_diversity):
    """Appelle l'API"""
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
        latency = (time.time() - start_time) * 1000

        response.raise_for_status()
        result = response.json()
        result['latency_ms'] = latency

        return result, None

    except Exception as e:
        return None, f"❌ Erreur: {str(e)}"

# Générer les recommandations
if st.session_state.get('generate', False):
    with st.spinner("🔄 Génération en cours..."):
        result, error = get_recommendations(
            user_id, n_recommendations,
            weight_content, weight_collab, weight_trend, use_diversity
        )

        if error:
            st.error(error)
        elif result:
            st.session_state.last_result = result
            st.session_state.generate = False

# Afficher les résultats
if 'last_result' in st.session_state:
    result = st.session_state.last_result

    if result.get('n_recommendations', 0) > 0:
        # Métriques de performance
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("✅ Recommandations", result['n_recommendations'])
        with col2:
            st.metric("⚡ Latence", f"{result.get('latency_ms', 0):.0f} ms")
        with col3:
            st.metric("🎯 Score max", f"{result['recommendations'][0]['score']:.3f}")
        with col4:
            st.metric("☁️ Platform", "Azure")

        if show_json:
            with st.expander("📄 JSON complet", expanded=False):
                st.json(result)

        st.markdown("---")

        # ===== SECTION INTERPRÉTABILITÉ =====

        # Profil utilisateur enrichi
        if user_id in user_profiles:
            st.subheader("👤 Profil de l'utilisateur")

            profile = user_profiles[user_id]

            col1, col2, col3 = st.columns(3)

            with col1:
                # Calculer le total de clicks depuis article_stats
                total_clicks = sum(
                    stats.get('num_clicks', 0)
                    for stats in profile.get('article_stats', {}).values()
                )
                total_time_min = profile.get('total_time_seconds', 0) / 60

                st.markdown(f"""
                <div class="profile-card">
                    <h3>📚 Activité</h3>
                    <p><strong>{profile.get('num_articles', 0)}</strong> articles lus</p>
                    <p><strong>{total_clicks}</strong> clicks</p>
                    <p><strong>{total_time_min:.0f}</strong> minutes de lecture</p>
                </div>
                """, unsafe_allow_html=True)

            with col2:
                # Catégories préférées
                articles_read = profile.get('articles_read', [])
                if articles_read and not articles_metadata.empty:
                    user_articles = articles_metadata[articles_metadata['article_id'].isin(articles_read)]
                    cat_counts = user_articles['category_id'].value_counts().head(5)

                    st.markdown(f"""
                    <div class="profile-card">
                        <h3>❤️ Catégories préférées</h3>
                    """, unsafe_allow_html=True)

                    for cat_id, count in cat_counts.items():
                        cat_name = get_category_name(cat_id)
                        pct = (count / len(articles_read)) * 100
                        st.markdown(f"<p><strong>{cat_name}</strong>: {count} articles ({pct:.0f}%)</p>",
                                  unsafe_allow_html=True)

                    st.markdown("</div>", unsafe_allow_html=True)

            with col3:
                # Qualité moyenne de lecture
                avg_quality = profile.get('avg_weight', 0)
                st.markdown(f"""
                <div class="profile-card">
                    <h3>⭐ Qualité de lecture</h3>
                    <p><strong>{avg_quality:.3f}</strong> score moyen</p>
                    <p>Basé sur 9 signaux:</p>
                    <ul style="font-size: 0.85rem;">
                        <li>Temps de lecture</li>
                        <li>Engagement (clicks)</li>
                        <li>Qualité session</li>
                        <li>Device & environnement</li>
                    </ul>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("---")

        # Analyse des recommandations
        st.subheader("🔍 Analyse des recommandations")

        recommendations = result.get('recommendations', [])

        # Enrichir avec les noms de catégories
        for rec in recommendations:
            rec['category_name'] = get_category_name(rec['category_id'])

        # Comparaison catégories lues vs recommandées
        if user_id in user_profiles:
            col1, col2 = st.columns(2)

            profile = user_profiles[user_id]
            articles_read = profile.get('articles_read', [])

            with col1:
                st.markdown("**📖 Catégories que vous lisez**")

                if articles_read and not articles_metadata.empty:
                    user_articles = articles_metadata[articles_metadata['article_id'].isin(articles_read)]
                    cat_read = user_articles['category_id'].value_counts().head(10)

                    df_read = pd.DataFrame({
                        'Catégorie': [get_category_name(c) for c in cat_read.index],
                        'Nombre': cat_read.values
                    })

                    fig = px.bar(df_read, x='Nombre', y='Catégorie', orientation='h',
                               color='Nombre', color_continuous_scale='Blues')
                    fig.update_layout(height=300, showlegend=False)
                    st.plotly_chart(fig, use_container_width=True)

            with col2:
                st.markdown("**🎯 Catégories recommandées**")

                cat_reco = pd.Series([r['category_id'] for r in recommendations]).value_counts()

                df_reco = pd.DataFrame({
                    'Catégorie': [get_category_name(c) for c in cat_reco.index],
                    'Nombre': cat_reco.values
                })

                fig = px.bar(df_reco, x='Nombre', y='Catégorie', orientation='h',
                           color='Nombre', color_continuous_scale='Teal')
                fig.update_layout(height=300, showlegend=False)
                st.plotly_chart(fig, use_container_width=True)

        st.markdown("---")

        # Articles recommandés
        st.subheader("🎯 Articles recommandés")

        gradients = [
            "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
            "linear-gradient(135deg, #f093fb 0%, #f5576c 100%)",
            "linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)",
            "linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)",
            "linear-gradient(135deg, #fa709a 0%, #fee140 100%)",
        ]

        for i, rec in enumerate(recommendations, 1):
            gradient = gradients[i % len(gradients)]

            col1, col2 = st.columns([5, 1])

            with col1:
                created_at = datetime.fromtimestamp(rec['created_at_ts'] / 1000)
                age_days = (datetime.now() - created_at).days

                st.markdown(f"""
                <div style="background: {gradient}; color: white; padding: 1.5rem; border-radius: 10px; margin-bottom: 1rem;">
                    <h3 style="margin: 0 0 0.5rem 0;">#{i} - Article {rec['article_id']}</h3>
                    <div style="display: flex; gap: 1rem; flex-wrap: wrap; font-size: 0.95rem;">
                        <span>📁 <strong>{rec['category_name']}</strong> (ID: {rec['category_id']})</span>
                        <span>📰 Éditeur: {rec['publisher_id']}</span>
                        <span>📝 {rec['words_count']} mots</span>
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

        display_df = df[['article_id', 'category_name', 'score', 'publisher_id',
                         'words_count', 'created_at', 'age_days']].copy()
        display_df.columns = ['Article ID', 'Catégorie', 'Score', 'Éditeur',
                              'Mots', 'Date', 'Âge (j)']

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
            st.metric("Catégories", df['category_name'].nunique())
        with col3:
            st.metric("Mots moyen", f"{df['words_count'].mean():.0f}")
        with col4:
            st.metric("Score moyen", f"{df['score'].mean():.3f}")
        with col5:
            st.metric("Âge moyen", f"{df['age_days'].mean():.0f}j")

        # Graphiques
        st.markdown("---")
        tab1, tab2, tab3, tab4 = st.tabs(["📊 Scores", "📁 Catégories", "📅 Temporalité", "🔍 Diversité"])

        with tab1:
            fig = px.bar(df, x='article_id', y='score',
                        title="Scores de recommandation par article",
                        labels={'article_id': 'Article ID', 'score': 'Score'},
                        color='score', color_continuous_scale='Blugrn')
            st.plotly_chart(fig, use_container_width=True)

        with tab2:
            category_counts = df['category_name'].value_counts()
            fig = px.pie(values=category_counts.values, names=category_counts.index,
                        title="Distribution des catégories recommandées",
                        color_discrete_sequence=px.colors.sequential.Greys)
            st.plotly_chart(fig, use_container_width=True)

        with tab3:
            fig = px.scatter(df, x='created_at', y='score', size='words_count',
                           hover_data=['category_name'],
                           title="Score vs Date de publication",
                           labels={'created_at': 'Date', 'score': 'Score'},
                           color='score', color_continuous_scale='ice')
            st.plotly_chart(fig, use_container_width=True)

        with tab4:
            # Analyse de la diversité
            st.markdown("**Diversité des recommandations**")
            col1, col2 = st.columns(2)

            with col1:
                st.metric("Catégories uniques", df['category_name'].nunique())
                st.metric("Éditeurs uniques", df['publisher_id'].nunique())

            with col2:
                # Coefficient de diversité (1 = tous différents, 0 = tous identiques)
                diversity_score = df['category_name'].nunique() / len(df)
                st.metric("Diversité catégorielle", f"{diversity_score:.1%}")

                # Spread temporel
                temporal_spread = df['age_days'].std()
                st.metric("Spread temporel (écart-type)", f"{temporal_spread:.0f} jours")

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
        st.warning(f"""
        ⚠️ **Aucune recommandation pour l'utilisateur #{user_id}**

        **Raisons possibles:**
        - L'utilisateur n'est pas dans les modèles Lite (10,000 users)
        - Essayez avec l'utilisateur **#58**
        """)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 2rem;">
    <p style="font-size: 1.2rem; font-weight: bold; color: #0078D4;">My Content - Système de Recommandation Intelligent</p>
    <p style="font-size: 0.9rem;">Version 2.0 avec interprétabilité complète</p>
    <p style="font-size: 0.8rem;">Algorithme hybride: 39% Content + 36% Collaborative + 25% Temporal (Optuna TPE)</p>
    <p style="font-size: 0.8rem;">9 signaux de qualité · Filtre 30 secondes · Diversification MMR</p>
</div>
""", unsafe_allow_html=True)
