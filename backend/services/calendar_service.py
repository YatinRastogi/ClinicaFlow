import uuid
from datetime import datetime

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/calendar"]

# Path to token.json — sits at the backend root directory
TOKEN_PATH = "token.json"


def create_google_meet(
    summary: str,
    description: str,
    start_time: datetime,
    end_time: datetime,
    attendees: list[str],
) -> dict:
    """
    Creates a Google Calendar event with a Google Meet link and sends
    invitations to all attendees via Google Calendar's built-in email.

    Returns:
        {
            "meet_link": "https://meet.google.com/...",
            "event_id":  "<google-calendar-event-id>",
        }

    Raises:
        RuntimeError if the token file is missing or the API call fails.
    """
    import os

    if not os.path.exists(TOKEN_PATH):
        raise RuntimeError(
            f"Google OAuth token file not found at '{TOKEN_PATH}'. "
            "Run the OAuth flow first to generate token.json."
        )

    creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

    service = build("calendar", "v3", credentials=creds)

    event = {
        "summary": summary,
        "description": description,
        "start": {
            "dateTime": start_time.isoformat(),
            "timeZone": "Asia/Kolkata",
        },
        "end": {
            "dateTime": end_time.isoformat(),
            "timeZone": "Asia/Kolkata",
        },
        "attendees": [{"email": email} for email in attendees],
        "conferenceData": {
            "createRequest": {
                "requestId": str(uuid.uuid4()),
                "conferenceSolutionKey": {
                    "type": "hangoutsMeet"
                },
            }
        },
    }

    created_event = (
        service.events()
        .insert(
            calendarId="primary",
            body=event,
            conferenceDataVersion=1,
            # "all" means Google Calendar emails invitations to attendees
            sendUpdates="all",
        )
        .execute()
    )

    meet_link = created_event.get("hangoutLink")
    if not meet_link:
        raise RuntimeError(
            "Google Calendar API did not return a Meet link. "
            "Ensure the Google Meet add-on is enabled for this account."
        )

    return {
        "meet_link": meet_link,
        "event_id": created_event["id"],
    }