import json
import os
import smtplib
from email.message import EmailMessage

# import openai
from dotenv import load_dotenv

load_dotenv()

GMAIL_ADDRESS = os.getenv("GMAIL_ADDRESS")
GMAIL_PASSWORD= os.getenv("GMAIL_PASSWORD")
RECEIVER_EMAIL= os.getenv("RECEIVER_EMAIL")
SMTP = os.getenv("SMTP")
PORT = os.getenv("PORT")

# openai.api_key = os.getenv("OPENAI_API_KEY")

# function stub for llm to use
def send_email(to: str, subject: str, body: str):
    message = {
        "from": "winston.sapien@gmail.com",
        "to": to,
        "body": body,
        "subject": subject
    }
    return json.dumps(message)

def email_sender (subject, body):
    """ send actual email """
    try:
        sender_email = GMAIL_ADDRESS
        sender_password = GMAIL_PASSWORD
        receiver_email = RECEIVER_EMAIL

        msg = EmailMessage()
        msg.set_content(body)
        msg["Subject"] = subject
        msg["From"] = sender_email
        msg["To"] = receiver_email

        session = smtplib.SMTP(SMTP, PORT)
        session.starttls()
        session.login(sender_email, sender_password)
        session.send_message(msg, sender_email, receiver_email)
        session.quit()
        print("Mail Sent!")
    except Exception as e:
        print (f'Error sending email: {e}')

