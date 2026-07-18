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

RECONCILE_PROMPT = """
You are the Memory AI deciding how to store a newly confirmed memory.

You are given the EXISTING memories in one category and a NEW memory. Decide:
- "replace": the new memory is about the SAME underlying preference/context as an existing
  entry and supersedes it (e.g. the user used to prefer studying in the morning, now prefers
  after school). Replace that specific existing entry.
- "add": the new memory describes a DIFFERENT preference or a different context. Keep the
  existing entries and add this as new.

Rules:
- Two memories only "relate" if they'd contradict or duplicate each other in the same context.
  Different contexts (e.g. "short emails" vs "detailed project plans") are ADD, not replace.
- Prefer "add" unless there is a clear same-context supersede.

Return ONLY JSON:
{"action": "replace", "replace_key": "<existing key to remove>"}
or
{"action": "add"}
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
            self._reconcile_and_save(
                category=self.pending_memory["category"],
                key=self.pending_memory["key"],
                value=value,
                context=self.pending_memory.get("context", "general")
            )
        self.pending_memory = None

    def _reconcile_and_save(self, category: str, key: str, value: str, context: str = "general"):
        """Decide whether a new confirmed memory replaces a related existing one or is added.

        Implements the architecture rule: a new memory about the same preference/context
        replaces the old one; a memory about a different area is added.
        """
        existing = store.get_all().get(category, {})

        # Nothing to reconcile against — or exact key already present (a direct update).
        if not existing or key in existing:
            store.write_memory(category, key, value, context, confirmed=True)
            return

        existing_text = "\n".join(
            f"- {k}: {d['value']} (context: {d.get('context', 'general')})"
            for k, d in existing.items()
        )
        message = (
            f"Category: {category}\n\n"
            f"Existing memories:\n{existing_text}\n\n"
            f"New memory:\n- {key}: {value} (context: {context})"
        )

        try:
            result = self.client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=128,
                system=RECONCILE_PROMPT,
                messages=[{"role": "user", "content": message}]
            )
            text = result.content[0].text.strip()
            decision = json.loads(text[text.index("{"):text.rindex("}") + 1])
            if decision.get("action") == "replace":
                old_key = decision.get("replace_key")
                if old_key and old_key in existing:
                    store.delete_memory(category, old_key)
        except (json.JSONDecodeError, ValueError, IndexError, KeyError):
            pass  # fall through to a plain add — never lose the new memory

        store.write_memory(category, key, value, context, confirmed=True)

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
        self._reconcile_and_save(category, key, value, context)
        return f"Memory saved: [{category}] {key} = {value}"

    def recall_all(self) -> str:
        memories = store.get_all()
        return store.format_for_prompt(memories)

    def recall_for_user(self) -> str:
        """A friendly summary of everything remembered, for when the user asks."""
        memories = store.get_all()
        if not any(memories.values()):
            return "I haven't learned anything about your preferences yet."
        return store.format_for_prompt(memories)

    def forget(self, category: str, key: str) -> str:
        """Let the user remove a memory they don't want kept."""
        existing = store.get_all().get(category, {})
        if key not in existing:
            return f"No memory found for [{category}] {key}."
        store.delete_memory(category, key)
        return f"Forgotten: [{category}] {key}."
