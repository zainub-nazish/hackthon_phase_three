# Quickstart: Todo Management MCP Tools

**Feature**: 009-mcp-tools | **Branch**: `009-mcp-tools`

## Prerequisites

- Python 3.11+
- Existing backend running (FastAPI + Neon PostgreSQL or SQLite for dev)
- `ANTHROPIC_API_KEY` configured in `.env`

## Setup

```bash
# Install new dependency
cd backend
pip install -r requirements.txt  # adds mcp>=1.26.0

# Verify installation
python -c "import mcp; print(mcp.__version__)"
```

## New Files

| File | Purpose |
|------|---------|
| `backend/services/mcp_tools.py` | MCP tool server — 5 tool handlers |
| `backend/services/mcp_bridge.py` | Schema converter + dispatch bridge |
| `backend/tests/test_mcp_tools.py` | MCP tool and bridge tests |

## Modified Files

| File | Change |
|------|--------|
| `backend/services/ai_agent.py` | Remove inline tools, use MCP bridge |
| `backend/tests/conftest.py` | Update DB session mock target |
| `backend/tests/test_ai_agent.py` | Update imports for MCP dispatch |
| `backend/requirements.txt` | Add `mcp>=1.26.0` |

## Running Tests

```bash
# Run MCP tool tests
pytest backend/tests/test_mcp_tools.py -v

# Run agent tests (verify integration)
pytest backend/tests/test_ai_agent.py -v

# Run all tests
pytest backend/tests/ -v
```

## Verification Checklist

- [ ] `mcp` package installed successfully
- [ ] MCP tool server defines 5 tools (add, list, complete, delete, update)
- [ ] `get_tool_schemas()` returns 5 Anthropic-format tool definitions
- [ ] `execute_tool("add_task", {...}, user_id)` creates a task
- [ ] All existing agent loop tests pass with MCP bridge
- [ ] `AIAgentService.generate_response()` interface unchanged
- [ ] No `TOOLS` or `TOOL_EXECUTORS` remain in `ai_agent.py`

## Architecture Diagram

```
                    ┌─────────────────────────┐
                    │    AIAgentService        │
                    │  generate_response()     │
                    └────────┬────────────────┘
                             │
                    ┌────────▼────────────────┐
                    │      MCP Bridge          │
                    │  get_tool_schemas()      │
                    │  execute_tool()          │
                    └────────┬────────────────┘
                             │
                    ┌────────▼────────────────┐
                    │   MCP Tool Server        │
                    │  @server.tool()          │
                    │  add_task, list_tasks,   │
                    │  complete_task,          │
                    │  delete_task,            │
                    │  update_task             │
                    └────────┬────────────────┘
                             │
                    ┌────────▼────────────────┐
                    │    Database (Task)        │
                    │  SQLModel + asyncpg      │
                    └─────────────────────────┘
```
