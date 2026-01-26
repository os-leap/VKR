"""API эндпоинты для системы рекомендаций"""

from flask import Flask, request, jsonify
from recommendation_system import RecommendationSystem
import json


def register_recommendation_endpoints(app):
    """Регистрация эндпоинтов для системы рекомендаций"""
    rec_system = RecommendationSystem()
    
    @app.route('/api/recommendations', methods=['GET'])
    def get_recommendations():
        """Получение рекомендаций для пользователя"""
        user_id = request.args.get('user_id')
        if not user_id:
            return jsonify({'error': 'User ID is required'}), 400
        
        days = int(request.args.get('days', 7))
        limit_per_type = int(request.args.get('limit_per_type', 3))
        
        recommendations = rec_system.get_recommendations(user_id, days, limit_per_type)
        
        return jsonify({
            'user_id': user_id,
            'recommendations': recommendations
        })
    
    @app.route('/api/log_request', methods=['POST'])
    def log_user_request():
        """Логирование запроса пользователя"""
        data = request.json
        user_id = data.get('user_id')
        item_type = data.get('item_type')
        item_id = data.get('item_id')
        
        if not all([user_id, item_type, item_id]):
            return jsonify({'error': 'User ID, item type, and item ID are required'}), 400
        
        rec_system.log_request(user_id, item_type, item_id)
        
        return jsonify({'status': 'success'})
    
    @app.route('/api/frequent_items', methods=['GET'])
    def get_frequent_items():
        """Получение часто запрашиваемых элементов определенного типа"""
        user_id = request.args.get('user_id')
        item_type = request.args.get('item_type')
        
        if not user_id or not item_type:
            return jsonify({'error': 'User ID and item type are required'}), 400
        
        days = int(request.args.get('days', 30))
        limit = int(request.args.get('limit', 5))
        
        frequent_items = rec_system.get_frequent_items(user_id, item_type, days, limit)
        
        return jsonify({
            'user_id': user_id,
            'item_type': item_type,
            'frequent_items': frequent_items
        })
    
    return app


# Для тестирования
if __name__ == "__main__":
    app = Flask(__name__)
    app = register_recommendation_endpoints(app)
    
    # Запуск тестового сервера
    app.run(debug=True, port=5001)