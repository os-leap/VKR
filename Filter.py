import json
import os
import re
from datetime import datetime


class FilterManager:
    """Менеджер фильтрации записей по темам"""

    def __init__(self, data_file="knowledge_base.json"):
        self.data_file = data_file
        self.data = self._load_data()

    def _load_data(self):
        """Загружает данные из файла"""
        if os.path.exists(self.data_file):
            with open(self.data_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return []

    def _save_data(self, data):
        """Сохраняет данные в файл"""
        with open(self.data_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        self.data = data

    def get_unique_topics(self):
        """Возвращает список уникальных тем"""
        topics = set(["Все темы", "Без темы"])
        for entry in self.data:  # Исправлено: self.data вместо self
            topic = entry.get("topic", "Без темы")
            topics.add(topic)
        return sorted(list(topics))
    
    def get_managed_topics(self):
        """Возвращает список управляемых тем (без служебных)"""
        topics = set()
        for entry in self.data:
            topic = entry.get("topic", "Без темы")
            if topic not in ["Все темы", "Без темы"]:
                topics.add(topic)
        return sorted(list(topics))

    def add_topic_field(self):
        """Добавляет поле topic в существующие записи"""
        updated = False
        for entry in self.data:  # Исправлено: self.data вместо self
            if "topic" not in entry:
                entry["topic"] = "Без темы"
                updated = True
        if updated:
            self._save_data(self.data)
        return updated

    def filter_by_topic(self, topic="Все темы"):
        """Фильтрует записи по теме"""
        if topic == "Все темы" or not topic:
            return self.data

        filtered_data = []
        for entry in self.data:  # Исправлено: self.data вместо self
            if entry.get("topic", "Без темы") == topic:
                filtered_data.append(entry)

        return filtered_data

    def get_topic_statistics(self):
        """Возвращает статистику по темам"""
        stats = {"Все темы": len(self.data)}
        for entry in self.data:  # Исправлено: self.data вместо self
            topic = entry.get("topic", "Без темы")
            stats[topic] = stats.get(topic, 0) + 1
        return stats

    def update_entry_topic(self, index, new_topic):
        """Обновляет тему для конкретной записи"""
        if 0 <= index < len(self.data):
            self.data[index]["topic"] = new_topic
            self._save_data(self.data)
            return True
        return False

    def add_topic(self, topic_name):
        """Добавляет новую тему в фильтры"""
        # Проверяем, что тема не входит в список зарезервированных
        reserved_topics = ["Все темы", "Без темы"]
        if topic_name in reserved_topics:
            return False
            
        # Проверяем, существует ли уже такая тема в данных
        for entry in self.data:
            if entry.get("topic") == topic_name:
                return False  # Тема уже существует
        
        # Чтобы тема появилась в списке уникальных тем, нужно, чтобы она была в какой-либо записи
        # Создаем временную запись с этой темой, если такой темы еще нет в данных
        temp_entry = {
            "title": f"Временная запись для темы {topic_name}",
            "content": f"Эта временная запись используется для добавления темы '{topic_name}' в список доступных тем",
            "topic": topic_name,
            "author": "system",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "id": str(len(self.data))
        }
        
        # Добавляем временную запись, чтобы тема появилась в списке
        self.data.append(temp_entry)
        self._save_data(self.data)
        
        # Удаляем временную запись, чтобы не засорять базу
        self.data.remove(temp_entry)
        self._save_data(self.data)
        
        return True

    def remove_topic(self, topic_name):
        """Удаляет тему из фильтров, заменяя на 'Без темы' все записи с этой темой"""
        if topic_name in ["Все темы", "Без темы"]:
            return False  # Нельзя удалить зарезервированные темы
            
        # Заменяем тему на "Без темы" во всех записях
        updated = False
        for entry in self.data:
            if entry.get("topic") == topic_name:
                entry["topic"] = "Без темы"
                updated = True
                
        if updated:
            self._save_data(self.data)
            
        return updated

    def format_date(self, date_str):
        """Форматирует дату для отображения"""
        try:
            dt = datetime.fromisoformat(date_str)
            return dt.strftime("%Y-%m-%d %H:%M")
        except:
            return "Неизвестно"

    def search_by_keywords(self, keywords):
        """
        Поиск записей по ключевым словам
        keywords: строка с ключевыми словами или список ключевых слов
        Возвращает список записей, содержащих хотя бы одно из ключевых слов
        """
        if isinstance(keywords, str):
            keywords = [kw.strip() for kw in keywords.split() if kw.strip()]
        
        if not keywords:
            return self.data
        
        # Попробуем определить, является ли запрос запросом по образовательным меткам
        class_level, parallel, subject = self._parse_education_tags(keywords)
        
        # Если удалось распознать образовательные метки, используем расширенный поиск
        if class_level or subject:
            return self.advanced_search_by_education_tags(
                class_level=class_level, 
                parallel=parallel, 
                subject=subject
            )
        
        # Иначе используем обычный поиск по ключевым словам
        results = []
        for entry in self.data:
            # Проверяем title, content и другие поля на наличие ключевых слов
            text_to_search = f"{entry.get('title', '')} {entry.get('content', '')}".lower()
            
            # Проверяем также информацию об образовании, если она есть
            education_info = entry.get('education_info', {})
            if education_info:
                class_info = education_info.get('class', '')
                parallel_info = education_info.get('parallel', 'все')  # Если параллель не указана, считаем что "все"
                subject_info = education_info.get('subject', '')
                text_to_search += f" {class_info} {parallel_info} {subject_info}".lower()
            
            # Проверяем, содержит ли текст хотя бы одно из ключевых слов
            if any(keyword.lower() in text_to_search for keyword in keywords):
                results.append(entry)
        
        return results

    def _parse_education_tags(self, keywords):
        """
        Анализирует ключевые слова и извлекает образовательные метки
        Возвращает кортеж (class_level, parallel, subject)
        """
        class_level = None
        parallel = "все"  # по умолчанию ищем по всем параллелям
        subject = None
        
        # Приводим все ключевые слова к нижнему регистру для сопоставления
        lower_keywords = [kw.lower() for kw in keywords]
        
        # Шаблоны для поиска класса
        class_patterns = {
            "1": ["1", "первый", "первом"],
            "2": ["2", "второй", "втором"],
            "3": ["3", "третий", "третьем"],
            "4": ["4", "четвертый", "четвертом"],
            "5": ["5", "пятый", "пятом"],
            "6": ["6", "шестой", "шестом"],
            "7": ["7", "седьмой", "седьмом"],
            "8": ["8", "восьмой", "восьмом"],
            "9": ["9", "девятый", "девятом"],
            "10": ["10", "десятый", "десятом"],
            "11": ["11", "одиннадцатый", "одиннадцатом"]
        }
        
        # Шаблоны для поиска предметов
        subject_patterns = {
            "русский язык": ["русский", "язык", "русского", "русскому"],
            "математика": ["математика", "математике", "математики"],
            "английский язык": ["английский", "английского", "английскому"],
            "французский язык": ["французский", "французского", "французскому", "французский язык"],
            "литература": ["литература", "литературе", "литературы"],
            "физика": ["физика", "физике", "физики"],
            "химия": ["химия", "химии", "химе"],
            "биология": ["биология", "биологии", "биологии"],
            "география": ["география", "географии", "географии"],
            "история": ["история", "истории", "истории"],
            "обществознание": ["обществознание", "обществознанию", "обществознания"],
            "информатика": ["информатика", "информатике", "информатики"],
            "алгебра": ["алгебра", "алгебре", "алгебры"],
            "геометрия": ["геометрия", "геометрии", "геометрии"]
        }
        
        # Поиск уровня класса
        for level, patterns in class_patterns.items():
            if any(pattern in lower_keywords for pattern in patterns):
                class_level = level
                break
        
        # Поиск предмета
        for subj, patterns in subject_patterns.items():
            if any(pattern in lower_keywords for pattern in patterns):
                subject = subj
                break
        
        return class_level, parallel, subject

    def advanced_search_by_education_tags(self, class_level=None, parallel="все", subject=None):
        """
        Расширенный поиск по образовательным меткам
        class_level: уровень класса (например, "1")
        parallel: параллель класса (по умолчанию "все")
        subject: предмет (например, "Французский язык")
        Возвращает список записей, соответствующих критериям
        """
        results = []
        
        for entry in self.data:
            education_info = entry.get('education_info', {})
            
            # Проверяем совпадение по классу
            if class_level and str(education_info.get('class', '')) != str(class_level):
                continue
            
            # Проверяем совпадение по предмету
            if subject and education_info.get('subject', '').lower() != subject.lower():
                continue
            
            # Для параллели "все" подходит любая параллель, иначе проверяем точное совпадение
            entry_parallel = education_info.get('parallel', 'все')
            if parallel != "все" and entry_parallel != parallel:
                continue
            
            results.append(entry)
        
        return results