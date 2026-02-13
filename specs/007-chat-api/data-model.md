# Data Model: Chat API & Conversation Persistence

**Feature**: 007-chat-api | **Date**: 2026-02-09

## Entity Relationship Diagram

```
User (Better Auth)
  │
  ├── 1:N ──→ Conversation
  │              │
  │              └── 1:N ──→ Message
  │                            │
  │                            └── 1:N ──→ ToolCall (assistant messages only)
  │
  └── 1:N ──→ Task (existing)
```

---

## Entities

### Conversation

Represents a chat session between a user and the AI assistant.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | UUID | PK, default `uuid4()` | Unique conversation identifier |
| `owner_id` | str | NOT NULL, INDEX | User ID from auth (FK to Better Auth `user.id`) |
| `created_at` | datetime | NOT NULL, default `utcnow()` | Conversation creation time |
| `updated_at` | datetime | NOT NULL, default `utcnow()` | Last activity time (updated on each new message) |

**Table name**: `conversations`
**Indexes**: `owner_id` (for user isolation queries)

### Message

Represents a single message within a conversation (user input or assistant response).

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | UUID | PK, default `uuid4()` | Unique message identifier |
| `conversation_id` | UUID | NOT NULL, FK → `conversations.id`, INDEX | Parent conversation |
| `role` | str | NOT NULL, max 20 chars | Sender: `"user"` or `"assistant"` |
| `content` | str | NOT NULL | Message text content |
| `created_at` | datetime | NOT NULL, default `utcnow()` | Message timestamp |

**Table name**: `messages`
**Indexes**: `conversation_id` (for loading conversation history)

### ToolCall

Records AI agent tool invocations linked to assistant messages.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | UUID | PK, default `uuid4()` | Unique tool call identifier |
| `message_id` | UUID | NOT NULL, FK → `messages.id`, INDEX | Parent assistant message |
| `tool_name` | str | NOT NULL, max 100 chars | Name of the invoked tool |
| `parameters` | str | NOT NULL | JSON-encoded input parameters |
| `result` | str | NOT NULL | JSON-encoded output result |
| `status` | str | NOT NULL, max 20 chars | `"success"` or `"error"` |
| `created_at` | datetime | NOT NULL, default `utcnow()` | Execution timestamp |

**Table name**: `tool_calls`
**Indexes**: `message_id` (for loading tool calls per message)

---

## Validation Rules

### Message Content
- Must be non-empty and non-whitespace
- Maximum 2000 characters
- Validated at the Pydantic schema level (request body)

### Role Field
- Must be exactly `"user"` or `"assistant"`
- Enforced by the application layer (not user-settable in API)

### Conversation Ownership
- All queries MUST filter by `owner_id` to enforce user isolation
- Cross-user conversation access returns 404 (not 403)

---

## State Transitions

### Conversation Lifecycle
```
[New Message with conversation_id=null]
  → CREATE Conversation (owner_id, timestamps)
  → CREATE Message (role="user", content=input)
  → INVOKE AI Agent
  → CREATE Message (role="assistant", content=response)
  → UPDATE Conversation.updated_at

[New Message with existing conversation_id]
  → VERIFY Conversation exists AND owner_id matches
  → CREATE Message (role="user", content=input)
  → INVOKE AI Agent
  → CREATE Message (role="assistant", content=response)
  → UPDATE Conversation.updated_at
```

### Error State Handling
```
[AI Agent Failure]
  → User message is ALREADY persisted
  → No assistant message created
  → Conversation.updated_at still updated (user message was added)
  → API returns 502/504 error
  → Conversation state remains valid — next message continues normally
```

---

## Relationship to Existing Models

The new models exist alongside the existing `Task` model. They share:
- Same database engine and async session
- Same UUID primary key pattern
- Same `owner_id` user isolation pattern
- Same timestamp pattern (`datetime.utcnow()`)
- Same SQLModel ORM pattern

The `ToolCall` entity will reference Task operations (create, update, delete, complete) when the AI agent invokes tools. The tool call's `parameters` field will contain the Task data, and `result` will contain the operation outcome. This linkage is semantic (JSON data), not a foreign key constraint.
