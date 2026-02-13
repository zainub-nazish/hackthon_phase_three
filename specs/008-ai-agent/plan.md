# Implementation Plan: AI Todo Agent

**Branch**: `008-ai-agent` | **Date**: 2026-02-10 | **Spec**: [specs/008-ai-agent/spec.md](spec.md)
**Input**: Feature specification from `/specs/008-ai-agent/spec.md`

## Summary

Replace the AI agent stub in `backend/services/ai_agent.py` with a real Claude-powered agent that processes natural language messages, selects and executes task management tools (add, list, complete, delete, update), and returns friendly confirmation responses. The agent uses the Anthropic Python SDK with tool use, operates within the existing chat API infrastructure (007-chat-api), and maintains the same `AIAgentService.generate_response()` interface.

## Technical Context

**Language/Version**: Python 3.11+ (matches existing backend)
**Primary Dependencies**: anthropic (SDK v0.79.0+), FastAPI, SQLModel (existing)
**Storage**: Neon PostgreSQL (existing — no new tables)
**Testing**: pytest + pytest-asyncio + unittest.mock (mock Anthropic API for unit tests)
**Target Platform**: Linux server (deployed alongside existing backend)
**Project Type**: Web application (backend-only modification)
**Performance Goals**: <10s total response time (SC-001, including LLM latency), <2s for tool execution
**Constraints**: Non-streaming responses, user isolation on all tool operations, max 20 messages context
**Scale/Scope**: Single agent with 5 tools, single-user conversations

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

The project constitution is unfilled (template placeholders). No specific gates to enforce. Proceeding with standard best practices:

- [x] **Smallest viable change**: Only modifying `ai_agent.py` and `config.py`, no unrelated changes
- [x] **No hardcoded secrets**: Anthropic API key via `ANTHROPIC_API_KEY` env var
- [x] **Test coverage**: Unit tests with mocked Anthropic API, integration tests optional
- [x] **Security**: Tools enforce `owner_id` filtering — same isolation as task endpoints
- [x] **Consistent patterns**: Following existing SQLModel query patterns from `tasks.py`

**Post-Phase 1 Re-check**: All design decisions follow existing patterns. No violations.

## Project Structure

### Documentation (this feature)

```text
specs/008-ai-agent/
├── plan.md              # This file
├── research.md          # Phase 0 output — SDK research, architecture decisions
├── data-model.md        # Phase 1 output — tool definitions, data flow
├── quickstart.md        # Phase 1 output — setup and verification guide
├── contracts/
│   └── tool-definitions.yaml  # Phase 1 output — tool schemas + system prompt
└── tasks.md             # Phase 2 output (/sp.tasks command)
```

### Source Code (repository root)

```text
backend/
├── services/
│   ├── __init__.py              # EXISTING: unchanged
│   └── ai_agent.py              # MODIFY: Replace stub with real Claude agent
├── config.py                    # MODIFY: Add ANTHROPIC_API_KEY, ANTHROPIC_MODEL settings
├── routes/
│   └── chat.py                  # EXISTING: unchanged (agent interface stays the same)
├── models/
│   ├── database.py              # EXISTING: unchanged
│   └── schemas.py               # EXISTING: unchanged
└── tests/
    ├── conftest.py              # MODIFY: Add AI agent test fixtures (mocked Anthropic client)
    └── test_ai_agent.py         # NEW: Agent unit tests + tool execution tests
```

**Structure Decision**: Minimal footprint — only 2 modified files (`ai_agent.py`, `config.py`) and 1 new test file. The agent interface remains unchanged, so `chat.py` needs no modifications.

## Design Decisions

### D-001: Anthropic SDK with Manual Agent Loop

The agent uses the Anthropic Python SDK (`anthropic` package) with a manual agent loop rather than the Tool Runner (beta). The loop: call Claude → receive tool_use blocks → execute tools → send tool_result → repeat until end_turn.

**Why manual over Tool Runner**: The chat API (007-chat-api) requires tool call persistence (ToolCall records). Manual control allows explicit capture of each tool call for database storage.

### D-002: Direct Database Operations for Tools

Agent tools execute direct SQLModel database queries (same pattern as `backend/routes/tasks.py`) rather than calling HTTP endpoints. The agent creates its own database session for tool execution.

**Why direct over HTTP**: Avoids HTTP overhead and auth token complexity within the same server process. The agent already has the verified `user_id`.

### D-003: Claude Haiku 4.5 as Default Model

Default model is `claude-haiku-4-5-20251001` — configurable via `ANTHROPIC_MODEL` env var. Haiku is fast and cost-effective for straightforward tool-calling. Users can upgrade to Sonnet or Opus for more nuanced conversations.

### D-004: System Prompt as Inline Constant

The system prompt is defined as a string constant in `ai_agent.py`. Not externalized to a file or database — simplicity for a single-agent system. Can be extracted later if needed.

### D-005: Tool Error Handling via tool_result

Tool execution errors (task not found, validation failure) are returned as `tool_result` with `is_error=True`. Claude then generates a user-friendly error message. This leverages Claude's natural language ability to explain errors.

### D-006: Graceful Fallback When API Key Missing

If `ANTHROPIC_API_KEY` is not configured, the agent falls back to the existing stub behavior (returns canned response). This allows the backend to run without an API key in development/testing.

## Implementation Phases

### Phase 1: Configuration (Foundation)
1. Add `ANTHROPIC_API_KEY` and `ANTHROPIC_MODEL` to `backend/config.py`
2. Install `anthropic` package as a dependency

### Phase 2: Tool Execution Functions
1. Create tool executor functions in `ai_agent.py` — one async function per tool
2. Each function takes `(parameters: dict, user_id: str, session: AsyncSession)` and returns a dict result
3. Functions follow the same SQLModel query patterns from `tasks.py`
4. Add a `TOOLS` constant with Anthropic tool definitions (JSON schema)
5. Add a `SYSTEM_PROMPT` constant

### Phase 3: Agent Loop Implementation
1. Replace `AIAgentService.generate_response()` with real Claude API integration
2. Implement the agent loop: call → tool_use → execute → tool_result → repeat
3. Collect tool call data into `ToolCallData` objects for persistence
4. Handle Anthropic API errors (rate limits, auth failures) — return appropriate errors
5. Implement fallback to stub when API key is not configured

### Phase 4: Testing
1. Create `test_ai_agent.py` with mocked Anthropic client
2. Unit test each tool executor function (direct DB operations)
3. Unit test the agent loop (mock API responses with tool_use blocks)
4. Test error scenarios: task not found, API failure, missing API key fallback
5. Test system prompt and tool definitions are correctly formatted

### Phase 5: Integration & Polish
1. End-to-end test via chat API (POST /chat → agent → tool → response)
2. Verify tool call persistence (ToolCall records in DB after agent invocation)
3. Test context resolution (multi-turn conversations with task references)
4. Verify all 5 tools work through the full stack

## Risks and Mitigations

1. **Anthropic API Latency**: Claude API calls add 1-5s per tool-use round. Multi-step operations (list → delete) may take 5-10s. **Mitigation**: Use Haiku for speed; documented in SC-001 as <10s acceptable. Non-streaming keeps implementation simple.

2. **API Key Exposure**: Anthropic API key must be kept secret. **Mitigation**: Loaded via env var, never hardcoded. `.env` is gitignored. Settings validation warns if missing.

3. **Tool Execution Side Effects**: Agent tools modify real task data (create, delete, update). **Mitigation**: All tools enforce `owner_id` filtering. Agent only modifies the authenticated user's tasks. Mocked Anthropic API in tests prevents accidental real API calls.

4. **Model Hallucination**: Claude might reference non-existent tasks. **Mitigation**: System prompt explicitly forbids hallucination. Tools return actual DB data — agent can only act on real results. Tests verify no fabricated task references.

## Complexity Tracking

No violations to justify — all design decisions follow existing patterns.

| Aspect | Decision | Justification |
|--------|----------|---------------|
| Manual agent loop | No Tool Runner | Need explicit tool call capture for DB persistence |
| Direct DB queries | No HTTP calls | Same-process optimization, same query patterns |
| Inline system prompt | No external file | Single agent, simplicity; can extract later |
| Haiku default model | Not Sonnet/Opus | Cost-effective for simple CRUD tool calling |
