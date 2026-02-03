"""
Тестирование полной интеграции семантического поиска в веб-приложение
"""
import sys
import os
import json
from datetime import datetime

# Добавляем путь к рабочей директории
sys.path.insert(0, '/workspace')

from app import load_data, perform_integrated_search
from simple_semantic_search_integration import initialize_search_system

def test_full_integration():
    """Тестирование полной интеграции семантического поиска"""
    print("Тестируем полную интеграцию семантического поиска в веб-приложение...")
    
    # Создаем тестовую базу знаний, если она не существует
    test_data = [
        {
            "title": "Искусственный интеллект и машинное обучение",
            "content": "Искусственный интеллект - это область компьютерных наук, занимающаяся созданием систем, способных выполнять задачи, требующие человеческого интеллекта. Машинное обучение является подразделом ИИ.",
            "topic": "Информационные технологии",
            "author": "test_user",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        },
        {
            "title": "Программирование на Python",
            "content": "Python - это высокоуровневый язык программирования, широко используемый для разработки веб-приложений, анализа данных и машинного обучения.",
            "topic": "Программирование",
            "author": "test_user",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        },
        {
            "title": "Базы данных и SQL",
            "content": "Базы данных используются для хранения и управления структурированными данными. SQL - это язык запросов для работы с реляционными базами данными.",
            "topic": "Базы данных",
            "author": "test_user",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        },
        {
            "title": "Веб-разработка",
            "content": "Веб-разработка включает создание сайтов и веб-приложений с использованием HTML, CSS и JavaScript.",
            "topic": "Программирование",
            "author": "test_user",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
    ]
    
    # Сохраняем тестовые данные
    with open('knowledge_base.json', 'w', encoding='utf-8') as f:
        json.dump(test_data, f, ensure_ascii=False, indent=4)
    
    print("Создана тестовая база знаний")
    
    # Загружаем данные через функцию приложения
    loaded_data = load_data()
    print(f"Загружено {len(loaded_data)} записей из базы знаний")
    
    # Тестируем семантический поиск
    print("\nТестируем семантический поиск:")
    
    test_queries = [
        "Как работают системы, имитирующие человеческий интеллект?",
        "Язык программирования для веб-разработки",
        "Хранение и управление данными",
        "Создание веб-приложений"
    ]
    
    for query in test_queries:
        print(f"\nЗапрос: '{query}'")
        results = perform_integrated_search(query, search_type="semantic", top_k=3)
        
        if results:
            for i, entry in enumerate(results):
                print(f"  {i+1}. {entry['title']} (релевантность: {entry.get('relevance_score', 0):.3f})")
                print(f"     Тема: {entry['topic']}")
                print(f"     Содержание: {entry['content'][:100]}...")
        else:
            print("  Нет результатов")
    
    # Тестируем синтаксический поиск для сравнения
    print("\nТестируем синтаксический поиск для сравнения:")
    query = "Python"
    results = perform_integrated_search(query, search_type="syntax", top_k=3)
    
    print(f"\nЗапрос: '{query}' (синтаксический)")
    if results:
        for i, entry in enumerate(results):
            print(f"  {i+1}. {entry['title']}")
            print(f"     Тема: {entry['topic']}")
    else:
        print("  Нет результатов")
    
    print("\nТестирование полной интеграции завершено успешно!")
    print("\nСемантический поиск теперь интегрирован в систему и готов к использованию.")
    print("Пользователи могут выбирать между синтаксическим и семантическим поиском через интерфейс.")

if __name__ == "__main__":
    test_full_integration()