import numpy as np
from typing import List, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
import string
import pickle
import os
import json
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
    
    def __init__(self, knowledge_base_file="knowledge_base.json"):
        self.documents = []
        self.processed_docs = []
        self.vectorizer = None
        self.doc_vectors = None
        self.lemmatizer = WordNetLemmatizer()
        self.stop_words = set(stopwords.words('english')).union(set(stopwords.words('russian')))
        self.knowledge_base_file = knowledge_base_file
        self.entries_data = []  # Добавляем хранилище для данных записей
        
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
    
    def add_documents(self, documents: List[str], entries_data: List[dict] = None):
        """
        Добавление документов в поисковый индекс.
        """
        self.documents = documents
        self.processed_docs = [self.preprocess_text(doc) for doc in documents]
        
        # Создание векторизатора и векторов документов
        self.vectorizer = TfidfVectorizer()
        self.doc_vectors = self.vectorizer.fit_transform(self.processed_docs)
        
        # Сохраняем данные записей, если они предоставлены
        if entries_data is not None:
            self.entries_data = entries_data
        else:
            # Если entries_data не предоставлены, загружаем из файла
            self.entries_data = self._load_entries_data()
    
    def _load_entries_data(self):
        """Загружает данные записей из JSON файла"""
        try:
            with open(self.knowledge_base_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Файл {self.knowledge_base_file} не найден.")
            return []
        except json.JSONDecodeError:
            print(f"Ошибка чтения JSON из файла {self.knowledge_base_file}.")
            return []
    
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
        
        # Если в запросе есть метки (например, "10 класс химия"), добавляем соответствующие документы
        label_results = self._search_by_labels(query)
        combined_results = self._combine_results(results, label_results, len(similarities))
        
        # Возвращаем топ-K результатов из объединенного списка
        combined_top_indices = sorted(combined_results, key=lambda x: x[1], reverse=True)[:top_k]
        
        return combined_top_indices
    
    def _search_by_labels(self, query: str) -> List[Tuple[int, float]]:
        """
        Поиск по меткам (класс, предмет и т.д.)
        """
        results = []
        
        # Парсим запрос на наличие меток
        query_lower = query.lower()
        
        # Проверяем, содержит ли запрос информацию о классе и предмете
        class_match = None
        subject_match = None
        
        # Ищем возможные обозначения класса
        for i in range(1, 12):
            if str(i) in query_lower and ('класс' in query_lower or 'grade' in query_lower):
                class_match = str(i)
                break
                
        # Ищем возможные обозначения предмета
        subjects = ["математика", "русский", "литература", "история", "география", 
                   "биология", "химия", "физика", "информатика", "английский", 
                   "немецкий", "французский", "обществознание", "экономика",
                   "право", "обж", "физкультура", "izo", "музыка", "технология"]
        
        for subject in subjects:
            if subject in query_lower:
                subject_match = subject
                break
        
        # Если нашли метки, ищем соответствующие документы
        for idx, entry in enumerate(self.entries_data):
            # Проверяем новые метки (образовательная информация)
            edu_info = entry.get("education_info", {})
            entry_class = str(edu_info.get("class")) if edu_info.get("class") else None
            entry_subject = edu_info.get("subject", "").lower()
            
            # Также проверяем старое поле topic
            entry_topic = entry.get("topic", "").lower()
            
            # Если есть совпадение по классу и предмету, добавляем документ
            if ((class_match and entry_class == class_match) and 
                (subject_match and subject_match in entry_subject)):
                results.append((idx, 1.0))  # Высокий вес для точного совпадения по меткам
            elif class_match and entry_class == class_match:
                results.append((idx, 0.8))  # Средний вес для совпадения только по классу
            elif subject_match and subject_match in entry_subject:
                results.append((idx, 0.8))  # Средний вес для совпадения только по предмету
            # Также проверяем совпадение с темой (topic)
            elif subject_match and subject_match in entry_topic:
                results.append((idx, 0.6))  # Немного меньший вес для совпадения по теме
        
        return results
    
    def _combine_results(self, semantic_results: List[Tuple[int, float]], 
                        label_results: List[Tuple[int, float]], 
                        total_docs: int) -> List[Tuple[int, float]]:
        """
        Объединение результатов семантического поиска и поиска по меткам
        """
        # Создаем массив с начальными весами
        combined_scores = np.zeros(total_docs)
        
        # Добавляем веса из семантического поиска
        for idx, score in semantic_results:
            combined_scores[idx] += score
            
        # Добавляем веса из поиска по меткам (с более высоким коэффициентом)
        for idx, score in label_results:
            combined_scores[idx] += score * 1.5  # Увеличиваем вес для меток
            
        # Формируем результаты
        results = [(i, combined_scores[i]) for i in range(total_docs) if combined_scores[i] > 0]
        
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
        
        # При загрузке модели также загружаем данные записей
        self.entries_data = self._load_entries_data()

def demo_simple_search():
    """
    Демонстрация работы простого семантического поиска.
    """
    # Загрузка данных из knowledge_base.json
    try:
        with open("knowledge_base.json", "r", encoding="utf-8") as f:
            knowledge_base = json.load(f)
    except FileNotFoundError:
        print("Файл knowledge_base.json не найден. Используем примеры по умолчанию.")
        knowledge_base = []
    
    # Подготовка документов для поиска из знаний
    if knowledge_base:
        documents = []
        entries_data = []
        for entry in knowledge_base:
            # Создаем документ из заголовка и содержимого
            doc_text = f"{entry.get('title', '')} {entry.get('content', '')}"
            documents.append(doc_text)
            entries_data.append(entry)  # Сохраняем полные данные записи
    else:
        # Пример документов по умолчанию
        documents = [
            "Искусственный интеллект - это область компьютерных наук, занимающаяся созданием интеллектуальных машин.",
            "Машинное обучение - это подраздел искусственного интеллекта, которое позволяет системам автоматически обучаться и улучшаться.",
            "Глубокое обучение использует нейронные сети для анализа сложных паттернов в данных.",
            "Python - популярный язык программирования для разработки приложений машинного обучения.",
            "Обработка естественного языка помогает компьютерам понимать человеческий язык.",
            "Веб-разработка включает создание сайтов и веб-приложений с использованием HTML, CSS и JavaScript.",
            "Базы данных используются для хранения и управления структурированными данными.",
            "Алгоритмы сортировки позволяют эффективно упорядочивать данные в определенном порядке.",
            "Квантовые вычисления представляют собой парадигму вычислений, основанную на квантовой механике.",
            "Блокчейн - это распределенная технология хранения данных, обеспечивающая безопасность и прозрачность."
        ]
        entries_data = None
    
    print("Инициализация простого семантического поискового движка...")
    
    # Создание экземпляра поискового движка
    search_engine = SimpleSemanticSearchEngine()
    search_engine.add_documents(documents, entries_data)
    
    print("Простой семантический поисковый движок успешно инициализирован!")
    print("=" * 70)
    
    # Примеры поисковых запросов, демонстрирующих семантическое понимание
    queries = [
        "Как работает машинное обучение?",      # Семантически связано с документом о машинном обучении
        "Программирование на Python",          # Семантически связано с документом о Python
        "Создание веб-сайтов",                 # Семантически связано с документом о веб-разработке
        "Хранение информации",                 # Семантически связано с документом о базах данных
        "Нейронные сети",                      # Семантически связано с документом о глубоком обучении
        "Как компьютеры понимают речь?",       # Семантически связано с NLP
        "Упорядочивание данных",               # Семантически связано с алгоритмами сортировки
        "10 класс химия",                      # Пример запроса с метками
        "задание для 10 класса по химии"       # Еще один пример запроса с метками
    ]
    
    for query in queries:
        print(f"\n🔍 Запрос: '{query}'")
        print("-" * 50)
        results = search_engine.search(query, top_k=3)
        
        if results:
            for rank, (idx, score) in enumerate(results, 1):
                print(f"{rank}. Релевантность: {score:.3f}")
                if idx < len(search_engine.documents):
                    print(f"   Документ: {search_engine.documents[idx][:100]}...")
                if entries_data and idx < len(entries_data):
                    entry = entries_data[idx]
                    edu_info = entry.get("education_info", {})
                    if edu_info:
                        class_val = edu_info.get("class", "Не указан")
                        subject = edu_info.get("subject", "Не указан")
                        print(f"   Метки: Класс: {class_val}, Предмет: {subject}")
                print()
        else:
            print("Не найдено релевантных документов.")

    print("\n" + "=" * 70)
    print("Демонстрация различий между семантическим и точным поиском:")
    print("Семантический поиск находит смысловые связи даже если ключевые слова не совпадают напрямую.")

def compare_approaches():
    """
    Сравнение подходов: семантический поиск vs точное совпадение
    """
    print("\nСравнение подходов:")
    print("1. Точный поиск: ищет документы с совпадающими словами")
    print("2. Семантический поиск: понимает смысл и контекст запроса")
    print("\nПример:")
    print("Запрос: 'Как компьютеры понимают человеческую речь?'")
    print("Точный поиск может не найти: 'Обработка естественного языка помогает компьютерам понимать человеческий язык'")
    print("Семантический поиск найдет этот документ благодаря пониманию смысла!")

if __name__ == "__main__":
    demo_simple_search()
    compare_approaches()