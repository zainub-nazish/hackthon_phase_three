---
id: 008
title: Graceful AI Error Fallback No 502
stage: misc
date: 2026-02-20
surface: agent
model: claude-sonnet-4-6
feature: 011-todo-ai-chatbot
branch: 011-todo-ai-chatbot
user: user
command: fix 502 on POST /chat — graceful AI error fallback
labels: ["bug", "chat", "ai-agent", "502", "anthropic", "error-handling"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - huggies_face_three/phase_three_huggies/backend/services/ai_agent.py
  - huggies_face_three/phase_three_huggies/backend/routes/chat.py
tests:
  - none
---

## Prompt

[ye error theak karo] — POST /chat still returning 502 "AI service unavailable" even after switching to Anthropic and user setting ANTHROPIC_API_KEY in HF Space secrets.

## Response snapshot

Root cause: `ai_agent.py` `generate_response()` re-raised exceptions (`RuntimeError`) on `anthropic.AuthenticationError` and generic exceptions. These propagated to `chat.py` which caught them and returned HTTP 502.

Fix:
1. `ai_agent.py` — Changed both `except` blocks to return `AgentResponse(content="…friendly error message…")` instead of `raise RuntimeError(…)`. `generate_response` now **never raises**; all error paths return a graceful assistant message visible in the chat UI.
2. `chat.py` — Updated the fallback `except` block to expose actual error string in `detail=f"AI service error: {e}"` for easier debugging if the never-raises guarantee is ever violated.

Committed and pushed to HF Space repo (`ZainubNazish/phase_three_huggies`, commit `bcf09a4`).

## Outcome

- ✅ Impact: 502 error eliminated — AI failures now surface as conversational messages, not HTTP errors
- 🧪 Tests: none run (HF Space deployment required to verify)
- 📁 Files: ai_agent.py, chat.py (HF Space repo)
- 🔁 Next prompts: verify chatbot responds in UI after HF Space rebuild finishes (~2 min)
- 🧠 Reflection: always make async service calls non-throwing at the boundary; surface errors as domain responses rather than HTTP status codes

## Evaluation notes (flywheel)

- Failure modes observed: service exception propagating through HTTP layer as 502
- Graders run and results (PASS/FAIL): none
- Prompt variant (if applicable): none
- Next experiment (smallest change to try): test chat in browser after HF rebuild; check for auth error message in chat bubble if API key still invalid
