# Implementation Plan: Todo Management MCP Tools

**Branch**: `009-mcp-tools` | **Date**: 2026-02-11 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `specs/009-mcp-tools/spec.md`

## Summary

Refactor the AI agent's inline tool definitions and executors into a standardized MCP (Model Context Protocol) tool server using the official `mcp` Python SDK. The MCP server registers five tools (add_task, list_tasks, complete_task, delete_task, update_task) with proper JSON Schema definitions. A lightweight bridge converts MCP schemas to Anthropic API format and dispatches tool calls to MCP handlers, preserving the existing `AIAgentService` interface and all database operations.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: FastAPI, `mcp` SDK (v1.26.0), `anthropic` SDK (>=0.79.0), SQLModel
**Storage**: Neon PostgreSQL (production), SQLite (testing) — no schema changes
**Testing**: pytest + pytest-asyncio, existing `agent_db` fixture
**Target Platform**: Linux server (Render/Railway) + local Windows dev
**Project Type**: Web application (FastAPI backend)
**Performance Goals**: MCP tool execution adds <2s overhead vs inline (per spec SC-007)
**Constraints**: Must preserve `AIAgentService.generate_response()` interface (FR-013), user isolation (FR-002)
**Scale/Scope**: 5 MCP tools, 3 new files, ~400 LOC new/modified

## Constitution Check

*GATE: Constitution template is not filled in — no gates to check. Proceeding.*

## Project Structure

### Documentation (this feature)

```text
specs/009-mcp-tools/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (from /sp.tasks)
```

### Source Code (repository root)

```text
backend/
├── services/
│   ├── ai_agent.py          # MODIFY — remove inline tools, use MCP bridge
│   ├── mcp_tools.py          # NEW — MCP tool server with 5 tool handlers
│   └── mcp_bridge.py         # NEW — schema converter + dispatch bridge
├── tests/
│   ├── conftest.py            # MODIFY — add MCP test fixtures
│   ├── test_ai_agent.py       # MODIFY — update imports for MCP dispatch
│   └── test_mcp_tools.py      # NEW — MCP tool handler + bridge tests
└── requirements.txt           # MODIFY — add mcp dependency
```

**Structure Decision**: Web application layout preserved. Three new files added under `backend/services/` and `backend/tests/`. No frontend changes — this is a backend-only refactor.

## Architecture Overview

### Current State (008-ai-agent)

```
User message → Chat API → AIAgentService.generate_response()
  → Claude API (tools=TOOLS inline list)
  → Claude returns tool_use → TOOL_EXECUTORS[name](params, user_id)
  → Tool executor calls DB directly → result
  → Claude API (tool_result) → final text response
```

### Target State (009-mcp-tools)

```
User message → Chat API → AIAgentService.generate_response()
  → MCP Bridge: get_tool_schemas() → Anthropic-format tool list
  → Claude API (tools=mcp_schemas)
  → Claude returns tool_use → MCP Bridge: execute_tool(name, params, user_id)
  → MCP Tool Server: registered handler → DB operations → result
  → Claude API (tool_result) → final text response
```

### Component Responsibilities

**1. MCP Tool Server** (`backend/services/mcp_tools.py`)
- Defines 5 tools using `mcp` SDK's `FastMCP` server with `@server.tool()` decorators
- Each tool handler contains validation, DB operations, and result formatting
- Tool handlers accept `user_id` as a parameter (injected by bridge, not exposed to LLM)
- Reuses existing DB session pattern (`_get_db_session()`)
- Single source of truth for all tool definitions and business logic

**2. MCP Bridge** (`backend/services/mcp_bridge.py`)
- `get_tool_schemas() → list[dict]`: Extracts tool definitions from MCP server, converts to Anthropic API format (`name`, `description`, `input_schema`)
- `execute_tool(name, params, user_id) → dict`: Dispatches a tool call to the correct MCP handler, injects `user_id`, returns the result
- Strips `user_id` from the schema exposed to Claude (security: LLM must not control which user's tasks it accesses)

**3. AI Agent Service** (`backend/services/ai_agent.py`)
- Removes: `TOOLS` list, `TOOL_EXECUTORS` dict, all `_execute_*` functions
- Keeps: `SYSTEM_PROMPT`, `AIAgentService` class, `AgentResponse`, `ToolCallData`
- Modified: `generate_response()` calls `mcp_bridge.get_tool_schemas()` for tool definitions and `mcp_bridge.execute_tool()` for tool execution
- Interface unchanged: `async generate_response(messages, user_id) → AgentResponse`

## Design Decisions

### D-001: Hybrid In-Process MCP (from R-002)
Use MCP SDK to define tools but invoke handlers directly without MCP transport. This gives standardized tool definitions with zero protocol overhead. See `research.md` R-002.

### D-002: Server-Side user_id Injection (from R-003)
The `user_id` parameter is NOT part of the MCP tool schema exposed to the LLM. The bridge injects it from the authenticated request context before calling each tool handler. This prevents the LLM from specifying a different user's ID.

### D-003: Schema Conversion at Startup (from R-004)
Tool schemas are converted from MCP format to Anthropic format once at module load time and cached. This avoids per-request schema generation overhead.

### D-004: Preserved System Prompt
The `SYSTEM_PROMPT` constant stays in `ai_agent.py`. It does not change — tool names and descriptions remain the same from the LLM's perspective.

### D-005: No Database Schema Changes
No new tables, columns, or migrations. The existing `Task`, `Conversation`, `Message`, and `ToolCall` models are unchanged. MCP tools operate on the same `Task` model through the same async session pattern.

## Tool Workflows

### add_task
1. Receive `title` (required), `description` (optional) from Claude + `user_id` from bridge
2. Validate: title non-empty, ≤255 chars; description ≤2000 chars
3. Create `Task` record with `owner_id=user_id`
4. Commit and return `{id, title, description, completed}`

### list_tasks
1. Receive `status` (optional, default "all") from Claude + `user_id` from bridge
2. Query `Task` where `owner_id=user_id`, apply status filter
3. Order by `created_at` desc
4. Return `{tasks: [{id, title, description, completed}, ...], count}`

### complete_task
1. Receive `task_id` (required) from Claude + `user_id` from bridge
2. Validate UUID format
3. Query `Task` where `id=task_id AND owner_id=user_id`
4. If not found → return error
5. Set `completed=True`, update `updated_at`
6. Return `{id, title, completed}`

### delete_task
1. Receive `task_id` (required) from Claude + `user_id` from bridge
2. Validate UUID format
3. Query `Task` where `id=task_id AND owner_id=user_id`
4. If not found → return error
5. Delete record, commit
6. Return `{deleted: true, id, title}`

### update_task
1. Receive `task_id` (required), `title` (optional), `description` (optional) from Claude + `user_id` from bridge
2. Validate: at least one field provided; title non-empty if present
3. Query `Task` where `id=task_id AND owner_id=user_id`
4. If not found → return error
5. Update provided fields, update `updated_at`
6. Return `{id, title, description, completed}`

## Error Handling

| Error Case | Handler | Response |
|-----------|---------|----------|
| Empty/missing title | `add_task` | `{is_error: true, error: "Task title is required"}` |
| Title >255 chars | `add_task` | `{is_error: true, error: "Task title must be 255 characters or less"}` |
| Invalid UUID format | `complete/delete/update` | `{is_error: true, error: "Invalid task_id format"}` |
| Task not found | `complete/delete/update` | `{is_error: true, error: "Task not found"}` |
| No fields to update | `update_task` | `{is_error: true, error: "At least one of title or description must be provided"}` |
| Unknown tool name | Bridge dispatcher | `{is_error: true, error: "Unknown tool: {name}"}` |
| DB exception | Any tool | Caught by bridge, returned as `{is_error: true, error: str(e)}` |

## Implementation Phases

### Phase A: MCP Tool Server (mcp_tools.py)
1. Add `mcp` to `requirements.txt`
2. Create `backend/services/mcp_tools.py` with `FastMCP` server
3. Register 5 tool handlers with `@server.tool()` decorators
4. Each handler mirrors existing `_execute_*` logic from `ai_agent.py`
5. Include `_get_db_session()` helper (moved from ai_agent.py)

### Phase B: MCP Bridge (mcp_bridge.py)
1. Create `backend/services/mcp_bridge.py`
2. Implement `get_tool_schemas()` — reads MCP server tool definitions, converts to Anthropic format, strips `user_id` from schemas
3. Implement `execute_tool(name, params, user_id)` — dispatches to MCP handler, injects `user_id`
4. Cache converted schemas at module level

### Phase C: Refactor AI Agent (ai_agent.py)
1. Remove `TOOLS` list, `TOOL_EXECUTORS` dict, and all `_execute_*` functions
2. Remove `_get_db_session()` (moved to mcp_tools.py)
3. Import `mcp_bridge.get_tool_schemas` and `mcp_bridge.execute_tool`
4. Update `generate_response()` to use bridge instead of inline dispatch
5. Preserve `SYSTEM_PROMPT`, `AgentResponse`, `ToolCallData`, `AIAgentService` interface

### Phase D: Testing
1. Create `backend/tests/test_mcp_tools.py`:
   - Unit tests for each MCP tool handler (mirrors TestAddTask, TestListTasks, etc.)
   - Schema conversion tests (verify Anthropic format output)
   - Bridge dispatch tests (route tool calls correctly)
   - Error handling tests (unknown tool, DB errors)
2. Update `backend/tests/conftest.py`:
   - Patch `mcp_tools._get_db_session` instead of `ai_agent._get_db_session`
3. Update `backend/tests/test_ai_agent.py`:
   - Update imports and mock targets for MCP bridge
   - Agent loop tests should still pass with the new dispatch path

## Risks and Mitigations

1. **MCP SDK version instability**: The `mcp` SDK is relatively new. Pin to `>=1.26.0,<2.0.0` to avoid breaking changes.
2. **Import overhead**: The `mcp` SDK may have heavy imports. Mitigate by lazy-importing only when the tool server is initialized.
3. **Test fixture patching**: Moving `_get_db_session` to a new module changes the mock target. Tests must be updated carefully to patch the correct module path.

## Complexity Tracking

No constitution violations to justify — the plan follows a minimal-change approach:
- 3 new files (mcp_tools.py, mcp_bridge.py, test_mcp_tools.py)
- 3 modified files (ai_agent.py, conftest.py, requirements.txt)
- 0 database changes
- 0 API contract changes
- 0 frontend changes
