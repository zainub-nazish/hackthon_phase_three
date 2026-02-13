# Implementation Plan: Database Models for Todo AI System

**Branch**: `010-database-models` | **Date**: 2026-02-11 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `specs/010-database-models/spec.md`

## Summary

Define and validate the database models (Task, Conversation, Message, ToolCall) for the Todo AI system. These models are the data foundation for task management, chat persistence, and AI tool auditing. The implementation uses SQLModel ORM with UUID primary keys, async sessions, and dual-database support (Neon PostgreSQL for production, SQLite for testing). This is a retroactive specification — the models already exist in `backend/models/database.py` and `backend/models/schemas.py`. The plan focuses on validating conformance, documenting contracts, and identifying any gaps.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: FastAPI, SQLModel (SQLAlchemy + Pydantic), aiosqlite (testing)
**Storage**: Neon PostgreSQL (production), SQLite+aiosqlite (testing) — no schema changes needed
**Testing**: pytest + pytest-asyncio, existing fixtures in `backend/tests/conftest.py`
**Target Platform**: Linux server (Render/Railway) + local Windows dev
**Project Type**: Web application (FastAPI backend)
**Performance Goals**: Standard CRUD latency (<100ms for single-entity operations)
**Constraints**: Must maintain compatibility with existing API routes, MCP tools, and AI agent service
**Scale/Scope**: 4 entities, 0 new files, ~155 LOC existing in database.py + ~150 LOC in schemas.py

## Constitution Check

*GATE: Constitution template is not filled in — no gates to check. Proceeding.*

## Project Structure

### Documentation (this feature)

```text
specs/010-database-models/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── database-models.yaml
├── checklists/
│   └── requirements.md
└── tasks.md             # Phase 2 output (from /sp.tasks)
```

### Source Code (repository root)

```text
backend/
├── models/
│   ├── database.py          # EXISTING — Task, Conversation, Message, ToolCall (SQLModel)
│   └── schemas.py           # EXISTING — Pydantic request/response models
├── database.py              # EXISTING — Async engine + session factory
├── routes/
│   ├── tasks.py             # EXISTING — Task CRUD API endpoints
│   └── chat.py              # EXISTING — Chat API endpoints
├── services/
│   ├── ai_agent.py          # EXISTING — AI agent service (uses MCP bridge)
│   ├── mcp_tools.py         # EXISTING — MCP tool handlers (CRUD on Task)
│   └── mcp_bridge.py        # EXISTING — Schema converter + dispatch
└── tests/
    ├── conftest.py           # EXISTING — Test fixtures (agent_db, mcp_db)
    ├── test_ai_agent.py      # EXISTING — Agent + tool executor tests
    ├── test_mcp_tools.py     # EXISTING — MCP tool handler tests
    ├── test_chat.py          # EXISTING — Chat endpoint tests
    └── test_chat_isolation.py # EXISTING — Cross-user isolation tests
```

**Structure Decision**: Web application layout. All files already exist. This feature is a retroactive specification and validation exercise — no new source files are created.

## Architecture Overview

### Data Flow

```
User Request → FastAPI Route → Pydantic Schema Validation
  → SQLModel ORM → Async SQLAlchemy Session → Database
  → Response Pydantic Schema → JSON Response
```

### Entity Relationships

```
User (external, from JWT)
  ├── owns → Task (0..N)
  └── owns → Conversation (0..N)
                └── contains → Message (0..N)
                                  └── has → ToolCall (0..N)
```

### Key Design Decisions

#### D-001: SQLModel ORM (from R-001)
Use SQLModel as the single ORM layer, combining Pydantic validation with SQLAlchemy query capabilities. This eliminates the model duplication problem (separate DB model + API schema) for read operations.

#### D-002: UUID Primary Keys (from R-002)
All entities use UUID v4 primary keys via `uuid4()` default factory. This prevents ID enumeration attacks, supports future distributed operations, and avoids sequential ID leakage.

#### D-003: Owner-Based Isolation (from R-004)
Task and Conversation have an `owner_id` string field (indexed) that maps to the JWT `sub` claim. Every query path filters by `owner_id`. Messages and ToolCalls are implicitly user-scoped through their parent Conversation.

#### D-004: Dual Database Strategy (from R-007)
Production uses Neon PostgreSQL via `asyncpg`. Tests use in-memory or file-based SQLite via `aiosqlite`. Both use the same async SQLAlchemy engine interface, ensuring test fidelity.

#### D-005: JSON-as-String Serialization (from R-006)
ToolCall `parameters` and `result` fields store JSON as plain strings (not JSONB), ensuring SQLite compatibility in tests. JSON parsing happens at the application layer.

## Model Definitions

### Task
- **Table**: `tasks`
- **Purpose**: Store personal todo items
- **Fields**: id (UUID PK), owner_id (str, indexed), title (str, max 255), description (str, nullable, max 2000), completed (bool, default false), created_at (datetime), updated_at (datetime)
- **Indexes**: owner_id
- **Operations**: Create, Read, List (with status filter), Update (partial), Delete, Complete (set completed=true)

### Conversation
- **Table**: `conversations`
- **Purpose**: Group chat messages into sessions
- **Fields**: id (UUID PK), owner_id (str, indexed), created_at (datetime), updated_at (datetime)
- **Indexes**: owner_id
- **Operations**: Create, Get Recent, Touch (update updated_at)

### Message
- **Table**: `messages`
- **Purpose**: Store individual chat utterances
- **Fields**: id (UUID PK), conversation_id (UUID FK, indexed), role (str, max 20), content (str), created_at (datetime)
- **Indexes**: conversation_id
- **Operations**: Create, List by Conversation (chronological)
- **Immutable**: No update or delete operations exposed

### ToolCall
- **Table**: `tool_calls`
- **Purpose**: Audit trail for AI tool invocations
- **Fields**: id (UUID PK), message_id (UUID FK, indexed), tool_name (str, max 100), parameters (str), result (str), status (str, max 20), created_at (datetime)
- **Indexes**: message_id
- **Operations**: Create, List by Message
- **Immutable**: No update or delete operations exposed

## Validation Rules

| Rule | Entity | Enforcement |
|------|--------|-------------|
| Non-empty title, max 255 chars | Task | Pydantic schema (TaskCreate/TaskBase) + MCP tool handler |
| Optional description, max 2000 chars | Task | Pydantic schema + MCP tool handler |
| Default completed=false | Task | SQLModel Field default |
| Role in {"user", "assistant"} | Message | Application-level check in chat route |
| Non-empty content | Message | Pydantic schema (ChatRequest min_length=1) |
| Status in {"success", "error"} | ToolCall | Application-level check in chat route |
| FK conversation_id exists | Message | Database-level foreign key constraint |
| FK message_id exists | ToolCall | Database-level foreign key constraint |
| owner_id required | Task, Conversation | SQLModel nullable=False + application injection |

## Existing Test Coverage

The following test files already validate the database models:

| Test File | Coverage |
|-----------|----------|
| `test_mcp_tools.py` (26 tests) | Task CRUD via MCP tools, validation errors, user isolation |
| `test_ai_agent.py` (25 tests) | Task CRUD via agent executors, agent loop with tool dispatch |
| `test_chat.py` (18 tests) | Conversation + Message CRUD, ToolCall persistence, edge cases |
| `test_chat_isolation.py` (4 tests) | Cross-user conversation/message isolation |

**Total**: 73 passing tests covering all 4 entities.

## Implementation Phases

### Phase A: Validation (No Code Changes)
1. Compare existing `database.py` models against the spec field definitions
2. Verify all FK constraints, indexes, and defaults match
3. Verify Pydantic schemas in `schemas.py` align with database models
4. Run existing test suite to confirm all 73 tests pass

### Phase B: Gap Analysis
1. Identify any spec requirements not covered by existing implementation
2. Known gap: `datetime.utcnow()` deprecation — should migrate to `datetime.now(UTC)`
3. Known gap: Message `role` enum validation is application-level, not database-level
4. Known gap: ToolCall `status` enum validation is application-level, not database-level

### Phase C: Documentation
1. Complete data-model.md with entity definitions
2. Complete contracts/database-models.yaml with CRUD operations
3. Complete quickstart.md with verification checklist

## Risks and Mitigations

1. **datetime.utcnow() deprecation**: Python 3.12+ emits DeprecationWarning. Mitigation: Migrate to `datetime.now(datetime.UTC)` in a future maintenance task. Low priority — functionally correct.
2. **Enum validation at application layer**: Role and status enums are validated in route/service code, not at the database level. Mitigation: Acceptable for current scale; database-level CHECK constraints can be added via migration if needed.
3. **No cascade delete policy defined**: Deleting a Conversation doesn't automatically delete Messages/ToolCalls. Mitigation: Current system doesn't expose conversation deletion — this is a future concern.

## Complexity Tracking

No constitution violations to justify — all models follow minimal, straightforward patterns:
- 4 entities in 1 file (155 LOC)
- No inheritance hierarchies or abstract base models
- No triggers or stored procedures
- No materialized views or complex indexes
- Standard CRUD operations only
