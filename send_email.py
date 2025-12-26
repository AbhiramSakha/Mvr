import smtplib
from email.message import EmailMessage
import os
import traceback
from dotenv import load_dotenv

load_dotenv()

EMAIL_USER = os.getenv("MAIL_USERNAME")
EMAIL_PASS = os.getenv("MAIL_PASSWORD")

def send_otp_email(to_email, otp):
    try:
        if not EMAIL_USER or not EMAIL_PASS:
            raise ValueError("MAIL_USERNAME or MAIL_PASSWORD not loaded from .env")

        msg = EmailMessage()
        msg["Subject"] = "Your OTP for Login"
        msg["From"] = EMAIL_USER
        msg["To"] = to_email
        msg.set_content(f"Hello,\n\nYour OTP is: {otp}\nThis OTP is valid for 5 minutes.\n\n– Team")

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_USER, EMAIL_PASS)
            server.send_message(msg)

        print("✅ OTP EMAIL SENT TO", to_email)
    except Exception as e:
        print("❌ EMAIL FAILED")
        traceback.print_exc()
        raise
