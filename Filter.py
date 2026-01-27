import json
import os
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

    def format_date(self, date_str):
        """Форматирует дату для отображения"""
        try:
            dt = datetime.fromisoformat(date_str)
            return dt.strftime("%Y-%m-%d %H:%M")
        except:
            return "Неизвестно"