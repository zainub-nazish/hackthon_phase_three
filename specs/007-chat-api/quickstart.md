# Quickstart: Chat API & Conversation Persistence

**Feature**: 007-chat-api | **Date**: 2026-02-09

## Prerequisites

- Python 3.11+
- Neon PostgreSQL database (or local PostgreSQL for dev)
- Backend dependencies installed (`pip install -r backend/requirements.txt`)
- `.env` with `DATABASE_URL` configured
- Better Auth session tokens (from the running frontend)

## New Files to Create

```
backend/
├── models/
│   └── database.py       # ADD: Conversation, Message, ToolCall models
├── models/
│   └── schemas.py        # ADD: Chat request/response Pydantic schemas
├── routes/
│   └── chat.py           # NEW: Chat route module (3 endpoints)
├── services/
│   └── ai_agent.py       # NEW: AI agent service interface + stub
└── main.py               # MODIFY: Register chat router
```

## New Dependencies

```
# Add to requirements.txt (if not already present)
# No new dependencies required — all tools already in place:
# - sqlmodel (ORM)
# - asyncpg (PostgreSQL driver)
# - fastapi (web framework)
```

## Quick Verification

### 1. Run Tests
```bash
cd backend
python -m pytest tests/ -v
```

### 2. Start Server
```bash
uvicorn backend.main:app --reload
```

### 3. Test Endpoints (with valid session token)

**Send a message (new conversation):**
```bash
curl -X POST http://localhost:8000/api/v1/users/{user_id}/chat \
  -H "Authorization: Bearer {session_token}" \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, what can you help me with?"}'
```

**Get recent conversation:**
```bash
curl http://localhost:8000/api/v1/users/{user_id}/conversations \
  -H "Authorization: Bearer {session_token}"
```

**Load message history:**
```bash
curl http://localhost:8000/api/v1/users/{user_id}/conversations/{conv_id}/messages \
  -H "Authorization: Bearer {session_token}"
```

## Architecture Notes

- **AI Agent**: Implemented as a stub service (`AIAgentService`) that returns canned responses. Real AI integration deferred to Spec-6.
- **User Isolation**: All queries filter by `owner_id`. Cross-user access returns 404.
- **Error Handling**: User message persisted before AI call. AI failures return 502 without corrupting conversation state.
- **Testing**: In-memory SQLite with aiosqlite, same as existing Task tests.
