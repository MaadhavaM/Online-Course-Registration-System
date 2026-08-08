from flask_mail import Message
from extensions import mail
from flask import current_app
import threading

def send_otp_email(to, otp):
    try:
        msg = Message(
            subject='Your OTP Code',
            sender=current_app.config.get('MAIL_USERNAME', 'noreply@online-course.com'),
            recipients=[to]
        )
        msg.body = f'Your OTP code is: {otp}\n\nPlease do not share this code with anyone.'
        
        mail.send(msg)
        print(f"Email sent successfully to {to}")
        return True
    except Exception as e:
        print(f"Error sending email to {to}: {e}")
        return False
