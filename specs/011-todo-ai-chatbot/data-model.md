# Data Model: Todo AI Chatbot (011)

**Date**: 2026-02-14
**Branch**: `011-todo-ai-chatbot`

## Entities

### Task

| Field       | Type     | Constraints                          |
|-------------|----------|--------------------------------------|
| id          | int      | Primary key, auto-increment          |
| user_id     | string   | Required, indexed, FK to auth users  |
| title       | string   | Required, max 200 chars              |
| description | text     | Optional, max 2000 chars             |
| completed   | boolean  | Default: false                       |
| created_at  | datetime | Auto-set on create, UTC              |
| updated_at  | datetime | Auto-set on create/update, UTC       |

**Relationships**: Belongs to User (via user_id). Standalone — no FK to Conversation.
**Indexes**: `(user_id)`, `(user_id, completed)`

### Conversation

| Field      | Type     | Constraints                          |
|------------|----------|--------------------------------------|
| id         | int      | Primary key, auto-increment          |
| user_id    | string   | Required, indexed, FK to auth users  |
| created_at | datetime | Auto-set on create, UTC              |
| updated_at | datetime | Auto-set on create/update, UTC       |

**Relationships**: Belongs to User. Has many Messages.
**Indexes**: `(user_id)`, `(user_id, updated_at DESC)`

### Message

| Field           | Type     | Constraints                               |
|-----------------|----------|-------------------------------------------|
| id              | int      | Primary key, auto-increment               |
| user_id         | string   | Required, indexed                         |
| conversation_id | int      | Required, FK to Conversation.id           |
| role            | string   | Required, enum: "user" or "assistant"     |
| content         | text     | Required, max 10000 chars                 |
| created_at      | datetime | Auto-set on create, UTC                   |

**Relationships**: Belongs to Conversation. Belongs to User.
**Indexes**: `(conversation_id, created_at ASC)`

## State Transitions

### Task.completed
```
false (pending) → true (completed)   via complete_task
true (completed) → false (pending)   not supported in this phase
```

### Conversation lifecycle
```
[none] → created    on first user message (auto-create)
created → active    on subsequent messages (updated_at refreshed)
```

## Data Isolation

All queries MUST include `user_id` filter. No cross-user data access is permitted.

- Task queries: `WHERE user_id = :current_user_id`
- Conversation queries: `WHERE user_id = :current_user_id`
- Message queries: `WHERE user_id = :current_user_id` (defense in depth, even though conversation_id implies it)
