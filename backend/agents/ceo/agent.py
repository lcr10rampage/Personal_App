import os
import anthropic
from agents.calendar.agent import CalendarAgent

SYSTEM_PROMPT = """
You are the user's personal chief of staff — calm, organized, and trusted.

You have specialist agents you can call:
- call_calendar_agent: READ the user's schedule, check availability, find conflicts
- create_calendar_event: CREATE a new event on the user's calendar
- update_calendar_event: CHANGE an existing event (time, title, description)
- delete_calendar_event: DELETE an event from the user's calendar

CRITICAL RULES:
1. When the user asks you to do something, DO IT IMMEDIATELY using tools. Never say "I will" or "I can". Just act.
2. If a task requires multiple steps, call tools one at a time until all steps are done.
3. When the user says "get rid of anything in the way", check the schedule then delete every conflicting event.
4. Never ask for confirmation. The user gave the instruction — execute it.
5. Today's date is 2026-07-17. The user's timezone is America/New_York (EDT, UTC-4).
6. When the user says "6pm", generate 2026-XX-XXT18:00:00 — do NOT add or subtract any offset.

After all tool calls are done, give a short calm confirmation of what was done.
"""

TOOLS = [
    {
        "name": "call_calendar_agent",
        "description": "Read the user's upcoming calendar events, check availability, or find conflicts",
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
        "description": "Create a new event on the user's Google Calendar",
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
        "name": "update_calendar_event",
        "description": "Update an existing event — change its time, title, or description",
        "input_schema": {
            "type": "object",
            "properties": {
                "search_name": {"type": "string"},
                "new_summary": {"type": "string"},
                "new_start_datetime": {"type": "string"},
                "new_end_datetime": {"type": "string"},
                "new_description": {"type": "string"}
            },
            "required": ["search_name"]
        }
    },
    {
        "name": "delete_calendar_event",
        "description": "Delete an existing event from the user's calendar",
        "input_schema": {
            "type": "object",
            "properties": {
                "search_name": {"type": "string"}
            },
            "required": ["search_name"]
        }
    }
]

class CEOAgent:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.history = []
        self.calendar = CalendarAgent()

    def chat(self, user_message: str) -> str:
        self.history.append({"role": "user", "content": user_message})

        while True:
            response = self.client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=1024,
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
        if block.name == "call_calendar_agent":
            return self.calendar.ask(block.input["query"])
        elif block.name == "create_calendar_event":
            return self.calendar.create(
                summary=block.input["summary"],
                start_datetime=block.input["start_datetime"],
                end_datetime=block.input["end_datetime"],
                description=block.input.get("description", "")
            )
        elif block.name == "update_calendar_event":
            return self.calendar.update(
                search_name=block.input["search_name"],
                new_summary=block.input.get("new_summary"),
                new_start=block.input.get("new_start_datetime"),
                new_end=block.input.get("new_end_datetime"),
                new_description=block.input.get("new_description")
            )
        elif block.name == "delete_calendar_event":
            return self.calendar.delete(search_name=block.input["search_name"])
        return "Unknown tool."
