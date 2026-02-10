#!/usr/bin/env python3
"""
GUI интерфейс для семантического поиска
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
from Filter import FilterManager


class SemanticSearchGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Поиск в базе знаний")
        self.root.geometry("800x600")

        # Инициализируем FilterManager
        self.filter_manager = FilterManager()

        # Создаем основные элементы интерфейса
        self.setup_ui()

    def setup_ui(self):
        # Заголовок
        title_label = tk.Label(self.root, text="Поиск в базе знаний", font=("Arial", 16))
        title_label.pack(pady=10)

        # Поле ввода запроса
        query_frame = tk.Frame(self.root)
        query_frame.pack(fill=tk.X, padx=20, pady=5)

        tk.Label(query_frame, text="Запрос:").pack(anchor=tk.W)
        self.query_entry = tk.Entry(query_frame, font=("Arial", 12))
        self.query_entry.pack(fill=tk.X, pady=5)

        # Выбор типа поиска
        search_type_frame = tk.Frame(self.root)
        search_type_frame.pack(fill=tk.X, padx=20, pady=5)

        tk.Label(search_type_frame, text="Тип поиска:").pack(anchor=tk.W)

        self.search_type = tk.StringVar(value="keywords")
        keyword_radio = tk.Radiobutton(search_type_frame, text="Обычный поиск", variable=self.search_type, value="keywords")
        semantic_radio = tk.Radiobutton(search_type_frame, text="Семантический поиск", variable=self.search_type, value="semantic")

        keyword_radio.pack(side=tk.LEFT, padx=(0, 20))
        semantic_radio.pack(side=tk.LEFT)

        # Кнопка поиска
        search_button = tk.Button(self.root, text="Найти", command=self.perform_search, bg="#4CAF50", fg="white", font=("Arial", 12))
        search_button.pack(pady=10)

        # Результаты поиска
        results_frame = tk.Frame(self.root)
        results_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        tk.Label(results_frame, text="Результаты поиска:", font=("Arial", 12)).pack(anchor=tk.NW)

        self.results_text = scrolledtext.ScrolledText(results_frame, wrap=tk.WORD, font=("Arial", 10))
        self.results_text.pack(fill=tk.BOTH, expand=True, pady=5)

    def perform_search(self):
        """Выполняет поиск в зависимости от выбранного типа"""
        query = self.query_entry.get().strip()
        if not query:
            self.show_message("Введите запрос для поиска.")
            return

        search_type = self.search_type.get()
        if search_type == "keywords":
            results = self.filter_manager.search_by_keywords(query)
        elif search_type == "semantic":
            results = self.filter_manager.semantic_search(query)
        else:
            results = []

        self.display_results(results, search_type)

    def display_results(self, results, search_type):
        """Отображает результаты поиска"""
        self.results_text.delete(1.0, tk.END)

        if not results:
            self.results_text.insert(tk.END, f"По запросу '{self.query_entry.get()}' ничего не найдено.")
            return

        search_name = "обычного" if search_type == "keywords" else "семантического"
        self.results_text.insert(tk.END, f"Результаты {search_name} поиска ({len(results)}):\n\n")

        for i, entry in enumerate(results, 1):
            title = entry.get('title', 'Без заголовка')
            content = entry.get('content', '')
            topic = entry.get('topic', 'Не указана')
            
            # Ограничиваем длину контента для отображения
            preview = content[:200] + "..." if len(content) > 200 else content
            
            self.results_text.insert(tk.END, f"{i}. {title}\n")
            self.results_text.insert(tk.END, f"   Тема: {topic}\n")
            self.results_text.insert(tk.END, f"   Содержание: {preview}\n\n")

    def show_message(self, message):
        """Показывает сообщение пользователю"""
        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(tk.END, message)


def main():
    root = tk.Tk()
    app = SemanticSearchGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()