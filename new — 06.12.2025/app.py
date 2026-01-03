import json
import os
import threading
from datetime import datetime
import audit_system
import bcrypt
import schedule
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, session
from werkzeug.utils import secure_filename
from audit_system import init_audit_system, log_action
from auth import auth
from data_utils import load_data
from scheduler import background_job, start_scheduler
from utils import extract_content_from_pdf, fetch_edsoo_documents, download_document, logger, sync_edsoo
from Filter import FilterManager
from forms import KnowledgeEntryForm
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

    # Сортируем по времени (новые сначала)
    logs.sort(key=lambda x: x["timestamp"], reverse=True)

    # Генерируем отчет
    report = audit_system.generate_audit_report()

    return render_template("audit.html", logs=logs, report=report, format_date=format_date)


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
            return data
    return []

def save_data(data):
    for entry in data:
        if "author" not in entry or not entry["author"]:
            entry["author"] = "system"
    with open(DATA_FILE, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)



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
    entries = load_data()
    return render_template("index.html", entries=entries, format_date=format_date)

    # Получаем выбранную тему из параметров запроса
    selected_topic = request.args.get('topic', "Все темы")

    # Фильтруем записи по теме
    filtered_data = filter_manager.filter_by_topic(selected_topic)

    # Получаем статистику по темам
    topic_stats = filter_manager.get_topic_statistics()

    # Передаем данные в шаблон
    return render_template("index.html",
                           entries=filtered_data,
                           format_date=format_date,
                           topics=filter_manager.get_unique_topics(),
                           selected_topic=selected_topic,
                           topic_stats=topic_stats)


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
            "updated_at": datetime.now().isoformat()
        }

        # Сохраняем запись
        try:
            data.append(new_entry)
            save_data(data)

            # Обновляем данные в менеджере фильтрации
            filter_manager.data = data

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
    return render_template("add.html", topics=filter_manager.get_unique_topics())


@app.route("/view/<int:index>")
def view_entry(index):
    data = load_data()
    if index < 0 or index >= len(data):
        return "Запись не найдена", 404
    entry = data[index]
    return render_template("view.html", entry=entry, format_date=format_date)


@app.route("/edit/<int:index>", methods=["GET", "POST"])
def edit_entry(index):
    if "user" not in session:
        return redirect(url_for("login"))
    data = load_data()
    if index < 0 or index >= len(data):
        return "Запись не найдена", 404
    entry = data[index]

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


        # Запись в аудит
        log_action(
            username=session["user"]["username"],
            action_type="edit",
            target=old_title,
            details=f"Изменение записи",
            old_value=old_content[:100] + "..." if len(old_content) > 100 else old_content,
            new_value=new_content[:100] + "..." if len(new_content) > 100 else new_content
        )
        ilter_manager.data = data
        return redirect(url_for("index"))
        return redirect(url_for("index"))

    return render_template("edit.html", entry=entry, index=index, topics=filter_manager.get_unique_topics())

    data = load_data()
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                for entry in data:
                    if "created_at" not in entry:
                        entry["created_at"] = datetime.now().isoformat()
                    if "updated_at" not in entry:
                        entry["updated_at"] = entry["created_at"]
                    # Добавляем автора по умолчанию, если его нет
                    if "author" not in entry:
                        entry["author"] = "system"
                return data
        except json.JSONDecodeError:
            return []
    return []

    entry = data[index]

    if entry["author"] != session["user"]["username"] and session["user"]["role"] != "admin":
        return "Нет прав", 403

    if request.method == "POST":
        new_title = request.form.get("title", "").strip()
        new_content = request.form.get("content", "").strip()
        file = request.files.get("file")

        # Генерация заголовка при редактировании
        if not new_title:
            new_title = generate_title_from_content(new_content)

        if not new_title or not new_content:
            return "Заголовок и содержание не могут быть пустыми", 400

        if any(e["title"] == new_title and e != entry for e in data):
            return "Дубликат заголовка", 400

        entry["title"] = new_title
        entry["content"] = new_content
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

        log_action(
            username=session["user"]["username"],
            action_type="edit",
            target=old_title,
            details=f"Изменение записи",
            old_value=old_content[:100] + "..." if len(old_content) > 100 else old_content,
            new_value=new_content[:100] + "..." if len(new_content) > 100 else new_content
        )
        
        return redirect(url_for("index"))

    return render_template("edit.html", entry=entry, index=index)


@app.route("/delete/<int:index>")
def delete_entry(index):
    if "user" not in session:
        return redirect(url_for("login"))

    data = load_data()
    if index < 0 or index >= len(data):
        return "Запись не найдена", 404

    entry = data[index]
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
    del data[index]
    save_data(data)
    return redirect(url_for("index"))

    del data[index]
    save_data(data)
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
    query = request.form.get("query", "").strip().lower()
    selected_topic = request.form.get("topic", "Все темы")

    if not query:
        return redirect(url_for("index"))

    data = load_data()
    results = []

    for entry in data:
        # Фильтруем по теме, если выбрана конкретная тема
        if selected_topic != "Все темы" and selected_topic:
            if entry.get("topic", "Без темы") != selected_topic:
                continue

        # Проверяем совпадение в заголовке или содержании
        if query in entry["title"].lower() or query in entry["content"].lower():
            results.append(entry)

    # Получаем статистику по темам
    topic_stats = filter_manager.get_topic_statistics()

    return render_template("index.html", entries=results, is_search=True,format_date=format_date,query=query,
                           topics=filter_manager.get_unique_topics(), selected_topic=selected_topic,
                           search_query=query, topic_stats=topic_stats)


def generate_title_from_content(content):
    """Генерирует заголовок из первых слов содержания"""
    if not content:
        return "Без заголовка"
    words = content.strip().split()
    title = ' '.join(words[:10])  # Первые 10 слов
    if len(title) > 100:  # Ограничиваем длину
        title = title[:100] + "..."
    return title



def start_background_tasks():
    schedule.every().monday.at("00:00").do(sync_edsoo)
    thread = threading.Thread(target=background_job, daemon=True)
    thread.start()

if __name__ == "__main__":
    start_scheduler(app)  # Передаем app в start_scheduler
    app.run(debug=True)
if __name__ == "__main__":
    filter_manager.add_topic_field()
    app.run(debug=True)

if __name__ == "__main__":
    start_background_tasks()
    app.run(debug=True)
if __name__ == "__main__":
    app.run(debug=True)