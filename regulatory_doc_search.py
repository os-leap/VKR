"""
Модуль для поиска записей в нормативных документах
"""

import json
import re
from typing import List, Dict, Any
from datetime import datetime
import logging

class RegulatoryDocumentSearch:
    """
    Класс для поиска записей в нормативных документах
    """
    
    def __init__(self, documents_path: str = None):
        """
        Инициализация системы поиска
        
        Args:
            documents_path: Путь к файлу с нормативными документами
        """
        self.documents_path = documents_path or "regulatory_documents.json"
        self.documents = []
        self.load_documents()
        
    def load_documents(self):
        """
        Загрузка нормативных документов из файла
        """
        try:
            with open(self.documents_path, 'r', encoding='utf-8') as f:
                self.documents = json.load(f)
        except FileNotFoundError:
            logging.warning(f"Файл {self.documents_path} не найден. Создаю пустой список документов.")
            self.documents = []
        except json.JSONDecodeError:
            logging.error(f"Ошибка чтения JSON из файла {self.documents_path}")
            self.documents = []
    
    def save_documents(self):
        """
        Сохранение нормативных документов в файл
        """
        with open(self.documents_path, 'w', encoding='utf-8') as f:
            json.dump(self.documents, f, ensure_ascii=False, indent=2)
    
    def add_document(self, doc_data: Dict[str, Any]):
        """
        Добавление нового нормативного документа
        
        Args:
            doc_data: Словарь с данными документа
        """
        # Добавляем ID если его нет
        if 'id' not in doc_data:
            doc_data['id'] = len(self.documents) + 1
            
        # Добавляем дату создания если её нет
        if 'created_date' not in doc_data:
            doc_data['created_date'] = datetime.now().isoformat()
            
        self.documents.append(doc_data)
        self.save_documents()
    
    def search_by_keywords(self, keywords: List[str], exact_match: bool = False) -> List[Dict[str, Any]]:
        """
        Поиск документов по ключевым словам
        
        Args:
            keywords: Список ключевых слов для поиска
            exact_match: Точный ли поиск (по умолчанию - частичное совпадение)
            
        Returns:
            Список документов, соответствующих критериям
        """
        results = []
        
        for doc in self.documents:
            found = False
            
            # Проверяем все текстовые поля документа
            for key, value in doc.items():
                if isinstance(value, str):
                    for keyword in keywords:
                        if exact_match:
                            if keyword.lower() in value.lower():
                                found = True
                                break
                        else:
                            if keyword.lower() in value.lower():
                                found = True
                                break
                
                if found:
                    break
            
            if found:
                results.append(doc)
                
        return results
    
    def search_by_attributes(self, attributes: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Поиск документов по атрибутам
        
        Args:
            attributes: Словарь с атрибутами для фильтрации
            
        Returns:
            Список документов, соответствующих критериям
        """
        results = []
        
        for doc in self.documents:
            match = True
            
            for attr_key, attr_value in attributes.items():
                if attr_key not in doc or doc[attr_key] != attr_value:
                    match = False
                    break
            
            if match:
                results.append(doc)
                
        return results
    
    def search_by_date_range(self, start_date: str = None, end_date: str = None) -> List[Dict[str, Any]]:
        """
        Поиск документов по диапазону дат
        
        Args:
            start_date: Начальная дата (в формате ISO 8601)
            end_date: Конечная дата (в формате ISO 8601)
            
        Returns:
            Список документов в заданном диапазоне дат
        """
        results = []
        
        for doc in self.documents:
            doc_date_str = doc.get('date', doc.get('created_date', ''))
            
            if not doc_date_str:
                continue
                
            try:
                doc_date = datetime.fromisoformat(doc_date_str.replace('Z', '+00:00'))
                
                if start_date:
                    start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                    if doc_date < start_dt:
                        continue
                        
                if end_date:
                    end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                    if doc_date > end_dt:
                        continue
                        
                results.append(doc)
                
            except ValueError:
                continue  # Пропускаем документы с некорректной датой
                
        return results
    
    def advanced_search(self, query_params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Расширенный поиск по нескольким критериям
        
        Args:
            query_params: Параметры запроса с различными критериями
            
        Returns:
            Список документов, соответствующих всем критериям
        """
        results = self.documents[:]  # Копируем все документы
        
        # Фильтруем по ключевым словам
        if 'keywords' in query_params and query_params['keywords']:
            keyword_results = self.search_by_keywords(query_params['keywords'])
            results = [doc for doc in results if doc in keyword_results]
        
        # Фильтруем по атрибутам
        if 'attributes' in query_params and query_params['attributes']:
            attr_results = self.search_by_attributes(query_params['attributes'])
            results = [doc for doc in results if doc in attr_results]
        
        # Фильтруем по диапазону дат
        if ('start_date' in query_params and query_params['start_date']) or \
           ('end_date' in query_params and query_params['end_date']):
            start_date = query_params.get('start_date')
            end_date = query_params.get('end_date')
            date_results = self.search_by_date_range(start_date, end_date)
            results = [doc for doc in results if doc in date_results]
        
        # Фильтруем по регулярному выражению
        if 'regex_pattern' in query_params and query_params['regex_pattern']:
            pattern = query_params['regex_pattern']
            filtered_results = []
            
            for doc in results:
                doc_text = ' '.join([str(v) for v in doc.values() if isinstance(v, str)])
                if re.search(pattern, doc_text, re.IGNORECASE):
                    filtered_results.append(doc)
                    
            results = filtered_results
        
        return results
    
    def get_all_documents(self) -> List[Dict[str, Any]]:
        """
        Получение всех документов
        
        Returns:
            Список всех документов
        """
        return self.documents
    
    def get_document_by_id(self, doc_id: int) -> Dict[str, Any]:
        """
        Получение документа по ID
        
        Args:
            doc_id: ID документа
            
        Returns:
            Документ с указанным ID или None
        """
        for doc in self.documents:
            if doc.get('id') == doc_id:
                return doc
        return None


def main():
    """
    Пример использования класса RegulatoryDocumentSearch
    """
    # Создаем экземпляр класса
    search_system = RegulatoryDocumentSearch("regulatory_documents.json")
    
    # Пример добавления документа
    sample_doc = {
        "title": "Приказ Минздрава от 15.03.2023 №123",
        "document_type": "приказ",
        "organization": "Министерство здравоохранения",
        "date": "2023-03-15",
        "content": "Настоящий приказ устанавливает новые правила обращения с лекарственными средствами",
        "status": "действует"
    }
    
    search_system.add_document(sample_doc)
    
    # Пример поиска по ключевым словам
    results = search_system.search_by_keywords(["лекарственные средства", "правила"])
    print(f"Найдено документов по ключевым словам: {len(results)}")
    
    # Пример расширенного поиска
    query = {
        "keywords": ["приказ", "Минздрав"],
        "attributes": {"status": "действует"},
        "start_date": "2023-01-01",
        "end_date": "2023-12-31"
    }
    
    advanced_results = search_system.advanced_search(query)
    print(f"Результатов расширенного поиска: {len(advanced_results)}")


if __name__ == "__main__":
    main()