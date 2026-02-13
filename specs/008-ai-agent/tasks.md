# Tasks: AI Todo Agent

**Input**: Design documents from `/specs/008-ai-agent/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/tool-definitions.yaml, quickstart.md

**Tests**: Included — plan.md Phase 4 explicitly requires unit tests with mocked Anthropic client.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Configuration and dependency installation for the Anthropic SDK integration

- [x] T001 Add `anthropic_api_key` (Optional[str], default None) and `anthropic_model` (str, default `claude-haiku-4-5-20251001`) settings to `backend/config.py` using pydantic-settings Field with alias `ANTHROPIC_API_KEY` and `ANTHROPIC_MODEL` — follow existing pattern (see `database_url` and `better_auth_url` fields)
- [x] T002 Install `anthropic` Python package (v0.79.0+) — add to `backend/requirements.txt` and run `pip install anthropic`

**Checkpoint**: Configuration ready — `settings.anthropic_api_key` and `settings.anthropic_model` accessible from `backend/config.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core constants and infrastructure that ALL user stories depend on — system prompt, tool definitions, and dispatcher

**Warning**: No user story work can begin until this phase is complete

- [x] T003 Define `SYSTEM_PROMPT` constant string in `backend/services/ai_agent.py` — copy from `specs/008-ai-agent/contracts/tool-definitions.yaml` system_prompt section. The prompt defines the agent as a friendly todo assistant with guidelines for tool usage, response format, context resolution, error handling, and scope limitations
- [x] T004 Define `TOOLS` constant list in `backend/services/ai_agent.py` — 5 Anthropic tool-use definitions (add_task, list_tasks, complete_task, delete_task, update_task) matching the JSON Schema in `specs/008-ai-agent/contracts/tool-definitions.yaml`. Each tool dict has `name`, `description`, and `input_schema` keys
- [x] T005 Create tool executor dispatcher in `backend/services/ai_agent.py` — a dict mapping tool name strings to async executor functions (e.g., `TOOL_EXECUTORS = {"add_task": _execute_add_task, ...}`). Also add a helper function `_get_db_session()` that creates an async database session using the existing engine from `backend/models/database.py` for tool execution

**Checkpoint**: Foundation ready — SYSTEM_PROMPT, TOOLS, and dispatcher defined. User story implementation can begin.

---

## Phase 3: User Story 1 — Create Task via Natural Language (Priority: P1) MVP

**Goal**: User sends "Add a task to buy milk" → agent creates the task and confirms with a friendly message

**Independent Test**: Send a chat message like "Add a task to buy groceries" → verify (1) task appears in user's task list, (2) agent response confirms creation with task title, (3) ToolCallData is returned for persistence

### Implementation for User Story 1

- [x] T006 [US1] Implement `_execute_add_task(parameters: dict, user_id: str)` async function in `backend/services/ai_agent.py` — creates a new Task (from `backend/models/database.py`) with `title` (required) and `description` (optional) from parameters, sets `owner_id = user_id`. Uses `_get_db_session()` for DB access. Returns dict with created task data (id, title, description, completed). On validation error, returns error dict
- [x] T007 [US1] Replace `AIAgentService.generate_response()` stub with real Anthropic-powered agent loop in `backend/services/ai_agent.py` — implementation steps: (1) Import and initialize `anthropic.AsyncAnthropic` client using `settings.anthropic_api_key`. (2) Call `client.messages.create()` with model=`settings.anthropic_model`, system=SYSTEM_PROMPT, messages=conversation history, tools=TOOLS, max_tokens=1024. (3) Check response.stop_reason — if `"tool_use"`, extract tool_use blocks, execute each via TOOL_EXECUTORS dispatcher, build tool_result content blocks, call Claude again with updated messages. (4) Repeat until stop_reason is `"end_turn"`. (5) Collect ToolCallData (tool_name, JSON parameters, JSON result, status) for each tool invocation. (6) Return AgentResponse with final text content and tool_calls list. (7) Catch `anthropic.APIError` and raise RuntimeError for the chat API to handle as 502. (8) Keep existing `set_stub_response` for test configurability
- [x] T008 [US1] Add graceful stub fallback in `generate_response` when `settings.anthropic_api_key` is None or empty in `backend/services/ai_agent.py` — if API key is not configured, return the existing canned stub response instead of calling Anthropic API. This allows the backend to run without an API key in development

**Checkpoint**: US1 complete — user can create tasks via natural language. The full agent pipeline works: message → Claude → tool_use → add_task → confirmation.

---

## Phase 4: User Story 2 — List and Query Tasks via Natural Language (Priority: P2)

**Goal**: User sends "Show my tasks" or "What tasks are pending?" → agent lists tasks with appropriate filtering

**Independent Test**: Create several tasks (some completed), send "Show my tasks" → verify all tasks listed. Send "Show completed tasks" → verify only completed tasks returned.

### Implementation for User Story 2

- [x] T009 [US2] Implement `_execute_list_tasks(parameters: dict, user_id: str)` async function in `backend/services/ai_agent.py` — queries Task table filtered by `owner_id = user_id`. If `status` parameter is "pending", filter `completed == False`; if "completed", filter `completed == True`; if "all" or not specified, return all tasks. Uses `_get_db_session()`. Returns dict with list of tasks (id, title, completed status). Returns friendly empty message if no tasks found

**Checkpoint**: US2 complete — user can list and filter tasks via natural language. Agent returns formatted task lists.

---

## Phase 5: User Story 3 — Complete, Delete, and Update Tasks (Priority: P3)

**Goal**: User sends "Mark 'Buy milk' as done", "Delete the old task", or "Rename it to 'Buy almond milk'" → agent identifies target task and executes the modification

**Independent Test**: Create a task, send "Complete 'Buy milk'" → verify task is marked completed. Send "Delete that task" → verify task is removed. Send "Change title to 'New title'" → verify title is updated.

### Implementation for User Story 3

- [x] T010 [US3] Implement `_execute_complete_task(parameters: dict, user_id: str)` async function in `backend/services/ai_agent.py` — finds Task by `id = task_id AND owner_id = user_id`, sets `completed = True`, commits. Returns updated task dict on success. Returns error dict with `is_error=True` if task not found
- [x] T011 [US3] Implement `_execute_delete_task(parameters: dict, user_id: str)` async function in `backend/services/ai_agent.py` — finds Task by `id = task_id AND owner_id = user_id`, deletes it, commits. Returns confirmation dict on success. Returns error dict with `is_error=True` if task not found
- [x] T012 [US3] Implement `_execute_update_task(parameters: dict, user_id: str)` async function in `backend/services/ai_agent.py` — finds Task by `id = task_id AND owner_id = user_id`, updates `title` and/or `description` from parameters (at least one must be provided), commits. Returns updated task dict on success. Returns error dict with `is_error=True` if task not found

**Checkpoint**: US3 complete — full CRUD cycle available. User can create, list, complete, delete, and update tasks via natural language.

---

## Phase 6: User Story 4 — Contextual Reference Resolution (Priority: P4)

**Goal**: User says "delete it" after agent confirmed a task → agent resolves "it" from conversation history and acts on the correct task

**Independent Test**: (1) Create a task → agent confirms "Buy milk". (2) Send "delete it" → verify agent identifies the just-created task and deletes it. (3) Send "delete it" with no prior context → verify agent asks for clarification.

### Implementation for User Story 4

- [x] T013 [US4] Ensure conversation history formatting in `generate_response` includes assistant messages with tool call results so Claude can resolve pronouns like "it", "that task", "the last one" in `backend/services/ai_agent.py` — verify that messages passed to Claude API include the full conversation history (up to 20 messages per spec SC-001 constraint), with assistant tool-use results preserved as content. Claude's native context understanding handles pronoun resolution when given proper history. No additional code logic needed beyond correct message formatting — the SYSTEM_PROMPT (T003) already instructs the agent on context resolution behavior

**Checkpoint**: US4 complete — agent resolves contextual references from conversation history. All 4 user stories functional.

---

## Phase 7: Polish & Testing

**Purpose**: Unit tests, error handling verification, and manual validation

- [x] T014 [P] Add AI agent test fixtures to `backend/tests/conftest.py` — create a `mock_anthropic_client` fixture that patches `anthropic.AsyncAnthropic` with a mock. Create helper functions: `make_tool_use_response(tool_name, tool_input)` that returns a mock Claude response with stop_reason="tool_use" and a tool_use content block, and `make_text_response(text)` that returns a mock response with stop_reason="end_turn" and a text content block
- [x] T015 [P] Create unit tests for all 5 tool executor functions in `backend/tests/test_ai_agent.py` — test `_execute_add_task` (creates task, returns dict with id/title/completed), `_execute_list_tasks` (returns all tasks, filters by status, returns empty list), `_execute_complete_task` (marks task done, returns error for missing task), `_execute_delete_task` (removes task, returns error for missing task), `_execute_update_task` (updates fields, returns error for missing task). All tests use real DB operations with test database. Verify `owner_id` isolation (user A cannot modify user B's tasks)
- [x] T016 Create unit tests for agent loop and error scenarios in `backend/tests/test_ai_agent.py` — test: (1) agent loop with single tool call (mock Claude returning tool_use → tool_result → end_turn), (2) agent loop with multi-step tool calls (list → delete), (3) ToolCallData collection matches tool invocations, (4) API error returns RuntimeError, (5) missing API key returns stub response, (6) set_stub_response still works for test configuration
- [ ] T017 Run quickstart.md verification (manual — requires live server with ANTHROPIC_API_KEY) steps from `specs/008-ai-agent/quickstart.md` against live server — create task via NL, list tasks, complete task, delete task, test error handling, test general conversation

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 completion — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Phase 2 — implements the agent loop (core engine)
- **US2 (Phase 4)**: Depends on Phase 3 — needs working agent loop from US1
- **US3 (Phase 5)**: Depends on Phase 3 — needs working agent loop from US1
- **US4 (Phase 6)**: Depends on Phase 3 — needs working agent loop with history
- **Polish (Phase 7)**: Depends on Phases 3-6 — tests all features

### User Story Dependencies

- **US1 (P1)**: Depends on Foundational (Phase 2). Implements the agent loop — ALL other stories depend on this
- **US2 (P2)**: Depends on US1 (Phase 3) for working agent loop. Can start after US1 is complete
- **US3 (P3)**: Depends on US1 (Phase 3) for working agent loop. Independent of US2 — can run in parallel with US2
- **US4 (P4)**: Depends on US1 (Phase 3) for working agent loop with history. Independent of US2/US3

### Within Each User Story

- All tool executor functions follow the same pattern: query DB with owner_id isolation
- Agent loop (T007) is the critical path — it must work before any tool can be tested end-to-end
- Tool executors can be implemented in any order after the agent loop works

### Parallel Opportunities

- T001 and T002 (Setup) are independent — can run in parallel
- T003 and T004 (Foundational) are independent — can run in parallel
- US2 and US3 can run in parallel after US1 completes (both only need the agent loop)
- T014 and T015 (test fixtures + tool tests) can run in parallel (different files)
- T010, T011, T012 (US3 tool executors) are independent functions — can be implemented in sequence within one editing session

---

## Parallel Example: Setup Phase

```
# Both setup tasks can run simultaneously:
Task T001: "Add anthropic config settings to backend/config.py"
Task T002: "Install anthropic package in backend/requirements.txt"
```

## Parallel Example: User Stories 2 & 3

```
# After US1 agent loop is working, US2 and US3 can run in parallel:
Task T009 [US2]: "Implement list_tasks executor in ai_agent.py"
Task T010-T012 [US3]: "Implement complete/delete/update executors in ai_agent.py"
# Note: Same file — true parallelism requires careful merging
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T002)
2. Complete Phase 2: Foundational (T003-T005)
3. Complete Phase 3: US1 - Create Task via NL (T006-T008)
4. **STOP and VALIDATE**: Test task creation through chat API end-to-end
5. Deploy/demo if ready — agent can create tasks via natural language

### Incremental Delivery

1. Setup + Foundational → Foundation ready (T001-T005)
2. Add US1 → Test task creation → **MVP** (T006-T008)
3. Add US2 → Test listing/filtering → Deploy (T009)
4. Add US3 → Test complete/delete/update → Deploy (T010-T012)
5. Add US4 → Test context resolution → Deploy (T013)
6. Polish → Tests + validation → Final release (T014-T017)

### Key Files Modified

| File | Phase | Tasks |
|------|-------|-------|
| `backend/config.py` | Setup | T001 |
| `backend/requirements.txt` | Setup | T002 |
| `backend/services/ai_agent.py` | Foundational + US1-US4 | T003-T013 |
| `backend/tests/conftest.py` | Polish | T014 |
| `backend/tests/test_ai_agent.py` | Polish | T015-T016 |

---

## Notes

- All tool executors follow the same pattern: `async _execute_<name>(parameters: dict, user_id: str) -> dict`
- All DB operations use SQLModel queries filtered by `owner_id = user_id` (same pattern as `backend/routes/tasks.py`)
- The agent loop is the critical path — implement it fully in T007 before adding more tools
- Error handling: tool errors return error dicts (Claude explains to user), API errors raise RuntimeError (chat API returns 502)
- Total: **17 tasks** across 7 phases
