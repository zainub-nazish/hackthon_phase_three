---
id: 002
title: Todo AI Chatbot System Plan
stage: plan
date: 2026-02-21
surface: agent
model: claude-sonnet-4-6
feature: 012-todo-ai-chatbot
branch: 012-todo-ai-chatbot
user: danish
command: /sp.plan
labels: ["plan","ai-chatbot","mcp","openai","fastapi","architecture"]
links:
  spec: specs/012-todo-ai-chatbot/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/012-todo-ai-chatbot/plan.md
  - specs/012-todo-ai-chatbot/research.md
  - specs/012-todo-ai-chatbot/data-model.md
  - specs/012-todo-ai-chatbot/quickstart.md
  - specs/012-todo-ai-chatbot/contracts/chat-api.yaml
tests:
  - none (plan stage)
---

## Prompt

/sp.plan (no additional arguments — operates on current branch 012-todo-ai-chatbot)

## Response snapshot

Generated full planning artifacts for 012-todo-ai-chatbot:

**Phase 0 — research.md**: 8 architecture decisions resolved:
1. Agentic loop: OpenAI Agents SDK (main) / GPT-4o direct dispatch (HF Space)
2. MCP tools: FastMCP @server.tool() with per-tool DB sessions, stdio transport
3. UUID PKs (not int) — prevents enumeration attacks
4. 20-message context window (not spec's 10) — covers 10 full exchanges
5. ToolCall persistence for audit trail
6. Better Auth JWT via verify_user_owns_resource on all endpoints
7. HTTP 502 for model errors; friendly messages for tool errors
8. Dual deployment split (main backend vs HF Space)

**Phase 1 — data-model.md**: 4 entities (Task, Conversation, Message, ToolCall) with full DDL, validation rules, MCP tool signatures.

**Phase 1 — contracts/chat-api.yaml**: OpenAPI 3.1 spec covering POST /chat, GET /conversations, GET /messages with all request/response schemas.

**Phase 1 — quickstart.md**: Local dev setup, test commands, cURL examples, HF Space deployment notes.

**plan.md**: Full implementation plan with technical context, constitution check (all gates pass), architecture decisions AD-1 through AD-5, phase status, risk register.

## Outcome

- ✅ Impact: All Phase 0 and Phase 1 artifacts complete. Plan is ready for /sp.tasks.
- 🧪 Tests: none (plan stage)
- 📁 Files: plan.md, research.md, data-model.md, quickstart.md, contracts/chat-api.yaml
- 🔁 Next prompts: /sp.tasks — generate implementation task list
- 🧠 Reflection: Core implementation already exists in backend/; plan captured existing architecture accurately. Key divergence from spec: UUID PKs (not int), owner_id (not user_id), 20-message context (not 10).

## Evaluation notes (flywheel)

- Failure modes observed: setup-plan.ps1 script errored on extra positional arg but still created branch/spec correctly
- Graders run and results (PASS/FAIL): constitution check all-pass
- Prompt variant (if applicable): none
- Next experiment (smallest change to try): /sp.tasks focused on test coverage gaps and HF Space alignment
