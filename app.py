from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import sqlite3
import requests
import os

# ================= LOAD ENV =================
load_dotenv()

app = Flask(__name__)

# ================= SECRET KEY (FIXED NAME) =================
app.secret_key = os.getenv("FLASK_SECRET_KEY")

if not app.secret_key:
    raise RuntimeError("FLASK_SECRET_KEY is not set in environment variables")

# ================= TMDb CONFIG =================
TMDB_API_KEY = os.getenv("TMDB_API_KEY")
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

# ================= LOGIN (JSON SAFE) =================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":

        if not request.is_json:
            return jsonify(success=False, message="Invalid request type"), 400

        try:
            data = request.get_json(force=True)
            email = data.get("email", "").strip()
            password = data.get("password", "")

            if not email or not password:
                return jsonify(success=False, message="Email and password required"), 400

            conn = sqlite3.connect("users.db")
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
            user = cursor.fetchone()
            conn.close()

            if not user:
                return jsonify(success=False, message="User not found"), 401

            if not check_password_hash(user[3], password):
                return jsonify(success=False, message="Invalid password"), 401

            # ✅ SAFE SESSION SET
            session.clear()
            session["user_id"] = int(user[0])
            session["username"] = user[1]

            return jsonify(success=True)

        except Exception as e:
            print("🔥 LOGIN ERROR:", e)
            return jsonify(success=False, message="Server error"), 500

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
        print("TMDB TRENDING ERROR:", e)
        return jsonify({"error": "Failed to fetch trending movies"}), 500


@app.route("/api/search")
def api_search():
    query = request.args.get("query")
    language = request.args.get("language", "en-US")

    if not query:
        return jsonify({"error": "Missing query"}), 400

    try:
        resp = requests.get(
            "https://api.themoviedb.org/3/search/movie",
            params={
                "query": query,
                "language": language,
                "api_key": TMDB_API_KEY
            },
            headers=TMDB_HEADERS
        )
        resp.raise_for_status()
        return jsonify(resp.json())
    except Exception as e:
        print("TMDB SEARCH ERROR:", e)
        return jsonify({"error": "Failed to search movies"}), 500

# ================= RUN =================
if __name__ == "__main__":
    app.run(debug=True)
