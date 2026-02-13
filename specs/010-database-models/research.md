# Research: Database Models for Todo AI System

**Feature**: 010-database-models | **Date**: 2026-02-11

## R-001: ORM Choice — SQLModel

**Decision**: Use SQLModel as the ORM layer for all database models.

**Rationale**: SQLModel combines Pydantic validation with SQLAlchemy's async query capabilities in a single model definition. This eliminates the common pattern of maintaining separate DB models and API schemas. SQLModel models can be used directly as Pydantic response schemas (with `from_attributes=True`), reducing boilerplate. The project already uses FastAPI, which is built by the same author (tiangolo), ensuring tight integration.

**Alternatives considered**:
- **Raw SQLAlchemy**: More flexible but requires separate Pydantic models for every entity, doubling the model count.
- **Tortoise ORM**: Django-style async ORM but less mature ecosystem and no Pydantic integration.
- **Prisma (Python)**: Early-stage Python client, not production-ready for async FastAPI use.

## R-002: Primary Key Strategy — UUID v4

**Decision**: Use UUID v4 (`uuid4()`) as the primary key for all entities.

**Rationale**: UUIDs prevent sequential ID enumeration attacks (e.g., user guessing task IDs by incrementing). They support distributed systems where multiple writers may create records simultaneously. They're generated client-side without database round-trips. The 36-character string representation is acceptable for the scale of this application.

**Alternatives considered**:
- **Sequential integers (SERIAL/BIGSERIAL)**: Simpler, smaller, faster indexes, but expose record count and are enumerable. Poor fit for user-facing task IDs.
- **ULID**: Time-ordered UUIDs; useful for time-series data but adds complexity with no benefit here since we already have `created_at` timestamps.
- **Snowflake IDs**: Require a coordination service; overkill for a single-service application.

## R-003: Timestamp Strategy — datetime.utcnow()

**Decision**: Use `datetime.utcnow()` as the default factory for `created_at` and `updated_at` fields.

**Rationale**: Simple, widely understood, and compatible with both PostgreSQL and SQLite. All timestamps are stored in UTC, avoiding timezone ambiguity.

**Known issue**: `datetime.utcnow()` is deprecated in Python 3.12+ in favor of `datetime.now(datetime.UTC)`. The current implementation emits DeprecationWarnings during tests. This is a non-breaking issue — functionally correct but should be migrated in a future maintenance pass.

**Alternatives considered**:
- **`datetime.now(datetime.UTC)`**: The modern replacement. Should be adopted when addressing the deprecation warning.
- **Database-level `DEFAULT NOW()`**: Offloads to the database, but SQLModel doesn't support this cleanly across both PostgreSQL and SQLite.
- **`func.now()` via SQLAlchemy server_default**: Works for PostgreSQL but not for SQLite in-memory test databases.

## R-004: User Identity Pattern — Opaque owner_id String

**Decision**: Store `owner_id` as an opaque string field on Task and Conversation models, sourced from the JWT `sub` claim.

**Rationale**: The application uses Better Auth for authentication, which provides user identity via JWT tokens. Storing only the user ID (not email, name, or profile data) keeps the models decoupled from the auth system. The string type accommodates any ID format Better Auth may use (UUID, CUID, etc.) without coupling to a specific format.

**Alternatives considered**:
- **Foreign key to a User table**: Would require a local User table synchronized with Better Auth, adding complexity. The auth system is the source of truth for user data.
- **UUID type for owner_id**: Assumes Better Auth uses UUIDs, which may not be true. String is more flexible.
- **Session-based context**: Using async context variables to pass user identity implicitly. Harder to test and reason about.

## R-005: Foreign Key Strategy

**Decision**: Use UUID foreign keys with database-level constraints and application-level indexes.

**Rationale**: `Message.conversation_id` references `Conversation.id` and `ToolCall.message_id` references `Message.id`. These are declared as SQLModel `Field(foreign_key="table.column")` which creates database-level FK constraints. Indexes on FK columns are added via `Field(index=True)` to optimize join/lookup queries.

**Alternatives considered**:
- **No FK constraints (application-level only)**: Faster writes but risks orphaned records. Not acceptable for data integrity.
- **Composite keys**: Using (conversation_id, sequence_number) for messages. Adds complexity with no benefit since UUID is sufficient.

## R-006: Serialization Strategy — JSON as String

**Decision**: Store ToolCall `parameters` and `result` as plain text strings containing JSON-encoded data.

**Rationale**: Different tools have different parameter and result structures, so a fixed schema isn't feasible. JSON-as-string works identically on both PostgreSQL and SQLite, maintaining test environment parity. The application layer handles JSON serialization/deserialization via `json.dumps()` and `json.loads()`.

**Alternatives considered**:
- **PostgreSQL JSONB column**: Native JSON querying and indexing, but incompatible with SQLite test databases. Would require separate test models or dialect-specific column types.
- **Separate parameter columns per tool**: Rigid, requires schema changes for every new tool. Completely impractical.
- **Binary/pickle serialization**: Not human-readable, not portable, security risk from arbitrary deserialization.

## R-007: Dual Database Strategy

**Decision**: Use Neon PostgreSQL (asyncpg) for production and SQLite (aiosqlite) for testing.

**Rationale**: Neon Serverless PostgreSQL provides a managed, scalable production database with connection pooling and branching features. SQLite provides fast, isolated, in-memory test databases with zero setup. Both are accessed through the same async SQLAlchemy engine interface (`create_async_engine`), so application code is database-agnostic.

**Alternatives considered**:
- **PostgreSQL for tests too (via testcontainers)**: More faithful to production but slower test startup, requires Docker, and adds CI complexity.
- **SQLite for production too**: Not suitable for concurrent web server access or production reliability requirements.
- **DuckDB**: Good for analytics but not suited as a transactional database for a web application.
