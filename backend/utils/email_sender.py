import os
from dotenv import load_dotenv
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema

load_dotenv()

# We set default fallbacks so it doesn't crash if env vars are missing, 
# but they need to be populated in .env to actually send.
conf = ConnectionConfig(
    MAIL_USERNAME=os.getenv("EMAIL_HOST_USER"),
    MAIL_PASSWORD=os.getenv("EMAIL_HOST_PASSWORD"),
    MAIL_FROM=os.getenv("EMAIL_HOST_USER"),
    MAIL_SERVER=os.getenv("EMAIL_HOST"),
    MAIL_PORT=int(os.getenv("EMAIL_PORT", "587")),
    MAIL_STARTTLS=os.getenv("EMAIL_USE_TLS") == "True",
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
)

async def send_appointment_email(to_email: str, patient_name: str, doctor_name: str, time: str, meet_link: str, duration: str):
    if not conf.MAIL_USERNAME or not conf.MAIL_PASSWORD:
        print(f"Skipping email to {to_email} because MAIL_USERNAME or MAIL_PASSWORD is not set.")
        return

    try:
        body = f"""
        <h2>Appointment Confirmation with {doctor_name}</h2>
        <p>Hello {patient_name},</p>
        <p>Your appointment with {doctor_name} has been successfully booked.</p>
        <p><b>Details:</b></p>
        <ul>
            <li><b>Date & Time:</b> {time}</li>
            <li><b>Type:</b> {duration}</li>
            <li><b>Meeting Link:</b> <a href="{meet_link}">{meet_link}</a></li>
        </ul>
        <p>Please keep this link handy to join your consultation.</p>
        <p>Regards,<br>ClinicaFlow Team</p>
        """

        message = MessageSchema(
            subject=f"Appointment Confirmation with {doctor_name}",
            recipients=[to_email],
            body=body,
            subtype="html",
        )

        fm = FastMail(conf)
        await fm.send_message(message)
        print(f"Successfully sent appointment email to {to_email} via fastapi-mail")
    except Exception as e:
        print(f"Failed to send email to {to_email}. Error: {e}")
