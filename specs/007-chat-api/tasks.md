# Tasks: Chat API & Conversation Persistence

**Input**: Design documents from `/specs/007-chat-api/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/chat-api.yaml

**Tests**: Included — spec requires test coverage (Constitution Check: "All endpoints will have unit tests following existing patterns").

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app (backend-only)**: `backend/` at repository root
- Models: `backend/models/database.py`, `backend/models/schemas.py`
- Routes: `backend/routes/chat.py`
- Services: `backend/services/ai_agent.py`
- Tests: `backend/tests/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the new files and package structure needed by all user stories.

- [X] T001 Create services package with `backend/services/__init__.py` (empty init file)
- [X] T002 [P] Add Conversation SQLModel to `backend/models/database.py` — fields: `id` (UUID PK, default uuid4), `owner_id` (str, indexed, NOT NULL), `created_at` (datetime, default utcnow), `updated_at` (datetime, default utcnow). Table name: `conversations`. Follow existing Task model pattern exactly.
- [X] T003 [P] Add Message SQLModel to `backend/models/database.py` — fields: `id` (UUID PK, default uuid4), `conversation_id` (UUID, FK to conversations.id, indexed), `role` (str, max 20), `content` (str, NOT NULL), `created_at` (datetime, default utcnow). Table name: `messages`.
- [X] T004 [P] Add ToolCall SQLModel to `backend/models/database.py` — fields: `id` (UUID PK, default uuid4), `message_id` (UUID, FK to messages.id, indexed), `tool_name` (str, max 100), `parameters` (str, JSON text), `result` (str, JSON text), `status` (str, max 20), `created_at` (datetime, default utcnow). Table name: `tool_calls`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Pydantic schemas, AI agent service interface, and test fixtures that MUST be complete before ANY user story endpoint can be implemented.

**CRITICAL**: No user story work can begin until this phase is complete.

- [X] T005 Add chat Pydantic schemas to `backend/models/schemas.py` — `ChatRequest` (conversation_id: Optional[UUID], message: str with min_length=1, max_length=2000, strip_whitespace validation), `ChatResponse` (conversation_id: UUID, response: str). Must match `frontend/types/chat.ts` field names exactly.
- [X] T006 [P] Add message/conversation Pydantic response schemas to `backend/models/schemas.py` — `MessageResponse` (id: UUID, conversation_id: UUID, role: str, content: str, created_at: datetime, from_attributes=True), `MessagesResponse` (conversation_id: UUID, messages: list[MessageResponse]), `ConversationResponse` (conversation_id: Optional[UUID], created_at: Optional[datetime], updated_at: Optional[datetime]).
- [X] T007 [P] Create AI agent service stub in `backend/services/ai_agent.py` — define `AgentResponse` dataclass (content: str, tool_calls: list), `AIAgentService` class with `async generate_response(messages: list, user_id: str) -> AgentResponse` that returns a canned stub response. Add `get_ai_agent_service()` FastAPI dependency function.
- [X] T008 [P] Create chat route module skeleton in `backend/routes/chat.py` — APIRouter with `prefix="/api/v1/users/{user_id}"`, `tags=["Chat"]`. Import `verify_user_owns_resource`, `get_db_session` pattern (same as tasks.py). Define `get_db_session()` dependency matching the tasks.py pattern.
- [X] T009 Register chat router in `backend/main.py` — import `backend.routes.chat` and call `app.include_router(chat.router)` after existing router registrations.
- [X] T010 [P] Add chat test fixtures to `backend/tests/conftest.py` — helper functions to create test conversations and messages in the DB. Add `create_test_conversation(session, owner_id)` and `create_test_message(session, conversation_id, role, content)` async helper functions.

**Checkpoint**: Foundation ready — all models, schemas, service interface, and route skeleton in place. User story implementation can begin.

---

## Phase 3: User Story 1 — Send a Chat Message and Receive AI Response (Priority: P1) MVP

**Goal**: An authenticated user sends a message, the system creates/continues a conversation, invokes the AI agent stub, persists both messages, and returns the AI response with a conversation_id.

**Independent Test**: Send POST `/api/v1/users/{user_id}/chat` with `{"message": "Hello"}` → verify conversation created, user message persisted, AI response returned with `conversation_id` and `response` fields.

**Functional Requirements**: FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-009, FR-010, FR-014, FR-015, FR-016

### Tests for User Story 1

- [X] T011 [P] [US1] Write test `test_send_message_new_conversation` in `backend/tests/test_chat.py` — POST with `conversation_id=null` returns 200 with new `conversation_id` (UUID) and `response` (non-empty string). Verify conversation and messages created in DB.
- [X] T012 [P] [US1] Write test `test_send_message_existing_conversation` in `backend/tests/test_chat.py` — create conversation first, then POST with that `conversation_id`. Verify response uses same `conversation_id`, message appended, `updated_at` refreshed.
- [X] T013 [P] [US1] Write test `test_send_message_empty_returns_400` in `backend/tests/test_chat.py` — POST with `message: ""` or whitespace returns 400. Also test message exceeding 2000 chars returns 400/422.
- [X] T014 [P] [US1] Write test `test_send_message_invalid_conversation_returns_404` in `backend/tests/test_chat.py` — POST with non-existent `conversation_id` returns 404.
- [X] T015 [P] [US1] Write test `test_send_message_unauthenticated_returns_401` in `backend/tests/test_chat.py` — POST without auth header returns 401.

### Implementation for User Story 1

- [X] T016 [US1] Implement `POST /chat` endpoint in `backend/routes/chat.py` — full flow: validate input, create or verify conversation (with owner_id check), persist user message (role="user"), load last 20 messages as context, call `AIAgentService.generate_response()`, persist assistant message (role="assistant"), persist any tool calls, update `conversation.updated_at`, return `ChatResponse`. On AI failure: user message already persisted, return 502.
- [X] T017 [US1] Add custom message validation in `POST /chat` handler in `backend/routes/chat.py` — strip whitespace and check non-empty before processing (FR-009). Return 400 with `{"detail": "Message cannot be empty"}` for empty/whitespace-only input. Pydantic handles max_length.

**Checkpoint**: User Story 1 complete. Users can send messages and receive AI (stub) responses. New conversations auto-created. Run `pytest backend/tests/test_chat.py -v -k "send_message"` to validate.

---

## Phase 4: User Story 2 — Retrieve Conversation History (Priority: P2)

**Goal**: An authenticated user can retrieve their most recent conversation and load its full message history for conversation continuity across page reloads.

**Independent Test**: Create conversation + messages via US1, then GET `/conversations` returns most recent conversation, GET `/conversations/{id}/messages` returns all messages chronologically.

**Functional Requirements**: FR-007, FR-008, FR-010, FR-011

### Tests for User Story 2

- [X] T018 [P] [US2] Write test `test_get_recent_conversation_exists` in `backend/tests/test_chat.py` — create a conversation, GET `/conversations` returns `conversation_id`, `created_at`, `updated_at`.
- [X] T019 [P] [US2] Write test `test_get_recent_conversation_none` in `backend/tests/test_chat.py` — user with no conversations, GET `/conversations` returns `conversation_id: null`.
- [X] T020 [P] [US2] Write test `test_get_messages_chronological` in `backend/tests/test_chat.py` — create conversation with multiple messages, GET `/conversations/{id}/messages` returns all messages ordered by `created_at` ASC with correct `id`, `conversation_id`, `role`, `content`, `created_at`.
- [X] T021 [P] [US2] Write test `test_get_messages_invalid_conversation_returns_404` in `backend/tests/test_chat.py` — GET messages for non-existent conversation_id returns 404.

### Implementation for User Story 2

- [X] T022 [US2] Implement `GET /conversations` endpoint in `backend/routes/chat.py` — query conversations where `owner_id == user_id`, order by `updated_at DESC`, limit 1. Return `ConversationResponse` with conversation_id/timestamps, or `conversation_id: null` if none.
- [X] T023 [US2] Implement `GET /conversations/{conversation_id}/messages` endpoint in `backend/routes/chat.py` — verify conversation exists AND `owner_id == user_id` (404 if not), query all messages where `conversation_id` matches, order by `created_at ASC`. Return `MessagesResponse`.

**Checkpoint**: User Story 2 complete. Frontend can load conversation state on page reload. Run `pytest backend/tests/test_chat.py -v -k "conversation"` to validate.

---

## Phase 5: User Story 3 — AI Agent Invocation with Tool Execution (Priority: P3)

**Goal**: When the AI agent determines a tool call is needed, the system executes it, stores tool call details, and returns a confirmation response. (Stub implementation — tool execution deferred to Spec-6.)

**Independent Test**: The AI agent stub can be configured to return tool call data; verify ToolCall records are persisted in DB with correct `tool_name`, `parameters`, `result`, `status`, linked to the assistant message.

**Functional Requirements**: FR-013

### Tests for User Story 3

- [X] T024 [P] [US3] Write test `test_tool_call_persisted` in `backend/tests/test_chat.py` — configure AI agent stub to return a tool call in its response, send a message, verify ToolCall record created in DB linked to the assistant message with correct `tool_name`, `parameters` (JSON), `result` (JSON), `status`.
- [X] T025 [P] [US3] Write test `test_tool_call_failure_persisted` in `backend/tests/test_chat.py` — configure AI agent stub to return a failed tool call, verify ToolCall record has `status="error"` and the error info in `result`.

### Implementation for User Story 3

- [X] T026 [US3] Enhance tool call persistence in `POST /chat` handler in `backend/routes/chat.py` — after receiving `AgentResponse`, iterate `response.tool_calls`, create `ToolCall` records with `message_id` pointing to the assistant message, serialize `parameters` and `result` as JSON strings, persist to DB.
- [X] T027 [US3] Add tool call stub configuration to `backend/services/ai_agent.py` — add a method or parameter to `AIAgentService` that allows tests to configure tool call responses (e.g., `set_stub_response(content, tool_calls)`). This enables US3 tests without a real AI agent.

**Checkpoint**: User Story 3 complete. Tool calls are persisted when the AI agent returns them. Run `pytest backend/tests/test_chat.py -v -k "tool_call"` to validate.

---

## Phase 6: User Story 4 — Conversation Data Integrity and Isolation (Priority: P4)

**Goal**: Verify that each user can only access their own conversations/messages, and the system handles AI agent failures without corrupting conversation state.

**Independent Test**: Create conversations for two users, verify cross-access returns 404 on all endpoints. Simulate AI failure, verify user message persisted and conversation intact.

**Functional Requirements**: FR-011, FR-012, FR-016

### Tests for User Story 4

- [X] T028 [P] [US4] Write test `test_cross_user_chat_returns_404` in `backend/tests/test_chat_isolation.py` — user A creates conversation, user B sends message with user A's conversation_id → 404.
- [X] T029 [P] [US4] Write test `test_cross_user_conversations_returns_404` in `backend/tests/test_chat_isolation.py` — user A has conversations, user B calls GET `/conversations` → only sees their own (or null).
- [X] T030 [P] [US4] Write test `test_cross_user_messages_returns_404` in `backend/tests/test_chat_isolation.py` — user B tries to GET messages for user A's conversation → 404.
- [X] T031 [P] [US4] Write test `test_ai_failure_preserves_user_message` in `backend/tests/test_chat_isolation.py` — configure AI agent to raise an exception, send message, verify user message persisted in DB, API returns 502, no assistant message created, conversation state valid.

### Implementation for User Story 4

- [X] T032 [US4] Add AI agent failure handling in `POST /chat` in `backend/routes/chat.py` — wrap agent call in try/except, on failure: user message already committed, return `HTTPException(502, "AI service unavailable")`. Ensure no partial assistant message or tool call records.
- [X] T033 [US4] Verify all chat queries filter by `owner_id` in `backend/routes/chat.py` — audit all three endpoints: POST /chat (conversation lookup), GET /conversations, GET /messages. Every query must include `.where(Conversation.owner_id == user_id)`.

**Checkpoint**: User Story 4 complete. Cross-user isolation verified. AI failures handled gracefully. Run `pytest backend/tests/test_chat_isolation.py -v` to validate.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final validation and edge case coverage.

- [X] T034 [P] Add edge case tests in `backend/tests/test_chat.py` — test message exactly at 2000 char limit (should succeed), test message at 2001 chars (should fail 400/422), test unauthenticated access on all three endpoints (401).
- [X] T035 Run full test suite and verify all tests pass — `python -m pytest backend/tests/ -v`. Verify no regressions in existing task tests.
- [ ] T036 Run quickstart.md validation — start server with `uvicorn backend.main:app`, manually test all three endpoints with curl commands from `specs/007-chat-api/quickstart.md`.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 (models must exist before schemas reference them)
- **User Story 1 (Phase 3)**: Depends on Phase 2 — BLOCKS Phase 4 (US2 needs conversations created by US1 for testing)
- **User Story 2 (Phase 4)**: Depends on Phase 2 — can start after Foundational but US2 integration tests benefit from US1
- **User Story 3 (Phase 5)**: Depends on Phase 2 and T016 (POST /chat must exist to test tool call persistence)
- **User Story 4 (Phase 6)**: Depends on all three endpoints being implemented (Phases 3-4)
- **Polish (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

- **US1 (P1 — MVP)**: Can start after Foundational (Phase 2). No dependencies on other stories.
- **US2 (P2)**: Can start after Foundational (Phase 2). Integration testing benefits from US1 but is independently testable via direct DB setup.
- **US3 (P3)**: Depends on POST /chat endpoint from US1 (T016). Tool call persistence hooks into the same handler.
- **US4 (P4)**: Depends on all three endpoints (US1 + US2). Isolation tests exercise all endpoints.

### Within Each User Story

1. Tests written first (if included)
2. Implementation tasks in dependency order
3. Story checkpoint validates independently

### Parallel Opportunities

**Phase 1** (all parallel — different models in same file but independent sections):
```
T002 + T003 + T004 (three model classes, can be written in parallel)
```

**Phase 2** (after Phase 1):
```
T005 + T006 (schemas, same file but independent sections)
T007 + T008 + T010 (different files, fully parallel)
```

**Phase 3 tests** (all parallel — independent test functions):
```
T011 + T012 + T013 + T014 + T015
```

**Phase 4 tests** (all parallel):
```
T018 + T019 + T020 + T021
```

**Phase 6 tests** (all parallel — different test file):
```
T028 + T029 + T030 + T031
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T004)
2. Complete Phase 2: Foundational (T005-T010)
3. Complete Phase 3: User Story 1 (T011-T017)
4. **STOP and VALIDATE**: Test US1 independently — user can send message and get AI stub response
5. Deploy/demo if ready — frontend can connect and chat

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add US1 → Test → Deploy (MVP! Frontend can chat with stub AI)
3. Add US2 → Test → Deploy (Conversation history loads on page reload)
4. Add US3 → Test → Deploy (Tool calls persisted for future AI integration)
5. Add US4 → Test → Deploy (Security hardened, AI failure handling verified)
6. Polish → Full test suite green → Production ready

---

## Summary

| Metric | Value |
|--------|-------|
| **Total tasks** | 36 |
| **Phase 1 (Setup)** | 4 tasks |
| **Phase 2 (Foundational)** | 6 tasks |
| **Phase 3 (US1 — MVP)** | 7 tasks (5 tests + 2 impl) |
| **Phase 4 (US2)** | 6 tasks (4 tests + 2 impl) |
| **Phase 5 (US3)** | 4 tasks (2 tests + 2 impl) |
| **Phase 6 (US4)** | 6 tasks (4 tests + 2 impl) |
| **Phase 7 (Polish)** | 3 tasks |
| **Parallel opportunities** | 22 tasks marked [P] |
| **MVP scope** | Phases 1-3 (17 tasks) |
| **Files created** | 4 new (chat.py, ai_agent.py, test_chat.py, test_chat_isolation.py) |
| **Files modified** | 4 existing (database.py, schemas.py, main.py, conftest.py) |

## Notes

- [P] tasks = different files or independent sections, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable
- AI agent is a stub — real implementation comes in Spec-6
- All queries MUST filter by `owner_id` for security (return 404, never 403)
- Commit after each phase or logical task group
