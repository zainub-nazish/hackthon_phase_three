# Implementation Plan: Todo AI Chatbot

**Branch**: `011-todo-ai-chatbot` | **Date**: 2026-02-14 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/011-todo-ai-chatbot/spec.md`

## Summary

Migrate the existing AI chatbot backend from Anthropic Claude to **OpenAI Agents SDK** with native MCP tool integration, while preserving the existing database models (Task, Conversation, Message), MCP tools (add, list, complete, delete, update), REST API endpoints, and ChatKit frontend. The backend remains 100% stateless — every request loads conversation history from Neon PostgreSQL, runs the agent, and persists the result.

## Technical Context

**Language/Version**: Python 3.11+ (backend), TypeScript 5.7 (frontend)
**Primary Dependencies**: FastAPI, OpenAI Agents SDK (`openai-agents`), MCP SDK (`mcp`), SQLModel, Next.js 16, `@openai/chatkit-react` 1.4.3
**Storage**: Neon Serverless PostgreSQL via `asyncpg` + SQLModel (async)
**Testing**: pytest + pytest-asyncio (backend), manual E2E (frontend)
**Target Platform**: Linux server (backend on HuggingFace Spaces), Vercel (frontend)
**Project Type**: Web application (frontend + backend)
**Performance Goals**: <5s end-to-end chat response, 50 concurrent users
**Constraints**: Stateless backend (no in-memory state), user-scoped data isolation
**Scale/Scope**: Single chat endpoint, 5 MCP tools, 3 DB models

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Constitution is in template state (no project-specific principles defined). No gates to enforce.
Proceeding with standard SDD practices: smallest viable diff, no hardcoded secrets, testable changes.

**Post-design re-check**: PASS — no violations introduced.

## Project Structure

### Documentation (this feature)

```text
specs/011-todo-ai-chatbot/
├── plan.md              # This file
├── research.md          # Phase 0 output — technology decisions
├── data-model.md        # Phase 1 output — entity definitions
├── quickstart.md        # Phase 1 output — setup guide
├── contracts/
│   ├── chat-api.yaml    # OpenAPI contract for chat endpoints
│   └── mcp-tools.yaml   # MCP tool interface definitions
└── tasks.md             # Phase 2 output (via /sp.tasks)
```

### Source Code (repository root)

```text
backend/
├── config.py                 # MODIFY: Replace ANTHROPIC_API_KEY → OPENAI_API_KEY
├── main.py                   # NO CHANGE: Routers already registered
├── database.py               # NO CHANGE: Async engine already configured
├── models/
│   ├── database.py           # VERIFY: Task, Conversation, Message models
│   └── schemas.py            # VERIFY: Request/response Pydantic models
├── routes/
│   ├── auth.py               # NO CHANGE
│   ├── tasks.py              # NO CHANGE
│   └── chat.py               # MODIFY: Update agent service import/usage
├── services/
│   ├── __init__.py            # NO CHANGE
│   ├── ai_agent.py           # REWRITE: Anthropic → OpenAI Agents SDK
│   ├── mcp_tools.py          # VERIFY: 5 tools match contract
│   └── mcp_bridge.py         # DELETE: Agents SDK has native MCP support
├── auth/
│   └── dependencies.py       # NO CHANGE
├── tests/
│   ├── conftest.py           # MODIFY: Update agent mocking
│   ├── test_chat.py          # MODIFY: Update for new agent interface
│   ├── test_ai_agent.py      # REWRITE: Test OpenAI Agent
│   ├── test_mcp_tools.py     # NO CHANGE
│   └── test_chat_isolation.py # NO CHANGE
└── requirements.txt          # MODIFY: Replace anthropic → openai-agents

frontend/
├── app/(dashboard)/chat/page.tsx        # NO CHANGE
├── components/chat/
│   ├── chat-container.tsx               # NO CHANGE (ChatKit integration)
│   ├── chat-error.tsx                   # NO CHANGE
│   └── chat-welcome.tsx                 # NO CHANGE
├── hooks/use-chat.ts                    # NO CHANGE
├── lib/
│   ├── chat-client.ts                   # NO CHANGE
│   └── api-client.ts                    # NO CHANGE
└── types/chat.ts                        # NO CHANGE
```

**Structure Decision**: Web application (frontend + backend). Existing structure is preserved — this feature is primarily a backend service migration (Anthropic → OpenAI Agents SDK) with minimal file changes.

## Complexity Tracking

No constitution violations. The migration is the smallest viable diff:
- 1 file rewrite (`ai_agent.py`)
- 1 file delete (`mcp_bridge.py`)
- 3 files modified (`config.py`, `requirements.txt`, `chat.py`)
- Test updates to match new interface

---

## Phase 1: Foundation — Environment & Dependencies

### Objective
Update project dependencies and environment configuration for OpenAI Agents SDK.

### Changes

1. **`backend/requirements.txt`** — Replace `anthropic>=0.79.0` with `openai-agents>=0.0.7`
2. **`backend/config.py`** — Replace `ANTHROPIC_API_KEY` / `ANTHROPIC_MODEL` with `OPENAI_API_KEY: str` environment variable
3. **`backend/.env`** — Add `OPENAI_API_KEY=sk-proj-...` (from user's env vars)
4. **`backend/.env.example`** — Document `OPENAI_API_KEY` requirement

### Validation (Definition of Done)
- [ ] `pip install -r requirements.txt` succeeds with `openai-agents` installed
- [ ] `from agents import Agent, Runner` imports without error
- [ ] `from agents.mcp import MCPServerStdio` imports without error
- [ ] `OPENAI_API_KEY` loads from environment in config
- [ ] No references to `anthropic` remain in `config.py`

---

## Phase 2: Database Models — Verify & Align

### Objective
Verify existing SQLModel models match the spec's schema exactly. No migration needed if aligned.

### Existing Models (`backend/models/database.py`)
- `Task`: owner_id, title, description, completed, created_at, updated_at
- `Conversation`: owner_id, created_at, updated_at
- `Message`: owner_id, conversation_id, role, content, created_at
- `ToolCall`: conversation_id, message_id, tool_name, parameters, result, status, created_at

### Verification Checklist
- [ ] `Task.owner_id` is string type (maps to `user_id` in spec)
- [ ] `Task.title` has max length constraint
- [ ] `Task.description` is optional text
- [ ] `Conversation.owner_id` is string type
- [ ] `Message.role` accepts "user" and "assistant"
- [ ] `Message.content` is text type
- [ ] Foreign key: `Message.conversation_id` → `Conversation.id`
- [ ] All timestamps are UTC

### Decision
The existing models use `owner_id` field name (consistent with existing routes). The spec says `user_id` — we keep `owner_id` to avoid breaking existing task CRUD routes. The MCP tools and chat route already map between `user_id` (URL param) and `owner_id` (DB field).

### Validation (Definition of Done)
- [ ] All model fields match data-model.md (accounting for `owner_id` = `user_id`)
- [ ] Database tables create successfully on startup
- [ ] Existing task CRUD operations still work

---

## Phase 3: MCP Server — Verify 5 Tools

### Objective
Verify existing MCP tools match the contract and work with OpenAI Agents SDK's `MCPServerStdio`.

### Existing Tools (`backend/services/mcp_tools.py`)
1. `add_task(title, user_id, description?)` — Creates task
2. `list_tasks(user_id, status?)` — Lists with filter
3. `complete_task(task_id, user_id)` — Marks complete
4. `delete_task(task_id, user_id)` — Deletes task
5. `update_task(task_id, user_id, updates)` — Updates fields

### Required Changes
- Verify tools expose proper JSON schema for Agents SDK discovery
- Verify `mcp_tools.py` can be invoked as a subprocess (for `MCPServerStdio`)
- Add `if __name__ == "__main__"` entry point if missing (for stdio mode)

### Tool Chaining Strategy (Multi-Step Reasoning)

The OpenAI Agent handles multi-step reasoning natively. The agent's system prompt instructs it:

> "When a user refers to a task by name or description (not by ID), you MUST first call `list_tasks` to find matching tasks, then use the returned task IDs to perform the requested operation (complete, delete, update). Never guess task IDs."

Example flow for "delete the meeting task":
1. Agent receives user message
2. Agent calls `list_tasks(user_id, status="all")` → gets task list
3. Agent identifies "Team meeting prep" as the match
4. Agent calls `delete_task(user_id, task_id=<matched_id>)` → task deleted
5. Agent responds: "I've deleted the task 'Team meeting prep'."

The Agents SDK runner handles this loop automatically — it calls tools, feeds results back to the model, and continues until the agent produces a final text response.

### Validation (Definition of Done)
- [ ] All 5 MCP tools are registered and discoverable
- [ ] `MCPServerStdio` can connect to the tool server
- [ ] Each tool enforces `user_id` isolation
- [ ] Existing `test_mcp_tools.py` tests pass

---

## Phase 4: Agent Logic — OpenAI Agents SDK Integration

### Objective
Rewrite `ai_agent.py` to use OpenAI Agents SDK with MCP tool integration, replacing Anthropic Claude.

### Architecture

```
Request → Load conversation history from DB
        → Build message list [{role, content}, ...]
        → Create Agent(name, instructions, mcp_servers)
        → Runner.run(agent, messages)    ← SDK handles tool loop
        → Extract final response text
        → Return response + tool_calls
```

### Key Design Decisions

1. **Agent is instantiated per-request** — stateless, no persistent agent instance
2. **MCP server is connected per-request** — `async with mcp_server:` context manager
3. **Conversation history is passed as messages** — full history loaded from DB
4. **System prompt defines agent behavior** — natural language → tool mapping instructions
5. **Agent handles tool chaining internally** — SDK runner loops until final response

### System Prompt Design

```
You are a helpful todo task management assistant. You help users manage their tasks
through natural conversation.

CAPABILITIES:
- Create tasks (add_task)
- List tasks with optional status filter (list_tasks)
- Mark tasks as completed (complete_task)
- Delete tasks (delete_task)
- Update task details (update_task)

RULES:
- Always use the user_id provided in tool parameters — never use a different user's ID.
- When a user refers to a task by name/description, FIRST call list_tasks to find the
  matching task ID, THEN perform the requested action.
- After any task operation, confirm what was done with specific details.
- For ambiguous requests matching multiple tasks, list the matches and ask the user
  to clarify.
- For non-task messages (greetings, questions), respond conversationally without
  calling any tools.
- Never expose internal IDs unless helpful for disambiguation.
```

### Files Changed

| File | Action | Description |
|------|--------|-------------|
| `backend/services/ai_agent.py` | REWRITE | OpenAI Agents SDK agent with MCP |
| `backend/services/mcp_bridge.py` | DELETE | Native MCP support in Agents SDK |
| `backend/routes/chat.py` | MODIFY | Update agent service call signature |
| `backend/tests/test_ai_agent.py` | REWRITE | Test new agent interface |
| `backend/tests/conftest.py` | MODIFY | Update agent mocking fixtures |

### Validation (Definition of Done)
- [ ] Agent processes a message and returns a response
- [ ] Agent calls MCP tools for task-related requests
- [ ] Agent handles multi-step tool chaining (list → delete)
- [ ] Agent responds conversationally to non-task messages
- [ ] No references to `anthropic` remain in services/
- [ ] `test_ai_agent.py` tests pass

---

## Phase 5: API Layer — Update Chat Endpoint

### Objective
Update the chat route to use the new OpenAI Agents SDK service while preserving the API contract.

### Existing Endpoint
`POST /api/v1/users/{user_id}/chat` — Already exists in `backend/routes/chat.py`

### Changes Required
1. Update import from `ai_agent.py` to new service interface
2. Ensure conversation history loading remains unchanged
3. Ensure message persistence (user + assistant) remains unchanged
4. Update response mapping if agent return type changes
5. Ensure `tool_calls` array in response is populated from agent result

### Request/Response Flow (Unchanged)
```
1. Authenticate user (Bearer token via auth dependency)
2. Verify user_id matches authenticated user (IDOR prevention)
3. Load or create conversation
4. Load conversation history (messages from DB)
5. Call agent service with user message + history
6. Save user message to DB
7. Save assistant response to DB
8. Return ChatResponse { conversation_id, response, tool_calls }
```

### Validation (Definition of Done)
- [ ] `POST /api/v1/users/{user_id}/chat` returns 200 with valid response
- [ ] Conversation auto-created for new users
- [ ] Messages persisted to database
- [ ] Tool calls recorded in response
- [ ] Auth enforcement works (401 for unauthenticated, 404 for wrong user)
- [ ] `test_chat.py` and `test_chat_isolation.py` pass

---

## Phase 6: Frontend — Verify ChatKit Integration

### Objective
Verify the existing ChatKit frontend works with the updated backend. No frontend code changes expected.

### Existing Integration
- `frontend/components/chat/chat-container.tsx` — ChatKit with authenticated fetch
- `frontend/hooks/use-chat.ts` — Loads history, sends messages via REST
- `frontend/lib/chat-client.ts` — API client for chat endpoints

### Verification
Since the API contract (request/response shape) is unchanged, the frontend should work without modification. This phase is verification only.

### Domain Allowlist
ChatKit requires domain allowlisting for the Full Proxy pattern. Ensure `NEXT_PUBLIC_CHATKIT_DOMAIN_KEY` is configured if using ChatKit's cloud proxy. If using direct API calls (current setup), no domain config needed.

### Validation (Definition of Done)
- [ ] Chat page loads without errors
- [ ] User can send a message and receive AI response
- [ ] Conversation history persists across page reloads
- [ ] Task operations work via chat ("add task", "show tasks", "complete task")
- [ ] Multi-step operations work ("delete the meeting task")
- [ ] Non-task messages get conversational responses

---

## Risk Analysis

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| OpenAI Agents SDK API changes (pre-1.0) | Medium | High | Pin exact version in requirements.txt |
| MCP stdio connection issues in production | Low | High | Add timeout and retry logic; fallback error message |
| OpenAI rate limits during peak usage | Medium | Medium | Implement retry with exponential backoff |
| Agent hallucinating tool calls | Low | Medium | System prompt constraints + user_id enforcement in tools |

## Follow-ups

1. **Performance**: Add response time logging to measure SC-001 (<5s target)
2. **Testing**: Add integration tests for full chat → agent → MCP → DB flow
3. **Monitoring**: Add observability for agent tool call patterns and error rates
