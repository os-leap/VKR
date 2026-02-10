class Material:
    """Класс для представления учебного материала"""
    def __init__(self, title, description, grade, subject, tags=None):
        self.title = title
        self.description = description
        self.grade = grade  # класс (например, 5)
        self.subject = subject  # предмет (например, "математика")
        self.tags = tags or []  # дополнительные теги
    
    def __repr__(self):
        return f"Material(title='{self.title}', grade={self.grade}, subject='{self.subject}', tags={self.tags})"


class SearchSystem:
    """Система поиска учебных материалов"""
    
    def __init__(self):
        self.materials = []
    
    def add_material(self, material):
        """Добавление материала в систему"""
        self.materials.append(material)
    
    def search_by_grade_and_subject(self, grade=None, subject=None):
        """
        Поиск материалов по классу и/или предмету
        Если параметры не указаны, возвращаются все материалы
        """
        results = []
        
        for material in self.materials:
            # Проверяем соответствие класса и предмета
            grade_match = (grade is None) or (material.grade == grade)
            subject_match = (subject is None) or (material.subject.lower() == subject.lower())
            
            if grade_match and subject_match:
                results.append(material)
        
        return results
    
    def search_with_tags(self, grade=None, subject=None):
        """
        Расширенный поиск с учетом тегов
        Ищет материалы, которые могут быть связаны с указанным классом и предметом через теги
        """
        results = []
        
        for material in self.materials:
            # Основная проверка по полям
            grade_match = (grade is None) or (material.grade == grade)
            subject_match = (subject is None) or (material.subject.lower() == subject.lower())
            
            # Проверка тегов на соответствие классу и предмету
            tag_grade_match = (grade is None) or any(
                str(grade) in str(tag).lower() or 
                f"{grade}-й" in str(tag).lower() or 
                f"{grade} класс" in str(tag).lower()
                for tag in material.tags
            )
            
            tag_subject_match = (subject is None) or any(
                subject.lower() in str(tag).lower()
                for tag in material.tags
            )
            
            # Включаем материал, если он соответствует хотя бы одному критерию
            if (grade_match and subject_match) or (tag_grade_match and tag_subject_match):
                results.append(material)
        
        return results


# Пример использования
if __name__ == "__main__":
    # Создаем систему поиска
    search_system = SearchSystem()
    
    # Добавляем примеры материалов
    search_system.add_material(Material(
        "Задачи по алгебре", 
        "Коллекция задач по алгебре для 8 класса", 
        8, 
        "алгебра",
        ["8 класс", "алгебра", "задачи", "уроки"]
    ))
    
    search_system.add_material(Material(
        "Геометрия 8 класс", 
        "Теория и практика по геометрии", 
        8, 
        "геометрия",
        ["8 класс", "геометрия", "теоремы"]
    ))
    
    search_system.add_material(Material(
        "Физика 7 класс", 
        "Эксперименты и теории", 
        7, 
        "физика",
        ["7 класс", "физика", "эксперименты"]
    ))
    
    search_system.add_material(Material(
        "Математика 8 класс", 
        "Общий курс математики", 
        9, 
        "математика",
        ["8 класс", "математика", "повторение"]  # обратите внимание: тег указывает на 8 класс, но материал для 9 класса
    ))
    
    # Тестирование поиска
    print("Поиск материалов для 8 класса по алгебре:")
    results = search_system.search_with_tags(grade=8, subject="алгебра")
    for result in results:
        print(f"  - {result}")
    
    print("\nПоиск всех материалов для 8 класса:")
    results = search_system.search_with_tags(grade=8)
    for result in results:
        print(f"  - {result}")
    
    print("\nПоиск всех материалов по алгебре:")
    results = search_system.search_with_tags(subject="алгебра")
    for result in results:
        print(f"  - {result}")
    
    print("\nПоиск без фильтров (все материалы):")
    results = search_system.search_with_tags()
    for result in results:
        print(f"  - {result}")