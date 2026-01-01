from flask import Flask, render_template, request, jsonify, redirect, url_for
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

# In-memory user store (DEMO ONLY)
# users[email] = { username, password }
users = {}

# ================= HOME =================
@app.route("/")
def home():
    return redirect(url_for("signup"))

# ================= SIGNUP =================
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "GET":
        return render_template("signup.html")

    data = request.get_json()
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    if not username or not email or not password:
        return jsonify(success=False, message="All fields required")

    if email in users:
        return jsonify(success=False, message="Email already registered")

    users[email] = {
        "username": username,
        "password": password
    }

    return jsonify(success=True, message="Signup successful! Redirecting to login...")

# ================= LOGIN =================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    user = users.get(email)

    if not user or user["password"] != password:
        return jsonify(success=False, message="Invalid email or password")

    return jsonify(success=True)

# ================= DASHBOARD =================
@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

if __name__ == "__main__":
    app.run(debug=True)
