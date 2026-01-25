#!/bin/bash
# Script de lancement de l'application Streamlit pour l'API My Content

echo "================================================="
echo "  My Content - Application Streamlit"
echo "================================================="
echo ""
echo "🚀 Lancement de l'application..."
echo ""
echo "📍 L'application va s'ouvrir dans votre navigateur"
echo "📍 URL: http://localhost:8501"
echo ""
echo "💡 Pour arrêter: Ctrl+C"
echo ""
echo "================================================="
echo ""

# Lancer Streamlit
streamlit run streamlit_api.py --server.port 8501 --server.headless false

# Note:
# --server.port 8501 : Port par défaut
# --server.headless false : Ouvre automatiquement le navigateur
