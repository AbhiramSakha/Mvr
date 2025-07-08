from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import requests
import os

app = Flask(__name__)
app.secret_key = "your_secret_key"

# TMDb API Configuration
TMDB_API_KEY = "314d3f0c5a3e7594114b148aa99cfb67"
TMDB_READ_ACCESS_TOKEN = "eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiIzMTRkM2YwYzVhM2U3NTk0MTE0YjE0OGFhOTljZmI2NyIsIm5iZiI6MTc0MTY3NzAzMC43MDcsInN1YiI6IjY3Y2ZlMWU2NDJjMGNjYzNjYTFkZDZhNyIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.M_1Oxd8GK14Iu9hIthAC6KfMuTJFgWY7dP7UiEduEDs"

HEADERS = {
    "Authorization": f"Bearer {TMDB_READ_ACCESS_TOKEN}",
    "Content-Type": "application/json"
}

# Database setup
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

# Home route
@app.route("/")
def home():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return render_template("dashboard.html")

# Login route
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user[3], password):
            session["user_id"] = user[0]
            session["username"] = user[1]
            return redirect(url_for("home"))
        else:
            return render_template("login.html", error="Invalid credentials")

    return render_template("login.html")

# Signup route
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        hashed_password = generate_password_hash(password)

        try:
            conn = sqlite3.connect("users.db")
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
                           (username, email, hashed_password))
            conn.commit()
            conn.close()
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            return render_template("signup.html", error="Email already registered")

    return render_template("signup.html")

# Logout route
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# Fetch movie recommendations from TMDb
@app.route("/recommend", methods=["GET"])
def recommend():
    movie_name = request.args.get("movie")
    if not movie_name:
        return jsonify({"error": "No movie name provided"}), 400

    url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={movie_name}"
    response = requests.get(url, headers=HEADERS)

    if response.status_code != 200:
        return jsonify({"error": "Failed to fetch data from TMDb"}), 500

    data = response.json()
    results = data.get("results", [])

    recommended_movies = []
    for movie in results[:5]:  
        recommended_movies.append({
            "title": movie.get("title"),
            "overview": movie.get("overview"),
            "poster": f"https://image.tmdb.org/t/p/w500{movie.get('poster_path')}" if movie.get("poster_path") else None
        })

    return jsonify({"recommended_movies": recommended_movies})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000)) 
    app.run(host='0.0.0.0', port=port)

