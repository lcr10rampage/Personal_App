"""Read-only Canvas (Instructure) LMS client.

SAFETY: This client performs ONLY HTTP GET requests. It can never submit an assignment,
post a comment, message anyone, or change any data in Canvas. The write helpers below exist
only to hard-fail if any code ever tries to call them.

Configure via environment (in backend/.env):
  CANVAS_BASE_URL=https://<your-school>.instructure.com
  CANVAS_ACCESS_TOKEN=<your personal access token>
"""
import os
import json
import urllib.request
import urllib.parse
import urllib.error


def _config():
    base = os.getenv("CANVAS_BASE_URL", "").rstrip("/")
    token = os.getenv("CANVAS_ACCESS_TOKEN", "")
    return base, token


def is_configured() -> bool:
    base, token = _config()
    return bool(base and token)


def _get(path: str, params: dict = None):
    """The ONLY network operation in this module — a read-only GET."""
    base, token = _config()
    if not (base and token):
        return {"_not_configured": True}
    url = f"{base}/api/v1/{path.lstrip('/')}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(
        url,
        method="GET",  # hard-coded: never anything but GET
        headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return {"_error": f"Canvas returned HTTP {e.code}. Check the token/permissions."}
    except (urllib.error.URLError, TimeoutError) as e:
        return {"_error": f"Could not reach Canvas: {e}"}


# ---- read-only endpoints ----
def get_courses():
    return _get("courses", {"enrollment_state": "active", "per_page": 50})


def get_upcoming():
    # Canvas's own "what's coming up" feed.
    return _get("users/self/upcoming_events")


def get_todo():
    return _get("users/self/todo")


def get_course_assignments(course_id):
    return _get(f"courses/{course_id}/assignments", {"per_page": 50, "order_by": "due_at"})


def get_grades():
    # Enrollments include computed_current_score per course.
    return _get("users/self/enrollments", {"state": ["active"], "per_page": 50})


# ---- writes are permanently disabled ----
def submit_assignment(*args, **kwargs):
    raise RuntimeError("DISABLED: Canvas access is read-only. Submitting assignments is not allowed.")


def post_comment(*args, **kwargs):
    raise RuntimeError("DISABLED: Canvas access is read-only. Posting comments is not allowed.")


def send_message(*args, **kwargs):
    raise RuntimeError("DISABLED: Canvas access is read-only. Messaging is not allowed.")
