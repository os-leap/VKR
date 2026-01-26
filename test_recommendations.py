#!/usr/bin/env python3
"""
Тестирование системы рекомендаций для часто запрашиваемых тем, разделов и записей
"""

import requests
import json
import time

BASE_URL = "http://localhost:5000"

def test_recommendations():
    print("=== Тестирование системы рекомендаций ===\n")
    
    # Тестируем разных пользователей
    test_users = ["test_user_001", "test_user_002"]
    
    # Симулируем действия пользователей
    user_actions = {
        "test_user_001": [
            {"item_type": "topic", "item_id": "math_algebra"},
            {"item_type": "topic", "item_id": "math_algebra"},
            {"item_type": "section", "item_id": "algebra_basics"},
            {"item_type": "record", "item_id": "linear_equations"},
            {"item_type": "record", "item_id": "linear_equations"},
            {"item_type": "record", "item_id": "quadratic_equations"},
        ],
        "test_user_002": [
            {"item_type": "topic", "item_id": "physics_mechanics"},
            {"item_type": "topic", "item_id": "physics_mechanics"},
            {"item_type": "section", "item_id": "kinematics"},
            {"item_type": "section", "item_id": "kinematics"},
            {"item_type": "record", "item_id": "newtons_laws"},
        ]
    }
    
    print("1. Логирование действий пользователей...")
    for user_id, actions in user_actions.items():
        print(f"\n  Логирование действий для {user_id}:")
        for action in actions:
            response = requests.post(
                f"{BASE_URL}/api/log_request",
                json={
                    "user_id": user_id,
                    "item_type": action["item_type"],
                    "item_id": action["item_id"]
                }
            )
            if response.status_code == 200:
                print(f"    ✓ {action['item_type']}: {action['item_id']}")
            else:
                print(f"    ✗ Ошибка при логировании: {response.text}")
    
    # Ждем немного, чтобы изменения вступили в силу
    time.sleep(1)
    
    print("\n2. Получение рекомендаций для пользователей...")
    for user_id in test_users:
        print(f"\n  Рекомендации для {user_id}:")
        response = requests.get(f"{BASE_URL}/api/recommendations?user_id={user_id}&limit_per_type=5")
        
        if response.status_code == 200:
            data = response.json()
            recommendations = data["recommendations"]
            
            for category, items in recommendations.items():
                if items:
                    print(f"    {category.upper()}:")
                    for item in items:
                        print(f"      - {item['item_id']} (запросов: {item['frequency']})")
                else:
                    print(f"    {category.upper()}: нет данных")
        else:
            print(f"    Ошибка при получении рекомендаций: {response.text}")
    
    print("\n3. Тестирование получения часто запрашиваемых элементов по типу...")
    for user_id in test_users:
        print(f"\n  Часто запрашиваемые темы для {user_id}:")
        response = requests.get(f"{BASE_URL}/api/frequent_items?user_id={user_id}&item_type=topic")
        
        if response.status_code == 200:
            data = response.json()
            for item in data["frequent_items"]:
                print(f"    - {item['item_id']} (частота: {item['frequency']})")
        else:
            print(f"    Ошибка: {response.text}")

    print("\n=== Тестирование завершено ===")

if __name__ == "__main__":
    test_recommendations()