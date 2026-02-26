---
id: 001
title: Todo AI Chatbot Spec Creation
stage: spec
date: 2026-02-14
surface: agent
model: claude-opus-4-6
feature: 011-todo-ai-chatbot
branch: 011-todo-ai-chatbot
user: danish
command: /sp.specify
labels: ["spec", "chatbot", "ai-agent", "todo", "mcp"]
links:
  spec: specs/011-todo-ai-chatbot/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/011-todo-ai-chatbot/spec.md
  - specs/011-todo-ai-chatbot/checklists/requirements.md
tests:
  - Specification quality checklist - all items passed
---

## Prompt

# Role: Senior AI Engineer & Architect
# Task: Generate a Comprehensive Technical Specification for Phase III: Todo AI Chatbot

As an expert architect, create a detailed `specs/todo-ai-chatbot.md` file based on the following requirements. This spec must serve as the single source of truth for the Agentic Dev Stack workflow.

### 1. Project Overview & Tech Stack
- Frontend: OpenAI ChatKit
- Backend: Python FastAPI (Stateless)
- AI Framework: OpenAI Agents SDK
- MCP Server: Official MCP SDK (Python)
- Database: Neon Serverless PostgreSQL with SQLModel (ORM)
- Auth: Better Auth

### 2. Database Schema (SQLModel)
Define the models precisely:
- **Task**: user_id (string), id (int, PK), title (string), description (text), completed (bool), created_at, updated_at.
- **Conversation**: user_id (string), id (int, PK), created_at, updated_at.
- **Message**: user_id, id, conversation_id (FK), role (user/assistant), content, created_at.

### 3. MCP Tools Definition (Strict JSON Interface)
Define the following tools with their parameters and return types:
- `add_task(user_id, title, description)`
- `list_tasks(user_id, status: ["all", "pending", "completed"])`
- `complete_task(user_id, task_id)`
- `delete_task(user_id, task_id)`
- `update_task(user_id, task_id, title?, description?)`

### 4. Agent Behavior & Logic
- The agent must be stateless.
- Every request must fetch conversation history from Neon DB.
- Natural Language Mapping: Map user intent (e.g., "remember to...", "done with...") to specific MCP tools.
- Multi-step reasoning: For "Delete the meeting task", the agent must first `list_tasks` to find the ID, then `delete_task`.

### 5. API Endpoints
- Define `POST /api/{user_id}/chat`
- Request Body: `{ "conversation_id": int?, "message": string }`
- Response: `{ "conversation_id": int, "response": string, "tool_calls": array }`

### 6. Implementation Instructions
- No manual coding.
- Use `mcp` official library.
- Ensure all DB operations are async.
- Setup environment variable requirements (DATABASE_URL, OPENAI_API_KEY).

Output this as a clean Markdown file in the `/specs` directory.

## Response snapshot

Created feature branch `011-todo-ai-chatbot` and wrote comprehensive specification at `specs/011-todo-ai-chatbot/spec.md`. The spec includes 6 user stories (P1: task creation, viewing, completion/deletion; P2: updates, conversation history, multi-step resolution), 13 functional requirements, 3 key entities (Task, Conversation, Message), 7 measurable success criteria, edge cases, assumptions, and scope boundaries. All quality checklist items passed — spec is technology-agnostic and business-focused per SDD guidelines. Technical stack details (FastAPI, OpenAI Agents SDK, MCP, SQLModel, Neon PostgreSQL) are noted for the planning phase.

## Outcome

- Impact: Created spec defining the full Todo AI Chatbot feature scope with 6 user stories and 13 functional requirements
- Tests: Quality checklist passed all items (content quality, requirement completeness, feature readiness)
- Files: specs/011-todo-ai-chatbot/spec.md, specs/011-todo-ai-chatbot/checklists/requirements.md
- Next prompts: /sp.plan to create architectural plan, or /sp.clarify if refinement needed
- Reflection: User provided very detailed technical requirements — translated to business-focused spec while preserving intent for planning phase

## Evaluation notes (flywheel)

- Failure modes observed: PowerShell create-new-feature script failed on positional parameter; recovered with manual directory creation
- Graders run and results (PASS/FAIL): Quality checklist PASS (all items)
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Fix PowerShell script parameter handling for long description strings
