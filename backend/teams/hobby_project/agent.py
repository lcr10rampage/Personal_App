import os
import re
import anthropic
import project_inbox

# Where the Project & Hobby Team knowledge base lives (the Project-hobby-team repo).
# Override with HOBBY_TEAM_DIR if it lives elsewhere.
TEAM_DIR = os.getenv("HOBBY_TEAM_DIR", os.path.expanduser("~/Project-hobby-team"))

MODEL = "claude-sonnet-4-6"

# Short key -> specialist prompt file. Each specialist runs as its own Sonnet call.
SPECIALISTS = {
    "measurement": "measurement-specialist.md",
    "designer": "designer.md",
    "functionality": "functionality-specialist.md",
    "cost": "cost-specialist.md",
    "risk": "risk-specialist.md",
    "time": "time-specialist.md",
    "sketch": "sketch-specialist.md",
    "3d_model": "3d-model-specialist.md",
    "materials": "materials-specialist.md",
    "tools_skills": "tools-skills-specialist.md",
    "build_sequence": "build-sequence-specialist.md",
    "research_compatibility": "research-compatibility-specialist.md",
    "testing": "testing-specialist.md",
    "documentation": "documentation-specialist.md",
}

# Operational addendum appended to the Coordinator's own instructions (agents/coordinator.md).
COORDINATOR_ADDENDUM = """

---

## How you operate in this app

You are a Sonnet agent driving the Project & Hobby Planning Team. Your knowledge base is the
Project-hobby-team repository. Use your tools:

- `read_team_file(path)` — load any file from the knowledge base (e.g. `modes/project-mode.md`,
  `agents/designer.md`, `TEAM_WORKFLOW.md`). Read the mode file after the user picks Hobby or
  Project so you activate the right specialists.
- `consult_specialist(specialist, task, context)` — run one specialist as its own Sonnet agent. It
  returns a detailed deliverable that already meets the Deliverable Standard. Give it the confirmed
  facts it needs in `context`. Valid specialist keys: %s.
- `save_workspace(name, mode, overview_markdown)` — persist/refresh a workspace's overview.
- `save_deliverable(workspace, filename, content)` — save a specialist deliverable to the workspace
  (e.g. `measurements.md`, `costs.md`).
- `list_workspaces()` / `read_workspace_file(workspace, filename)` — reopen prior work.

Rules of engagement:
- At the START of a new conversation, call `list_incoming` — the user's Life Manager may have handed
  off a project or hobby idea (from research or a goal). If there are incoming ideas, mention them
  and offer to plan one: "Your Life Manager sent over '<title>' — want to start a workspace for it?"
  When you turn one into a workspace, call `claim_incoming` with its id to clear it from the inbox.
- Ask "Is this a hobby or a project?" ONLY when the user proposes a NEW thing to plan and the
  current conversation has not already established the mode. Once this conversation has classified
  the current thing (the user answered, or it's clearly implied), DO NOT ask again — treat every
  follow-up question as being about that same workspace and just answer it. Only ask again if the
  user clearly starts planning a different, unrelated new thing.
- Do not role-play the specialists yourself — call `consult_specialist` so each is a real Sonnet
  agent. Integrate and sanity-check their outputs; surface conflicts rather than silently choosing.
- Tell the user which stage you're in and what the single next action is.
- Keep the user in control of important decisions.
""" % ", ".join(SPECIALISTS.keys())

FALLBACK_COORDINATOR = (
    "You are the Project Coordinator of the Project & Hobby Planning Team. Always begin a new "
    "workspace by asking 'Is this a hobby or a project?' and wait for the answer before doing "
    "anything else. Then activate the relevant specialists and produce detailed, practical plans."
)

TOOLS = [
    {
        "name": "read_team_file",
        "description": "Read a file from the Project-hobby-team knowledge base. Pass a path relative to the repo root, e.g. 'modes/project-mode.md', 'agents/coordinator.md', 'TEAM_WORKFLOW.md', 'HOBBY_PROJECT_TEAM_SPEC.md'.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path relative to the Project-hobby-team repo root"}
            },
            "required": ["path"],
        },
    },
    {
        "name": "list_team_files",
        "description": "List the files available in the Project-hobby-team knowledge base.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "consult_specialist",
        "description": "Run one specialist as its own Sonnet agent and get back a detailed deliverable. Provide the confirmed facts and the specific task.",
        "input_schema": {
            "type": "object",
            "properties": {
                "specialist": {"type": "string", "description": "One of: " + ", ".join(SPECIALISTS.keys())},
                "task": {"type": "string", "description": "The specific task for this specialist"},
                "context": {"type": "string", "description": "Confirmed facts, prior deliverables, and constraints the specialist needs"},
            },
            "required": ["specialist", "task"],
        },
    },
    {
        "name": "save_workspace",
        "description": "Create or refresh a workspace overview on disk (local, not cloud).",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "mode": {"type": "string", "description": "hobby | project"},
                "overview_markdown": {"type": "string"},
            },
            "required": ["name", "mode", "overview_markdown"],
        },
    },
    {
        "name": "save_deliverable",
        "description": "Save a specialist deliverable into a workspace. 'filename' must be a bare name only, e.g. 'measurements.md', 'sketches.svg', or 'model.html' — NEVER include the workspace name or any path. The interactive 3D model must always be saved as exactly 'model.html' (overwriting the previous one) so its URL stays stable.",
        "input_schema": {
            "type": "object",
            "properties": {
                "workspace": {"type": "string"},
                "filename": {"type": "string", "description": "Bare filename only, e.g. 'model.html'"},
                "content": {"type": "string"},
            },
            "required": ["workspace", "filename", "content"],
        },
    },
    {
        "name": "list_workspaces",
        "description": "List saved workspaces.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "read_workspace_file",
        "description": "Read a file from a saved workspace to reopen prior work.",
        "input_schema": {
            "type": "object",
            "properties": {
                "workspace": {"type": "string"},
                "filename": {"type": "string"},
            },
            "required": ["workspace", "filename"],
        },
    },
    {
        "name": "list_incoming",
        "description": "List project/hobby ideas handed off from the user's Life Manager (via research or goals). Check this at the start of a conversation.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "claim_incoming",
        "description": "Remove an incoming idea from the hand-off inbox once you've turned it into a workspace (pass its id).",
        "input_schema": {"type": "object", "properties": {"seed_id": {"type": "string"}}, "required": ["seed_id"]},
    },
]


def _slug(name: str) -> str:
    return re.sub(r"[^a-z0-9-]+", "-", name.lower()).strip("-") or "workspace"


def _safe_path(base: str, rel_path: str) -> str:
    full = os.path.normpath(os.path.join(base, rel_path))
    if not full.startswith(os.path.normpath(base)):
        return ""
    return full


class HobbyProjectTeam:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self._cache = {}
        self.system_prompt = self._build_system_prompt()

    def _build_system_prompt(self) -> str:
        coordinator = self._read_kb("agents/coordinator.md")
        if coordinator.startswith("File not found"):
            coordinator = FALLBACK_COORDINATOR
        return coordinator + COORDINATOR_ADDENDUM

    # --- knowledge base access ---
    def _read_kb(self, rel_path: str, max_chars: int = 16000) -> str:
        if rel_path in self._cache:
            return self._cache[rel_path]
        full = _safe_path(TEAM_DIR, rel_path)
        if not full or not os.path.isfile(full):
            return f"File not found: {rel_path}"
        with open(full, "r", encoding="utf-8", errors="ignore") as fh:
            content = fh.read()
        if len(content) > max_chars:
            content = content[:max_chars] + f"\n\n[... truncated at {max_chars} chars ...]"
        self._cache[rel_path] = content
        return content

    def _list_kb(self) -> str:
        if not os.path.isdir(TEAM_DIR):
            return f"Project-hobby-team not found at {TEAM_DIR}."
        paths = []
        for root, _dirs, files in os.walk(TEAM_DIR):
            if "/.git" in root or "/projects" in root:
                continue
            for f in files:
                if f.endswith(".md"):
                    paths.append(os.path.relpath(os.path.join(root, f), TEAM_DIR))
        return "\n".join(sorted(paths))

    # --- specialists as Sonnet agents ---
    def _consult(self, specialist: str, task: str, context: str = "") -> str:
        filename = SPECIALISTS.get(specialist)
        if not filename:
            return f"Unknown specialist '{specialist}'. Valid: {', '.join(SPECIALISTS.keys())}"
        standard = self._read_kb("DELIVERABLE_STANDARD.md")
        prompt = self._read_kb(f"agents/{filename}")
        system = f"{standard}\n\n---\n\n{prompt}"
        user = f"Task from the Project Coordinator:\n{task}"
        if context:
            user += f"\n\nContext / confirmed facts:\n{context}"
        result = self.client.messages.create(
            model=MODEL,
            max_tokens=3000,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return result.content[0].text

    # --- workspace persistence (local JSON/markdown) ---
    def _workspace_dir(self, name: str) -> str:
        d = os.path.join(TEAM_DIR, "projects", _slug(name))
        os.makedirs(d, exist_ok=True)
        return d

    def _save_workspace(self, name: str, mode: str, overview: str) -> str:
        d = self._workspace_dir(name)
        with open(os.path.join(d, "workspace.md"), "w", encoding="utf-8") as fh:
            fh.write(f"# {name}\n\n- **Type:** {mode}\n\n{overview}\n")
        return f"Workspace '{name}' saved ({mode}) at projects/{_slug(name)}/."

    def _save_deliverable(self, workspace: str, filename: str, content: str) -> str:
        d = self._workspace_dir(workspace)
        # Guard against the model jamming the workspace name / a path into the filename:
        # keep only the base name, and strip a leading workspace-slug prefix if present.
        filename = os.path.basename(filename.strip())
        slug = _slug(workspace)
        if filename.startswith(slug) and filename != slug:
            filename = filename[len(slug):].lstrip("-_") or filename
        safe = _safe_path(d, filename)
        if not safe:
            return "Invalid filename."
        with open(safe, "w", encoding="utf-8") as fh:
            fh.write(content)
        return f"Saved {filename} to workspace '{workspace}'."

    def _list_workspaces(self) -> str:
        base = os.path.join(TEAM_DIR, "projects")
        if not os.path.isdir(base):
            return "No workspaces yet."
        names = sorted(n for n in os.listdir(base) if os.path.isdir(os.path.join(base, n)))
        return "\n".join(names) if names else "No workspaces yet."

    def _read_workspace_file(self, workspace: str, filename: str) -> str:
        d = os.path.join(TEAM_DIR, "projects", _slug(workspace))
        safe = _safe_path(d, filename)
        if not safe or not os.path.isfile(safe):
            return f"Not found: {workspace}/{filename}"
        with open(safe, "r", encoding="utf-8", errors="ignore") as fh:
            return fh.read()

    # --- tool dispatch ---
    def _handle_tool(self, block) -> str:
        n, i = block.name, block.input
        if n == "read_team_file":
            return self._read_kb(i["path"])
        if n == "list_team_files":
            return self._list_kb()
        if n == "consult_specialist":
            return self._consult(i["specialist"], i["task"], i.get("context", ""))
        if n == "save_workspace":
            return self._save_workspace(i["name"], i["mode"], i["overview_markdown"])
        if n == "save_deliverable":
            return self._save_deliverable(i["workspace"], i["filename"], i["content"])
        if n == "list_workspaces":
            return self._list_workspaces()
        if n == "read_workspace_file":
            return self._read_workspace_file(i["workspace"], i["filename"])
        if n == "list_incoming":
            return project_inbox.format_seeds()
        if n == "claim_incoming":
            ok = project_inbox.remove_seed(i["seed_id"])
            return "Cleared from the inbox." if ok else f"No incoming idea with id {i['seed_id']}."
        return "Unknown tool."

    # --- main loop ---
    def chat(self, user_message: str, history=None) -> str:
        # Prior turns come from the persisted conversation (text-only), so the
        # Coordinator remembers the classification and won't re-ask hobby/project.
        messages = [dict(m) for m in (history or [])]
        messages.append({"role": "user", "content": user_message})
        while True:
            response = self.client.messages.create(
                model=MODEL,
                max_tokens=4096,
                system=self.system_prompt,
                tools=TOOLS,
                messages=messages,
            )
            if response.stop_reason == "tool_use":
                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": self._handle_tool(block),
                        })
                messages.append({"role": "assistant", "content": response.content})
                messages.append({"role": "user", "content": tool_results})
                continue

            reply = next((b.text for b in response.content if getattr(b, "type", None) == "text"), "")
            return reply
