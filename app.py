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

# ======== LOAD ENV ONLY FOR MONGO URI ========
load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")

app = Flask(__name__)

# ======== SECRET KEY (Hardcoded) ========
app.secret_key = "super_secret_key_123"

# ======== MAIL CONFIG (Directly set here) ========
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = "abhiramsakhaa@gmail.com"  # Your Gmail
app.config['MAIL_PASSWORD'] = "gors vdqm lpwe dlbp"      # Your Gmail App Password
app.config['MAIL_DEFAULT_SENDER'] = ("Movie App Team", app.config['MAIL_USERNAME'])
mail = Mail(app)


# ======== MONGODB (Only OTPs) ========
mongo_client = MongoClient(MONGO_URI)
db = mongo_client["movie_app"]
otps_collection = db["otps"]

# ======== TMDb CONFIG ========
TMDB_API_KEY = "714874b0f9b013fb2f6a3f2162fb3730"
TMDB_READ_ACCESS_TOKEN = (
    "eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiI3MTQ4NzRiMGY5YjAxM2ZiMmY2YTNmMjE2MmZiMzczMCIsIm5iZiI6MTc0MTY3NzAzMC43MDcsInN1YiI6IjY3Y2ZlMWU2NDJjMGNjYzNjYTFkZDZhNyIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.ZQC4cE7jPNUr6BWvVC5Wn0G06EHGVhiut9eRfflCAio"
)

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
    """Send OTP email asynchronously with strong logging."""
    def send():
        try:
            msg = Message(
                subject="🎬 Your OTP Verification Code",
                recipients=[email],
                body=f"""
Hello {email},

Your One-Time Password (OTP) is: {otp}

This OTP will expire in 10 minutes.
If you did not request this, you can safely ignore this message.

Best regards,  
Movie App Team 🎥
"""
            )
            mail.send(msg)
            print(f"✅ OTP successfully sent to {email}")
        except Exception as e:
            print(f"❌ Email sending failed for {email}: {e}")
            print(f"💡 Fallback OTP (debug): {otp}")

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

                send_otp_email_async(email, otp)
                print(f"📧 OTP being sent to {email}...")

                session['pending_email'] = email
                session['pending_user_id'] = user[0]
                session['pending_username'] = user[1]

                return jsonify(success=True, message="✅ OTP sent successfully! Check your inbox or spam folder.")
            except Exception as e:
                print(f"⚠️ Server Error: {e}")
                return jsonify(success=False, message=f"Server error: {str(e)}"), 500

        return jsonify(success=False, message="Invalid request format."), 400

    return render_template("login.html")

@app.route("/verify_otp", methods=["POST"])
def verify_otp():
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")
    input_otp = request.form.get("otp", "").strip()

    if 'pending_email' not in session or session.get('pending_email') != email:
        return render_template("login.html", error="Session expired. Please log in again.")

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
    """Quick test to confirm Gmail SMTP works."""
    try:
        msg = Message(
            "✅ Test Email from Movie App",
            recipients=[app.config['MAIL_USERNAME']],
            body="This is a test email sent successfully from your Flask Movie App!"
        )
        mail.send(msg)
        return "✅ Test email sent! Check your inbox/spam folder."
    except Exception as e:
        return f"❌ Failed to send test email: {e}"

# ======== RUN APP ========
if __name__ == "__main__":
    app.debug = True
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
