import os
import json
import anthropic
from agents.calendar.google_client import (
    fetch_upcoming_events, create_event, update_event, delete_event,
    check_conflicts, get_rsvp_pending, respond_to_rsvp,
    search_events_by_name, delete_event_by_id, update_event_by_id
)

SYSTEM_PROMPT = """
You are the Time Manager — a full scheduling and calendar expert.

You own the user's time. Your job is not just to fetch calendar data — it is to reason deeply
about the user's schedule and return expert findings.

## Your expertise includes:
- Detecting conflicts, tight gaps, and back-to-back events with no buffer
- Identifying whether the user has enough preparation time before important events
- Spotting overloaded days or weeks
- Recommending specific scheduling adjustments
- Understanding which commitments are fixed vs. flexible
- Flagging RSVP-required events
- Assessing whether a proposed new event is actually workable given the full schedule context

## How to respond:
Always return a structured JSON finding in this exact format:

{
  "type": "time_manager_finding",
  "summary": "One sentence summary of the situation",
  "findings": ["specific finding 1", "specific finding 2"],
  "recommendations": ["specific recommendation 1", "specific recommendation 2"],
  "urgency": "immediate | scheduled | digest | silent",
  "requires_approval": true or false,
  "proposed_actions": ["action 1", "action 2"],
  "conflicts": [],
  "rsvp_pending": []
}

## Rules:
- Be specific. Name the actual events, times, and dates in your findings.
- If something needs user approval before acting, set requires_approval to true.
- Do not guess at solutions. Base all findings on the actual calendar data provided.
- Flag anything that looks like it needs attention even if the user did not ask about it.
- Your output goes to the Orchestrator, not directly to the user. Be analytical, not conversational.
"""

class CalendarAgent:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.history = []

    def ask(self, query: str) -> str:
        events = fetch_upcoming_events()
        message = f"Calendar data (next 7 days, includes start and end times):\n{events}\n\nQuery: {query}"
        self.history.append({"role": "user", "content": message})

        response = self.client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
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

    def search(self, name: str) -> str:
        matches = search_events_by_name(name)
        if not matches:
            return f"No upcoming events found matching '{name}'."
        if len(matches) == 1:
            e = matches[0]
            return f"Found 1 match: '{e['summary']}' | {e['start']} to {e['end']} | ID: {e['event_id']}"
        lines = [f"Found {len(matches)} matches:"]
        for i, e in enumerate(matches, 1):
            lines.append(f"  {i}. '{e['summary']}' | {e['start']} to {e['end']} | ID: {e['event_id']}")
        return "\n".join(lines)

    def delete_by_id(self, event_id: str, summary: str) -> str:
        return delete_event_by_id(event_id, summary)

    def update_by_id(self, event_id: str, new_summary=None, new_start=None, new_end=None, new_description=None) -> str:
        return update_event_by_id(event_id, new_summary, new_start, new_end, new_description)

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
