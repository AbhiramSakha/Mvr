from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from pymongo import MongoClient
from datetime import datetime, timedelta
import sqlite3
import os
import random
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv

# =====================
# LOAD ENV
# =====================
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "fallback_secret_key")

# =====================
# EMAIL CONFIG (GMAIL SMTP)
# =====================
EMAIL_USER = os.getenv("MAIL_USERNAME")
EMAIL_PASS = os.getenv("MAIL_PASSWORD")

# =====================
# MONGODB (OTP STORAGE)
# =====================
MONGO_URI = os.getenv("MONGO_URI")
mongo = MongoClient(MONGO_URI)
db = mongo["movie_app"]
otp_col = db["otps"]

# =====================
# SQLITE USERS DB
# =====================
def init_db():
    with sqlite3.connect("users.db") as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                email TEXT UNIQUE,
                password TEXT
            )
        """)
init_db()

# =====================
# HELPERS
# =====================
def generate_otp():
    return str(random.randint(100000, 999999))

def send_otp_email(email, otp):
    if not EMAIL_USER or not EMAIL_PASS:
        raise ValueError("Email credentials not set")

    msg = EmailMessage()
    msg["Subject"] = "Your OTP Code"
    msg["From"] = EMAIL_USER
    msg["To"] = email
    msg.set_content(f"""
Hello,

Your OTP is: {otp}

This OTP is valid for 10 minutes.
Do not share it with anyone.
""")

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_USER, EMAIL_PASS)
        server.send_message(msg)

# =====================
# ROUTES
# =====================

@app.route("/")
def home():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return f"Welcome {session['username']} 🎉"

# ---------- SIGNUP ----------
@app.route("/signup", methods=["GET", "POST"])
def signup():
    error = None
    if request.method == "POST":
        try:
            username = request.form["username"]
            email = request.form["email"]
            password = generate_password_hash(request.form["password"])

            with sqlite3.connect("users.db") as conn:
                conn.execute(
                    "INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
                    (username, email, password)
                )
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            error = "Email already exists"

    return render_template("signup.html", error=error)

# ---------- LOGIN + SEND OTP ----------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        data = request.get_json()
        email = data.get("email")
        password = data.get("password")

        with sqlite3.connect("users.db") as conn:
            cur = conn.cursor()
            cur.execute("SELECT id, username, password FROM users WHERE email=?", (email,))
            user = cur.fetchone()

        if not user or not check_password_hash(user[2], password):
            return jsonify(success=False, message="Invalid email or password"), 401

        otp = generate_otp()
        expiry = datetime.utcnow() + timedelta(minutes=10)

        otp_col.delete_many({"email": email})
        otp_col.insert_one({
            "email": email,
            "otp": generate_password_hash(otp),
            "expiry": expiry
        })

        send_otp_email(email, otp)

        session["pending_email"] = email
        session["pending_user_id"] = user[0]
        session["pending_username"] = user[1]

        return jsonify(success=True, message="OTP sent successfully")

    return render_template("login.html")

# ---------- VERIFY OTP ----------
@app.route("/verify_otp", methods=["POST"])
def verify_otp():
    email = request.form.get("email")
    otp = request.form.get("otp")

    if session.get("pending_email") != email:
        return "Session expired. Login again."

    record = otp_col.find_one({"email": email})
    if not record or record["expiry"] < datetime.utcnow():
        return "OTP expired. Login again."

    if not check_password_hash(record["otp"], otp):
        return "Invalid OTP"

    session["user_id"] = session.pop("pending_user_id")
    session["username"] = session.pop("pending_username")
    session.pop("pending_email")

    otp_col.delete_many({"email": email})

    return redirect(url_for("home"))

# ---------- LOGOUT ----------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# =====================
# RUN
# =====================
if __name__ == "__main__":
    app.run(debug=True)
