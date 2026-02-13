# Quickstart: Database Models for Todo AI System

**Feature**: 010-database-models | **Branch**: `010-database-models`

## Prerequisites

- Python 3.11+
- Existing backend running (FastAPI)
- Database configured (Neon PostgreSQL for production, SQLite for testing)

## Existing Files

These models already exist in the codebase:

| File | Purpose |
|------|---------|
| `backend/models/database.py` | SQLModel ORM definitions for Task, Conversation, Message, ToolCall |
| `backend/models/schemas.py` | Pydantic request/response schemas for API layer |
| `backend/database.py` | Async engine and session factory |

## Model Overview

| Entity | Table | PK | Owner | FK |
|--------|-------|----|-------|----|
| Task | tasks | UUID | owner_id (indexed) | None |
| Conversation | conversations | UUID | owner_id (indexed) | None |
| Message | messages | UUID | N/A (via conversation) | conversation_id -> conversations.id |
| ToolCall | tool_calls | UUID | N/A (via message) | message_id -> messages.id |

## Running Tests

```bash
# Run all backend tests (includes model CRUD tests)
pytest backend/tests/ -v

# Run specific test files
pytest backend/tests/test_mcp_tools.py -v      # MCP tool CRUD tests
pytest backend/tests/test_ai_agent.py -v        # Agent tool executor tests
pytest backend/tests/test_chat.py -v            # Chat endpoint tests
pytest backend/tests/test_chat_isolation.py -v  # Cross-user isolation tests
```

## Verification Checklist

- [ ] All 4 models (Task, Conversation, Message, ToolCall) are defined in `backend/models/database.py`
- [ ] All models use UUID primary keys with auto-generation
- [ ] Task and Conversation have `owner_id` field with index
- [ ] Message has `conversation_id` foreign key with index
- [ ] ToolCall has `message_id` foreign key with index
- [ ] Task has title (max 255), description (max 2000, nullable), completed (default false)
- [ ] Message has role (max 20) and content (non-null)
- [ ] ToolCall has tool_name, parameters, result, status fields
- [ ] All models have created_at with auto-generation
- [ ] Task and Conversation have updated_at with auto-generation
- [ ] Pydantic schemas in schemas.py match the database models
- [ ] User isolation enforced in all query paths

## Architecture

```
Authentication (Better Auth)
    │
    ▼ user_id (JWT sub claim)
    │
┌───┴────────────────────────────────────┐
│          API Layer (FastAPI)            │
│  routes/tasks.py  routes/chat.py       │
└───┬────────────────────────────────────┘
    │
    ▼ Pydantic schemas (models/schemas.py)
    │
┌───┴────────────────────────────────────┐
│       ORM Layer (SQLModel)             │
│  models/database.py                    │
│  Task | Conversation | Message | ToolCall │
└───┬────────────────────────────────────┘
    │
    ▼ Async SQLAlchemy engine
    │
┌───┴────────────────────────────────────┐
│         Database                       │
│  Neon PostgreSQL (prod)                │
│  SQLite + aiosqlite (test)             │
└────────────────────────────────────────┘
```
