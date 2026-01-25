"""
Version ultra-simple pour tester si la Function App fonctionne
"""
import json
import logging
import azure.functions as func

def main(req: func.HttpRequest) -> func.HttpResponse:
    """Test simple sans chargement de modèles"""
    logging.info('Test simple - Function appelée')

    try:
        # Juste retourner un message simple
        response = {
            'status': 'ok',
            'message': 'Function App fonctionne!',
            'test': 'simple'
        }

        return func.HttpResponse(
            json.dumps(response, indent=2),
            status_code=200,
            mimetype="application/json"
        )

    except Exception as e:
        logging.error(f"Erreur: {e}", exc_info=True)
        return func.HttpResponse(
            json.dumps({
                'error': str(e),
                'type': type(e).__name__
            }),
            status_code=500,
            mimetype="application/json"
        )
