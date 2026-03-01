import json
import re
from datetime import datetime


class Material:
    """Класс для представления учебного материала"""
    def __init__(self, title, description, grade, subject, tags=None):
        self.title = title
        self.description = description
        self.grade = grade  # класс (например, 5)
        self.subject = subject  # предмет (например, "математика")
        self.tags = tags or []  # дополнительные теги
    
    def __repr__(self):
        return f"Material(title='{self.title}', grade={self.grade}, subject='{self.subject}', tags={self.tags})"


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
            print(f"Загружено {len(self.documents)} PDF-документов из {self.pdf_documents_file}")
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


class SearchSystem:
    """Система поиска учебных материалов"""
    
    def __init__(self):
        self.materials = []
    
    def add_material(self, material):
        """Добавление материала в систему"""
        self.materials.append(material)
    
    def search_by_grade_and_subject(self, grade=None, subject=None):
        """
        Поиск материалов по классу и/или предмету
        Если параметры не указаны, возвращаются все материалы
        """
        results = []
        
        for material in self.materials:
            # Проверяем соответствие класса и предмета
            grade_match = (grade is None) or (material.grade == grade)
            subject_match = (subject is None) or (material.subject.lower() == subject.lower())
            
            if grade_match and subject_match:
                results.append(material)
        
        return results
    
    def search_with_tags(self, grade=None, subject=None):
        """
        Расширенный поиск с учетом тегов
        Ищет материалы, которые могут быть связаны с указанным классом и предметом через теги
        """
        results = []
        
        for material in self.materials:
            # Основная проверка по полям
            grade_match = (grade is None) or (material.grade == grade)
            subject_match = (subject is None) or (material.subject.lower() == subject.lower())
            
            # Проверка тегов на соответствие классу и предмету
            tag_grade_match = (grade is None) or any(
                str(grade) in str(tag).lower() or 
                f"{grade}-й" in str(tag).lower() or 
                f"{grade} класс" in str(tag).lower()
                for tag in material.tags
            )
            
            tag_subject_match = (subject is None) or any(
                subject.lower() in str(tag).lower()
                for tag in material.tags
            )
            
            # Включаем материал, если он соответствует хотя бы одному критерию
            if (grade_match and subject_match) or (tag_grade_match and tag_subject_match):
                results.append(material)
        
        return results


def main():
    # Создаем систему поиска
    search_system = SearchSystem()
    
    # Добавляем примеры материалов
    search_system.add_material(Material(
        "Задачи по алгебре", 
        "Коллекция задач по алгебре для 8 класса", 
        8, 
        "алгебра",
        ["8 класс", "алгебра", "задачи", "уроки"]
    ))
    
    search_system.add_material(Material(
        "Геометрия 8 класс", 
        "Теория и практика по геометрии", 
        8, 
        "геометрия",
        ["8 класс", "геометрия", "теоремы"]
    ))
    
    search_system.add_material(Material(
        "Физика 7 класс", 
        "Эксперименты и теории", 
        7, 
        "физика",
        ["7 класс", "физика", "эксперименты"]
    ))
    
    search_system.add_material(Material(
        "Математика 8 класс", 
        "Общий курс математики", 
        9, 
        "математика",
        ["8 класс", "математика", "повторение"]  # обратите внимание: тег указывает на 8 класс, но материал для 9 класса
    ))
    
    # Создаем систему поиска по PDF документам
    pdf_search = PDFDocumentSearch()
    
    # Тестирование поиска
    print("Поиск материалов для 8 класса по алгебре:")
    results = search_system.search_with_tags(grade=8, subject="алгебра")
    for result in results:
        print(f"  - {result}")
    
    print("\nПоиск всех материалов для 8 класса:")
    results = search_system.search_with_tags(grade=8)
    for result in results:
        print(f"  - {result}")
    
    print("\nПоиск всех материалов по алгебре:")
    results = search_system.search_with_tags(subject="алгебра")
    for result in results:
        print(f"  - {result}")
    
    print("\nПоиск без фильтров (все материалы):")
    results = search_system.search_with_tags()
    for result in results:
        print(f"  - {result}")
    
    # Интерактивный поиск по PDF документам
    print("\n=== Поиск по PDF документам ===")
    while True:
        query = input("\nВведите поисковый запрос (или 'exit' для выхода): ").strip()

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
            print("\nДокументы не найдены.")


if __name__ == "__main__":
    main()