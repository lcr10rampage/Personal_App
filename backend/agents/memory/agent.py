import os
import json
import anthropic
from agents.memory import store

PERSONALIZE_PROMPT = """
You are the Memory AI — you know this user deeply.

Your job right now is to take a response that was assembled by the Orchestrator and
personalize it based on everything you know about the user before it reaches them.

You adjust:
- Tone (calm, direct, encouraging, practical — based on what the user prefers)
- Length (shorter or more detailed — based on their information style)
- Format (bullets vs paragraphs — based on their preference)
- Framing (recommendation-first vs options — based on their decision style)
- Motivation (accountability, encouragement, scripture, streaks — based on their motivation style)

Rules:
- Keep all the facts and content exactly correct. Only change how it is communicated.
- If the user prefers short responses, trim without losing important information.
- If the user prefers direct language, remove softening phrases.
- If faith-based encouragement is enabled, you may add a relevant note at the end — but only occasionally, not every response.
- If you have no relevant memories yet, return the response unchanged.
- Return only the final personalized response text. No commentary, no explanation.
"""

OBSERVE_PROMPT = """
You are the Memory AI — you watch every interaction and look for patterns about how the user works.

Review this exchange and determine if there is a pattern worth remembering.

Look for:
- How the user phrased their request (direct, casual, detailed, terse)
- Whether they pushed back on the response (too long, too short, wrong tone)
- Whether they asked for changes (more formal, simpler, different format)
- Whether they approved something quickly (suggests it matched their preference)
- Whether they expressed frustration or satisfaction

Memory categories to consider:
- work_style: how they approach tasks and work sessions
- information_style: how they like information presented
- planning_style: how they prefer to plan and schedule
- writing_style: their email and communication voice
- notification_style: how often and how they want to be interrupted
- decision_style: how they make choices
- motivation_style: what motivates or discourages them
- personal: anything personal they shared about themselves

Rules:
- Only flag a pattern if it appears clearly in this exchange. Do not guess.
- Be specific. Bad: "user likes short responses." Good: "user asked to shorten the email summary and said 'just the key points.'"
- If nothing is worth learning, return null.
- If something is worth learning, return a JSON object:

{
  "category": "information_style",
  "key": "response_length",
  "value": "prefers bullet-point summaries, not paragraphs — said 'just the key points'",
  "context": "email summaries",
  "question": "I noticed you prefer bullet points over paragraphs for summaries. Should I remember that?"
}
"""

RECALL_PROMPT = """
You are the Memory AI. A manager is requesting the user preferences relevant to their domain.

Return a clean summary of the relevant memories in plain language.
Be specific. These memories will be used by the manager to personalize their work.
"""

class MemoryAgent:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.pending_memory = None

    def personalize(self, response: str, context: str = "") -> str:
        memories = store.get_all()
        memory_text = store.format_for_prompt(memories)

        if not any(memories.values()):
            return response

        message = (
            f"What I know about the user:\n{memory_text}\n\n"
            f"Context of this interaction: {context}\n\n"
            f"Response to personalize:\n{response}"
        )

        result = self.client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=PERSONALIZE_PROMPT,
            messages=[{"role": "user", "content": message}]
        )
        return result.content[0].text

    def observe(self, user_message: str, system_response: str) -> str | None:
        message = (
            f"User said:\n{user_message}\n\n"
            f"System responded:\n{system_response}"
        )

        result = self.client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=512,
            system=OBSERVE_PROMPT,
            messages=[{"role": "user", "content": message}]
        )

        text = result.content[0].text.strip()
        if text.lower() == "null" or not text.startswith("{"):
            return None

        try:
            data = json.loads(text)
            self.pending_memory = data
            return data.get("question")
        except json.JSONDecodeError:
            return None

    def confirm_pending(self, confirmed: bool, modification: str = None):
        if not self.pending_memory:
            return
        if confirmed:
            value = modification if modification else self.pending_memory["value"]
            store.write_memory(
                category=self.pending_memory["category"],
                key=self.pending_memory["key"],
                value=value,
                context=self.pending_memory.get("context", "general"),
                confirmed=True
            )
        self.pending_memory = None

    def get_for_manager(self, manager: str) -> str:
        memories = store.get_for_manager(manager)
        memory_text = store.format_for_prompt(memories)

        if not any(memories.values()):
            return f"No memories stored yet for {manager}."

        result = self.client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=512,
            system=RECALL_PROMPT,
            messages=[{"role": "user", "content": f"Manager: {manager}\n\nMemories:\n{memory_text}"}]
        )
        return result.content[0].text

    def save_directly(self, category: str, key: str, value: str, context: str = "general"):
        store.write_memory(category, key, value, context, confirmed=True)
        return f"Memory saved: [{category}] {key} = {value}"

    def recall_all(self) -> str:
        memories = store.get_all()
        return store.format_for_prompt(memories)
