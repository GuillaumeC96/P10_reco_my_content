"""
Configuration pour la Lambda Function
"""

import os

# Configuration S3
S3_BUCKET = os.environ.get('S3_BUCKET', 'my-content-reco-bucket')
S3_MODELS_PREFIX = os.environ.get('S3_MODELS_PREFIX', 'models/')

# Configuration du moteur de recommandation
DEFAULT_N_RECOMMENDATIONS = 5
DEFAULT_ALPHA = 0.6  # Poids du collaborative filtering
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
