#!/usr/bin/env python3
"""
Тестирование функционала поиска по образовательным меткам
"""

from Filter import FilterManager

def test_education_search():
    """Тестирует поиск по образовательным меткам"""
    fm = FilterManager()
    
    print("Тест 1: Поиск по запросу '1 класс французский'")
    results = fm.search_by_keywords("1 класс французский")
    print(f"Найдено записей: {len(results)}")
    for i, entry in enumerate(results, 1):
        print(f"  {i}. {entry.get('title', 'Без заголовка')}")
        edu_info = entry.get('education_info', {})
        if edu_info:
            print(f"     Класс: {edu_info.get('class', 'не указан')}, "
                  f"Предмет: {edu_info.get('subject', 'не указан')}, "
                  f"Параллель: {edu_info.get('parallel', 'все')}")
    
    print("\nТест 2: Поиск по запросу 'французский язык 1'")
    results = fm.search_by_keywords("французский язык 1")
    print(f"Найдено записей: {len(results)}")
    for i, entry in enumerate(results, 1):
        print(f"  {i}. {entry.get('title', 'Без заголовка')}")
        edu_info = entry.get('education_info', {})
        if edu_info:
            print(f"     Класс: {edu_info.get('class', 'не указан')}, "
                  f"Предмет: {edu_info.get('subject', 'не указан')}, "
                  f"Параллель: {edu_info.get('parallel', 'все')}")
    
    print("\nТест 3: Обычный поиск по ключевым словам")
    results = fm.search_by_keywords("задание для детей")
    print(f"Найдено записей: {len(results)}")
    for i, entry in enumerate(results, 1):
        print(f"  {i}. {entry.get('title', 'Без заголовка')}")
        edu_info = entry.get('education_info', {})
        if edu_info:
            print(f"     Класс: {edu_info.get('class', 'не указан')}, "
                  f"Предмет: {edu_info.get('subject', 'не указан')}, "
                  f"Параллель: {edu_info.get('parallel', 'все')}")

if __name__ == "__main__":
    test_education_search()