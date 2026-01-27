"""
Модуль интеграции упрощенного семантического поиска в основное приложение
"""
import numpy as np
from typing import List, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re


class SimpleIntegratedSearchSystem:
    """
    Упрощенная интегрированная система поиска, объединяющая синтаксический и семантический подходы
    """
    
    def __init__(self, data_file="knowledge_base.json"):
        """
        Инициализация системы поиска
        
        Args:
            data_file: путь к файлу с базой знаний
        """
        self.data_file = data_file
        self.vectorizer = TfidfVectorizer()
        self.tfidf_matrix = None
        self.documents = []
        self.data = []
        
    def simple_preprocess(self, text):
        """Упрощенная предобработка текста"""
        # Приведение к нижнему регистру
        text = text.lower()
        # Удаление пунктуации
        text = re.sub(r'[^\w\s]', ' ', text)
        # Удаление лишних пробелов
        text = ' '.join(text.split())
        return text
        
    def load_documents(self, data: List[dict]):
        """
        Загрузка документов из базы знаний для семантического поиска
        
        Args:
            data: список документов из базы знаний
        """
        self.data = data
        # Подготовка документов для семантического поиска
        # Объединяем заголовок и содержание для лучшего понимания контекста
        semantic_docs = []
        for entry in data:
            combined_text = f"{entry.get('title', '')} {entry.get('content', '')}"
            processed_text = self.simple_preprocess(combined_text.strip())
            semantic_docs.append(processed_text)
        
        self.documents = semantic_docs
        
        # Создание TF-IDF матрицы
        if semantic_docs:
            self.tfidf_matrix = self.vectorizer.fit_transform(semantic_docs)
        
    def semantic_search(self, query: str, top_k: int = 5) -> List[Tuple[int, float]]:
        """
        Выполнение семантического поиска
        
        Args:
            query: поисковый запрос
            top_k: количество возвращаемых результатов
            
        Returns:
            Список кортежей (индекс документа, оценка релевантности)
        """
        if not self.documents or self.tfidf_matrix is None:
            return []
        
        processed_query = self.simple_preprocess(query)
        query_vec = self.vectorizer.transform([processed_query])
        
        # Вычисление косинусного сходства
        similarities = cosine_similarity(query_vec, self.tfidf_matrix).flatten()
        
        # Получение топ-k результатов
        top_indices = similarities.argsort()[-top_k:][::-1]
        
        results = []
        for idx in top_indices:
            if similarities[idx] > 0:
                results.append((idx, similarities[idx]))
        
        return results
    
    def get_document_by_index(self, idx: int) -> dict:
        """
        Получение оригинального документа по индексу
        
        Args:
            idx: индекс документа
            
        Returns:
            Оригинальный документ из базы знаний
        """
        if 0 <= idx < len(self.data):
            return self.data[idx]
        return None


# Глобальная переменная для хранения системы поиска
search_system = SimpleIntegratedSearchSystem()


def initialize_search_system(data: List[dict]):
    """
    Инициализация системы поиска с данными
    
    Args:
        data: список документов из базы знаний
    """
    search_system.load_documents(data)


def perform_integrated_search(query: str, search_type: str = "semantic", top_k: int = 10) -> List[dict]:
    """
    Выполнение интегрированного поиска
    
    Args:
        query: поисковый запрос
        search_type: тип поиска ("semantic", "syntax", "combined")
        top_k: количество возвращаемых результатов
        
    Returns:
        Список найденных документов
    """
    if search_type == "semantic":
        # Семантический поиск
        results = search_system.semantic_search(query, top_k)
        found_entries = []
        for idx, score in results:
            entry = search_system.get_document_by_index(idx)
            if entry:
                # Добавляем оценку релевантности к документу
                entry_with_score = entry.copy()
                entry_with_score['relevance_score'] = float(score)
                found_entries.append(entry_with_score)
        return found_entries
    
    # Здесь можно добавить другие типы поиска (синтаксический, комбинированный)
    return []


# Функция для синтаксического поиска (скопирована из app.py для полноты)
def syntax_aware_search(text, query):
    """
    Performs syntax-aware search supporting:
    - AND operator: "word1 AND word2"
    - OR operator: "word1 OR word2" 
    - NOT operator: "word1 NOT word2"
    - Phrase search: "word1 word2" (both words present)
    - Quoted phrases: "\"exact phrase\""
    """
    import re
    # Normalize text and query to lowercase
    text_lower = text.lower()
    query = query.strip()
    
    # Handle quoted phrases first
    quoted_phrases = re.findall(r'\"([^\"]*)\"', query)
    query_without_quotes = re.sub(r'\"[^\"]*\"', '', query)
    
    # Check if all quoted phrases are present in the text
    for phrase in quoted_phrases:
        phrase = phrase.strip().lower()
        if phrase and phrase not in text_lower:
            return False
    
    # Process the remaining query without quotes
    terms = query_without_quotes.strip()
    if not terms:
        return len(quoted_phrases) > 0  # If only quotes were provided, return True if they matched
    
    # Split by AND, OR, NOT operators while preserving them
    parts = re.split(r'\s+(AND|OR|NOT)\s+', terms, flags=re.IGNORECASE)
    
    # Process parts with operators
    i = 0
    result = True  # Start with True for AND logic
    operator = 'AND'  # Default operator
    
    while i < len(parts):
        part = parts[i].strip()
        
        if part.upper() in ['AND', 'OR', 'NOT']:
            operator = part.upper()
        else:
            term = part.strip().lower()
            if term:
                term_exists = term in text_lower
                
                if operator == 'AND':
                    result = result and term_exists
                elif operator == 'OR':
                    if i == 0:  # First term, initialize result
                        result = term_exists
                    else:
                        result = result or term_exists
                elif operator == 'NOT':
                    result = result and not term_exists
        
        i += 1
    
    return result