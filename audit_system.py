
import json
import os
from datetime import datetime

# Путь к файлу аудита
AUDIT_LOG_FILE = "audit_logs.json"


def init_audit_system():
    """
    Инициализация системы аудита.
    Создает файл аудита, если он не существует.
    """
    if not os.path.exists(AUDIT_LOG_FILE):
        with open(AUDIT_LOG_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=4)
    return True


def log_action(username, action_type, target, details=None, old_value=None, new_value=None, entry_id=None):
    """
    Записывает действие в систему аудита.

    :param username: Имя пользователя, совершившего действие
    :param action_type: Тип действия (add, edit, delete, sync, backup_create, backup_restore, selective_restore)
    :param target: Цель действия (название записи или ID)
    :param details: Дополнительные детали
    :param old_value: Старое значение (для редактирования)
    :param new_value: Новое значение (для редактирования)
    :param entry_id: ID записи (опционально)
    """
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "username": username,
        "action_type": action_type,
        "target": target,
        "details": details or "",
        "entry_id": entry_id  # Добавляем ID записи для более точного восстановления
    }

    # Добавляем информацию о старом и новом значении для действий редактирования
    if action_type in ["edit", "delete"]:
        log_entry["old_value"] = old_value
        log_entry["new_value"] = new_value

    # Загружаем существующие логи
    logs = load_audit_logs()

    # Добавляем новую запись
    logs.append(log_entry)

    # Сохраняем обновленные логи
    with open(AUDIT_LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(logs, f, ensure_ascii=False, indent=4)


def load_audit_logs():
    """
    Загружает логи аудита из файла.

    :return: Список записей аудита
    """
    if os.path.exists(AUDIT_LOG_FILE):
        try:
            with open(AUDIT_LOG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            # Если файл поврежден, создаем новый
            init_audit_system()
            return []
    return []


def get_user_actions(username, limit=None):
    """
    Получает все действия пользователя.

    :param username: Имя пользователя
    :param limit: Ограничение количества записей
    :return: Список действий пользователя
    """
    logs = load_audit_logs()
    user_logs = [log for log in logs if log["username"] == username]

    # Сортируем по времени (новые сначала)
    user_logs.sort(key=lambda x: x["timestamp"], reverse=True)

    if limit:
        return user_logs[:limit]
    return user_logs


def get_recent_actions(limit=50):
    """
    Получает последние действия системы.

    :param limit: Количество записей
    :return: Список последних действий
    """
    logs = load_audit_logs()
    # Сортируем по времени (новые сначала)
    logs.sort(key=lambda x: x["timestamp"], reverse=True)
    return logs[:limit]


def get_actions_by_type(action_type, limit=None):
    """
    Получает действия определенного типа.

    :param action_type: Тип действия (add, edit, delete, sync)
    :param limit: Ограничение количества записей
    :return: Список действий указанного типа
    """
    logs = load_audit_logs()
    filtered_logs = [log for log in logs if log["action_type"] == action_type]

    # Сортируем по времени (новые сначала)
    filtered_logs.sort(key=lambda x: x["timestamp"], reverse=True)

    if limit:
        return filtered_logs[:limit]
    return filtered_logs


def format_audit_log(log_entry, include_details=True):
    """
    Форматирует запись аудита для отображения.

    :param log_entry: Запись аудита
    :param include_details: Включать ли детали
    :return: Отформатированная строка
    """
    timestamp = format_timestamp(log_entry["timestamp"])
    username = log_entry["username"]
    action = log_entry["action_type"]
    target = log_entry["target"]

    # Преобразуем тип действия в читаемый вид
    action_names = {
        "add": "Добавление",
        "edit": "Редактирование",
        "delete": "Удаление",
        "sync": "Синхронизация",
        "login": "Вход в систему",
        "logout": "Выход из системы"
    }
    action_display = action_names.get(action, action.capitalize())

    # Формируем основное сообщение
    if action == "add":
        message = f"{action_display} записи: {target}"
    elif action == "edit":
        message = f"{action_display} записи: {target}"
    elif action == "delete":
        message = f"{action_display} записи: {target}"
    elif action == "sync":
        message = f"{action_display} данных с внешнего источника"
    else:
        message = f"{action_display}: {target}"

    # Добавляем детали, если нужно
    if include_details and log_entry.get("details"):
        message += f" | {log_entry['details']}"

    # Добавляем информацию о старом и новом значении для редактирования
    if action == "edit" and "old_value" in log_entry and "new_value" in log_entry:
        message += f"\nСтарое значение: {log_entry['old_value']}\nНовое значение: {log_entry['new_value']}"

    return f"[{timestamp}] {username}: {message}"


def format_timestamp(timestamp_str):
    """
    Форматирует временную метку в удобочитаемый вид.

    :param timestamp_str: Временная метка в формате ISO
    :return: Отформатированная строка
    """
    try:
        dt = datetime.fromisoformat(timestamp_str)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return timestamp_str


def clear_audit_logs():
    """
    Очищает все логи аудита.

    :return: True, если успешно
    """
    with open(AUDIT_LOG_FILE, "w", encoding="utf-8") as f:
        json.dump([], f, ensure_ascii=False, indent=4)
    return True


def export_audit_logs(filename):
    """
    Экспортирует логи аудита в файл.

    :param filename: Имя файла для экспорта
    :return: True, если успешно
    """
    logs = load_audit_logs()
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(logs, f, ensure_ascii=False, indent=4)
    return True


def import_audit_logs(filename):
    """
    Импортирует логи аудита из файла.

    :param filename: Имя файла для импорта
    :return: True, если успешно
    """
    if not os.path.exists(filename):
        return False

    try:
        with open(filename, "r", encoding="utf-8") as f:
            logs = json.load(f)

        # Проверяем корректность структуры
        if not isinstance(logs, list) or not all(isinstance(log, dict) for log in logs):
            return False

        # Сохраняем импортированные логи
        with open(AUDIT_LOG_FILE, "w", encoding="utf-8") as f:
            json.dump(logs, f, ensure_ascii=False, indent=4)

        return True
    except:
        return False


def get_changes_for_entry(entry_title):
    """
    Получает все изменения для конкретной записи.

    :param entry_title: Название записи
    :return: Список изменений
    """
    logs = load_audit_logs()
    entry_logs = [log for log in logs if log["target"] == entry_title]

    # Сортируем по времени (новые сначала)
    entry_logs.sort(key=lambda x: x["timestamp"], reverse=True)

    return entry_logs


def generate_audit_report():
    """
    Генерирует отчет по аудиту.

    :return: Словарь с данными отчета
    """
    logs = load_audit_logs()

    # Подсчитываем общее количество действий
    total_actions = len(logs)

    # Подсчитываем действия по типам
    actions_by_type = {}
    for log in logs:
        action_type = log["action_type"]
        actions_by_type[action_type] = actions_by_type.get(action_type, 0) + 1

    # Подсчитываем действия по пользователям
    actions_by_user = {}
    for log in logs:
        username = log["username"]
        actions_by_user[username] = actions_by_user.get(username, 0) + 1

    # Находим самую активную запись
    entries_by_count = {}
    for log in logs:
        if log["action_type"] in ["add", "edit", "delete"]:
            target = log["target"]
            entries_by_count[target] = entries_by_count.get(target, 0) + 1

    most_active_entry = max(entries_by_count, key=entries_by_count.get) if entries_by_count else None

    return {
        "total_actions": total_actions,
        "actions_by_type": actions_by_type,
        "actions_by_user": actions_by_user,
        "most_active_entry": most_active_entry,
        "recent_actions": logs[-10:] if len(logs) > 10 else logs
    }