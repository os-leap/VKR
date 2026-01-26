
import json
import os
from datetime import datetime

DATA_FILE = "knowledge_base.json"

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                for entry in data:
                    if "topic" not in entry:
                        entry["topic"] = "Без темы"
                    if "created_at" not in entry:
                        entry["created_at"] = datetime.now().isoformat()
                    if "updated_at" not in entry:
                        entry["updated_at"] = entry["created_at"]
                    if "title" not in entry or not entry["title"]:
                        entry["title"] = generate_title_from_content(entry.get("content", ""))
                return data
        except (json.JSONDecodeError, FileNotFoundError):
            return []
    return []

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def generate_title_from_content(content):
    if not content:
        return "Без заголовка"
    words = content.strip().split()[:10]
    title = " ".join(words)
    return title[:100] + "..." if len(title) > 100 else title