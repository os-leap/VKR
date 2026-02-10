#!/usr/bin/env python3
"""
Тестовый скрипт для проверки функциональности поиска заданий по образовательным меткам
"""

from Filter import FilterManager

def test_education_search():
    """Тестируем поиск заданий по образовательным меткам"""
    print("=== Тестирование поиска заданий по образовательным меткам ===")
    
    # Создаем экземпляр менеджера фильтров
    filter_manager = FilterManager()
    
    # Пример: ищем задания для 1 класса по французскому языку
    print("\nПоиск: задания для 1 класса по французскому языку")
    print("Ожидаемый результат: Класс: 1, Параллель: все, Предмет: Французский язык")
    
    results = filter_manager.advanced_search_by_education_tags(
        class_level="1", 
        parallel="все", 
        subject="Французский язык"
    )
    
    print(f"\nНайдено записей: {len(results)}")
    for i, entry in enumerate(results, 1):
        print(f"\n{i}. Заголовок: {entry['title']}")
        print(f"   Содержание: {entry['content'][:100]}...")
        education_info = entry.get('education_info', {})
        if education_info:
            print(f"   Класс: {education_info.get('class', 'не указан')}")
            print(f"   Параллель: {education_info.get('parallel', 'не указана')}")
            print(f"   Предмет: {education_info.get('subject', 'не указан')}")
    
    # Также проверим обычный поиск по ключевым словам
    print("\n=== Тестирование обычного поиска по ключевым словам ===")
    print("Поиск по ключевым словам: '1 класс французский'")
    
    keyword_results = filter_manager.search_by_keywords("1 класс французский")
    
    print(f"\nНайдено записей по ключевым словам: {len(keyword_results)}")
    for i, entry in enumerate(keyword_results, 1):
        print(f"\n{i}. Заголовок: {entry['title']}")
        education_info = entry.get('education_info', {})
        if education_info:
            print(f"   Образовательная информация:")
            print(f"   - Класс: {education_info.get('class', 'не указан')}")
            print(f"   - Параллель: {education_info.get('parallel', 'не указана')}")
            print(f"   - Предмет: {education_info.get('subject', 'не указан')}")

if __name__ == "__main__":
    test_education_search()