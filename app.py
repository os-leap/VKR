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
from Filter import FilterManager
from advanced_filter import AdvancedFilterManager
from forms import KnowledgeEntryForm
from simple_semantic_search_integration import initialize_search_system, perform_integrated_search
from backup_system import backup_system, create_daily_backup
init_audit_system()


app = Flask(__name__)

app.secret_key = 'your_secret_key_here'  # Для сессий


# --- Настройка приложения ---
USERS_FILE = "users.json"
DATA_FILE = "knowledge_base.json"
app.config["UPLOAD_FOLDER"] = "static/uploads"
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
ALLOWED_EXTENSIONS = {"pdf", "docx", "txt", "doc", "rtf"}

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

    # Генерируем отчет
    report = audit_system.generate_audit_report()

    return render_template("audit.html", logs=logs, report=report, format_date=format_date)


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
    
    return render_template(
        "index.html",
        entries=filtered_data,
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
            title = generate_title_from_content(content)
            # Дополнительная проверка, чтобы заголовок не был пустым
            if not title:
                title = "Без заголовка"

        # Загружаем данные и проверяем на дубликаты
        data = load_data()
        if any(entry["title"] == title for entry in data):
            return "Запись с таким заголовком уже существует", 400

        # Обработка файла
        filename = None
        if file and file.filename:
            if allowed_file(file.filename):
                try:
                    filename = secure_filename(file.filename)
                    file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                    file.save(file_path)
                    # Дополнительная проверка сохранения файла
                    if not os.path.exists(file_path):
                        raise Exception("Файл не был сохранен на диск")
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
            "file": filename,
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
                details=f"Добавлена новая запись в теме '{topic}'" + (" с файлом" if filename else "")
            )

            return redirect(url_for("index"))
        except Exception as e:
            logging.error(f"Ошибка при сохранении записи '{title}': {str(e)}")
            # Если был загружен файл, удаляем его
            if filename and os.path.exists(os.path.join(app.config["UPLOAD_FOLDER"], filename)):
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
    return render_template("view.html", entry=entry, format_date=format_date)


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
    if entry_author != session["user"]["username"] and session["user"]["role"] != "admin":
        return "Доступ запрещён", 403

    if request.method == "POST":
        new_title = request.form.get("title", "").strip()
        new_topic = request.form.get("topic", "Без темы").strip()
        new_content = request.form.get("content", "").strip()
        file = request.files.get("file")

        # Генерация заголовка, если он пустой
        if not new_title:
            new_title = generate_title_from_content(new_content)

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

        # Обработка файла
        if file and allowed_file(file.filename):
            old_file = entry.get("file")
            if old_file:
                old_path = os.path.join(app.config["UPLOAD_FOLDER"], old_file)
                if os.path.exists(old_path):
                    os.remove(old_path)
            entry["file"] = secure_filename(file.filename)
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], entry["file"]))

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

    if entry["author"] != session["user"]["username"] and session["user"]["role"] != "admin":
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
    # Очищаем кэш фильтров после удаления записи
    advanced_filter_manager.clear_cache()
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
    search_type = request.form.get("search_type", "syntax")  # Получаем тип поиска из формы

    if not query:
        return redirect(url_for("index"))

    # Redirect to GET route to have clean URLs that can be shared
    return redirect(url_for('search_entry_get', query=query, topic=selected_topic, search_type=search_type))


@app.route("/search", methods=["GET"])
def search_entry_get():
    query = request.args.get("query", "").strip()
    selected_topic = request.args.get("topic", "Все темы")
    search_type = request.args.get("search_type", "syntax")  # Добавляем параметр типа поиска

    if not query:
        return redirect(url_for("index"))

    # Загружаем данные (это также инициализирует систему семантического поиска)
    data = load_data()

    results = []
    
    # Сначала выполняем синтаксический поиск
    if search_type == "semantic":
        # Используем семантический поиск
        results = perform_integrated_search(query, search_type="semantic", top_k=20)
    else:
        # Используем синтаксический поиск
        for entry in data:
            # Фильтруем по теме, если выбрана конкретная тема
            if selected_topic != "Все темы" and selected_topic:
                if entry.get("topic", "Без темы") != selected_topic:
                    continue

            # Используем синтаксически-осознанный поиск в заголовке и содержании
            search_in_title = syntax_aware_search(entry["title"], query)
            search_in_content = syntax_aware_search(entry["content"], query)

            if search_in_title or search_in_content:
                results.append(entry)
    
    # Если синтаксический поиск не дал результатов, выполняем семантический поиск
    if not results and search_type == "syntax":
        results = perform_integrated_search(query, search_type="semantic", top_k=20)

    # Получаем статистику по темам
    topic_stats = filter_manager.get_topic_statistics()

    return render_template("index.html", entries=results, is_search=True, format_date=format_date, query=query,
                           topics=filter_manager.get_unique_topics(), selected_topic=selected_topic,
                           search_query=query, topic_stats=topic_stats, search_type=search_type)


def generate_title_from_content(content):
    """Генерирует заголовок из первых слов содержания"""
    if not content:
        return "Без заголовка"
    words = content.strip().split()
    title = ' '.join(words[:10])  # Первые 10 слов
    if len(title) > 100:  # Ограничиваем длину
        title = title[:100] + "..."
    return title



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
    return render_template("view.html", entry=entry, format_date=format_date)


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
    if entry_author != session["user"]["username"] and session["user"]["role"] != "admin":
        return "Доступ запрещён", 403

    if request.method == "POST":
        new_title = request.form.get("title", "").strip()
        new_topic = request.form.get("topic", "Без темы").strip()
        new_content = request.form.get("content", "").strip()
        file = request.files.get("file")

        # Генерация заголовка, если он пустой
        if not new_title:
            new_title = generate_title_from_content(new_content)

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

        # Обработка файла
        if file and allowed_file(file.filename):
            old_file = entry.get("file")
            if old_file:
                old_path = os.path.join(app.config["UPLOAD_FOLDER"], old_file)
                if os.path.exists(old_path):
                    os.remove(old_path)
            entry["file"] = secure_filename(file.filename)
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], entry["file"]))

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
    if entry["author"] != session["user"]["username"] and session["user"]["role"] != "admin":
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
    # Очищаем кэш фильтров после удаления записи
    advanced_filter_manager.clear_cache()
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


def start_background_tasks():
    schedule.every().monday.at("00:00").do(sync_edsoo)
    thread = threading.Thread(target=background_job, daemon=True)
    thread.start()

if __name__ == "__main__":
    start_scheduler(app)  # Передаем app в start_scheduler
    app.run(debug=True)