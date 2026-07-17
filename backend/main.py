from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from agents.ceo.agent import CEOAgent
from teams.app_builder.agent import AppBuilderTeam

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# One persistent instance per team — history is kept across the session.
TEAMS = {
    "life_manager": CEOAgent(),
    "app_builder": AppBuilderTeam(),
}

class ChatRequest(BaseModel):
    message: str
    team: str = "life_manager"

@app.post("/chat")
async def chat(req: ChatRequest):
    agent = TEAMS.get(req.team)
    if agent is None:
        return {"response": f"Unknown team: {req.team}"}
    response = agent.chat(req.message)
    return {"response": response}

@app.get("/health")
async def health():
    return {"status": "running"}
