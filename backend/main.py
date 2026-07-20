import os
from typing import Optional
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.concurrency import run_in_threadpool
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv
from agents.ceo.agent import CEOAgent
from teams.app_builder.agent import AppBuilderTeam
from teams.hobby_project.agent import HobbyProjectTeam, TEAM_DIR
import conversations as convo

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve the Project & Hobby Team's workspace files (sketches, model.html, docs)
# through the backend so they open via the same tunnel the dashboard already uses:
#   http://localhost:8000/workspaces/<name>/model.html
WORKSPACES_DIR = os.path.join(TEAM_DIR, "projects")
os.makedirs(WORKSPACES_DIR, exist_ok=True)
app.mount("/workspaces", StaticFiles(directory=WORKSPACES_DIR, html=True), name="workspaces")

# One persistent instance per team — history is kept across the session.
TEAMS = {
    "life_manager": CEOAgent(),
    "app_builder": AppBuilderTeam(),
    "hobby_project": HobbyProjectTeam(),
}

class ChatRequest(BaseModel):
    message: str
    team: str = "life_manager"
    conversation_id: Optional[str] = None

@app.post("/chat")
async def chat(req: ChatRequest):
    agent = TEAMS.get(req.team)
    if agent is None:
        return {"response": f"Unknown team: {req.team}"}

    # Resume the named conversation (or start a new one) so history persists.
    conv = convo.get_conversation(req.conversation_id) if req.conversation_id else None
    if conv is None or conv.get("team") != req.team:
        conv = convo.create_conversation(req.team)
    history = convo.history_for_model(conv)

    # agent.chat makes blocking API calls; run it off the event loop so one slow
    # request (e.g. a multi-specialist team) doesn't freeze the whole server.
    try:
        response = await run_in_threadpool(agent.chat, req.message, history)
    except Exception as e:
        return {"response": f"The team hit an error: {type(e).__name__}: {e}",
                "conversation_id": conv["id"], "title": conv["title"]}

    convo.append_message(conv["id"], "user", req.message)
    updated = convo.append_message(conv["id"], "assistant", response)
    return {"response": response, "conversation_id": conv["id"], "title": updated["title"]}


class NewConversation(BaseModel):
    team: str = "life_manager"
    title: Optional[str] = None

class RenameConversation(BaseModel):
    title: str

@app.get("/conversations")
async def list_conversations(team: str):
    return {"conversations": convo.list_conversations(team)}

@app.post("/conversations")
async def new_conversation(body: NewConversation):
    c = convo.create_conversation(body.team, body.title)
    return {"id": c["id"], "title": c["title"], "team": c["team"], "updated": c["updated"]}

@app.get("/conversations/{cid}")
async def get_conversation(cid: str):
    c = convo.get_conversation(cid)
    if not c:
        return {"error": "not found"}
    msgs = [{"role": m["role"], "content": m["content"], "ts": m.get("ts")} for m in c["messages"]]
    return {"id": c["id"], "title": c["title"], "team": c["team"], "messages": msgs}

@app.patch("/conversations/{cid}")
async def rename_conversation(cid: str, body: RenameConversation):
    c = convo.rename_conversation(cid, body.title)
    return {"ok": c is not None, "title": c["title"] if c else None}

@app.delete("/conversations/{cid}")
async def delete_conversation(cid: str):
    return {"ok": convo.delete_conversation(cid)}

@app.get("/health")
async def health():
    return {"status": "running"}
