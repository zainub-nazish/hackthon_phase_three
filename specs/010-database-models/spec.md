# Feature Specification: Database Models for Todo AI System

**Feature Branch**: `010-database-models`
**Created**: 2026-02-11
**Status**: Draft
**Input**: User description: "Define database models for the Todo AI system — Task, Conversation, Message. Specify fields, types, relationships, constraints, and rules. No code."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Create and Manage Tasks (Priority: P1)

A user creates, reads, updates, completes, and deletes personal todo items. Each task has a title, optional description, and completion status. Tasks are private to their owner and persist across sessions.

**Why this priority**: Tasks are the core data entity of the application. Without persistent task storage, no other feature (chat, AI tools) has a purpose.

**Independent Test**: Create a task with title "Buy groceries", verify it persists with correct owner, default incomplete status, and auto-generated timestamps. Update its title, mark complete, then delete it — confirming each state change is reflected.

**Acceptance Scenarios**:

1. **Given** no tasks exist for a user, **When** the user creates a task with title "Buy milk", **Then** the system stores a task with a unique identifier, the user's ID as owner, the title "Buy milk", no description, completed=false, and auto-generated created/updated timestamps.
2. **Given** a task exists for user A, **When** user B attempts to read, update, or delete that task, **Then** the system denies access (task not found from user B's perspective).
3. **Given** a task with title "Old title", **When** the owner updates the title to "New title", **Then** the system persists the new title and refreshes the updated timestamp.
4. **Given** an incomplete task, **When** the owner marks it as complete, **Then** the system sets completed=true and refreshes the updated timestamp.

---

### User Story 2 - Store Chat Conversations (Priority: P2)

A user initiates a chat session with the AI assistant. The system creates a conversation record that groups related messages together. Conversations are private to their owner and track creation and last-activity timestamps.

**Why this priority**: Conversations provide the container for chat messages and tool calls. Without conversation persistence, multi-turn AI interactions cannot be maintained across page reloads.

**Independent Test**: Create a conversation for a user, verify it has a unique ID, correct owner, and auto-generated timestamps. Confirm a second user cannot access it.

**Acceptance Scenarios**:

1. **Given** a user starts a new chat, **When** the system creates a conversation, **Then** it has a unique identifier, the user's ID as owner, and auto-generated created/updated timestamps.
2. **Given** a conversation exists, **When** a new message is added, **Then** the conversation's updated timestamp refreshes to reflect latest activity.
3. **Given** user A owns a conversation, **When** user B requests it, **Then** the system returns not found.

---

### User Story 3 - Persist Chat Messages (Priority: P2)

Messages within a conversation are stored in chronological order. Each message records the sender role (user or assistant) and text content. Messages are immutable once created — they represent a historical record of the conversation.

**Why this priority**: Tied to P2 because messages require conversations. Message persistence enables multi-turn AI interactions where the assistant can reference earlier context.

**Independent Test**: Create a conversation, add a user message "Hello" and an assistant message "Hi there!", verify both are stored in order with correct roles, content, and timestamps. Verify messages cannot exist without a parent conversation.

**Acceptance Scenarios**:

1. **Given** a conversation exists, **When** a user sends a message, **Then** the system stores it with role "user", the message content, the conversation's ID, and an auto-generated timestamp.
2. **Given** a conversation with messages, **When** messages are retrieved, **Then** they are returned in chronological order (oldest first).
3. **Given** a message is stored, **When** queried, **Then** its content and role are immutable — no update path exists.
4. **Given** no conversation with the specified ID exists, **When** a message is created referencing it, **Then** the system rejects the operation (referential integrity enforced).

---

### User Story 4 - Track AI Tool Invocations (Priority: P3)

When the AI assistant uses tools (e.g., creating a task, listing tasks), the system records each tool invocation as a child of the assistant's message. This provides auditability and debugging capability for AI actions.

**Why this priority**: Tool call tracking is supplementary to core chat and task functionality. It adds observability but is not required for basic operation.

**Independent Test**: Create a conversation with an assistant message, attach a tool call record with name "add_task", input parameters, output result, and status "success". Verify the tool call is linked to the correct message and all fields are persisted.

**Acceptance Scenarios**:

1. **Given** an assistant message exists, **When** the AI invokes a tool, **Then** the system stores a tool call record with the tool name, input parameters, output result, execution status, and a timestamp.
2. **Given** a tool call fails, **When** the system records it, **Then** the status is "error" and the result contains the error details.
3. **Given** a tool call record exists, **When** queried by its parent message ID, **Then** all tool calls for that message are returned.

---

### Edge Cases

- What happens when a task title is empty or exceeds 255 characters? The system rejects the operation with a validation error.
- What happens when a task description exceeds 2000 characters? The system rejects the operation with a validation error.
- What happens when a message has an invalid role (not "user" or "assistant")? The system rejects the operation.
- What happens when a conversation is deleted? All child messages and their tool calls are orphaned or cascade-deleted (system-defined policy).
- What happens when two tasks are created at the exact same timestamp for the same user? Both are stored — uniqueness is on ID, not timestamp.
- What happens when message content is empty? The system rejects the operation — messages must have non-empty content.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST assign a globally unique identifier to every Task, Conversation, Message, and ToolCall record at creation time.
- **FR-002**: System MUST enforce user isolation — each Task and Conversation is owned by exactly one user, identified by a user identifier string. Users MUST NOT access other users' data.
- **FR-003**: System MUST auto-generate creation timestamps for all records at the time of insertion.
- **FR-004**: System MUST auto-generate and update "last modified" timestamps on Task and Conversation records whenever they are changed.
- **FR-005**: System MUST enforce that every Task has a non-empty title of 255 characters or fewer.
- **FR-006**: System MUST allow Task descriptions to be optional (nullable), with a maximum length of 2000 characters when provided.
- **FR-007**: System MUST default a Task's completion status to "not completed" (false) at creation.
- **FR-008**: System MUST enforce that every Message belongs to exactly one Conversation via a foreign key relationship.
- **FR-009**: System MUST restrict Message role values to "user" or "assistant".
- **FR-010**: System MUST enforce that every ToolCall belongs to exactly one Message via a foreign key relationship.
- **FR-011**: System MUST store ToolCall parameters and results as serialized text (to accommodate varying structures across different tools).
- **FR-012**: System MUST restrict ToolCall status values to "success" or "error".
- **FR-013**: System MUST enforce that Message content is non-empty.
- **FR-014**: System MUST support efficient lookup of Tasks by owner (indexed).
- **FR-015**: System MUST support efficient lookup of Messages by conversation (indexed).
- **FR-016**: System MUST support efficient lookup of ToolCalls by message (indexed).

### Key Entities

- **Task**: A personal todo item owned by a user. Has a title, optional description, completion flag, and timestamps. Core entity for the todo management domain.
- **Conversation**: A chat session between a user and the AI assistant. Groups Messages together. Tracks creation and last-activity timestamps.
- **Message**: A single utterance within a Conversation. Attributed to either the user or the assistant. Immutable once created. Ordered chronologically.
- **ToolCall**: A record of an AI tool invocation attached to an assistant Message. Stores the tool name, input/output data, and execution status. Provides an audit trail for AI actions.

### Relationships

| Relationship | Type | Description |
|-------------|------|-------------|
| User -> Task | One-to-Many | A user owns zero or more tasks |
| User -> Conversation | One-to-Many | A user owns zero or more conversations |
| Conversation -> Message | One-to-Many | A conversation contains zero or more messages |
| Message -> ToolCall | One-to-Many | An assistant message may have zero or more tool calls |

### Field Definitions

#### Task

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | Unique Identifier | Primary key, auto-generated | Globally unique task ID |
| owner_id | String | Required, indexed | Owning user's identifier |
| title | String | Required, max 255 characters, non-empty | Task title |
| description | String | Optional (nullable), max 2000 characters | Task details |
| completed | Boolean | Required, default false | Completion status |
| created_at | Timestamp | Required, auto-generated on create | When the task was created |
| updated_at | Timestamp | Required, auto-updated on modify | When the task was last changed |

#### Conversation

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | Unique Identifier | Primary key, auto-generated | Globally unique conversation ID |
| owner_id | String | Required, indexed | Owning user's identifier |
| created_at | Timestamp | Required, auto-generated on create | When the conversation started |
| updated_at | Timestamp | Required, auto-updated on modify | When the last activity occurred |

#### Message

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | Unique Identifier | Primary key, auto-generated | Globally unique message ID |
| conversation_id | Unique Identifier | Required, foreign key -> Conversation.id, indexed | Parent conversation |
| role | String | Required, max 20 characters, enum: "user" / "assistant" | Who sent the message |
| content | String | Required, non-empty | Message text |
| created_at | Timestamp | Required, auto-generated on create | When the message was sent |

#### ToolCall

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | Unique Identifier | Primary key, auto-generated | Globally unique tool call ID |
| message_id | Unique Identifier | Required, foreign key -> Message.id, indexed | Parent assistant message |
| tool_name | String | Required, max 100 characters | Name of the invoked tool |
| parameters | Text | Required | Serialized input parameters |
| result | Text | Required | Serialized output result |
| status | String | Required, max 20 characters, enum: "success" / "error" | Execution outcome |
| created_at | Timestamp | Required, auto-generated on create | When the tool was invoked |

### Validation Rules

1. **Task title**: Must be non-empty and 255 characters or fewer. Whitespace-only titles are rejected.
2. **Task description**: When provided, must be 2000 characters or fewer.
3. **Message content**: Must be non-empty.
4. **Message role**: Must be exactly "user" or "assistant". No other values accepted.
5. **ToolCall status**: Must be exactly "success" or "error".
6. **Foreign keys**: Conversation must exist before Messages can reference it. Message must exist before ToolCalls can reference it.
7. **Owner isolation**: Queries for Tasks and Conversations must always filter by owner_id. No cross-user data access is permitted.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All four entities (Task, Conversation, Message, ToolCall) can be created, read, and (where applicable) updated and deleted within the system.
- **SC-002**: User isolation is enforced — a user's query for tasks or conversations never returns another user's data, verified by cross-user test scenarios.
- **SC-003**: Referential integrity is enforced — messages cannot reference non-existent conversations, tool calls cannot reference non-existent messages.
- **SC-004**: All validation constraints are enforced — empty titles, oversized descriptions, invalid roles, and invalid statuses are rejected with clear error feedback.
- **SC-005**: Timestamps are automatically generated and accurate — created_at is set on insert, updated_at refreshes on modification.
- **SC-006**: Lookup by owner (Tasks, Conversations) and by parent (Messages by conversation, ToolCalls by message) performs efficiently via indexed fields.

## Assumptions

- User identity is a string identifier provided by an external authentication system. The data models do not store user profile information — only the user ID reference.
- The system uses a relational database with support for unique identifiers, foreign keys, and indexing.
- "Unique Identifier" in field definitions refers to a universally unique value (e.g., UUID) rather than a sequential integer, to support distributed systems and prevent enumeration attacks.
- Cascade deletion policy (whether deleting a Conversation also deletes its Messages and ToolCalls) is an implementation decision, not specified here.
- Message ordering within a conversation is determined by the created_at timestamp, which is sufficient given single-user-per-conversation semantics.
