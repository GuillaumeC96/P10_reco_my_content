"""
AWS Lambda Function pour le système de recommandation
Point d'entrée pour les requêtes HTTP
"""

import json
import logging
import os
from recommendation_engine import RecommendationEngine

# Configuration du logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Instance globale du moteur (réutilisée entre invocations Lambda)
engine = None

def initialize_engine():
    """Initialise le moteur de recommandation (appelé une seule fois)"""
    global engine
    if engine is None:
        logger.info("Initialisation du moteur de recommandation...")
        models_path = os.environ.get('MODELS_PATH', '/tmp/models')
        engine = RecommendationEngine(models_path=models_path)
        engine.load_models()
        logger.info("Moteur initialisé avec succès")
    return engine

def lambda_handler(event, context):
    """
    Handler principal de la Lambda Function

    Args:
        event: Événement AWS Lambda contenant les paramètres de la requête
        context: Contexte d'exécution Lambda

    Returns:
        Réponse HTTP avec les recommandations
    """
    logger.info(f"Événement reçu: {json.dumps(event)}")

    try:
        # Initialiser le moteur (si pas déjà fait)
        rec_engine = initialize_engine()

        # Parser les paramètres
        # Gérer différents formats d'événements (API Gateway, Function URL, etc.)
        if 'queryStringParameters' in event and event['queryStringParameters']:
            params = event['queryStringParameters']
        elif 'body' in event and event['body']:
            params = json.loads(event['body'])
        else:
            params = event

        # Récupérer les paramètres
        user_id = params.get('user_id')
        n_recommendations = int(params.get('n_recommendations', 5))

        # Nouveaux paramètres avec 3 coefficients (ratio 3:2:1 par défaut)
        weight_collab = float(params.get('weight_collab', 3.0))
        weight_content = float(params.get('weight_content', 2.0))
        weight_trend = float(params.get('weight_trend', 1.0))
        use_diversity = params.get('use_diversity', 'true').lower() == 'true'

        # Validation
        if user_id is None:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Le paramètre user_id est requis',
                    'example': '/recommend?user_id=123&n_recommendations=5&weight_collab=3&weight_content=2&weight_trend=1'
                })
            }

        user_id = int(user_id)

        if n_recommendations < 1 or n_recommendations > 50:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'n_recommendations doit être entre 1 et 50'
                })
            }

        # Générer les recommandations
        logger.info(f"Génération de recommandations pour user_id={user_id}")
        recommendations = rec_engine.recommend(
            user_id=user_id,
            n_recommendations=n_recommendations,
            weight_collab=weight_collab,
            weight_content=weight_content,
            weight_trend=weight_trend,
            use_diversity=use_diversity
        )

        # Construire la réponse
        response_body = {
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

        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(response_body, indent=2)
        }

    except ValueError as e:
        logger.error(f"Erreur de validation: {e}")
        return {
            'statusCode': 400,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': f'Paramètre invalide: {str(e)}'
            })
        }

    except Exception as e:
        logger.error(f"Erreur lors de la génération des recommandations: {e}", exc_info=True)
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Erreur interne du serveur',
                'message': str(e)
            })
        }

def health_check_handler(event, context):
    """Handler pour vérifier que la Lambda est opérationnelle"""
    try:
        rec_engine = initialize_engine()

        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'status': 'healthy',
                'engine_loaded': rec_engine.loaded,
                'message': 'Le système de recommandation est opérationnel'
            })
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        return {
            'statusCode': 503,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'status': 'unhealthy',
                'error': str(e)
            })
        }
