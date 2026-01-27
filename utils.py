
import requests
from bs4 import BeautifulSoup
import os
from datetime import datetime
import logging
from pdfplumber import open as pdf_open

from audit_system import log_action
from data_utils import load_data, save_data

logger = logging.getLogger(__name__)

def fetch_edsoo_documents():
    url = "https://edsoo.ru/normativnye-dokumenty/ "
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            documents = []
            for item in soup.find_all("a", href=True):
                if item["href"].endswith(".pdf"):
                    documents.append({
                        "title": item.text.strip(),
                        "url": item["href"],
                        "registered_at": datetime.now().isoformat()
                    })
            return documents
        else:
            logger.error(f"Не удалось загрузить сайт: {response.status_code}")
            return []
    except Exception as e:
        logger.error(f"Ошибка парсинга: {e}")
        return []

def download_document(doc, folder="static/uploads"):
    try:
        response = requests.get(doc["url"], stream=True)
        if response.status_code == 200:
            filename = f"{doc['title'].replace(' ', '_').replace('/', '')}.pdf"
            file_path = os.path.join(folder, filename)
            with open(file_path, "wb") as f:
                for chunk in response.iter_content(1024):
                    if chunk:
                        f.write(chunk)
            logger.info(f"Файл сохранён: {filename}")
            return filename
    except Exception as e:
        logger.error(f"Ошибка скачивания: {e}")
        return None

def extract_content_from_pdf(pdf_path):
    try:
        with pdf_open(pdf_path) as pdf:
            text = ""
            for page in pdf.pages[:3]:  # Первые 3 страницы
                text += page.extract_text() + "\n\n"
            return text[:5000]  # Ограничиваем длину
    except Exception as e:
        logger.warning(f"Не удалось извлечь содержание: {e}")
        return "Недоступно для предпросмотра"

def sync_edsoo():
    
    from data_utils import load_data, save_data
    new_docs = fetch_edsoo_documents()
    knowledge = load_data()
    added = 0
    updated = 0

    for doc in new_docs:
        existing = next((x for x in knowledge if x["title"] == doc["title"]), None)
        if existing:
            if doc["registered_at"] > existing.get("updated_at", ""):
                filename = download_document(doc, "static/uploads")
                if filename:
                    existing.update({
                        "file": filename,
                        "content": extract_content_from_pdf(os.path.join("static/uploads", filename))[:2000],
                        "updated_at": datetime.now().isoformat()
                    })
                    updated += 1
        else:
            filename = download_document(doc, "static/uploads")
            if filename:
                knowledge.append({
                    "title": doc["title"],
                    "content": extract_content_from_pdf(os.path.join("static/uploads", filename))[:2000],
                    "file": filename,
                    "source": "edsoo.ru",
                    "created_at": doc["registered_at"],
                    "updated_at": doc["registered_at"]
                })
                added += 1

    if added or updated:
        save_data(knowledge)
        log_action(
            username="system",
            action_type="sync",
            target="edsoo.ru",
            details=f"Добавлено: {added}, Обновлено: {updated}"
        )

    log_action(
        username="system",
        action_type="sync",
        target="edsoo.ru",
        details=f"Добавлено: {added}, Обновлено: {updated}"
    )
    return "Синхронизация завершена"

