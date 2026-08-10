from datetime import datetime, timedelta

from services.calendar_service import create_google_meet

result = create_google_meet(
    summary="ClinicaFlow Demo Appointment",
    description="Testing Google Meet generation",
    start_time=datetime.now() + timedelta(minutes=5),
    end_time=datetime.now() + timedelta(minutes=35),
    attendees=[
        "yatin.rastogi.81@gmail.com"
    ],
)

print(result)