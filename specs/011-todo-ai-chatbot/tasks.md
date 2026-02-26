# Tasks: Todo AI Chatbot

**Input**: Design documents from `/specs/011-todo-ai-chatbot/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/

**Tests**: Tests are included — existing test files need updating for the Anthropic → OpenAI Agents SDK migration.

**Organization**: Tasks are grouped by user story. Since this is a migration (not greenfield), the foundational phase contains the core rewrite work, and user story phases focus on per-story validation and tool verification.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Backend**: `backend/` at repository root
- **Frontend**: `frontend/` at repository root
- **Specs**: `specs/011-todo-ai-chatbot/`

---

## Phase 1: Setup (Dependencies & Environment)

**Purpose**: Replace Anthropic SDK with OpenAI Agents SDK in dependencies and configuration.

- [x] T001 Replace `anthropic>=0.79.0` with `openai-agents>=0.0.7` in `backend/requirements.txt`
- [x] T002 [P] Replace `ANTHROPIC_API_KEY` and `ANTHROPIC_MODEL` settings with `OPENAI_API_KEY: str` in `backend/config.py`
- [x] T003 [P] Add `OPENAI_API_KEY` to `backend/.env` and document in `backend/.env.example`
- [x] T004 Run `pip install -r backend/requirements.txt` and verify `from agents import Agent, Runner` and `from agents.mcp import MCPServerStdio` import without error

**Checkpoint**: Dependencies installed, config updated, OpenAI Agents SDK importable.

---

## Phase 2: Foundational (Core Migration — Blocks All User Stories)

**Purpose**: Rewrite the AI agent service, update MCP stdio entry point, update chat route, and clean up deprecated files. ALL user stories depend on this phase.

**CRITICAL**: No user story work can begin until this phase is complete.

### Database Model Verification

- [x] T005 Verify existing Task, Conversation, Message, ToolCall models in `backend/models/database.py` match `specs/011-todo-ai-chatbot/data-model.md` — confirm field types, constraints, and relationships (owner_id maps to user_id)
- [x] T006 [P] Verify request/response schemas in `backend/models/schemas.py` match `specs/011-todo-ai-chatbot/contracts/chat-api.yaml` — ChatRequest, ChatResponse, ToolCallRecord

### MCP Server Preparation

- [x] T007 Verify all 5 MCP tools in `backend/services/mcp_tools.py` match `specs/011-todo-ai-chatbot/contracts/mcp-tools.yaml` — add_task, list_tasks, complete_task, delete_task, update_task
- [x] T008 Add `if __name__ == "__main__"` stdio entry point to `backend/services/mcp_tools.py` so it can be launched via `MCPServerStdio(command="python", args=["mcp_tools.py"])`

### Agent Service Rewrite

- [x] T009 Rewrite `backend/services/ai_agent.py` — replace Anthropic Claude integration with OpenAI Agents SDK: create Agent with system prompt from plan.md Phase 4, connect MCP server via `MCPServerStdio`, use `Runner.run()` for stateless per-request execution, return response text + tool_calls list
- [x] T010 Delete `backend/services/mcp_bridge.py` — no longer needed since Agents SDK has native MCP support
- [x] T011 Update `backend/services/__init__.py` if it imports from `mcp_bridge`

### Chat Route Update

- [x] T012 Update `backend/routes/chat.py` — change agent service import and call signature to match rewritten `ai_agent.py`, preserve conversation loading/persistence logic and response mapping

### Test Infrastructure Update

- [x] T013 Update agent mocking fixtures in `backend/tests/conftest.py` — replace Anthropic mock with OpenAI Agents SDK mock/stub
- [x] T014 Rewrite `backend/tests/test_ai_agent.py` — test new agent interface: message processing, tool call extraction, error handling, graceful fallback when API key missing
- [x] T015 Update `backend/tests/test_chat.py` — adjust for new agent service interface, verify chat endpoint still returns correct ChatResponse shape

**Checkpoint**: Foundation ready — agent processes messages via OpenAI Agents SDK with MCP tools. All existing tests updated and passing.

---

## Phase 3: User Story 1 — Natural Language Task Creation (Priority: P1) MVP

**Goal**: Users can create tasks by chatting naturally (e.g., "remind me to buy groceries").

**Independent Test**: Send "Add a task to review the quarterly report" via `POST /api/v1/users/{user_id}/chat` and verify a new task is created in the database.

### Implementation for User Story 1

- [x] T016 [US1] Verify `add_task` MCP tool creates tasks with correct title, description, and owner_id isolation in `backend/services/mcp_tools.py`
- [x] T017 [US1] Verify agent system prompt in `backend/services/ai_agent.py` includes instructions to map natural language creation intents ("remind me to...", "add a task...", "I need to...") to `add_task` tool
- [x] T018 [US1] Verify agent does NOT call task tools for ambiguous/non-task messages (e.g., "hello", "how are you") — responds conversationally only
- [x] T019 [US1] Verify agent returns confirmation message with task details after successful creation

**Checkpoint**: Task creation works via natural language chat. Agent correctly maps creation intents and ignores non-task messages.

---

## Phase 4: User Story 2 — View and Filter Tasks via Chat (Priority: P1)

**Goal**: Users can ask to see their tasks filtered by status (all, pending, completed).

**Independent Test**: Send "show me my pending tasks" via chat and verify only incomplete tasks are listed in the response.

### Implementation for User Story 2

- [x] T020 [US2] Verify `list_tasks` MCP tool supports status filter parameter (all/pending/completed) and returns correct filtered results in `backend/services/mcp_tools.py`
- [x] T021 [US2] Verify agent maps listing intents ("show my tasks", "what's left to do?", "list completed tasks") to `list_tasks` with correct status parameter
- [x] T022 [US2] Verify agent formats task list in a readable way in the response (titles, status, descriptions)
- [x] T023 [US2] Verify agent handles empty task list gracefully ("No tasks found — would you like to create one?")

**Checkpoint**: Task listing with filters works via natural language chat.

---

## Phase 5: User Story 3 — Complete and Delete Tasks via Chat (Priority: P1)

**Goal**: Users can mark tasks as done or delete them by describing them in natural language.

**Independent Test**: Send "I'm done with buying groceries" and verify the matching task's `completed` field changes to `true`.

### Implementation for User Story 3

- [x] T024 [US3] Verify `complete_task` MCP tool marks correct task as completed with owner_id enforcement in `backend/services/mcp_tools.py`
- [x] T025 [P] [US3] Verify `delete_task` MCP tool permanently removes correct task with owner_id enforcement in `backend/services/mcp_tools.py`
- [x] T026 [US3] Verify agent maps completion intents ("I'm done with...", "mark X as done", "finished the...") to `complete_task` tool
- [x] T027 [US3] Verify agent maps deletion intents ("delete the...", "remove the...", "get rid of...") to `delete_task` tool
- [x] T028 [US3] Verify agent reports "no matching task found" when task reference doesn't match any existing task

**Checkpoint**: Task completion and deletion work via natural language. Agent correctly identifies tasks by name.

---

## Phase 6: User Story 4 — Update Existing Tasks via Chat (Priority: P2)

**Goal**: Users can update task titles and descriptions through conversation.

**Independent Test**: Send "rename the groceries task to weekly shopping" and verify the task title is updated in the database.

### Implementation for User Story 4

- [x] T029 [US4] Verify `update_task` MCP tool correctly updates title and/or description with owner_id enforcement in `backend/services/mcp_tools.py`
- [x] T030 [US4] Verify agent maps update intents ("rename...", "change the title...", "add a description to...") to `update_task` tool with correct parameters
- [x] T031 [US4] Verify agent confirms the update with before/after details in the response

**Checkpoint**: Task updates work via natural language chat.

---

## Phase 7: User Story 5 — Persistent Conversation History (Priority: P2)

**Goal**: Chat conversations persist across sessions — users see previous messages when they return.

**Independent Test**: Send messages, then call `GET /api/v1/users/{user_id}/conversations/{id}/messages` and verify all messages (user + assistant) are returned in order.

### Implementation for User Story 5

- [x] T032 [US5] Verify conversation auto-creation logic in `backend/routes/chat.py` — new conversation created when `conversation_id` is null, existing conversation reused when provided
- [x] T033 [US5] Verify both user message and assistant response are persisted to `Message` table after each chat interaction in `backend/routes/chat.py`
- [x] T034 [US5] Verify conversation history is loaded from DB and passed to agent on every request — agent receives full message history, not just latest message
- [x] T035 [US5] Verify `GET /api/v1/users/{user_id}/conversations` returns most recent conversation metadata
- [x] T036 [P] [US5] Verify `GET /api/v1/users/{user_id}/conversations/{id}/messages` returns all messages in chronological order

**Checkpoint**: Conversation persistence works — messages survive across sessions, agent receives full history.

---

## Phase 8: User Story 6 — Multi-Step Task Resolution (Priority: P2)

**Goal**: Agent handles requests requiring multiple tool calls transparently (e.g., "delete the meeting task" → list_tasks → delete_task).

**Independent Test**: With a task "Team meeting prep" in the database, send "delete the meeting task" and verify the agent first lists tasks, identifies the match, then deletes it — all in one response.

### Implementation for User Story 6

- [x] T037 [US6] Verify agent system prompt in `backend/services/ai_agent.py` instructs: "When a user refers to a task by name (not ID), FIRST call list_tasks, THEN use the returned ID for the action"
- [x] T038 [US6] Verify Agents SDK Runner handles the tool-call loop automatically — agent calls list_tasks, receives results, then calls delete_task/complete_task/update_task with the correct ID
- [x] T039 [US6] Verify agent handles ambiguous multi-match scenario — when multiple tasks match a vague description, agent lists matches and asks user to clarify
- [x] T040 [US6] Verify agent handles batch operations — "complete all my shopping tasks" finds and completes multiple matching tasks

**Checkpoint**: Multi-step reasoning works transparently. Agent chains tool calls without user intervention.

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Final cleanup, test verification, and E2E validation.

- [x] T041 Run existing `backend/tests/test_mcp_tools.py` — verify no regressions in MCP tools
- [x] T042 [P] Run existing `backend/tests/test_chat_isolation.py` — verify cross-user data isolation
- [x] T043 Remove all remaining references to `anthropic` from backend codebase (imports, comments, config)
- [x] T044 [P] Verify frontend chat page loads and works end-to-end: login → chat → create task → list tasks → complete task → verify via task list page
- [x] T045 Run `specs/011-todo-ai-chatbot/quickstart.md` validation steps to confirm setup guide is accurate

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 completion — BLOCKS all user stories
- **User Stories (Phase 3–8)**: All depend on Phase 2 completion
  - US1, US2, US3 (P1) can proceed in parallel after Phase 2
  - US4, US5, US6 (P2) can proceed in parallel after Phase 2
  - US6 (Multi-Step) benefits from US3 completion (delete/complete tools validated)
- **Polish (Phase 9)**: Depends on all user stories being complete

### User Story Dependencies

- **US1 (Task Creation)**: After Phase 2 — no dependency on other stories
- **US2 (View/Filter)**: After Phase 2 — no dependency on other stories
- **US3 (Complete/Delete)**: After Phase 2 — no dependency on other stories
- **US4 (Update)**: After Phase 2 — no dependency on other stories
- **US5 (History)**: After Phase 2 — no dependency on other stories
- **US6 (Multi-Step)**: After Phase 2 — benefits from US3 validation but not blocked by it

### Within Each User Story

- Tool verification before agent behavior verification
- Agent behavior before edge case handling
- Story checkpoint before moving to next

### Parallel Opportunities

**Phase 1 (Setup)**:
```
T002 (config.py) and T003 (.env files) can run in parallel — different files
```

**Phase 2 (Foundational)**:
```
T005 (model verification) and T006 (schema verification) can run in parallel
T007 (MCP tool verification) can run parallel with T005/T006
T013 (conftest), T014 (test_ai_agent), T015 (test_chat) can run after T009
```

**User Stories (Phase 3–8)**:
```
All 6 user story phases can run in parallel after Phase 2 completes
Within US3: T024 (complete_task) and T025 (delete_task) can run in parallel
Within US5: T035 (conversations endpoint) and T036 (messages endpoint) can run in parallel
```

---

## Implementation Strategy

### MVP First (User Stories 1–3 Only)

1. Complete Phase 1: Setup (T001–T004)
2. Complete Phase 2: Foundational (T005–T015) — **core migration work**
3. Complete Phase 3: US1 — Task Creation (T016–T019)
4. **STOP and VALIDATE**: Test task creation via chat
5. Complete Phase 4: US2 — View/Filter (T020–T023)
6. Complete Phase 5: US3 — Complete/Delete (T024–T028)
7. **STOP and VALIDATE**: Full P1 story coverage — MVP ready

### Incremental Delivery

1. Setup + Foundational → Agent migrated, core working
2. Add US1 → Task creation via chat (MVP!)
3. Add US2 → Task viewing via chat
4. Add US3 → Task lifecycle complete
5. Add US4 → Task updates
6. Add US5 → History persistence
7. Add US6 → Multi-step intelligence
8. Polish → Final cleanup and validation

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- This is a **migration**, not greenfield — most code already exists
- Phase 2 (Foundational) is the **heaviest phase** — agent rewrite + test updates
- User story phases are primarily **verification and validation** of the new agent
- The agent's system prompt (T009) is the key to all user stories — it defines how intents map to tools
- Commit after each task or logical group
