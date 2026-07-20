"""Local JSON store for the Goal Manager. Goals persist across restarts."""
import os
import json
import time
import uuid

GOALS_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "data", "goals.json")
os.makedirs(os.path.dirname(GOALS_FILE), exist_ok=True)


def _load() -> list:
    if not os.path.isfile(GOALS_FILE):
        return []
    try:
        with open(GOALS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []


def _save(goals: list) -> None:
    with open(GOALS_FILE, "w", encoding="utf-8") as f:
        json.dump(goals, f, indent=2)


def add_goal(title: str, detail: str = "", category: str = "general", target_date: str = "") -> dict:
    goals = _load()
    g = {
        "id": uuid.uuid4().hex[:8],
        "title": title,
        "detail": detail,
        "category": category,
        "target_date": target_date,
        "percent": 0,
        "status": "active",
        "created": time.time(),
        "updated": time.time(),
        "progress_log": [],
    }
    goals.append(g)
    _save(goals)
    return g


def _find(goals, gid):
    return next((g for g in goals if g["id"] == gid), None)


def update_progress(gid: str, note: str = "", percent: int = None) -> dict:
    goals = _load()
    g = _find(goals, gid)
    if not g:
        return None
    if percent is not None:
        g["percent"] = max(0, min(100, int(percent)))
    g["progress_log"].append({"ts": time.time(), "note": note, "percent": g["percent"]})
    g["updated"] = time.time()
    if g["percent"] >= 100:
        g["status"] = "done"
    _save(goals)
    return g


def complete_goal(gid: str) -> dict:
    goals = _load()
    g = _find(goals, gid)
    if not g:
        return None
    g["status"] = "done"
    g["percent"] = 100
    g["updated"] = time.time()
    _save(goals)
    return g


def remove_goal(gid: str) -> bool:
    goals = _load()
    new = [g for g in goals if g["id"] != gid]
    if len(new) == len(goals):
        return False
    _save(new)
    return True


def list_goals(status: str = None) -> list:
    goals = _load()
    if status:
        goals = [g for g in goals if g["status"] == status]
    return goals


def format_for_model(status: str = None) -> str:
    goals = list_goals(status)
    if not goals:
        return "No goals recorded yet."
    lines = []
    for g in goals:
        target = f", target {g['target_date']}" if g.get("target_date") else ""
        last = g["progress_log"][-1]["note"] if g.get("progress_log") else ""
        lines.append(
            f"[{g['id']}] {g['title']} — {g['percent']}% ({g['status']}){target}"
            + (f"\n    category: {g['category']}" if g.get("category") else "")
            + (f"\n    detail: {g['detail']}" if g.get("detail") else "")
            + (f"\n    latest: {last}" if last else "")
        )
    return "\n".join(lines)
