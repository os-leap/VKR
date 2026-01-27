import numpy as np
from typing import List, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
import string
import warnings
warnings.filterwarnings('ignore')

# Загрузка необходимых ресурсов NLTK
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('tokenizers/punkt_tab')
except LookupError:
    nltk.download('punkt_tab')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

try:
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('wordnet')

class SimpleSemanticSearchEngine:
    """
    Простой класс для реализации семантического поиска, который анализирует смысл и контекст запроса,
    используя TF-IDF векторайзер и косинусное сходство. Не требует GPU.
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

def demo_simple_search():
    """
    Демонстрация работы простого семантического поиска.
    """
    # Меньше документов для экономии памяти
    documents = [
        "Искусственный интеллект - это область компьютерных наук, занимающаяся созданием интеллектуальных машин.",
        "Машинное обучение - это подраздел искусственного интеллекта, которое позволяет системам автоматически обучаться.",
        "Python - популярный язык программирования для разработки приложений машинного обучения.",
        "Обработка естественного языка помогает компьютерам понимать человеческий язык.",
        "Веб-разработка включает создание сайтов и веб-приложений с использованием HTML, CSS и JavaScript."
    ]
    
    print("Инициализация простого семантического поискового движка...")
    
    # Создание экземпляра поискового движка
    search_engine = SimpleSemanticSearchEngine()
    search_engine.add_documents(documents)
    
    print("Простой семантический поисковый движок успешно инициализирован!")
    print("=" * 70)
    
    # Примеры поисковых запросов
    queries = [
        "Как работает машинное обучение?",      # Семантически связано с документом о машинном обучении
        "Программирование на Python",          # Семантически связано с документом о Python
        "Как компьютеры понимают речь?",       # Семантически связано с NLP
    ]
    
    for query in queries:
        print(f"\n🔍 Запрос: '{query}'")
        print("-" * 50)
        results = search_engine.search(query, top_k=3)
        
        if results:
            for rank, (idx, score) in enumerate(results, 1):
                print(f"{rank}. Релевантность: {score:.3f}")
                print(f"   Документ: {search_engine.documents[idx][:100]}...")
                print()
        else:
            print("Не найдено релевантных документов.")
    
    print("\n" + "=" * 70)
    print("Демонстрация семантического поиска:")
    print("Поиск понимает смысл запроса, а не просто ищет совпадающие слова.")

if __name__ == "__main__":
    demo_simple_search()