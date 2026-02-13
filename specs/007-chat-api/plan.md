# Implementation Plan: Chat API & Conversation Persistence

**Branch**: `007-chat-api` | **Date**: 2026-02-09 | **Spec**: [specs/007-chat-api/spec.md](spec.md)
**Input**: Feature specification from `/specs/007-chat-api/spec.md`

## Summary

Build a stateless backend Chat API that receives user messages, persists conversations and messages to Neon PostgreSQL, invokes an AI agent service (stub for now, real integration in Spec-6), returns AI responses, stores tool call records, and maintains conversation continuity via database. Three REST endpoints matching the frontend contract established in 006-chat-ui.

## Technical Context

**Language/Version**: Python 3.11+ (matches existing backend)
**Primary Dependencies**: FastAPI, SQLModel, asyncpg, Pydantic
**Storage**: Neon PostgreSQL (async via asyncpg, same engine as Task model)
**Testing**: pytest + pytest-asyncio + httpx + aiosqlite (in-memory SQLite for tests)
**Target Platform**: Linux server (deployed alongside existing backend)
**Project Type**: Web application (backend-only for this feature)
**Performance Goals**: <10s end-to-end response (SC-001), <2s history load for 100 messages (SC-002)
**Constraints**: Stateless architecture, user isolation enforced on all queries, max 2000 char messages
**Scale/Scope**: Single-user conversations (one active per user), tool call persistence

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

The project constitution is unfilled (template placeholders). No specific gates to enforce. Proceeding with standard best practices:

- [x] **Smallest viable change**: Only adding chat-specific code, no unrelated modifications
- [x] **No hardcoded secrets**: AI API keys via `.env`, not in code
- [x] **Test coverage**: All endpoints will have unit tests following existing patterns
- [x] **Security**: User isolation via `verify_user_owns_resource` + `owner_id` filtering
- [x] **Consistent patterns**: Following established Task model/route/schema structure exactly

**Post-Phase 1 Re-check**: All design decisions follow existing patterns. No violations.

## Project Structure

### Documentation (this feature)

```text
specs/007-chat-api/
├── plan.md              # This file
├── research.md          # Phase 0 output — all unknowns resolved
├── data-model.md        # Phase 1 output — Conversation, Message, ToolCall entities
├── quickstart.md        # Phase 1 output — setup and verification guide
├── contracts/
│   └── chat-api.yaml    # Phase 1 output — OpenAPI 3.1 specification
└── tasks.md             # Phase 2 output (/sp.tasks command)
```

### Source Code (repository root)

```text
backend/
├── models/
│   ├── database.py          # MODIFY: Add Conversation, Message, ToolCall models
│   └── schemas.py           # MODIFY: Add Chat request/response schemas
├── routes/
│   ├── tasks.py             # EXISTING: Task CRUD (unchanged)
│   └── chat.py              # NEW: Chat endpoints (POST /chat, GET /conversations, GET /messages)
├── services/
│   ├── __init__.py          # NEW: Services package init
│   └── ai_agent.py          # NEW: AI agent service interface + stub implementation
├── auth/
│   └── dependencies.py      # EXISTING: verify_user_owns_resource (unchanged)
├── main.py                  # MODIFY: Register chat router
├── config.py                # EXISTING: Settings (unchanged)
├── database.py              # EXISTING: Async session management (unchanged)
└── tests/
    ├── conftest.py           # MODIFY: Add chat-specific fixtures (conversations, messages)
    ├── test_chat.py          # NEW: Chat endpoint tests
    └── test_chat_isolation.py # NEW: Cross-user isolation tests for chat
```

**Structure Decision**: Backend-only change following the existing web application structure. New files are a route module (`chat.py`), a service module (`ai_agent.py`), and test files. Existing files receive additions (models, schemas, main.py router registration, conftest fixtures).

## Design Decisions

### D-001: AI Agent as Service Abstraction

The AI agent is encapsulated behind an `AIAgentService` class with a `generate_response(messages, user_id)` method. The initial implementation returns a stub response. This allows:
- Clean testing without external API mocks
- Spec-6 to implement the real agent by swapping the service
- The route layer to remain unchanged when the agent changes

The service is injected via FastAPI dependency injection, making it swappable in tests.

### D-002: Message Persistence Before AI Invocation

The user's message is committed to the database BEFORE calling the AI agent (FR-003). This ensures:
- The user's message is never lost, even if the AI fails
- The conversation state is always consistent
- Error recovery is straightforward (user message exists, no assistant response)

### D-003: Conversation ID as UUID String in API

The frontend sends `conversation_id` as `string | null`. The backend stores it as UUID. Pydantic handles the UUID ↔ string serialization automatically. The API contract uses string format for JSON compatibility.

### D-004: Tool Call Storage as JSON Text

Tool call `parameters` and `result` are stored as plain text (JSON-serialized strings) rather than native JSONB. This ensures compatibility with SQLite in the test environment while still being queryable as text in PostgreSQL.

### D-005: Route URL Pattern

Endpoints use `/api/v1/users/{user_id}/...` prefix matching the existing Task routes and the frontend `chat-client.ts` implementation:
- `POST /api/v1/users/{user_id}/chat`
- `GET /api/v1/users/{user_id}/conversations`
- `GET /api/v1/users/{user_id}/conversations/{conversation_id}/messages`

## Implementation Phases

### Phase 1: Database Models (Foundation)
1. Add `Conversation`, `Message`, `ToolCall` SQLModel classes to `backend/models/database.py`
2. Follow existing `Task` model patterns exactly (UUID PK, `owner_id`, timestamps)
3. Models auto-create tables via `SQLModel.metadata.create_all` in lifespan

### Phase 2: Pydantic Schemas
1. Add chat schemas to `backend/models/schemas.py`:
   - `ChatRequest` (conversation_id: Optional[UUID], message: str with validation)
   - `ChatResponse` (conversation_id: UUID, response: str)
   - `MessageResponse` (id, conversation_id, role, content, created_at)
   - `MessagesResponse` (conversation_id, messages list)
   - `ConversationResponse` (conversation_id nullable, optional timestamps)
2. Match frontend `types/chat.ts` field names exactly

### Phase 3: AI Agent Service
1. Create `backend/services/__init__.py` and `backend/services/ai_agent.py`
2. Define `AIAgentService` with `async generate_response(messages, user_id) -> AgentResponse`
3. `AgentResponse` contains `content: str` and `tool_calls: list[ToolCallData]`
4. Stub implementation returns a canned response — real integration in Spec-6

### Phase 4: Chat Route Endpoints
1. Create `backend/routes/chat.py` with three endpoints
2. `POST /chat`: Create/continue conversation, persist user message, call agent, persist response
3. `GET /conversations`: Return most recent conversation by `updated_at DESC`
4. `GET /conversations/{conversation_id}/messages`: Return all messages chronologically
5. Register router in `backend/main.py`

### Phase 5: Error Handling
1. Input validation: 400 for empty/whitespace/over-limit messages
2. Auth: 401 via existing `verify_user_owns_resource`
3. Not found: 404 for invalid/cross-user conversation access
4. AI failure: 502 when agent raises, 504 on timeout (if implemented)
5. DB failure: 503 when database unavailable (existing pattern)

### Phase 6: Testing
1. Update `conftest.py` with chat fixtures (conversations, messages, helper functions)
2. `test_chat.py`: Happy path tests for all three endpoints, validation errors, auth errors
3. `test_chat_isolation.py`: Cross-user access tests (404 for all endpoints)
4. Test AI agent failure handling (user message persisted, 502 returned)

## Risks and Mitigations

1. **AI Agent Stub Limitation**: The stub returns canned responses, which means tool call persistence can't be fully tested end-to-end until Spec-6. **Mitigation**: Test tool call persistence with direct database operations in unit tests.

2. **Frontend Contract Drift**: The frontend `chat-client.ts` uses `/api/v1/` prefix while the original contract doc uses `/api/`. **Mitigation**: Use the frontend code as the authoritative source; all endpoints match `chat-client.ts` exactly.

3. **SQLite Test Limitations**: JSON text storage works differently in SQLite vs PostgreSQL (no JSONB queries). **Mitigation**: Store as plain text, parse in application layer. No DB-level JSON queries needed for this feature.

## Complexity Tracking

No violations to justify — all design decisions follow existing patterns.

| Aspect | Decision | Justification |
|--------|----------|---------------|
| AI Agent | Stub service | Spec explicitly defers real implementation to Spec-6 |
| Tool Calls | JSON text storage | SQLite test compatibility; no complex DB queries needed |
| Conversations | One per user (API) | Spec assumption; data model supports multiple for future |
