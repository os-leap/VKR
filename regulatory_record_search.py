"""
Модуль для поиска записей внутри нормативных документов
"""

import json
import re
from typing import List, Dict, Any
from datetime import datetime
import logging

class RegulatoryRecordSearch:
    """
    Класс для поиска записей внутри нормативных документов
    """

    def __init__(self, documents_path: str = None):
        """
        Инициализация системы поиска записей

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

    def search_records_in_documents(self, search_term: str, field_to_search: str = "content") -> List[Dict[str, Any]]:
        """
        Поиск записей внутри документов по указанному полю

        Args:
            search_term: Поисковый термин для поиска в записях
            field_to_search: Поле документа, в котором осуществляется поиск (по умолчанию 'content')

        Returns:
            Список документов, содержащих искомую запись
        """
        results = []

        for doc in self.documents:
            # Проверяем наличие искомого термина в указанном поле документа
            field_content = doc.get(field_to_search, "")
            
            if isinstance(field_content, str) and search_term.lower() in field_content.lower():
                # Если нашли совпадение, добавляем документ в результаты
                results.append(doc)
            elif isinstance(field_content, list):
                # Если поле содержит список записей, проверяем каждую запись
                matching_records = [
                    record for record in field_content
                    if isinstance(record, str) and search_term.lower() in record.lower()
                ]
                
                if matching_records:
                    # Создаем копию документа с только подходящими записями
                    doc_copy = doc.copy()
                    doc_copy[field_to_search] = matching_records
                    results.append(doc_copy)

        return results

    def search_records_by_multiple_fields(self, search_params: Dict[str, str]) -> List[Dict[str, Any]]:
        """
        Поиск записей по нескольким полям документа

        Args:
            search_params: Словарь с парами поле-значение для поиска

        Returns:
            Список документов, соответствующих всем критериям
        """
        results = []

        for doc in self.documents:
            match = True
            
            for field, search_term in search_params.items():
                field_value = doc.get(field, "")
                
                if isinstance(field_value, str):
                    if search_term.lower() not in field_value.lower():
                        match = False
                        break
                elif isinstance(field_value, list):
                    # Если значение является списком, проверяем хотя бы одно совпадение
                    found = any(
                        search_term.lower() in str(item).lower()
                        for item in field_value
                    )
                    if not found:
                        match = False
                        break
                else:
                    if search_term.lower() not in str(field_value).lower():
                        match = False
                        break
            
            if match:
                results.append(doc)

        return results

    def search_records_by_regex(self, pattern: str, field_to_search: str = "content") -> List[Dict[str, Any]]:
        """
        Поиск записей с использованием регулярных выражений

        Args:
            pattern: Регулярное выражение для поиска
            field_to_search: Поле документа, в котором осуществляется поиск

        Returns:
            Список документов, содержащих записи, соответствующие шаблону
        """
        results = []

        for doc in self.documents:
            field_content = doc.get(field_to_search, "")
            
            if isinstance(field_content, str):
                if re.search(pattern, field_content, re.IGNORECASE):
                    results.append(doc)
            elif isinstance(field_content, list):
                matching_records = [
                    record for record in field_content
                    if isinstance(record, str) and re.search(pattern, record, re.IGNORECASE)
                ]
                
                if matching_records:
                    doc_copy = doc.copy()
                    doc_copy[field_to_search] = matching_records
                    results.append(doc_copy)

        return results

    def search_records_by_date_and_content(self, search_term: str, start_date: str = None, end_date: str = None) -> List[Dict[str, Any]]:
        """
        Поиск записей по содержанию и диапазону дат

        Args:
            search_term: Поисковый термин
            start_date: Начальная дата (в формате ISO 8601)
            end_date: Конечная дата (в формате ISO 8601)

        Returns:
            Список документов, соответствующих критериям
        """
        results = []

        for doc in self.documents:
            # Проверяем совпадение по содержанию
            content = doc.get("content", "")
            title = doc.get("title", "")
            
            has_content_match = (
                isinstance(content, str) and search_term.lower() in content.lower()
            ) or (
                isinstance(title, str) and search_term.lower() in title.lower()
            )
            
            if not has_content_match:
                continue

            # Проверяем соответствие дате
            doc_date_str = doc.get('date', doc.get('created_date', ''))
            
            if not doc_date_str:
                results.append(doc)
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
                # Пропускаем документы с некорректной датой, но только если не заданы ограничения по дате
                if not start_date and not end_date:
                    results.append(doc)

        return results

    def extract_specific_records(self, doc_id: int, search_term: str = None) -> List[str]:
        """
        Извлечение конкретных записей из документа по ID

        Args:
            doc_id: ID документа
            search_term: Опциональный поисковый термин для фильтрации записей

        Returns:
            Список записей из указанного документа
        """
        for doc in self.documents:
            if doc.get('id') == doc_id:
                content = doc.get('content', '')
                
                if isinstance(content, str):
                    if not search_term or search_term.lower() in content.lower():
                        return [content]
                elif isinstance(content, list):
                    if search_term:
                        return [
                            record for record in content
                            if isinstance(record, str) and search_term.lower() in record.lower()
                        ]
                    else:
                        return content
        
        return []


def main():
    """
    Пример использования класса RegulatoryRecordSearch
    """
    # Создаем экземпляр класса
    record_search = RegulatoryRecordSearch("regulatory_documents.json")

    # Пример поиска записей по ключевому слову
    medication_results = record_search.search_records_in_documents("лекарственные средства")
    print(f"Найдено документов с записями о 'лекарственные средства': {len(medication_results)}")

    # Пример поиска по нескольким полям
    multi_field_query = {
        "title": "приказ",
        "content": "правила"
    }
    multi_results = record_search.search_records_by_multiple_fields(multi_field_query)
    print(f"Найдено документов по нескольким критериям: {len(multi_results)}")

    # Пример поиска с использованием регулярных выражений
    regex_results = record_search.search_records_by_regex(r"[Лл]екарственн\w+\s[Сс]редств\w+")
    print(f"Найдено документов по регулярному выражению: {len(regex_results)}")

    # Пример поиска по дате и содержанию
    date_content_results = record_search.search_records_by_date_and_content(
        "приказ", 
        start_date="2023-01-01", 
        end_date="2023-12-31"
    )
    print(f"Найдено документов по дате и содержанию: {len(date_content_results)}")


if __name__ == "__main__":
    main()