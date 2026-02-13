# Research: Todo Management MCP Tools

**Feature**: 009-mcp-tools | **Date**: 2026-02-11

## R-001: MCP Python SDK Selection

**Decision**: Use the official `mcp` Python SDK (v1.26.0) by Anthropic.

**Rationale**: It is the canonical implementation of the Model Context Protocol, maintained by Anthropic (the same provider as the Claude API used by the AI agent). It provides `@server.tool()` decorators, automatic JSON Schema generation from type hints, and multiple transport options.

**Alternatives considered**:
- **Custom tool registry (no SDK)**: Lower overhead but no MCP compatibility, no standardized discovery, no future extensibility.
- **LangChain tool wrappers**: Too heavy a dependency for this use case; adds abstraction without MCP protocol benefits.

## R-002: MCP Integration Architecture

**Decision**: Hybrid in-process approach — define tools with MCP SDK, extract schemas for Anthropic API, execute tool handlers directly (bypass MCP transport).

**Rationale**: The AI agent already uses the Anthropic tool-use API, which is schema-compatible with MCP tool definitions. Running a full MCP client-server transport within a single FastAPI process adds protocol overhead (~2-10ms per tool call) with no practical benefit for this monolithic app. Instead:
1. Define tools using `mcp` SDK's `FastMCP` server → get standardized schemas and handlers.
2. Convert MCP tool schemas to Anthropic API format → pass to Claude.
3. When Claude requests a tool call → invoke the MCP handler directly (in-process).

This gives MCP-compatible tool definitions and a clean separation of tool logic from agent logic, while avoiding transport overhead. The MCP server can later be exposed externally (via stdio or HTTP) if needed.

**Alternatives considered**:
- **Full MCP client-server via stdio**: Requires subprocess management, adds latency, unnecessary for a monolith.
- **MCP server mounted via ASGI**: Real MCP protocol within FastAPI, but still adds client-server round-trip overhead (~5-10ms) per tool call with no user-facing benefit.
- **Direct function calls (no MCP)**: Current approach; works but lacks standardized tool registry, harder to extend.

## R-003: User Context Passing to MCP Tools

**Decision**: Pass `user_id` as a required parameter to each MCP tool handler function, injected by the agent service before calling the tool.

**Rationale**: MCP tools are stateless by design. The `user_id` must be provided per invocation to enforce user isolation. Since the AI agent already has the `user_id` from the authenticated request, it injects this into every tool call. The `user_id` is NOT exposed to the LLM as a tool parameter — it is injected server-side.

**Alternatives considered**:
- **MCP server context/session state**: MCP supports server-side context, but this couples tool execution to MCP transport which we're bypassing.
- **Thread-local or async context var**: Works but is implicit and harder to test.

## R-004: Schema Conversion (MCP → Anthropic)

**Decision**: Write a lightweight converter that transforms MCP tool definitions (JSON Schema) to Anthropic API tool-use format.

**Rationale**: MCP tools use standard JSON Schema for input definitions. The Anthropic API expects `{"name", "description", "input_schema"}` — the same structure. The converter is a simple mapping with no lossy transformation. This keeps the MCP server as the single source of truth for tool definitions.

## R-005: Database Session Management in MCP Tools

**Decision**: Reuse the existing `_get_db_session()` async context manager pattern from `ai_agent.py` within MCP tool handlers.

**Rationale**: The current approach creates a fresh async session per tool execution, with proper commit/rollback handling. This is already tested and works with both PostgreSQL (production) and SQLite (testing). Moving tools to MCP handlers doesn't change the DB access pattern.

## R-006: Testing Strategy

**Decision**: Test MCP tools at three levels — (1) individual tool handler unit tests, (2) schema conversion tests, (3) agent integration tests with MCP tool dispatch.

**Rationale**: The existing test suite in `test_ai_agent.py` tests tool executors directly and the agent loop with mocks. The new tests will mirror this structure but exercise the MCP tool handlers and the dispatch bridge. The `agent_db` fixture for patching DB sessions will be reused.
