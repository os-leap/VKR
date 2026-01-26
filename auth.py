from flask import Blueprint, render_template, request, redirect, url_for, session
import json
import os
import bcrypt

auth = Blueprint("auth", __name__)  # Уникальное имя

USERS_FILE = "users.json"

@auth.route("/register", methods=["GET", "POST"])
def register():
    error = None
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirm = request.form.get("confirm")

        if not username or not password or not confirm:
            error = "Все поля обязательны"
        elif password != confirm:
            error = "Пароли не совпадают"
        elif any(u["username"] == username for u in load_users()):
            error = "Логин уже занят"

        if error:
            return render_template("register.html", error=error)

        # Хэшируем пароль и сохраняем нового пользователя
        new_user = {
            "username": username,
            "password_hash": hash_password(password),
            "role": "user"  # По умолчанию роль "user"
        }

        users = load_users()
        users.append(new_user)
        with open(USERS_FILE, "w") as f:
            json.dump(users, f, indent=4, ensure_ascii=False)

        return redirect(url_for("auth.login"))

    return render_template("register.html", error=error)
def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    return []

def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password, hash):
    return bcrypt.checkpw(password.encode(), hash.encode())

@auth.route("/login", methods=["GET", "POST"])
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

@auth.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("index"))
