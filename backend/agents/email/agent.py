import os
import anthropic
from agents.email.gmail_client import fetch_recent_emails, format_emails_for_model, create_draft

SYSTEM_PROMPT = """
You are the Communication Manager — a specialist responsible for the user's email inbox.

Your job:
- Summarize what matters in recent emails
- Extract action items and deadlines
- Detect schedule changes, important announcements, or opportunities
- Draft replies in a clear, natural tone
- Tell the user what needs a response and what is just informational

Rules:
- Always answer the user's literal request first. If they ask for the most recent email, give them that email — do not reorder by importance.
- After answering the literal request, check if any other email is significantly more urgent or requires action. If so, add a brief note: "Also flagging: [subject] from [sender] — [one sentence why it matters]."
- Only flag something if it genuinely warrants attention. Do not flag every other email.
- Never send an email. Only create drafts. The user must approve before anything is sent.
- Be concise. The user should feel less overwhelmed after reading your summary, not more.
- When asked to draft a reply, always present it for approval before doing anything with it.
"""

class EmailAgent:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.history = []
        self.last_emails = []

    def ask(self, query: str) -> str:
        self.last_emails = fetch_recent_emails()
        email_text = format_emails_for_model(self.last_emails)

        message = f"Recent emails:\n\n{email_text}\n\nQuery: {query}"
        self.history.append({"role": "user", "content": message})

        response = self.client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=self.history
        )
        reply = response.content[0].text
        self.history.append({"role": "assistant", "content": reply})
        return reply

    def draft_reply(self, to: str, subject: str, body: str) -> str:
        return create_draft(to, subject, body)
