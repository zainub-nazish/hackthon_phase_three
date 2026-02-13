# Feature Specification: Todo Management MCP Tools

**Feature Branch**: `009-mcp-tools`
**Created**: 2026-02-11
**Status**: Draft
**Input**: User description: "The AI chatbot agent should support Todo Management MCP tools including add, list, update, delete, and complete tasks. It should interact with the database through MCP and manage user todos via natural language commands."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Add a Task via Natural Language (Priority: P1)

An authenticated user sends a natural language message to the AI chatbot asking to create a new task. The agent invokes the `add_task` MCP tool, which creates the task in the database and returns a confirmation. The user sees a friendly response confirming the task was added.

**Why this priority**: Task creation proves the full MCP tool pipeline end-to-end — the agent receives a message, selects the correct MCP tool, executes it against the database, and returns a confirmation. This is the foundational capability upon which all other operations depend.

**Independent Test**: Send "Add a task to buy groceries" and verify (1) a new task appears in the user's database, (2) the agent confirms creation with the task title, and (3) the MCP tool call is recorded.

**Acceptance Scenarios**:

1. **Given** an authenticated user in a chat conversation, **When** they send "Add a task to buy milk", **Then** the system creates a task titled "Buy milk" in the user's task list and returns a confirmation including the task title.
2. **Given** an authenticated user, **When** they send "Create a task called 'Prepare slides' with description 'For Monday's meeting'", **Then** the system creates a task with the specified title and description, and confirms both.
3. **Given** an authenticated user, **When** the MCP tool execution fails (e.g., validation error), **Then** the system returns a user-friendly error message without exposing internal details.

---

### User Story 2 - List and Filter Tasks via Natural Language (Priority: P2)

An authenticated user asks the chatbot to show their tasks. The agent invokes the `list_tasks` MCP tool with appropriate filters (all, pending, or completed) and presents the results in a readable format.

**Why this priority**: Listing is the most common read operation and is a prerequisite for complete, delete, and update operations since users need to see tasks before referencing them.

**Independent Test**: Create several tasks (some completed, some pending), then ask "Show my tasks" and verify the response lists all tasks. Ask "Show pending tasks" and verify the filter applies correctly.

**Acceptance Scenarios**:

1. **Given** an authenticated user with existing tasks, **When** they send "Show my tasks", **Then** the system returns all their tasks with titles and completion status.
2. **Given** an authenticated user with mixed tasks, **When** they send "What tasks are still pending?", **Then** the system returns only incomplete tasks.
3. **Given** an authenticated user with no tasks, **When** they send "Show my tasks", **Then** the system responds with a friendly message indicating no tasks exist.

---

### User Story 3 - Complete a Task via Natural Language (Priority: P3)

An authenticated user asks the chatbot to mark a task as done. The agent identifies the target task (using `list_tasks` MCP tool if needed to resolve by name), then invokes the `complete_task` MCP tool, and confirms the completion.

**Why this priority**: Completing tasks is the primary workflow conclusion — users create tasks to eventually mark them done. It validates that the agent can chain MCP tool calls (list then complete) to resolve task references.

**Independent Test**: Create a task "Buy milk", then send "Mark 'Buy milk' as done" and verify the task's completion status changes to true.

**Acceptance Scenarios**:

1. **Given** an authenticated user with a task titled "Buy milk", **When** they send "Complete 'Buy milk'", **Then** the system marks the task as completed and confirms.
2. **Given** an authenticated user, **When** they reference a task that doesn't exist, **Then** the system responds that the task was not found and suggests listing tasks.
3. **Given** multiple tasks with similar names, **When** the user's reference is ambiguous, **Then** the system lists matching tasks and asks the user to clarify.

---

### User Story 4 - Update a Task via Natural Language (Priority: P4)

An authenticated user asks the chatbot to change a task's title or description. The agent identifies the target task, invokes the `update_task` MCP tool with the new values, and confirms the update.

**Why this priority**: Updating extends task management beyond create/complete by allowing corrections and refinements without deleting and recreating tasks.

**Independent Test**: Create a task "Buy milk", then send "Change 'Buy milk' to 'Buy almond milk'" and verify the task title is updated.

**Acceptance Scenarios**:

1. **Given** an authenticated user with a task titled "Buy milk", **When** they send "Rename 'Buy milk' to 'Buy almond milk'", **Then** the system updates the title and confirms the change.
2. **Given** an authenticated user, **When** they provide a new title and description, **Then** the system updates both fields and confirms.

---

### User Story 5 - Delete a Task via Natural Language (Priority: P5)

An authenticated user asks the chatbot to permanently remove a task. The agent identifies the target task, invokes the `delete_task` MCP tool, and confirms the deletion.

**Why this priority**: Deletion is the least frequent operation but necessary for task lifecycle management. It is destructive, so the agent should handle it carefully.

**Independent Test**: Create a task "Old notes", then send "Delete 'Old notes'" and verify the task is removed from the database.

**Acceptance Scenarios**:

1. **Given** an authenticated user with a task titled "Old notes", **When** they send "Delete 'Old notes'", **Then** the system deletes the task and confirms the deletion.
2. **Given** an authenticated user, **When** they try to delete a non-existent task, **Then** the system responds that the task was not found.

---

### Edge Cases

- What happens when the user sends a non-task message (e.g., "Hello" or "What can you do?")? The system responds conversationally without invoking any MCP tool.
- What happens when a user's message contains multiple intents (e.g., "Add 'Buy milk' and delete 'Old task'")? The system executes both MCP tools sequentially and confirms each action.
- What happens when the database is unavailable during MCP tool execution? The system returns a user-friendly error message without corrupting conversation state.
- What happens when the MCP tool returns an unexpected error format? The system gracefully handles the error and returns a generic failure message to the user.
- What happens when the user refers to a task contextually (e.g., "delete it" after discussing a task)? The system resolves the reference from conversation history.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST expose five MCP tools for todo management: `add_task`, `list_tasks`, `complete_task`, `delete_task`, and `update_task`.
- **FR-002**: Each MCP tool MUST operate exclusively on the authenticated user's tasks, enforcing the same user isolation as the existing task endpoints.
- **FR-003**: The `add_task` MCP tool MUST accept a required `title` parameter (1-255 characters) and an optional `description` parameter (max 2000 characters), and create a new task in the database.
- **FR-004**: The `list_tasks` MCP tool MUST accept an optional `status` filter (`all`, `pending`, `completed`) defaulting to `all`, and return the user's tasks with their titles, IDs, and completion status.
- **FR-005**: The `complete_task` MCP tool MUST accept a required `task_id` parameter and mark the specified task as completed in the database.
- **FR-006**: The `delete_task` MCP tool MUST accept a required `task_id` parameter and permanently remove the specified task from the database.
- **FR-007**: The `update_task` MCP tool MUST accept a required `task_id` and at least one of `title` or `description`, and update the specified fields in the database.
- **FR-008**: The AI agent MUST use MCP tools to interact with the database rather than making direct database calls from inline tool functions.
- **FR-009**: The AI agent MUST select the appropriate MCP tool based on the user's natural language intent (e.g., "add a task" maps to `add_task`, "show my tasks" maps to `list_tasks`).
- **FR-010**: The AI agent MUST return friendly, human-readable confirmation messages after successful MCP tool execution.
- **FR-011**: The AI agent MUST return user-friendly error messages when MCP tool execution fails, without exposing internal system details.
- **FR-012**: All MCP tool calls, parameters, and results MUST be persisted via the existing tool call storage mechanism (ToolCall model).
- **FR-013**: The AI agent MUST maintain the existing service interface contract: `async generate_response(messages: list[dict], user_id: str) -> AgentResponse`.
- **FR-014**: When the agent cannot determine the `task_id` for a modification operation, it MUST first call `list_tasks` to find matching tasks, then resolve automatically (one match) or ask the user to clarify (multiple matches).
- **FR-015**: The AI agent MUST respond conversationally to non-task messages (greetings, capability questions) without invoking any MCP tools.

### Key Entities

- **MCP Tool**: A standardized callable tool exposed via the Model Context Protocol. Each tool has a name, description, input schema, and executes a specific task management operation against the database. Tools enforce user isolation by requiring user identity context.
- **MCP Tool Server**: The service layer that registers, validates, and executes MCP tools. It receives tool invocation requests from the AI agent and returns structured results.
- **AI Agent**: The intelligent service that processes natural language messages, selects appropriate MCP tools, executes them, and generates user-facing responses. Consumes conversation history and user identity as context.
- **Tool Call Record**: A persistent record of each MCP tool invocation, including the tool name, input parameters, execution result, and status. Used for auditability and debugging.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can create a task through natural language in a single conversational turn at least 95% of the time when using clear phrasing.
- **SC-002**: Users can list their tasks and receive a formatted response within 10 seconds of sending the request.
- **SC-003**: Users can complete, delete, or update a task by referencing it by name, with the agent correctly identifying the target task at least 90% of the time when the name is unambiguous.
- **SC-004**: All five MCP tool operations return appropriate user-friendly confirmation or error messages with zero silent failures.
- **SC-005**: The agent never fabricates task data — all task references in responses correspond to actual tasks in the user's list.
- **SC-006**: Non-task messages receive helpful responses without invoking any MCP tools.
- **SC-007**: MCP tool execution adds no more than 2 seconds of overhead compared to the previous inline tool approach, measured end-to-end per user request.

## Assumptions

- The chat API from 007-chat-api is fully implemented and provides message persistence, conversation continuity, tool call storage, and the `AIAgentService` interface.
- The existing Task CRUD database operations are stable and will be reused by MCP tool handlers.
- The MCP tool layer is an internal server-side abstraction — it does not expose external MCP endpoints. The AI agent consumes MCP tools internally.
- Non-streaming responses are used (consistent with 007-chat-api).
- The agent operates within the existing authentication and user isolation boundaries.
- The Anthropic Claude API is used as the underlying language model, with tool-use capabilities for MCP tool invocation.
- Multi-step tool execution (e.g., list then complete) happens within a single agent invocation.
