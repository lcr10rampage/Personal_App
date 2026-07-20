"""Durable, local chat history — multiple named conversations per team.

Each conversation is one JSON file under data/conversations/. Messages are stored as
plain text turns ({role, content, ts}); that is both what the UI shows and what gets
replayed to the agent as prior context.
"""
import os
import re
import json
import time
import uuid

DATA_DIR = os.path.join(os.path.dirname(__file__), "data", "conversations")
os.makedirs(DATA_DIR, exist_ok=True)

_ID_RE = re.compile(r"^[a-f0-9]{6,32}$")


def _valid(cid: str) -> bool:
    return bool(cid) and bool(_ID_RE.match(cid))


def _path(cid: str) -> str:
    return os.path.join(DATA_DIR, f"{cid}.json")


def _title_from(text: str) -> str:
    t = " ".join((text or "").strip().split())
    if not t:
        return "New conversation"
    return t[:40] + "…" if len(t) > 40 else t


def _save(c: dict) -> None:
    with open(_path(c["id"]), "w", encoding="utf-8") as f:
        json.dump(c, f, indent=2)


def get_conversation(cid: str):
    if not _valid(cid) or not os.path.isfile(_path(cid)):
        return None
    with open(_path(cid), "r", encoding="utf-8") as f:
        return json.load(f)


def list_conversations(team: str):
    out = []
    for fn in os.listdir(DATA_DIR):
        if not fn.endswith(".json"):
            continue
        try:
            with open(os.path.join(DATA_DIR, fn), "r", encoding="utf-8") as f:
                c = json.load(f)
        except (json.JSONDecodeError, OSError):
            continue
        if c.get("team") == team:
            out.append({
                "id": c["id"],
                "title": c.get("title") or "New conversation",
                "updated": c.get("updated", 0),
                "message_count": len(c.get("messages", [])),
            })
    out.sort(key=lambda c: c["updated"], reverse=True)
    return out


def create_conversation(team: str, title: str = None) -> dict:
    now = time.time()
    c = {
        "id": uuid.uuid4().hex[:12],
        "team": team,
        "title": title or "New conversation",
        "created": now,
        "updated": now,
        "messages": [],
    }
    _save(c)
    return c


def append_message(cid: str, role: str, content: str):
    c = get_conversation(cid)
    if not c:
        return None
    c["messages"].append({"role": role, "content": content, "ts": time.time()})
    # Auto-title from the first user message.
    if role == "user" and (not c.get("title") or c["title"] == "New conversation"):
        c["title"] = _title_from(content)
    c["updated"] = time.time()
    _save(c)
    return c


def rename_conversation(cid: str, title: str):
    c = get_conversation(cid)
    if not c:
        return None
    c["title"] = (title or "").strip() or c["title"]
    c["updated"] = time.time()
    _save(c)
    return c


def delete_conversation(cid: str) -> bool:
    if _valid(cid) and os.path.isfile(_path(cid)):
        os.remove(_path(cid))
        return True
    return False


def history_for_model(c: dict):
    """Prior turns as text-only messages the agent can replay."""
    return [{"role": m["role"], "content": m["content"]} for m in c.get("messages", [])]
