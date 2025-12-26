import os
import random
import sqlite3
import smtplib
from email.message import EmailMessage
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from pymongo import MongoClient
from dotenv import load_dotenv

# ================= LOAD ENV =================
load_dotenv()

EMAIL_USER = os.getenv("MAIL_USERNAME")
EMAIL_PASS = os.getenv("MAIL_PASSWORD")

# ================= APP =================
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")

# ================= DB =================
mongo = MongoClient(os.getenv("MONGO_URI"))
db = mongo["movie_app"]
otp_col = db["otps"]

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

# ================= OTP EMAIL =================
def send_otp_email(email, otp):
    if not EMAIL_USER or not EMAIL_PASS:
        raise RuntimeError("Email credentials missing")

    msg = EmailMessage()
    msg["Subject"] = "Your OTP Code"
    msg["From"] = EMAIL_USER
    msg["To"] = email
    msg.set_content(f"""
Your One-Time Password is:

{otp}

Valid for 5 minutes.
Do not share it.
""")

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_USER, EMAIL_PASS)
        server.send_message(msg)

# ================= HELPERS =================
def generate_otp():
    return str(random.randint(100000, 999999))

# ================= ROUTES =================

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        data = request.get_json()
        email = data.get("email")
        password = data.get("password")

        with sqlite3.connect("users.db") as conn:
            user = conn.execute(
                "SELECT id, username, password FROM users WHERE email=?",
                (email,)
            ).fetchone()

        if not user or not check_password_hash(user[2], password):
            return jsonify(success=False, message="Invalid credentials"), 401

        otp = generate_otp()
        otp_col.delete_many({"email": email})
        otp_col.insert_one({
            "email": email,
            "otp": generate_password_hash(otp),
            "expiry": datetime.utcnow() + timedelta(minutes=5)
        })

        send_otp_email(email, otp)

        session["pending_email"] = email
        session["pending_user_id"] = user[0]
        session["pending_username"] = user[1]

        return jsonify(success=True, message="OTP sent")

    return render_template("login.html")

@app.route("/verify_otp", methods=["POST"])
def verify_otp():
    email = request.form.get("email")
    otp = request.form.get("otp")

    record = otp_col.find_one({"email": email})
    if not record:
        return render_template("verify_otp.html", error="OTP not found")

    if record["expiry"] < datetime.utcnow():
        return render_template("verify_otp.html", error="OTP expired")

    if not check_password_hash(record["otp"], otp):
        return render_template("verify_otp.html", error="Invalid OTP")

    session["user_id"] = session.pop("pending_user_id")
    session["username"] = session.pop("pending_username")
    session.pop("pending_email")

    otp_col.delete_many({"email": email})
    return redirect("/dashboard")

@app.route("/resend_otp", methods=["POST"])
def resend_otp():
    email = session.get("pending_email")
    if not email:
        return jsonify(success=False), 400

    otp = generate_otp()
    otp_col.delete_many({"email": email})
    otp_col.insert_one({
        "email": email,
        "otp": generate_password_hash(otp),
        "expiry": datetime.utcnow() + timedelta(minutes=5)
    })

    send_otp_email(email, otp)
    return jsonify(success=True)

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/login")
    return f"Welcome {session['username']} 🎉"

# ================= RUN =================
if __name__ == "__main__":
    app.run(debug=False)
