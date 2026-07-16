import anthropic
import os
from datetime import datetime, timezone
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

SCOPES = [
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/calendar.events"
]

def get_calendar_service():
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    return build("calendar", "v3", credentials=creds)

def fetch_upcoming_events(days=7):
    service = get_calendar_service()
    now = datetime.now(timezone.utc)
    time_max = (now + __import__("datetime").timedelta(days=days)).isoformat()
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
        return "No upcoming events found in the next 7 days."

    lines = []
    for e in events:
        start = e["start"].get("dateTime", e["start"].get("date"))
        end = e["end"].get("dateTime", e["end"].get("date"))
        lines.append(f"- {e['summary']} | start: {start} | end: {end}")
    return "\n".join(lines)

def find_event_by_name(service, name: str):
    now = datetime.now(timezone.utc).isoformat()
    result = service.events().list(
        calendarId="primary",
        timeMin=now,
        maxResults=50,
        singleEvents=True,
        orderBy="startTime"
    ).execute()
    events = result.get("items", [])
    name_lower = name.lower()
    for e in events:
        if name_lower in e.get("summary", "").lower():
            return e
    return None

def update_calendar_event(search_name: str, new_summary: str = None, new_start_datetime: str = None, new_end_datetime: str = None, new_description: str = None) -> str:
    service = get_calendar_service()
    event = find_event_by_name(service, search_name)
    if not event:
        return f"Could not find an upcoming event matching '{search_name}'."

    if new_summary:
        event["summary"] = new_summary
    if new_start_datetime:
        event["start"] = {"dateTime": new_start_datetime, "timeZone": "America/New_York"}
    if new_end_datetime:
        event["end"] = {"dateTime": new_end_datetime, "timeZone": "America/New_York"}
    if new_description is not None:
        event["description"] = new_description

    updated = service.events().update(
        calendarId="primary",
        eventId=event["id"],
        body=event
    ).execute()
    return f"Event updated: '{updated['summary']}' now starts at {updated['start'].get('dateTime', updated['start'].get('date'))}"

def delete_calendar_event(search_name: str) -> str:
    service = get_calendar_service()
    event = find_event_by_name(service, search_name)
    if not event:
        return f"Could not find an upcoming event matching '{search_name}'."
    service.events().delete(calendarId="primary", eventId=event["id"]).execute()
    return f"Event deleted: '{event.get('summary')}'"

def create_event(summary: str, start_datetime: str, end_datetime: str, description: str = "") -> str:
    service = get_calendar_service()
    event = {
        "summary": summary,
        "description": description,
        "start": {"dateTime": start_datetime, "timeZone": "America/New_York"},
        "end": {"dateTime": end_datetime, "timeZone": "America/New_York"},
    }
    created = service.events().insert(calendarId="primary", body=event).execute()
    return f"Event created: '{summary}' on {start_datetime}"

def calendar_manager(query: str) -> str:
    events_text = fetch_upcoming_events()

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=512,
        system=(
            "You are a calendar specialist. You have the user's full schedule for the next 7 days, "
            "including exact start AND end times for every event. Use both start and end times when "
            "reasoning about conflicts, gaps, or availability. Do not dump the full schedule on the user "
            "unless they ask — just answer their specific question using the data."
        ),
        messages=[{
            "role": "user",
            "content": f"My upcoming events (next 7 days):\n{events_text}\n\nQuestion: {query}"
        }]
    )
    return response.content[0].text
