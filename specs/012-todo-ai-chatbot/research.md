# Research: Todo AI Chatbot System (012-todo-ai-chatbot)

**Date**: 2026-02-21 | **Branch**: `012-todo-ai-chatbot`

---

## 1. Agentic Loop Architecture

**Decision**: Use OpenAI Agents SDK (`openai-agents`) with MCP via stdio subprocess for the main backend; use direct in-process function dispatch for the HF Space deployment.

**Rationale**:
- The OpenAI Agents SDK handles the tool-call loop automatically (call tool → feed result → repeat until `end_turn`), reducing boilerplate.
- MCP via stdio is the cleanest separation for the main backend — tools run as a child process, decoupled from the FastAPI event loop.
- The HF Space cannot spawn reliable subprocesses in the free tier sandbox, so direct function dispatch is used there with the same tool signatures.

**Alternatives considered**:
- Manual loop with raw `openai.chat.completions.create` — viable but requires manual round-trip management; rejected in favour of the SDK's built-in loop.
- LangChain agents — heavyweight dependency, harder to test, rejected.

---

## 2. MCP Tool Execution Strategy

**Decision**: MCP tools are implemented as `@server.tool()` decorated async functions in `backend/services/mcp_tools.py` using `FastMCP`. Each tool opens its own database session via `_get_db_session()`.

**Rationale**:
- Tools need their own DB sessions because they run in a subprocess context (stdio transport) separate from the FastAPI request session.
- `FastMCP` from the official MCP Python SDK (`mcp>=1.26.0`) provides decorator-based tool registration and handles JSON schema generation automatically.
- User isolation is enforced server-side: every tool accepts `user_id` and filters all DB queries by `owner_id == user_id`.

**Alternatives considered**:
- Sharing the FastAPI request session with tools — not possible across subprocess boundary.
- HTTP-based MCP transport — adds latency and port management complexity; stdio simpler for co-located deployment.

---

## 3. Database Schema — Primary Key Type

**Decision**: Use UUID primary keys (not integer `id`) for all tables.

**Rationale**:
- UUIDs prevent enumeration attacks (users cannot guess neighbouring task IDs).
- Neon PostgreSQL supports UUID natively; `uuid4()` generation is done in Python to avoid DB round-trips.
- The spec describes `int` IDs, but the existing implementation uses UUIDs — UUIDs are strictly better for a web API.

**Aliases**: `owner_id` is used instead of `user_id` as the column name to avoid SQL reserved word conflicts and to be explicit about ownership semantics.

---

## 4. Conversation Context Window

**Decision**: Load the last **20** messages (10 user + ~10 assistant turns) as context, not the spec's stated 10.

**Rationale**:
- Each back-and-forth exchange produces 2 messages (user + assistant). Loading 10 messages covers only 5 exchanges — too shallow for multi-step task management flows.
- 20 messages gives 10 full exchanges while staying well within GPT-4o's context window.
- The constant `MAX_CONTEXT_MESSAGES = 20` is defined in `backend/routes/chat.py` and can be tuned without code changes.

---

## 5. Tool Call Persistence

**Decision**: Persist every tool call (name, parameters, result, status) to the `tool_calls` table linked to the assistant message.

**Rationale**:
- Enables audit trails — operators can see exactly what the AI did and why.
- Supports debugging when the agent takes unexpected actions.
- The `ToolCall` model (message_id FK → messages.id) maintains the full causal chain: user message → assistant message → tool calls.

---

## 6. Auth Integration

**Decision**: Use `verify_user_owns_resource` FastAPI dependency (Better Auth JWT verification) on all chat endpoints. `user_id` in the URL path is cross-checked against the JWT `sub` claim.

**Rationale**:
- Consistent with the rest of the API (tasks, auth routes all use the same dependency).
- Prevents horizontal privilege escalation — a user cannot send messages under another user's conversation even if they guess the UUID.

---

## 7. Error Handling Strategy

**Decision**: AI agent errors return HTTP 502 to the client; tool call errors are captured in the agent loop and returned as natural-language messages to the user (not HTTP errors).

**Rationale**:
- Tool failures (task not found, DB error) should be communicated conversationally — the AI translates the `is_error` result into a friendly message.
- Agent-level failures (model unavailable, auth error) are infrastructure problems the user cannot fix, so they surface as HTTP 502.

---

## 8. Deployment Split (Main vs HF Space)

**Decision**: Maintain two deployments with the same API contract but different AI backends:
- **Main backend** (`backend/`): OpenAI Agents SDK + MCP via stdio + Neon DB
- **HF Space** (`huggies_face_three/`): OpenAI GPT-4o with direct function dispatch + same Neon DB

**Rationale**:
- HF Space free tier cannot reliably spawn subprocesses, so MCP stdio is not viable there.
- Both deployments share the same DB, schemas, and API contract — the frontend is unaware of the difference.
- The HF Space is the public-facing deployment; the main backend is for development/reference.
