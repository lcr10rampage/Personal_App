# Personal Life Manager

## Detailed Multi-Agent Architecture Specification

## 1. System Overview

The Personal Life Manager is built as a coordinated system of specialized AI agents.

The user should not feel as though they are operating several separate AI tools. From the user's perspective, they have one intelligent personal assistant that understands their life and can help across email, school, scheduling, projects, goals, documents, and daily planning.

Behind the scenes, however, the system is divided into specialized managers. Each manager owns one area of responsibility and collaborates with the others through a shared event and change-request system.

The architecture follows five central principles:

1. Each manager owns one clearly defined domain.
2. Managers do not directly modify another manager's data.
3. Managers consult the Memory AI when personalization is needed.
4. Managers communicate changes through structured events and change requests.
5. The Orchestrator AI combines the results into one unified user experience.

The basic system can be understood as:

**User or external event**

↓

**Relevant specialized manager**

↓

**Memory AI consultation**

↓

**Other affected managers**

↓

**Orchestrator AI**

↓

**One clear response to the user**

---

# 2. Orchestrator AI

## Core Purpose

The Orchestrator AI replaces the original CEO AI.

It is the primary interface between the user and the Personal Life Manager system. It does not own a specific area of the user's life. Instead, it understands requests, finds the correct managers, coordinates their work, resolves conflicts, and communicates the final result.

The Orchestrator is the system's coordination and communication layer.

Its central question is:

> "Which managers need to participate, and how should their findings be combined into one useful response?"

## What the Orchestrator Owns

The Orchestrator owns:

* The active conversation with the user
* User-intent interpretation
* Request routing
* Manager coordination
* Conflict resolution
* Response assembly
* Approval collection
* Conversational continuity during the current interaction

It may maintain temporary context during an active conversation, but it does not create its own permanent long-term memory.

## What the Orchestrator Does Not Own

The Orchestrator does not permanently own:

* User preferences
* User habits
* Email data
* Calendar data
* School information
* Documents
* Notes
* Goals
* Notification rules
* Project information

Those belong to the appropriate specialized manager.

## Orchestrator Workflow

When the user asks a question, the Orchestrator:

1. Determines what the user is trying to accomplish.
2. Identifies which managers are relevant.
3. Sends each manager a focused request.
4. Waits for the relevant managers to complete their analysis.
5. Compares their findings.
6. Identifies conflicts, dependencies, or missing information.
7. Requests additional analysis when necessary.
8. Consults the Memory AI indirectly or requests personalized output from each manager.
9. Produces one clear response.
10. Requests user approval before any important external action.

## Example

The user says:

> "Help me prepare for tomorrow."

The Orchestrator may contact:

* Time Manager for tomorrow's schedule
* School Manager for assignments and tests
* Communication Manager for recent changes
* Knowledge Manager for relevant materials
* Memory AI for planning and information preferences

The Orchestrator then combines the results:

> "Tomorrow you have chemistry first period, band rehearsal after school, and a math quiz. Your chemistry teacher also sent a reminder about bringing your lab notebook. Based on how you prefer to prepare, I recommend reviewing math first, packing your band materials tonight, and leaving chemistry review for your shorter morning session."

The Orchestrator did not independently remember or discover those details. It coordinated the managers that owned them.

## Conflict Resolution

The Orchestrator is responsible for resolving conflicts between recommendations.

For example:

* The School Manager recommends two hours of studying.
* The Time Manager reports only one hour is available.
* The Goal Manager recommends protecting workout consistency.
* The Memory AI indicates the user becomes overwhelmed by overly full evenings.

The Orchestrator may respond:

> "There is not enough time tonight for the full two-hour study plan without removing your workout. I recommend a focused 60-minute study session tonight and a 30-minute review tomorrow morning."

The Orchestrator does not alter the underlying data itself. It creates a unified recommendation and asks the user what should happen.

## Important Boundary

The Orchestrator should never become an all-knowing agent.

Its intelligence comes from knowing:

* Which manager to ask
* What information to request
* How to combine the results
* When to involve the user

This separation prevents duplicated data and keeps the architecture easier to maintain.

---

# 3. Memory AI

## Core Purpose

The Memory AI strictly remembers the user.

It does not primarily remember documents, assignments, email contents, event details, or general information. Those belong to other managers.

The Memory AI builds and maintains a living model of how the user operates.

Its central question is:

> "How does this person naturally work, communicate, decide, organize, plan, and respond?"

## What the Memory AI Learns

### Work Style

The Memory AI learns:

* Whether the user prefers one large task or several smaller tasks
* Preferred work-session length
* Preferred break structure
* Best times for focused work
* Whether the user prefers early preparation or deadline pressure
* Whether the user likes completing difficult tasks first
* Whether the user prefers batching related work
* How much work the user can realistically handle at once
* How the user responds to busy or low-energy days

The distinction between one large task and several smaller tasks is especially important because it affects how plans are created across the entire system.

### Information Style

The Memory AI learns:

* Whether the user wants a summary first
* How much detail the user prefers
* Whether the user prefers lists or paragraphs
* Whether visual explanations are helpful
* Whether the user wants one recommendation or several options
* Whether reasoning should be shown before or after the recommendation
* Whether the user prefers calm, direct, encouraging, or highly practical wording
* How much complexity the user can comfortably process at once

### Planning Style

The Memory AI learns:

* Preferred planning days
* Preferred rest days
* Desired schedule flexibility
* Preferred buffer time
* Whether the user likes strict schedules or flexible plans
* How the user wants school, work, band, workouts, hobbies, and free time balanced
* How much unscheduled time the user prefers
* Whether the user likes planning far ahead or one day at a time
* How the user responds when plans change

The Memory AI does not own the actual school, work, band, or workout events. It remembers how those areas normally fit into the user's life and how the user prefers them to be handled.

### Writing Style

During onboarding, the user provides a foundation for their preferred writing style.

The Memory AI then learns from:

* Email drafts the user approves
* Edits the user makes
* Messages written by the user
* Documents and reports the user creates
* Repeated changes to tone, length, structure, and formality

It may learn:

* Preferred tone
* Preferred level of formality
* Typical sentence length
* Vocabulary preferences
* Greeting and closing style
* Whether the user prefers contractions
* Whether the user prefers direct or diplomatic language
* How much context the user normally includes

### Notification Style

The Memory AI learns:

* How often the user wants to be interrupted
* Which categories justify immediate interruption
* Best times to deliver notifications
* Preferred notification length
* Whether several updates should be grouped
* How often reminders should repeat
* When reminders become annoying
* Whether the user responds better to gentle or firm reminders

The user defines an initial interruption preference during onboarding. The system then learns from the user's behavior over time.

### Decision Style

The Memory AI learns:

* Whether the user wants all options or only the strongest options
* Whether the user wants a recommendation first
* Whether pros and cons are useful
* How much reasoning the user needs
* Whether cost, time, energy, or convenience matters most
* Whether the user prefers quick decisions or time to consider
* Whether the user wants the AI to be decisive or neutral

### Motivation Style

The Memory AI asks the user what motivates them when they first begin using the application.

It then learns whether the user responds well to:

* Encouragement
* Direct honesty
* Accountability
* Progress tracking
* Percent-complete indicators
* Goal reminders
* Deadline reminders
* Competition
* Rewards
* Scripture or faith-based encouragement, when enabled by the user
* Calm recovery planning after falling behind

The Memory AI should observe outcomes rather than assuming that a motivational style works simply because the user selected it during onboarding.

## Memory Learning Rules

The Memory AI should observe closely but avoid jumping to conclusions.

When it identifies a likely pattern, it asks:

> "I've noticed that you usually prefer one larger focused work session instead of several short sessions. Would you like me to remember that?"

The user can:

* Confirm it
* Reject it
* Modify it
* Mark it as situational

## Replacing and Adding Memories

When a new confirmed memory relates to an existing preference, the new memory replaces the old one.

When the new memory describes a different area, it is added without removing unrelated memories.

## Context-Specific Preferences

The Memory AI should avoid treating every preference as universal.

A user may prefer:

* Short emails
* Detailed startup plans
* Flexible weekend schedules
* Strict school schedules
* Direct reminders for deadlines
* Gentle reminders for personal goals

Each memory should include its relevant context.

## Memory Organization by Manager

The Memory AI separates and serves memories according to each manager's needs.

### Communication Manager receives:
* Writing style, tone, formality, preferred summary format, important communication preferences, approval habits

### Time Manager receives:
* Planning style, buffer preferences, work-session preferences, best focus times, rest preferences, interruption tolerance

### School Manager receives:
* Study habits, task-size preference, learning preferences, academic planning preferences, motivation style

### Goal Manager receives:
* Motivation style, progress-display preferences, accountability preferences, preferred milestone size, long-term planning style

### Notification Manager receives:
* Interruption frequency, urgency thresholds, preferred notification format, reminder tolerance, quiet periods

### Knowledge Manager receives:
* Preferred search-result format, preferred explanation depth, organization preferences, whether the user prefers one result or several alternatives

## Memory AI Boundary

The Memory AI remembers how the user works and what they prefer.

It does not own domain facts (test dates, emails, assignments). Those belong to the appropriate manager.

---

# 4. Knowledge Manager

## Core Purpose

The Knowledge Manager acts as the system's intelligent librarian.

Its central question is:

> "Where is the relevant information, and how is it connected?"

## Information Sources

The Knowledge Manager may index:

* Notes, PDFs, Google Docs, Presentations, Spreadsheets
* Emails, Calendar attachments
* Photos, Screenshots, Manuals
* Websites, Saved research, Project files

## Main Responsibilities

* Finds documents and information
* Indexes titles, keywords, topics, and metadata
* Connects related documents
* Identifies categories and creates virtual organization
* Provides relevant materials to other managers
* Suggests improved organization
* Helps distinguish current from outdated information
* Provides source locations

## Organization Rules

* May create a virtual organizational layer without physically moving files
* Must request permission before moving, renaming, deleting, archiving, or changing folder structures

## Collaboration

Supplies information to: School Manager, Goal Manager, Communication Manager, Time Manager, Orchestrator.

Does not decide what the user should do with information — only finds and organizes it.

---

# 5. Communication Manager

## Core Purpose

The Communication Manager helps the user understand and act on communications.

Its central question is:

> "What changed, what matters, and what does the user need to do?"

## Main Responsibilities

* Reads incoming communications
* Summarizes long messages
* Extracts action items and deadlines
* Detects schedule changes
* Identifies opportunities
* Drafts replies
* Tracks conversation state
* Identifies which other managers are affected
* Creates structured events and change requests
* Consults the Memory AI for communication style

## Email Summary Structure

For an important email, produces:

* What changed
* Why it matters
* What action is required
* Relevant deadline
* Suggested reply
* Other affected areas

## Prioritization Order

1. College and scholarship matters
2. Important school changes
3. Extracurricular changes
4. Time-sensitive logistics
5. Casual communication

## Reply Drafting

1. Reads original message and conversation history
2. Determines communication goal
3. Requests writing preferences from Memory AI
4. Drafts the response
5. Explains important wording choices when useful
6. Presents draft for approval
7. Learns from user edits through Memory AI

**Never sends an important message without explicit user approval.**

## Conversation States

* Reply required
* Waiting for response
* Completed
* Follow-up needed
* Deadline approaching
* Information only

## Opportunity Detection

May identify scholarships, applications, invitations, deadlines, leadership opportunities, job opportunities, and important requests. Suggestions should be rare and high-confidence.

---

# 6. Time Manager

## Core Purpose

The Time Manager owns the user's calendar, scheduling logic, time blocks, availability, and schedule recommendations.

Its central question is:

> "How should the user's limited time be arranged?"

## Main Responsibilities

* Reads calendar events
* Identifies free time and detects conflicts
* Creates scheduling recommendations
* Suggests time blocks and estimates preparation time
* Protects important commitments and adds appropriate buffers
* Responds to date or time changes from other managers
* Consults the Memory AI for planning preferences

## What It Owns

* Calendar events, time blocks, availability
* Scheduling constraints, recurring time patterns
* Conflict detection, proposed schedule changes

Does not own the meaning of a test or the contents of an email — receives that context from the appropriate manager.

## Schedule Change Workflow

1. Receives a proposed date change from another manager
2. Verifies relevant calendar information
3. Checks existing related blocks for conflicts
4. Consults Memory AI for planning preferences
5. Creates a recommended adjustment
6. Returns recommendation to Orchestrator
7. Waits for approval before making important changes

## Important Boundary

The Time Manager should suggest rather than silently rearrange important commitments.

---

# 7. School Manager

## Core Purpose

The School Manager owns the academic domain.

Its central question is:

> "What does the user need to understand, prepare, complete, or submit for school?"

## Main Responsibilities

* Tracks classes, assignments, tests, quizzes, and academic deadlines
* Understands teachers and course structures
* Connects school communications to classes
* Creates academic plans and identifies missing or late work
* Helps create recovery plans
* Requests class materials from Knowledge Manager
* Requests scheduling support from Time Manager
* Consults Memory AI for study preferences

## Academic Change Workflow

1. Communication Manager extracts a change
2. School Manager confirms the class and assessment
3. Updates its academic understanding
4. Identifies affected assignments or study plans
5. Consults Memory AI for study preferences
6. Sends Time Manager a scheduling change request
7. Sends Orchestrator an academic-impact summary

## Recovery Planning

* Clearly explains what was missed without guilt-based language
* Identifies what still matters and ranks work by consequence
* Suggests a realistic recovery plan coordinated with Time Manager
* Uses the user's task-size preference from Memory AI

## Boundary

School Manager understands the academic meaning. Knowledge Manager finds the files. Time Manager schedules the work. Memory AI explains how the user works best.

---

# 8. Goal Manager

## Core Purpose

The Goal Manager owns long-term goals, milestones, progress, and goal-related planning.

Its central question is:

> "What is the user trying to achieve over time, and are they making meaningful progress?"

## Main Responsibilities

* Stores long-term goals and breaks them into milestones
* Tracks progress and detects stalled goals
* Connects daily actions to long-term outcomes
* Suggests next steps
* Coordinates with Time Manager
* Requests relevant materials from Knowledge Manager
* Consults Memory AI for motivation and planning preferences

## Goal Structure

A goal may contain:

* Desired outcome, motivation, target date
* Milestones, current status
* Required resources, related projects
* Recurring actions, risks or blockers

## Stalled Goals

When a goal has not progressed, investigates:

* Lack of time, unclear next step, missing resources
* Goal no longer matters, goal is too large
* User prefers a different task structure, competing priorities

Does not automatically assume laziness.

## Boundary

Goal Manager owns desired outcome and progress. Time Manager owns when work occurs. Knowledge Manager owns related materials. Memory AI owns how progress and motivation should be communicated.

---

# 9. Notification Manager

## Core Purpose

The Notification Manager protects the user's attention.

Its central question is:

> "Does the user need to know this now, later, or not at all?"

## Main Responsibilities

* Receives notification requests from other managers
* Assigns urgency and groups related updates
* Respects quiet periods and prevents repetitive notifications
* Selects appropriate delivery time
* Escalates unresolved urgent items
* Consults Memory AI for interruption preferences

## Notification Levels

### Immediate
Serious schedule conflicts, time-sensitive deadlines, important cancellations, security issues, changes requiring quick decisions.

### Scheduled
Upcoming assignments, preparation reminders, planned daily summaries, goal check-ins, non-urgent follow-ups.

### Digest
General updates, low-priority emails, progress summaries, suggested organization, non-urgent opportunities.

### Silent
Information should be recorded but does not justify interrupting the user.

## Boundary

Other managers determine what an event means. The Notification Manager determines when and how it reaches the user.

---

# 10. Event-Driven Collaboration System

## Core Concept

Managers respond to both direct Orchestrator requests and external/internal events.

Examples of triggering events:

* New email received
* Calendar event changed
* Assignment added
* Deadline approaching
* Document uploaded
* Goal milestone completed
* User preference confirmed
* Schedule conflict detected

## Standard Event Workflow

1. **Event Reception** — Manager responsible for the event source receives it
2. **Event Analysis** — Determines what happened, whether it matters, which domains are affected
3. **Memory Consultation** — Requests relevant personalization from Memory AI
4. **Structured Event Creation** — Creates event containing: type, source, summary, confidence, urgency, entities, dates, affected managers, proposed actions, approval requirements
5. **Affected Manager Routing** — Event sent to relevant managers
6. **Independent Manager Analysis** — Each manager evaluates in its own domain, avoids editing another manager's data
7. **Change Requests** — Managers submit structured change requests to the manager that owns the affected data
8. **Orchestrator Assembly** — Combines findings, conflicts, proposed changes, approval needs
9. **User Approval** — User approves, rejects, or modifies proposed actions
10. **Execution and Confirmation** — Appropriate manager executes and reports completion

---

# 11. Detailed Email Change Example

A teacher emails: *"The chemistry test originally scheduled for Thursday has been moved to Friday. Students should bring their lab notebooks."*

## Communication Manager
* Summarizes email, extracts date change and lab notebook requirement
* Creates structured event: type = academic schedule change, class = chemistry, old date = Thursday, new date = Friday, required item = lab notebook, affected managers = School / Time / Notification

## School Manager
* Matches email to chemistry, updates test context
* Finding: "Current plan schedules final study session on Thursday. Test moved to Friday creates an additional review opportunity."

## Time Manager
* Checks Thursday and Friday, reviews existing study blocks
* Recommendation: "Keep Wednesday's main study block, use Thursday evening for shorter review."

## Notification Manager
* Determines immediate interruption unnecessary
* Adds update to next briefing, creates Thursday reminder to pack lab notebook

## Orchestrator
> "Your chemistry test moved from Thursday to Friday, and you need to bring your lab notebook. Your study schedule still works — keep Wednesday as your main session and use Thursday for a shorter review. Would you like the Thursday review added and a reminder to pack your notebook?"

After approval: Time Manager adds review, Notification Manager creates reminder, School Manager confirms updated plan.

---

# 12. Change Request System

## Purpose

Managers never directly overwrite another manager's records. They communicate through structured change requests.

## Change Request Contents

* Requesting manager
* Receiving manager
* Reason for the request
* Source evidence
* Proposed change
* Confidence level
* Urgency
* Whether user approval is required
* Dependencies
* Expiration or deadline

## Benefits

* Preserves clear ownership
* Prevents accidental overwrites
* Creates an audit trail
* Makes errors easier to trace
* Allows managers to disagree
* Supports user approval
* Makes future managers easier to add

---

# 13. Manager Response Contract

Every manager returns information in a consistent internal format containing:

* Summary
* Domain impact
* Confidence
* Urgency
* Recommended action
* Alternative actions
* Required approval
* Affected managers
* Supporting evidence
* Suggested notification timing
* Unresolved questions

---

# 14. Permissions and User Control

## Managers May Usually Act Without Approval

* Read connected information
* Summarize information
* Detect patterns and conflicts
* Prepare drafts
* Create recommendations and internal change requests
* Organize virtual information
* Update non-sensitive internal status

## Managers Should Require Approval Before

* Sending an email or message
* Moving an important calendar event
* Accepting an invitation
* Committing the user to an appointment
* Deleting information
* Moving or renaming files
* Changing a major goal
* Making purchases
* Sharing information externally
* Applying a newly inferred long-term memory

---

# 15. Architecture Summary

| Agent | Owns | Central Question |
|---|---|---|
| Orchestrator AI | Active conversation, routing, conflict resolution | Which managers need to participate? |
| Memory AI | How the user works, communicates, and decides | How does this person naturally operate? |
| Knowledge Manager | Documents, files, notes, information location | Where is the relevant information? |
| Communication Manager | Emails, messages, drafts, conversation state | What changed and what needs a response? |
| Time Manager | Calendar, schedule, availability, time blocks | How should the user's time be arranged? |
| School Manager | Classes, assignments, tests, academic plans | What does the user need to do for school? |
| Goal Manager | Long-term goals, milestones, progress | Is the user making meaningful progress? |
| Notification Manager | Urgency, delivery timing, interruption protection | Does the user need to know this now? |

---

# 16. Final System Philosophy

The Personal Life Manager is not one enormous AI that tries to know and control everything.

It is a coordinated organization of focused managers.

Each manager:

* Understands one domain
* Owns its own data
* Consults the Memory AI for personalization
* Communicates through events and change requests
* Provides findings to the Orchestrator
* Respects user approval boundaries

The Orchestrator makes the entire organization feel like one assistant.

The Memory AI makes the entire organization feel personal.

The specialized managers make the system capable.

Together, they create a personal management system that can understand changes, coordinate across areas of life, reduce mental overhead, and still leave the user fully in control.
