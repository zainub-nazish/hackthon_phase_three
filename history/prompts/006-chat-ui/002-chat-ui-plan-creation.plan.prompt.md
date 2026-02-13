---
id: 002
title: Chat UI Plan Creation
stage: plan
date: 2026-02-08
surface: agent
model: claude-opus-4-6
feature: 006-chat-ui
branch: 006-chat-ui
user: system
command: /sp.plan
labels: ["plan", "chat-ui", "frontend", "chatkit", "architecture"]
links:
  spec: specs/006-chat-ui/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/006-chat-ui/plan.md
  - specs/006-chat-ui/research.md
  - specs/006-chat-ui/data-model.md
  - specs/006-chat-ui/contracts/chat-api.md
  - specs/006-chat-ui/quickstart.md
tests:
  - null
---

## Prompt

Plan Generation Prompt — Spec-4 Chat UI

Generate a detailed implementation plan for the Chat UI frontend feature. The UI integrates with a backend Chat API and displays AI responses using OpenAI ChatKit. Key requirements include chat layout, message rendering, send message flow with conversation_id support, and integration with Better Auth session.

## Response snapshot

Generated complete implementation plan for 006-chat-ui with 5 design artifacts:

1. **plan.md**: Full implementation plan with technical context (TypeScript 5.7, React 18.3, Next.js 16.1, @openai/chatkit-react), constitution check (all 8 gates PASS), project structure (6 new files, 1 modified), and 5 key design decisions.

2. **research.md**: 6 research items resolved:
   - R1: ChatKit Full Proxy approach (custom backend, not direct OpenAI)
   - R2: ChatKit Python SDK for backend integration
   - R3: `/chat` route under existing `(dashboard)` group
   - R4: ChatKit dark theme with CSS variables mapped to Tailwind
   - R5: ChatKit handles its own fetch; REST for history loading
   - R6: Single dependency `@openai/chatkit-react`

3. **data-model.md**: Frontend types — Message, Conversation, ChatRequest, ChatResponse, ChatState.

4. **contracts/chat-api.md**: 4 endpoints documented:
   - POST /api/{user_id}/chat (send message)
   - GET /api/{user_id}/conversations/{id}/messages (load history)
   - GET /api/{user_id}/conversations (get recent conversation)
   - POST /chatkit (ChatKit proxy, internal)

5. **quickstart.md**: Setup guide with 5 verification steps (page load, send/receive, persistence, error handling, mobile).

## Outcome

- ✅ Impact: Complete implementation plan with all Phase 0 and Phase 1 artifacts
- 🧪 Tests: N/A (planning document)
- 📁 Files: plan.md, research.md, data-model.md, contracts/chat-api.md, quickstart.md
- 🔁 Next prompts: /sp.tasks to generate implementation tasks
- 🧠 Reflection: ChatKit's drop-in component approach significantly simplifies the plan — instead of building 5+ custom components, the ChatKit component handles message list, input, typing indicators, and scroll management internally.

## Evaluation notes (flywheel)

- Failure modes observed: Constitution file was reverted to template during session; used knowledge from previous read instead.
- Graders run and results (PASS/FAIL): Constitution Check PASS (all 8 gates)
- Prompt variant (if applicable): Standard plan generation with parallel research agents
- Next experiment (smallest change to try): Validate ChatKit npm package installation during /sp.tasks setup phase
