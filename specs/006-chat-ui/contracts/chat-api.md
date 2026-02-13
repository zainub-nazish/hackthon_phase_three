# API Contract: Chat API (Frontend Perspective)

**Feature**: 006-chat-ui
**Date**: 2026-02-08
**Note**: This contract describes the API from the frontend's perspective. The backend implementation is defined in Spec-5.

## Endpoints

### POST /api/{user_id}/chat

Send a message and receive an AI response.

**Path Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| user_id | string | Yes | Authenticated user's ID (from Better Auth session) |

**Request Headers**:

| Header | Value | Description |
|--------|-------|-------------|
| Content-Type | application/json | Required |
| Authorization | Bearer {session_token} | Better Auth session token |

**Request Body**:

```json
{
  "conversation_id": "uuid-string-or-null",
  "message": "User's natural language input"
}
```

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| conversation_id | string \| null | No | UUID of existing conversation, or null to create new |
| message | string | Yes | Non-empty, max 2000 characters |

**Success Response** (200 OK):

```json
{
  "conversation_id": "uuid-string",
  "response": "AI assistant's response text"
}
```

| Field | Type | Description |
|-------|------|-------------|
| conversation_id | string | UUID (new if first message, existing otherwise) |
| response | string | AI assistant's natural language response |

**Error Responses**:

| Status | Body | Condition |
|--------|------|-----------|
| 400 | `{"detail": "Message cannot be empty"}` | Empty or whitespace message |
| 401 | `{"detail": "Unauthorized"}` | Missing or invalid session token |
| 404 | `{"detail": "Conversation not found"}` | Invalid conversation_id |
| 422 | `{"detail": [{"loc": [...], "msg": "...", "type": "..."}]}` | Validation error |
| 500 | `{"detail": "Internal server error"}` | Server-side failure |

### GET /api/{user_id}/conversations/{conversation_id}/messages

Load conversation history.

**Path Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| user_id | string | Yes | Authenticated user's ID |
| conversation_id | string | Yes | UUID of the conversation |

**Request Headers**:

| Header | Value | Description |
|--------|-------|-------------|
| Authorization | Bearer {session_token} | Better Auth session token |

**Success Response** (200 OK):

```json
{
  "conversation_id": "uuid-string",
  "messages": [
    {
      "id": "uuid-string",
      "conversation_id": "uuid-string",
      "role": "user",
      "content": "Add task Buy groceries",
      "created_at": "2026-02-08T10:30:00Z"
    },
    {
      "id": "uuid-string",
      "conversation_id": "uuid-string",
      "role": "assistant",
      "content": "Task 'Buy groceries' has been added successfully.",
      "created_at": "2026-02-08T10:30:02Z"
    }
  ]
}
```

**Error Responses**:

| Status | Body | Condition |
|--------|------|-----------|
| 401 | `{"detail": "Unauthorized"}` | Missing or invalid session token |
| 404 | `{"detail": "Conversation not found"}` | Invalid conversation_id or belongs to another user |

### GET /api/{user_id}/conversations

Get the user's most recent conversation (for restoring session).

**Request Headers**:

| Header | Value | Description |
|--------|-------|-------------|
| Authorization | Bearer {session_token} | Better Auth session token |

**Success Response** (200 OK):

```json
{
  "conversation_id": "uuid-string",
  "created_at": "2026-02-08T10:00:00Z",
  "updated_at": "2026-02-08T10:30:00Z"
}
```

**Empty Response** (200 OK — no conversations):

```json
{
  "conversation_id": null
}
```

## ChatKit Proxy Endpoint

### POST /chatkit

ChatKit's internal communication endpoint (managed by ChatKit SDK).

**Note**: This endpoint is used internally by the `<ChatKit />` component. The frontend does not call it directly — ChatKit's fetch handler manages all requests to this URL.

**Request/Response**: Follows the ChatKit protocol specification. Handled by the `ChatKitServer` implementation on the backend.

**Auth**: Session token forwarded by ChatKit via configuration.
