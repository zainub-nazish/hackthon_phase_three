# Implementation Plan: Todo AI Chatbot System

**Branch**: `012-todo-ai-chatbot` | **Date**: 2026-02-21 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/012-todo-ai-chatbot/spec.md`

---

## Summary

Build a stateless, database-backed AI chat system that allows authenticated users to manage their tasks through natural conversation. Each chat request loads the last 20 messages as context, invokes an AI model with MCP tool capabilities (add/list/complete/delete/update task), persists both the user and assistant turns, and returns a structured JSON response. The system runs on two deployments sharing one database: the main backend using the OpenAI Agents SDK with MCP via stdio, and the HF Space using GPT-4o with direct function dispatch.

---

## Technical Context

**Language/Version**: Python 3.11+ (backend), TypeScript / Next.js 15 (frontend)
**Primary Dependencies**:
- FastAPI + Uvicorn (HTTP server)
- SQLModel + asyncpg (async ORM + PostgreSQL driver)
- openai-agents >= 0.0.7 (agentic loop with MCP)
- mcp >= 1.26.0 (official MCP Python SDK, stdio transport)
- openai (direct API for HF Space deployment)
- pydantic-settings (configuration)
- python-jose[cryptography] (JWT verification)

**Storage**: Neon PostgreSQL (asyncpg dialect, SSL required)
**Testing**: pytest + pytest-asyncio + httpx + aiosqlite (SQLite in-memory for tests)
**Target Platform**: Linux server (HF Space Docker), Vercel (frontend)
**Performance Goals**: AI response < 10 seconds p95 (dominated by model latency)
**Constraints**: No in-memory state — all reads/writes to DB. User isolation enforced on every query.
**Scale/Scope**: Single-user per conversation, ~10K users total

---

## Constitution Check

*GATE: Evaluated against project constitution (unfilled template — defaulting to project patterns).*

| Gate | Status | Notes |
|------|--------|-------|
| No hardcoded secrets | PASS | API keys read from env/pydantic-settings |
| User isolation enforced | PASS | All queries filter by `owner_id == user_id` |
| No in-memory state | PASS | All persistence via Neon DB |
| Tests required | PASS | pytest suite in `backend/tests/` |
| Smallest viable diff | PASS | Plan extends existing routes/models, no rewrites |
| Auth on all endpoints | PASS | `verify_user_owns_resource` dependency on all chat routes |

No violations requiring justification.

---

## Project Structure

### Documentation (this feature)

```text
specs/012-todo-ai-chatbot/
├── plan.md              ← this file
├── research.md          ← Phase 0: decisions and rationale
├── data-model.md        ← Phase 1: entity definitions and DDL
├── quickstart.md        ← Phase 1: local dev and test instructions
├── contracts/
│   └── chat-api.yaml   ← Phase 1: OpenAPI 3.1 contract
└── tasks.md             ← Phase 2 output (/sp.tasks — not yet created)
```

### Source Code

```text
backend/                            ← Main backend (FastAPI)
├── main.py                         # App entry, CORS, router registration
├── config.py                       # Settings (OPENAI_API_KEY, DATABASE_URL, etc.)
├── database.py                     # Async engine, session factory
├── auth/
│   └── dependencies.py             # verify_user_owns_resource (JWT → CurrentUser)
├── models/
│   ├── database.py                 # Task, Conversation, Message, ToolCall (SQLModel)
│   └── schemas.py                  # ChatRequest, ChatResponse, MessageResponse, etc.
├── routes/
│   └── chat.py                     # POST /chat, GET /conversations, GET /messages
├── services/
│   ├── ai_agent.py                 # Agentic loop (OpenAI Agents SDK + MCP stdio)
│   └── mcp_tools.py                # @server.tool() handlers (FastMCP)
└── tests/
    ├── conftest.py                  # Fixtures: test app, DB, auth override
    ├── test_chat.py                 # Integration: POST /chat scenarios
    ├── test_chat_isolation.py       # Security: cross-user isolation
    ├── test_mcp_tools.py            # Unit: each tool handler
    └── test_ai_agent.py             # Unit: agent stub + tool dispatch

huggies_face_three/phase_three_huggies/   ← HF Space deployment
├── main.py                               # Same contract, same routes
├── config.py                             # OPENAI_API_KEY (root-level, not used)
├── backend/
│   ├── config.py                         # Reads OPENAI_API_KEY / ANTHROPIC_API_KEY
│   ├── services/
│   │   ├── ai_agent.py                   # GPT-4o with direct function dispatch
│   │   └── mcp_tools.py                  # Same tools, called as async functions
│   └── routes/chat.py                    # Same routes
└── requirements.txt                      # openai (not openai-agents), no mcp

frontend/                           ← Next.js 15
├── src/app/(dashboard)/
│   └── chat/                       # Chat UI page
└── lib/api-client.ts               # apiClient() — attaches Bearer token
```

**Structure Decision**: Web application (Option 2). Backend and frontend are separate sub-projects sharing the same git repository. No monorepo tooling required.

---

## Architecture Decisions

### AD-1: Agentic Loop Implementation
- **Main backend**: OpenAI Agents SDK `Runner.run()` with `MCPServerStdio` subprocess.
  - SDK handles tool-call rounds automatically until `end_turn`.
  - MCP subprocess is spawned per-request; `cache_tools_list=True` avoids repeated schema fetches.
- **HF Space**: `openai.AsyncOpenAI` with a manual loop (`finish_reason == "tool_calls"` → dispatch → append tool messages → repeat).
  - Same tool functions called directly as `await tool_fn(**args)`.

### AD-2: User Isolation in Tools
- `user_id` is injected into the system prompt by the agent service, not read from user input.
- Every MCP tool function validates `owner_id == user_id` in the DB query — no trust of the model's claimed user_id without DB verification.

### AD-3: Message Persistence Order
1. User message persisted **before** AI call (so it's never lost even if the model times out).
2. Assistant message persisted **after** AI returns (with all tool calls).
3. If the AI call raises an exception, the conversation timestamp is still updated and HTTP 502 is returned.

### AD-4: Context Window
- Last 20 messages (`MAX_CONTEXT_MESSAGES = 20`) loaded by `created_at DESC LIMIT 20`, then reversed for chronological order.
- Only `user` and `assistant` roles are sent to the model — system prompt is injected separately.

### AD-5: MCP Transport Split
- Main backend: stdio transport (subprocess). Cleanest MCP separation; avoids port conflicts.
- HF Space: direct function calls. Subprocess spawning unreliable in HF free tier sandbox.

---

## Phase 0: Research

✅ Complete — see [research.md](research.md).

Key decisions resolved:
- UUID PKs (not int) — prevents enumeration
- `owner_id` column name (not `user_id`) — avoids SQL keyword collision
- 20-message context window (not 10) — covers 10 full user/assistant exchanges
- MCP stdio for main backend; direct dispatch for HF Space
- Tool call persistence via `ToolCall` table for audit trail

---

## Phase 1: Design & Contracts

✅ Complete — artifacts:

| Artifact | Path | Status |
|----------|------|--------|
| Data model | [data-model.md](data-model.md) | Done |
| OpenAPI contract | [contracts/chat-api.yaml](contracts/chat-api.yaml) | Done |
| Quickstart guide | [quickstart.md](quickstart.md) | Done |

---

## Phase 2: Tasks

➡️ Run `/sp.tasks` to generate [tasks.md](tasks.md).

**Scope for tasks.md**:
The core implementation already exists in the main backend. Tasks should focus on:
1. Verifying all existing tests pass and gaps are covered
2. Aligning HF Space `ai_agent.py` (direct dispatch) with the main backend's tool signatures
3. Adding any missing test coverage (isolation tests, edge cases from spec)
4. Confirming the end-to-end flow works on both deployments

---

## Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| OpenAI API key invalid/revoked on HF Space | High | High | `/health` endpoint exposes key status; clear error messages guide the user |
| MCP subprocess timeout in cloud deployment | Medium | Medium | `client_session_timeout_seconds=30` set; fallback to direct dispatch in HF Space |
| Conversation context too large (tokens) | Low | Medium | 20-message window is well within GPT-4o 128K context; monitor if users hit limits |
| Cross-user data leak | Low | Critical | Every DB query filters by `owner_id`; isolation tests enforce this |

---

## Open Questions (carry-forward)

- Should `completed` tasks ever be un-completable? Spec says no; current tools only set `completed=True`. Confirm before tasks.
- Should the frontend show tool call details to the user? Currently hidden in the UI — confirm UX preference.
