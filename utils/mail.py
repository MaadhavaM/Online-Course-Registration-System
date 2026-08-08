from flask_mail import Message
from extensions import mail
from flask import current_app
import threading
import socket

def send_otp_email(to, otp):
    # Render blocks outbound SMTP by default, causing a 30s hang and 500 Error.
    # We set a 5-second socket timeout so Gunicorn doesn't crash.
    socket.setdefaulttimeout(5.0)
    print(f"--- ATTENTION: OTP for {to} is: {otp} ---") # Print to Render logs as a fallback
    
    try:
        msg = Message(
            subject='Your OTP Code',
            sender=current_app.config.get('MAIL_USERNAME', 'noreply@online-course.com'),
            recipients=[to]
        )
        msg.body = f'Your OTP for login/verification is: {otp}\nPlease do not share this code with anyone.'
        
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False
    finally:
        socket.setdefaulttimeout(None) # Reset timeout

def send_certificate_email(to, course_name, certificate_url):
    socket.setdefaulttimeout(5.0)
    print(f"--- ATTENTION: Certificate for {course_name} sent to {to}. Link: {certificate_url} ---")
    
    try:
        msg = Message(
            subject=f'Congratulations on completing {course_name}!',
            sender=current_app.config.get('MAIL_USERNAME', 'noreply@unicore.com'),
            recipients=[to]
        )
        msg.body = f'''Hello,

Congratulations on successfully completing the course: {course_name}!

Your official certificate of completion is now ready. 
You can view and download it at any time using the following link:
{certificate_url}

Best regards,
The UniCore Education Team'''
        
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Error sending certificate email: {e}")
        return False
    finally:
        socket.setdefaulttimeout(None)
