"""Система рекомендаций для часто запрашиваемых тем, разделов и записей"""

import sqlite3
from datetime import datetime, timedelta
from collections import defaultdict
import json


class RecommendationSystem:
    def __init__(self, db_path='recommendations.db'):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        """Инициализация базы данных для хранения истории запросов"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Таблица для хранения истории запросов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS request_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                item_type TEXT NOT NULL,  -- 'topic', 'section', 'record'
                item_id TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Индекс для ускорения поиска по пользователю и типу элемента
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_user_type ON request_history(user_id, item_type)
        ''')
        
        conn.commit()
        conn.close()
    
    def log_request(self, user_id, item_type, item_id):
        """Логирование запроса пользователя"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO request_history (user_id, item_type, item_id)
            VALUES (?, ?, ?)
        ''', (user_id, item_type, item_id))
        
        conn.commit()
        conn.close()
    
    def get_frequent_items(self, user_id, item_type, days=30, limit=5):
        """Получение часто запрашиваемых элементов определенного типа за последние дни"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Вычисляем дату начала периода
        start_date = datetime.now() - timedelta(days=days)
        
        cursor.execute('''
            SELECT item_id, COUNT(*) as frequency
            FROM request_history
            WHERE user_id = ? AND item_type = ? AND timestamp >= ?
            GROUP BY item_id
            ORDER BY frequency DESC
            LIMIT ?
        ''', (user_id, item_type, start_date.isoformat(), limit))
        
        results = cursor.fetchall()
        conn.close()
        
        return [{'item_id': item[0], 'frequency': item[1]} for item in results]
    
    def get_all_frequent_items(self, user_id, days=30):
        """Получение всех часто запрашиваемых элементов для пользователя"""
        item_types = ['topic', 'section', 'record']
        result = {}
        
        for item_type in item_types:
            result[item_type] = self.get_frequent_items(user_id, item_type, days)
        
        return result
    
    def get_recommendations(self, user_id, days=7, limit_per_type=3):
        """Получение рекомендаций для пользователя"""
        frequent_items = self.get_all_frequent_items(user_id, days)
        recommendations = {}
        
        for item_type, items in frequent_items.items():
            recommendations[item_type] = items[:limit_per_type]
        
        return recommendations


# Пример использования
if __name__ == "__main__":
    rec_system = RecommendationSystem()
    
    # Логирование примеров запросов
    rec_system.log_request("user123", "topic", "math_algebra")
    rec_system.log_request("user123", "topic", "math_algebra")
    rec_system.log_request("user123", "section", "algebra_basics")
    rec_system.log_request("user123", "record", "linear_equations")
    rec_system.log_request("user123", "topic", "physics_mechanics")
    
    # Получение рекомендаций
    recommendations = rec_system.get_recommendations("user123")
    print(json.dumps(recommendations, indent=2, ensure_ascii=False))