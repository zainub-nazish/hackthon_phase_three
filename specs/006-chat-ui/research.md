# Research: Chat UI (Frontend)

**Feature**: 006-chat-ui
**Date**: 2026-02-08
**Status**: Complete

## R1: OpenAI ChatKit Integration Approach

**Decision**: Use `@openai/chatkit-react` with Full Proxy approach (custom backend)

**Rationale**:
- ChatKit provides a drop-in `<ChatKit />` component that handles the entire chat UI (message list, input, typing indicators, scroll management).
- The Full Proxy approach routes all operations through our FastAPI backend rather than directly to OpenAI, which aligns with our architecture (Spec-5 Chat API owns conversation logic).
- ChatKit manages internal state (threads, messages, UI) — no external state management needed.
- The `useChatKit` hook provides configuration and event control.
- Supports dark/light theme via `colorScheme` prop, CSS variables for custom theming.

**Alternatives Considered**:
- **Custom chat components from scratch**: Rejected — would require implementing message list, auto-scroll, typing indicators, input handling manually. ChatKit provides all of this.
- **@chatscope/chat-ui-kit-react**: Provides granular components (ChatContainer, MessageList, etc.) but requires more assembly. ChatKit is more opinionated and faster to integrate.
- **ChatKit getClientSecret approach**: Would let OpenAI handle sessions/threads directly. Rejected — our Spec-5 Chat API is the single orchestration layer, and we need our own conversation persistence.

## R2: ChatKit Backend Integration Pattern

**Decision**: Use ChatKit Python SDK (`chatkit` package) with FastAPI for the server proxy

**Rationale**:
- The ChatKit Python SDK provides `ChatKitServer` base class that handles message processing.
- A single `POST /chatkit` endpoint handles all ChatKit operations (sessions, threads, messages).
- Our existing FastAPI backend can host this endpoint alongside existing routes.
- The SDK supports tool calling, streaming responses, and custom actions — aligns with MCP tool invocation in Spec-6/7.
- Data persistence through custom `chatkit.store.Store` implementation backed by our existing Neon PostgreSQL.

**Alternatives Considered**:
- **Raw fetch calls to custom REST API**: Would work but requires building the entire ChatKit protocol handler manually. The SDK handles serialization/deserialization.
- **WebSocket-based chat**: Overhead for non-streaming first iteration. ChatKit's HTTP-based approach is simpler and aligns with stateless architecture (Constitution Principle VIII).

## R3: Frontend Routing for Chat

**Decision**: Add chat as a new route under the existing `(dashboard)` group at `/chat`

**Rationale**:
- Reuses the existing AuthGuard + Header layout from the dashboard.
- The chat page will be a sibling to `/tasks` under the `(dashboard)` group route.
- Navigation link added to the Header component alongside "Tasks".
- The existing dark theme and responsive design carry over automatically.

**Alternatives Considered**:
- **Replace the tasks page with chat**: Rejected — the tasks page remains useful for direct CRUD operations.
- **Separate standalone route outside dashboard**: Rejected — would lose AuthGuard and Header, requiring duplication.

## R4: Chat Theming Strategy

**Decision**: Use ChatKit's built-in theming with CSS variables mapped to existing Tailwind color tokens

**Rationale**:
- ChatKit uses its own styling system with CSS custom properties.
- We can set `colorScheme: "dark"` to match our dark theme.
- Accent colors can be mapped to our primary teal (#2DD4BF).
- The surrounding page layout (header, container) uses Tailwind CSS as before.
- No conflict — ChatKit renders as a self-contained component within our Tailwind-styled container.

**Alternatives Considered**:
- **Override all ChatKit styles with Tailwind**: Fragile, would break on ChatKit updates.
- **Build custom chat UI with Tailwind only**: More control but much more effort, loses ChatKit's built-in features.

## R5: API Communication Pattern

**Decision**: ChatKit's internal fetch handles API calls to `/chatkit` proxy endpoint; conversation history loaded via separate REST endpoint

**Rationale**:
- ChatKit manages its own API calls when configured with the proxy URL.
- For conversation history (US2), we need a separate REST call on page load: `GET /api/{user_id}/conversations/{conversation_id}/messages`.
- The existing `apiClient` from `lib/api-client.ts` can be used for REST calls outside of ChatKit's scope.
- Auth token injection is handled by ChatKit's configuration for its calls, and by our apiClient for REST calls.

**Alternatives Considered**:
- **All communication through ChatKit only**: ChatKit doesn't natively support loading historical conversation lists from our custom backend without the proxy.
- **All communication through raw fetch**: Would bypass ChatKit's internal state management.

## R6: Package Dependencies

**Decision**: Add `@openai/chatkit-react` (includes `@openai/chatkit` as dependency)

**Rationale**:
- Single npm install adds both the React bindings and core web component.
- Peer dependencies: React 18+ (already satisfied).
- No conflicting dependencies with existing stack.

**Packages to Add**:
- `@openai/chatkit-react` — React component and hooks
