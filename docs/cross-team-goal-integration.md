# Plan: Project/Hobby Team → Goal Manager (cross-team goal creation)

**Status:** Planned — not built yet. Requested 2026-07-20. Build later.

## What the user wants
When they add a **project or goal in the Project & Hobby team**, that team should hand it to the
**Personal manager team (Life Manager)** and create a matching **goal in the Goal Manager**, so the
project becomes something they can track (progress %, target date, accountability) alongside the
rest of their life.

Example: user creates the "6×10 camper trailer" project in the hobby team → a goal
"Build the 6×10 camper trailer" appears in the Goal Manager with the project's target completion
date, linked back to the workspace.

## Why this is easy here
Both teams run in the **same FastAPI backend** (`main.py` `TEAMS`), and the Goal Manager's store is
a plain local module (`agents/goals/store.py`). So the hobby team can create goals by calling the
**same store directly** — no network, no cross-process messaging needed.

## Recommended approach — shared store + a confirm step
1. **New tool on the hobby_project team:** `propose_goal(title, detail, target_date, workspace)`.
   - The Coordinator offers it when a workspace is created or reaches READY_TO_BUILD / READY_TO_START:
     "Want to track this as a goal in your Life Manager?"
   - On yes, it calls `agents.goals.store.add_goal(...)` with:
     - `category="project"` (or `"hobby"`)
     - `title` = the workspace name / goal
     - `target_date` = target completion (from the Time Specialist when available)
     - `detail` = one-line summary + a link to the workspace files
       (`/workspaces/<slug>/workspace.md`)
2. **Link the two:** store the workspace slug on the goal (add an optional `workspace` field to the
   goal schema in `store.py`). That lets the Goal Manager deep-link to the 3D model / sketches, and
   lets us find "the goal for this project" later.
3. **Progress sync (nice-to-have):** map the workspace `stage` → goal `percent`
   (e.g. CLASSIFICATION 0% … BUILDING 70% … COMPLETE 100%), updated whenever the Coordinator
   changes the stage. Or let the user update progress manually via the Life Manager.
4. **Dedupe:** before creating, check `list_goals()` for an existing goal with the same `workspace`
   slug; update it instead of adding a duplicate.

## Alternative (only if teams ever split into separate services)
Have the hobby team emit a "goal proposal" that the Life Manager CEO ingests via a tool
(`import_goal_proposal`). More moving parts; unnecessary while both share one backend. Keep the
direct-store approach unless the architecture changes.

## Data model change (small)
In `agents/goals/store.py`, add to each goal:
- `workspace: str` (optional) — the hobby workspace slug this goal came from
- `source: str` — "manual" | "school" | "project" | "hobby"

## Build steps when we do this
1. Extend `store.add_goal(...)` with `workspace` and `source` fields (backwards compatible).
2. Add `propose_goal` tool + handler to `teams/hobby_project/agent.py` (imports the goals store).
3. Update the Coordinator prompt (`Project-hobby-team/agents/coordinator.md`) to offer goal tracking
   at workspace creation and at READY_TO_BUILD/READY_TO_START.
4. (Optional) stage→percent sync on stage changes.
5. Surface the linked workspace URL in the Goal Manager's output.

## Open questions
- Should creating the goal be automatic on project creation, or always confirmed? (Default: confirm.)
- One goal per project, or sub-goals per phase? (Start with one; revisit.)
- Who owns progress updates — the hobby team (by stage) or the user (via Life Manager)? (Start manual.)

## Related
- Goal Manager: `agents/goals/agent.py`, `agents/goals/store.py`
- Hobby team: `teams/hobby_project/agent.py`, knowledge base in `~/Project-hobby-team`
- CEO Rule 13 already connects **School → Goals**; this extends the same idea to **Projects → Goals**.
