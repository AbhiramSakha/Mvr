from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Mail, Message
from pymongo import MongoClient
import sqlite3
import requests
import os
import random
import threading
from datetime import datetime, timedelta
from dotenv import load_dotenv

# ======== LOAD .ENV CONFIG ========
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "your_secret_key")

# ======== MAIL CONFIG ========
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USERNAME'] = os.getenv("MAIL_USERNAME", "abhiramsakhaa@gmail.com")
app.config['MAIL_PASSWORD'] = os.getenv("MAIL_PASSWORD", "gors vdqm lpwe dlbp")  # Gmail App Password
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
mail = Mail(app)

# ======== MONGODB (for OTPs) ========
MONGO_URI = os.getenv("MONGO_URI")
mongo_client = MongoClient(MONGO_URI)
db = mongo_client["movie_app"]
otps_collection = db["otps"]

# ======== TMDb CONFIG ========
TMDB_API_KEY = os.getenv("TMDB_API_KEY", "714874b0f9b013fb2f6a3f2162fb3730")
TMDB_READ_ACCESS_TOKEN = os.getenv("TMDB_READ_ACCESS_TOKEN")

# ======== INIT USERS DB ========
def init_db():
    with sqlite3.connect("users.db", timeout=10) as conn:
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

init_db()

# ======== HELPER FUNCTIONS ========
def generate_otp():
    return str(random.randint(100000, 999999))

def send_otp_email_async(email, otp):
    """Send OTP email in a background thread with improved logging."""
    def send():
        try:
            msg = Message(
                subject="Your OTP Code",
                sender=app.config['MAIL_USERNAME'],
                recipients=[email],
                body=(
                    f"Your OTP code is: {otp}\n\n"
                    f"This code will expire in 10 minutes.\n"
                    f"If you didn't request this, please ignore."
                )
            )
            mail.send(msg)
            print(f"✅ OTP email successfully sent to {email}")
        except Exception as e:
            print(f"❌ Failed to send OTP to {email}: {e}")
            print(f"💡 Debug OTP (for testing): {otp}")

    threading.Thread(target=send).start()

# ======== ROUTES ========

@app.route("/")
def home():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return render_template("dashboard.html", username=session.get("username"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.is_json:
            try:
                data = request.get_json(force=True)
                email = data.get("email", "").strip()
                password = data.get("password", "")

                with sqlite3.connect("users.db", timeout=10) as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
                    user = cursor.fetchone()

                if not user or not check_password_hash(user[3], password):
                    return jsonify(success=False, message="Invalid email or password."), 401

                otp = generate_otp()
                expiry = datetime.utcnow() + timedelta(minutes=10)

                otps_collection.delete_many({"email": email})
                otps_collection.insert_one({
                    "email": email,
                    "otp": generate_password_hash(otp),
                    "expiry": expiry
                })

                try:
                    send_otp_email_async(email, otp)
                    print(f"📧 Sending OTP to {email} ...")
                    message = "✅ OTP sent! Please check your inbox or spam folder."
                except Exception as e:
                    print(f"❌ OTP sending failed: {e}")
                    message = "⚠️ Failed to send OTP. Please try again later."

                session['pending_email'] = email
                session['pending_user_id'] = user[0]
                session['pending_username'] = user[1]

                return jsonify(success=True, message=message)

            except Exception as e:
                return jsonify(success=False, message=f"Server error: {str(e)}"), 500

        return jsonify(success=False, message="Invalid request format."), 400

    return render_template("login.html")

@app.route("/verify_otp", methods=["POST"])
def verify_otp():
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")
    input_otp = request.form.get("otp", "").strip()

    if 'pending_email' not in session or session.get('pending_email') != email:
        return render_template("login.html", error="Session expired. Please login again.")

    with sqlite3.connect("users.db", timeout=10) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()

    if not user or not check_password_hash(user[3], password):
        return render_template("login.html", error="Invalid credentials.")

    otp_record = otps_collection.find_one({"email": email})
    now = datetime.utcnow()

    if not otp_record:
        return render_template("login.html", error="No OTP found. Please login again.")
    if otp_record["expiry"] < now:
        otps_collection.delete_many({"email": email})
        session.clear()
        return render_template("login.html", error="OTP expired. Please login again.")

    if check_password_hash(otp_record["otp"], input_otp):
        session['user_id'] = session.pop('pending_user_id')
        session['username'] = session.pop('pending_username')
        session.pop('pending_email', None)
        otps_collection.delete_many({"email": email})
        return redirect(url_for("home"))

    return render_template("login.html", error="Invalid OTP. Please try again.")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        hashed_password = generate_password_hash(password)

        try:
            with sqlite3.connect("users.db", timeout=10) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
                    (username, email, hashed_password)
                )
                conn.commit()
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            error = "Email already registered."
        except sqlite3.OperationalError as e:
            error = f"Database error: {e}"

    return render_template("signup.html", error=error)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/testmail")
def testmail():
    try:
        msg = Message(
            "Test Email From Flask",
            sender=app.config['MAIL_USERNAME'],
            recipients=[app.config['MAIL_USERNAME']],
            body="✅ This is a test email sent from your Flask app."
        )
        mail.send(msg)
        return "✅ Test email sent successfully! Please check your inbox/spam."
    except Exception as e:
        return f"❌ Failed to send email: {e}"

if __name__ == "__main__":
    app.debug = True
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
