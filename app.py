from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Mail, Message
from pymongo import MongoClient
import os
import sqlite3
import random
import threading
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "fallback_secret_key")

# ===== MAIL CONFIG =====
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USERNAME'] = 'sakhabhiram1234@gmail.com'
app.config['MAIL_PASSWORD'] = 'aqelcqlruyhiutip'
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
mail = Mail(app)

# ===== MONGODB =====
MONGO_URI = os.getenv("MONGO_URI")
mongo_client = MongoClient(MONGO_URI)
db = mongo_client["movie_app"]
otps_collection = db["otps"]

# ===== INIT USERS DB =====
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

# ===== HELPER FUNCTIONS =====
def generate_otp():
    return str(random.randint(100000, 999999))

def send_otp_email_async(email, otp):
    def send():
        try:
            msg = Message(
                subject="Your OTP Code",
                sender=app.config['MAIL_USERNAME'],
                recipients=[email],
                body=f"Your OTP code is: {otp}\n\nIt expires in 10 minutes."
            )
            mail.send(msg)
            print(f"✅ OTP email sent to {email}")
        except Exception as e:
            print(f"❌ Failed to send OTP to {email}: {e}")
            print(f"💡 Debug OTP: {otp}")  # Show OTP in console if email fails
            session['otp_send_error'] = "Failed to send OTP email. Please try again later."

    threading.Thread(target=send).start()

# ===== ROUTES =====
@app.route("/")
def home():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return render_template("dashboard.html", username=session.get("username"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        try:
            if request.is_json:
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

                send_otp_email_async(email, otp)
                session['pending_email'] = email
                session['pending_user_id'] = user[0]
                session['pending_username'] = user[1]
                session['debug_otp'] = otp  # TEMP: for testing if email fails

                return jsonify(success=True, message="OTP sent! Check inbox/spam.")

            return jsonify(success=False, message="Invalid request format."), 400

        except Exception as e:
            return jsonify(success=False, message=f"Server error: {str(e)}"), 500

    return render_template("login.html")

@app.route("/verify_otp", methods=["GET", "POST"])
def verify_otp():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        input_otp = request.form.get("otp", "").strip()

        if 'pending_email' not in session or session.get('pending_email') != email:
            return render_template("verify_otp.html", error="Session expired. Login again.")

        otp_record = otps_collection.find_one({"email": email})
        now = datetime.utcnow()

        if not otp_record:
            return render_template("verify_otp.html", error="No OTP found. Login again.")
        if otp_record["expiry"] < now:
            otps_collection.delete_many({"email": email})
            session.clear()
            return render_template("verify_otp.html", error="OTP expired. Login again.")

        if check_password_hash(otp_record["otp"], input_otp):
            session['user_id'] = session.pop('pending_user_id')
            session['username'] = session.pop('pending_username')
            session.pop('pending_email', None)
            otps_collection.delete_many({"email": email})
            session.pop('debug_otp', None)
            return redirect(url_for("home"))

        return render_template("verify_otp.html", error="Invalid OTP. Try again.")

    return render_template("verify_otp.html", debug_otp=session.get('debug_otp'), otp_send_error=session.get('otp_send_error'))

@app.route("/resend_otp", methods=["POST"])
def resend_otp():
    if 'pending_email' not in session:
        return jsonify(success=False, message="Session expired. Please log in again."), 400

    email = session['pending_email']
    otp = generate_otp()
    expiry = datetime.utcnow() + timedelta(minutes=10)

    otps_collection.delete_many({"email": email})
    otps_collection.insert_one({
        "email": email,
        "otp": generate_password_hash(otp),
        "expiry": expiry
    })

    send_otp_email_async(email, otp)
    return jsonify(success=True, message="OTP resent. Check your inbox/spam.")

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

if __name__ == "__main__":
    app.debug = True
    app.run(host="0.0.0.0", port=5000)
