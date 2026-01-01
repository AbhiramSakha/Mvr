from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import sqlite3
import requests
import os

# ================= LOAD ENV =================
load_dotenv()

app = Flask(__name__)

# ================= CONFIG =================
app.secret_key = os.getenv("SECRET_KEY")

TMDB_READ_ACCESS_TOKEN = os.getenv("TMDB_READ_ACCESS_TOKEN")

TMDB_HEADERS = {
    "Authorization": f"Bearer {TMDB_READ_ACCESS_TOKEN}",
    "Content-Type": "application/json"
}

# ================= DATABASE INIT =================
def init_db():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

init_db()

# ================= HOME / DASHBOARD =================
@app.route("/")
def home():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return render_template("dashboard.html", username=session.get("username"))

# ================= SIGNUP =================
@app.route("/signup", methods=["GET", "POST"])
def signup():
    error = None

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()

        if not username or not email or not password:
            return render_template("signup.html", error="All fields are required")

        hashed_password = generate_password_hash(password)

        try:
            conn = sqlite3.connect("users.db")
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
                (username, email, hashed_password)
            )
            conn.commit()
            conn.close()

            # ✅ Redirect to login after signup
            return redirect(url_for("login"))

        except sqlite3.IntegrityError:
            error = "Email already registered."

    return render_template("signup.html", error=error)

# ================= LOGIN (FIXED PERFECTLY) =================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":

        # ✅ Accept JSON (fetch) OR form submit
        if request.is_json:
            data = request.get_json()
            email = data.get("email", "").strip()
            password = data.get("password", "")
        else:
            email = request.form.get("email", "").strip()
            password = request.form.get("password", "")

        if not email or not password:
            return jsonify(success=False, message="Email and password required")

        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user[3], password):
            session["user_id"] = user[0]
            session["username"] = user[1]
            return jsonify(success=True)

        return jsonify(success=False, message="Invalid email or password")

    return render_template("login.html")

# ================= LOGOUT =================
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ================= TMDb API PROXY =================
@app.route("/api/trending")
def api_trending():
    try:
        resp = requests.get(
            "https://api.themoviedb.org/3/trending/movie/week",
            params={"language": "en-US"},
            headers=TMDB_HEADERS
        )
        resp.raise_for_status()
        return jsonify(resp.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/search")
def api_search():
    query = request.args.get("query")
    language = request.args.get("language", "en-US")

    if not query:
        return jsonify({"error": "Missing query"}), 400

    try:
        resp = requests.get(
            "https://api.themoviedb.org/3/search/movie",
            params={"query": query, "language": language},
            headers=TMDB_HEADERS
        )
        resp.raise_for_status()
        return jsonify(resp.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ================= RUN =================
if __name__ == "__main__":
    app.run(debug=True)
