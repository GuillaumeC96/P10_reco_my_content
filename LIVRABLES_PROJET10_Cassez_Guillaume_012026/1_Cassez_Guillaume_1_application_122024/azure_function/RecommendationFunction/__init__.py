"""
Azure Function pour le système de recommandation My Content
Point d'entrée HTTP pour les requêtes de recommandation
Version simplifiée: modèles inclus dans le déploiement
"""

import json
import logging
import os
import sys
import azure.functions as func

# Ajouter le répertoire parent au path pour imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from recommendation_engine import RecommendationEngine

# Instance globale du moteur (réutilisée entre invocations)
engine = None

def initialize_engine():
    """Initialise le moteur de recommandation (appelé une seule fois)"""
    global engine
    if engine is None:
        try:
            logging.info("Initialisation du moteur de recommandation...")

            # Chemin vers les modèles inclus dans le déploiement
            # Les modèles sont dans le dossier 'models' à la racine de la Function App
            base_dir = os.path.dirname(os.path.dirname(__file__))
            models_path = os.path.join(base_dir, 'models')

            logging.info(f"Chemin des modèles: {models_path}")
            logging.info(f"Existence: {os.path.exists(models_path)}")

            if os.path.exists(models_path):
                files = os.listdir(models_path)
                logging.info(f"Fichiers trouvés: {len(files)} - {', '.join(files[:5])}")
            else:
                raise FileNotFoundError(f"Répertoire modèles introuvable: {models_path}")

            engine = RecommendationEngine(models_path=models_path)
            engine.load_models()
            logging.info("✓ Moteur initialisé avec succès")

        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            logging.error(f"Erreur lors de l'initialisation du moteur: {e}")
            logging.error(f"Traceback: {error_trace}")
            raise

    return engine

def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    Handler principal de l'Azure Function

    Args:
        req: Requête HTTP Azure Functions

    Returns:
        Réponse HTTP avec les recommandations
    """
    logging.info(f'Requête HTTP reçue: {req.method} {req.url}')

    try:
        # Initialiser le moteur (si pas déjà fait)
        rec_engine = initialize_engine()

        # Parser les paramètres (query params ou body JSON)
        user_id = req.params.get('user_id')
        n_recommendations = req.params.get('n_recommendations', '5')
        weight_collab = req.params.get('weight_collab', '0.36')
        weight_content = req.params.get('weight_content', '0.39')
        weight_trend = req.params.get('weight_trend', '0.25')
        use_diversity = req.params.get('use_diversity', 'true')

        # Si pas de query params, essayer le body JSON
        if user_id is None:
            try:
                req_body = req.get_json()
                user_id = req_body.get('user_id')
                n_recommendations = req_body.get('n', req_body.get('n_recommendations', 5))
                weight_collab = req_body.get('weight_collab', 0.36)
                weight_content = req_body.get('weight_content', 0.39)
                weight_trend = req_body.get('weight_trend', 0.25)
                use_diversity = req_body.get('use_diversity', True)
            except ValueError:
                pass

        # Validation
        if user_id is None:
            return func.HttpResponse(
                json.dumps({
                    'error': 'Le paramètre user_id est requis',
                    'example': {
                        'user_id': 58,
                        'n': 5
                    }
                }, indent=2),
                status_code=400,
                mimetype="application/json"
            )

        # Conversion des types
        try:
            user_id = int(user_id)
            n_recommendations = int(n_recommendations)
            weight_collab = float(weight_collab)
            weight_content = float(weight_content)
            weight_trend = float(weight_trend)
            use_diversity_bool = str(use_diversity).lower() in ['true', '1', 'yes']
        except ValueError as e:
            return func.HttpResponse(
                json.dumps({
                    'error': f'Paramètre invalide: {str(e)}'
                }, indent=2),
                status_code=400,
                mimetype="application/json"
            )

        # Générer les recommandations
        logging.info(f"Génération de {n_recommendations} recommandations pour user_id={user_id}")

        recommendations = rec_engine.recommend(
            user_id=user_id,
            n_recommendations=n_recommendations,
            weight_collab=weight_collab,
            weight_content=weight_content,
            weight_trend=weight_trend,
            use_diversity=use_diversity_bool
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
                'use_diversity': use_diversity_bool
            },
            'metadata': {
                'engine_loaded': rec_engine.loaded,
                'platform': 'Azure Functions',
                'version': 'lite'
            }
        }

        logging.info(f"Recommandations générées avec succès: {len(recommendations)} articles")

        return func.HttpResponse(
            json.dumps(response_body, indent=2),
            status_code=200,
            mimetype="application/json",
            headers={
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            }
        )

    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        logging.error(f"Erreur: {e}", exc_info=True)

        return func.HttpResponse(
            json.dumps({
                'error': 'Erreur interne du serveur',
                'message': str(e),
                'type': type(e).__name__,
                'traceback': error_trace.split('\n')[:15]
            }, indent=2),
            status_code=500,
            mimetype="application/json"
        )
