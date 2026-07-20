import os
import anthropic
from agents.school import canvas_client as canvas

MODEL = "claude-haiku-4-5-20251001"

SCHOOL_PROMPT = """
You are the School Manager — the user's academic assistant. Core question:
"What do I need to know about school?"

You work from READ-ONLY Canvas data (courses, assignments, due dates, grades). You can never
submit assignments, post comments, or message teachers — you only read and advise.

Rules:
- Answer the user's literal question first, using the Canvas data provided.
- Surface what's due soon and what looks at risk (missing, low grade, close deadline).
- Be specific: name the course, assignment, due date, and points where available.
- Never claim to have submitted, posted, or turned in anything — you cannot.
- If Canvas isn't connected, say so and explain how to connect it, then help with whatever the
  user tells you manually.
"""


def _fmt_courses(data):
    if isinstance(data, dict) and data.get("_not_configured"):
        return None
    if isinstance(data, dict) and data.get("_error"):
        return f"(Canvas error: {data['_error']})"
    if not data:
        return "No active courses found."
    return "\n".join(f"- {c.get('name','(unnamed)')} [id {c.get('id')}]" for c in data if isinstance(c, dict))


def _fmt_planner(data):
    if isinstance(data, dict) and (data.get("_not_configured") or data.get("_error")):
        return None if data.get("_not_configured") else f"(Canvas error: {data['_error']})"
    if not data:
        return "Nothing due upcoming on Canvas."
    lines = []
    for it in data:
        if not isinstance(it, dict):
            continue
        p = it.get("plannable", {})
        title = p.get("title") or p.get("name") or it.get("plannable_type", "item")
        due = it.get("plannable_date") or p.get("due_at") or ""
        ctx = it.get("context_name", "")
        done = "✓ " if (it.get("planner_override") or {}).get("marked_complete") else ""
        lines.append(f"- {done}{title}" + (f" — {ctx}" if ctx else "") + (f" — due {due}" if due else ""))
    return "\n".join(lines) or "Nothing due upcoming on Canvas."


def _fmt_grades(data, course_names=None):
    if isinstance(data, dict) and (data.get("_not_configured") or data.get("_error")):
        return None if data.get("_not_configured") else f"(Canvas error: {data['_error']})"
    if not data:
        return "No grades available."
    lines = []
    for e in data:
        if not isinstance(e, dict):
            continue
        score = e.get("grades", {}).get("current_score")
        cid = e.get("course_id")
        if score is not None:
            name = (course_names or {}).get(cid, f"Course {cid}")
            lines.append(f"- {name}: {score}%")
    return "\n".join(lines) or "No current scores posted."


class SchoolAgent:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    def _course_names(self):
        raw = canvas.get_courses()
        if not isinstance(raw, list):
            return {}
        return {c.get("id"): c.get("name", f"Course {c.get('id')}") for c in raw if isinstance(c, dict)}

    def _snapshot(self) -> str:
        if not canvas.is_configured():
            return ("_not_connected_")
        courses = _fmt_courses(canvas.get_courses())
        assignments = _fmt_planner(canvas.get_planner())
        grades = _fmt_grades(canvas.get_grades(), self._course_names())
        return (
            f"COURSES:\n{courses or '—'}\n\n"
            f"UPCOMING ASSIGNMENTS (due soon):\n{assignments or '—'}\n\n"
            f"GRADES:\n{grades or '—'}"
        )

    def ask(self, query: str) -> str:
        snapshot = self._snapshot()
        if snapshot == "_not_connected_":
            data_block = ("Canvas is NOT connected. Tell the user to set CANVAS_BASE_URL and "
                          "CANVAS_ACCESS_TOKEN (a read-only personal access token) in the backend .env, "
                          "then help them with whatever school info they provide manually.")
        else:
            data_block = f"Read-only Canvas snapshot:\n\n{snapshot}"
        message = f"{data_block}\n\nUser question: {query}"
        result = self.client.messages.create(
            model=MODEL,
            max_tokens=900,
            system=SCHOOL_PROMPT,
            messages=[{"role": "user", "content": message}],
        )
        return result.content[0].text

    def assignments(self) -> str:
        if not canvas.is_configured():
            return "Canvas isn't connected yet (set CANVAS_BASE_URL and CANVAS_ACCESS_TOKEN)."
        return _fmt_planner(canvas.get_planner()) or "Nothing upcoming."

    def courses(self) -> str:
        if not canvas.is_configured():
            return "Canvas isn't connected yet (set CANVAS_BASE_URL and CANVAS_ACCESS_TOKEN)."
        return _fmt_courses(canvas.get_courses()) or "No courses found."

    def grades(self) -> str:
        if not canvas.is_configured():
            return "Canvas isn't connected yet (set CANVAS_BASE_URL and CANVAS_ACCESS_TOKEN)."
        return _fmt_grades(canvas.get_grades(), self._course_names()) or "No grades found."
