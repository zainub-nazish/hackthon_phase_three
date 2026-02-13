# Feature Specification: AI Todo Agent

**Feature Branch**: `008-ai-agent`
**Created**: 2026-02-10
**Status**: Draft
**Input**: User description: "Spec-6 — AI Agent: AI Todo Assistant that manages tasks via natural language. Supports intent-to-tool mapping (add, list, complete, delete, update tasks), contextual reference resolution, friendly confirmations, and graceful error handling."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Create a Task via Natural Language (Priority: P1)

An authenticated user types a natural language message like "Add a task to buy milk" in the chat interface. The AI agent understands the intent (create a task), extracts the task title and optional description, executes the task creation tool, and returns a friendly confirmation message including the created task's details.

**Why this priority**: Task creation is the single most impactful action — it proves the full AI agent pipeline works end-to-end (message understanding, tool selection, tool execution, confirmation). Without this, the agent is just a chatbot with no actionable capability.

**Independent Test**: Can be fully tested by sending a message like "Add a task to buy groceries" and verifying that (1) a new task appears in the user's task list, (2) the agent's response confirms the creation with the task title, and (3) the tool call is recorded in the database.

**Acceptance Scenarios**:

1. **Given** an authenticated user in a chat conversation, **When** they send "Add a task to buy milk", **Then** the system creates a task with title "Buy milk" in the user's task list and returns a confirmation message including the task title.
2. **Given** an authenticated user, **When** they send "Create a task called 'Prepare presentation' with description 'Slides for Monday meeting'", **Then** the system creates a task with the specified title and description, and confirms with both fields.
3. **Given** an authenticated user, **When** they send a message with no clear title like "Add a task", **Then** the system asks the user to provide a task title rather than creating an empty or generic task.
4. **Given** an authenticated user, **When** the task creation tool fails (e.g., validation error), **Then** the system returns a user-friendly error message explaining what went wrong without exposing internal details.

---

### User Story 2 - List and Query Tasks via Natural Language (Priority: P2)

An authenticated user asks the AI agent to show their tasks — either all tasks, only pending tasks, or only completed tasks. The agent executes the listing tool with the appropriate filter and presents the results in a readable format.

**Why this priority**: Listing tasks is the prerequisite for all other task operations (complete, delete, update) since users need to see their tasks to reference them. It's also the most common read operation.

**Independent Test**: Can be tested by first creating several tasks (some completed, some pending), then asking "Show my tasks" and verifying the response includes all tasks. Then asking "Show completed tasks" and verifying the filter works.

**Acceptance Scenarios**:

1. **Given** an authenticated user with existing tasks, **When** they send "Show my tasks", **Then** the system returns a list of all their tasks with titles and completion status.
2. **Given** an authenticated user with mixed tasks, **When** they send "What tasks are pending?", **Then** the system returns only incomplete tasks.
3. **Given** an authenticated user with mixed tasks, **When** they send "Show completed tasks", **Then** the system returns only completed tasks.
4. **Given** an authenticated user with no tasks, **When** they send "Show my tasks", **Then** the system responds with a friendly message indicating no tasks exist (e.g., "You don't have any tasks yet").
5. **Given** an authenticated user, **When** they ask a general question like "What can you help me with?", **Then** the system responds with a helpful description of its capabilities without invoking any tool.

---

### User Story 3 - Complete, Delete, and Update Tasks via Natural Language (Priority: P3)

An authenticated user instructs the AI agent to modify an existing task — mark it as done, delete it, or change its title/description. The agent identifies the target task (by name matching or by listing tasks first if ambiguous), executes the appropriate tool, and confirms the action.

**Why this priority**: These operations complete the full CRUD cycle for task management. They depend on the listing capability (US2) for task identification and the creation capability (US1) for having tasks to act on.

**Independent Test**: Can be tested by creating a task, then sending "Complete 'Buy milk'" and verifying the task is marked as completed. Similarly for delete ("Delete the task about groceries") and update ("Change 'Buy milk' to 'Buy almond milk'").

**Acceptance Scenarios**:

1. **Given** an authenticated user with a task titled "Buy milk", **When** they send "Mark 'Buy milk' as done", **Then** the system marks that task as completed and confirms with a success message.
2. **Given** an authenticated user with a task titled "Old meeting notes", **When** they send "Delete 'Old meeting notes'", **Then** the system deletes the task and confirms the deletion.
3. **Given** an authenticated user with a task titled "Buy milk", **When** they send "Change 'Buy milk' to 'Buy almond milk'", **Then** the system updates the task title and confirms the change.
4. **Given** an authenticated user, **When** they send "Complete task 'Nonexistent task'", **Then** the system responds with "I couldn't find that task" and suggests listing tasks to find the correct one.
5. **Given** an authenticated user with multiple tasks that partially match (e.g., "Buy milk" and "Buy eggs"), **When** they send "Delete the buy task", **Then** the system lists the matching tasks and asks the user to clarify which one they mean.
6. **Given** an authenticated user, **When** the modification tool fails, **Then** the system returns a user-friendly error message and the task remains unchanged.

---

### User Story 4 - Contextual Reference Resolution (Priority: P4)

An authenticated user refers to a task using conversational context rather than explicit names — for example, saying "delete it" after discussing a specific task, or "mark that one as done" after the agent listed tasks. The agent resolves these references using conversation history and executes the appropriate action.

**Why this priority**: Contextual understanding makes the agent feel natural and conversational rather than requiring rigid command syntax. However, it builds on all previous stories and is an enhancement to usability rather than core functionality.

**Independent Test**: Can be tested by (1) creating a task, (2) the agent confirming with the task name, (3) user saying "delete it", and verifying the agent correctly identifies the referenced task and deletes it.

**Acceptance Scenarios**:

1. **Given** the agent just confirmed creating a task "Buy milk", **When** the user says "Actually, delete it", **Then** the system identifies "it" as the just-created task and deletes it.
2. **Given** the agent just listed tasks including "Task 3: Buy groceries", **When** the user says "Complete that one", **Then** the system identifies the most recently referenced task and completes it.
3. **Given** no prior task context in the conversation, **When** the user says "Delete it", **Then** the system asks the user to specify which task they mean rather than guessing or hallucinating.
4. **Given** conversation history with multiple tasks mentioned, **When** the user uses an ambiguous reference, **Then** the system asks for clarification rather than acting on the wrong task.

---

### Edge Cases

- What happens when the user sends a message that is not related to task management (e.g., "What's the weather?")? The system responds conversationally but explains it can only help with task management.
- What happens when the user's message contains multiple intents (e.g., "Add 'Buy milk' and delete 'Old task'")? The system executes both operations sequentially and confirms each one.
- What happens when the user provides a task title that exactly matches an existing task for creation? The system creates the task regardless (duplicates are allowed).
- What happens when tool execution times out? The system returns a friendly timeout message without corrupting conversation or task state.
- What happens when the user sends a message in a different language? The system attempts to understand and respond in the same language, or falls back to English with a helpful message.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST replace the existing AI agent stub (`backend/services/ai_agent.py`) with a real AI-powered agent that processes natural language messages and returns actionable responses.
- **FR-002**: System MUST define a system prompt that instructs the agent to act as a Todo Assistant, with clear role definition and behavioral guidelines.
- **FR-003**: System MUST provide the agent with five tools for task management: `add_task` (create), `list_tasks` (read), `complete_task` (update status), `delete_task` (remove), and `update_task` (modify fields).
- **FR-004**: Each tool MUST operate on the authenticated user's tasks only, enforcing the same user isolation as the existing task endpoints.
- **FR-005**: The agent MUST detect user intent from natural language input and select the appropriate tool based on the intent-to-tool mapping defined in the system prompt.
- **FR-006**: The agent MUST extract required parameters from the user's message (e.g., task title for creation, task identifier for completion/deletion).
- **FR-007**: When a required parameter is missing or ambiguous, the agent MUST ask the user for clarification rather than guessing or failing silently.
- **FR-008**: The agent MUST return friendly, human-readable confirmation messages after successful tool execution (e.g., "Task 'Buy milk' added").
- **FR-009**: The agent MUST return user-friendly error messages when tool execution fails, without exposing internal system details.
- **FR-010**: The agent MUST use conversation history (provided by the chat API) to resolve contextual references like "it", "that task", or "the last one".
- **FR-011**: The agent MUST never fabricate or hallucinate task data — it must only reference tasks that actually exist in the user's task list.
- **FR-012**: The agent MUST respond conversationally to non-task messages (e.g., greetings, capability questions) without invoking any tools.
- **FR-013**: All tool calls, their parameters, and results MUST be persisted via the existing tool call storage mechanism from the chat API (007-chat-api).
- **FR-014**: The agent MUST maintain the existing `AIAgentService` interface contract: `async generate_response(messages: list[dict], user_id: str) -> AgentResponse`.
- **FR-015**: The `add_task` tool MUST accept a required `title` parameter and an optional `description` parameter.
- **FR-016**: The `list_tasks` tool MUST accept an optional `status` filter parameter with values: `pending`, `completed`, or `all` (default: `all`).
- **FR-017**: The `complete_task` tool MUST accept a required `task_id` parameter identifying the task to mark as completed.
- **FR-018**: The `delete_task` tool MUST accept a required `task_id` parameter identifying the task to remove.
- **FR-019**: The `update_task` tool MUST accept a required `task_id` and optional `title` and `description` parameters.
- **FR-020**: When the agent cannot determine the `task_id` for a modification operation, it MUST first call `list_tasks` to find matching tasks, then either resolve automatically (if exactly one match) or ask the user to choose (if multiple matches).

### Key Entities

- **AI Agent**: The intelligent service that processes natural language messages, selects appropriate tools, and generates responses. Receives conversation history and user identity as context. Maintains the system prompt that defines its role and behavior.
- **Tool**: A callable function available to the agent that performs a specific task operation. Each tool has a name, description, required and optional parameters, and returns a result. Tools map to existing task management operations.
- **System Prompt**: The instruction set that configures the agent's personality, role, capabilities, tool usage guidelines, error handling behavior, and response formatting. This is the "brain" of the agent.
- **Tool Call**: A record of the agent invoking a tool, including the tool name, input parameters, and execution result. Persisted by the chat API for auditability and debugging.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can create a task through natural language in a single conversational turn at least 95% of the time when using clear phrasing (e.g., "Add a task to buy milk").
- **SC-002**: Users can list their tasks and receive a formatted response within 10 seconds of sending the request.
- **SC-003**: Users can complete, delete, or update a task by referencing it by name, with the agent correctly identifying the target task at least 90% of the time when the name is unambiguous.
- **SC-004**: All five tool operations (add, list, complete, delete, update) return appropriate user-friendly confirmation or error messages with zero cases of silent failures.
- **SC-005**: The agent never fabricates task data — all task references in responses correspond to actual tasks in the user's list, verified across all test scenarios.
- **SC-006**: The agent correctly resolves contextual references ("it", "that task") from conversation history at least 80% of the time when the context is within the last 5 messages.
- **SC-007**: Non-task messages (greetings, capability questions) receive helpful responses without invoking any tools, verified across common conversational patterns.

## Assumptions

- The chat API from 007-chat-api is fully implemented and provides: message persistence, conversation continuity, tool call storage, and the `AIAgentService` interface contract.
- The existing Task CRUD endpoints (`/api/v1/users/{user_id}/tasks`) are stable and will be used by the agent's tools internally to perform task operations.
- The AI language model provider and SDK choice will be determined during the planning phase. This spec defines the agent's behavior, not its implementation technology.
- Non-streaming responses are used (consistent with 007-chat-api). The agent returns a complete response, not a stream.
- The agent operates within the existing authentication and user isolation boundaries — tools only access the authenticated user's data.
- The system prompt will be iterable — initial deployment uses a reasonable default, with refinement based on real usage.
- Multi-step tool execution (e.g., list then delete) happens within a single agent invocation — the agent can call multiple tools in sequence to fulfill one user request.
