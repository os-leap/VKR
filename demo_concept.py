import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re

class ConceptualSemanticSearch:
    """
    Упрощенная концептуальная реализация семантического поиска
    для демонстрации принципов работы без использования ресурсоемких библиотек.
    """
    
    def __init__(self):
        self.documents = []
        self.vectorizer = None
        self.tfidf_matrix = None
    
    def simple_preprocess(self, text):
        """Упрощенная предобработка текста"""
        # Приведение к нижнему регистру
        text = text.lower()
        # Удаление пунктуации
        text = re.sub(r'[^\w\s]', ' ', text)
        # Удаление лишних пробелов
        text = ' '.join(text.split())
        return text
    
    def add_documents(self, docs):
        """Добавление документов"""
        self.documents = [self.simple_preprocess(doc) for doc in docs]
        # Создание TF-IDF матрицы
        self.vectorizer = TfidfVectorizer()
        self.tfidf_matrix = self.vectorizer.fit_transform(self.documents)
    
    def search(self, query, top_k=3):
        """Поиск по запросу"""
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

def demonstrate_semantic_search():
    """Демонстрация работы семантического поиска"""
    
    print("Демонстрация концепции семантического поиска")
    print("="*50)
    
    # Пример документов
    documents = [
        "Искусственный интеллект позволяет машинам принимать решения как люди",
        "Машинное обучение - это способность алгоритмов учиться на данных",
        "Python язык программирования используется для разработки ИИ приложений",
        "Обработка естественного языка позволяет компьютерам понимать речь",
        "Веб-разработка создает интерфейсы для взаимодействия с пользователями"
    ]
    
    # Создаем поисковую систему
    search_system = ConceptualSemanticSearch()
    search_system.add_documents(documents)
    
    print("Документы:")
    for i, doc in enumerate(documents):
        print(f"{i+1}. {doc}")
    
    print("\n" + "="*50)
    print("Примеры семантического поиска:")
    print("(система находит смысловые связи, а не просто совпадение слов)")
    
    # Примеры запросов
    queries_examples = [
        ("Как машины могут принимать решения?", "Ожидается документ про ИИ"),
        ("Язык программирования для ИИ", "Ожидается документ про Python"),
        ("Как компьютеры понимают человеческую речь?", "Ожидается документ про обработку языка")
    ]
    
    for query, explanation in queries_examples:
        print(f"\nЗапрос: '{query}'")
        print(f"Ожидаемый результат: {explanation}")
        
        results = search_system.search(query, top_k=2)
        
        if results:
            print("Найденные документы:")
            for rank, (idx, score) in enumerate(results, 1):
                print(f"  {rank}. [{score:.3f}] {search_system.documents[idx]}")
        else:
            print("Не найдено релевантных документов")
    
    print("\n" + "="*50)
    print("Вывод:")
    print("Семантический поиск анализирует смысл и контекст запроса,")
    print("а не просто ищет точное совпадение слов. Это позволяет")
    print("находить релевантные документы даже если они не содержат")
    print("тех же ключевых слов, что и запрос.")

if __name__ == "__main__":
    demonstrate_semantic_search()