# Data Model: Todo Management MCP Tools

**Feature**: 009-mcp-tools | **Date**: 2026-02-11

## No Schema Changes

This feature introduces **no new database tables, columns, or migrations**. All MCP tools operate on the existing `Task` model defined in `backend/models/database.py`.

## Existing Entities Used

### Task (unchanged)

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PK, default uuid4 | Unique task identifier |
| owner_id | str | NOT NULL, indexed | User ID from JWT sub claim |
| title | str | NOT NULL, max 255 | Task title |
| description | str | nullable, max 2000 | Optional task description |
| completed | bool | NOT NULL, default False | Completion status |
| created_at | datetime | NOT NULL | Creation timestamp |
| updated_at | datetime | NOT NULL | Last update timestamp |

### ToolCall (unchanged, used for persistence)

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PK, default uuid4 | Unique tool call identifier |
| message_id | UUID | FK messages.id, indexed | Parent assistant message |
| tool_name | str | NOT NULL, max 100 | MCP tool name (e.g., "add_task") |
| parameters | str | NOT NULL | JSON-encoded input parameters |
| result | str | NOT NULL | JSON-encoded output result |
| status | str | NOT NULL, max 20 | "success" or "error" |
| created_at | datetime | NOT NULL | Execution timestamp |

## MCP Tool Input/Output Schemas

These are runtime schemas (not database models), defined by the MCP server:

### add_task
- **Input**: `{title: string (required), description?: string}`
- **Output**: `{id: string, title: string, description: string|null, completed: boolean}`

### list_tasks
- **Input**: `{status?: "all"|"pending"|"completed"}`
- **Output**: `{tasks: [{id, title, description, completed}, ...], count: integer}`

### complete_task
- **Input**: `{task_id: string (required)}`
- **Output**: `{id: string, title: string, completed: true}`

### delete_task
- **Input**: `{task_id: string (required)}`
- **Output**: `{deleted: true, id: string, title: string}`

### update_task
- **Input**: `{task_id: string (required), title?: string, description?: string}`
- **Output**: `{id: string, title: string, description: string|null, completed: boolean}`

### Error Output (all tools)
- `{is_error: true, error: string}`
