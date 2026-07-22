"""Shared hand-off inbox between the Life Manager (Personal App) and the Project & Hobby team.

When a goal/research item in the Life Manager relates to a physical project or hobby, it drops a
"seed" here. The Project & Hobby team reads these and offers to turn them into a workspace.
Both teams run in the same backend, so this is just a shared local JSON file.
"""
import os
import json
import time
import uuid

INBOX_FILE = os.path.join(os.path.dirname(__file__), "data", "project_inbox.json")
os.makedirs(os.path.dirname(INBOX_FILE), exist_ok=True)


def _load() -> list:
    if not os.path.isfile(INBOX_FILE):
        return []
    try:
        with open(INBOX_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []


def _save(seeds: list) -> None:
    with open(INBOX_FILE, "w", encoding="utf-8") as f:
        json.dump(seeds, f, indent=2)


def add_seed(title: str, detail: str = "", source: str = "Life Manager", target_date: str = "") -> dict:
    seeds = _load()
    seed = {
        "id": uuid.uuid4().hex[:8],
        "title": title,
        "detail": detail,
        "source": source,
        "target_date": target_date,
        "created": time.time(),
    }
    seeds.append(seed)
    _save(seeds)
    return seed


def list_seeds() -> list:
    return _load()


def remove_seed(seed_id: str) -> bool:
    seeds = _load()
    new = [s for s in seeds if s["id"] != seed_id]
    if len(new) == len(seeds):
        return False
    _save(new)
    return True


def format_seeds() -> str:
    seeds = _load()
    if not seeds:
        return "No incoming project/hobby ideas from the Life Manager."
    lines = []
    for s in seeds:
        target = f" (target {s['target_date']})" if s.get("target_date") else ""
        lines.append(f"[{s['id']}] {s['title']}{target} — from {s['source']}"
                     + (f"\n    {s['detail']}" if s.get("detail") else ""))
    return "\n".join(lines)
