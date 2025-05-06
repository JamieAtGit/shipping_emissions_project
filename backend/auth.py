import json
import os
from flask import Blueprint, request, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

auth = Blueprint("auth", __name__)
USERS_FILE = os.path.join(os.path.dirname(__file__), "users.json")

# === Utilities ===
def load_users():
    try:
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)

def login_required(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        if "user" not in session:
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return wrapped

# === Routes ===
@auth.route("/signup", methods=["POST"])
def signup():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "Username and password required"}), 400

    users = load_users()
    if any(u["username"] == username for u in users):
        return jsonify({"error": "User already exists"}), 400

    hashed_pw = generate_password_hash(password)
    new_user = {
        "username": username,
        "password": hashed_pw,
        "role": "admin" if username == "admin" else "user"
    }

    users.append(new_user)
    save_users(users)
    return jsonify({"message": "✅ User registered"}), 200

@auth.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    users = load_users()
    user = next((u for u in users if u["username"] == username), None)
    if not user or not check_password_hash(user["password"], password):
        return jsonify({"error": "Invalid credentials"}), 401

    session["user"] = {"username": user["username"], "role": user["role"]}
    return jsonify({"message": "✅ Logged in", "user": session["user"]}), 200

@auth.route("/logout", methods=["POST"])
def logout():
    session.pop("user", None)
    return jsonify({"message": "Logged out"})

@auth.route("/me", methods=["GET"])
@login_required
def me():
    return jsonify(session.get("user"))