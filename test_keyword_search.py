#!/usr/bin/env python3
"""Тестирование возможности поиска по ключевым словам"""

from Filter import FilterManager

def test_keyword_search():
    # Создаем экземпляр менеджера фильтров
    fm = FilterManager()
    
    print("Тестирование поиска по ключевым словам...")
    print("="*50)
    
    # Тестируем поиск по ключевым словам
    print("\n1. Поиск по запросу 'задание для N класса по I предмету':")
    keywords = "задание для 1 класса по Французский язык"
    results = fm.search_by_keywords(keywords)
    
    print(f"Найдено {len(results)} записей:")
    for i, entry in enumerate(results, 1):
        print(f"  {i}. Заголовок: {entry['title']}")
        print(f"     Тема: {entry['topic']}")
        if 'education_info' in entry:
            edu_info = entry['education_info']
            print(f"     Класс: {edu_info.get('class', 'N/A')}, Предмет: {edu_info.get('subject', 'N/A')}")
        print()
    
    # Тестируем более простой поиск
    print("\n2. Поиск по слову 'класс':")
    results = fm.search_by_keywords("класс")
    print(f"Найдено {len(results)} записей:")
    for i, entry in enumerate(results[:5], 1):  # Показываем первые 5 результатов
        print(f"  {i}. Заголовок: {entry['title']}")
    
    print("\n3. Поиск по слову 'предмет':")
    results = fm.search_by_keywords("предмет")
    print(f"Найдено {len(results)} записей:")
    for i, entry in enumerate(results, 1):
        print(f"  {i}. Заголовок: {entry['title']}")
    
    print("\n4. Поиск по нескольким ключевым словам 'задание детям':")
    results = fm.search_by_keywords("задание дети")
    print(f"Найдено {len(results)} записей:")
    for i, entry in enumerate(results, 1):
        print(f"  {i}. Заголовок: {entry['title']}")
        print(f"     Содержание: {entry['content'][:50]}...")

if __name__ == "__main__":
    test_keyword_search()