# Implementation Plan: Chat UI (Frontend)

**Branch**: `006-chat-ui` | **Date**: 2026-02-08 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/006-chat-ui/spec.md`

## Summary

Build a conversational chatbot interface using OpenAI ChatKit (`@openai/chatkit-react`) that allows authenticated users to manage their todos through natural language. The `<ChatKit />` component provides a drop-in chat UI with message rendering, input handling, auto-scroll, and typing indicators. It communicates with a backend Chat API proxy endpoint (`POST /chatkit`) and integrates into the existing Next.js dashboard layout under a new `/chat` route.

## Technical Context

**Language/Version**: TypeScript 5.7 / React 18.3 / Next.js 16.1
**Primary Dependencies**: @openai/chatkit-react, Better Auth, Tailwind CSS 3.4
**Storage**: N/A (frontend-only; backend handles persistence via Neon PostgreSQL)
**Testing**: Manual verification via quickstart.md
**Target Platform**: Web browsers (desktop + mobile, minimum 375px width)
**Project Type**: Web application (frontend portion only)
**Performance Goals**: Optimistic message rendering (<100ms), history load <2s
**Constraints**: Non-streaming responses (full response returned at once); ChatKit handles internal state
**Scale/Scope**: Single chat page, ~6 new files, ~1 modified file (nav)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| # | Principle | Gate | Status |
|---|-----------|------|--------|
| I | Spec-First Development | Spec approved before implementation | PASS |
| II | Security by Design | Auth token attached to all API calls; session validation | PASS |
| III | Deterministic Behavior | Acceptance scenarios defined in Given/When/Then | PASS |
| IV | Separation of Concerns | Frontend handles only UI; API calls through defined contracts | PASS |
| V | Reproducibility | Plan + spec sufficient to rebuild feature | PASS |
| VI | API Standards | Chat API contract defined with request/response schemas | PASS |
| VII | AI Agent Safety | N/A for frontend (agent logic is backend Spec-6) | PASS |
| VIII | Stateless Architecture | Frontend does not hold server-side session state; each request self-contained | PASS |

**Post-Design Re-check**: All gates still pass. ChatKit manages UI state internally; no server-side session state held by frontend.

## Project Structure

### Documentation (this feature)

```text
specs/006-chat-ui/
├── plan.md              # This file
├── research.md          # Phase 0: ChatKit research & decisions
├── data-model.md        # Phase 1: Frontend data types
├── quickstart.md        # Phase 1: Setup & verification guide
├── contracts/
│   └── chat-api.md      # Phase 1: API contract (frontend perspective)
└── tasks.md             # Phase 2: /sp.tasks output (NOT created here)
```

### Source Code (repository root)

```text
frontend/
├── app/
│   └── (dashboard)/
│       ├── layout.tsx                  # EXISTING — no changes needed
│       └── chat/
│           └── page.tsx                # NEW — Chat page component
├── components/
│   ├── chat/
│   │   ├── chat-container.tsx          # NEW — ChatKit wrapper with config
│   │   ├── chat-welcome.tsx            # NEW — Welcome state (no conversation)
│   │   └── chat-error.tsx              # NEW — Error display component
│   └── layout/
│       └── nav.tsx                     # MODIFY — Add "Chat" navigation link
├── hooks/
│   └── use-chat.ts                     # NEW — Chat state management hook
├── lib/
│   └── chat-client.ts                  # NEW — Chat API helper functions
└── types/
    └── chat.ts                         # NEW — Chat TypeScript types
```

**Structure Decision**: Web application (frontend only). This feature adds a `/chat` route under the existing `(dashboard)` group, reusing AuthGuard and Header. No backend changes in this spec — backend endpoints are defined in Spec-5.

## Key Design Decisions

### D1: ChatKit as Primary UI Component

ChatKit (`<ChatKit />`) renders the entire chat interface including message list, input field, typing indicators, and auto-scroll. This means:
- No need to build MessageList, MessageItem, ChatInput components from scratch.
- ChatKit manages internal message state, loading indicators, and scroll behavior.
- The `useChatKit` hook configures the backend proxy URL and auth headers.
- Theme is set to dark mode with teal accent to match existing design.

### D2: ChatKit Proxy Architecture

ChatKit communicates with the backend through a single `POST /chatkit` endpoint (managed by ChatKit Python SDK on the backend, Spec-5). The frontend configures ChatKit with the proxy URL:
- `url`: Points to `NEXT_PUBLIC_API_URL + /chatkit`
- Auth: Session token forwarded via ChatKit configuration headers.
- The proxy handles thread management, message persistence, and AI agent invocation internally.

### D3: Conversation History via REST

For loading conversation history on page revisit (US2):
- On mount, call `GET /api/{user_id}/conversations` to get the most recent conversation_id.
- Pass the conversation_id to ChatKit's configuration to restore the thread.
- ChatKit loads messages from the backend proxy automatically when given a thread/conversation reference.

### D4: Navigation Integration

Add "Chat" link to the Header navigation (`nav.tsx`) alongside the existing "Tasks" link:
- Desktop: Text link in the top nav bar.
- Mobile: Entry in the hamburger menu.
- Active route indicator follows existing pattern (teal highlight).

### D5: Error Handling Strategy

- **Network errors**: ChatKit displays built-in error states; additionally, `chat-error.tsx` provides a retry mechanism.
- **Auth errors (401)**: Intercepted by the existing AuthGuard/apiClient pattern → redirect to login.
- **API errors (400, 422, 500)**: Displayed inline in the chat as system messages.

## Component Architecture

```
/chat page
└── ChatContainer
    ├── ChatKit (from @openai/chatkit-react)
    │   ├── Internal MessageList
    │   ├── Internal Input + Send Button
    │   └── Internal Typing Indicator
    ├── ChatWelcome (shown when no conversation exists)
    └── ChatError (shown on unrecoverable errors)
```

## Complexity Tracking

> No constitution violations detected. No complexity justifications needed.
