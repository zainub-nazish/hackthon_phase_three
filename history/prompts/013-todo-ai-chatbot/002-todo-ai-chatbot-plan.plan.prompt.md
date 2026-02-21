---
id: "002"
title: Todo AI Chatbot Implementation Plan
stage: plan
date: 2026-02-21
surface: agent
model: claude-sonnet-4-6
feature: 013-todo-ai-chatbot
branch: 013-todo-ai-chatbot
user: zainub-nazish
command: /sp.plan
labels: ["plan","fastapi","neon-db","mcp","openai-agents","chatkit"]
links:
  spec: specs/013-todo-ai-chatbot/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/013-todo-ai-chatbot/plan.md
  - specs/013-todo-ai-chatbot/research.md
  - specs/013-todo-ai-chatbot/data-model.md
  - specs/013-todo-ai-chatbot/quickstart.md
  - specs/013-todo-ai-chatbot/contracts/chat-api.yaml
tests:
  - "none (plan stage)"
---

## Prompt

Setup FastAPI and Neon DB connection.

Implement Official MCP SDK for task tools.

Integrate OpenAI Agents SDK for natural language reasoning.

Connect ChatKit UI with the /api/{user_id}/chat endpoint.

## Response snapshot

Generated all Phase 0 + Phase 1 plan artifacts for `013-todo-ai-chatbot`:

**Phase 0 (Research)** — `research.md`:
8 decisions documented: FastAPI+asyncpg for Neon DB, FastMCP with `@server.tool()` for MCP SDK, OpenAI Agents SDK `Runner.run` with `MCPServerStdio`, Vercel rewrites for ChatKit→backend, UUID PKs, 20-message context window, ToolCall persistence table, 502/conversational error split.

**Phase 1 (Design & Contracts)** — 4 artifacts:
- `plan.md`: technical context, AD-1–AD-5 architecture decisions, constitution check (all pass), risk register, project structure
- `data-model.md`: Task/Conversation/Message/ToolCall entities with field-level constraints, MCP tool signature table, DDL
- `quickstart.md`: backend setup, MCP inspection, test commands, frontend setup, cURL examples, env var reference
- `contracts/chat-api.yaml`: OpenAPI 3.1 for all 3 chat endpoints (`POST /chat`, `GET /conversations`, `GET /messages`)

`update-agent-context.ps1` run — CLAUDE.md updated with language/DB stack.
All 5 files committed as `529261d`.

## Outcome

- ✅ Impact: Full planning documentation for 013 — 913 lines across 5 files; covers all 4 user-specified focus areas
- 🧪 Tests: n/a (plan stage)
- 📁 Files: plan.md, research.md, data-model.md, quickstart.md, contracts/chat-api.yaml
- 🔁 Next prompts: `/sp.tasks` to generate tasks.md with testable implementation tasks
- 🧠 Reflection: 013 plan explicitly decomposes into the 4 user-specified layers (FastAPI+DB, MCP SDK, Agents SDK, ChatKit). Architecture decisions are numbered AD-1–AD-5 for easy reference in tasks.md.

## Evaluation notes (flywheel)

- Failure modes observed: create-new-feature.ps1 positional arg error (branch already created correctly); setup-plan.ps1 succeeded cleanly
- Graders run and results (PASS/FAIL): constitution check — 6/6 PASS
- Prompt variant (if applicable): n/a
- Next experiment (smallest change to try): n/a
