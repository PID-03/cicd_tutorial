from flask_mail import Message
from extensions import mail   
def send_email(to, subject, html_body):
    msg = Message(
        subject=subject,
        recipients=[to],
        html=html_body
    )
    mail.send(msg)