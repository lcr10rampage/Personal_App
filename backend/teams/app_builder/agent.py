import os
import anthropic
from teams.sdk_backend import use_sdk, run_agentic, format_prompt

# Where the App-Building Team system lives (the App-System-Guide repo).
# Override with APP_SYSTEM_GUIDE_DIR if it lives elsewhere.
GUIDE_DIR = os.getenv("APP_SYSTEM_GUIDE_DIR", os.path.expanduser("~/App-System-Guide"))

SYSTEM_PROMPT = """
You are the App Builder — a disciplined AI app-building TEAM, not a single coder.

You operate the system documented in the App-System-Guide repository. That repository
defines four roles and a strict workflow. You take on whichever role the current stage
requires, and you never let a role approve its own work.

The four roles:
- App Architect — designs the complete app experience (screens, flows, states) with mock data.
- Functionality Engineer — makes the approved design actually work (real data, backend, auth).
- Quality Manager — judges every deliverable against the repo's criteria, controls the stage, is the only approver.
- Application Tester — independently verifies behavior; never fixes bugs.

The workflow (only the Manager advances the stage):
PROJECT_BRIEF -> DESIGNING -> DESIGN_REVIEW -> FUNCTIONALITY_BUILD ->
IMPLEMENTATION_REVIEW -> TESTING -> FIXING -> RETESTING -> FINAL_REVIEW -> RELEASE_APPROVED

HOW YOU WORK:
- Your knowledge base is the App-System-Guide repo. Use the read_guide_file tool to load
  the exact file you need before acting: START_HERE.md, TEAM_WORKFLOW.md, agents/<role>.md,
  criteria/<...>.md, templates/<...>.md, workflows/<...>.md, and the foundation in
  app-build-set/ (app-system-guide.md = the UI/UX + build law; EngineeringMemory.md = proven
  patterns and known mistakes).
- Do NOT guess at the rules — read the relevant role/criteria file first, then act as that role.
- The foundation files are large; read them in targeted pieces when a design or build question
  needs them, not all at once.
- Always tell the user which role you're currently acting as and which workflow stage you're in.
- Enforce the core rules: no role approves its own work; only the Manager approves and moves the
  stage; the Architect never builds production backend; the Tester never fixes bugs; every
  completed step needs evidence; nothing enters memory without Manager approval.

At the start of a new conversation, if the user hasn't said what they want, offer to start a new
project (PROJECT_BRIEF) and read START_HERE.md + TEAM_WORKFLOW.md to ground yourself.
"""

TOOLS = [
    {
        "name": "read_guide_file",
        "description": "Read a file from the App-System-Guide repository (the team's knowledge base). Pass a path relative to the repo root, e.g. 'START_HERE.md', 'agents/architect.md', 'criteria/design-review-criteria.md', or 'app-build-set/app-system-guide.md'.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path relative to the App-System-Guide repo root"},
                "max_chars": {"type": "integer", "description": "Optional cap on characters returned (default 12000). Use for large foundation files."}
            },
            "required": ["path"]
        }
    },
    {
        "name": "list_guide_files",
        "description": "List the files available in the App-System-Guide repository so you know what you can read.",
        "input_schema": {"type": "object", "properties": {}}
    }
]


def _safe_path(rel_path: str) -> str:
    # Prevent escaping the guide directory.
    full = os.path.normpath(os.path.join(GUIDE_DIR, rel_path))
    if not full.startswith(os.path.normpath(GUIDE_DIR)):
        return ""
    return full


class AppBuilderTeam:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    def chat(self, user_message: str, history=None) -> str:
        if use_sdk():
            try:
                prompt = format_prompt(history, user_message)
                return run_agentic(SYSTEM_PROMPT, TOOLS, self._dispatch, prompt)
            except Exception as e:
                # A subscription hiccup must not hard-break the team — fall back to the
                # API path (which needs ANTHROPIC_API_KEY to actually succeed).
                print(f"[app_builder] SDK backend failed ({type(e).__name__}: {e}); falling back to API")
        return self._chat_api(user_message, history)

    def _chat_api(self, user_message: str, history=None) -> str:
        # Prior turns come from the persisted conversation (text-only).
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
                        result = self._handle_tool(block)
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result,
                        })
                messages.append({"role": "assistant", "content": response.content})
                messages.append({"role": "user", "content": tool_results})

    def _handle_tool(self, block) -> str:
        return self._dispatch(block.name, block.input)

    def _dispatch(self, name: str, inp: dict) -> str:
        if name == "list_guide_files":
            return self._list_files()
        if name == "read_guide_file":
            return self._read_file(inp["path"], inp.get("max_chars", 12000))
        return "Unknown tool."

    def _list_files(self) -> str:
        if not os.path.isdir(GUIDE_DIR):
            return f"App-System-Guide not found at {GUIDE_DIR}."
        paths = []
        for root, _dirs, files in os.walk(GUIDE_DIR):
            if "/.git" in root:
                continue
            for f in files:
                if f.endswith(".md"):
                    rel = os.path.relpath(os.path.join(root, f), GUIDE_DIR)
                    paths.append(rel)
        return "\n".join(sorted(paths))

    def _read_file(self, rel_path: str, max_chars: int) -> str:
        full = _safe_path(rel_path)
        if not full or not os.path.isfile(full):
            return f"File not found: {rel_path}"
        with open(full, "r", encoding="utf-8", errors="ignore") as fh:
            content = fh.read()
        if len(content) > max_chars:
            return content[:max_chars] + f"\n\n[... truncated at {max_chars} chars — request more with max_chars ...]"
        return content
