"""Refined priority-based search system with improved relevance filtering"""

import re
from difflib import SequenceMatcher
from typing import List, Dict, Any


class PriorityMaterial:
    """Class for representing material with priority-based search capabilities"""
    def __init__(self, title: str, content: str, file_name: str = "",
                 description: str = "", grade: int = None, subject: str = "",
                 tags: List[str] = None):
        self.title = title
        self.content = content
        self.file_name = file_name
        self.description = description
        self.grade = grade
        self.subject = subject
        self.tags = tags or []

    def __repr__(self):
        return f"PriorityMaterial(title='{self.title}', subject='{self.subject}', grade={self.grade})"


class RefinedSearchSystem:
    """Search system that prioritizes results based on field importance and filters by relevance"""

    def __init__(self, min_relevance_threshold=0.5):
        """
        Initialize search system
        
        Args:
            min_relevance_threshold: Minimum combined relevance score to include in results
        """
        self.materials = []
        self.min_relevance_threshold = min_relevance_threshold

    def add_material(self, material: PriorityMaterial):
        """Add material to the search system"""
        self.materials.append(material)

    def search_with_priority(self, query: str) -> List[Dict[str, Any]]:
        """
        Search with priority ranking and relevance filtering:
        1. Title matches (highest priority)
        2. Content matches (medium priority)
        3. Description matches (medium-low priority)
        4. File name matches (lowest priority)
        
        Only returns results above minimum relevance threshold
        """
        query_lower = query.lower()
        results = []

        for material in self.materials:
            # Calculate scores for each field with different priorities
            title_score = self._calculate_field_score(query_lower, material.title or "")
            content_score = self._calculate_field_score(query_lower, material.content or "")
            file_score = self._calculate_field_score(query_lower, material.file_name or "")
            desc_score = self._calculate_field_score(query_lower, material.description or "")

            # Check if there's at least some meaningful match in any field
            max_field_score = max(title_score, content_score, file_score, desc_score)
            
            # Skip if no field has meaningful match
            if max_field_score < 0.2:
                continue

            # Assign weights based on priority
            weighted_score = (
                title_score * 3.0 +    # Title gets highest weight
                content_score * 2.0 +  # Content gets medium weight
                desc_score * 1.5 +     # Description gets medium-low weight
                file_score * 1.0       # File name gets lowest weight
            )

            # Only include results with sufficient overall relevance
            if weighted_score >= self.min_relevance_threshold and max_field_score >= 0.2:
                results.append({
                    'material': material,
                    'score': weighted_score,
                    'title_match': title_score,
                    'content_match': content_score,
                    'file_match': file_score,
                    'description_match': desc_score
                })

        # Sort by weighted score (highest first)
        results.sort(key=lambda x: x['score'], reverse=True)
        return results

    def _calculate_field_score(self, query: str, text: str) -> float:
        """
        Calculate similarity score between query and text
        Returns 0.0-1.0 where higher is more similar
        """
        if not query or not text:
            return 0.0

        # Use SequenceMatcher for better similarity calculation
        matcher = SequenceMatcher(None, query, text.lower())
        base_score = matcher.ratio()

        # Boost score if exact phrase match exists
        if query in text.lower():
            base_score = min(1.0, base_score * 1.5)

        # Boost score if individual words match
        query_words = query.split()
        word_matches = sum(1 for word in query_words if word in text.lower())
        if word_matches == len(query_words):
            base_score = min(1.0, base_score * 1.2)

        # Additional boost for exact word matches (not just substrings)
        exact_word_matches = 0
        text_words = text.lower().split()
        for word in query_words:
            if word in text_words:
                exact_word_matches += 1
        if exact_word_matches > 0:
            base_score = min(1.0, base_score * (1 + (exact_word_matches / len(query_words)) * 0.3))

        return base_score

    def set_relevance_threshold(self, threshold: float):
        """
        Adjust the minimum relevance threshold
        
        Args:
            threshold: Value between 0.0 and 1.0
        """
        self.min_relevance_threshold = max(0.0, min(1.0, threshold))


# Example usage and test
if __name__ == "__main__":
    # Create search system
    search_system = RefinedSearchSystem(min_relevance_threshold=0.6)

    # Add example materials
    materials = [
        PriorityMaterial(
            title="Алгебраические выражения 8 класс",
            content="В этой статье рассматриваются основные алгебраические выражения и их применение в 8 классе",
            file_name="algebra_expressions_8_class.pdf",
            description="Подробное руководство по алгебраическим выражениям",
            grade=8,
            subject="алгебра"
        ),
        PriorityMaterial(
            title="Задачи по геометрии",
            content="Различные задачи по геометрии для школьников",
            file_name="geometrical_problems_solutions.docx",
            description="Коллекция геометрических задач",
            grade=8,
            subject="геометрия"
        ),
        PriorityMaterial(
            title="История России",
            content="Курс истории России от древности до современности",
            file_name="history_russia_course.pdf",
            description="Полный курс истории России",
            grade=8,
            subject="история"
        ),
        PriorityMaterial(
            title="Физика основы",
            content="Основные принципы физики для начинающих",
            file_name="word_combination_N_basic_physics.pdf",  # Contains "слово сочетание N" equivalent
            description="Введение в физику",
            grade=8,
            subject="физика"
        ),
        PriorityMaterial(
            title="Слово сочетание N и его применение",
            content="Описание слова сочетания N и как его использовать",
            file_name="unrelated_file_name.txt",
            description="Документ о слове сочетании N",
            grade=9,
            subject="литература"
        ),
        PriorityMaterial(
            title="Не связанный заголовок",
            content="Здесь содержится информация о слово сочетание N",
            file_name="another_unrelated_name.pdf",
            description="Также рассматривается слово сочетание N",
            grade=9,
            subject="литература"
        ),
        PriorityMaterial(
            title="Просто заголовок",
            content="Обычное содержание",
            file_name="word_combination_N_documentation.xlsx",  # Contains "слово сочетание N" equivalent
            description="Описание документа",
            grade=10,
            subject="информатика"
        )
    ]

    for material in materials:
        search_system.add_material(material)

    # Test search with priority
    print("=== Тестирование поискового запроса 'слово сочетание N' ===")
    results = search_system.search_with_priority("слово сочетание N")

    print(f"Найдено {len(results)} результатов:")
    for i, result in enumerate(results, 1):
        print(f"\n{i}. Заголовок: {result['material'].title}")
        print(f"   Предмет: {result['material'].subject}, Класс: {result['material'].grade}")
        print(f"   Описание: {result['material'].description}")
        print(f"   Файл: {result['material'].file_name}")
        print(f"   Приоритеты - Заголовок: {result['title_match']:.2f}, "
              f"Содержание: {result['content_match']:.2f}, "
              f"Файл: {result['file_match']:.2f}, "
              f"Описание: {result['description_match']:.2f}")
        print(f"   Общий балл: {result['score']:.2f}")

    print("\n=== Тестирование поискового запроса 'алгебраические выражения' ===")
    results = search_system.search_with_priority("алгебраические выражения")

    print(f"Найдено {len(results)} результатов:")
    for i, result in enumerate(results, 1):
        print(f"\n{i}. Заголовок: {result['material'].title}")
        print(f"   Общий балл: {result['score']:.2f}")
        print(f"   Совпадения - Заголовок: {result['title_match']:.2f}, "
              f"Содержание: {result['content_match']:.2f}")

    print("\n=== Тестирование поискового запроса 'геометрии' (проверка релевантности) ===")
    results = search_system.search_with_priority("геометрии")

    print(f"Найдено {len(results)} результатов:")
    for i, result in enumerate(results, 1):
        print(f"\n{i}. Заголовок: {result['material'].title}")
        print(f"   Общий балл: {result['score']:.2f}")
        print(f"   Совпадения - Заголовок: {result['title_match']:.2f}, "
              f"Содержание: {result['content_match']:.2f}")