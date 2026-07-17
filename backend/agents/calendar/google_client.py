from datetime import datetime, timezone, timedelta
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

SCOPES = [
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/calendar.events",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.compose",
    "https://www.googleapis.com/auth/gmail.send"
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

def search_events_by_name(name: str) -> list:
    service = get_service()
    now = datetime.now(timezone.utc).isoformat()
    result = service.events().list(
        calendarId="primary",
        timeMin=now,
        maxResults=50,
        singleEvents=True,
        orderBy="startTime"
    ).execute()
    matches = []
    for e in result.get("items", []):
        if name.lower() in e.get("summary", "").lower():
            start = e["start"].get("dateTime", e["start"].get("date"))
            end = e["end"].get("dateTime", e["end"].get("date"))
            matches.append({
                "event_id": e["id"],
                "summary": e.get("summary", "(no title)"),
                "start": start,
                "end": end
            })
    return matches

def delete_event_by_id(event_id: str, summary: str) -> str:
    service = get_service()
    service.events().delete(calendarId="primary", eventId=event_id).execute()
    return f"Deleted '{summary}'."

def update_event_by_id(event_id: str, new_summary: str = None, new_start: str = None, new_end: str = None, new_description: str = None) -> str:
    service = get_service()
    event = service.events().get(calendarId="primary", eventId=event_id).execute()
    if new_summary:
        event["summary"] = new_summary
    if new_start:
        event["start"] = {"dateTime": new_start, "timeZone": "America/New_York"}
    if new_end:
        event["end"] = {"dateTime": new_end, "timeZone": "America/New_York"}
    if new_description is not None:
        event["description"] = new_description
    updated = service.events().update(calendarId="primary", eventId=event_id, body=event).execute()
    return f"Updated '{updated['summary']}'."

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

def get_rsvp_pending() -> list:
    service = get_service()
    now = datetime.now(timezone.utc)
    time_max = (now + timedelta(days=30)).isoformat()
    result = service.events().list(
        calendarId="primary",
        timeMin=now.isoformat(),
        timeMax=time_max,
        maxResults=50,
        singleEvents=True,
        orderBy="startTime"
    ).execute()

    pending = []
    for e in result.get("items", []):
        attendees = e.get("attendees", [])
        for a in attendees:
            if a.get("self") and a.get("responseStatus") == "needsAction":
                start = e["start"].get("dateTime", e["start"].get("date"))
                end = e["end"].get("dateTime", e["end"].get("date"))
                pending.append({
                    "event_id": e["id"],
                    "summary": e.get("summary", "(no title)"),
                    "start": start,
                    "end": end,
                    "organizer": e.get("organizer", {}).get("email", "unknown")
                })
    return pending

def respond_to_rsvp(event_id: str, response: str) -> str:
    service = get_service()
    event = service.events().get(calendarId="primary", eventId=event_id).execute()
    attendees = event.get("attendees", [])
    for a in attendees:
        if a.get("self"):
            a["responseStatus"] = response  # "accepted", "declined", or "tentative"
    event["attendees"] = attendees
    service.events().update(calendarId="primary", eventId=event_id, body=event).execute()
    label = {"accepted": "accepted", "declined": "declined", "tentative": "marked as maybe"}.get(response, response)
    return f"RSVP {label} for event ID {event_id}."

def check_conflicts(start_datetime: str, end_datetime: str) -> str:
    service = get_service()
    result = service.events().list(
        calendarId="primary",
        timeMin=start_datetime + "-04:00" if "+" not in start_datetime and "Z" not in start_datetime else start_datetime,
        timeMax=end_datetime + "-04:00" if "+" not in end_datetime and "Z" not in end_datetime else end_datetime,
        singleEvents=True,
        orderBy="startTime"
    ).execute()
    events = result.get("items", [])
    if not events:
        return "no_conflicts"
    lines = []
    for e in events:
        start = e["start"].get("dateTime", e["start"].get("date"))
        end = e["end"].get("dateTime", e["end"].get("date"))
        lines.append(f"- {e['summary']} | start: {start} | end: {end}")
    return "CONFLICTS FOUND:\n" + "\n".join(lines)

def delete_event(search_name: str) -> str:
    service = get_service()
    event = find_event(service, search_name)
    if not event:
        return f"No upcoming event found matching '{search_name}'."
    service.events().delete(calendarId="primary", eventId=event["id"]).execute()
    return f"Deleted '{event.get('summary')}'."
