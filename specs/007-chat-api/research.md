# Research: Chat API & Conversation Persistence

**Feature**: 007-chat-api | **Date**: 2026-02-09

## Research Summary

All technical unknowns for the Chat API have been resolved through codebase analysis and spec review.

---

## R-001: AI Agent Invocation Pattern

**Question**: How should the Chat API invoke the AI agent (LLM) for generating responses?

**Decision**: Define an `AIAgentService` abstraction with a `generate_response()` method. Initial implementation uses a stub/mock that returns canned responses. The real AI integration (model selection, prompt engineering, MCP tool definitions) is deferred to Spec-6 per the spec's assumptions.

**Rationale**: The spec explicitly states (Assumptions section): "The AI agent implementation details (model selection, prompt engineering, MCP tool definitions) will be handled in a subsequent spec (Spec-6). This spec focuses on the API layer, persistence, and agent invocation interface." By building a clean interface now, Spec-6 can swap in the real implementation without touching any route or persistence code.

**Alternatives Considered**:
- Direct OpenAI/Anthropic SDK call in routes → Rejected: violates separation of concerns, makes testing impossible without mocking external services
- Defer the entire feature → Rejected: frontend already built (006-chat-ui), needs a working API to integrate with

---

## R-002: Frontend Contract Compatibility

**Question**: What exact API shape does the frontend expect?

**Decision**: Match the frontend's existing `chat-client.ts` URL patterns exactly:
- `POST /api/v1/users/{user_id}/chat` — send message
- `GET /api/v1/users/{user_id}/conversations` — get recent conversation
- `GET /api/v1/users/{user_id}/conversations/{conversation_id}/messages` — get history

**Rationale**: The frontend code (`frontend/lib/chat-client.ts`) is already deployed and uses `/api/v1/` prefix. The contract doc (`specs/006-chat-ui/contracts/chat-api.md`) shows `/api/{user_id}/` without `v1`, but the actual frontend code is authoritative.

**Key Response Shapes** (must match `frontend/types/chat.ts`):
- `ChatResponse`: `{ conversation_id: string, response: string }`
- `ConversationResponse`: `{ conversation_id: string | null, created_at?: string, updated_at?: string }`
- `MessagesResponse`: `{ conversation_id: string, messages: Message[] }`
- `Message`: `{ id: string, conversation_id: string, role: "user" | "assistant", content: string, created_at: string }`

---

## R-003: Database Model Design

**Question**: How should conversations, messages, and tool calls be modeled?

**Decision**: Three new SQLModel tables following the existing Task model pattern:
- `conversations` — UUID PK, `owner_id` (indexed), timestamps
- `messages` — UUID PK, FK to `conversations.id` (indexed), `role`, `content`, timestamp
- `tool_calls` — UUID PK, FK to `messages.id` (indexed), `tool_name`, `parameters` (JSON text), `result` (JSON text), `status`

**Rationale**: Follows the exact patterns from the existing `Task` model: UUID primary keys, `owner_id` for user isolation, `datetime.utcnow()` for timestamps, SQLModel with `table=True`.

**Alternatives Considered**:
- Single `messages` table with embedded conversation data → Rejected: violates normalization, makes conversation-level queries harder
- JSONB for tool call parameters → Rejected: SQLite (used in tests) doesn't support JSONB; JSON stored as text string is portable

---

## R-004: Conversation History Context Window

**Question**: How much conversation history should be sent to the AI agent?

**Decision**: Load the last 20 messages from the conversation and pass them as context. This is a constant that can be adjusted in Spec-6.

**Rationale**: 20 messages (10 exchanges) provides sufficient context for most conversations without overwhelming token limits. The AI agent service interface accepts a list of messages, so the caller controls how many to pass.

**Alternatives Considered**:
- All messages → Rejected: unbounded token usage for long conversations
- Configurable via env var → Rejected: premature; keep it simple, adjust in Spec-6

---

## R-005: Authentication and User Isolation

**Question**: How should the chat endpoints authenticate and enforce user isolation?

**Decision**: Reuse the existing `verify_user_owns_resource` dependency from `backend/auth/dependencies.py`. All queries must filter by `owner_id`. Cross-user access returns 404 (not 403).

**Rationale**: This is the established pattern used by all Task endpoints. The spec explicitly requires it (FR-010, FR-011).

---

## R-006: Error Handling for AI Agent Failures

**Question**: What happens when the AI agent fails or times out?

**Decision**:
- The user message is persisted BEFORE calling the AI agent (FR-003).
- If the AI agent fails, the user message stays persisted, and the API returns a 502 error.
- If the AI agent times out (>30 seconds), the API returns a 504 error.
- The conversation state is never corrupted — no partial assistant messages are stored.

**Rationale**: Spec requires (FR-016): "handle AI agent failures gracefully — persisting the user's message and returning an error response without corrupting the conversation." Edge case section specifies 502 for AI unavailability.

---

## R-007: Tool Call Persistence

**Question**: When and how are tool calls stored?

**Decision**: Tool calls are linked to the assistant's Message record. When the AI agent returns a response that includes tool calls, each tool call is persisted as a `ToolCall` record with FK to the assistant message. The tool call's `parameters` and `result` are stored as JSON strings.

**Rationale**: Spec entity definition: "Tool calls are linked to the assistant message that triggered them." Storing as JSON text ensures SQLite test compatibility.

---

## R-008: One Active Conversation Constraint

**Question**: Does the system support multiple simultaneous conversations per user?

**Decision**: No. The spec states: "One active conversation per user is sufficient for the initial implementation. Multi-conversation support is out of scope." The `GET /conversations` endpoint returns the single most recent conversation.

**Rationale**: Explicit spec assumption. The data model still supports multiple conversations (no unique constraint on owner_id), but the API only surfaces the most recent one.
