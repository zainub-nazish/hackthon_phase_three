---
id: "006"
title: Add MCP Tools Contract and Commit PHR 005
stage: green
date: 2026-02-21
surface: agent
model: claude-sonnet-4-6
feature: 012-todo-ai-chatbot
branch: 012-todo-ai-chatbot
user: zainub-nazish
command: implement plan — add missing spec-kit docs & commit process artifacts
labels: ["docs","contracts","mcp-tools","phr","sdd-process"]
links:
  spec: specs/012-todo-ai-chatbot/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/012-todo-ai-chatbot/contracts/mcp-tools.yaml
  - history/prompts/012-todo-ai-chatbot/005-agent-system-prompt-update.refactor.prompt.md
tests:
  - "none (docs-only change)"
---

## Prompt

Implement the following plan:

# Plan: Add Missing Spec-Kit Docs & Commit Process Artifacts

Judges need to see the full SDD process — not just the finished code. Two gaps found after audit:
1. `specs/012-todo-ai-chatbot/contracts/mcp-tools.yaml` — present in 011 but missing in 012
2. PHR `005-agent-system-prompt-update.refactor.prompt.md` — created locally, not committed

Changes:
1. Create `specs/012-todo-ai-chatbot/contracts/mcp-tools.yaml` updated for 012 (UUID IDs, list_tasks returns object, error_return on every tool)
2. Commit PHR 005
3. Commit & push both files on `012-todo-ai-chatbot`, merge into `003-frontend-app`, push

## Response snapshot

Created `specs/012-todo-ai-chatbot/contracts/mcp-tools.yaml` with 012-specific changes:
- All `id` / `task_id` fields: `type: string, format: uuid` (not `integer` as in 011)
- `list_tasks` returns `{ tasks: [...], count: int }` object (not bare array)
- `error_return` block on every tool with `{ is_error: boolean, error: string }`

Staged and committed both files in a single commit (`94336ae`) on `012-todo-ai-chatbot`,
then fast-forward merged into `003-frontend-app` and pushed both branches.

## Outcome

- ✅ Impact: Both missing artifacts now visible on GitHub under `003-frontend-app` (deploy branch) — SDD process evidence complete for judges
- 🧪 Tests: No tests needed — docs-only change
- 📁 Files: specs/012-todo-ai-chatbot/contracts/mcp-tools.yaml (new), history/prompts/012-todo-ai-chatbot/005 (committed)
- 🔁 Next prompts: PHR ID 007 if further docs needed; otherwise feature is fully documented
- 🧠 Reflection: Fast-forward merge worked cleanly — both branches share commit 94336ae. UUID type correction from 011→012 is a meaningful contract update that accurately reflects the actual implementation.

## Evaluation notes (flywheel)

- Failure modes observed: none
- Graders run and results (PASS/FAIL): n/a
- Prompt variant (if applicable): n/a
- Next experiment (smallest change to try): n/a
