from datetime import datetime, timezone, timedelta
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

SCOPES = [
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/calendar.events"
]

def get_service():
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    return build("calendar", "v3", credentials=creds)

def fetch_upcoming_events(days=7) -> str:
    service = get_service()
    now = datetime.now(timezone.utc)
    time_max = (now + timedelta(days=days)).isoformat()
    result = service.events().list(
        calendarId="primary",
        timeMin=now.isoformat(),
        timeMax=time_max,
        maxResults=50,
        singleEvents=True,
        orderBy="startTime"
    ).execute()
    events = result.get("items", [])
    if not events:
        return "No upcoming events in the next 7 days."
    lines = []
    for e in events:
        start = e["start"].get("dateTime", e["start"].get("date"))
        end = e["end"].get("dateTime", e["end"].get("date"))
        lines.append(f"- {e['summary']} | start: {start} | end: {end}")
    return "\n".join(lines)

def find_event(service, name: str):
    now = datetime.now(timezone.utc).isoformat()
    result = service.events().list(
        calendarId="primary",
        timeMin=now,
        maxResults=50,
        singleEvents=True,
        orderBy="startTime"
    ).execute()
    for e in result.get("items", []):
        if name.lower() in e.get("summary", "").lower():
            return e
    return None

def create_event(summary: str, start_datetime: str, end_datetime: str, description: str = "") -> str:
    service = get_service()
    event = {
        "summary": summary,
        "description": description,
        "start": {"dateTime": start_datetime, "timeZone": "America/New_York"},
        "end": {"dateTime": end_datetime, "timeZone": "America/New_York"},
    }
    service.events().insert(calendarId="primary", body=event).execute()
    return f"Created '{summary}' from {start_datetime} to {end_datetime}."

def update_event(search_name: str, new_summary: str = None, new_start: str = None, new_end: str = None, new_description: str = None) -> str:
    service = get_service()
    event = find_event(service, search_name)
    if not event:
        return f"No upcoming event found matching '{search_name}'."
    if new_summary:
        event["summary"] = new_summary
    if new_start:
        event["start"] = {"dateTime": new_start, "timeZone": "America/New_York"}
    if new_end:
        event["end"] = {"dateTime": new_end, "timeZone": "America/New_York"}
    if new_description is not None:
        event["description"] = new_description
    updated = service.events().update(calendarId="primary", eventId=event["id"], body=event).execute()
    return f"Updated '{updated['summary']}'."

def delete_event(search_name: str) -> str:
    service = get_service()
    event = find_event(service, search_name)
    if not event:
        return f"No upcoming event found matching '{search_name}'."
    service.events().delete(calendarId="primary", eventId=event["id"]).execute()
    return f"Deleted '{event.get('summary')}'."
