# Quickstart: AI Todo Agent

**Feature**: 008-ai-agent | **Date**: 2026-02-10

## Prerequisites

1. Backend running (`uvicorn backend.main:app --reload`)
2. `ANTHROPIC_API_KEY` set in `backend/.env`
3. Database configured (`DATABASE_URL` in `backend/.env`)
4. Authenticated session token (from Better Auth login)

## Setup

Add to `backend/.env`:
```
ANTHROPIC_API_KEY=sk-ant-...your-key-here
ANTHROPIC_MODEL=claude-haiku-4-5-20251001
```

## Verification Steps

### 1. Create a Task via Natural Language

```bash
curl -X POST http://localhost:8000/api/v1/users/{user_id}/chat \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{"conversation_id": null, "message": "Add a task to buy groceries"}'
```

**Expected**: Response with `conversation_id` and `response` containing a confirmation like "Task 'Buy groceries' added".

### 2. List Tasks via Natural Language

```bash
curl -X POST http://localhost:8000/api/v1/users/{user_id}/chat \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{"conversation_id": "{conv_id}", "message": "Show my tasks"}'
```

**Expected**: Response listing the user's tasks including "Buy groceries".

### 3. Complete a Task via Natural Language

```bash
curl -X POST http://localhost:8000/api/v1/users/{user_id}/chat \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{"conversation_id": "{conv_id}", "message": "Mark buy groceries as done"}'
```

**Expected**: Response confirming the task was completed.

### 4. Delete a Task via Natural Language

```bash
curl -X POST http://localhost:8000/api/v1/users/{user_id}/chat \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{"conversation_id": "{conv_id}", "message": "Delete the groceries task"}'
```

**Expected**: Response confirming the task was deleted.

### 5. Test Error Handling

```bash
curl -X POST http://localhost:8000/api/v1/users/{user_id}/chat \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{"conversation_id": "{conv_id}", "message": "Delete a task called nonexistent thing"}'
```

**Expected**: Friendly error message that the task couldn't be found.

### 6. Test General Conversation

```bash
curl -X POST http://localhost:8000/api/v1/users/{user_id}/chat \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{"conversation_id": "{conv_id}", "message": "What can you help me with?"}'
```

**Expected**: Conversational response describing capabilities without invoking any tools.

## Testing (Automated)

```bash
# Run all agent tests
python -m pytest backend/tests/test_ai_agent.py -v

# Run integration tests (requires ANTHROPIC_API_KEY)
python -m pytest backend/tests/test_ai_agent.py -v -k "integration" --runslow
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| 502 "AI service unavailable" | Check `ANTHROPIC_API_KEY` is set correctly |
| Agent returns stub response | Verify the new agent implementation is loaded (not the stub) |
| Task not found by name | The agent should call `list_tasks` first — check system prompt |
| Slow responses | Try `claude-haiku-4-5-20251001` model (fastest) |
