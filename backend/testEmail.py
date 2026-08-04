import os
from dotenv import load_dotenv

from fastapi import FastAPI
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig

# Load environment variables
load_dotenv()

app = FastAPI()

# Mail Configuration
conf = ConnectionConfig(
    MAIL_USERNAME=os.getenv("EMAIL_HOST_USER"),
    MAIL_PASSWORD=os.getenv("EMAIL_HOST_PASSWORD"),
    MAIL_FROM=os.getenv("EMAIL_HOST_USER"),
    MAIL_SERVER=os.getenv("EMAIL_HOST"),
    MAIL_PORT=int(os.getenv("EMAIL_PORT")),
    MAIL_STARTTLS=os.getenv("EMAIL_USE_TLS") == "True",
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
)


@app.get("/")
async def home():
    return {"message": "FastAPI Email Server Running"}


@app.get("/send-email")
async def send_email():

    message = MessageSchema(
        subject="FastAPI Gmail Test",
        recipients=["yatinrastogi05@gmail.com"],   # Change this if you want
        body="""
        <h2>Hello Yatin 👋</h2>

        <p>This email was sent successfully using <b>FastAPI + Gmail SMTP</b>.</p>

        <p>If you received this email, your SMTP configuration is working correctly.</p>

        <br>

        <p>Regards,</p>
        <b>ClinicaFlow Backend</b>
        """,
        subtype="html",
    )

    fm = FastMail(conf)

    try:
        await fm.send_message(message)
        return {"status": "success", "message": "Email sent successfully"}

    except Exception as e:
        return {"status": "error", "message": str(e)}