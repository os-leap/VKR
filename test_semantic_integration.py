"""
Тестирование интеграции семантического поиска в систему
"""
import sys
import os

# Добавляем путь к рабочей директории
sys.path.insert(0, '/workspace')

from simple_semantic_search_integration import SimpleIntegratedSearchSystem, initialize_search_system, perform_integrated_search

def test_semantic_search_integration():
    """Тестирование интеграции семантического поиска"""
    print("Тестируем интеграцию семантического поиска...")
    
    # Пример данных из базы знаний
    sample_data = [
        {
            "title": "Искусственный интеллект и машинное обучение",
            "content": "Искусственный интеллект - это область компьютерных наук, занимающаяся созданием систем, способных выполнять задачи, требующие человеческого интеллекта. Машинное обучение является подразделом ИИ.",
            "topic": "Информационные технологии",
            "author": "test_user"
        },
        {
            "title": "Программирование на Python",
            "content": "Python - это высокоуровневый язык программирования, широко используемый для разработки веб-приложений, анализа данных и машинного обучения.",
            "topic": "Программирование",
            "author": "test_user"
        },
        {
            "title": "Базы данных и SQL",
            "content": "Базы данных используются для хранения и управления структурированными данными. SQL - это язык запросов для работы с реляционными базами данных.",
            "topic": "Базы данных",
            "author": "test_user"
        }
    ]
    
    # Инициализируем систему поиска
    print("Инициализируем систему поиска...")
    initialize_search_system(sample_data)
    
    # Тестируем семантический поиск
    print("\nТестируем семантический поиск...")
    
    test_queries = [
        "Как работают системы, имитирующие человеческий интеллект?",
        "Язык программирования для машинного обучения",
        "Хранение структурированных данных"
    ]
    
    for query in test_queries:
        print(f"\nЗапрос: '{query}'")
        results = perform_integrated_search(query, search_type="semantic", top_k=3)
        
        if results:
            for i, entry in enumerate(results):
                print(f"  {i+1}. {entry['title']} (релевантность: {entry.get('relevance_score', 0):.3f})")
                print(f"     Содержание: {entry['content'][:100]}...")
        else:
            print("  Нет результатов")
    
    print("\nТестирование завершено успешно!")

if __name__ == "__main__":
    test_semantic_search_integration()