import json
import os
import re
import threading
import logging
import uuid
from datetime import datetime
import audit_system
import bcrypt
import schedule
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, session, jsonify
from werkzeug.utils import secure_filename
from audit_system import init_audit_system, log_action
from auth import auth
from data_utils import load_data
from scheduler import background_job, start_scheduler
from utils import extract_content_from_pdf, fetch_edsoo_documents, download_document, logger, sync_edsoo
from scrape_pdfs import PDFScraper
import threading
import time
from Filter import FilterManager
from advanced_filter import AdvancedFilterManager
from forms import KnowledgeEntryForm
from simple_semantic_search_integration import initialize_search_system, perform_integrated_search
from backup_system import backup_system, create_daily_backup
from enhanced_search_system import EnhancedSearchSystem, EnhancedMaterial
from fgo_headers_processor import FGOHeadersProcessor
init_audit_system()


app = Flask(__name__)

app.secret_key = 'your_secret_key_here'  # Для сессий


# --- Настройка приложения ---
USERS_FILE = "users.json"
DATA_FILE = "knowledge_base.json"
app.config["UPLOAD_FOLDER"] = "static/uploads"
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
ALLOWED_EXTENSIONS = {"pdf", "docx", "txt", "doc", "rtf", "mp4", "avi", "mov", "wmv", "flv", "webm"}

filter_manager = FilterManager(DATA_FILE)
advanced_filter_manager = AdvancedFilterManager(DATA_FILE, "filters.json")

UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


app.register_blueprint(auth, url_prefix="/auth")





@app.route("/audit")
def audit_log():
    if "user" not in session or session["user"]["role"] != "admin":
        return "Доступ запрещён", 403

        # Получаем параметры фильтрации
    action_type = request.args.get("type", "")
    username = request.args.get("user", "")
    query = request.args.get("query", "").strip().lower()
    date_from = request.args.get("date_from", "")
    date_to = request.args.get("date_to", "")

    # Загружаем логи
    logs = audit_system.load_audit_logs()

    # Фильтруем логи
    if action_type:
        logs = [log for log in logs if log["action_type"] == action_type]

    if username:
        logs = [log for log in logs if log["username"] == username]

    if query:
        logs = [log for log in logs if query in log["details"].lower() or
                query in log["target"].lower() or
                query in log["username"].lower()]
    
    # Фильтруем по дате
    if date_from:
        from_date = datetime.strptime(date_from, '%Y-%m-%d')
        logs = [log for log in logs if datetime.fromisoformat(log["timestamp"]) >= from_date]
    
    if date_to:
        to_date = datetime.strptime(date_to, '%Y-%m-%d')
        logs = [log for log in logs if datetime.fromisoformat(log["timestamp"]).date() <= to_date.date()]

    # Сортируем по времени (новые сначала)
    logs.sort(key=lambda x: x["timestamp"], reverse=True)

    return render_template("audit.html", logs=logs, format_date=format_date)


@app.route("/backups")
def list_backups():
    if "user" not in session or session["user"]["role"] != "admin":
        return "Доступ запрещён", 403
    
    backups = backup_system.list_backups()
    return render_template("backups.html", backups=backups)


@app.route("/create-backup", methods=["POST"])
def create_backup():
    if "user" not in session or session["user"]["role"] != "admin":
        return "Доступ запрещён", 403
    
    backup_path = backup_system.create_backup()
    log_action(session["user"]["username"], "backup_create", backup_path, "Создание резервной копии")
    return jsonify({"success": True, "backup_path": backup_path})


@app.route("/restore-backup/<filename>", methods=["POST"])
def restore_backup(filename):
    if "user" not in session or session["user"]["role"] != "admin":
        return "Доступ запрещён", 403
    
    success = backup_system.restore_backup(filename)
    if success:
        log_action(session["user"]["username"], "backup_restore", filename, "Восстановление из резервной копии")
        return jsonify({"success": True})
    else:
        return jsonify({"success": False, "error": "Failed to restore backup"})


@app.route("/restore-data-page")
def restore_data_page():
    if "user" not in session or session["user"]["role"] != "admin":
        return "Доступ запрещён", 403
    
    return render_template("restore_data.html")

@app.route("/get-changed-records", methods=["POST"])
def get_changed_records():
    """Get records with changes within a time period"""
    if "user" not in session or session["user"]["role"] != "admin":
        return "Доступ запрещён", 403
    
    try:
        data = request.get_json()
        date_from = data.get("date_from")
        date_to = data.get("date_to")
        
        # Load audit logs
        logs = audit_system.load_audit_logs()
        
        # Filter logs based on date range
        filtered_logs = []
        for log in logs:
            log_time = datetime.fromisoformat(log["timestamp"])
            
            # Check date range
            if date_from:
                from_date = datetime.strptime(date_from, '%Y-%m-%d')
                if log_time < from_date:
                    continue
            
            if date_to:
                to_date = datetime.strptime(date_to, '%Y-%m-%d')
                if log_time.date() > to_date.date():
                    continue
            
            # Add to filtered logs
            filtered_logs.append(log)
        
        # Format the records for the frontend
        records = []
        for log in filtered_logs:
            record = {
                "id": log.get("id", str(uuid.uuid4())),
                "timestamp": format_date(log["timestamp"]),
                "action_type": log["action_type"],
                "title": log.get("target", ""),
                "description": log.get("details", ""),
                "old_value": log.get("old_value", None),
                "new_value": log.get("new_value", None),
                "backup_id": log.get("backup_id", "")
            }
            records.append(record)
        
        return jsonify({
            "success": True,
            "records": records
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route("/perform-action", methods=["POST"])
def perform_action():
    """Perform selected action on a record"""
    if "user" not in session or session["user"]["role"] != "admin":
        return "Доступ запрещён", 403
    
    try:
        data = request.get_json()
        action = data.get("action")
        record_id = data.get("record_id")
        backup_id = data.get("backup_id", "")
        
        # Find the corresponding log entry
        logs = audit_system.load_audit_logs()
        target_log = None
        for log in logs:
            if log.get("id") == record_id or str(log.get("id")) == str(record_id):
                target_log = log
                break
        
        if not target_log:
            return jsonify({"success": False, "error": "Лог не найден"})
        
        # Perform the selected action
        if action == "restore":
            if target_log["action_type"] == "delete" and "old_value" in target_log:
                # Restore deleted item
                knowledge_data = load_data()
                # Check if item doesn't already exist
                if not any(item.get("title") == target_log["old_value"].get("title") for item in knowledge_data):
                    knowledge_data.append(target_log["old_value"])
                    save_data(knowledge_data)
                    log_action(
                        session["user"]["username"], 
                        "restore", 
                        target_log["target"], 
                        f"Восстановлена удаленная запись: {target_log['target']}"
                    )
                    return jsonify({
                        "success": True,
                        "message": f"Запись '{target_log['target']}' успешно восстановлена"
                    })
                else:
                    return jsonify({
                        "success": False,
                        "error": "Запись уже существует"
                    })
            elif target_log["action_type"] == "edit" and "old_value" in target_log:
                # Restore from backup (if available) or old value
                knowledge_data = load_data()
                for i, item in enumerate(knowledge_data):
                    if item.get("title") == target_log["target"] or item.get("id") == target_log.get("entry_id"):
                        knowledge_data[i] = target_log["old_value"]
                        break
                save_data(knowledge_data)
                log_action(
                    session["user"]["username"], 
                    "restore", 
                    target_log["target"], 
                    f"Восстановлена запись из резервной копии: {target_log['target']}"
                )
                return jsonify({
                    "success": True,
                    "message": f"Запись '{target_log['target']}' успешно восстановлена из резервной копии"
                })
            else:
                # General restore action - try to restore from old_value if available
                if "old_value" in target_log:
                    knowledge_data = load_data()
                    existing_index = -1
                    for i, item in enumerate(knowledge_data):
                        if item.get("title") == target_log["target"] or item.get("id") == target_log.get("entry_id"):
                            existing_index = i
                            break
                    
                    if existing_index != -1:
                        knowledge_data[existing_index] = target_log["old_value"]
                    else:
                        knowledge_data.append(target_log["old_value"])
                    
                    save_data(knowledge_data)
                    log_action(
                        session["user"]["username"], 
                        "restore", 
                        target_log["target"], 
                        f"Восстановлена запись: {target_log['target']}"
                    )
                    return jsonify({
                        "success": True,
                        "message": f"Запись '{target_log['target']}' успешно восстановлена"
                    })
        
        elif action == "revert":
            if target_log["action_type"] == "edit" and "old_value" in target_log:
                # Revert edit to old value
                knowledge_data = load_data()
                for i, item in enumerate(knowledge_data):
                    if item.get("title") == target_log["target"] or item.get("id") == target_log.get("entry_id"):
                        knowledge_data[i] = target_log["old_value"]
                        break
                save_data(knowledge_data)
                log_action(
                    session["user"]["username"], 
                    "revert", 
                    target_log["target"], 
                    f"Отменено редактирование записи: {target_log['target']}"
                )
                return jsonify({
                    "success": True,
                    "message": f"Изменения в записи '{target_log['target']}' успешно отменены"
                })
            else:
                return jsonify({
                    "success": False,
                    "error": "Для этого типа действия невозможно отменить изменение"
                })
        
        elif action == "delete":
            if target_log["action_type"] == "create":
                # Remove the created item
                knowledge_data = load_data()
                knowledge_data = [item for item in knowledge_data if not (
                    item.get("title") == target_log["target"] or 
                    item.get("id") == target_log.get("entry_id")
                )]
                save_data(knowledge_data)
                log_action(
                    session["user"]["username"], 
                    "delete", 
                    target_log["target"], 
                    f"Удалена запись: {target_log['target']}"
                )
                return jsonify({
                    "success": True,
                    "message": f"Запись '{target_log['target']}' успешно удалена"
                })
            else:
                return jsonify({
                    "success": False,
                    "error": "Для этого типа действия невозможно выполнить удаление"
                })
        
        return jsonify({
            "success": False,
            "error": "Неизвестное действие"
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route("/restore-data", methods=["POST"])
def restore_data():
    """Restore specific data from audit logs within a time period"""
    if "user" not in session or session["user"]["role"] != "admin":
        return "Доступ запрещён", 403
    
    try:
        data = request.get_json()
        date_from = data.get("date_from")
        date_to = data.get("date_to")
        action_types = data.get("action_types", [])
        targets = data.get("targets", [])
        
        # Load audit logs
        logs = audit_system.load_audit_logs()
        
        # Filter logs based on criteria
        filtered_logs = []
        for log in logs:
            log_time = datetime.fromisoformat(log["timestamp"])
            
            # Check date range
            if date_from:
                from_date = datetime.strptime(date_from, '%Y-%m-%d')
                if log_time < from_date:
                    continue
            
            if date_to:
                to_date = datetime.strptime(date_to, '%Y-%m-%d')
                if log_time.date() > to_date.date():
                    continue
            
            # Check action types
            if action_types and log["action_type"] not in action_types:
                continue
                
            # Check targets
            if targets and log["target"] not in targets:
                continue
                
            filtered_logs.append(log)
        
        # Perform restoration based on logs
        restored_items = []
        for log in filtered_logs:
            if log["action_type"] == "delete" and "old_value" in log:
                # Restore deleted item
                data = load_data()
                # Check if item doesn't already exist
                if not any(item.get("title") == log["old_value"].get("title") for item in data):
                    data.append(log["old_value"])
                    save_data(data)
                    restored_items.append(log["target"])
            elif log["action_type"] == "edit" and "old_value" in log:
                # Revert edit to old value
                data = load_data()
                for i, item in enumerate(data):
                    if item.get("title") == log["target"] or item.get("id") == log.get("entry_id"):
                        data[i] = log["old_value"]
                        break
                save_data(data)
                restored_items.append(log["target"])
        
        log_action(
            session["user"]["username"], 
            "selective_restore", 
            f"{len(restored_items)} items", 
            f"Восстановлено элементов: {', '.join(restored_items)}"
        )
        
        return jsonify({
            "success": True, 
            "restored_items": restored_items,
            "message": f"Восстановлено {len(restored_items)} элементов"
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route("/sync-edsoo")
def sync_edsoo_route():
    if "user" not in session or session["user"]["role"] != "admin":
        return "Доступ запрещён", 403
    from utils import sync_edsoo
    sync_edsoo()  # Вызываем синхронизацию
    return redirect(url_for("index"))

def start_background_tasks(app):
    def job():
        with app.app_context():
            logger.info("Запуск фоновой проверки документов")
            new_docs = fetch_edsoo_documents()
            knowledge = load_data()
            added = 0
            for doc in new_docs:
                if not any(e["title"] == doc["title"] for e in knowledge):
                    filename = download_document(doc["url"])
                    if filename:
                        content = extract_content_from_pdf(filename)
                        knowledge.append({
                            "title": doc["title"],
                            "content": content,
                            "file": filename,
                            "source": "edsoo.ru",
                            "created_at": doc["registered_at"],
                            "updated_at": doc["registered_at"]
                        })
                        added += 1
            if added:
                save_data(knowledge)
                logger.info(f"Добавлено новых документов: {added}")
        schedule.every().monday.at("00:00").do(job)

    thread = threading.Thread(target=background_job, daemon=True)
    thread.start()


def load_data():
    """Загружает данные с обновлением структуры"""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            for entry in data:
                if "created_at" not in entry:
                    entry["created_at"] = datetime.now().isoformat()
                if "updated_at" not in entry:
                    entry["updated_at"] = entry["created_at"]
                # Добавляем поле topic, если его нет
                if "topic" not in entry or entry["topic"] is None:
                    entry["topic"] = "Без темы"
            
            # Инициализируем систему семантического поиска с новыми данными
            try:
                initialize_search_system(data)
            except Exception as e:
                print(f"[ERROR] Не удалось инициализировать систему семантического поиска: {e}")
            
            return data
    return []


def initialize_enhanced_search_system(data):
    """Initialize the enhanced search system with data from knowledge base"""
    search_system = EnhancedSearchSystem()
    
    for entry in data:
        # Get content from entry
        content = entry.get("content", "")
        
        # Get files associated with entry
        files = entry.get("files", [])
        file_paths = []
        for filename in files:
            file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            if os.path.exists(file_path):
                file_paths.append(file_path)
        
        # For now, we'll use the first file if available, or None
        file_path = file_paths[0] if file_paths else None
        
        # Extract FGOs list if available in entry
        fgo_list = entry.get("fgo_list", [])
        
        # Determine grade and subject from education info if available
        education_info = entry.get("education_info", {})
        grade = education_info.get("class", "")  # Using class as grade
        subject = education_info.get("subject", "общее")  # Default to general subject
        
        # Create EnhancedMaterial object
        material = EnhancedMaterial(
            title=entry.get("title", ""),
            description=content[:100] + "..." if len(content) > 100 else content,  # First 100 chars as description
            grade=grade,
            subject=subject,
            content=content,
            file_path=file_path,
            tags=entry.get("tags", []),
            fgo_list=fgo_list,
            original_id=entry.get("id")  # Pass the original database ID
        )
        
        search_system.add_material(material)
    
    return search_system

def save_data(data):
    for entry in data:
        if "author" not in entry or not entry["author"]:
            entry["author"] = "system"
    with open(DATA_FILE, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)


def syntax_aware_search(text, query):
    """
    Performs syntax-aware search supporting:
    - AND operator: "word1 AND word2"
    - OR operator: "word1 OR word2" 
    - NOT operator: "word1 NOT word2"
    - Phrase search: "word1 word2" (both words present)
    - Quoted phrases: "\"exact phrase\""
    """
    # Normalize text and query to lowercase
    text_lower = text.lower()
    query = query.strip()
    
    # Handle quoted phrases first
    quoted_phrases = re.findall(r'"([^"]*)"', query)
    query_without_quotes = re.sub(r'"[^"]*"', '', query)
    
    # Check if all quoted phrases are present in the text
    for phrase in quoted_phrases:
        phrase = phrase.strip().lower()
        if phrase and phrase not in text_lower:
            return False
    
    # Process the remaining query without quotes
    terms = query_without_quotes.strip()
    if not terms:
        return len(quoted_phrases) > 0  # If only quotes were provided, return True if they matched
    
    # Split by AND, OR, NOT operators while preserving them
    parts = re.split(r'\s+(AND|OR|NOT)\s+', terms, flags=re.IGNORECASE)
    
    # Process parts with operators
    i = 0
    result = True  # Start with True for AND logic
    operator = 'AND'  # Default operator
    
    while i < len(parts):
        part = parts[i].strip()
        
        if part.upper() in ['AND', 'OR', 'NOT']:
            operator = part.upper()
        else:
            term = part.strip().lower()
            if term:
                term_exists = term in text_lower
                
                if operator == 'AND':
                    result = result and term_exists
                elif operator == 'OR':
                    if i == 0:  # First term, initialize result
                        result = term_exists
                    else:
                        result = result or term_exists
                elif operator == 'NOT':
                    result = result and not term_exists
        
        i += 1
    
    return result



def format_date(date_str):
    try:
        dt = datetime.fromisoformat(date_str)
        return dt.strftime("%Y-%m-%d %H:%M")
    except:
        return "Неизвестно"
    return filter_manager.format_date(date_str)


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# --- Маршруты ---
@app.route("/")
def index():
    if "user" not in session:
        return redirect(url_for("login"))
    
    # Получаем параметры фильтрации из URL
    selected_class = request.args.get('class', '')
    selected_parallel = request.args.get('parallel', '')
    selected_subject = request.args.get('subject', '')
    selected_topic = request.args.get('topic', 'Все темы')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    
    # Фильтруем записи по всем параметрам
    filtered_data = advanced_filter_manager.filter_entries(
        selected_class=selected_class,
        selected_parallel=selected_parallel,
        selected_subject=selected_subject,
        selected_topic=selected_topic
    )
    
    # Применяем фильтрацию по дате, если указаны параметры
    if date_from or date_to:
        filtered_temp = []
        for entry in filtered_data:
            entry_date = datetime.fromisoformat(entry['created_at'].replace('Z', '+00:00'))
            if date_from:
                from_date = datetime.strptime(date_from, '%Y-%m-%d')
                if entry_date.date() < from_date.date():
                    continue
            if date_to:
                to_date = datetime.strptime(date_to, '%Y-%m-%d')
                if entry_date.date() > to_date.date():
                    continue
            filtered_temp.append(entry)
        filtered_data = filtered_temp
    
    # Сортируем записи по дате создания (новые сверху)
    filtered_data.sort(key=lambda x: x['created_at'], reverse=True)
    
    # Получаем доступные фильтры
    available_filters = advanced_filter_manager.get_available_filters()
    
    # Получаем статистику по темам
    topic_stats = filter_manager.get_topic_statistics()
    
    # Получаем уникальные значения из существующих записей
    unique_classes = advanced_filter_manager.get_unique_classes()
    unique_parallels = advanced_filter_manager.get_unique_parallels()
    unique_subjects = advanced_filter_manager.get_unique_subjects()
    
    # Загружаем документы из pdf_documents.json
    pdf_documents = []
    try:
        with open('pdf_documents.json', 'r', encoding='utf-8') as f:
            pdf_documents = json.load(f)
    except FileNotFoundError:
        pdf_documents = []
    except Exception as e:
        print(f"Ошибка при загрузке pdf_documents.json: {e}")
        pdf_documents = []
    
    return render_template(
        "index.html",
        entries=filtered_data,
        pdf_documents=pdf_documents,  # Передаем документы из pdf_documents.json в шаблон
        format_date=format_date,
        topics=filter_manager.get_unique_topics(),
        selected_topic=selected_topic,
        topic_stats=topic_stats,
        available_classes=available_filters['classes'],
        available_parallels=available_filters['parallels'],
        available_subjects=available_filters['subjects'],
        selected_class=selected_class,
        selected_parallel=selected_parallel,
        selected_subject=selected_subject,
        date_from=date_from,
        date_to=date_to,
        unique_classes=unique_classes,
        unique_parallels=unique_parallels,
        unique_subjects=unique_subjects
    )


@app.route("/manage-filters", methods=["GET", "POST"])
def manage_filters():
    if "user" not in session or session["user"]["role"] != "admin":
        return "Доступ запрещён", 403

    if request.method == "POST":
        action = request.form.get("action")
        filter_type = request.form.get("filter_type")
        filter_value = request.form.get("filter_value")

        if action == "add" and filter_type and filter_value:
            if filter_type == "class":
                advanced_filter_manager.add_class(filter_value)
            elif filter_type == "parallel":
                advanced_filter_manager.add_parallel(filter_value)
            elif filter_type == "subject":
                advanced_filter_manager.add_subject(filter_value)

        elif action == "remove" and filter_type and filter_value:
            if filter_type == "class":
                advanced_filter_manager.remove_class(filter_value)
            elif filter_type == "parallel":
                advanced_filter_manager.remove_parallel(filter_value)
            elif filter_type == "subject":
                advanced_filter_manager.remove_subject(filter_value)

        return redirect(url_for("manage_filters"))

    available_filters = advanced_filter_manager.get_available_filters()
    return render_template(
        "manage_filters.html",
        classes=available_filters["classes"],
        parallels=available_filters["parallels"],
        subjects=available_filters["subjects"]
    )
    
@app.context_processor
def utility_processor():
    return {"format_date": format_date}

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    return []

def verify_password(password, hash):
    if not hash or not password:
        return False
    try:
        # Хэш уже сохранён как строка → кодируем обратно в байты
        return bcrypt.checkpw(password.encode("utf-8"), hash.encode("utf-8"))
    except Exception as e:
        print(f"[ERROR] Ошибка проверки пароля: {e}")
        return False
def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        users = load_users()
        for user in users:
            if user["username"] == username and verify_password(password, user["password_hash"]):
                session["user"] = {"username": username, "role": user["role"]}
                return redirect(url_for("index"))
        error = "Неверный логин или пароль"
    return render_template("login.html", error=error)

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("index"))





@app.route("/add", methods=["GET", "POST"])
def add_entry():
    if "user" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        # Получаем данные из формы
        title = request.form.get("title", "").strip()
        content = request.form.get("content", "").strip()
        topic = request.form.get("topic", "Без темы").strip()
        class_name = request.form.get("class", "").strip()
        parallel = request.form.get("parallel", "").strip()
        subject = request.form.get("subject", "").strip()
        file = request.files.get("file")

        # Валидация обязательных полей
        if not content:
            return "Содержание не может быть пустым", 400

        # Генерация заголовка, если он пустой
        if not title:
            title = generate_title_from_content(content, filename if 'filename' in locals() else "")
            # Дополнительная проверка, чтобы заголовок не был пустым
            if not title:
                title = "Без заголовка"

        # Загружаем данные и проверяем на дубликаты
        data = load_data()
        if any(entry["title"] == title for entry in data):
            return "Запись с таким заголовком уже существует", 400

        # Обработка файлов (множественная загрузка)
        filenames = []
        files = request.files.getlist("file")
        
        for file in files:
            if file and file.filename:
                if allowed_file(file.filename):
                    try:
                        filename = secure_filename(file.filename)
                        file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                        file.save(file_path)
                        # Дополнительная проверка сохранения файла
                        if not os.path.exists(file_path):
                            raise Exception("Файл не был сохранен на диск")
                        filenames.append(filename)
                        
                        # Если это PDF файл, извлекаем возможные ФГОС заголовки из имени файла
                        if filename.lower().endswith('.pdf'):
                            processor = FGOHeadersProcessor()
                            fgo_header = processor.generate_headers_from_filename(filename)
                            
                            # Обновляем заголовок записи, если в имени файла есть указание на ФГОС
                            if 'фгос' in fgo_header.lower() or 'стандарт' in fgo_header.lower():
                                title = fgo_header
                    except Exception as e:
                        logging.error(f"Ошибка при сохранении файла {filename}: {str(e)}")
                        return "Ошибка при сохранении файла", 500
                else:
                    return "Недопустимый тип файла. Разрешенные типы: pdf, docx, txt, doc, rtf", 400

        # Создаем новую запись
        new_entry = {
            "title": title,
            "content": content,
            "topic": topic,
            "files": filenames,  # Сохраняем список файлов вместо одного файла
            "author": session["user"]["username"],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "id": str(uuid.uuid4())
        }
        
        # Добавляем информацию об образовании, если она есть
        if class_name or parallel or subject:
            new_entry["education_info"] = {}
            if class_name:
                new_entry["education_info"]["class"] = class_name
            if parallel:
                new_entry["education_info"]["parallel"] = parallel
            if subject:
                new_entry["education_info"]["subject"] = subject

        # Сохраняем запись
        try:
            data.append(new_entry)
            save_data(data)

            # Обновляем данные в менеджере фильтрации
            filter_manager.data = data
            advanced_filter_manager.data = data

            # Логируем действие
            log_action(
                username=session["user"]["username"],
                action_type="add",
                target=title,
                details=f"Добавлена новая запись в теме '{topic}'" + (f" с {len(filenames)} файлами" if filenames else "")
            )

            return redirect(url_for("index"))
        except Exception as e:
            logging.error(f"Ошибка при сохранении записи '{title}': {str(e)}")
            # Если были загружены файлы, удаляем их
            for filename in filenames:
                if os.path.exists(os.path.join(app.config["UPLOAD_FOLDER"], filename)):
                    os.remove(os.path.join(app.config["UPLOAD_FOLDER"], filename))
            return "Ошибка при сохранении записи", 500

    # Для GET-запроса отображаем форму добавления
    available_filters = advanced_filter_manager.get_available_filters()
    return render_template(
        "add.html", 
        topics=filter_manager.get_unique_topics(),
        available_classes=available_filters["classes"],
        available_parallels=available_filters["parallels"],
        available_subjects=available_filters["subjects"]
    )


@app.route("/view/<id>")
def view_entry(id):
    data = load_data()
    entry = next((item for item in data if str(item.get('id')) == str(id)), None)
    if entry is None:
        return "Запись не найдена", 404
    
    # Initialize enhanced search system and find similar materials
    enhanced_search_system = initialize_enhanced_search_system(data)
    try:
        material_id = int(hash(entry.get('title', '') + str(entry.get('education_info', {}).get('class', '')) + entry.get('subject', 'общее')) % 10000)
        similar_materials = enhanced_search_system.find_similar_materials(material_id, limit=5)
    except Exception as e:
        print(f"Error finding similar materials: {e}")
        similar_materials = []
    
    return render_template("view.html", entry=entry, similar_materials=similar_materials, format_date=format_date)


@app.route("/edit/<id>", methods=["GET", "POST"])
def edit_entry(id):
    if "user" not in session:
        return redirect(url_for("login"))
    data = load_data()
    entry = next((item for item in data if str(item.get('id')) == str(id)), None)
    if entry is None:
        return "Запись не найдена", 404

    # Проверяем наличие автора, если его нет — устанавливаем значение по умолчанию
    entry_author = entry.get("author", "system")

    # Проверка прав доступа
    if entry_author != session["user"]["username"] and session["user"]["role"] != "admin" and session["user"]["role"] != "editor":
        return "Доступ запрещён", 403

    if request.method == "POST":
        new_title = request.form.get("title", "").strip()
        new_topic = request.form.get("topic", "Без темы").strip()
        new_content = request.form.get("content", "").strip()
        files = request.files.getlist("file")

        # Генерация заголовка, если он пустой
        if not new_title:
            new_title = generate_title_from_content(new_content, entry.get("file", ""))

        if not new_title or not new_content:
            return "Поля не могут быть пустыми", 400

        # Проверка на дубликаты (кроме текущей записи)
        if any(e["title"] == new_title and e != entry for e in data):
            return "Дубликат заголовка", 400

        # Сохраняем старые значения для аудита
        old_title = entry["title"]
        old_topic = entry["topic"]
        old_content = entry["content"]

        # Обновляем запись
        entry["title"] = new_title
        entry["topic"] = new_topic
        entry["content"] = new_content
        entry["author"] = session["user"]["username"]  # Устанавливаем автора
        entry["updated_at"] = datetime.now().isoformat()

        # Обработка файлов (множественная загрузка)
        if files and any(f for f in files if f.filename):  # Если есть хотя бы один файл
            # Удаляем старые файлы, если они есть
            old_files = entry.get("files", [])
            if old_files:
                for old_file in old_files:
                    old_path = os.path.join(app.config["UPLOAD_FOLDER"], old_file)
                    if os.path.exists(old_path):
                        os.remove(old_path)
            
            # Сохраняем новые файлы
            new_filenames = []
            for file in files:
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
                    new_filenames.append(filename)
            
            # Обновляем поле с файлами в записи
            entry["files"] = new_filenames

        save_data(data)

        # Обновляем данные в менеджере фильтрации
        filter_manager.data = data
        advanced_filter_manager.data = data

        # Запись в аудит
        log_action(
            username=session["user"]["username"],
            action_type="edit",
            target=old_title,
            details=f"Изменение записи",
            old_value=old_content[:100] + "..." if len(old_content) > 100 else old_content,
            new_value=new_content[:100] + "..." if len(new_content) > 100 else new_content
        )
        
        return redirect(url_for("index"))

    return render_template("edit.html", entry=entry, index=index, entry_id=entry.get('id'), topics=filter_manager.get_unique_topics())


@app.route("/delete/<id>")
def delete_entry(id):
    if "user" not in session:
        return redirect(url_for("login"))

    data = load_data()
    entry = next((item for item in data if str(item.get('id')) == str(id)), None)
    if entry is None:
        return "Запись не найдена", 404

    if entry["author"] != session["user"]["username"] and session["user"]["role"] != "admin" and session["user"]["role"] != "editor":
        return "Доступ запрещён", 403
    log_action(
        username=session["user"]["username"],
        action_type="delete",
        target=entry["title"],
        details="Удалена запись из базы знаний"
    )

    old_file = entry.get("file")
    if old_file:
        old_path = os.path.join(app.config["UPLOAD_FOLDER"], old_file)
        if os.path.exists(old_path):
            os.remove(old_path)
    
    data.remove(entry)
    save_data(data)
    # Обновляем данные в менеджере фильтров после удаления записи
    advanced_filter_manager.data = data
    return redirect(url_for("index"))


import logging
logging.basicConfig(level=logging.DEBUG)


@app.route("/uploads/<filename>")
def uploaded_file(filename):
    from werkzeug.utils import secure_filename
    safe_filename = secure_filename(filename)
    file_path = os.path.join(app.config["UPLOAD_FOLDER"], safe_filename)
    try:
        if not os.path.isfile(file_path):
            return "Файл не найден", 404
        return send_from_directory(app.config["UPLOAD_FOLDER"], filename)
    except FileNotFoundError:
        return "Файл не найден", 404
    except Exception as e:
        return f"Произошла ошибка: {e}", 500


@app.route("/search", methods=["POST"])
def search_entry():
    query = request.form.get("query", "").strip()
    selected_topic = request.form.get("topic", "Все темы")

    if not query:
        return redirect(url_for("index"))

    # Redirect to GET route to have clean URLs that can be shared
    return redirect(url_for('search_entry_get', query=query, topic=selected_topic))


@app.route("/search", methods=["GET"])
def search_entry_get():
    query = request.args.get("query", "").strip()
    selected_topic = request.args.get("topic", "Все темы")

    if not query:
        return redirect(url_for("index"))

    # Загружаем данные (это также инициализирует систему семантического поиска)
    data = load_data()

    results = []
    
    # Извлекаем параметры фильтрации из поискового запроса
    extracted_class, extracted_subject = extract_filters_from_query(query)
    
    # Сначала выполняем синтаксический поиск
    for entry in data:
        # Применяем извлеченные фильтры
        if extracted_class:
            entry_class = entry.get("education_info", {}).get("class", "")
            if entry_class != extracted_class:
                continue
        
        if extracted_subject:
            entry_subject = entry.get("education_info", {}).get("subject", "")
            if entry_subject != extracted_subject:
                continue

        # Фильтруем по теме, если выбрана конкретная тема
        if selected_topic != "Все темы" and selected_topic:
            if entry.get("topic", "Без темы") != selected_topic:
                continue

        # Используем синтаксически-осознанный поиск в заголовке, содержании и файлах
        search_in_title = syntax_aware_search(entry["title"], query)
        search_in_content = syntax_aware_search(entry["content"], query)
        
        # Поиск в файлах, если они есть
        search_in_files = False
        if "files" in entry and entry["files"]:
            for filename in entry["files"]:
                file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                if os.path.exists(file_path):
                    try:
                        if file_path.endswith('.pdf'):
                            import PyPDF2
                            with open(file_path, 'rb') as f:
                                pdf_reader = PyPDF2.PdfReader(f)
                                file_content = ""
                                for page in pdf_reader.pages:
                                    file_content += page.extract_text()
                                search_in_files = syntax_aware_search(file_content, query)
                        elif file_path.endswith(('.txt', '.docx')):
                            with open(file_path, 'r', encoding='utf-8') as f:
                                file_content = f.read()
                                search_in_files = syntax_aware_search(file_content, query)
                    except Exception as e:
                        print(f"Ошибка при чтении файла {file_path}: {e}")
        
        # Поиск в FGOs списках
        search_in_fgoss = False
        if "fgo_list" in entry and entry["fgo_list"]:
            fgos_content = " ".join(entry["fgo_list"])
            search_in_fgoss = syntax_aware_search(fgos_content, query)
        
        # Поиск в pdf_documents.json
        search_in_pdf_docs = False
        pdf_docs_results = []
        try:
            with open('pdf_documents.json', 'r', encoding='utf-8') as f:
                pdf_documents = json.load(f)
            
            for doc in pdf_documents:
                # Проверяем точное совпадение заголовка перед синтаксическим поиском
                doc_title = doc.get('title', '').lower()
                doc_filename = doc.get('filename', '').lower()
                doc_extracted_title = doc.get('extracted_title', '').lower()
                
                # Если запрос полностью содержится в заголовке документа, считаем это совпадением
                query_lower = query.lower()
                if query_lower in doc_title or query_lower in doc_filename or query_lower in doc_extracted_title:
                    search_in_pdf_docs = True
                    pdf_docs_results.append(doc)
                    continue  # Добавляем документ в результаты
                
                # Также проверяем через синтаксический поиск
                doc_text = f"{doc_title} {doc_filename} {doc_extracted_title}"
                if syntax_aware_search(doc_text, query):
                    search_in_pdf_docs = True
                    pdf_docs_results.append(doc)
                    continue
        except FileNotFoundError:
            search_in_pdf_docs = False
            pdf_docs_results = []
        except Exception as e:
            print(f"Ошибка при поиске в pdf_documents.json: {e}")
            search_in_pdf_docs = False
            pdf_docs_results = []

        if search_in_title or search_in_content or search_in_files or search_in_fgoss or search_in_pdf_docs:
            results.append(entry)
    
    # Если синтаксический поиск не дал результатов, выполняем семантический поиск
    if not results and not pdf_docs_results:
        results = perform_integrated_search(query, search_type="semantic", top_k=20)
    elif pdf_docs_results:
        # Добавляем найденные документы из pdf_documents.json к результатам
        for doc in pdf_docs_results:
            # Преобразуем документ в формат, подходящий для отображения в шаблоне
            formatted_doc = {
                "id": f"pdf_{doc.get('id', '')}",
                "title": doc.get('title', ''),
                "content": doc.get('extracted_title', ''),
                "topic": "Нормативные документы",
                "created_at": doc.get('download_date', ''),
                "updated_at": doc.get('download_date', ''),
                "author": "Система",
                "file": doc.get('filename', ''),
                "url": doc.get('url', '')
            }
            results.append(formatted_doc)

    # Получаем статистику по темам
    topic_stats = filter_manager.get_topic_statistics()

    return render_template("index.html", entries=results, is_search=True, format_date=format_date, query=query,
                           topics=filter_manager.get_unique_topics(), selected_topic=selected_topic,
                           search_query=query, topic_stats=topic_stats, pdf_documents=pdf_docs_results)


def extract_filters_from_query(query):
    """
    Извлекает информацию о классе и предмете из поискового запроса.
    Например, из запроса "задания для 1 класса по французскому" извлекает класс "1" и предмет "Французский язык".
    """
    import re
    
    # Приводим запрос к нижнему регистру для поиска
    lower_query = query.lower()
    
    # Ищем паттерн "для X класса" или "X класс"
    class_pattern = r'(?:для\s+)?(\d+)\s*(?:-й|-го|-ый|-ой|-я)?\s*класс'
    class_match = re.search(class_pattern, lower_query)
    extracted_class = class_match.group(1) if class_match else None
    
    # Словарь соответствия названий предметов
    subject_mapping = {
        'русский': 'Русский язык',
        'английский': 'Английский язык',
        'немецкий': 'Немецкий язык',
        'французский': 'Французский язык',
        'математика': 'Математика',
        'литература': 'Литература',
        'история': 'История',
        'география': 'География',
        'биология': 'Биология',
        'химия': 'Химия',
        'физика': 'Физика',
        'информатика': 'Информатика',
        'обществознание': 'Обществознание',
        'экономика': 'Экономика',
        'право': 'Право',
        'обж': 'ОБЖ',
        'физкультура': 'Физкультура',
        'изо': 'ИЗО',
        'музыка': 'Музыка',
        'технология': 'Технология',
        'фгос': 'ФГОС',
        'стандарт': 'Федеральные государственные образовательные стандарты'
    }
    
    # Ищем предмет в запросе
    extracted_subject = None
    for key, value in subject_mapping.items():
        if key in lower_query:
            extracted_subject = value
            break
    
    # Если в запросе есть "по" + название предмета
    if not extracted_subject:
        for key, value in subject_mapping.items():
            subject_pattern = r'по\s+' + key
            if re.search(subject_pattern, lower_query):
                extracted_subject = value
                break

    return extracted_class, extracted_subject


def generate_title_from_content(content, filename=""):
    """
    Генерирует заголовок из первых слов содержания
    Если в content есть "Заголовок не найден", используем имя файла для генерации заголовка
    """
    if not content:
        if filename:
            # Remove extension and convert underscores/hyphens to spaces
            title = os.path.splitext(filename)[0].replace('_', ' ').replace('-', ' ')
            # Convert to more readable Russian text if possible
            title = make_russian_readable(title)
            return title[:100]  # Ограничиваем длину
        return "Без заголовка"
    
    # Check if content contains "Заголовок не найден" or similar
    if "Заголовок не найден" in content or "No title found" in content.lower():
        if filename:
            # Use filename to generate a meaningful title
            title = os.path.splitext(filename)[0].replace('_', ' ').replace('-', ' ')
            # Convert to more readable Russian text if possible
            title = make_russian_readable(title)
            return title[:100]  # Ограничиваем длину
        return "Без заголовка"
    
    words = content.strip().split()
    title = ' '.join(words[:10])  # Первые 10 слов
    if len(title) > 100:  # Ограничиваем длину
        title = title[:100] + "..."
    
    # If we have a filename, append it to the title if the original content was unhelpful
    if filename and ("Заголовок не найден" in content or len(content.strip()) < 20):
        file_part = os.path.splitext(filename)[0].replace('_', ' ').replace('-', ' ')
        file_part = make_russian_readable(file_part)
        combined_title = f"{title} - {file_part}"[:100]
        return combined_title
    
    return title


def make_russian_readable(text):
    """Convert filename-friendly text to more readable Russian text"""
    # Some common replacements to make filenames more readable in Russian
    replacements = {
        "fgos": "ФГОС",
        "prikaz": "Приказ",
        "obrazovanie": "Образование",
        "standart": "Стандарт",
        "metodicheskie": "Методические",
        "rekomendaczii": "Рекомендации",
        "organizacii": "Организации",
        "procedur": "Процедур",
        "oczenochnyh": "Оценочных",
        "adaptaczionnyj": "Адаптационный",
        "period": "Период",
        "sentyabr": "Сентябрь",
        "oktyabr": "Октябрь",
        "noo": "НОО",
        "ooo": "ООО",
        "soo": "СОО",
        "ministerstvo": "Министерство",
        "prosveshenie": "Просвещение",
        "rossijskoj": "Российской",
        "federacii": "Федерации",
        "ob": "Об",
        "i": "И",
        "na": "На",
        "po": "По",
        "ot": "От",
        "№": "Номер ",
        " ": " "
    }
    
    result = text
    for old, new in replacements.items():
        result = result.replace(old, new)
    
    # Capitalize first letter of each sentence
    result = '. '.join(s.capitalize() for s in result.split('. '))
    return result



def find_entry_index_by_id(data, entry_id):
    """Находит индекс записи по её ID"""
    for i, entry in enumerate(data):
        if entry.get("id") == entry_id:
            return i
    return None


def find_entry_by_id(data, entry_id):
    """Находит запись по её ID"""
    for entry in data:
        if entry.get("id") == entry_id:
            return entry
    return None


@app.route("/view/id/<entry_id>")
def view_entry_by_id(entry_id):
    data = load_data()
    entry = find_entry_by_id(data, entry_id)
    if not entry:
        return "Запись не найдена", 404
    
    # Initialize enhanced search system and find similar materials
    enhanced_search_system = initialize_enhanced_search_system(data)
    try:
        material_id = int(hash(entry.get('title', '') + str(entry.get('education_info', {}).get('class', '')) + entry.get('subject', 'общее')) % 10000)
        similar_materials = enhanced_search_system.find_similar_materials(material_id, limit=5)
    except Exception as e:
        print(f"Error finding similar materials: {e}")
        similar_materials = []
    
    return render_template("view.html", entry=entry, similar_materials=similar_materials, format_date=format_date)


@app.route("/edit/id/<entry_id>", methods=["GET", "POST"])
def edit_entry_by_id(entry_id):
    if "user" not in session:
        return redirect(url_for("login"))
    data = load_data()
    entry = find_entry_by_id(data, entry_id)
    if not entry:
        return "Запись не найдена", 404

    # Проверяем наличие автора, если его нет — устанавливаем значение по умолчанию
    entry_author = entry.get("author", "system")

    # Проверка прав доступа
    if entry_author != session["user"]["username"] and session["user"]["role"] != "admin" and session["user"]["role"] != "editor":
        return "Доступ запрещён", 403

    if request.method == "POST":
        new_title = request.form.get("title", "").strip()
        new_topic = request.form.get("topic", "Без темы").strip()
        new_content = request.form.get("content", "").strip()
        files = request.files.getlist("file")

        # Генерация заголовка, если он пустой
        if not new_title:
            new_title = generate_title_from_content(new_content, entry.get("file", ""))

        if not new_title or not new_content:
            return "Поля не могут быть пустыми", 400

        # Проверка на дубликаты (кроме текущей записи)
        if any(e["title"] == new_title and e.get("id") != entry_id for e in data):
            return "Дубликат заголовка", 400

        # Сохраняем старые значения для аудита
        old_title = entry["title"]
        old_topic = entry["topic"]
        old_content = entry["content"]

        # Обновляем запись
        entry["title"] = new_title
        entry["topic"] = new_topic
        entry["content"] = new_content
        entry["author"] = session["user"]["username"]  # Устанавливаем автора
        entry["updated_at"] = datetime.now().isoformat()

        # Обработка файлов (множественная загрузка)
        if files and any(f for f in files if f.filename):  # Если есть хотя бы один файл
            # Удаляем старые файлы, если они есть
            old_files = entry.get("files", [])
            if old_files:
                for old_file in old_files:
                    old_path = os.path.join(app.config["UPLOAD_FOLDER"], old_file)
                    if os.path.exists(old_path):
                        os.remove(old_path)
            
            # Сохраняем новые файлы
            new_filenames = []
            for file in files:
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
                    new_filenames.append(filename)
            
            # Обновляем поле с файлами в записи
            entry["files"] = new_filenames

        save_data(data)

        # Запись в аудит
        log_action(
            username=session["user"]["username"],
            action_type="edit",
            target=old_title,
            details=f"Изменение записи",
            old_value=old_content[:100] + "..." if len(old_content) > 100 else old_content,
            new_value=new_content[:100] + "..." if len(new_content) > 100 else new_content
        )
        
        filter_manager.data = data
        return redirect(url_for("index"))

    return render_template("edit.html", entry=entry, entry_id=entry_id, topics=filter_manager.get_unique_topics())


@app.route("/delete/id/<entry_id>")
def delete_entry_by_id(entry_id):
    if "user" not in session:
        return redirect(url_for("login"))

    data = load_data()
    entry_index = find_entry_index_by_id(data, entry_id)
    if entry_index is None:
        return "Запись не найдена", 404

    entry = data[entry_index]
    if entry["author"] != session["user"]["username"] and session["user"]["role"] != "admin" and session["user"]["role"] != "editor":
        return "Доступ запрещён", 403
        
    log_action(
        username=session["user"]["username"],
        action_type="delete",
        target=entry["title"],
        details="Удалена запись из базы знаний"
    )

    old_file = entry.get("file")
    if old_file:
        old_path = os.path.join(app.config["UPLOAD_FOLDER"], old_file)
        if os.path.exists(old_path):
            os.remove(old_path)
    del data[entry_index]
    save_data(data)
    # Обновляем данные в менеджере фильтров после удаления записи
    advanced_filter_manager.data = data
    return redirect(url_for("index"))


@app.route("/manage-users", methods=["GET", "POST"])
def manage_users():
    if "user" not in session or session["user"]["role"] != "admin":
        return "Доступ запрещён", 403

    if request.method == "POST":
        action = request.form.get("action")
        username = request.form.get("username")

        users = load_users()

        if action == "add":
            new_username = request.form.get("username")
            password = request.form.get("password")
            role = request.form.get("role")

            # Проверяем, существует ли уже пользователь с таким именем
            if any(user["username"] == new_username for user in users):
                # Возвращаем на страницу с сообщением об ошибке
                users = load_users()
                return render_template("manage_users.html", users=users, error="Пользователь с таким именем уже существует")
            else:
                hashed_password = hash_password(password)
                new_user = {
                    "username": new_username,
                    "password_hash": hashed_password,
                    "role": role
                }
                users.append(new_user)
                
                # Логируем действие
                log_action(
                    username=session["user"]["username"],
                    action_type="add_user",
                    target=new_username,
                    details=f"Создан пользователь с ролью {role}"
                )

        elif action == "update_role":
            role = request.form.get("role")
            for user in users:
                if user["username"] == username:
                    old_role = user["role"]
                    user["role"] = role
                    
                    # Логируем изменение роли
                    log_action(
                        username=session["user"]["username"],
                        action_type="update_user_role",
                        target=username,
                        details=f"Изменена роль с {old_role} на {role}"
                    )
                    break

        elif action == "delete":
            # Не позволяем администратору удалить самого себя
            if username == session["user"]["username"]:
                return "Нельзя удалить самого себя", 400
            
            users = [user for user in users if user["username"] != username]
            
            # Логируем удаление пользователя
            log_action(
                username=session["user"]["username"],
                action_type="delete_user",
                target=username,
                details="Пользователь удален из системы"
            )

        # Сохраняем обновленный список пользователей
        with open(USERS_FILE, "w") as f:
            json.dump(users, f)

    users = load_users()
    return render_template("manage_users.html", users=users)


# Глобальная переменная для отслеживания статуса последнего запуска
last_run_status = {"running": False, "completed": False, "progress": "", "timestamp": None}

def run_scraper_in_thread():
    """Запуск скрапера в отдельном потоке"""
    global last_run_status
    last_run_status["running"] = True
    last_run_status["completed"] = False
    last_run_status["progress"] = "Начинаю процесс парсинга..."
    last_run_status["timestamp"] = time.strftime("%Y-%m-%d %H:%M:%S")
    
    try:
        scraper = PDFScraper()
        scraper.process_pdfs()
        last_run_status["progress"] = "Процесс завершен успешно!"
    except Exception as e:
        last_run_status["progress"] = f"Ошибка: {str(e)}"
    finally:
        last_run_status["running"] = False
        last_run_status["completed"] = True

def schedule_periodic_updates():
    """Функция для периодического запуска обновления (запуск в фоновом режиме)"""
    while True:
        # Ждем 24 часа перед следующим запуском (в реальном приложении можно использовать более точный планировщик)
        time.sleep(24 * 60 * 60)  # 24 часа в секундах
        
        # Запускаем обновление
        if not last_run_status["running"]:
            print("Автоматический запуск обновления системы...")
            scraper = PDFScraper()
            scraper.process_pdfs()

def start_background_tasks():
    schedule.every().monday.at("00:00").do(sync_edsoo)
    
    # Запускаем фоновый поток для периодических обновлений PDF
    scheduler_thread = threading.Thread(target=schedule_periodic_updates, daemon=True)
    scheduler_thread.start()
    
    thread = threading.Thread(target=background_job, daemon=True)
    thread.start()

@app.route('/api/status')
def get_status():
    """API endpoint для получения статуса последнего запуска"""
    return jsonify(last_run_status)

@app.route('/api/run', methods=['POST'])
def run_scraper_api():
    """Запуск процесса скрапинга по запросу"""
    global last_run_status
    if not last_run_status["running"]:
        thread = threading.Thread(target=run_scraper_in_thread)
        thread.start()
        return jsonify({"status": "started", "message": "Процесс запущен"})
    else:
        return jsonify({"status": "error", "message": "Процесс уже запущен"})

@app.route('/update-system')
def update_system():
    """Страница для обновления системы"""
    if "user" not in session or session["user"]["role"] != "admin":
        return "Доступ запрещён", 403
    return render_template('update_system.html', status=last_run_status)

if __name__ == "__main__":
    start_scheduler(app)  # Передаем app в start_scheduler
    app.run(debug=True)