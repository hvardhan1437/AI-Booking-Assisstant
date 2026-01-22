import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import streamlit as st


def send_confirmation_email(to_email, booking_id, booking):
    try:
        sender_email = st.secrets["EMAIL_USER"]
        sender_password = st.secrets["EMAIL_PASS"]

        msg = MIMEMultipart()
        msg["From"] = sender_email
        msg["To"] = to_email
        msg["Subject"] = "Appointment Confirmation – AI Clinic"

        body = f"""
Dear {booking['name']},

Thank you for scheduling an appointment with AI Clinic.

Here are your appointment details:

Service: {booking['booking_type']}
Date: {booking['date']}
Time: {booking['time']}
Booking ID: {booking_id}

Please arrive at least 10 minutes before your scheduled time.

If you need any further assistance, reply to this email or contact our support team.

Warm regards,
AI Clinic Team
"""

        msg.attach(MIMEText(body, "plain"))

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()

        return True

    except Exception as e:
        print("Email error:", e)
        return False
