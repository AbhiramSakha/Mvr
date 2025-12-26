from flask import Flask, render_template, request, jsonify, redirect, url_for
from send_email import send_otp_email
import random
import time

app = Flask(__name__)

# In-memory DB (replace with real DB)
users = {}  # {email: {username, password, otp, otp_expiry}}

# ===== SIGNUP =====
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "GET":
        return render_template("signup.html")

    data = request.get_json()
    if not data:
        return jsonify({"success": False, "message": "No data received"}), 400

    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    if not username or not email or not password:
        return jsonify({"success": False, "message": "All fields are required"}), 400

    if email in users:
        return jsonify({"success": False, "message": "Email already registered"}), 400

    otp = str(random.randint(100000, 999999))
    otp_expiry = time.time() + 300  # OTP valid for 5 minutes
    users[email] = {"username": username, "password": password, "otp": otp, "otp_expiry": otp_expiry}

    try:
        send_otp_email(email, otp)
    except:
        return jsonify({"success": False, "message": "Failed to send OTP email"}), 500

    return jsonify({"success": True, "message": "OTP sent to your email. Check inbox/spam."})


# ===== VERIFY OTP =====
@app.route("/verify_otp", methods=["POST"])
def verify_otp():
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "message": "No data received"}), 400

    email = data.get("email")
    otp = data.get("otp")

    user = users.get(email)
    if not user:
        return jsonify({"success": False, "message": "User not found"}), 404

    if user.get("otp") != otp:
        return jsonify({"success": False, "message": "Invalid OTP"}), 400

    if time.time() > user.get("otp_expiry", 0):
        return jsonify({"success": False, "message": "OTP expired"}), 400

    # OTP verified, remove it
    user.pop("otp", None)
    user.pop("otp_expiry", None)

    return jsonify({"success": True, "message": "OTP verified. Account created successfully!"})


# ===== LOGIN =====
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    data = request.get_json()
    if not data:
        return jsonify({"success": False, "message": "No data received"}), 400

    email = data.get("email")
    password = data.get("password")

    user = users.get(email)
    if not user or user.get("password") != password:
        return jsonify({"success": False, "message": "Invalid email or password"}), 401

    # Generate OTP for login
    otp = str(random.randint(100000, 999999))
    user["otp"] = otp
    user["otp_expiry"] = time.time() + 300

    try:
        send_otp_email(email, otp)
    except:
        return jsonify({"success": False, "message": "Failed to send OTP"}), 500

    return jsonify({"success": True, "message": "OTP sent to your email."})


# ===== RESEND OTP =====
@app.route("/resend_otp", methods=["POST"])
def resend_otp():
    data = request.get_json()
    email = data.get("email")
    user = users.get(email)
    if not user:
        return jsonify({"success": False, "message": "User not found"}), 404

    otp = str(random.randint(100000, 999999))
    user["otp"] = otp
    user["otp_expiry"] = time.time() + 300

    try:
        send_otp_email(email, otp)
    except:
        return jsonify({"success": False, "message": "Failed to resend OTP"}), 500

    return jsonify({"success": True, "message": "OTP resent successfully."})


if __name__ == "__main__":
    app.run(debug=True)
