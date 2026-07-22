import os
import anthropic
from agents.email.gmail_client import fetch_recent_emails
from agents.calendar.google_client import fetch_upcoming_events
from agents.school import canvas_client as canvas
from agents.goals import store as goal_store

MODEL = "claude-haiku-4-5-20251001"

NOTIFY_PROMPT = """
You are the Notification Manager. Core question: "Does this matter right now?"

You are given the user's current signals across email, school (assignments + grades), calendar, and
goals. Your job is to CUT THE NOISE and tell them what actually matters — you are the opposite of a
firehose. A high-school student is overwhelmed; your value is deciding what deserves attention.

Produce a short, scannable briefing:
- Start with THE single most important thing right now (or say "nothing urgent" if that's true).
- Then a short "needs attention soon" list.
- Then a brief "can wait / FYI" line if useful.

Rules:
- Be specific: name the sender, assignment, class, deadline, or goal. Never invent items.
- Rank by real urgency + consequence (deadlines, grades slipping, time-sensitive email, RSVPs).
- Group related items; don't repeat.
- Use urgency markers: 🔴 now, 🟡 soon, ⚪ FYI.
- Keep it tight — a student should read it in 20 seconds. Do not pad.
- If a data source is missing (e.g. Canvas not connected), just work with what you have; don't complain.
"""


class NotificationAgent:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    def _gather(self) -> str:
        """Pull raw signals from the other domains (no nested LLM calls)."""
        parts = []

        # Email — subjects/snippets only (keep it cheap)
        try:
            emails = fetch_recent_emails(max_results=8)
            if emails:
                lines = [
                    f"- ({e.get('account', 'Personal')}) {e['from']}: {e['subject']} — {(e.get('snippet') or '')[:120]}"
                    for e in emails
                ]
                parts.append("RECENT EMAIL:\n" + "\n".join(lines))
        except Exception:
            pass

        # Calendar — next 7 days
        try:
            cal = fetch_upcoming_events(days=7)
            if cal and "No upcoming" not in cal:
                parts.append("UPCOMING CALENDAR (7 days):\n" + cal)
        except Exception:
            pass

        # School — upcoming assignments + current grades (read-only Canvas)
        try:
            if canvas.is_configured():
                planner = canvas.get_planner()
                if isinstance(planner, list) and planner:
                    lines = []
                    for it in planner[:10]:
                        p = it.get("plannable", {})
                        title = p.get("title") or p.get("name") or it.get("plannable_type", "item")
                        due = it.get("plannable_date") or p.get("due_at") or ""
                        ctx = it.get("context_name", "")
                        lines.append(f"- {title}" + (f" ({ctx})" if ctx else "") + (f" — due {due}" if due else ""))
                    parts.append("SCHOOL — UPCOMING ASSIGNMENTS:\n" + "\n".join(lines))
                grades = canvas.get_grades()
                if isinstance(grades, list):
                    gl = [
                        f"- course {e.get('course_id')}: {e.get('grades', {}).get('current_score')}%"
                        for e in grades if e.get("grades", {}).get("current_score") is not None
                    ]
                    if gl:
                        parts.append("SCHOOL — CURRENT GRADES:\n" + "\n".join(gl))
        except Exception:
            pass

        # Goals — active only
        try:
            goals = goal_store.format_for_model("active")
            if goals and "No goals" not in goals:
                parts.append("ACTIVE GOALS:\n" + goals)
        except Exception:
            pass

        return "\n\n".join(parts) if parts else "No signals available right now."

    def brief(self, query: str = "") -> str:
        data = self._gather()
        user = f"Current signals:\n\n{data}"
        if query:
            user += f"\n\nThe user specifically asked: {query}"
        result = self.client.messages.create(
            model=MODEL,
            max_tokens=900,
            system=NOTIFY_PROMPT,
            messages=[{"role": "user", "content": user}],
        )
        return result.content[0].text
