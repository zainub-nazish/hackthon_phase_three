# Data Model: Chat UI (Frontend)

**Feature**: 006-chat-ui
**Date**: 2026-02-08

## Overview

The Chat UI feature introduces two frontend entities: **Conversation** and **Message**. These are TypeScript types used for API communication and UI rendering. The source of truth for these entities is the backend database (Spec-8); the frontend only holds them in memory during the user's session.

## Entities

### Message

Represents a single chat message exchanged between the user and the AI assistant.

| Field | Type | Description |
|-------|------|-------------|
| id | string | Unique message identifier (UUID from backend) |
| conversation_id | string | ID of the parent conversation |
| role | "user" \| "assistant" | Who sent the message |
| content | string | Message text body |
| created_at | string (ISO 8601) | When the message was created |

**Validation Rules**:
- `content` MUST NOT be empty or whitespace-only (enforced before API call)
- `content` MUST NOT exceed 2000 characters
- `role` MUST be either "user" or "assistant"

### Conversation

Represents a chat session between a user and the AI.

| Field | Type | Description |
|-------|------|-------------|
| id | string | Unique conversation identifier (UUID from backend) |
| user_id | string | Owner of the conversation |
| created_at | string (ISO 8601) | When the conversation started |
| updated_at | string (ISO 8601) | Last activity timestamp |

**State Transitions**:
- New → Active (first message sent, conversation_id returned from API)
- Active → Active (subsequent messages within same session)

### ChatRequest

Request body sent to the Chat API.

| Field | Type | Description |
|-------|------|-------------|
| conversation_id | string \| null | Existing conversation ID, or null for new conversation |
| message | string | User's message text |

### ChatResponse

Response body returned from the Chat API.

| Field | Type | Description |
|-------|------|-------------|
| conversation_id | string | Conversation ID (new or existing) |
| response | string | AI assistant's response text |

## Relationships

```
User (1) ──── (*) Conversation (1) ──── (*) Message
```

- A User has zero or many Conversations (frontend shows one active conversation).
- A Conversation has one or many Messages.
- Each Message belongs to exactly one Conversation.

## Frontend State Shape

```typescript
interface ChatState {
  conversationId: string | null;     // null until first API response
  messages: Message[];               // ordered by created_at ascending
  isLoading: boolean;                // true while waiting for AI response
  error: string | null;              // current error message
}
```

## Notes

- The frontend does NOT persist messages locally; all persistence is via the backend API.
- ChatKit manages its own internal state for the active session; these types are used for REST API calls outside ChatKit's scope (e.g., loading history).
- The `user_id` is derived from the Better Auth session, never stored in frontend state directly.
