"""Improved search system that properly filters results and searches in pdf_documents"""

import json
import re
from difflib import SequenceMatcher
from typing import List, Dict, Any


class ImprovedSearchSystem:
    """Search system that properly filters results and searches in pdf_documents"""

    def __init__(self, pdf_documents_path: str = "/workspace/pdf_documents.json"):
        self.materials = []
        self.pdf_documents = self.load_pdf_documents(pdf_documents_path)

    def load_pdf_documents(self, path: str) -> List[Dict]:
        """Load PDF documents from JSON file"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"PDF documents file not found: {path}")
            return []

    def add_material(self, material: Dict[str, Any]):
        """Add material to the search system"""
        self.materials.append(material)

    def search_with_filter(self, query: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Search with strict filtering - only returns results that contain the query
        Results are separated into materials and pdf_documents
        """
        query_lower = query.lower()
        
        # Search in materials
        material_results = []
        for material in self.materials:
            # Check all relevant fields in material
            fields_to_check = [
                material.get('title', ''),
                material.get('content', ''),
                material.get('description', ''),
                material.get('file_name', ''),
                str(material.get('subject', '')),
                str(material.get('grade', ''))
            ]
            
            # Calculate score based on matches
            score = 0
            match_details = {}
            
            for field_name, field_value in [('title', material.get('title', '')), 
                                          ('content', material.get('content', '')),
                                          ('description', material.get('description', '')),
                                          ('file_name', material.get('file_name', '')),
                                          ('subject', str(material.get('subject', ''))),
                                          ('grade', str(material.get('grade', '')))]:
                if query_lower in field_value.lower():
                    # Exact match in field gets high score
                    score += 1
                    match_details[field_name] = field_value
            
            if score > 0:
                material_results.append({
                    'material': material,
                    'score': score,
                    'matches': match_details
                })
        
        # Search in pdf_documents
        pdf_results = []
        for doc in self.pdf_documents:
            # Check all relevant fields in PDF document
            fields_to_check = [
                doc.get('title', ''),
                doc.get('filename', ''),
                doc.get('extracted_title', ''),
                doc.get('url', '')
            ]
            
            score = 0
            match_details = {}
            
            for field_name, field_value in [
                ('title', doc.get('title', '')), 
                ('filename', doc.get('filename', '')),
                ('extracted_title', doc.get('extracted_title', '')),
                ('url', doc.get('url', ''))
            ]:
                if query_lower in field_value.lower():
                    score += 1
                    match_details[field_name] = field_value
            
            if score > 0:
                pdf_results.append({
                    'document': doc,
                    'score': score,
                    'matches': match_details
                })
        
        # Sort both result sets by score (highest first)
        material_results.sort(key=lambda x: x['score'], reverse=True)
        pdf_results.sort(key=lambda x: x['score'], reverse=True)
        
        return {
            'materials': material_results,
            'pdf_documents': pdf_results
        }

    def search_exact_match(self, query: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Search for exact phrase matches only
        """
        query_lower = query.lower()
        
        # Search in materials
        material_results = []
        for material in self.materials:
            # Check if the exact query appears in any field
            fields_to_check = [
                material.get('title', ''),
                material.get('content', ''),
                material.get('description', ''),
                material.get('file_name', ''),
                str(material.get('subject', '')),
                str(material.get('grade', ''))
            ]
            
            for field_value in fields_to_check:
                if query_lower in field_value.lower():
                    # Found exact match
                    match_details = {}
                    for field_name, field_value in [('title', material.get('title', '')), 
                                                  ('content', material.get('content', '')),
                                                  ('description', material.get('description', '')),
                                                  ('file_name', material.get('file_name', '')),
                                                  ('subject', str(material.get('subject', ''))),
                                                  ('grade', str(material.get('grade', '')))]:
                        if query_lower in field_value.lower():
                            match_details[field_name] = field_value
                    
                    material_results.append({
                        'material': material,
                        'matches': match_details
                    })
                    break  # Don't add the same material twice
        
        # Search in pdf_documents
        pdf_results = []
        for doc in self.pdf_documents:
            # Check if the exact query appears in any field
            fields_to_check = [
                doc.get('title', ''),
                doc.get('filename', ''),
                doc.get('extracted_title', ''),
                doc.get('url', '')
            ]
            
            for field_value in fields_to_check:
                if query_lower in field_value.lower():
                    # Found exact match
                    match_details = {}
                    for field_name, field_value in [
                        ('title', doc.get('title', '')), 
                        ('filename', doc.get('filename', '')),
                        ('extracted_title', doc.get('extracted_title', '')),
                        ('url', doc.get('url', ''))
                    ]:
                        if query_lower in field_value.lower():
                            match_details[field_name] = field_value
                    
                    pdf_results.append({
                        'document': doc,
                        'matches': match_details
                    })
                    break  # Don't add the same document twice
        
        return {
            'materials': material_results,
            'pdf_documents': pdf_results
        }


# Example usage and test
if __name__ == "__main__":
    # Create search system
    search_system = ImprovedSearchSystem()
    
    # Add example materials (these would normally come from your database)
    materials = [
        {
            'title': 'Алгебраические выражения 8 класс',
            'content': 'В этой статье рассматриваются основные алгебраические выражения и их применение в 8 классе',
            'file_name': 'algebra_expressions_8_class.pdf',
            'description': 'Подробное руководство по алгебраическим выражениям',
            'grade': 8,
            'subject': 'алгебра'
        },
        {
            'title': 'Задачи по геометрии',
            'content': 'Различные задачи по геометрии для школьников',
            'file_name': 'geometrical_problems_solutions.docx',
            'description': 'Коллекция геометрических задач',
            'grade': 8,
            'subject': 'геометрия'
        },
        {
            'title': 'Приказ №286 от 31.05.2021 ФГОС НОО',
            'content': 'Федеральный государственный образовательный стандарт начального общего образования',
            'file_name': 'prikaz_286_fgos_noo.pdf',
            'description': 'Официальный документ по ФГОС НОО',
            'grade': None,
            'subject': 'образование'
        },
        {
            'title': 'История России',
            'content': 'Курс истории России от древности до современности',
            'file_name': 'history_russia_course.pdf',
            'description': 'Полный курс истории России',
            'grade': 8,
            'subject': 'история'
        }
    ]
    
    for material in materials:
        search_system.add_material(material)
    
    # Test search with filter
    print("=== Тестирование поискового запроса 'приказ №' ===")
    results = search_system.search_exact_match("приказ №")
    
    print(f"Найдено {len(results['materials'])} материалов:")
    for i, result in enumerate(results['materials'], 1):
        print(f"\n{i}. Заголовок: {result['material']['title']}")
        print(f"   Предмет: {result['material']['subject']}, Класс: {result['material']['grade']}")
        print(f"   Описание: {result['material']['description']}")
        print(f"   Файл: {result['material']['file_name']}")
        print(f"   Совпадения: {list(result['matches'].keys())}")
    
    print(f"\nНайдено {len(results['pdf_documents'])} PDF документов:")
    for i, result in enumerate(results['pdf_documents'], 1):
        print(f"\n{i}. Заголовок: {result['document']['title']}")
        print(f"   Файл: {result['document']['filename']}")
        print(f"   URL: {result['document']['url']}")
        print(f"   Совпадения: {list(result['matches'].keys())}")
    
    print("\n" + "="*50)
    print("=== Тестирование поискового запроса 'ФГОС' ===")
    results = search_system.search_exact_match("ФГОС")
    
    print(f"Найдено {len(results['materials'])} материалов:")
    for i, result in enumerate(results['materials'], 1):
        print(f"\n{i}. Заголовок: {result['material']['title']}")
        print(f"   Предмет: {result['material']['subject']}, Класс: {result['material']['grade']}")
        print(f"   Описание: {result['material']['description']}")
        print(f"   Совпадения: {list(result['matches'].keys())}")
    
    print(f"\nНайдено {len(results['pdf_documents'])} PDF документов:")
    for i, result in enumerate(results['pdf_documents'], 1):
        print(f"\n{i}. Заголовок: {result['document']['title']}")
        print(f"   Файл: {result['document']['filename']}")
        print(f"   Совпадения: {list(result['matches'].keys())}")