"""
Модуль для поиска записей в нормативных документах формата PDF
"""

import json
import re
from typing import List, Dict, Any
from datetime import datetime
import logging
import PyPDF2
import os

class PDFRegulatorySearch:
    """
    Класс для поиска записей в нормативных документах формата PDF
    """

    def __init__(self, pdf_docs_path: str = None):
        """
        Инициализация системы поиска в PDF

        Args:
            pdf_docs_path: Путь к файлу со списком PDF-документов
        """
        self.pdf_docs_path = pdf_docs_path or "pdf_documents.json"
        self.pdf_documents = []
        self.load_pdf_documents()

    def load_pdf_documents(self):
        """
        Загрузка списка PDF-документов из файла
        """
        try:
            with open(self.pdf_docs_path, 'r', encoding='utf-8') as f:
                self.pdf_documents = json.load(f)
        except FileNotFoundError:
            logging.warning(f"Файл {self.pdf_docs_path} не найден. Создаю пустой список документов.")
            self.pdf_documents = []
        except json.JSONDecodeError:
            logging.error(f"Ошибка чтения JSON из файла {self.pdf_docs_path}")
            self.pdf_documents = []

    def save_pdf_documents(self):
        """
        Сохранение списка PDF-документов в файл
        """
        with open(self.pdf_docs_path, 'w', encoding='utf-8') as f:
            json.dump(self.pdf_documents, f, ensure_ascii=False, indent=2)

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """
        Извлечение текста из PDF-файла

        Args:
            pdf_path: Путь к PDF-файлу

        Returns:
            Текст из PDF-файла
        """
        text = ""
        try:
            # Путь к файлу PDF должен быть в папке uploads
            full_pdf_path = os.path.join("static", "uploads", pdf_path)
            
            if not os.path.exists(full_pdf_path):
                logging.warning(f"PDF-файл не найден: {full_pdf_path}")
                return text
                
            with open(full_pdf_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page_num in range(len(reader.pages)):
                    page = reader.pages[page_num]
                    text += page.extract_text()
        except Exception as e:
            logging.error(f"Ошибка при извлечении текста из PDF {pdf_path}: {str(e)}")
            
        return text

    def search_by_keywords_in_pdf(self, keywords: List[str], exact_match: bool = False) -> List[Dict[str, Any]]:
        """
        Поиск документов по ключевым словам в содержимом PDF

        Args:
            keywords: Список ключевых слов для поиска
            exact_match: Точный ли поиск (по умолчанию - частичное совпадение)

        Returns:
            Список документов, соответствующих критериям
        """
        results = []

        for doc in self.pdf_documents:
            filename = doc.get("filename", "")
            if not filename:
                continue

            # Извлекаем текст из PDF
            pdf_text = self.extract_text_from_pdf(filename)
            
            if not pdf_text:
                continue

            found = False
            
            # Проверяем наличие ключевых слов в тексте PDF
            for keyword in keywords:
                if exact_match:
                    if keyword.lower() in pdf_text.lower():
                        found = True
                        break
                else:
                    if keyword.lower() in pdf_text.lower():
                        found = True
                        break

            if found:
                # Добавляем информацию о найденных совпадениях
                doc_copy = doc.copy()
                doc_copy["matched_keywords"] = [
                    kw for kw in keywords 
                    if kw.lower() in pdf_text.lower()
                ]
                results.append(doc_copy)

        return results

    def search_by_pdf_attributes(self, attributes: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Поиск документов по атрибутам в информации о PDF-документах

        Args:
            attributes: Словарь с атрибутами для фильтрации

        Returns:
            Список документов, соответствующих критериям
        """
        results = []

        for doc in self.pdf_documents:
            match = True

            for attr_key, attr_value in attributes.items():
                if attr_key not in doc or doc[attr_key] != attr_value:
                    match = False
                    break

            if match:
                results.append(doc)

        return results

    def advanced_pdf_search(self, query_params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Расширенный поиск по нескольким критериям в PDF-документах

        Args:
            query_params: Параметры запроса с различными критериями

        Returns:
            Список документов, соответствующих всем критериям
        """
        results = self.pdf_documents[:]  # Копируем все документы

        # Фильтруем по ключевым словам в содержимом PDF
        if 'keywords' in query_params and query_params['keywords']:
            keyword_results = self.search_by_keywords_in_pdf(query_params['keywords'])
            results = [doc for doc in results if doc in keyword_results]

        # Фильтруем по атрибутам документа
        if 'attributes' in query_params and query_params['attributes']:
            attr_results = self.search_by_pdf_attributes(query_params['attributes'])
            results = [doc for doc in results if doc in attr_results]

        # Фильтруем по регулярному выражению
        if 'regex_pattern' in query_params and query_params['regex_pattern']:
            pattern = query_params['regex_pattern']
            filtered_results = []

            for doc in results:
                filename = doc.get("filename", "")
                if filename:
                    pdf_text = self.extract_text_from_pdf(filename)
                    if re.search(pattern, pdf_text, re.IGNORECASE):
                        filtered_results.append(doc)

            results = filtered_results

        return results

    def get_all_pdf_documents(self) -> List[Dict[str, Any]]:
        """
        Получение всех PDF-документов

        Returns:
            Список всех PDF-документов
        """
        return self.pdf_documents

    def get_pdf_document_by_id(self, doc_id: int) -> Dict[str, Any]:
        """
        Получение PDF-документа по ID

        Args:
            doc_id: ID документа

        Returns:
            Документ с указанным ID или None
        """
        for doc in self.pdf_documents:
            if doc.get('id') == doc_id:
                return doc
        return None


def main():
    """
    Пример использования класса PDFRegulatorySearch
    """
    # Создаем экземпляр класса
    pdf_search = PDFRegulatorySearch("pdf_documents.json")

    # Пример поиска по ключевым словам в PDF
    results = pdf_search.search_by_keywords_in_pdf(["образование", "ФГОС"])
    print(f"Найдено документов по ключевым словам: {len(results)}")

    # Пример расширенного поиска
    query = {
        "keywords": ["приказ", "Минпросвещения"],
        "attributes": {"extracted_title": "МИНИСТЕРСТВО ПРОСВЕЩЕНИЯ РОССИЙСКОЙ ФЕДЕРАЦИИ"}
    }

    advanced_results = pdf_search.advanced_pdf_search(query)
    print(f"Результатов расширенного поиска: {len(advanced_results)}")


if __name__ == "__main__":
    main()