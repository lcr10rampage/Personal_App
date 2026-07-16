# Personal Life Manager

**Startup Specification & Technical Blueprint — Version 0.1**

---

## Vision

Modern people — especially students — are overwhelmed by disconnected responsibilities. Important information is scattered across email, calendars, school portals, documents, notes, messages, files, reminders, and personal goals. The user becomes responsible for connecting everything. They must remember what needs to be done, when it needs to be done, how long it will take, what conflicts exist, and what should matter most. This creates mental overload.

The Personal Life Manager is an AI-powered personal assistant designed to remove that mental burden entirely.

### The Central Promise

> "You live your life. Your manager handles everything else."

### What the AI Does
- Remembering
- Organizing
- Planning
- Connecting information
- Finding priorities
- Preparing suggestions
- Creating drafts
- Keeping track of important things

### What the User Does
- Making decisions
- Creating
- Learning
- Building relationships
- Meaningful work

---

## Mission Statement

> Build software that manages life instead of simply organizing it.

This is not another calendar app, task manager, productivity tracker, or chatbot. The goal is a trusted AI system that understands a person and helps them navigate life.

---

## Core Philosophy

### Humans Should Focus On
- Thinking, creating, learning, building
- Relationships and purposeful work

### AI Should Handle
- Remembering, organizing, preparing
- Summarizing, connecting information
- Reducing repetitive mental work

---

## Initial Target User

**Primary user:** High school students who are involved in many activities, have many responsibilities, and feel like they are always trying to remember something.

**Examples:**
- Musicians and band members
- Athletes
- Student leaders
- Advanced students (AP, IB, dual enrollment)
- Students preparing for college
- Students with part-time jobs
- Students building side projects

---

## Customer Pain Points

### Problem 1 — Forgetting Important Things
Students have information everywhere. A teacher emails something. A deadline appears. A practice changes. A test gets scheduled. The student has to manually connect everything.

### Problem 2 — Feeling Overwhelmed
The problem is not always having too much work. The problem is not knowing what matters most, what can wait, and what should happen next.

### Problem 3 — Lack of Planning
Students know their responsibilities but struggle with time allocation, scheduling, and balancing priorities.

### Problem 4 — Information Overload
Most productivity apps show more information. This app should reduce information.

---

## Product Promise

**Before:** "What am I forgetting?"

**After:** "My manager already checked."

The goal is not maximum productivity. The goal is **confidence**.

---

## Product Identity & Feel

The app should feel like:

- **A Cozy Library** — warm, peaceful, inviting, comfortable
- **A Personal Study** — focused, organized, a place where meaningful work happens
- **A Command Center** — everything connected, important information available, AI coordinating behind the scenes

> "This is my headquarters."

---

## Design Principles

1. **Calm First** — The app should reduce stress before increasing productivity. The first feeling should be peace, welcome, and confidence. Not pressure, anxiety, or overwhelm.
2. **Everything Connected** — The AI connects calendar, email, school, documents, goals, research, notes, and projects.
3. **AI Earns Trust** — The AI explains, suggests, asks permission when appropriate, and learns. Trust grows through consistency.
4. **User Always Controls Decisions** — The AI prepares. The user decides. The AI should never secretly send messages, change important events, or make decisions for the user.
5. **Every Recommendation Has Reasoning** — The AI explains what happened, why it matters, why it recommends something, and other options.
6. **Reduce Cognitive Load** — Every feature must answer: "Will this make the user have to think about one less thing?" If not, it should be reconsidered.

---

## AI Organization

The app works like a company. The user interacts primarily with the CEO AI. Behind the scenes, specialist managers handle their domains.

### CEO AI
The heart of the product. The user's main relationship. The CEO:
- Understands the whole picture
- Coordinates other AI managers
- Creates summaries
- Resolves conflicts
- Makes suggestions
- Learns user preferences
- Communicates clearly

The user should feel: *"I have an assistant."* Not: *"I have ten AI agents."*

### Specialist Managers

| Manager | Responsible For | Core Question |
|---|---|---|
| Email Manager | Understanding emails, finding important messages, summarizing, drafting, identifying actions | "What changed?" |
| Calendar Manager | Scheduling, conflicts, time planning, preparation | "When should things happen?" |
| School Manager | Classes, assignments, tests, teachers, academic planning | "What do I need to know about school?" |
| Goal Manager | Long-term goals, progress, accountability, improvement | "Am I moving forward?" |
| Research Manager | Research, projects, learning, decisions | "What do I need to know before I begin?" |
| Knowledge Manager | Finding information, connecting information, remembering where things are | "Where is it?" |
| Notification Manager | Deciding importance, reducing interruptions, combining information | "Does this matter right now?" |
| Memory Manager | Preferences, habits, communication style, work style | "What does the user prefer?" |

### How CEO + Manager Communication Works

The user talks to the CEO AI. Example:

> User: "Help me prepare for my chemistry test."

CEO AI understands the request → contacts School Manager → gets information → responds.

The user can optionally talk directly to specialists, but should never need to understand the internal organization.

---

## Daily Experience

### Morning
- Calm sunrise animation
- Greeting
- Optional Bible verse
- Weather
- Most important notification
- Next upcoming event
- Goal progress

The app does not show everything immediately. It creates confidence first.

### During the Day
The AI works quietly — reviewing updates, finding conflicts, planning ahead, improving itself. It does not constantly interrupt.

### After School
The AI suggests a plan: what should happen, why, how long it takes, and other options. The user chooses.

### Evening
The AI adapts to the user. Some users want reflection and planning. Others want a simple summary. The AI learns.

### Saturday
Heavy planning — homework, tests, goals, projects, upcoming events.

### Sunday
Intentional simplicity. Minimal planning. Preparation and rest.

---

## Navigation Model

The app uses a headquarters model. The CEO AI is the primary navigation system. Users can ask:
- "Show me my robotics notes."
- "Find my chemistry assignment."
- "Help me plan this project."

Possible section structure:
- **Today** — Home, daily overview, notifications
- **Life** — Goals, health, habits
- **Knowledge** — Notes, research, documents
- **Communication** — Email, messages
- **Settings**

---

## Long-Term Vision

The Personal Life Manager is the first piece of a larger ecosystem.

### Future Products
- **Engineering Notebook** — AI for engineers, developers, projects, experiments
- **Local Business Operating System** — AI for businesses, customers, operations
- **Cognitive Operating System** — A unified intelligence system for people, projects, and organizations

---

# Technical Architecture

## Stack

| Layer | Technology | Purpose |
|---|---|---|
| AI Brain | Claude API (Anthropic) | All agent reasoning and responses |
| Agent Orchestration | Custom routing loop (Python) | CEO routes to specialist managers |
| Backend | FastAPI (Python) | API server |
| Frontend (planned) | React + TypeScript + Vite | UI |
| Animations (planned) | Framer Motion | Calm transitions, sunrise animation |
| Styling (planned) | Tailwind CSS | Design system |
| Auth (planned) | Supabase Auth | Google OAuth |
| Database (planned) | Supabase (PostgreSQL) | Goals, assignments, user data |
| Memory (planned) | Supabase + pgvector | Long-term semantic memory |
| Calendar | Google Calendar API | Read/write calendar events |
| Email (planned) | Gmail API | Read, draft, send emails |
| School (planned) | Google Classroom API | Assignments, classes |
| Weather (planned) | OpenWeatherMap | Daily briefing |
| Deployment (planned) | GCP Cloud Run | Production hosting |

---

## Claude API Model Decisions

### Model Selection

| Use Case | Model | Reason |
|---|---|---|
| CEO AI (synthesis, routing, reasoning) | `claude-sonnet-4-6` | Smart enough for complex reasoning, fast enough for conversation |
| Specialist managers (calendar, email, etc.) | `claude-haiku-4-5-20251001` | Simple, focused tasks — fast and cheap |
| Nothing in this app | `claude-opus-4-8` | Overkill for routine work |

**Rule:** Use the smallest model that does the job well. Haiku handles 70%+ of all work. Sonnet handles the CEO layer. Opus is never needed here.

### How Agents "Spin Up and Down"

A common misconception is that manager agents are running processes. They are not. Each manager is a **Python function that makes a single Claude API call**. It exists for the duration of that call and is gone when the function returns.

```
User message
    → CEO AI (Claude Sonnet API call)
    → CEO decides which manager to call
    → Manager function runs (Claude Haiku API call)
    → Manager returns result to CEO
    → CEO synthesizes final response
    → Function returns, everything gone
```

There are no background processes to manage. No servers to start or stop. No resource management needed. You pay only for what gets called.

If the user asks "how are you?" — zero manager calls happen. If they ask about their schedule — one calendar manager call happens. If they ask to reschedule an event and clear conflicts — multiple tool calls happen in sequence inside a single request loop.

### Multi-Tool Call Loop

The CEO runs in a `while True` loop that keeps processing tool calls until the model returns `stop_reason == "end_turn"`. This allows the CEO to:
1. Check the calendar for conflicts
2. Delete conflicting events
3. Update the target event

All in one user request, without the user seeing any of the intermediate steps.

### Cost Estimates

| User Type | Daily Requests | Monthly API Cost (with caching) |
|---|---|---|
| Light (2x/day check-ins) | ~7 | ~$0.90 |
| Medium (active daily use) | ~20 | ~$5.00 |
| Heavy (power user, documents) | ~50 | ~$20.00 |

**Key cost controls:**
- Use Haiku for all specialist manager calls
- Use prompt caching for system prompts and user profile (90% discount on repeated tokens)
- Summarize emails/documents with Haiku before passing to CEO
- Use Anthropic Batch API for non-real-time background tasks (50% discount)
- Set monthly token budgets per user tier

**Pricing tiers (planned):**
- Free: 500K tokens/month
- Basic ($5/mo): 3M tokens/month
- Pro ($12/mo): 15M tokens/month

---

## Current File Structure

```
Personal_App/
├── backend/
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── ceo.py          ← CEO AI + tool routing loop
│   │   └── managers.py     ← All specialist managers + Google Calendar functions
│   ├── main.py             ← FastAPI server + /chat endpoint
│   ├── chat.py             ← Terminal chat interface for testing
│   ├── auth_google.py      ← One-time Google OAuth flow (run once)
│   ├── .env                ← ANTHROPIC_API_KEY (never committed)
│   ├── credentials.json    ← Google OAuth credentials (never committed)
│   └── token.json          ← Google Calendar access token (never committed)
├── .gitignore
└── README.md
```

---

## Current Capabilities (MVP Phase 1)

- [x] CEO AI — holds natural language conversations
- [x] Calendar Manager — reads Google Calendar (7-day lookahead with full start/end times)
- [x] Create events via natural language
- [x] Update events via natural language
- [x] Delete events via natural language
- [x] Conflict detection and clearing
- [x] Terminal chat interface for testing
- [x] FastAPI `/chat` endpoint

## Next Up

- [ ] React frontend (headquarters UI)
- [ ] School Manager (Google Classroom)
- [ ] Email Manager (Gmail)
- [ ] Goal Manager (Supabase)
- [ ] Morning briefing endpoint
- [ ] User memory system
- [ ] Onboarding flow
- [ ] Mobile-responsive design

---

## Running Locally

```bash
# Install dependencies
cd Personal_App
python3 -m venv venv
source venv/bin/activate
pip install anthropic fastapi uvicorn python-dotenv google-api-python-client google-auth-httplib2 google-auth-oauthlib

# Add your API key
echo "ANTHROPIC_API_KEY=your-key-here" > backend/.env

# Run one-time Google auth (first time only)
cd backend && python auth_google.py

# Start the server
uvicorn main:app --reload --port 8000

# Or use the terminal chat
python chat.py
```

---

*Startup Specification Version 0.1 — Personal Life Manager*
