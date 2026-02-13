# Quickstart: Chat UI (Frontend)

**Feature**: 006-chat-ui
**Date**: 2026-02-08

## Prerequisites

- Node.js 18+
- Frontend dependencies installed (`npm install` in `frontend/`)
- Backend running at `http://localhost:8000` (for Chat API)
- Better Auth configured with valid session
- `.env.local` configured with `NEXT_PUBLIC_API_URL` and auth secrets

## Setup

1. Install ChatKit dependency:

```bash
cd frontend
npm install @openai/chatkit-react
```

2. Ensure environment variables are set in `.env.local`:

```
BETTER_AUTH_SECRET=your-secret-here
NEXT_PUBLIC_APP_URL=http://localhost:3000
NEXT_PUBLIC_API_URL=http://localhost:8000
DATABASE_URL=your-neon-connection-string
```

3. Start the development server:

```bash
npm run dev
```

4. Navigate to `http://localhost:3000/chat` (must be logged in).

## Verification Steps

### V1: Chat Page Loads (US1)

1. Log in with valid credentials.
2. Navigate to `/chat`.
3. Verify: Chat interface is visible with input field and send button.
4. Verify: Header shows "Chat" as active navigation item.

### V2: Send and Receive Message (US1)

1. Type "Show my tasks" in the input field.
2. Press Enter or click Send.
3. Verify: User message appears right-aligned immediately.
4. Verify: Loading indicator shows while waiting.
5. Verify: AI response appears left-aligned after processing.
6. Verify: Input field is cleared after sending.

### V3: Conversation Persistence (US2)

1. Send a message and receive a response.
2. Refresh the page (F5).
3. Verify: Previous messages are loaded and displayed.

### V4: Error Handling

1. Stop the backend server.
2. Send a message.
3. Verify: An error message appears in the chat area.
4. Verify: The user can understand what went wrong.

### V5: Mobile Responsiveness

1. Open browser DevTools → responsive mode → 375px width.
2. Verify: Chat interface is fully usable.
3. Verify: Messages, input, and send button are accessible.

## File Structure

```
frontend/
├── app/
│   └── (dashboard)/
│       └── chat/
│           └── page.tsx            # Chat page component
├── components/
│   └── chat/
│       ├── chat-container.tsx      # ChatKit wrapper with configuration
│       ├── chat-welcome.tsx        # Welcome state for new conversations
│       └── chat-error.tsx          # Error display component
├── hooks/
│   └── use-chat.ts                 # Chat state management hook
├── lib/
│   └── chat-client.ts             # Chat API helper functions
└── types/
    └── chat.ts                     # Chat-related TypeScript types
```
