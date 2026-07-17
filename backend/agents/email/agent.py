import os
import json
import anthropic
from agents.email.gmail_client import (
    fetch_recent_emails, format_emails_for_model,
    create_draft, send_email
)

SYSTEM_PROMPT = """
You are the Communication Manager — a full email and communication expert.

You own the user's inbox and all email drafting. Your job is to deeply understand
communications and produce expert-quality output.

## Your expertise includes:
- Understanding email context, tone, and intent
- Writing clear, appropriately-toned email replies and new emails
- Revising drafts based on feedback while preserving the user's voice
- Extracting action items, deadlines, and schedule changes from emails
- Identifying which emails need responses and which are informational
- Detecting opportunities buried in email text

## Priority order:
1. College and scholarship matters
2. Important school changes
3. Extracurricular changes
4. Time-sensitive logistics
5. Casual communication

## Rules:
- When writing or revising a draft, always return the COMPLETE email text ready to send.
- Never send an email yourself. Only write the content. The user approves, then it gets sent.
- When analyzing emails, answer the literal request first, then flag anything urgent.
- Be specific — name senders, subjects, deadlines, and required actions.
- Your structured findings go to the Orchestrator. Be analytical, not conversational.
"""

DRAFT_PROMPT = """
You are the Communication Manager writing an email draft.

Write the complete email text based on the context and instructions provided.
Return ONLY a JSON object in this exact format:

{
  "to": "recipient email address",
  "subject": "email subject line",
  "body": "the complete email body text",
  "reasoning": "one sentence explaining the tone and approach you used"
}

Write in a natural, clear voice. Match the tone requested. Do not add extra commentary.
"""

ANALYSIS_PROMPT = """
You are the Communication Manager analyzing emails.

Return a structured JSON finding in this exact format:

{
  "type": "communication_manager_finding",
  "summary": "One sentence summary of what matters right now",
  "action_required": [
    {
      "subject": "email subject",
      "from": "sender",
      "action": "what needs to be done",
      "deadline": "deadline if any",
      "priority": "high | medium | low"
    }
  ],
  "informational": ["brief notes about non-action emails worth knowing"],
  "affects_other_managers": [
    {
      "manager": "Time Manager | School Manager | Goal Manager",
      "reason": "why this email affects them",
      "detail": "specific change or information"
    }
  ],
  "urgency": "immediate | scheduled | digest | silent",
  "requires_approval": false
}

Answer the user's literal request first. Flag urgent items after.
Do not flag low-priority emails as urgent.
"""

class EmailAgent:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.history = []
        self.last_emails = []

    def ask(self, query: str) -> str:
        """Analyze emails and return structured findings."""
        self.last_emails = fetch_recent_emails()
        email_text = format_emails_for_model(self.last_emails)

        message = f"Recent emails:\n\n{email_text}\n\nQuery: {query}"
        self.history.append({"role": "user", "content": message})

        response = self.client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=ANALYSIS_PROMPT,
            messages=self.history
        )
        reply = response.content[0].text
        self.history.append({"role": "assistant", "content": reply})
        return reply

    def write_draft(self, context: str, instructions: str) -> str:
        """Write a new email draft. Returns JSON with to, subject, body, reasoning."""
        if not self.last_emails:
            self.last_emails = fetch_recent_emails()
        email_text = format_emails_for_model(self.last_emails)

        message = (
            f"Email context (recent inbox):\n\n{email_text}\n\n"
            f"Context for this draft: {context}\n\n"
            f"Instructions: {instructions}"
        )

        response = self.client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=DRAFT_PROMPT,
            messages=[{"role": "user", "content": message}]
        )
        return response.content[0].text

    def revise_draft(self, current_draft: str, revision_instructions: str) -> str:
        """Revise an existing draft based on user feedback. Returns updated JSON draft."""
        message = (
            f"Current draft:\n{current_draft}\n\n"
            f"Revision instructions: {revision_instructions}\n\n"
            f"Rewrite the complete email applying these changes. "
            f"Return the same JSON format with updated fields."
        )

        response = self.client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=DRAFT_PROMPT,
            messages=[{"role": "user", "content": message}]
        )
        return response.content[0].text

    def send(self, to: str, subject: str, body: str) -> str:
        """Send an approved email."""
        return send_email(to, subject, body)

    def save_draft(self, to: str, subject: str, body: str) -> str:
        """Save email as a Gmail draft without sending."""
        return create_draft(to, subject, body)
