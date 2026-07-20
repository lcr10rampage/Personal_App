import os
import anthropic
from agents.goals import store

MODEL = "claude-haiku-4-5-20251001"

COACH_PROMPT = """
You are the Goal Manager — the user's accountability partner for long-term goals.

Your job: help the user move forward. Given their current goals and their question, respond with
specific, honest, encouraging guidance. Core question: "Am I moving forward?"

Rules:
- Be specific and reference the actual goals (by title and %). Do not invent goals.
- Point out stalled goals (low % or no recent progress) kindly but honestly.
- Suggest the single most useful next step when helpful.
- Keep it concise and practical. You are supportive, not preachy.
- You cannot see anything except the goals given to you. If the user asks to add or change a goal,
  tell the Orchestrator that's needed rather than pretending you did it.
"""


class GoalAgent:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    # --- reasoning ---
    def ask(self, query: str) -> str:
        goals_text = store.format_for_model()
        message = f"Current goals:\n{goals_text}\n\nUser question: {query}"
        result = self.client.messages.create(
            model=MODEL,
            max_tokens=800,
            system=COACH_PROMPT,
            messages=[{"role": "user", "content": message}],
        )
        return result.content[0].text

    # --- data operations (return short confirmations) ---
    def add(self, title, detail="", category="general", target_date="") -> str:
        g = store.add_goal(title, detail, category, target_date)
        return f"Goal added [{g['id']}]: {g['title']}" + (f" (target {target_date})" if target_date else "")

    def list(self, status=None) -> str:
        return store.format_for_model(status)

    def update_progress(self, goal_id, note="", percent=None) -> str:
        g = store.update_progress(goal_id, note, percent)
        if not g:
            return f"No goal found with id {goal_id}."
        return f"Updated [{g['id']}] {g['title']} → {g['percent']}%" + (f" ({g['status']})" if g['status'] == 'done' else "")

    def complete(self, goal_id) -> str:
        g = store.complete_goal(goal_id)
        return f"Marked [{g['id']}] {g['title']} complete. 🎉" if g else f"No goal found with id {goal_id}."

    def remove(self, goal_id) -> str:
        return "Goal removed." if store.remove_goal(goal_id) else f"No goal found with id {goal_id}."
