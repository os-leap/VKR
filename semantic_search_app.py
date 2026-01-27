import numpy as np
from typing import List, Dict, Tuple
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
import string
import pickle
import os

# Загрузка необходимых ресурсов NLTK
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

try:
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('wordnet')

class SemanticSearchEngine:
    """
    Класс для реализации семантического поиска, который анализирует смысл и контекст запроса,
    используя TF-IDF векторайзер и косинусное сходство.
    """
    
    def __init__(self):
        self.documents = []
        self.processed_docs = []
        self.vectorizer = None
        self.doc_vectors = None
        self.lemmatizer = WordNetLemmatizer()
        self.stop_words = set(stopwords.words('english')).union(set(stopwords.words('russian')))
        
    def preprocess_text(self, text: str) -> str:
        """
        Предварительная обработка текста: приведение к нижнему регистру,
        удаление пунктуации, лемматизация и удаление стоп-слов.
        """
        # Приведение к нижнему регистру
        text = text.lower()
        
        # Удаление пунктуации
        text = text.translate(str.maketrans('', '', string.punctuation))
        
        # Токенизация
        tokens = word_tokenize(text)
        
        # Удаление стоп-слов и лемматизация
        tokens = [self.lemmatizer.lemmatize(token) for token in tokens 
                  if token not in self.stop_words and token.isalpha()]
        
        return ' '.join(tokens)
    
    def add_documents(self, documents: List[str]):
        """
        Добавление документов в поисковый индекс.
        """
        self.documents = documents
        self.processed_docs = [self.preprocess_text(doc) for doc in documents]
        
        # Создание векторизатора и векторов документов
        self.vectorizer = TfidfVectorizer()
        self.doc_vectors = self.vectorizer.fit_transform(self.processed_docs)
    
    def search(self, query: str, top_k: int = 5) -> List[Tuple[int, float]]:
        """
        Поиск наиболее релевантных документов для запроса.
        
        Args:
            query: Поисковый запрос
            top_k: Количество возвращаемых результатов
            
        Returns:
            Список кортежей (индекс документа, оценка релевантности)
        """
        if not self.vectorizer:
            raise ValueError("Нет загруженных документов. Используйте метод add_documents() сначала.")
            
        processed_query = self.preprocess_text(query)
        query_vector = self.vectorizer.transform([processed_query])
        
        # Вычисление косинусного сходства между запросом и документами
        similarities = cosine_similarity(query_vector, self.doc_vectors).flatten()
        
        # Получение индексов топ-K наиболее похожих документов
        top_indices = similarities.argsort()[-top_k:][::-1]
        
        # Возврат пар (индекс, сходство) для топ-K результатов
        results = [(idx, similarities[idx]) for idx in top_indices if similarities[idx] > 0]
        
        return results
    
    def save_model(self, filepath: str):
        """
        Сохранение модели в файл.
        """
        model_data = {
            'documents': self.documents,
            'processed_docs': self.processed_docs,
            'vectorizer': self.vectorizer,
            'doc_vectors': self.doc_vectors
        }
        with open(filepath, 'wb') as f:
            pickle.dump(model_data, f)
    
    def load_model(self, filepath: str):
        """
        Загрузка модели из файла.
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Файл {filepath} не найден.")
            
        with open(filepath, 'rb') as f:
            model_data = pickle.load(f)
        
        self.documents = model_data['documents']
        self.processed_docs = model_data['processed_docs']
        self.vectorizer = model_data['vectorizer']
        self.doc_vectors = model_data['doc_vectors']

def main():
    """
    Демонстрация работы семантического поиска.
    """
    # Пример документов
    documents = [
        "Искусственный интеллект - это область компьютерных наук, занимающаяся созданием интеллектуальных машин.",
        "Машинное обучение - это подраздел искусственного интеллекта, которое позволяет системам автоматически обучаться и улучшаться.",
        "Глубокое обучение использует нейронные сети для анализа сложных паттернов в данных.",
        "Python - популярный язык программирования для разработки приложений машинного обучения.",
        "Обработка естественного языка помогает компьютерам понимать человеческий язык.",
        "Веб-разработка включает создание сайтов и веб-приложений с использованием HTML, CSS и JavaScript.",
        "Базы данных используются для хранения и управления структурированными данными.",
        "Алгоритмы сортировки позволяют эффективно упорядочивать данные в определенном порядке."
    ]
    
    # Создание экземпляра поискового движка
    search_engine = SemanticSearchEngine()
    search_engine.add_documents(documents)
    
    print("Семантический поисковый движок успешно инициализирован!")
    print("=" * 60)
    
    # Примеры поисковых запросов
    queries = [
        "Как работает машинное обучение?",
        "Программирование на Python",
        "Создание веб-сайтов",
        "Хранение информации",
        "Нейронные сети"
    ]
    
    for query in queries:
        print(f"\nЗапрос: '{query}'")
        print("-" * 30)
        results = search_engine.search(query, top_k=3)
        
        if results:
            for idx, score in results:
                print(f"Релевантность: {score:.3f}")
                print(f"Документ: {search_engine.documents[idx]}")
                print()
        else:
            print("Не найдено релевантных документов.")

if __name__ == "__main__":
    main()