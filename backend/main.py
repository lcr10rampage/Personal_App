import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.concurrency import run_in_threadpool
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv
from agents.ceo.agent import CEOAgent
from teams.app_builder.agent import AppBuilderTeam
from teams.hobby_project.agent import HobbyProjectTeam, TEAM_DIR

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

@app.post("/chat")
async def chat(req: ChatRequest):
    agent = TEAMS.get(req.team)
    if agent is None:
        return {"response": f"Unknown team: {req.team}"}
    # agent.chat makes blocking API calls; run it off the event loop so one slow
    # request (e.g. a multi-specialist team) doesn't freeze the whole server.
    try:
        response = await run_in_threadpool(agent.chat, req.message)
    except Exception as e:
        return {"response": f"The team hit an error: {type(e).__name__}: {e}"}
    return {"response": response}

@app.get("/health")
async def health():
    return {"status": "running"}
