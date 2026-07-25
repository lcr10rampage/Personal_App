"""Finance team — budget, saving goals, and investment planning.

Reuses the standalone finance-agent's pure math + Google Sheets logic (from
FINANCE_AGENT_DIR, default ~/finance-agent) so the dashboard and the terminal app
share one codebase and one Google Sheets token. Runs on the Claude subscription via
the shared sdk_backend, like the other heavy teams.

WRITE SAFETY: the terminal app gates every write with an interactive y/n prompt. A web
request has no terminal, and sdk_backend runs with bypassPermissions, so that hard gate
cannot exist here. Instead the system prompt enforces a two-turn confirmation: the agent
must propose the exact change and wait for the user to reply 'yes' before it calls the
write tool. This is a softer, prompt-level guard — documented as such.
"""
import os
import importlib.util
import anthropic
from teams.sdk_backend import use_sdk, run_agentic, format_prompt

FINANCE_AGENT_DIR = os.getenv("FINANCE_AGENT_DIR", os.path.expanduser("~/finance-agent"))
# The budget occupies A1:L40 on the first tab (header row 5, categories A, amounts B,
# balance C, months D+). Override with FINANCE_BUDGET_RANGE if the layout changes.
BUDGET_RANGE = os.getenv("FINANCE_BUDGET_RANGE", "A1:L40")


def _load(mod_name: str, filename: str):
    """Load a finance-agent module by file path — avoids polluting sys.path with the
    finance-agent dir (which has generically-named modules like agent.py/chat.py)."""
    path = os.path.join(FINANCE_AGENT_DIR, filename)
    spec = importlib.util.spec_from_file_location(mod_name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


finance_math = _load("finance_math", "finance_math.py")
finance_sheets = _load("finance_sheets", "sheets.py")


SYSTEM_PROMPT = """You are a careful personal finance assistant in a web dashboard. You
help with a budget kept in a Google Sheet, saving toward goals, and investment planning.

Your tools:
- read_budget — read the user's budget sheet.
- savings_timeline / compound_growth — do the math. ALWAYS use these for any
  future-value or savings number. NEVER do the arithmetic yourself.
- apply_budget_write — change one cell of the budget sheet.
- write_range — write a grid of values at once, starting at an anchor cell (e.g.
  'August!A1'). Use for a column/block of values.
- write_cells — change several scattered cells in one action.
- append_rows — add new rows (e.g. new budget categories) to a tab.
- add_sheet — create a new blank tab/page; then fill it with write_range/append_rows
  using 'TabTitle!A1' ranges.

Money rules you never break:
- For any future-value or savings-timeline number, call the math tools.
- For investment projections, ALWAYS ask the user what annual return rate to assume.
  Never pick a rate for them. State the assumption in your answer.
- You cannot access Venmo, live market prices, or brokerage accounts. Say so if asked.
- Explain your reasoning plainly. You prepare and advise; the user decides.

WRITE SAFETY (critical — this is a web chat with no confirmation popup). This applies
to EVERY tool that changes the sheet: apply_budget_write, write_range, write_cells,
append_rows, and add_sheet.
- NEVER call any of those tools in the same turn you first propose the change.
- First REPLY describing the exact change in full — the cell(s) and old -> new values,
  or the grid/rows you'll write, or the tab you'll create — and ask the user to reply
  "yes" to apply it. Do NOT call the write tool yet.
- Only call the tool AFTER the user has replied confirming (yes / confirm / do it) in a
  later message. For a bulk change, confirm the whole change, then apply it in one call.
- If you are unsure whether the user actually confirmed, ask again rather than writing.
"""

TOOLS = [
    {
        "name": "read_budget",
        "description": "Read the user's budget sheet and return its rows.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "apply_budget_write",
        "description": ("Write one value to one budget cell in A1 notation (e.g. cell "
                        "'C5'). Only call this AFTER the user has explicitly confirmed "
                        "the change in a prior message."),
        "input_schema": {
            "type": "object",
            "properties": {
                "cell": {"type": "string", "description": "A1 cell reference, e.g. 'C12'"},
                "value": {"type": "string", "description": "The new cell value"},
            },
            "required": ["cell", "value"],
        },
    },
    {
        "name": "write_range",
        "description": ("Write a 2D grid of values at once, starting at an anchor cell. "
                        "'anchor' is A1 notation and may include a tab name (e.g. "
                        "'August!A1'). 'values' is a list of rows, each a list of strings. "
                        "Only call AFTER the user confirmed the change."),
        "input_schema": {
            "type": "object",
            "properties": {
                "anchor": {"type": "string", "description": "Anchor cell, e.g. 'August!A1'"},
                "values": {"type": "array", "items": {"type": "array", "items": {"type": "string"}}},
            },
            "required": ["anchor", "values"],
        },
    },
    {
        "name": "write_cells",
        "description": ("Write several scattered cells in one action. 'updates' is a list "
                        "of {\"cell\": \"C5\", \"value\": \"650\"}. Only call AFTER the "
                        "user confirmed the change."),
        "input_schema": {
            "type": "object",
            "properties": {
                "updates": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "cell": {"type": "string"},
                            "value": {"type": "string"},
                        },
                        "required": ["cell", "value"],
                    },
                },
            },
            "required": ["updates"],
        },
    },
    {
        "name": "append_rows",
        "description": ("Append new rows after existing data on a tab (e.g. add new budget "
                        "category rows). 'values' is a list of rows; 'sheet_title' is "
                        "optional (defaults to the first tab). Only call AFTER the user "
                        "confirmed the change."),
        "input_schema": {
            "type": "object",
            "properties": {
                "values": {"type": "array", "items": {"type": "array", "items": {"type": "string"}}},
                "sheet_title": {"type": "string"},
            },
            "required": ["values"],
        },
    },
    {
        "name": "add_sheet",
        "description": ("Create a new blank tab/page. 'title' is the tab name. Then fill it "
                        "with write_range/append_rows using 'Title!A1' ranges. Only call "
                        "AFTER the user confirmed."),
        "input_schema": {
            "type": "object",
            "properties": {"title": {"type": "string", "description": "New tab name"}},
            "required": ["title"],
        },
    },
    {
        "name": "savings_timeline",
        "description": "Months to reach a savings target given a monthly contribution.",
        "input_schema": {
            "type": "object",
            "properties": {
                "target": {"type": "number"},
                "current": {"type": "number"},
                "monthly": {"type": "number"},
            },
            "required": ["target", "current", "monthly"],
        },
    },
    {
        "name": "compound_growth",
        "description": ("Project investment value with monthly compounding. annual_rate "
                        "is a decimal (0.07 = 7%). The rate MUST come from the user."),
        "input_schema": {
            "type": "object",
            "properties": {
                "principal": {"type": "number"},
                "monthly": {"type": "number"},
                "annual_rate": {"type": "number"},
                "years": {"type": "number"},
            },
            "required": ["principal", "monthly", "annual_rate", "years"],
        },
    },
]


class FinanceTeam:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    def chat(self, user_message: str, history=None) -> str:
        if use_sdk():
            try:
                prompt = format_prompt(history, user_message)
                return run_agentic(SYSTEM_PROMPT, TOOLS, self._dispatch, prompt)
            except Exception as e:
                print(f"[finance] SDK backend failed ({type(e).__name__}: {e}); falling back to API")
        return self._chat_api(user_message, history)

    def _chat_api(self, user_message: str, history=None) -> str:
        messages = [dict(m) for m in (history or [])]
        messages.append({"role": "user", "content": user_message})
        while True:
            response = self.client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=2048,
                system=SYSTEM_PROMPT,
                tools=TOOLS,
                messages=messages,
            )
            if response.stop_reason == "end_turn":
                return response.content[0].text
            if response.stop_reason == "tool_use":
                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": self._dispatch(block.name, block.input),
                        })
                messages.append({"role": "assistant", "content": response.content})
                messages.append({"role": "user", "content": tool_results})

    def _dispatch(self, name: str, inp: dict) -> str:
        if name == "read_budget":
            rows = finance_sheets.read_range(BUDGET_RANGE)
            return "\n".join("\t".join(r) for r in rows) or "(empty)"
        if name == "apply_budget_write":
            finance_sheets.write_cell(inp["cell"], inp["value"])
            return f"Wrote '{inp['value']}' to {inp['cell']}."
        if name == "write_range":
            finance_sheets.write_range(inp["anchor"], inp["values"])
            n = sum(len(r) for r in inp["values"])
            return f"Wrote {n} values starting at {inp['anchor']}."
        if name == "write_cells":
            finance_sheets.write_cells(inp["updates"])
            return f"Wrote {len(inp['updates'])} cells: " + ", ".join(u["cell"] for u in inp["updates"]) + "."
        if name == "append_rows":
            finance_sheets.append_rows(inp["values"], inp.get("sheet_title") or None)
            return f"Appended {len(inp['values'])} row(s) to {inp.get('sheet_title') or 'the budget tab'}."
        if name == "add_sheet":
            finance_sheets.add_sheet(inp["title"])
            return f"Created new tab '{inp['title']}'."
        if name == "savings_timeline":
            return str(finance_math.savings_timeline(
                inp["target"], inp["current"], inp["monthly"]))
        if name == "compound_growth":
            return str(finance_math.compound_growth(
                inp["principal"], inp["monthly"], inp["annual_rate"], inp["years"]))
        return "Unknown tool."
