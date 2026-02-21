# Quickstart: Todo AI Chatbot (012-todo-ai-chatbot)

**Date**: 2026-02-21 | **Branch**: `012-todo-ai-chatbot`

---

## Prerequisites

- Python 3.11+
- Neon PostgreSQL database (connection string)
- OpenAI API key (`sk-proj-...` or `sk-...`) **or** Anthropic API key (`sk-ant-...`)
- Node.js 18+ (for frontend)

---

## Backend Setup

```bash
# 1. Create and activate virtual environment
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env:
#   DATABASE_URL=postgresql+asyncpg://user:pass@host/dbname?ssl=require
#   BETTER_AUTH_SECRET=your-secret
#   OPENAI_API_KEY=sk-...          # for main backend (OpenAI Agents SDK)
#   # OR ANTHROPIC_API_KEY=sk-ant-... # for HF Space deployment

# 4. Start the server
uvicorn backend.main:app --reload --port 8000
```

API docs (debug mode only): `http://localhost:8000/docs`
Health check: `http://localhost:8000/health`

---

## Running Tests

```bash
cd /path/to/phase_three
pytest backend/tests/ -v

# Run only chat tests
pytest backend/tests/test_chat.py -v

# Run with coverage
pytest backend/tests/ --cov=backend --cov-report=term-missing
```

Tests use `aiosqlite` (in-memory SQLite) — no real database needed.

---

## Frontend Setup

```bash
cd frontend
npm install
cp .env.local.example .env.local
# Edit .env.local:
#   NEXT_PUBLIC_API_URL=http://localhost:8000   # or HF Space URL

npm run dev   # http://localhost:3000
```

---

## Sending a Chat Message (cURL)

```bash
# 1. Get a Bearer token (from login)
TOKEN="your-jwt-token"
USER_ID="your-user-id"
BASE="http://localhost:8000"

# 2. Start a new conversation
curl -X POST "$BASE/api/v1/users/$USER_ID/chat" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "Add buy groceries to my list"}'

# Response:
# {
#   "conversation_id": "a5308f26-...",
#   "response": "Done! I've added 'buy groceries' to your task list.",
#   "tool_calls": [{"tool_name": "add_task", ...}]
# }

# 3. Continue the conversation
curl -X POST "$BASE/api/v1/users/$USER_ID/chat" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "What tasks do I have?", "conversation_id": "a5308f26-..."}'

# 4. Mark a task complete
curl -X POST "$BASE/api/v1/users/$USER_ID/chat" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "I am done with groceries", "conversation_id": "a5308f26-..."}'
```

---

## Key Source Files

| File | Purpose |
|------|---------|
| `backend/routes/chat.py` | Chat endpoints (POST /chat, GET /conversations, GET /messages) |
| `backend/services/ai_agent.py` | Agentic loop — sends messages to model, executes tools |
| `backend/services/mcp_tools.py` | MCP tool handlers (add/list/complete/delete/update task) |
| `backend/models/database.py` | SQLModel table definitions (Task, Conversation, Message, ToolCall) |
| `backend/models/schemas.py` | Pydantic request/response schemas |
| `backend/auth/dependencies.py` | `verify_user_owns_resource` — JWT auth + user isolation |
| `backend/tests/test_chat.py` | Integration tests for the chat endpoint |

---

## HF Space Deployment

The HF Space uses a simplified AI backend without MCP subprocess:

```
huggies_face_three/phase_three_huggies/
├── main.py              # FastAPI app entry point
├── config.py            # Settings (OPENAI_API_KEY or ANTHROPIC_API_KEY)
├── backend/
│   ├── config.py        # Same settings, reads backend/.env
│   ├── services/
│   │   ├── ai_agent.py  # GPT-4o with direct function dispatch (no MCP subprocess)
│   │   └── mcp_tools.py # Same tool functions, called directly
│   └── routes/chat.py   # Same API contract
```

Set secrets in HF Space → Settings → Variables and secrets:
- `OPENAI_API_KEY` (must start with `sk-`)
- `DATABASE_URL`
- `BETTER_AUTH_SECRET`
- `BETTER_AUTH_URL`
