import json
import re
from datetime import datetime


class PDFDocumentSearch:
    """Система поиска по документам из файла pdf_documents.json"""
    
    def __init__(self, pdf_documents_file="pdf_documents.json"):
        self.pdf_documents_file = pdf_documents_file
        self.documents = []
        self.load_documents()
    
    def load_documents(self):
        """Загрузка документов из JSON-файла"""
        try:
            with open(self.pdf_documents_file, 'r', encoding='utf-8') as f:
                self.documents = json.load(f)
            print(f"Загружено {len(self.documents)} документов из {self.pdf_documents_file}")
        except FileNotFoundError:
            print(f"Файл {self.pdf_documents_file} не найден")
            self.documents = []
        except json.JSONDecodeError:
            print(f"Ошибка чтения JSON из файла {self.pdf_documents_file}")
            self.documents = []
    
    def search(self, query):
        """
        Поиск документов по запросу
        Поиск производится по следующим полям: title, filename, extracted_title
        """
        if not query:
            return self.documents
        
        query_lower = query.lower().strip()
        results = []
        
        for doc in self.documents:
            # Проверяем совпадения в различных полях документа
            match_fields = []
            
            # Проверяем заголовки
            if 'title' in doc and query_lower in doc['title'].lower():
                match_fields.append('title')
                
            if 'extracted_title' in doc and doc['extracted_title'] and query_lower in doc['extracted_title'].lower():
                match_fields.append('extracted_title')
                
            if 'filename' in doc and query_lower in doc['filename'].lower():
                match_fields.append('filename')
            
            # Если есть совпадения, добавляем документ в результаты
            if match_fields:
                doc_copy = doc.copy()
                doc_copy['match_fields'] = match_fields
                results.append(doc_copy)
        
        return results
    
    def advanced_search(self, query, filters=None):
        """
        Расширенный поиск с возможностью фильтрации
        filters: словарь с фильтрами {'field': 'value'}
        """
        results = self.search(query)
        
        if filters:
            filtered_results = []
            for doc in results:
                match = True
                for field, value in filters.items():
                    if field in doc:
                        if str(value).lower() not in str(doc[field]).lower():
                            match = False
                            break
                if match:
                    filtered_results.append(doc)
            results = filtered_results
        
        return results


def main():
    # Создаем экземпляр системы поиска
    pdf_search = PDFDocumentSearch()
    
    # Примеры использования
    print("=== Система поиска по PDF документам ===\n")
    
    while True:
        query = input("Введите поисковый запрос (или 'exit' для выхода): ").strip()
        
        if query.lower() == 'exit':
            break
            
        if not query:
            continue
            
        results = pdf_search.search(query)
        
        print(f"\nНайдено {len(results)} документов по запросу '{query}':")
        
        for i, doc in enumerate(results, 1):
            print(f"\n{i}. ID: {doc.get('id', 'N/A')}")
            print(f"   Заголовок: {doc.get('title', 'N/A')}")
            print(f"   Имя файла: {doc.get('filename', 'N/A')}")
            print(f"   Извлеченный заголовок: {doc.get('extracted_title', 'N/A')}")
            print(f"   URL: {doc.get('url', 'N/A')}")
            print(f"   Дата скачивания: {doc.get('download_date', 'N/A')}")
            print(f"   Совпадения в полях: {doc.get('match_fields', [])}")
        
        if not results:
            print("Документы не найдены.")


if __name__ == "__main__":
    main()