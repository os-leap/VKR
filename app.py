"""Основное Flask-приложение с системой рекомендаций"""

from flask import Flask, render_template
from api_endpoints import register_recommendation_endpoints
import os


def create_app():
    app = Flask(__name__, 
                template_folder='templates',
                static_folder='static')
    
    # Регистрация эндпоинтов для системы рекомендаций
    app = register_recommendation_endpoints(app)
    
    @app.route('/')
    def index():
        return render_template('index.html')
    
    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))