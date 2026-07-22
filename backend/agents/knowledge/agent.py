import os
import anthropic
from agents.knowledge import store

MODEL = "claude-haiku-4-5-20251001"

FIND_PROMPT = """
You are the Knowledge Manager. Core question: "Where is it?"

You help the user find and connect things they've saved — facts, notes, links, and where they put
things. You are given the saved items that matched their query. Answer their question using ONLY
those items.

Rules:
- Point to the specific saved item(s) — quote the relevant content and note its title/id.
- Connect related items when it helps ("you also saved X, which is related").
- If the matches don't actually answer the question, say what you DO have and what's missing.
- Never invent information that isn't in the provided items.
- Be concise and direct.
"""


class KnowledgeAgent:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    def remember(self, content: str, title: str = "", tags=None, source: str = "") -> str:
        it = store.add_item(content, title, tags, source)
        tagline = f" [tags: {', '.join(it['tags'])}]" if it["tags"] else ""
        return f"Saved to your knowledge base [{it['id']}]: {it['title']}{tagline}"

    def find(self, query: str) -> str:
        matches = store.search(query)
        if not matches:
            return f"I don't have anything saved about \"{query}\". Want me to remember something about it?"
        context = store.format_items(matches)
        result = self.client.messages.create(
            model=MODEL,
            max_tokens=700,
            system=FIND_PROMPT,
            messages=[{"role": "user", "content": f"Saved items that matched:\n{context}\n\nQuestion: {query}"}],
        )
        return result.content[0].text

    def list(self) -> str:
        return store.format_items(store.list_items())

    def remove(self, item_id: str) -> str:
        return "Removed." if store.remove_item(item_id) else f"No knowledge item with id {item_id}."
