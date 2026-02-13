# Data Model: AI Todo Agent

**Feature**: 008-ai-agent | **Date**: 2026-02-10

## Entity Overview

This feature does **not** add new database tables. It modifies the `AIAgentService` to use a real LLM with tool execution. The agent operates on existing entities from 007-chat-api and the Task CRUD feature.

## Existing Entities Used

### Task (from 002-backend-api-data-layer)

The agent's tools operate on the existing Task model:

| Field | Type | Notes |
|-------|------|-------|
| `id` | UUID | PK — used as `task_id` in agent tools |
| `owner_id` | str | Enforces user isolation in all tool operations |
| `title` | str (max 255) | Created/updated by `add_task`/`update_task` tools |
| `description` | str (max 2000, nullable) | Optional in `add_task`/`update_task` |
| `completed` | bool | Set to `True` by `complete_task` tool |
| `created_at` | datetime | Auto-set |
| `updated_at` | datetime | Updated on PATCH operations |

### Conversation, Message, ToolCall (from 007-chat-api)

The agent produces data persisted by the chat API:

- **Message**: Agent's text response stored as `role="assistant"` messages.
- **ToolCall**: Each tool invocation stored with `tool_name`, `parameters` (JSON), `result` (JSON), `status`.

---

## Tool Definitions (New — Not DB Entities)

Tools are defined as JSON Schema objects for the Anthropic API. They do NOT create database tables — they are runtime configuration.

### add_task

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `title` | string | Yes | Task title (1-255 chars) |
| `description` | string | No | Task description (max 2000 chars) |

**Operation**: INSERT into `tasks` table with `owner_id = user_id`.
**Returns**: Created task with id, title, description, completed status.

### list_tasks

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `status` | string (enum) | No | Filter: "all" (default), "pending", "completed" |

**Operation**: SELECT from `tasks` WHERE `owner_id = user_id`, optionally filtered by `completed` status.
**Returns**: List of tasks with id, title, completed status.

### complete_task

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `task_id` | string (UUID) | Yes | ID of the task to complete |

**Operation**: UPDATE `tasks` SET `completed = True` WHERE `id = task_id AND owner_id = user_id`.
**Returns**: Updated task or error if not found.

### delete_task

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `task_id` | string (UUID) | Yes | ID of the task to delete |

**Operation**: DELETE from `tasks` WHERE `id = task_id AND owner_id = user_id`.
**Returns**: Confirmation or error if not found.

### update_task

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `task_id` | string (UUID) | Yes | ID of the task to update |
| `title` | string | No | New title (1-255 chars) |
| `description` | string | No | New description (max 2000 chars) |

**Operation**: UPDATE `tasks` SET provided fields WHERE `id = task_id AND owner_id = user_id`.
**Returns**: Updated task or error if not found.

---

## Data Flow

```
User Message
  → Chat API (POST /chat) — persists user message
  → AIAgentService.generate_response(messages, user_id)
    → Anthropic API (with tools + system prompt + conversation history)
    → Claude returns tool_use blocks
    → Agent executes tools (direct DB queries using user_id)
    → Agent sends tool_result back to Claude
    → Claude returns final text response
  → AgentResponse(content, tool_calls) returned
  → Chat API persists assistant message + tool call records
  → ChatResponse returned to frontend
```

---

## Configuration Additions

| Setting | Env Var | Type | Default | Description |
|---------|---------|------|---------|-------------|
| `anthropic_api_key` | `ANTHROPIC_API_KEY` | str (optional) | None | API key for Anthropic Claude |
| `anthropic_model` | `ANTHROPIC_MODEL` | str | `claude-haiku-4-5-20251001` | Claude model ID for agent |
