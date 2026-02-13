---
id: 002
title: Chat API Implementation Plan
stage: plan
date: 2026-02-09
surface: agent
model: claude-opus-4-6
feature: 007-chat-api
branch: 007-chat-api
user: architext
command: /sp.plan
labels: ["plan", "chat-api", "backend", "architecture"]
links:
  spec: specs/007-chat-api/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/007-chat-api/plan.md
  - specs/007-chat-api/research.md
  - specs/007-chat-api/data-model.md
  - specs/007-chat-api/quickstart.md
  - specs/007-chat-api/contracts/chat-api.yaml
tests:
  - none (planning phase)
---

## Prompt

# Plan Generation Prompt — Spec-5 Chat API

You are an expert backend architect working in a Spec-Driven Development workflow using the Agentic Dev Stack.

Your task is to generate a detailed implementation plan for the Chat API defined in Spec-5.

Do NOT write code.
Focus only on planning, architecture, and task breakdown.

---

# Spec Reference

Spec-5 — Chat API & Conversation Persistence

---

# Objective

Build a backend Chat API endpoint that:

- Receives user messages
- Saves conversations
- Stores chat history
- Invokes AI agent
- Returns assistant responses
- Maintains context via database
- Operates in a stateless architecture

---

# Core Endpoint

## POST /api/chat

This endpoint handles the complete conversational lifecycle.

---

# Request Schema

```json
{
  "conversation_id": "integer (optional)",
  "message": "string (required)"
}
```

## Response snapshot

Generated a comprehensive implementation plan for the Chat API (007-chat-api) with the following artifacts:

1. **plan.md** — Full implementation plan with 6 phases: Database Models → Pydantic Schemas → AI Agent Service → Chat Route Endpoints → Error Handling → Testing. Key design decisions: AI agent as service abstraction (stub now, real in Spec-6), message persistence before AI invocation, JSON text for tool call storage.

2. **research.md** — Resolved 8 technical unknowns: AI agent invocation pattern (service abstraction), frontend contract compatibility (matches chat-client.ts exactly), database model design (3 new tables), conversation history context (20 messages), auth/isolation (reuse verify_user_owns_resource), error handling (persist user message first, 502 on AI failure), tool call persistence (linked to assistant messages), one-conversation constraint.

3. **data-model.md** — Three new entities: Conversation (UUID PK, owner_id, timestamps), Message (UUID PK, FK to conversation, role, content), ToolCall (UUID PK, FK to message, tool_name, parameters/result as JSON text, status). All follow existing Task model patterns.

4. **contracts/chat-api.yaml** — OpenAPI 3.1 specification defining all 3 endpoints with request/response schemas matching the frontend types exactly.

5. **quickstart.md** — Setup guide with prerequisites, new file listing, and curl commands for verification.

## Outcome

- ✅ Impact: Full architectural plan for Chat API with all unknowns resolved
- 🧪 Tests: None (planning phase — test plan defined in Phase 6)
- 📁 Files: 5 artifacts created in specs/007-chat-api/
- 🔁 Next prompts: Run `/sp.tasks` to generate tasks.md from this plan
- 🧠 Reflection: Frontend code (chat-client.ts) was the authoritative source for API URLs — the contract doc had a discrepancy (missing /v1/ prefix). Always verify against actual frontend code.

## Evaluation notes (flywheel)

- Failure modes observed: Contract doc URL mismatch (no /v1/ prefix) — resolved by using frontend code as source of truth
- Graders run and results (PASS/FAIL): N/A (planning phase)
- Prompt variant (if applicable): Standard /sp.plan with spec-5 reference
- Next experiment (smallest change to try): Generate tasks from this plan with /sp.tasks
