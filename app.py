from flask import Flask, request, jsonify, render_template_string, redirect, url_for
import random
import os
from dotenv import load_dotenv
from flask import Flask

load_dotenv()  # take environment variables from .env file

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

# rest of your app code...


# Temporary in-memory stores (for demo only!)
users = {}      # key: email, value: dict with username, password
otp_store = {}  # key: email, value: otp


# Signup page with embedded HTML template
signup_html = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Signup</title>
  <style>
    body {
      font-family: 'Poppins', sans-serif;
      background: #121212;
      color: white;
      display: flex;
      justify-content: center;
      align-items: center;
      height: 100vh;
      margin: 0;
    }
    .container {
      background: rgba(255, 255, 255, 0.1);
      padding: 30px;
      border-radius: 15px;
      width: 320px;
      box-shadow: 0 0 15px rgba(0,255,255,0.3);
    }
    input {
      width: 100%;
      padding: 12px;
      margin: 12px 0;
      border-radius: 8px;
      border: none;
      background: rgba(255, 255, 255, 0.15);
      color: white;
      font-size: 14px;
    }
    input::placeholder {
      color: #ccc;
    }
    button {
      width: 100%;
      padding: 12px;
      border: none;
      border-radius: 8px;
      background: linear-gradient(90deg, #00DBDE, #FC00FF);
      color: black;
      font-weight: bold;
      cursor: pointer;
      font-size: 16px;
    }
    button:disabled {
      opacity: 0.6;
      cursor: not-allowed;
    }
    #otp-section {
      display: none;
      margin-top: 10px;
    }
    .message {
      margin-top: 12px;
      min-height: 20px;
      font-weight: bold;
    }
    .message.error {
      color: #ff6961;
    }
    .message.success {
      color: #00ff99;
    }
    p {
      text-align: center;
      margin-top: 18px;
      font-size: 14px;
      color: #aaa;
    }
    a {
      color: #00DBDE;
      text-decoration: none;
      font-weight: bold;
    }
  </style>
</head>
<body>

<div class="container">
  <h2>Signup & Send OTP</h2>
  <form id="signupForm">
    <input type="text" id="username" placeholder="Username" required />
    <input type="email" id="email" placeholder="Email" required />
    <input type="password" id="password" placeholder="Password" required />

    <button type="button" id="signupBtn">Signup & Send OTP</button>

    <div id="otp-section">
      <input type="text" id="otp" placeholder="Enter 6-digit OTP" maxlength="6" required />
      <button type="button" id="verifyOtpBtn">Verify OTP</button>
    </div>

    <div id="message" class="message"></div>
  </form>

  <p>Already have an account? <a href="/login">Login</a></p>
</div>

<script>
  const signupBtn = document.getElementById('signupBtn');
  const verifyOtpBtn = document.getElementById('verifyOtpBtn');
  const messageEl = document.getElementById('message');
  const otpSection = document.getElementById('otp-section');

  function showMessage(msg, type='error') {
    messageEl.textContent = msg;
    messageEl.className = 'message ' + type;
  }

  signupBtn.addEventListener('click', async () => {
    const username = document.getElementById('username').value.trim();
    const email = document.getElementById('email').value.trim();
    const password = document.getElementById('password').value.trim();

    if (!username || !email || !password) {
      showMessage('All fields are required.');
      return;
    }

    signupBtn.disabled = true;
    signupBtn.textContent = 'Sending OTP...';

    try {
      const res = await fetch('/signup', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, email, password })
      });

      const data = await res.json();

      if (!res.ok) throw new Error(data.message || 'Signup failed');

      showMessage('OTP sent to your email!', 'success');
      otpSection.style.display = 'block';
      signupBtn.style.display = 'none';

      // Lock inputs
      document.getElementById('username').readOnly = true;
      document.getElementById('email').readOnly = true;
      document.getElementById('password').readOnly = true;

    } catch (err) {
      showMessage(err.message || 'An error occurred.');
      signupBtn.disabled = false;
      signupBtn.textContent = 'Signup & Send OTP';
    }
  });

  verifyOtpBtn.addEventListener('click', async () => {
    const email = document.getElementById('email').value.trim();
    const otp = document.getElementById('otp').value.trim();

    if (otp.length !== 6) {
      showMessage('Please enter a valid 6-digit OTP.');
      return;
    }

    verifyOtpBtn.disabled = true;
    verifyOtpBtn.textContent = 'Verifying...';

    try {
      const res = await fetch('/verify_otp', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, otp })
      });

      const data = await res.json();

      if (!res.ok) throw new Error(data.message || 'OTP verification failed');

      showMessage('OTP verified! You are now logged in.', 'success');

      // Redirect after short delay
      setTimeout(() => window.location.href = '/dashboard', 1500);

    } catch (err) {
      showMessage(err.message || 'Verification error.');
      verifyOtpBtn.disabled = false;
      verifyOtpBtn.textContent = 'Verify OTP';
    }
  });
</script>

</body>
</html>
"""


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'GET':
        return render_template_string(signup_html)

    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': 'Invalid request data'}), 400

    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not username or not email or not password:
        return jsonify({'success': False, 'message': 'All fields are required'}), 400

    if email in users:
        return jsonify({'success': False, 'message': 'Email already registered'}), 400

    # Save user data temporarily (in real app, save hashed password in DB)
    users[email] = {
        'username': username,
        'password': password
    }

    # Generate 6-digit OTP
    otp = f"{random.randint(100000, 999999)}"
    otp_store[email] = otp

    # Simulate sending OTP by printing in server console (replace with real email sending)
    print(f"Sending OTP to {email}: {otp}")

    return jsonify({'success': True, 'message': 'OTP sent to your email'}), 200


@app.route('/verify_otp', methods=['POST'])
def verify_otp():
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': 'Invalid request data'}), 400

    email = data.get('email')
    otp = data.get('otp')

    if not email or not otp:
        return jsonify({'success': False, 'message': 'Email and OTP required'}), 400

    saved_otp = otp_store.get(email)
    if not saved_otp:
        return jsonify({'success': False, 'message': 'No OTP found for this email'}), 400

    if otp != saved_otp:
        return jsonify({'success': False, 'message': 'Incorrect OTP'}), 400

    # OTP correct - clear OTP and log user in
    otp_store.pop(email)

    # For demo: store login state in users dict (not recommended for production)
    users[email]['logged_in'] = True

    return jsonify({'success': True, 'message': 'OTP verified! Logged in.'}), 200


@app.route('/dashboard')
def dashboard():
    # For demo, just a simple page
    return "<h1>Welcome to your dashboard!</h1><p><a href='/signup'>Logout</a></p>"


@app.route('/login')
def login():
    # Simple placeholder
    return "<h1>Login Page - implement as needed</h1><p><a href='/signup'>Go to Signup</a></p>"


@app.route('/')
def home():
    return redirect(url_for('signup'))


if __name__ == "__main__":
    app.run(debug=True)
