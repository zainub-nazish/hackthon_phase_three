---
id: 002
title: Todo AI Chatbot Implementation Plan
stage: plan
date: 2026-02-14
surface: agent
model: claude-opus-4-6
feature: 011-todo-ai-chatbot
branch: 011-todo-ai-chatbot
user: danish
command: /sp.plan
labels: ["plan", "architecture", "openai-agents-sdk", "mcp", "migration"]
links:
  spec: specs/011-todo-ai-chatbot/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/011-todo-ai-chatbot/plan.md
  - specs/011-todo-ai-chatbot/research.md
  - specs/011-todo-ai-chatbot/data-model.md
  - specs/011-todo-ai-chatbot/quickstart.md
  - specs/011-todo-ai-chatbot/contracts/chat-api.yaml
  - specs/011-todo-ai-chatbot/contracts/mcp-tools.yaml
tests:
  - Constitution check PASS (template state, no violations)
  - Post-design re-check PASS
---

## Prompt

# Role: Senior Agentic Developer
# Task: Create an Implementation Plan (plan.md) based on Specifications

I have provided the technical specification in `/specs/todo-ai-chatbot.md`. Your task is to generate a comprehensive `plan.md` file in the root directory that outlines the execution of this project.

The plan must strictly follow the "Agentic Dev Stack" workflow (Spec -> Plan -> Tasks -> Implementation).

### Instructions for the Plan:

1. **Architecture Alignment**: The plan must ensure the backend is 100% stateless.
2. **Phase Breakdown**:
    - **Phase 1: Foundation**: Project structure, Environment Variables (.env), and Neon DB connection using SQLModel (Async).
    - **Phase 2: Database Migration**: Implementation of Task, Conversation, and Message models.
    - **Phase 3: MCP Server**: Building the Official MCP server with the 5 required tools (add, list, complete, delete, update).
    - **Phase 4: Agent Logic**: Integration of OpenAI Agents SDK and conversation history retrieval logic.
    - **Phase 5: API Layer**: Creating the `/api/{user_id}/chat` endpoint.
    - **Phase 6: Frontend**: ChatKit integration and Domain Allowlist configuration.

3. **Tool Chaining**: The plan must include a strategy for multi-step reasoning (e.g., searching for a task by name before deleting it by ID).

4. **Definition of Done (DoD)**: Every phase must end with a validation step to ensure the requirements are met.

### Execution Command:
"Generate the `plan.md` file now. After generating the plan, do NOT start coding yet. Wait for my approval of the plan."

## Response snapshot

Created comprehensive 6-phase implementation plan at `specs/011-todo-ai-chatbot/plan.md`. Key finding: most infrastructure already exists (models, MCP tools, routes, ChatKit frontend). The primary change is migrating `ai_agent.py` from Anthropic Claude to OpenAI Agents SDK with native MCP support. Generated 6 artifacts: plan.md, research.md, data-model.md, quickstart.md, chat-api.yaml, mcp-tools.yaml. Plan includes tool chaining strategy (system prompt instructs agent to list_tasks before delete/complete by name) and DoD checkboxes for every phase.

## Outcome

- Impact: Complete architectural plan for Anthropic → OpenAI Agents SDK migration with 6 phases, each with DoD
- Tests: Constitution gate PASS, post-design re-check PASS
- Files: plan.md, research.md, data-model.md, quickstart.md, contracts/chat-api.yaml, contracts/mcp-tools.yaml
- Next prompts: /sp.tasks to generate task breakdown, then /sp.implement after approval
- Reflection: Existing codebase already has 90% of infrastructure — plan correctly scopes this as a targeted migration, not a greenfield build

## Evaluation notes (flywheel)

- Failure modes observed: None
- Graders run and results (PASS/FAIL): Constitution check PASS, structure validation PASS
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): N/A
