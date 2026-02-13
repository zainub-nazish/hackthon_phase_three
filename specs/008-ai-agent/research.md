# Research: AI Todo Agent

**Feature**: 008-ai-agent | **Date**: 2026-02-10

## Research Summary

All technical unknowns for the AI Agent feature have been resolved through SDK documentation analysis, codebase exploration, and best-practice evaluation.

---

## R-001: AI Model Provider and SDK

**Question**: Which LLM provider and SDK should power the agent?

**Decision**: Anthropic Python SDK (`anthropic` v0.79.0+) with Claude models. Default model: `claude-haiku-4-5-20251001` for cost efficiency. Configurable via `ANTHROPIC_MODEL` env var to allow upgrading to Sonnet/Opus.

**Rationale**:
- Project already uses Claude (Claude Code for development).
- Anthropic SDK has native tool use support with structured JSON schema tool definitions.
- Claude Haiku 4.5 is fast and cost-effective for straightforward tool-calling tasks like CRUD operations.
- Tool use API is stable and well-documented (stop_reason="tool_use", tool_use/tool_result blocks).

**Alternatives Considered**:
- OpenAI SDK with GPT-4 → Rejected: adds a second provider dependency, project is already Claude-oriented.
- LangChain/LangGraph → Rejected: over-engineered for 5 CRUD tools; adds heavy dependency for minimal gain.
- Anthropic Agent SDK → Evaluated but too early/complex for this scope. Manual agent loop gives full control over tool persistence.

---

## R-002: Agent Architecture Pattern

**Question**: How should the agent loop be structured — automatic (Tool Runner) or manual?

**Decision**: Manual agent loop using the low-level Messages API. The `AIAgentService.generate_response()` method implements the loop: call → tool_use → execute → tool_result → call → end_turn.

**Rationale**:
- The chat API (007-chat-api) requires tool call persistence (ToolCall records in DB). The manual loop gives explicit control over when and what to persist.
- The Tool Runner (beta) auto-executes tools, making it harder to intercept for DB persistence.
- Manual loop allows per-tool error handling and custom logging.
- Only 5 tools — complexity is minimal.

**Alternatives Considered**:
- Tool Runner (beta) → Rejected: doesn't expose tool call details for persistence without monkey-patching.
- Programmatic tool calling (beta) → Rejected: advanced feature for data processing, not needed for simple CRUD.

---

## R-003: Tool Execution Strategy

**Question**: Should agent tools call HTTP endpoints or access the database directly?

**Decision**: Direct database operations using SQLModel queries — same pattern as the existing route handlers in `backend/routes/tasks.py`. The agent creates its own database session for tool execution.

**Rationale**:
- Avoids HTTP roundtrip overhead (localhost HTTP call within same process).
- Avoids auth complexity — the agent already has the verified `user_id`.
- Follows the same query patterns already tested in tasks.py.
- The `generate_response` interface already receives `user_id`, so tools can filter by `owner_id`.

**Alternatives Considered**:
- HTTP calls to task endpoints → Rejected: unnecessary overhead, auth token management complexity within same server.
- Shared TaskService class → Rejected: would require refactoring existing routes; over-engineering for this scope.

---

## R-004: System Prompt Design

**Question**: How should the system prompt be structured?

**Decision**: Store system prompt as a constant string in `backend/services/ai_agent.py`. The prompt defines the agent's role, tool usage guidelines, confirmation format, error handling, and context resolution rules.

**Rationale**:
- Simple and co-located with the agent code.
- Easy to iterate — change the constant, restart server.
- No need for a separate prompt management system for a single agent.
- System prompt best practices from Anthropic docs: clear role, explicit guidelines, examples of desired behavior.

**Alternatives Considered**:
- External file (YAML/JSON) → Rejected: adds file I/O complexity for a single prompt. Can move to file later if needed.
- Database-stored prompts → Rejected: massive over-engineering for iteration speed at this stage.

---

## R-005: Tool Definition Format

**Question**: How should the 5 agent tools be defined?

**Decision**: JSON Schema tool definitions following Anthropic's tool use format. Each tool has `name`, `description` (3-4+ sentences per Anthropic best practices), and `input_schema` (JSON Schema object with properties and required fields).

**Rationale**:
- Anthropic docs emphasize that description quality is the #1 driver for tool selection accuracy.
- Detailed descriptions (3-4+ sentences) with examples of when to use each tool.
- `input_schema` with strict types ensures Claude generates valid parameters.

**Tool Definitions**:
1. `add_task` — title (required, string), description (optional, string)
2. `list_tasks` — status (optional, enum: "all"/"pending"/"completed", default "all")
3. `complete_task` — task_id (required, string/UUID)
4. `delete_task` — task_id (required, string/UUID)
5. `update_task` — task_id (required, string/UUID), title (optional, string), description (optional, string)

---

## R-006: Configuration and API Key Management

**Question**: How to configure the Anthropic API key and model selection?

**Decision**: Add two new environment variables to `backend/config.py`:
- `ANTHROPIC_API_KEY` (required for AI features) — the API key
- `ANTHROPIC_MODEL` (optional, default `claude-haiku-4-5-20251001`) — the model to use

**Rationale**: Follows the existing pattern in `config.py` using `pydantic-settings` with `Field(alias=...)`. No hardcoded secrets per constitution/best practices.

---

## R-007: Multi-Step Tool Resolution

**Question**: How should the agent resolve task references when task_id is unknown?

**Decision**: The agent relies on Claude's native multi-step tool calling. When the user says "delete the buy milk task", Claude will:
1. Call `list_tasks` to find matching tasks
2. Review the results
3. Call `delete_task` with the matched task_id
4. If multiple matches, ask the user to clarify

This happens naturally within the agent loop — Claude makes multiple tool calls per turn as needed. The system prompt instructs: "If you need to find a task by name, use list_tasks first."

**Rationale**: Claude's tool-use capability natively supports multi-step resolution. No custom logic needed — the system prompt guides behavior.

---

## R-008: Error Handling Strategy

**Question**: How should tool execution errors be communicated to the user?

**Decision**: Three-tier error handling:
1. **Tool execution errors** (task not found, validation failure): Return error as `tool_result` with `is_error=True`. Claude generates a user-friendly message.
2. **Anthropic API errors** (rate limit, auth failure): Caught by the agent loop, return 502 to chat API (existing error handling from 007-chat-api).
3. **Unexpected exceptions**: Caught by try/except in agent loop, return 502.

**Rationale**: Claude is excellent at converting error messages into user-friendly language. By passing errors as tool results, the model explains what went wrong naturally.
