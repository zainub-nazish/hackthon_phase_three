# Tasks: Todo Management MCP Tools

**Input**: Design documents from `specs/009-mcp-tools/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/mcp-tools.yaml, quickstart.md

**Tests**: Included — each user story has test tasks to verify MCP tool correctness.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/` for backend source and tests

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Add MCP SDK dependency and prepare project for MCP integration

- [x] T001 Add `mcp>=1.26.0,<2.0.0` to `backend/requirements.txt` and install dependencies
- [x] T002 Verify MCP SDK installation by importing `mcp` in a quick smoke test (e.g., `python -c "from mcp.server.fastmcp import FastMCP; print('OK')"`)

---

## Phase 2: Foundational (MCP Server Scaffold + Bridge)

**Purpose**: Create the MCP tool server scaffold and bridge module that ALL user stories depend on

**CRITICAL**: No user story tool handler can be implemented until this phase is complete

- [x] T003 Create MCP tool server scaffold in `backend/services/mcp_tools.py`: initialize `FastMCP` server instance named `"todo-tools"`, move `_get_db_session()` async context manager from `backend/services/ai_agent.py` to this module (keep the original in ai_agent.py temporarily for backward compatibility until Phase 8)
- [x] T0 Create MCP bridge module in `backend/services/mcp_bridge.py`: implement `get_tool_schemas() -> list[dict]` that reads tool definitions from the MCP server and converts them to Anthropic API format (`name`, `description`, `input_schema`), stripping any `user_id` parameter from exposed schemas; implement `execute_tool(name: str, params: dict, user_id: str) -> dict` that dispatches tool calls to the registered MCP handler by name, injecting `user_id` into the call, and returning the result dict; handle unknown tool names with `{is_error: true, error: "Unknown tool: {name}"}`; cache converted schemas at module level for performance (D-003)
- [x] T0 [P] Create test scaffolding in `backend/tests/test_mcp_tools.py`: add imports, create `TestMCPBridge` class with a test that verifies `get_tool_schemas()` returns exactly 5 tool definitions, each with `name`, `description`, and `input_schema` keys in Anthropic format
- [x] T0 [P] Update `backend/tests/conftest.py`: add a new `mcp_db` fixture that patches `backend.services.mcp_tools._get_db_session` (same pattern as existing `agent_db` but targeting the new module path)

**Checkpoint**: MCP server scaffold created, bridge module functional, test infrastructure ready. Tool handlers can now be added per user story.

---

## Phase 3: User Story 1 — Add a Task via MCP (Priority: P1) MVP

**Goal**: Implement the `add_task` MCP tool so authenticated users can create tasks via natural language through the AI chatbot.

**Independent Test**: Call `add_task` handler with `{title: "Buy milk"}` and `user_id`, verify a task is created in the database with the correct title, owner, and default `completed=False`. Verify the tool schema includes `title` (required) and `description` (optional).

### Tests for User Story 1

- [x] T0 [P] [US1] Write unit test `TestMCPAddTask.test_add_task_creates_task` in `backend/tests/test_mcp_tools.py`: call the `add_task` MCP handler with `{title: "Buy milk"}` and a test `user_id`, assert result contains `id`, `title == "Buy milk"`, `completed == False`, `description is None`
- [x] T0 [P] [US1] Write unit test `TestMCPAddTask.test_add_task_with_description` in `backend/tests/test_mcp_tools.py`: call with `{title: "Meeting", description: "Slides for Monday"}`, assert both fields are present in result
- [x] T0 [P] [US1] Write unit test `TestMCPAddTask.test_add_task_empty_title_returns_error` in `backend/tests/test_mcp_tools.py`: call with `{title: ""}`, assert `is_error == True` and error message mentions "required"
- [x] T0 [P] [US1] Write unit test `TestMCPAddTask.test_add_task_title_too_long` in `backend/tests/test_mcp_tools.py`: call with title of 256 chars, assert `is_error == True` and error message mentions "255"

### Implementation for User Story 1

- [x] T0 [US1] Implement `add_task` tool handler in `backend/services/mcp_tools.py`: register with `@server.tool()` decorator, accept `title` (str, required), `description` (str, optional), and `user_id` (str, injected by bridge); validate title non-empty and ≤255 chars, description ≤2000 chars; create `Task` record with `owner_id=user_id`; commit and return `{id, title, description, completed}` dict; on validation failure return `{is_error: true, error: "..."}`. Follow the workflow from contracts/mcp-tools.yaml `add_task`.
- [x] T0 [US1] Wire `add_task` into the bridge dispatch in `backend/services/mcp_bridge.py`: ensure `execute_tool("add_task", params, user_id)` routes to the MCP handler and `get_tool_schemas()` includes the `add_task` schema with `title` required and `description` optional
- [x] T0 [US1] Run tests: verify T007-T010 pass with `pytest backend/tests/test_mcp_tools.py::TestMCPAddTask -v`

**Checkpoint**: `add_task` MCP tool fully functional. Users can create tasks through the MCP layer. This proves the full MCP pipeline end-to-end.

---

## Phase 4: User Story 2 — List and Filter Tasks via MCP (Priority: P2)

**Goal**: Implement the `list_tasks` MCP tool so users can query their tasks with optional status filtering.

**Independent Test**: Create 3 tasks (1 completed, 2 pending) for a user, call `list_tasks` with no filter and verify count=3. Call with `status="pending"` and verify count=2. Call with `status="completed"` and verify count=1.

### Tests for User Story 2

- [x] T0 [P] [US2] Write unit test `TestMCPListTasks.test_list_all_tasks` in `backend/tests/test_mcp_tools.py`: create 2 tasks for a user, call `list_tasks` with `{}`, assert `count == 2` and both tasks are in the response
- [x] T0 [P] [US2] Write unit test `TestMCPListTasks.test_list_pending_tasks` in `backend/tests/test_mcp_tools.py`: create 2 tasks (1 completed, 1 pending), call with `{status: "pending"}`, assert `count == 1` and only the pending task is returned
- [x] T0 [P] [US2] Write unit test `TestMCPListTasks.test_list_completed_tasks` in `backend/tests/test_mcp_tools.py`: same setup, call with `{status: "completed"}`, assert only completed task returned
- [x] T0 [P] [US2] Write unit test `TestMCPListTasks.test_list_empty` in `backend/tests/test_mcp_tools.py`: call for a user with no tasks, assert `count == 0` and `tasks == []`
- [x] T0 [P] [US2] Write unit test `TestMCPListTasks.test_list_user_isolation` in `backend/tests/test_mcp_tools.py`: create tasks for user_a and user_b, call list for each, verify each user only sees their own tasks

### Implementation for User Story 2

- [x] T0 [US2] Implement `list_tasks` tool handler in `backend/services/mcp_tools.py`: register with `@server.tool()`, accept optional `status` (str, enum: all/pending/completed, default "all") and `user_id`; query `Task` where `owner_id=user_id` with status filter; order by `created_at` desc; return `{tasks: [{id, title, description, completed}, ...], count}`. Follow contracts/mcp-tools.yaml `list_tasks`.
- [x] T0 [US2] Wire `list_tasks` into the bridge dispatch and verify schema includes optional `status` parameter
- [x] T0 [US2] Run tests: verify T014-T018 pass with `pytest backend/tests/test_mcp_tools.py::TestMCPListTasks -v`

**Checkpoint**: `list_tasks` MCP tool functional. Combined with US1, users can add and view tasks through MCP.

---

## Phase 5: User Story 3 — Complete a Task via MCP (Priority: P3)

**Goal**: Implement the `complete_task` MCP tool so users can mark tasks as done.

**Independent Test**: Create a task, call `complete_task` with its ID, verify `completed == True` in the result and in the database.

### Tests for User Story 3

- [x] T0 [P] [US3] Write unit test `TestMCPCompleteTask.test_complete_task_success` in `backend/tests/test_mcp_tools.py`: create a task, call `complete_task` with its ID, assert `completed == True` and `title` matches
- [x] T0 [P] [US3] Write unit test `TestMCPCompleteTask.test_complete_task_not_found` in `backend/tests/test_mcp_tools.py`: call with random UUID, assert `is_error == True` and "not found" in error
- [x] T0 [P] [US3] Write unit test `TestMCPCompleteTask.test_complete_task_wrong_user` in `backend/tests/test_mcp_tools.py`: create task for user_a, try to complete as user_b, assert `is_error == True`
- [x] T0 [P] [US3] Write unit test `TestMCPCompleteTask.test_complete_task_invalid_uuid` in `backend/tests/test_mcp_tools.py`: call with `{task_id: "not-a-uuid"}`, assert `is_error == True` and "Invalid" in error

### Implementation for User Story 3

- [x] T0 [US3] Implement `complete_task` tool handler in `backend/services/mcp_tools.py`: register with `@server.tool()`, accept `task_id` (str, required) and `user_id`; validate UUID format; query `Task` where `id=task_id AND owner_id=user_id`; if not found return error; set `completed=True`, update `updated_at`; return `{id, title, completed}`. Follow contracts/mcp-tools.yaml `complete_task`.
- [x] T0 [US3] Wire `complete_task` into the bridge dispatch and verify schema includes required `task_id`
- [x] T0 [US3] Run tests: verify T022-T025 pass with `pytest backend/tests/test_mcp_tools.py::TestMCPCompleteTask -v`

**Checkpoint**: `complete_task` MCP tool functional. Full create-list-complete workflow now possible through MCP.

---

## Phase 6: User Story 4 — Update a Task via MCP (Priority: P4)

**Goal**: Implement the `update_task` MCP tool so users can modify task titles and descriptions.

**Independent Test**: Create a task "Old title", call `update_task` with `{task_id, title: "New title"}`, verify the title changed in the result.

### Tests for User Story 4

- [x] T0 [P] [US4] Write unit test `TestMCPUpdateTask.test_update_title` in `backend/tests/test_mcp_tools.py`: create task, update title, assert new title in result
- [x] T0 [P] [US4] Write unit test `TestMCPUpdateTask.test_update_description` in `backend/tests/test_mcp_tools.py`: create task, update description, assert new description in result
- [x] T0 [P] [US4] Write unit test `TestMCPUpdateTask.test_update_not_found` in `backend/tests/test_mcp_tools.py`: call with random UUID, assert error
- [x] T0 [P] [US4] Write unit test `TestMCPUpdateTask.test_update_no_fields` in `backend/tests/test_mcp_tools.py`: call with only `task_id`, assert `is_error == True` and "at least one" in error

### Implementation for User Story 4

- [x] T0 [US4] Implement `update_task` tool handler in `backend/services/mcp_tools.py`: register with `@server.tool()`, accept `task_id` (required), optional `title` and `description`, and `user_id`; validate at least one field provided, title non-empty if present; query and update task; return `{id, title, description, completed}`. Follow contracts/mcp-tools.yaml `update_task`.
- [x] T0 [US4] Wire `update_task` into the bridge dispatch and verify schema
- [x] T0 [US4] Run tests: verify T029-T032 pass with `pytest backend/tests/test_mcp_tools.py::TestMCPUpdateTask -v`

**Checkpoint**: `update_task` MCP tool functional. Users can modify existing tasks through MCP.

---

## Phase 7: User Story 5 — Delete a Task via MCP (Priority: P5)

**Goal**: Implement the `delete_task` MCP tool so users can permanently remove tasks.

**Independent Test**: Create a task, call `delete_task` with its ID, verify `deleted == True` in result and task no longer exists in the database.

### Tests for User Story 5

- [x] T0 [P] [US5] Write unit test `TestMCPDeleteTask.test_delete_task_success` in `backend/tests/test_mcp_tools.py`: create task, delete it, assert `deleted == True` and `title` matches; call `list_tasks` to verify count=0
- [x] T0 [P] [US5] Write unit test `TestMCPDeleteTask.test_delete_task_not_found` in `backend/tests/test_mcp_tools.py`: call with random UUID, assert error
- [x] T0 [P] [US5] Write unit test `TestMCPDeleteTask.test_delete_task_wrong_user` in `backend/tests/test_mcp_tools.py`: create task for user_a, try to delete as user_b, assert error

### Implementation for User Story 5

- [x] T0 [US5] Implement `delete_task` tool handler in `backend/services/mcp_tools.py`: register with `@server.tool()`, accept `task_id` (required) and `user_id`; validate UUID; query task with owner check; delete and commit; return `{deleted: true, id, title}`. Follow contracts/mcp-tools.yaml `delete_task`.
- [x] T0 [US5] Wire `delete_task` into the bridge dispatch and verify schema
- [x] T0 [US5] Run tests: verify T036-T038 pass with `pytest backend/tests/test_mcp_tools.py::TestMCPDeleteTask -v`

**Checkpoint**: All 5 MCP tools implemented and tested. Full CRUD + complete operations available through MCP.

---

## Phase 8: Agent Integration (Refactor ai_agent.py)

**Purpose**: Refactor the AI agent to use MCP bridge instead of inline tools. This is the critical integration step.

- [x] T042 Refactor `backend/services/ai_agent.py`: remove the `TOOLS` list constant (5 inline tool definitions), remove the `TOOL_EXECUTORS` dict, remove all `_execute_*` functions (`_execute_add_task`, `_execute_list_tasks`, `_execute_complete_task`, `_execute_delete_task`, `_execute_update_task`), remove `_get_db_session()` helper. Import `get_tool_schemas` and `execute_tool` from `backend.services.mcp_bridge`. Keep `SYSTEM_PROMPT`, `ToolCallData`, `AgentResponse`, `AIAgentService` class, `get_ai_agent_service()`.
- [x] T043 Update `AIAgentService.generate_response()` in `backend/services/ai_agent.py`: replace `tools=TOOLS` with `tools=get_tool_schemas()` in the `client.messages.create()` call; replace `TOOL_EXECUTORS.get(block.name)` dispatch block with `execute_tool(block.name, block.input, user_id)` call through the MCP bridge; preserve all existing error handling, stub fallback, and `ToolCallData` recording logic
- [x] T044 Update `backend/tests/conftest.py`: modify the `agent_db` fixture to patch `backend.services.mcp_tools._get_db_session` instead of `backend.services.ai_agent._get_db_session`; ensure the `mcp_db` fixture (from T006) is also available; add `backend.services.mcp_tools` to the module reload list in `_setup_test_app()`
- [x] T045 Update `backend/tests/test_ai_agent.py`: update all imports that reference `_execute_add_task`, `_execute_list_tasks`, etc. to import from `backend.services.mcp_tools` instead of `backend.services.ai_agent`; update `TestAgentLoopSingleToolCall` and `TestAgentLoopMultiStep` to work with the MCP bridge dispatch path; verify all existing test assertions still hold (same behavior, different dispatch path)
- [x] T046 Run full test suite: `pytest backend/tests/ -v` — verify all existing tests in `test_ai_agent.py`, `test_chat.py`, `test_chat_isolation.py`, and the new `test_mcp_tools.py` pass

**Checkpoint**: AI agent fully refactored to use MCP tools. The `ai_agent.py` file no longer contains any inline tool definitions or executors.

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Final validation, cleanup, and verification

- [x] T047 [P] Verify MCP bridge schema caching works correctly: ensure `get_tool_schemas()` returns consistent results across multiple calls and schemas are computed once at module load time
- [x] T048 [P] Verify user isolation across all 5 MCP tools: write a test in `backend/tests/test_mcp_tools.py` class `TestMCPUserIsolation` that creates tasks for user_a, then attempts each tool (list, complete, update, delete) as user_b, verifying user_b cannot access user_a's tasks
- [x] T049 Run quickstart.md validation: follow the steps in `specs/009-mcp-tools/quickstart.md` verification checklist and confirm all items pass
- [x] T050 Verify no inline tool definitions remain in `backend/services/ai_agent.py`: grep for `TOOLS`, `TOOL_EXECUTORS`, `_execute_` to confirm they have been fully removed

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 (mcp installed) — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Phase 2 — MVP target
- **US2 (Phase 4)**: Depends on Phase 2 — can run in parallel with US1
- **US3 (Phase 5)**: Depends on Phase 2 — can run in parallel (but tests use add_task from US1)
- **US4 (Phase 6)**: Depends on Phase 2 — can run in parallel
- **US5 (Phase 7)**: Depends on Phase 2 — can run in parallel
- **Agent Integration (Phase 8)**: Depends on ALL user stories (Phases 3-7) being complete
- **Polish (Phase 9)**: Depends on Phase 8

### User Story Dependencies

- **US1 (add_task)**: Independent — no other stories required
- **US2 (list_tasks)**: Independent — but used by US3/US4/US5 tests for setup
- **US3 (complete_task)**: Tests depend on US1 (add_task) for task creation
- **US4 (update_task)**: Tests depend on US1 (add_task) for task creation
- **US5 (delete_task)**: Tests depend on US1 (add_task) for task creation, US2 (list_tasks) for verification

### Within Each User Story

1. Tests written first (T00x test tasks)
2. Implementation (handler + bridge wiring)
3. Tests verified passing
4. Checkpoint before next story

### Parallel Opportunities

- T005 and T006 can run in parallel (different files)
- All test tasks within a story marked [P] can run in parallel
- US1 through US5 can be implemented in parallel after Phase 2 (all go in the same file but different functions)
- T047 and T048 can run in parallel in Phase 9

---

## Parallel Example: User Story 3

```bash
# Launch all US3 test stubs in parallel (different test classes):
Task: T022 "TestMCPCompleteTask.test_complete_task_success"
Task: T023 "TestMCPCompleteTask.test_complete_task_not_found"
Task: T024 "TestMCPCompleteTask.test_complete_task_wrong_user"
Task: T025 "TestMCPCompleteTask.test_complete_task_invalid_uuid"

# Then implement sequentially:
Task: T026 "Implement complete_task handler"
Task: T027 "Wire into bridge"
Task: T028 "Run and verify tests"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T002)
2. Complete Phase 2: Foundational (T003-T006)
3. Complete Phase 3: US1 add_task (T007-T013)
4. **STOP and VALIDATE**: Verify add_task MCP tool works end-to-end
5. This proves the full MCP pipeline — continue to remaining stories

### Incremental Delivery

1. Setup + Foundational → MCP infrastructure ready
2. US1 add_task → First tool working (MVP!)
3. US2 list_tasks → Query capability added
4. US3 complete_task → Task lifecycle (create → complete)
5. US4 update_task → Modification capability
6. US5 delete_task → Full CRUD
7. Agent Integration → AI agent uses MCP tools
8. Polish → Final validation

### Sequential Implementation (Recommended for Solo Dev)

Complete stories in priority order: US1 → US2 → US3 → US4 → US5 → Integration → Polish. Each story is independently testable at its checkpoint.

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- All 5 tool handlers go in `backend/services/mcp_tools.py` (single file)
- The bridge module `backend/services/mcp_bridge.py` handles all schema conversion and dispatch
- Tests in `backend/tests/test_mcp_tools.py` use the `mcp_db` fixture from conftest.py
- The existing `ai_agent.py` is not modified until Phase 8 (backward compatible until integration)
- Commit after each phase or story completion
