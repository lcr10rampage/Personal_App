"""Run a team on the Claude *subscription* via the Claude Agent SDK.

Auth comes from the Claude Code CLI login on this host (the ``claudeAiOauth`` creds in
``~/.claude/.credentials.json``), so these calls count against the subscription's rate
limits instead of per-token Anthropic API billing.

Toggle with the ``TEAM_BACKEND`` env var:
  - ``sdk`` (default) → run on the subscription through this module.
  - ``api``           → use the original Anthropic API path (needs ANTHROPIC_API_KEY).

Only the two heavy teams (app_builder, hobby_project) use this. The Life Manager
managers stay on the API where lean, cached, per-call control matters.
"""
import os
import anyio
import claude_agent_sdk as sdk

# "sdk" = subscription; "api" = per-token Anthropic fallback (the original code path).
TEAM_BACKEND = os.getenv("TEAM_BACKEND", "sdk").strip().lower()
# On the subscription the model is named simply ("sonnet" / "haiku"), not the API id.
SDK_MODEL = os.getenv("TEAM_SDK_MODEL", "sonnet")
# Cap agentic turns so a tool loop can't run away.
MAX_TURNS = int(os.getenv("TEAM_SDK_MAX_TURNS", "30"))


def use_sdk() -> bool:
    return TEAM_BACKEND == "sdk"


def format_prompt(history, user_message: str) -> str:
    """Flatten the persisted text-only history + new message into one prompt string.

    Matches how these teams already work — history is plain text context re-sent each
    call, not a live SDK session.
    """
    if not history:
        return user_message
    lines = []
    for m in history:
        speaker = "User" if m.get("role") == "user" else "Assistant"
        lines.append(f"{speaker}: {m.get('content', '')}")
    lines.append(f"User: {user_message}")
    lines.append("\n(Continue as the Assistant. Reply only to the latest User message.)")
    return "\n\n".join(lines)


def _last_assistant_text(final: str, msg) -> str:
    """Keep only the most recent assistant turn's text (mirrors returning the final
    text block at end_turn in the original loops)."""
    if isinstance(msg, sdk.AssistantMessage):
        texts = [b.text for b in msg.content if isinstance(b, sdk.TextBlock)]
        if texts:
            return "\n".join(texts)
    return final


async def _run_agentic(system_prompt, tool_specs, dispatch, prompt, model):
    server = None
    allowed = []
    if tool_specs:
        sdk_tools = []
        for spec in tool_specs:
            schema = spec.get("input_schema") or {"type": "object", "properties": {}}

            async def handler(args, _name=spec["name"]):
                # dispatch is sync (and may make its own nested SDK calls) → run it off
                # the event loop so it can't block or re-enter the loop.
                result = await anyio.to_thread.run_sync(dispatch, _name, args)
                return {"content": [{"type": "text", "text": str(result)}]}

            sdk_tools.append(sdk.tool(spec["name"], spec.get("description", ""), schema)(handler))
            allowed.append(f"mcp__team__{spec['name']}")
        server = sdk.create_sdk_mcp_server("team", "1.0.0", sdk_tools)

    opts = sdk.ClaudeAgentOptions(
        system_prompt=system_prompt,
        model=model,
        mcp_servers={"team": server} if server else {},
        allowed_tools=allowed,
        permission_mode="bypassPermissions",
        setting_sources=[],  # do NOT load ~/CLAUDE.md / skills — keep the team agent clean
        max_turns=MAX_TURNS,
    )
    final = ""
    async for msg in sdk.query(prompt=prompt, options=opts):
        final = _last_assistant_text(final, msg)
    return final


async def _run_oneshot(system_prompt, prompt, model):
    opts = sdk.ClaudeAgentOptions(
        system_prompt=system_prompt,
        model=model,
        permission_mode="bypassPermissions",
        setting_sources=[],
        max_turns=1,
    )
    final = ""
    async for msg in sdk.query(prompt=prompt, options=opts):
        final = _last_assistant_text(final, msg)
    return final


def run_agentic(system_prompt, tool_specs, dispatch, prompt, model=None) -> str:
    """Sync entry point for an agentic (tool-using) team turn.

    ``chat()`` runs inside a FastAPI threadpool thread, so ``anyio.run`` here is safe —
    there's no event loop already running in this thread.
    """
    return anyio.run(_run_agentic, system_prompt, tool_specs, dispatch, prompt, model or SDK_MODEL)


def run_oneshot(system_prompt, prompt, model=None) -> str:
    """Sync entry point for a single no-tools completion (e.g. one specialist)."""
    return anyio.run(_run_oneshot, system_prompt, prompt, model or SDK_MODEL)
