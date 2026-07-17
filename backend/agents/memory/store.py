import json
import os
from datetime import datetime

MEMORY_FILE = os.path.join(os.path.dirname(__file__), "memories.json")

EMPTY_MEMORY = {
    "work_style": {},
    "information_style": {},
    "planning_style": {},
    "writing_style": {},
    "notification_style": {},
    "decision_style": {},
    "motivation_style": {},
    "personal": {}
}

def load() -> dict:
    if not os.path.exists(MEMORY_FILE):
        save(EMPTY_MEMORY)
        return EMPTY_MEMORY
    with open(MEMORY_FILE, "r") as f:
        return json.load(f)

def save(memories: dict):
    with open(MEMORY_FILE, "w") as f:
        json.dump(memories, f, indent=2)

def get_all() -> dict:
    return load()

def get_for_manager(manager: str) -> dict:
    memories = load()
    mapping = {
        "Time Manager": ["planning_style", "notification_style", "work_style"],
        "Communication Manager": ["writing_style", "information_style", "notification_style"],
        "School Manager": ["work_style", "information_style", "motivation_style"],
        "Goal Manager": ["motivation_style", "planning_style", "information_style"],
        "Notification Manager": ["notification_style", "information_style"],
        "Knowledge Manager": ["information_style"]
    }
    relevant_keys = mapping.get(manager, list(memories.keys()))
    return {k: memories[k] for k in relevant_keys if k in memories}

def write_memory(category: str, key: str, value: str, context: str = "general", confirmed: bool = True):
    memories = load()
    if category not in memories:
        memories[category] = {}
    memories[category][key] = {
        "value": value,
        "context": context,
        "confirmed": confirmed,
        "updated": datetime.now().isoformat()
    }
    save(memories)

def delete_memory(category: str, key: str):
    memories = load()
    if category in memories and key in memories[category]:
        del memories[category][key]
        save(memories)

def format_for_prompt(memories: dict) -> str:
    if not any(memories.values()):
        return "No memories stored yet."
    lines = []
    for category, entries in memories.items():
        if entries:
            lines.append(f"\n{category.replace('_', ' ').title()}:")
            for key, data in entries.items():
                ctx = f" (context: {data['context']})" if data.get("context") != "general" else ""
                lines.append(f"  - {key}: {data['value']}{ctx}")
    return "\n".join(lines)
