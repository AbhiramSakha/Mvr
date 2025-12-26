from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Mail, Message
from pymongo import MongoClient
import sqlite3
import os
import random
import threading
from datetime import datetime, timedelta

# ================= APP CONFIG =================
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "super_secret_key")

# ================= MAIL CONFIG =================
app.config.update(
    MAIL_SERVER="smtp.gmail.com",
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USERNAME="sakhabhiram1234@gmail.com",
    MAIL_PASSWORD="aqelcqlruyhiutip"
)

mail = Mail(app)

# ================= DATABASES =================
# SQLite users DB
def init_db():
    with sqlite3.connect("users.db") as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        """)
init_db()

# MongoDB for OTPs
mongo = MongoClient(os.getenv("MONGO_URI"))
db = mongo["movie_app"]
otp_col = db["otps"]

# ================= HELPERS =================
def generate_otp():
    return str(random.randint(100000, 999999))

def send_otp_email(email, otp):
    def send():
        try:
            msg = Message(
                subject="Your Login OTP",
                sender=app.config["MAIL_USERNAME"],
                recipients=[email],
                body=f"Your OTP is: {otp}\n\nValid for 10 minutes."
            )
            mail.send(msg)
            print(f"✅ OTP sent to {email}")
        except Exception as e:
            print(f"❌ OTP email failed: {e}")
            print(f"DEBUG OTP: {otp}")  # console-only fallback

    threading.Thread(target=send).start()

# ================= ROUTES =================

@app.route("/")
def home():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return f"Welcome {session['username']} 🎉"

# ---------- LOGIN (SEND OTP) ----------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if not request.is_json:
            return jsonify(success=False, message="Invalid request"), 400

        data = request.get_json()
        email = data.get("email", "").strip()
        password = data.get("password", "")

        # Validate user
        with sqlite3.connect("users.db") as conn:
            user = conn.execute(
                "SELECT id, username, password FROM users WHERE email=?",
                (email,)
            ).fetchone()

        if not user or not check_password_hash(user[2], password):
            return jsonify(success=False, message="Invalid email or password"), 401

        # Generate OTP
        otp = generate_otp()
        expiry = datetime.utcnow() + timedelta(minutes=10)

        otp_col.delete_many({"email": email})
        otp_col.insert_one({
            "email": email,
            "otp": generate_password_hash(otp),
            "expiry": expiry
        })

        send_otp_email(email, otp)

        # Temp session
        session["pending_email"] = email
        session["pending_user_id"] = user[0]
        session["pending_username"] = user[1]

        return jsonify(success=True, message="OTP sent successfully")

    return render_template("login.html")

# ---------- VERIFY OTP ----------
@app.route("/verify_otp", methods=["POST"])
def verify_otp():
    email = request.form.get("email", "").strip()
    otp_input = request.form.get("otp", "").strip()

    if session.get("pending_email") != email:
        return render_template("verify_otp.html", error="Session expired. Login again.")

    record = otp_col.find_one({"email": email})

    if not record:
        return render_template("verify_otp.html", error="OTP not found. Login again.")

    if record["expiry"] < datetime.utcnow():
        otp_col.delete_many({"email": email})
        session.clear()
        return render_template("verify_otp.html", error="OTP expired.")

    if not check_password_hash(record["otp"], otp_input):
        return render_template("verify_otp.html", error="Invalid OTP.")

    # OTP valid → Login user
    session["user_id"] = session.pop("pending_user_id")
    session["username"] = session.pop("pending_username")
    session.pop("pending_email", None)

    otp_col.delete_many({"email": email})
    return redirect(url_for("home"))

# ---------- SIGNUP ----------
@app.route("/signup", methods=["GET", "POST"])
def signup():
    error = None
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = generate_password_hash(request.form["password"])

        try:
            with sqlite3.connect("users.db") as conn:
                conn.execute(
                    "INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
                    (username, email, password)
                )
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            error = "Email already exists"

    return render_template("signup.html", error=error)

# ---------- LOGOUT ----------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ================= RUN =================
if __name__ == "__main__":
    app.run(debug=False)
