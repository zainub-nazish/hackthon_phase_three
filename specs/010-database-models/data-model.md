# Data Model: Database Models for Todo AI System

**Feature**: 010-database-models | **Date**: 2026-02-11

## Entities

### Task

**Table**: `tasks`
**Purpose**: Store personal todo items owned by authenticated users.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PK, default uuid4 | Unique task identifier |
| owner_id | String | NOT NULL, indexed | User ID from JWT sub claim |
| title | String | NOT NULL, max 255 | Task title |
| description | String | Nullable, max 2000 | Optional task description |
| completed | Boolean | NOT NULL, default false | Completion status |
| created_at | Datetime | NOT NULL, auto-generated | Creation timestamp |
| updated_at | Datetime | NOT NULL, auto-generated | Last update timestamp |

**Indexes**: `owner_id` (B-tree)

### Conversation

**Table**: `conversations`
**Purpose**: Group chat messages into sessions, one per user interaction.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PK, default uuid4 | Unique conversation identifier |
| owner_id | String | NOT NULL, indexed | User ID from JWT sub claim |
| created_at | Datetime | NOT NULL, auto-generated | Conversation start time |
| updated_at | Datetime | NOT NULL, auto-generated | Last activity timestamp |

**Indexes**: `owner_id` (B-tree)

### Message

**Table**: `messages`
**Purpose**: Store individual chat utterances within a conversation.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PK, default uuid4 | Unique message identifier |
| conversation_id | UUID | NOT NULL, FK -> conversations.id, indexed | Parent conversation |
| role | String | NOT NULL, max 20 | Sender role: "user" or "assistant" |
| content | String | NOT NULL | Message text content |
| created_at | Datetime | NOT NULL, auto-generated | Message timestamp |

**Indexes**: `conversation_id` (B-tree)
**Immutable**: Messages are append-only. No update or delete path exposed.

### ToolCall

**Table**: `tool_calls`
**Purpose**: Audit trail for AI agent tool invocations.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PK, default uuid4 | Unique tool call identifier |
| message_id | UUID | NOT NULL, FK -> messages.id, indexed | Parent assistant message |
| tool_name | String | NOT NULL, max 100 | Name of invoked tool (e.g., "add_task") |
| parameters | Text | NOT NULL | JSON-encoded input parameters |
| result | Text | NOT NULL | JSON-encoded output result |
| status | String | NOT NULL, max 20 | "success" or "error" |
| created_at | Datetime | NOT NULL, auto-generated | Execution timestamp |

**Indexes**: `message_id` (B-tree)
**Immutable**: ToolCall records are append-only. No update or delete path exposed.

## Relationships

```
User (external, from JWT sub claim)
  │
  ├── 1:N ──→ Task
  │            (owner_id = user_id)
  │
  └── 1:N ──→ Conversation
               (owner_id = user_id)
               │
               └── 1:N ──→ Message
                            (conversation_id = conversation.id)
                            │
                            └── 1:N ──→ ToolCall
                                         (message_id = message.id)
```

| Parent | Child | FK Column | Cardinality |
|--------|-------|-----------|-------------|
| User (external) | Task | Task.owner_id | One-to-Many |
| User (external) | Conversation | Conversation.owner_id | One-to-Many |
| Conversation | Message | Message.conversation_id | One-to-Many |
| Message | ToolCall | ToolCall.message_id | One-to-Many |

## Validation Rules

| # | Rule | Entity | Enforcement Layer |
|---|------|--------|--------------------|
| V1 | Title non-empty, max 255 chars, no whitespace-only | Task | Pydantic schema + MCP tool handler |
| V2 | Description max 2000 chars (when provided) | Task | Pydantic schema + MCP tool handler |
| V3 | Completed defaults to false | Task | SQLModel Field default |
| V4 | Role must be "user" or "assistant" | Message | Application layer (chat route) |
| V5 | Content must be non-empty | Message | Pydantic schema (min_length=1) |
| V6 | Status must be "success" or "error" | ToolCall | Application layer (chat route) |
| V7 | Conversation must exist for message | Message | Database FK constraint |
| V8 | Message must exist for tool call | ToolCall | Database FK constraint |
| V9 | Owner_id must be non-null | Task, Conversation | SQLModel nullable=False |

## State Transitions

### Task Lifecycle
```
Created (completed=false)
  │
  ├── Update title/description → Updated (completed=false, updated_at refreshed)
  │
  ├── Complete → Completed (completed=true, updated_at refreshed)
  │
  └── Delete → Removed (hard delete, record gone)
```

### Message Lifecycle
```
Created → Immutable (no state changes after creation)
```

### ToolCall Lifecycle
```
Created → Immutable (no state changes after creation)
```

### Conversation Lifecycle
```
Created (on first message)
  │
  └── Touch (on each new message) → updated_at refreshed
```

## Query Patterns

| Operation | Query Pattern | Index Used |
|-----------|--------------|------------|
| List user's tasks | `WHERE owner_id = :uid ORDER BY created_at DESC` | owner_id |
| Filter tasks by status | `WHERE owner_id = :uid AND completed = :flag` | owner_id |
| Get recent conversation | `WHERE owner_id = :uid ORDER BY updated_at DESC LIMIT 1` | owner_id |
| List conversation messages | `WHERE conversation_id = :cid ORDER BY created_at ASC` | conversation_id |
| List message tool calls | `WHERE message_id = :mid ORDER BY created_at ASC` | message_id |
| Get single task | `WHERE id = :tid AND owner_id = :uid` | PK + owner_id |

## Notes

- These models already exist in `backend/models/database.py` (155 LOC). This document is a retroactive specification.
- No new tables, columns, or migrations are needed.
- The Pydantic request/response schemas in `backend/models/schemas.py` mirror these models for the API layer.
