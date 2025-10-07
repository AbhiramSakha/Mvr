from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Mail, Message
from pymongo import MongoClient
import sqlite3
import random
import threading
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = "supersecretkey123"  # Direct secret key

# ======== MAIL CONFIG (Directly set) ========
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = "abhiramsakhaa@gmail.com"  # Your Gmail
app.config['MAIL_PASSWORD'] = "gors vdqm lpwe dlbp"      # Your Gmail App Password
app.config['MAIL_DEFAULT_SENDER'] = ("Movie App Team", app.config['MAIL_USERNAME'])
mail = Mail(app)

# ======== MONGODB CONFIG (for OTPs) ========
MONGO_URI = "your_mongodb_connection_string_here"  # Keep your MongoDB URI here
mongo_client = MongoClient(MONGO_URI)
db = mongo_client["movie_app"]
otps_collection = db["otps"]

# ======== INIT USERS DB (SQLite) ========
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
    def send():
        try:
            msg = Message(
                subject="Your OTP Code",
                recipients=[email],
                body=f"Your OTP code is: {otp}\nThis code expires in 10 minutes."
            )
            mail.send(msg)
            print(f"✅ OTP sent to {email}")
        except Exception as e:
            print(f"❌ Failed to send OTP: {e}")
            print(f"💡 Debug OTP for testing: {otp}")  # fallback
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
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        with sqlite3.connect("users.db", timeout=10) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
            user = cursor.fetchone()

        if not user or not check_password_hash(user[3], password):
            return render_template("login.html", error="Invalid email or password.")

        # Generate OTP
        otp = generate_otp()
        expiry = datetime.utcnow() + timedelta(minutes=10)

        otps_collection.delete_many({"email": email})
        otps_collection.insert_one({
            "email": email,
            "otp": generate_password_hash(otp),
            "expiry": expiry
        })

        send_otp_email_async(email, otp)
        print(f"📧 Sending OTP to {email}")

        # Store pending login session
        session['pending_email'] = email
        session['pending_user_id'] = user[0]
        session['pending_username'] = user[1]

        return redirect(url_for("verify_otp"))

    return render_template("login.html")

@app.route("/verify_otp", methods=["GET", "POST"])
def verify_otp():
    if request.method == "POST":
        input_otp = request.form.get("otp", "").strip()
        email = session.get("pending_email")
        if not email:
            return redirect(url_for("login"))

        otp_record = otps_collection.find_one({"email": email})
        now = datetime.utcnow()

        if not otp_record:
            session.clear()
            return render_template("login.html", error="No OTP found. Please login again.")
        if otp_record["expiry"] < now:
            otps_collection.delete_many({"email": email})
            session.clear()
            return render_template("login.html", error="OTP expired. Please login again.")

        if check_password_hash(otp_record["otp"], input_otp):
            # OTP correct: login successful
            session['user_id'] = session.pop('pending_user_id')
            session['username'] = session.pop('pending_username')
            session.pop('pending_email', None)
            otps_collection.delete_many({"email": email})
            return redirect(url_for("home"))
        else:
            return render_template("verify_otp.html", error="Invalid OTP. Please try again.")

    # GET request: show verify_otp page
    return render_template("verify_otp.html", message="✅ OTP sent! Check inbox or spam folder.")

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
            recipients=[app.config['MAIL_USERNAME']],
            body="✅ This is a test email from your Flask app."
        )
        mail.send(msg)
        return "✅ Test email sent! Check inbox/spam."
    except Exception as e:
        return f"❌ Failed to send email: {e}"

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
