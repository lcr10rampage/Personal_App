import anthropic
import os
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

CEO_PROMPT = """
You are the user's personal chief of staff — calm, organized, and trusted.

You have four calendar tools:
- call_calendar_manager: READ the user's schedule, check availability, find conflicts
- create_calendar_event: CREATE a new event
- update_calendar_event: CHANGE an existing event (time, title, description)
- delete_calendar_event: DELETE an event

CRITICAL RULES — follow these exactly:
1. When the user asks you to do something, DO IT IMMEDIATELY using tools. Never say "I will" or "I can". Just act.
2. If a task requires multiple steps (e.g. check conflicts, delete them, then update), call tools one at a time until all steps are done.
3. When the user says "get rid of anything in the way", check the schedule first, then delete every conflicting event.
4. Never ask for confirmation. The user gave you the instruction — execute it.
5. Today's date is 2026-07-16. The user's timezone is America/New_York (EDT, UTC-4).
6. When the user says "6pm", generate 2026-XX-XXT18:00:00. Do not add or subtract any offset.

After completing all tool calls, give a short calm confirmation of what was done.
"""

TOOLS = [
    {
        "name": "call_calendar_manager",
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
                "search_name": {"type": "string", "description": "Part of the event name to search for"},
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
                "search_name": {"type": "string", "description": "Part of the event name to search for and delete"}
            },
            "required": ["search_name"]
        }
    }
]

def handle_tool_call(block):
    from agents.managers import calendar_manager, create_event, update_calendar_event, delete_calendar_event
    if block.name == "call_calendar_manager":
        return calendar_manager(block.input["query"])
    elif block.name == "create_calendar_event":
        return create_event(
            summary=block.input["summary"],
            start_datetime=block.input["start_datetime"],
            end_datetime=block.input["end_datetime"],
            description=block.input.get("description", "")
        )
    elif block.name == "update_calendar_event":
        return update_calendar_event(
            search_name=block.input["search_name"],
            new_summary=block.input.get("new_summary"),
            new_start_datetime=block.input.get("new_start_datetime"),
            new_end_datetime=block.input.get("new_end_datetime"),
            new_description=block.input.get("new_description")
        )
    elif block.name == "delete_calendar_event":
        return delete_calendar_event(search_name=block.input["search_name"])
    return "Unknown tool."

def run_ceo(user_message: str, history: list) -> str:
    messages = history + [{"role": "user", "content": user_message}]

    # Loop until the CEO is done calling tools
    while True:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=CEO_PROMPT,
            tools=TOOLS,
            messages=messages
        )

        if response.stop_reason == "end_turn":
            return response.content[0].text

        if response.stop_reason == "tool_use":
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    result = handle_tool_call(block)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result
                    })

            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": tool_results})
