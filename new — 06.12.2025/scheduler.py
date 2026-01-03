
import schedule
import time
import threading
from flask import current_app

def background_job(app):
    with app.app_context():  # Явно передаем и используем app
        while True:
            schedule.run_pending()
            time.sleep(60)  # Проверка каждую минуту

def start_scheduler(app):
    # Регистрация задач
    from utils import sync_edsoo
    schedule.every().monday.at("00:00").do(sync_edsoo)

    # Запуск в отдельном потоке
    def run_scheduler():
        with app.app_context():  # Убедимся, что контекст доступен
            while True:
                schedule.run_pending()
                time.sleep(60)

    thread = threading.Thread(target=run_scheduler, daemon=True)
    thread.start()