import json
import os
from datetime import datetime


class AdvancedFilterManager:
    """Менеджер расширенной фильтрации записей по классам, параллелям и предметам"""

    def __init__(self, data_file="knowledge_base.json", filters_file="filters.json"):
        self.data_file = data_file
        self.filters_file = filters_file
        self.data = self._load_data()
        self.filters = self._load_filters()

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

    def _load_filters(self):
        """Загружает конфигурацию фильтров"""
        if os.path.exists(self.filters_file):
            with open(self.filters_file, "r", encoding="utf-8") as f:
                return json.load(f)
        # Возвращаем стандартные фильтры
        default_filters = {
            "classes": ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11"],
            "parallels": ["А", "Б", "В", "Г", "Д", "Е"],
            "subjects": [
                "Математика", "Русский язык", "Литература", "История", "География", 
                "Биология", "Химия", "Физика", "Информатика", "Английский язык",
                "Немецкий язык", "Французский язык", "Обществознание", "Экономика",
                "Право", "ОБЖ", "Физкультура", "ИЗО", "Музыка", "Технология"
            ]
        }
        self._save_filters(default_filters)
        return default_filters

    def _save_filters(self, filters):
        """Сохраняет конфигурацию фильтров"""
        with open(self.filters_file, "w", encoding="utf-8") as f:
            json.dump(filters, f, ensure_ascii=False, indent=4)
        self.filters = filters

    def get_available_filters(self):
        """Возвращает доступные фильтры"""
        return {
            "classes": sorted(self.filters["classes"]),
            "parallels": sorted(self.filters["parallels"]),
            "subjects": sorted(self.filters["subjects"])
        }

    def add_class(self, class_name):
        """Добавляет новый класс в фильтры"""
        if class_name not in self.filters["classes"]:
            self.filters["classes"].append(class_name)
            self._save_filters(self.filters)
            return True
        return False

    def remove_class(self, class_name):
        """Удаляет класс из фильтров"""
        if class_name in self.filters["classes"]:
            self.filters["classes"].remove(class_name)
            self._save_filters(self.filters)
            return True
        return False

    def add_parallel(self, parallel_name):
        """Добавляет новую параллель в фильтры"""
        if parallel_name not in self.filters["parallels"]:
            self.filters["parallels"].append(parallel_name)
            self._save_filters(self.filters)
            return True
        return False

    def remove_parallel(self, parallel_name):
        """Удаляет параллель из фильтров"""
        if parallel_name in self.filters["parallels"]:
            self.filters["parallels"].remove(parallel_name)
            self._save_filters(self.filters)
            return True
        return False

    def add_subject(self, subject_name):
        """Добавляет новый предмет в фильтры"""
        if subject_name not in self.filters["subjects"]:
            self.filters["subjects"].append(subject_name)
            self._save_filters(self.filters)
            return True
        return False

    def remove_subject(self, subject_name):
        """Удаляет предмет из фильтров"""
        if subject_name in self.filters["subjects"]:
            self.filters["subjects"].remove(subject_name)
            self._save_filters(self.filters)
            return True
        return False

    def update_entry_filters(self, index, class_name=None, parallel=None, subject=None):
        """Обновляет фильтры для конкретной записи"""
        if 0 <= index < len(self.data):
            if "education_info" not in self.data[index]:
                self.data[index]["education_info"] = {}
            
            if class_name is not None:
                self.data[index]["education_info"]["class"] = class_name
            if parallel is not None:
                self.data[index]["education_info"]["parallel"] = parallel
            if subject is not None:
                self.data[index]["education_info"]["subject"] = subject
                
            self._save_data(self.data)
            return True
        return False

    def filter_entries(self, selected_class=None, selected_parallel=None, selected_subject=None, selected_topic=None):
        """Фильтрует записи по указанным параметрам"""
        filtered_data = self.data
        
        # Фильтрация по классу
        if selected_class and selected_class != "all":
            filtered_data = [
                entry for entry in filtered_data
                if entry.get("education_info", {}).get("class") == selected_class
            ]
        
        # Фильтрация по параллели
        if selected_parallel and selected_parallel != "all":
            filtered_data = [
                entry for entry in filtered_data
                if entry.get("education_info", {}).get("parallel") == selected_parallel
            ]
        
        # Фильтрация по предмету
        if selected_subject and selected_subject != "all":
            filtered_data = [
                entry for entry in filtered_data
                if entry.get("education_info", {}).get("subject") == selected_subject
            ]
        
        # Фильтрация по теме (если была часть предыдущей системы)
        if selected_topic and selected_topic != "Все темы" and selected_topic != "":
            filtered_data = [
                entry for entry in filtered_data
                if entry.get("topic", "Без темы") == selected_topic
            ]
        
        return filtered_data

    def get_unique_classes(self):
        """Возвращает уникальные классы из существующих записей"""
        classes = set()
        for entry in self.data:
            edu_info = entry.get("education_info", {})
            class_name = edu_info.get("class")
            if class_name:
                classes.add(class_name)
        return sorted(list(classes))

    def get_unique_parallels(self):
        """Возвращает уникальные параллели из существующих записей"""
        parallels = set()
        for entry in self.data:
            edu_info = entry.get("education_info", {})
            parallel = edu_info.get("parallel")
            if parallel:
                parallels.add(parallel)
        return sorted(list(parallels))

    def get_unique_subjects(self):
        """Возвращает уникальные предметы из существующих записей"""
        subjects = set()
        for entry in self.data:
            edu_info = entry.get("education_info", {})
            subject = edu_info.get("subject")
            if subject:
                subjects.add(subject)
        return sorted(list(subjects))

    def get_unique_topics(self):
        """Возвращает уникальные темы (для совместимости со старой системой)"""
        topics = set(["Все темы", "Без темы"])
        for entry in self.data:
            topic = entry.get("topic", "Без темы")
            topics.add(topic)
        return sorted(list(topics))

    def format_date(self, date_str):
        """Форматирует дату для отображения"""
        try:
            dt = datetime.fromisoformat(date_str)
            return dt.strftime("%Y-%m-%d %H:%M")
        except:
            return "Неизвестно"