import os
import anthropic
from agents.calendar.agent import CalendarAgent
from agents.email.agent import EmailAgent

SYSTEM_PROMPT = """
You are the Orchestrator — the user's personal chief of staff. Calm, organized, and trusted.

Your job: coordinate specialist managers, combine their findings, deliver one clear response.
You do not own data. You route, coordinate, resolve conflicts, and communicate.

---

## PROCESSING RULES — Follow these exactly, in order.

### Rule 1: Multiple instructions = one at a time
When the user gives more than one instruction in a single message:
- Mentally number each task: Task 1, Task 2, Task 3...
- Complete Task 1 fully (all tool calls done, result confirmed) before starting Task 2.
- Never attempt two tasks simultaneously.

### Rule 2: Search before delete or update
When deleting or updating a calendar event:
- FIRST call search_calendar_events with the event name.
- If 0 results → tell the user nothing was found.
- If 1 result → confirm the exact event name and time to the user, then execute immediately.
- If 2+ results → list all matches and ask: "Which one did you mean?" Wait for their answer.
- NEVER delete or update without knowing the exact event_id first.

### Rule 3: Check conflicts before creating
Before creating any event, call check_calendar_conflicts.
- "no_conflicts" → create immediately.
- Conflicts found → STOP. Tell the user what overlaps. Ask: "Reschedule [event] to fit, or delete it entirely?" Wait for answer, then execute.

### Rule 4: RSVP requires approval
When get_rsvp_pending returns items with requires_approval: true:
- STOP. Present each pending RSVP to the user one at a time.
- Ask: "Can you make it to [event name] on [date]? Yes, No, or Maybe?"
- Call respond_to_rsvp only after the user answers.

### Rule 5: Act, don't narrate
Never say "I will" or "I'm going to". Use tools immediately.
After all tools complete, give one short calm summary of what was done.

### Rule 6: Time and date
Today is 2026-07-17. Timezone: America/New_York (EDT, UTC-4).
When the user says "6pm" → generate T18:00:00. Do NOT apply any offset manually.

### Rule 7: Email safety
Never send an email. Create drafts only. Always show the draft to the user first.

---

## AVAILABLE TOOLS

- search_calendar_events — search by name, returns all matches with event_id. Use before delete/update.
- call_calendar_agent — read schedule, check availability
- create_calendar_event — create a new event
- update_calendar_event_by_id — update using exact event_id (get this from search first)
- delete_calendar_event_by_id — delete using exact event_id (get this from search first)
- check_calendar_conflicts — check if a time slot is free
- get_rsvp_pending — check for events needing RSVP
- respond_to_rsvp — submit RSVP response
- call_email_agent — read and summarize emails
"""

TOOLS = [
    {
        "name": "search_calendar_events",
        "description": "Search for calendar events by name. Returns all matches with their event_id, summary, start, and end. Always call this before deleting or updating an event.",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Event name or partial name to search for"}
            },
            "required": ["name"]
        }
    },
    {
        "name": "call_calendar_agent",
        "description": "Read the user's upcoming calendar events, check availability, or answer schedule questions",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"}
            },
            "required": ["query"]
        }
    },
    {
        "name": "create_calendar_event",
        "description": "Create a new event on the user's Google Calendar. Always check conflicts first.",
        "input_schema": {
            "type": "object",
            "properties": {
                "summary": {"type": "string"},
                "start_datetime": {"type": "string", "description": "ISO 8601, e.g. 2026-07-17T15:00:00"},
                "end_datetime": {"type": "string", "description": "ISO 8601, e.g. 2026-07-17T16:00:00"},
                "description": {"type": "string"}
            },
            "required": ["summary", "start_datetime", "end_datetime"]
        }
    },
    {
        "name": "update_calendar_event_by_id",
        "description": "Update a calendar event using its exact event_id. Get the event_id from search_calendar_events first.",
        "input_schema": {
            "type": "object",
            "properties": {
                "event_id": {"type": "string"},
                "new_summary": {"type": "string"},
                "new_start_datetime": {"type": "string"},
                "new_end_datetime": {"type": "string"},
                "new_description": {"type": "string"}
            },
            "required": ["event_id"]
        }
    },
    {
        "name": "delete_calendar_event_by_id",
        "description": "Delete a calendar event using its exact event_id. Get the event_id from search_calendar_events first.",
        "input_schema": {
            "type": "object",
            "properties": {
                "event_id": {"type": "string"},
                "summary": {"type": "string", "description": "Event name, used for confirmation message"}
            },
            "required": ["event_id", "summary"]
        }
    },
    {
        "name": "check_calendar_conflicts",
        "description": "Check if a proposed time slot conflicts with existing events. Always call before creating.",
        "input_schema": {
            "type": "object",
            "properties": {
                "start_datetime": {"type": "string"},
                "end_datetime": {"type": "string"}
            },
            "required": ["start_datetime", "end_datetime"]
        }
    },
    {
        "name": "get_rsvp_pending",
        "description": "Check for calendar events that need the user's RSVP.",
        "input_schema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "respond_to_rsvp",
        "description": "Submit the user's RSVP response for a calendar event.",
        "input_schema": {
            "type": "object",
            "properties": {
                "event_id": {"type": "string"},
                "response": {"type": "string", "description": "accepted, declined, or tentative"}
            },
            "required": ["event_id", "response"]
        }
    },
    {
        "name": "call_email_agent",
        "description": "Read and summarize recent emails, find action items, deadlines, or important changes",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"}
            },
            "required": ["query"]
        }
    }
]

class CEOAgent:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.history = []
        self.calendar = CalendarAgent()
        self.email = EmailAgent()

    def chat(self, user_message: str) -> str:
        self.history.append({"role": "user", "content": user_message})

        while True:
            response = self.client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=2048,
                system=SYSTEM_PROMPT,
                tools=TOOLS,
                messages=self.history
            )

            if response.stop_reason == "end_turn":
                reply = response.content[0].text
                self.history.append({"role": "assistant", "content": reply})
                return reply

            if response.stop_reason == "tool_use":
                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        result = self._handle_tool(block)
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result
                        })
                self.history.append({"role": "assistant", "content": response.content})
                self.history.append({"role": "user", "content": tool_results})

    def _handle_tool(self, block) -> str:
        if block.name == "search_calendar_events":
            return self.calendar.search(block.input["name"])
        elif block.name == "call_calendar_agent":
            return self.calendar.ask(block.input["query"])
        elif block.name == "create_calendar_event":
            return self.calendar.create(
                summary=block.input["summary"],
                start_datetime=block.input["start_datetime"],
                end_datetime=block.input["end_datetime"],
                description=block.input.get("description", "")
            )
        elif block.name == "update_calendar_event_by_id":
            return self.calendar.update_by_id(
                event_id=block.input["event_id"],
                new_summary=block.input.get("new_summary"),
                new_start=block.input.get("new_start_datetime"),
                new_end=block.input.get("new_end_datetime"),
                new_description=block.input.get("new_description")
            )
        elif block.name == "delete_calendar_event_by_id":
            return self.calendar.delete_by_id(
                event_id=block.input["event_id"],
                summary=block.input["summary"]
            )
        elif block.name == "check_calendar_conflicts":
            return self.calendar.conflicts(
                start_datetime=block.input["start_datetime"],
                end_datetime=block.input["end_datetime"]
            )
        elif block.name == "get_rsvp_pending":
            return self.calendar.get_rsvp_findings()
        elif block.name == "respond_to_rsvp":
            return self.calendar.respond_rsvp(
                event_id=block.input["event_id"],
                response=block.input["response"]
            )
        elif block.name == "call_email_agent":
            return self.email.ask(block.input["query"])
        return "Unknown tool."
