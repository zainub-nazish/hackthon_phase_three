# Tasks: Todo AI Chatbot System

**Input**: Design documents from `/specs/012-todo-ai-chatbot/`
**Branch**: `012-todo-ai-chatbot`
**Date**: 2026-02-21
**Prerequisites**: plan.md ✅ | spec.md ✅ | research.md ✅ | data-model.md ✅ | contracts/chat-api.yaml ✅

**Note**: Core backend implementation already exists in `backend/`. Tasks focus on verification, test coverage gaps, HF Space alignment, and spec edge cases.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no incomplete dependencies)
- **[Story]**: User story this task belongs to (US1–US5)

---

## Phase 1: Setup — Verify Project Structure

**Purpose**: Confirm the existing project matches the plan.md structure and all dependencies are installed.

- [X] T001 Verify `backend/requirements.txt` includes all required packages: `fastapi`, `openai-agents`, `mcp`, `sqlmodel`, `asyncpg`, `pydantic-settings`, `pytest`, `pytest-asyncio`, `httpx`, `aiosqlite`
- [X] T002 [P] Confirm `backend/tests/conftest.py` sets up in-memory SQLite, test app, and auth override for all test files
- [X] T003 [P] Run existing test suite `pytest backend/tests/ -v` and record which tests pass and which fail — note all failures for later tasks

---

## Phase 2: Foundational — DB Models, Auth, Config

**Purpose**: Core infrastructure that all user stories depend on. Must be verified before story tasks begin.

**⚠️ CRITICAL**: All story phases depend on this phase being complete and passing.

- [X] T004 Verify `backend/models/database.py` defines all 4 entities from data-model.md: `Task` (UUID pk, owner_id, title, description, completed, created_at, updated_at), `Conversation` (UUID pk, owner_id, created_at, updated_at), `Message` (UUID pk, conversation_id FK, role, content, created_at), `ToolCall` (UUID pk, message_id FK, tool_name, parameters, result, status)
- [X] T005 [P] Verify `backend/models/schemas.py` defines `ChatRequest` (message, conversation_id?), `ChatResponse` (conversation_id, response, tool_calls), `MessageResponse`, `MessagesResponse`, `ConversationResponse` matching `contracts/chat-api.yaml`
- [X] T006 [P] Verify `backend/auth/dependencies.py` `verify_user_owns_resource` checks JWT `sub` claim against URL `user_id` param and rejects mismatches with HTTP 403
- [X] T007 Verify `backend/config.py` reads `OPENAI_API_KEY`, `DATABASE_URL`, `BETTER_AUTH_URL`, `BETTER_AUTH_SECRET` from env and `backend/.env` via pydantic-settings — confirm no key defaults to a hardcoded secret
- [X] T008 Verify `backend/routes/chat.py` registers all 3 endpoints from `contracts/chat-api.yaml`: `POST /api/v1/users/{user_id}/chat`, `GET /api/v1/users/{user_id}/conversations`, `GET /api/v1/users/{user_id}/conversations/{conversation_id}/messages`

**Checkpoint**: All 4 DB models verified, auth working, 3 endpoints registered — user story implementation can proceed.

---

## Phase 3: User Story 1 — Create a Task via Chat (Priority: P1) 🎯 MVP

**Goal**: A user sends a natural language message; the assistant creates a task in the DB and confirms by name.

**Independent Test**: `POST /api/v1/users/{user_id}/chat` with `{"message": "Add buy milk"}` → task row exists in DB with `title="buy milk"`, response contains confirmation text, `conversation_id` is returned.

### Implementation

- [X] T009 [US1] Verify `backend/services/mcp_tools.py` `add_task()` strips whitespace from `title`, validates max 200 chars, creates a `Task` row with `owner_id=user_id`, and returns `{id, title, description, completed}` — if any validation fails, returns `{"is_error": true, "error": "..."}` without writing to DB
- [X] T010 [US1] Verify `backend/services/ai_agent.py` agentic loop: when AI calls `add_task` tool, the result is fed back and the model produces a final confirmation message before returning `AgentResponse`
- [X] T011 [US1] Verify `backend/routes/chat.py` `send_message`: persists user message **before** calling agent, persists assistant message + tool calls **after**, returns `ChatResponse` with `conversation_id`, `response`, and `tool_calls` list
- [X] T012 [US1] Add test in `backend/tests/test_chat.py`: POST `/chat` with `{"message": "Add buy milk"}` → HTTP 200, `conversation_id` is UUID, `response` is non-empty string, at least one tool_call with `tool_name="add_task"` and `status="success"`
- [X] T013 [US1] Add test in `backend/tests/test_chat.py`: POST `/chat` with `{"message": ""}` (empty after strip) → HTTP 400, no task created in DB
- [X] T014 [US1] Add test in `backend/tests/test_chat.py`: POST `/chat` without `conversation_id` → new `Conversation` row created in DB, `conversation_id` in response matches the new row
- [X] T015 [US1] Add test in `backend/tests/test_chat.py`: POST `/chat` with `conversation_id` of existing conversation → no new Conversation created, message appended to same conversation

**Checkpoint**: User can create a task through natural language chat. US1 is independently testable.

---

## Phase 4: User Story 2 — List and View Tasks via Chat (Priority: P2)

**Goal**: User asks "What are my tasks?" and the assistant returns a readable list filtered by status.

**Independent Test**: Create 3 tasks, POST `/chat` with `{"message": "Show my pending tasks"}` → response text contains the 3 task titles, no completed tasks shown.

### Implementation

- [X] T016 [US2] Verify `backend/services/mcp_tools.py` `list_tasks()` filters by `owner_id=user_id` and `status` param (`all`/`pending`/`completed`), returns `{tasks: [{id, title, description, completed}...], count: int}` — no tasks from other users appear
- [X] T017 [US2] Add test in `backend/tests/test_mcp_tools.py`: `list_tasks(user_id, status="pending")` with 2 pending + 1 completed tasks → returns only 2 tasks
- [X] T018 [US2] Add test in `backend/tests/test_mcp_tools.py`: `list_tasks(user_id, status="completed")` → returns only completed tasks
- [ ] T019 [US2] Add test in `backend/tests/test_chat.py`: POST `/chat` with `{"message": "What tasks do I have?"}` → response lists task titles, tool_calls contains `list_tasks` entry with `status="success"` — deferred (requires live OpenAI key for NL→tool routing)
- [ ] T020 [US2] Add test in `backend/tests/test_chat.py`: POST `/chat` when user has no tasks and asks "Show my tasks" → response indicates no tasks (friendly message), HTTP 200, no tool error — deferred (requires live OpenAI key)

**Checkpoint**: User can list tasks filtered by status. US2 independently testable alongside US1.

---

## Phase 5: User Story 3 — Complete a Task via Natural Language (Priority: P3)

**Goal**: User says "I'm done with buy milk" → assistant finds the task by name, marks it complete, confirms.

**Independent Test**: Create task "buy milk", POST `/chat` with `{"message": "I'm done with buy milk"}` → DB row has `completed=True`, response confirms by task name.

### Implementation

- [X] T021 [US3] Verify `backend/services/mcp_tools.py` `complete_task()` validates UUID format, queries by `id=task_uuid AND owner_id=user_id`, sets `completed=True` and `updated_at=now()`, returns `{id, title, completed: true}` — returns `is_error` if not found or wrong user
- [X] T022 [US3] Verify `backend/services/ai_agent.py` system prompt instructs the model to call `list_tasks` first when user refers to a task by name (not ID), then call `complete_task` with the found `task_id` — multi-step agentic loop handles both calls in one request
- [X] T023 [US3] Add test in `backend/tests/test_mcp_tools.py`: `complete_task(task_id=valid_uuid, user_id=owner)` → returns `{completed: true}`, DB row updated
- [X] T024 [US3] Add test in `backend/tests/test_mcp_tools.py`: `complete_task(task_id=valid_uuid, user_id=OTHER_user)` → returns `{is_error: true}`, DB row unchanged
- [ ] T025 [US3] Add test in `backend/tests/test_chat.py`: POST `/chat` with `{"message": "I am done with buy milk"}` after creating that task → `tool_calls` contains `list_tasks` then `complete_task`, DB row has `completed=True` — deferred (requires live OpenAI key)

**Checkpoint**: User can complete tasks by name. Multi-step agent loop works. US3 independently testable.

---

## Phase 6: User Story 4 — Delete a Task via Chat (Priority: P4)

**Goal**: User says "Delete the dentist task" → assistant finds it by name, deletes it, confirms.

**Independent Test**: Create task "dentist appointment", POST `/chat` with `{"message": "Delete the dentist task"}` → task row no longer exists in DB, response confirms deletion.

### Implementation

- [X] T026 [US4] Verify `backend/services/mcp_tools.py` `delete_task()` validates UUID format, queries by `id AND owner_id`, deletes the row, returns `{deleted: true, id, title}` — returns `is_error` if not found
- [X] T027 [US4] Add test in `backend/tests/test_mcp_tools.py`: `delete_task(task_id=valid_uuid, user_id=owner)` → returns `{deleted: true}`, task row gone from DB
- [X] T028 [US4] Add test in `backend/tests/test_mcp_tools.py`: `delete_task(task_id=valid_uuid, user_id=OTHER_user)` → returns `{is_error: true}`, task row still exists
- [ ] T029 [US4] Add test in `backend/tests/test_chat.py`: POST `/chat` "Delete the dentist task" after creating it → `tool_calls` contains `list_tasks` then `delete_task`, task not in DB after response — deferred (requires live OpenAI key)

**Checkpoint**: User can delete tasks by name. US4 independently testable.

---

## Phase 7: User Story 5 — Update a Task via Chat (Priority: P5)

**Goal**: User says "Rename buy milk to buy whole milk" → assistant updates the task title, confirms.

**Independent Test**: Create task "buy milk", POST `/chat` with `{"message": "Rename buy milk to buy whole milk"}` → DB row has `title="buy whole milk"`, original description unchanged.

### Implementation

- [X] T030 [US5] Verify `backend/services/mcp_tools.py` `update_task()` accepts optional `title` and optional `description`, requires at least one, validates title max 200 chars, updates only provided fields, sets `updated_at=now()`, returns updated task — returns `is_error` if not found or wrong user
- [X] T031 [US5] Add test in `backend/tests/test_mcp_tools.py`: `update_task(task_id, user_id, title="new title")` → only title changes in DB, description unchanged
- [X] T032 [US5] Add test in `backend/tests/test_mcp_tools.py`: `update_task(task_id, user_id)` (no title or description) → returns `{is_error: true}`
- [ ] T033 [US5] Add test in `backend/tests/test_chat.py`: POST `/chat` "Rename buy milk to buy whole milk" → `tool_calls` contains `list_tasks` then `update_task`, DB row has new title — deferred (requires live OpenAI key)

**Checkpoint**: All 5 user stories implemented and independently testable.

---

## Phase 8: Security — User Isolation

**Purpose**: Enforce that no user can read, modify, or delete another user's data (SC-007).

- [X] T034 Verify `backend/tests/test_chat_isolation.py` covers: User A cannot POST to `/api/v1/users/{userB_id}/chat` (HTTP 403)
- [X] T035 [P] Add test in `backend/tests/test_chat_isolation.py`: User A's tasks do not appear in User B's `list_tasks` results even when both have tasks
- [X] T036 [P] Add test in `backend/tests/test_chat_isolation.py`: User A cannot `complete_task` on User B's task — `mcp_tools.complete_task(task_id=userB_task, user_id=userA)` returns `{is_error: true}`
- [X] T037 [P] Add test in `backend/tests/test_chat_isolation.py`: User A cannot access User B's conversation messages via `GET /conversations/{convB_id}/messages` (HTTP 404)

**Checkpoint**: All isolation boundaries verified by tests.

---

## Phase 9: HF Space Alignment

**Purpose**: Ensure the HF Space deployment (`huggies_face_three/`) is in sync with the main backend's API contract and tool signatures.

- [X] T038 Verify `huggies_face_three/phase_three_huggies/backend/config.py` reads `OPENAI_API_KEY` via `settings.openai_api_key` (not `anthropic_api_key`) — confirm health endpoint at `/health` shows `"ai_key": "ok"` for a valid key
- [X] T039 Verify `huggies_face_three/phase_three_huggies/backend/services/ai_agent.py` GPT-4o agentic loop: `finish_reason == "tool_calls"` triggers dispatch → tool results appended as `role="tool"` messages → loop continues until `finish_reason == "stop"`
- [X] T040 Verify `huggies_face_three/phase_three_huggies/backend/services/mcp_tools.py` defines the same 5 functions (`add_task`, `list_tasks`, `complete_task`, `delete_task`, `update_task`) as async functions callable directly (not via MCP stdio)
- [X] T041 Verify `huggies_face_three/phase_three_huggies/requirements.txt` lists `openai` (not `anthropic`, not `openai-agents`) as the AI dependency — confirm `openai-agents` is NOT listed (HF Space uses direct dispatch)
- [X] T042 Confirm `huggies_face_three/phase_three_huggies/main.py` `/health` response checks `settings.openai_api_key` and returns `"ai_key": "ok"` when format is valid (`sk-...`)

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: Edge cases, context window, error paths, and end-to-end validation.

- [X] T043 [P] Verify `MAX_CONTEXT_MESSAGES = 20` in `backend/routes/chat.py` — add test that sends 25 messages to a conversation and confirms only the last 20 are passed to the agent (use stub agent to inspect the messages list)
- [X] T044 [P] Add test in `backend/tests/test_chat.py`: POST `/chat` with `conversation_id` that does not exist → HTTP 404
- [X] T045 [P] Add test in `backend/tests/test_chat.py`: POST `/chat` with `conversation_id` belonging to a different user → HTTP 404 (not 403, to avoid leaking existence)
- [X] T046 Verify `backend/services/ai_agent.py` graceful fallback: when `OPENAI_API_KEY` is not set (`settings.openai_api_key` is None/empty), `generate_response()` returns stub `AgentResponse` without calling the OpenAI API
- [X] T047 [P] Run the full test suite `pytest backend/tests/ -v --tb=short` — all tests must pass. Fix any failures before marking phase complete
- [ ] T048 Run quickstart validation: start backend locally (`uvicorn backend.main:app --reload`), send a cURL request per `quickstart.md` examples, confirm end-to-end task creation and listing works
- [X] T049 [P] Confirm `GET /api/v1/users/{user_id}/conversations` returns `conversation_id: null` (not a 404) when user has no conversations
- [ ] T050 Push all changes to GitHub (`003-frontend-app` branch) and confirm Vercel frontend deploy succeeds

---

## Dependencies & Execution Order

### Phase Dependencies

```
Phase 1 (Setup)
  └─► Phase 2 (Foundational) ─► BLOCKS ALL STORIES
         ├─► Phase 3 (US1 - Create Task)   ← MVP
         ├─► Phase 4 (US2 - List Tasks)
         ├─► Phase 5 (US3 - Complete Task)
         ├─► Phase 6 (US4 - Delete Task)
         └─► Phase 7 (US5 - Update Task)
                   All ─► Phase 8 (Isolation)
                   All ─► Phase 9 (HF Space)
                   All ─► Phase 10 (Polish)
```

### User Story Dependencies

- **US1 (P1)**: No dependencies on other stories — start first
- **US2 (P2)**: Independent — `list_tasks` tool exists separately from `add_task`
- **US3 (P3)**: Builds on US1/US2 (needs tasks to exist, needs list to find by name)
- **US4 (P4)**: Builds on US1/US2 (same pattern as US3)
- **US5 (P5)**: Builds on US1/US2 (same pattern as US3/US4)

### Parallel Opportunities (within phases)

- T002, T003: parallel (different files)
- T005, T006: parallel (schemas vs auth)
- T017, T018: parallel (different status filters)
- T027, T028: parallel (success vs isolation test)
- T035, T036, T037: parallel (different isolation scenarios)
- T043, T044, T045, T046, T047, T049: parallel (all different test scenarios)

---

## Parallel Execution Example: User Story 1

```bash
# Parallel — run simultaneously:
Task T009: Verify mcp_tools.py add_task() in backend/services/mcp_tools.py
Task T010: Verify ai_agent.py agentic loop in backend/services/ai_agent.py

# Sequential — after T009 and T010:
Task T011: Verify chat.py send_message in backend/routes/chat.py

# Parallel — after T011:
Task T012: Test POST /chat creates task
Task T013: Test empty message → HTTP 400
Task T014: Test new conversation created when no conversation_id
Task T015: Test existing conversation_id is reused
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001–T003)
2. Complete Phase 2: Foundational (T004–T008) — CRITICAL BLOCKER
3. Complete Phase 3: US1 Create Task (T009–T015)
4. **STOP and VALIDATE**: `pytest backend/tests/test_chat.py -v -k "add or create"` — all pass
5. Deploy to HF Space and test live chat

### Incremental Delivery

1. Setup + Foundational → All infrastructure ready
2. US1 (P1) → Create tasks via chat ← **MVP demo point**
3. US2 (P2) → List tasks via chat
4. US3 (P3) → Complete tasks by name
5. US4 (P4) → Delete tasks by name
6. US5 (P5) → Update tasks by name
7. Security + HF Space + Polish → Production-ready

### Suggested MVP Scope

**Phases 1–3 only** (T001–T015, 15 tasks). Delivers:
- ✅ Create task via "Add X" message
- ✅ New/existing conversation management
- ✅ Task persisted to Neon DB
- ✅ AI confirms creation by name

---

## Notes

- [P] = different files, no blocking dependencies — safe to run in parallel
- Core implementation exists — most "implementation" tasks are verification + gap-filling tests
- The HF Space and main backend share the same Neon DB — isolation tests apply to both
- Commit after each phase checkpoint before moving to the next
- `aiosqlite` (in-memory SQLite) is used for all tests — no real Neon DB needed in CI
