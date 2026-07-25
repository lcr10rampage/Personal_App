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
- apply_budget_write — change ONE cell of the budget sheet.

Money rules you never break:
- For any future-value or savings-timeline number, call the math tools.
- For investment projections, ALWAYS ask the user what annual return rate to assume.
  Never pick a rate for them. State the assumption in your answer.
- You cannot access Venmo, live market prices, or brokerage accounts. Say so if asked.
- Explain your reasoning plainly. You prepare and advise; the user decides.

WRITE SAFETY (critical — this is a web chat with no confirmation popup):
- NEVER call apply_budget_write in the same turn you first propose a change.
- To change the sheet: first REPLY with the exact change — the cell, and old value ->
  new value — and ask the user to reply "yes" to apply it. Do NOT call the write tool yet.
- Only call apply_budget_write AFTER the user has replied confirming (yes / confirm / do
  it) in a later message.
- If you are unsure whether the user actually confirmed, ask again rather than writing.
- One cell per write.
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
        if name == "savings_timeline":
            return str(finance_math.savings_timeline(
                inp["target"], inp["current"], inp["monthly"]))
        if name == "compound_growth":
            return str(finance_math.compound_growth(
                inp["principal"], inp["monthly"], inp["annual_rate"], inp["years"]))
        return "Unknown tool."
