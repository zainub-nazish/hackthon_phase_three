# Tasks: Chat UI (Frontend)

**Input**: Design documents from `/specs/006-chat-ui/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/chat-api.md, quickstart.md

**Tests**: No test tasks generated — testing is not explicitly requested in the feature specification. Manual verification via quickstart.md.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app (frontend only)**: All paths relative to `frontend/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Install dependencies and create foundational file structure

- [x] T001 Install `@openai/chatkit-react` dependency in `frontend/` via `npm install @openai/chatkit-react`
- [x] T002 [P] Create chat TypeScript types in `frontend/types/chat.ts` with Message, Conversation, ChatRequest, ChatResponse, and ChatState interfaces per data-model.md
- [x] T003 [P] Create chat API client helper in `frontend/lib/chat-client.ts` with functions: `sendMessage(userId, request)`, `getConversation(userId)`, and `getMessages(userId, conversationId)` using the existing `apiClient` from `frontend/lib/api-client.ts` per contracts/chat-api.md

**Checkpoint**: Dependencies installed, types defined, API client ready

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**CRITICAL**: No user story work can begin until this phase is complete

- [x] T004 Add "Chat" navigation link to `frontend/components/layout/nav.tsx` — add `{ href: "/chat", label: "Chat" }` to the `navItems` array in both `MobileNav` and `DesktopNav` components
- [x] T005 Create chat page route at `frontend/app/(dashboard)/chat/page.tsx` — a "use client" page component that renders the ChatContainer component within the existing dashboard layout

**Checkpoint**: Foundation ready — `/chat` route exists, navigation links work, user story implementation can begin

---

## Phase 3: User Story 1 - Send a Chat Message (Priority: P1) MVP

**Goal**: User can type a message, send it, and see the AI response in the chat interface

**Independent Test**: Open `/chat`, type "Show my tasks", press Enter, verify user message appears right-aligned, loading indicator shows, AI response appears left-aligned

### Implementation for User Story 1

- [x] T006 [US1] Create ChatContainer component in `frontend/components/chat/chat-container.tsx` — wraps the `<ChatKit />` component from `@openai/chatkit-react` with configuration: proxy URL pointing to `NEXT_PUBLIC_API_URL + /chatkit`, dark color scheme, teal accent color (#2DD4BF), and auth headers from Better Auth session via `useChatKit` hook
- [x] T007 [US1] Create `useChat` hook in `frontend/hooks/use-chat.ts` — manages chat state (conversationId, messages, isLoading, error), provides `sendMessage` function that calls `sendMessage()` from chat-client.ts, handles optimistic message rendering (adds user message to list immediately), stores conversation_id from first response, disables input during in-flight requests (FR-010, FR-011), and clears input after send (FR-009)
- [x] T008 [US1] Integrate ChatContainer into chat page `frontend/app/(dashboard)/chat/page.tsx` — connect useChat hook, useAuth hook for user_id, pass configuration to ChatContainer, handle the case where user is not yet loaded (show spinner)
- [x] T009 [US1] Create ChatError component in `frontend/components/chat/chat-error.tsx` — displays user-friendly error messages for API failures (network errors, 400, 500), provides a "Try again" button that clears the error and re-enables input (FR-012)
- [x] T010 [US1] Add error handling to ChatContainer `frontend/components/chat/chat-container.tsx` — catch errors from API calls, display ChatError component inline, handle 401 errors by redirecting to login via existing auth pattern (FR-016), implement request cancellation on component unmount via AbortController

**Checkpoint**: User can send messages and receive AI responses. Core chat interaction works end-to-end.

---

## Phase 4: User Story 2 - View Conversation History (Priority: P2)

**Goal**: Previous messages persist across page reloads so user maintains context

**Independent Test**: Send a message, refresh the page, verify previous messages still appear

### Implementation for User Story 2

- [x] T011 [US2] Add conversation restoration to `useChat` hook in `frontend/hooks/use-chat.ts` — on mount, call `getConversation(userId)` from chat-client.ts to get the most recent conversation_id, if one exists call `getMessages(userId, conversationId)` to load message history, populate messages state with loaded history, pass conversation reference to ChatKit configuration for thread restoration
- [x] T012 [US2] Create ChatWelcome component in `frontend/components/chat/chat-welcome.tsx` — displayed when no conversation exists (conversation_id is null), shows a welcome message encouraging the user to start chatting (e.g., "Ask me to manage your tasks"), styled with dark theme matching existing empty states in the app
- [x] T013 [US2] Integrate ChatWelcome into ChatContainer `frontend/components/chat/chat-container.tsx` — show ChatWelcome when conversationId is null and messages array is empty, hide ChatWelcome once the user sends their first message, auto-scroll to bottom when history loads (FR-013)

**Checkpoint**: Conversation history persists across page reloads. Welcome state shows for new users.

---

## Phase 5: User Story 3 - Real-Time Loading Feedback (Priority: P3)

**Goal**: Visual typing/loading indicator shows while waiting for AI response

**Independent Test**: Send a message, observe typing indicator appears between send and response

### Implementation for User Story 3

- [x] T014 [US3] Configure ChatKit typing indicator in `frontend/components/chat/chat-container.tsx` — ensure ChatKit's built-in typing/loading indicator is enabled and visible during API processing, verify the indicator uses the dark theme styling, confirm the indicator does not show a premature timeout error for requests up to 30 seconds

**Checkpoint**: Loading feedback is visible during AI processing. No premature timeout errors.

---

## Phase 6: User Story 4 - Tool Confirmation Display (Priority: P4)

**Goal**: Clear confirmation messages when AI performs todo actions (create, complete, delete, update)

**Independent Test**: Ask "Add task Buy milk", verify response confirms task creation with task name

### Implementation for User Story 4

- [x] T015 [US4] Verify ChatKit renders tool confirmation responses clearly in `frontend/components/chat/chat-container.tsx` — confirm that AI responses containing action confirmations (e.g., "Task created: Buy milk") are rendered as standard assistant messages, verify error responses from tool failures are displayed in friendly natural language, no additional component needed if ChatKit's default rendering is sufficient

**Checkpoint**: Tool confirmation messages are clearly displayed. Error messages are user-friendly.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [x] T016 Ensure mobile responsiveness across all chat components — test chat page at 375px width, verify input field, send button, and messages are accessible, adjust ChatKit container CSS if needed for full-height layout on mobile (FR-017)
- [x] T017 [P] Add input validation edge cases to `useChat` hook in `frontend/hooks/use-chat.ts` — prevent empty/whitespace-only messages (FR-010), add character limit warning at 2000 characters, handle rapid message sending by disabling input during in-flight (FR-011)
- [x] T018 [P] Run quickstart.md verification — execute all 5 verification steps (V1-V5) from `specs/006-chat-ui/quickstart.md`, document any issues found

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on T001 (ChatKit installed) and T002/T003 (types and client ready)
- **User Story 1 (Phase 3)**: Depends on Phase 1 + Phase 2 completion — BLOCKS US2, US3, US4
- **User Story 2 (Phase 4)**: Depends on Phase 3 (needs working chat to test history persistence)
- **User Story 3 (Phase 5)**: Can start after Phase 3 (independent of US2)
- **User Story 4 (Phase 6)**: Can start after Phase 3 (independent of US2, US3)
- **Polish (Phase 7)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) — No dependencies on other stories
- **User Story 2 (P2)**: Depends on US1 (needs chat functionality to test history)
- **User Story 3 (P3)**: Can start after US1 — Independent of US2
- **User Story 4 (P4)**: Can start after US1 — Independent of US2, US3

### Within Each User Story

- Types and API client before components
- Hook logic before component integration
- Core functionality before error handling
- Story complete before moving to next priority

### Parallel Opportunities

- T002 and T003 can run in parallel (different files, no dependencies)
- T004 and T005 can run in parallel after Phase 1 (different files)
- US3 (Phase 5) and US4 (Phase 6) can run in parallel after US1 is complete
- T016, T017, and T018 can run in parallel in the Polish phase

---

## Parallel Example: Phase 1 Setup

```bash
# Launch parallel setup tasks:
Task T002: "Create chat TypeScript types in frontend/types/chat.ts"
Task T003: "Create chat API client helper in frontend/lib/chat-client.ts"
```

## Parallel Example: After US1 Complete

```bash
# US3 and US4 can run in parallel:
Task T014: "Configure ChatKit typing indicator (US3)"
Task T015: "Verify ChatKit renders tool confirmations (US4)"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T003)
2. Complete Phase 2: Foundational (T004-T005)
3. Complete Phase 3: User Story 1 (T006-T010)
4. **STOP and VALIDATE**: Test User Story 1 independently via quickstart V1 + V2
5. Deploy/demo if ready — users can send and receive chat messages

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (history persistence)
4. Add User Story 3 + 4 in parallel → Test → Deploy/Demo (polish)
5. Each story adds value without breaking previous stories

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- ChatKit manages most UI complexity internally — tasks focus on configuration and integration, not building chat UI from scratch
