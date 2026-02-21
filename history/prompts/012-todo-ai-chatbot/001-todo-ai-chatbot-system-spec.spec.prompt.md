---
id: 001
title: Todo AI Chatbot System Spec
stage: spec
date: 2026-02-21
surface: agent
model: claude-sonnet-4-6
feature: 012-todo-ai-chatbot
branch: 012-todo-ai-chatbot
user: danish
command: /sp.specify
labels: ["spec","ai-chatbot","todo","mcp","openai"]
links:
  spec: specs/012-todo-ai-chatbot/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/012-todo-ai-chatbot/spec.md
  - specs/012-todo-ai-chatbot/checklists/requirements.md
tests:
  - none
---

## Prompt

# Todo AI Chatbot System Specification (Phase III)

## Overview
An AI-powered task management system using a stateless FastAPI backend, MCP (Model Context Protocol) for tool calling, and Neon PostgreSQL for persistence.

## 1. Database Schema (SQLModel)
- **Task**: `id` (int), `user_id` (str), `title` (str), `description` (str, optional), `completed` (bool), `created_at`, `updated_at`.
- **Conversation**: `id` (int), `user_id` (str), `created_at`, `updated_at`.
- **Message**: `id` (int), `conversation_id` (int, FK), `role` (user/assistant), `content` (str), `created_at`.

## 2. MCP Tools Definition
The backend must implement the Official MCP SDK to expose these tools:
- `add_task(user_id, title, description)`: Creates a new record in Neon DB.
- `list_tasks(user_id, status)`: Filters tasks (all/pending/completed) from DB.
- `complete_task(user_id, task_id)`: Marks `completed=True`.
- `delete_task(user_id, task_id)`: Removes task record.
- `update_task(user_id, task_id, title, description)`: Updates task fields.

## 3. Agent Logic (OpenAI Agents SDK)
- **State Management**: On every POST request to `/api/{user_id}/chat`, fetch the last 10 messages from the `Message` table to build context.
- **Tool Usage**: The agent must intelligently map natural language (e.g., "I'm done with the milk") to the `complete_task` tool.
- **Statelessness**: No in-memory dictionaries. Every action must read/write to Neon DB.

## 4. API Endpoint
- **POST `/api/{user_id}/chat`**
  - Input: `{"message": "string", "conversation_id": "int?"}`
  - Logic: Save User Message -> Run Agent -> Agent calls MCP Tool -> Save Assistant Response -> Return JSON.

## Response snapshot

Created branch `012-todo-ai-chatbot` (next after existing `011-todo-ai-chatbot`). Wrote full spec to `specs/012-todo-ai-chatbot/spec.md` covering:
- 5 prioritised user stories (create, list, complete, delete, update tasks via natural language)
- 12 functional requirements (FR-001–FR-012)
- 7 measurable, technology-agnostic success criteria (SC-001–SC-007)
- Key entities: Task, Conversation, Message
- Edge cases, assumptions, and explicit out-of-scope items
- Quality checklist at `checklists/requirements.md` — all items pass

## Outcome

- ✅ Impact: Spec complete and validated for 012-todo-ai-chatbot. No NEEDS CLARIFICATION markers. Ready for /sp.plan.
- 🧪 Tests: none (spec stage)
- 📁 Files: specs/012-todo-ai-chatbot/spec.md, specs/012-todo-ai-chatbot/checklists/requirements.md
- 🔁 Next prompts: /sp.plan — generate architecture and implementation plan
- 🧠 Reflection: User description was detailed and technically precise; all requirements mapped cleanly to user-facing stories with no ambiguity requiring clarification.

## Evaluation notes (flywheel)

- Failure modes observed: none
- Graders run and results (PASS/FAIL): checklist all-pass on first iteration
- Prompt variant (if applicable): none
- Next experiment (smallest change to try): run /sp.plan to generate architecture decisions for the agentic loop and MCP tool dispatch
