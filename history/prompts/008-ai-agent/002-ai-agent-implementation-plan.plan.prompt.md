---
id: 002
title: AI Agent Implementation Plan
stage: plan
date: 2026-02-10
surface: agent
model: claude-opus-4-6
feature: 008-ai-agent
branch: 008-ai-agent
user: architext
command: /sp.plan
labels: ["plan", "ai-agent", "anthropic-sdk", "tool-use", "architecture"]
links:
  spec: specs/008-ai-agent/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/008-ai-agent/plan.md
  - specs/008-ai-agent/research.md
  - specs/008-ai-agent/data-model.md
  - specs/008-ai-agent/contracts/tool-definitions.yaml
  - specs/008-ai-agent/quickstart.md
tests:
  - null
---

## Prompt

/sp.plan — Plan the AI Agent implementation for 008-ai-agent. Define agent architecture (agent instance + runner + tool registry), intent detection logic, tool selection & invocation flow, parameter resolution & multi-step actions, confirmation message templates, context handling & pronoun resolution, error handling strategy, testing & validation plan. Break work into sequential implementation phases. Do NOT generate code.

## Response snapshot

Created implementation plan with 5 phases and 8 research decisions. Architecture: Anthropic Python SDK with manual agent loop, 5 task management tools with direct DB operations, Claude Haiku 4.5 as default model (configurable).

**Artifacts created:**
- `plan.md` — 5 implementation phases, 6 design decisions, 4 risks
- `research.md` — 8 research items (SDK, architecture, tools, system prompt, config, errors)
- `data-model.md` — Tool definitions, data flow, config additions (no new DB tables)
- `contracts/tool-definitions.yaml` — Full JSON Schema tool definitions + system prompt
- `quickstart.md` — Setup and verification guide with curl examples

**Key decisions:**
- D-001: Manual agent loop over Tool Runner for tool call persistence control
- D-002: Direct DB queries over HTTP calls for tool execution
- D-003: Haiku 4.5 default, configurable via ANTHROPIC_MODEL env var
- D-004: System prompt as inline constant (single agent, simplicity)
- D-005: Error handling via tool_result is_error flag (Claude explains errors)
- D-006: Graceful stub fallback when API key missing

## Outcome

- ✅ Impact: Complete implementation plan for AI agent with tool-use task management
- 🧪 Tests: N/A (plan phase)
- 📁 Files: 5 created (plan, research, data-model, contracts, quickstart)
- 🔁 Next prompts: /sp.tasks to generate implementation task breakdown
- 🧠 Reflection: Manual agent loop is the right call — Tool Runner abstracts away tool call details needed for persistence. Direct DB queries avoid auth complexity.

## Evaluation notes (flywheel)

- Failure modes observed: None
- Graders run and results (PASS/FAIL): Constitution check PASS (all 5 items)
- Prompt variant (if applicable): null
- Next experiment (smallest change to try): null
