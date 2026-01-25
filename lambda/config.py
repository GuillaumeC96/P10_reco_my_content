"""
Configuration pour la Lambda Function
"""

import os

# Configuration S3
S3_BUCKET = os.environ.get('S3_BUCKET', 'my-content-reco-bucket')
S3_MODELS_PREFIX = os.environ.get('S3_MODELS_PREFIX', 'models/')

# Configuration du moteur de recommandation
DEFAULT_N_RECOMMENDATIONS = 5

# POIDS OPTIMISÉS PAR OPTUNA (23 Jan 2026)
# Fonction objectif: Maximiser le temps de lecture (sans temps fantômes < 30s)
# Méthode: Optuna TPE, 30 trials, échantillon stratifié 60 utilisateurs
# Trial 22 (meilleur): 1385.8 secondes de temps de lecture moyen
#
# Références:
# - "A Survey of Personalized News Recommendation" (2023)
# - "Accurate News Recommendation Coalescing Personal and Global Temporal Preferences" (2020)
# - "Beyond-accuracy: a review on diversity, serendipity, and fairness" (2023)
#
# Architecture hybride optimisée: 39% Content + 36% Collaborative + 25% Temporal
DEFAULT_WEIGHT_CONTENT = 0.39   # 39% Content-Based (similarité embeddings)
DEFAULT_WEIGHT_COLLAB = 0.36    # 36% Collaborative (utilisateurs similaires)
DEFAULT_WEIGHT_TREND = 0.25     # 25% Temporal/Popularity (fraîcheur articles)

# Poids Niveau 1 optimaux (interaction_weights normalisés) - Trial 17
# Top 3: Time (41.0%), Clicks (24.3%), Session (10.4%)
OPTIMAL_INTERACTION_WEIGHTS = {
    'w_time': 0.410,        # 41.0% - Temps passé sur article
    'w_clicks': 0.243,      # 24.3% - Nombre de clics
    'w_session': 0.104,     # 10.4% - Qualité de session
    'w_device': 0.060,      #  6.0% - Type d'appareil
    'w_env': 0.046,         #  4.6% - Environnement
    'w_referrer': 0.031,    #  3.1% - Source de trafic
    'w_os': 0.034,          #  3.4% - Système d'exploitation
    'w_country': 0.007,     #  0.7% - Pays (quasi inutile)
    'w_region': 0.066       #  6.6% - Région (important!)
}

DEFAULT_USE_DIVERSITY = True

# Configuration Lambda
MODELS_LOCAL_PATH = '/tmp/models'
TIMEOUT_SECONDS = 30
MEMORY_MB = 1024

# Paramètres de recommandation
MIN_USER_INTERACTIONS = 5  # Minimum d'interactions pour collaborative filtering
MAX_RECOMMENDATIONS = 50
K_SIMILAR_USERS = 50  # Nombre d'utilisateurs similaires à considérer

# Configuration du logging
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
