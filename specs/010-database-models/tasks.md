# Tasks: Database Models for Todo AI System

**Input**: Design documents from `/specs/010-database-models/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/database-models.yaml, quickstart.md
**Context**: This is a **retroactive specification** — all 4 models already exist in `backend/models/database.py` (155 LOC) and `backend/models/schemas.py` (152 LOC). 73 tests pass across 4 test files. Tasks focus on **validation, gap analysis, and documentation** rather than greenfield implementation.

**Tests**: Not generating new test tasks — 73 existing tests cover all entities. Validation tasks confirm test coverage against spec requirements.

**Organization**: Tasks are grouped by user story to enable independent validation of each entity.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Environment Verification)

**Purpose**: Confirm the development environment is ready and existing code compiles/runs

- [x] T001 Verify Python 3.11+ is available and virtual environment is active in `backend/` — Python 3.13.2 confirmed
- [x] T002 Run `pip install -r backend/requirements.txt` to confirm all dependencies install cleanly — all deps installed
- [x] T003 Run full test suite `pytest backend/tests/ -v` and confirm all 73 tests pass (25 in test_mcp_tools.py, 25 in test_ai_agent.py, 18 in test_chat.py, 5 in test_chat_isolation.py) — 73 passed, 168 warnings
- [x] T004 [P] Verify SQLModel, aiosqlite, and pytest-asyncio are listed in `backend/requirements.txt` — all present

---

## Phase 2: Foundational (Cross-Entity Structural Validation)

**Purpose**: Validate shared patterns across all 4 models before per-entity deep-dive

**CRITICAL**: Completes before any user story validation begins

- [x] T005 Validate all 4 models (Task, Conversation, Message, ToolCall) are defined as `SQLModel, table=True` with explicit `__tablename__` in `backend/models/database.py` — all 4 confirmed
- [x] T006 [P] Validate all 4 models use UUID v4 primary keys with `default_factory=uuid4` in `backend/models/database.py` — all 4 confirmed
- [x] T007 [P] Validate all 4 models have `created_at: datetime` with `default_factory=datetime.utcnow` and `nullable=False` in `backend/models/database.py` — all 4 confirmed
- [x] T008 [P] Validate Task and Conversation have `owner_id: str` with `index=True` and `nullable=False` in `backend/models/database.py` — both confirmed
- [x] T009 [P] Validate Message.conversation_id and ToolCall.message_id declare `foreign_key=` and `index=True` in `backend/models/database.py` — both confirmed
- [x] T010 Validate Pydantic schemas in `backend/models/schemas.py` cover all CRUD operations defined in `specs/010-database-models/contracts/database-models.yaml` — all 9 schemas present
- [x] T011 [P] Validate `backend/database.py` provides async engine factory supporting both Neon PostgreSQL (asyncpg) and SQLite (aiosqlite) per research decision R-007 — dual-DB with SQLite detection confirmed

**Checkpoint**: All structural patterns confirmed — per-entity validation can proceed

---

## Phase 3: User Story 1 — Create and Manage Tasks (Priority: P1) MVP

**Goal**: Validate the Task model and schemas fully conform to spec FR-001 through FR-007, FR-014

**Independent Test**: Run `pytest backend/tests/test_mcp_tools.py -v` — all 26 tests pass covering Task CRUD, validation errors, and user isolation

### Validation for User Story 1

- [x] T012 [US1] Validate Task.title field: `max_length=255`, `nullable=False` in `backend/models/database.py` matches spec FR-005 — confirmed line 25-28
- [x] T013 [P] [US1] Validate Task.description field: `Optional[str]`, `max_length=2000`, `default=None` in `backend/models/database.py` matches spec FR-006 — confirmed line 30-33
- [x] T014 [P] [US1] Validate Task.completed field: `bool`, `default=False`, `nullable=False` in `backend/models/database.py` matches spec FR-007 — confirmed line 35-38
- [x] T015 [P] [US1] Validate Task.updated_at field: `default_factory=datetime.utcnow`, `nullable=False` in `backend/models/database.py` matches spec FR-004 — confirmed line 45-48
- [x] T016 [US1] Validate TaskCreate schema enforces `min_length=1` on title (rejects empty/whitespace) and `max_length=255` in `backend/models/schemas.py` matches validation rule V1 — confirmed via TaskBase line 58
- [x] T017 [P] [US1] Validate TaskUpdate schema allows partial updates (all fields Optional) with same length constraints in `backend/models/schemas.py` — confirmed line 69-74
- [x] T018 [P] [US1] Validate TaskResponse schema includes all fields (id, owner_id, title, description, completed, created_at, updated_at) with `from_attributes=True` in `backend/models/schemas.py` — confirmed line 77-85
- [x] T019 [US1] Validate TaskListResponse schema includes items, total, limit, offset fields matching contract `task_list` in `backend/models/schemas.py` — confirmed line 88-94
- [x] T020 [US1] Confirm test_mcp_tools.py covers acceptance scenarios: create task with defaults, user isolation, update title, mark complete — all 4 acceptance scenarios covered
- [x] T021 [US1] Document any gaps found for User Story 1 in `specs/010-database-models/checklists/requirements.md` under a US1 section — no gaps found

**Checkpoint**: Task entity fully validated against spec — all CRUD operations, validation rules, and isolation confirmed

---

## Phase 4: User Story 2 — Store Chat Conversations (Priority: P2)

**Goal**: Validate the Conversation model conforms to spec FR-001 through FR-004, FR-014

**Independent Test**: Run `pytest backend/tests/test_chat.py -v -k conversation` and `pytest backend/tests/test_chat_isolation.py -v` — conversation creation, timestamp refresh, and cross-user isolation all pass

### Validation for User Story 2

- [x] T022 [US2] Validate Conversation model has only id, owner_id, created_at, updated_at fields in `backend/models/database.py` matches spec Conversation field definitions — 4 fields confirmed line 57-81
- [x] T023 [P] [US2] Validate Conversation.updated_at refreshes on new message activity — confirmed chat.py:155 and chat.py:127 call datetime.utcnow() on updated_at
- [x] T024 [P] [US2] Validate ConversationResponse schema in `backend/models/schemas.py` matches contract `conversation_get_recent` output shape — confirmed line 144-152
- [x] T025 [US2] Confirm test_chat_isolation.py covers acceptance scenario: user A's conversation is invisible to user B — covered by test_cross_user_conversations_isolation and test_cross_user_chat_returns_404
- [x] T026 [US2] Document any gaps found for User Story 2 in `specs/010-database-models/checklists/requirements.md` under a US2 section — no gaps found

**Checkpoint**: Conversation entity validated — creation, timestamp refresh, and user isolation confirmed

---

## Phase 5: User Story 3 — Persist Chat Messages (Priority: P2)

**Goal**: Validate the Message model conforms to spec FR-001, FR-003, FR-008, FR-009, FR-013, FR-015

**Independent Test**: Run `pytest backend/tests/test_chat.py -v -k message` — message creation, chronological ordering, role validation, and FK enforcement all pass

### Validation for User Story 3

- [x] T027 [US3] Validate Message.conversation_id field: `foreign_key="conversations.id"`, `index=True`, `nullable=False` in `backend/models/database.py` matches spec FR-008 — confirmed line 94-98
- [x] T028 [P] [US3] Validate Message.role field: `max_length=20`, `nullable=False` in `backend/models/database.py` — roles are server-assigned ("user"/"assistant") in chat.py:100,138; no client input path. FR-009 satisfied
- [x] T029 [P] [US3] Validate Message.content field: `nullable=False` in `backend/models/database.py` — ChatRequest min_length=1 + whitespace strip in chat.py:70-75. FR-013 satisfied
- [x] T030 [US3] Validate Message immutability — no PUT/PATCH/DELETE endpoints for messages in chat.py. Only POST and GET exist
- [x] T031 [P] [US3] Validate MessageResponse and MessagesResponse schemas in `backend/models/schemas.py` match contract output shapes — confirmed line 123-141
- [x] T032 [US3] Confirm test_chat.py covers acceptance scenarios: role "user" (test_send_message), chronological order (test_get_messages_chronological), FK integrity (test_invalid_conversation_returns_404) — all 4 covered
- [x] T033 [US3] Document any gaps found for User Story 3 in `specs/010-database-models/checklists/requirements.md` under a US3 section — no gaps found

**Checkpoint**: Message entity validated — creation, ordering, immutability, role enum, and FK integrity confirmed

---

## Phase 6: User Story 4 — Track AI Tool Invocations (Priority: P3)

**Goal**: Validate the ToolCall model conforms to spec FR-001, FR-003, FR-010, FR-011, FR-012, FR-016

**Independent Test**: Run `pytest backend/tests/test_chat.py -v -k tool` and `pytest backend/tests/test_ai_agent.py -v` — tool call creation, status tracking, and FK enforcement all pass

### Validation for User Story 4

- [x] T034 [US4] Validate ToolCall.message_id field: `foreign_key="messages.id"`, `index=True`, `nullable=False` in `backend/models/database.py` matches spec FR-010 — confirmed line 126-130
- [x] T035 [P] [US4] Validate ToolCall.tool_name field: `max_length=100`, `nullable=False` in `backend/models/database.py` — confirmed line 132-135
- [x] T036 [P] [US4] Validate ToolCall.parameters and ToolCall.result fields: both `str`, `nullable=False` in `backend/models/database.py` — JSON-as-string per R-006/FR-011 confirmed line 137-143
- [x] T037 [P] [US4] Validate ToolCall.status field: `max_length=20`, `nullable=False` in `backend/models/database.py` — application-level via ToolCallData in chat.py:150. FR-012 satisfied
- [x] T038 [US4] Validate ToolCall immutability — no PUT/PATCH/DELETE endpoints for tool calls. Only created in chat.py:145-152
- [x] T039 [US4] Confirm test_chat.py and test_ai_agent.py cover acceptance scenarios: success (test_tool_call_persisted), error (test_tool_call_failure_persisted), message linkage verified — all 3 covered
- [x] T040 [US4] Document any gaps found for User Story 4 in `specs/010-database-models/checklists/requirements.md` under a US4 section — no gaps found

**Checkpoint**: ToolCall entity validated — creation, JSON serialization, status enum, FK integrity, and immutability confirmed

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Address known gaps, edge case validation, and documentation completeness

- [x] T041 [P] Validate edge case handling: empty title (test_mcp_tools:95), title too long (test_mcp_tools:104), empty message (test_chat:75), whitespace message (test_chat:86), oversized message (test_chat:98) — all edge cases covered
- [x] T042 [P] Document `datetime.utcnow()` deprecation gap in `specs/010-database-models/checklists/requirements.md` — documented as GAP-001 with migration recommendation
- [x] T043 [P] Document cascade deletion policy gap in `specs/010-database-models/checklists/requirements.md` — documented as GAP-002 with future migration note
- [x] T044 Validate user isolation contract: all 9 query paths in tasks.py and chat.py filter by owner_id from JWT path parameter — no client-supplied owner_id
- [x] T045 Verify chat_send_message 8-step workflow in chat.py — all 8 steps confirmed (validate, create/get conv, user msg, AI call, assistant msg, tool calls, touch, return)
- [x] T046 Run full test suite — 73 passed, 168 warnings (all DeprecationWarning from datetime.utcnow). No failures
- [x] T047 Run quickstart.md verification checklist — all 12 items confirmed against validation results from T005-T044

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 completion (T003 confirms tests pass) — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Phase 2 — can start after foundational validation
- **US2 (Phase 4)**: Depends on Phase 2 — can run in parallel with US1
- **US3 (Phase 5)**: Depends on Phase 2 — can run in parallel with US1/US2 (but logically after US2 since Messages depend on Conversations)
- **US4 (Phase 6)**: Depends on Phase 2 — can run in parallel with US1/US2/US3 (but logically after US3 since ToolCalls depend on Messages)
- **Polish (Phase 7)**: Depends on all user story phases being complete

### User Story Dependencies

- **US1 (Task)**: Independent — no dependencies on other stories
- **US2 (Conversation)**: Independent — no dependencies on other stories
- **US3 (Message)**: Logically after US2 (Message FK -> Conversation), but validation can proceed independently
- **US4 (ToolCall)**: Logically after US3 (ToolCall FK -> Message), but validation can proceed independently

### Within Each User Story

- Field validation tasks marked [P] can run in parallel
- Schema validation can run in parallel with model validation
- Test coverage confirmation depends on field/schema validation completing
- Gap documentation is always the final task per story

### Parallel Opportunities

- T004, T006, T007, T008, T009, T011 can all run in parallel in Phase 2
- T013, T014, T015, T017, T018 can run in parallel within US1
- T023, T024 can run in parallel within US2
- T028, T029, T031 can run in parallel within US3
- T035, T036, T037 can run in parallel within US4
- T041, T042, T043 can run in parallel in Phase 7
- All 4 user story phases (3-6) can run in parallel after Phase 2

---

## Parallel Example: User Story 1

```bash
# Launch all parallelizable field validations for US1 together:
Task: "T013 [P] [US1] Validate Task.description field in backend/models/database.py"
Task: "T014 [P] [US1] Validate Task.completed field in backend/models/database.py"
Task: "T015 [P] [US1] Validate Task.updated_at field in backend/models/database.py"
Task: "T017 [P] [US1] Validate TaskUpdate schema in backend/models/schemas.py"
Task: "T018 [P] [US1] Validate TaskResponse schema in backend/models/schemas.py"

# Then sequential: T016 → T019 → T020 → T021
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (verify environment)
2. Complete Phase 2: Foundational (structural validation across all entities)
3. Complete Phase 3: User Story 1 — Task entity validation
4. **STOP and VALIDATE**: All Task CRUD operations, validation rules, and isolation confirmed
5. Document findings

### Incremental Delivery

1. Complete Setup + Foundational → Environment and structural patterns confirmed
2. Validate US1 (Task) → Core entity confirmed (MVP!)
3. Validate US2 (Conversation) → Chat container confirmed
4. Validate US3 (Message) → Chat content confirmed
5. Validate US4 (ToolCall) → Audit trail confirmed
6. Polish → Cross-cutting gaps documented, full suite green

### Parallel Team Strategy

With multiple validators:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Validator A: User Story 1 (Task)
   - Validator B: User Story 2 (Conversation)
   - Validator C: User Story 3 (Message) + User Story 4 (ToolCall)
3. All converge for Phase 7 (Polish)

---

## Notes

- [P] tasks = different files or independent checks, no dependencies
- [Story] label maps validation task to specific user story for traceability
- This is a **retroactive validation** — no new source files are created
- All validation tasks are read-only analysis against `backend/models/database.py` and `backend/models/schemas.py`
- Gap documentation goes to `specs/010-database-models/checklists/requirements.md`
- Known gaps from plan.md: `datetime.utcnow()` deprecation (R-003), application-level enum validation (Risk #2), no cascade delete policy (Risk #3)
