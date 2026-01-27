#!/usr/bin/env python3
"""
Скрипт для обновления записей в базе знаний, добавляя уникальные идентификаторы
"""
import json
import uuid
import os

DATA_FILE = "knowledge_base.json"

def update_entries_with_ids():
    # Загружаем существующие данные
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        print(f"Файл {DATA_FILE} не найден")
        return

    # Добавляем уникальный ID каждой записи, если его еще нет
    updated_count = 0
    for entry in data:
        if "id" not in entry:
            entry["id"] = str(uuid.uuid4())
            updated_count += 1
    
    # Сохраняем обновленные данные
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    
    print(f"Обновлено {updated_count} записей с добавлением уникальных ID")
    print(f"Всего записей в базе: {len(data)}")

if __name__ == "__main__":
    update_entries_with_ids()