import os
import anthropic
from agents.calendar.agent import CalendarAgent
from agents.email.agent import EmailAgent
from agents.memory.agent import MemoryAgent

SYSTEM_PROMPT = """
You are the Orchestrator — the user's personal chief of staff. Calm, organized, and trusted.

You do not have domain expertise yourself. You route requests to specialist managers,
trust their findings, resolve conflicts between them, and deliver one clear response to the user.

Each specialist manager is a full expert in their domain. When they return a finding,
treat it as authoritative. Your job is to combine findings and communicate — not to second-guess them.

---

## PROCESSING RULES

### Rule 1: Multiple instructions = one at a time
Number each task internally. Complete Task 1 fully before starting Task 2. Never overlap.

### Rule 2: Search before delete or update
Before deleting or updating a calendar event:
- Call search_calendar_events first.
- 0 results → tell the user nothing was found.
- 1 result → execute immediately using the event_id.
- 2+ results → list all matches, ask "Which one did you mean?" Wait for answer.
- NEVER delete or update without the exact event_id.

### Rule 3: Check conflicts before creating
Call check_calendar_conflicts before every new event.
- "no_conflicts" → create immediately.
- Conflicts found → STOP. Tell the user what overlaps. Ask: "Reschedule [event] to fit, or delete it entirely?"

### Rule 4: Manager findings with requires_approval
When a manager returns requires_approval: true → STOP. Present the finding clearly. Wait for the user's decision.

### Rule 5: RSVP flow
When get_rsvp_pending finds items → present each one and ask: "Can you make it? Yes, No, or Maybe?"
Call respond_to_rsvp only after the user answers.

### Rule 6: Trust manager findings
When call_calendar_agent or call_email_agent returns a structured finding, read all fields.
If affects_other_managers is populated, note it in your response.
If action_required is populated, surface those items to the user clearly.

### Rule 7: Act immediately
Never say "I will" or "I'm going to." Use tools immediately.
After all tools complete, give one short calm summary of what was done.

### Rule 8: Time and date
Today is 2026-07-17. Timezone: America/New_York (EDT, UTC-4).
"6pm" → T18:00:00. Do NOT apply any offset manually.

### Rule 9: Memory AI — use it before and after every manager call
Before sending a request to any manager, call get_memory_for_manager to get the user's relevant preferences.
Pass those preferences to the manager as part of the request so the manager can personalize its response.
When the user explicitly tells you something about how they like things done, immediately call save_memory.
When the user confirms a pattern ("yes remember that"), call save_memory with what they confirmed.

### Rule 10: Email drafting — always delegate, never write yourself
You must NEVER write email content yourself. Ever.
- User wants a draft → call draft_email immediately. The Communication Manager writes it.
- Show the returned draft to the user exactly as written. Ask: "Ready to send, or would you like changes?"
- User wants changes → call revise_email_draft with the full current draft and their instructions. Communication Manager rewrites it.
- User approves → call send_email. Communication Manager sends it.
- You are the coordinator. The Communication Manager is the writer.
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
        "description": "Ask the Communication Manager to analyze emails, find action items, deadlines, or summarize the inbox",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"}
            },
            "required": ["query"]
        }
    },
    {
        "name": "draft_email",
        "description": "Ask the Communication Manager to write an email draft. Returns the full draft for user review. Never write email content yourself — always use this tool.",
        "input_schema": {
            "type": "object",
            "properties": {
                "context": {"type": "string", "description": "What email this is replying to or what situation prompted it"},
                "instructions": {"type": "string", "description": "What the email should say, tone, and any specific details"}
            },
            "required": ["context", "instructions"]
        }
    },
    {
        "name": "revise_email_draft",
        "description": "Ask the Communication Manager to revise the current draft based on user feedback. Pass the full current draft and the requested changes.",
        "input_schema": {
            "type": "object",
            "properties": {
                "current_draft": {"type": "string", "description": "The full current draft JSON"},
                "revision_instructions": {"type": "string", "description": "What the user wants changed"}
            },
            "required": ["current_draft", "revision_instructions"]
        }
    },
    {
        "name": "get_memory_for_manager",
        "description": "Ask the Memory AI for the user preferences relevant to a specific manager before that manager responds. Use this to personalize manager requests.",
        "input_schema": {
            "type": "object",
            "properties": {
                "manager": {"type": "string", "description": "Time Manager | Communication Manager | School Manager | Goal Manager | Notification Manager"}
            },
            "required": ["manager"]
        }
    },
    {
        "name": "save_memory",
        "description": "Save a confirmed user preference to the Memory AI. Use this when the user confirms a pattern or explicitly tells you something about how they like things done.",
        "input_schema": {
            "type": "object",
            "properties": {
                "category": {"type": "string", "description": "work_style | information_style | planning_style | writing_style | notification_style | decision_style | motivation_style | personal"},
                "key": {"type": "string", "description": "Short identifier for this preference"},
                "value": {"type": "string", "description": "The preference or fact to remember"},
                "context": {"type": "string", "description": "When this applies (e.g. 'email summaries', 'study planning', 'general')"}
            },
            "required": ["category", "key", "value"]
        }
    },
    {
        "name": "send_email",
        "description": "Ask the Communication Manager to send an approved email. Only call this after the user has explicitly approved the draft.",
        "input_schema": {
            "type": "object",
            "properties": {
                "to": {"type": "string"},
                "subject": {"type": "string"},
                "body": {"type": "string"}
            },
            "required": ["to", "subject", "body"]
        }
    }
]

class CEOAgent:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.history = []
        self.calendar = CalendarAgent()
        self.email = EmailAgent()
        self.memory = MemoryAgent()

    def chat(self, user_message: str) -> str:
        # Handle memory confirmation if one is pending
        if self.memory.pending_memory:
            lower = user_message.lower().strip()
            if any(w in lower for w in ["yes", "yeah", "correct", "right", "remember that", "yep"]):
                self.memory.confirm_pending(confirmed=True)
                return "Got it — I'll remember that."
            elif any(w in lower for w in ["no", "nope", "don't", "not quite", "wrong"]):
                self.memory.confirm_pending(confirmed=False)
                return "No problem, I won't remember that."
            elif any(w in lower for w in ["sometimes", "situational", "depends", "only when"]):
                self.memory.confirm_pending(confirmed=True, modification=f"{self.memory.pending_memory['value']} (situational: {user_message})")
                return "Got it — I'll remember that as situational."

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
                raw_reply = response.content[0].text

                # Every response goes through Memory AI for personalization
                personalized = self.memory.personalize(
                    response=raw_reply,
                    context=user_message
                )

                self.history.append({"role": "assistant", "content": personalized})

                # Memory AI observes the exchange and may generate a learning question
                learning_question = self.memory.observe(user_message, personalized)
                if learning_question:
                    return f"{personalized}\n\n---\n_{learning_question}_"

                return personalized

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
        elif block.name == "draft_email":
            return self.email.write_draft(
                context=block.input["context"],
                instructions=block.input["instructions"]
            )
        elif block.name == "revise_email_draft":
            return self.email.revise_draft(
                current_draft=block.input["current_draft"],
                revision_instructions=block.input["revision_instructions"]
            )
        elif block.name == "get_memory_for_manager":
            return self.memory.get_for_manager(block.input["manager"])
        elif block.name == "save_memory":
            return self.memory.save_directly(
                category=block.input["category"],
                key=block.input["key"],
                value=block.input["value"],
                context=block.input.get("context", "general")
            )
        elif block.name == "send_email":
            return self.email.send(
                to=block.input["to"],
                subject=block.input["subject"],
                body=block.input["body"]
            )
        return "Unknown tool."
