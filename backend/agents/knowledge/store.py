"""Local JSON store for the Knowledge Manager — facts, notes, links, and where things are."""
import os
import re
import json
import time
import uuid

KB_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "data", "knowledge.json")
os.makedirs(os.path.dirname(KB_FILE), exist_ok=True)


def _load() -> list:
    if not os.path.isfile(KB_FILE):
        return []
    try:
        with open(KB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []


def _save(items: list) -> None:
    with open(KB_FILE, "w", encoding="utf-8") as f:
        json.dump(items, f, indent=2)


def add_item(content: str, title: str = "", tags=None, source: str = "") -> dict:
    items = _load()
    item = {
        "id": uuid.uuid4().hex[:8],
        "title": title or content[:50],
        "content": content,
        "tags": [t.lower().strip() for t in (tags or []) if t.strip()],
        "source": source,
        "created": time.time(),
        "updated": time.time(),
    }
    items.append(item)
    _save(items)
    return item


def remove_item(item_id: str) -> bool:
    items = _load()
    new = [i for i in items if i["id"] != item_id]
    if len(new) == len(items):
        return False
    _save(new)
    return True


def _tokens(text: str):
    return set(re.findall(r"[a-z0-9]+", (text or "").lower()))


def search(query: str, limit: int = 6) -> list:
    """Keyword scoring over title (x3), tags (x2), content (x1)."""
    items = _load()
    q = _tokens(query)
    if not q:
        return []
    scored = []
    for it in items:
        title_t = _tokens(it.get("title", ""))
        tag_t = _tokens(" ".join(it.get("tags", [])))
        content_t = _tokens(it.get("content", ""))
        score = 3 * len(q & title_t) + 2 * len(q & tag_t) + 1 * len(q & content_t)
        if score > 0:
            scored.append((score, it))
    scored.sort(key=lambda s: s[0], reverse=True)
    return [it for _, it in scored[:limit]]


def list_items() -> list:
    return _load()


def format_items(items: list) -> str:
    if not items:
        return "No knowledge items."
    lines = []
    for it in items:
        tags = f" #{' #'.join(it['tags'])}" if it.get("tags") else ""
        src = f" (source: {it['source']})" if it.get("source") else ""
        lines.append(f"[{it['id']}] {it['title']}{tags}{src}\n    {it['content']}")
    return "\n".join(lines)
