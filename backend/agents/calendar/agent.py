import os
import anthropic
import json
from agents.calendar.google_client import (
    fetch_upcoming_events, create_event, update_event, delete_event,
    check_conflicts, get_rsvp_pending, respond_to_rsvp
)

SYSTEM_PROMPT = """
You are the Calendar Manager — a specialist responsible for the user's schedule.

You have access to the user's real Google Calendar data for the next 7 days, including
exact start AND end times for every event. Use both when reasoning about conflicts or gaps.

Rules:
- Answer the specific question using the calendar data provided. Do not dump the full schedule unless asked.
- When reasoning about conflicts, always check end times — not just start times.
- Be precise about times and dates. Never guess.
- The user's timezone is America/New_York (EDT, UTC-4).
"""

class CalendarAgent:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.history = []

    def ask(self, query: str) -> str:
        events = fetch_upcoming_events()
        message = f"Current calendar (next 7 days):\n{events}\n\nQuery: {query}"
        self.history.append({"role": "user", "content": message})

        response = self.client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=512,
            system=SYSTEM_PROMPT,
            messages=self.history
        )
        reply = response.content[0].text
        self.history.append({"role": "assistant", "content": reply})
        return reply

    def create(self, summary: str, start_datetime: str, end_datetime: str, description: str = "") -> str:
        return create_event(summary, start_datetime, end_datetime, description)

    def update(self, search_name: str, new_summary=None, new_start=None, new_end=None, new_description=None) -> str:
        return update_event(search_name, new_summary, new_start, new_end, new_description)

    def delete(self, search_name: str) -> str:
        return delete_event(search_name)

    def conflicts(self, start_datetime: str, end_datetime: str) -> str:
        return check_conflicts(start_datetime, end_datetime)

    def get_rsvp_findings(self) -> str:
        pending = get_rsvp_pending()
        if not pending:
            return json.dumps({
                "type": "rsvp_check",
                "summary": "No pending RSVPs.",
                "requires_approval": False,
                "items": []
            })
        return json.dumps({
            "type": "rsvp_check",
            "summary": f"{len(pending)} event(s) need your RSVP.",
            "requires_approval": True,
            "urgency": "scheduled",
            "items": pending
        })

    def respond_rsvp(self, event_id: str, response: str) -> str:
        return respond_to_rsvp(event_id, response)
