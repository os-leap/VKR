#!/usr/bin/env python3
"""
Простой тест для проверки работы системы поиска по PDF документам
"""

from pdf_search_system import PDFDocumentSearch

def test_pdf_search():
    print("Тестирование системы поиска по PDF документам...")
    
    # Создаем экземпляр системы поиска
    pdf_search = PDFDocumentSearch()
    
    # Тестируем различные поисковые запросы
    test_queries = [
        "образование",
        "ФГОС",
        "закон",
        "министерство",
        "адаптационный"
    ]
    
    for query in test_queries:
        print(f"\n--- Поиск по запросу: '{query}' ---")
        results = pdf_search.search(query)
        print(f"Найдено {len(results)} документов:")
        
        for i, doc in enumerate(results, 1):
            print(f"  {i}. ID: {doc.get('id', 'N/A')}")
            print(f"     Заголовок: {doc.get('title', 'N/A')}")
            print(f"     Совпадения в полях: {doc.get('match_fields', [])}")
    
    # Тест без запроса (должно вернуть все документы)
    print(f"\n--- Поиск без запроса (все документы) ---")
    all_results = pdf_search.search("")
    print(f"Всего документов: {len(all_results)}")

if __name__ == "__main__":
    test_pdf_search()