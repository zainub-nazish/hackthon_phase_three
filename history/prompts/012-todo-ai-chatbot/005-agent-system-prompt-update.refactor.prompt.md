---
id: "005"
title: Agent System Prompt Update
stage: refactor
date: 2026-02-21
surface: agent
model: claude-sonnet-4-6
feature: 012-todo-ai-chatbot
branch: 012-todo-ai-chatbot
user: zainub-nazish
command: prompt engineering (manual)
labels: ["prompt-engineering","ai-agent","system-prompt"]
links:
  spec: specs/012-todo-ai-chatbot/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - backend/services/ai_agent.py
  - huggies_face_three/phase_three_huggies/backend/services/ai_agent.py
tests:
  - "none (prompt-only change)"
---

## Prompt

Prompt Engineering: Apne Agent ko system prompt mein batayein ke 'You are a Todo AI. Use the provided MCP tools for every action.'

## Response snapshot

Updated `SYSTEM_PROMPT` in both `backend/services/ai_agent.py` and
`huggies_face_three/.../ai_agent.py` to prepend:

```
You are a Todo AI. Use the provided MCP tools for every action.
```

Committed as `feat: update agent system prompt — Todo AI identity` and
merged into `003-frontend-app` → Vercel deploy triggered.

## Outcome

- ✅ Impact: Agent now has a clear identity ("Todo AI") and explicit tool-use instruction as the first line of its system prompt
- 🧪 Tests: No test changes needed — stub agent bypasses the system prompt in tests
- 📁 Files: backend/services/ai_agent.py (main), huggies_face_three backend/services/ai_agent.py (HF Space)
- 🔁 Next prompts: T048 E2E quickstart validation, T019/T020/T025/T029/T033 (deferred — need live OpenAI key)
- 🧠 Reflection: Small, focused prompt-engineering change. Prepending identity + tool directive as line 1 gives the model the clearest possible framing before capability/rule details.

## Evaluation notes (flywheel)

- Failure modes observed: none
- Graders run and results (PASS/FAIL): n/a
- Prompt variant (if applicable): n/a
- Next experiment (smallest change to try): Add "Do not respond to messages unrelated to task management." to RULES section if off-topic responses observed in production
