---
id: 009
title: Fix HF Space Anthropic API Key Config Mismatch
stage: misc
date: 2026-02-20
surface: agent
model: claude-sonnet-4-6
feature: 011-todo-ai-chatbot
branch: 003-frontend-app
user: danish
command: chat
labels: ["bugfix","config","hf-space","anthropic"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - huggies_face_three/phase_three_huggies/config.py
  - huggies_face_three/phase_three_huggies/backend/.env.example
tests:
  - none
---

## Prompt

I'm unable to connect to the AI service right now (authentication error). Please check the ANTHROPIC_API_KEY in the HF Space secrets. ma ne set kar dia hai

## Response snapshot

Root cause: `config.py` in the HF Space defined `openai_api_key` (alias `OPENAI_API_KEY`), but `ai_agent.py` reads `settings.anthropic_api_key` — that attribute didn't exist, causing an `AttributeError` that surfaced as the auth error message.

Fix: Renamed the field in `huggies_face_three/phase_three_huggies/config.py` from `openai_api_key / OPENAI_API_KEY` to `anthropic_api_key / ANTHROPIC_API_KEY`. Also updated `.env.example` to document the correct key name.

## Outcome

- ✅ Impact: `settings.anthropic_api_key` now correctly reads `ANTHROPIC_API_KEY` from HF Space secrets — AI chat will work once deployed.
- 🧪 Tests: No tests changed; existing test stubs bypass the key check.
- 📁 Files: 2 files changed (config.py, .env.example)
- 🔁 Next prompts: Redeploy HF Space and verify chat responds with Claude.
- 🧠 Reflection: The HF Space config.py was an old copy that still had the OpenAI field from an earlier migration; the ai_agent.py had already been updated to Anthropic but the config wasn't synced.

## Evaluation notes (flywheel)

- Failure modes observed: Config field name mismatch between ai_agent.py and config.py after provider migration.
- Graders run and results (PASS/FAIL): none
- Prompt variant (if applicable): none
- Next experiment (smallest change to try): Add a startup config validation that asserts `anthropic_api_key` is set and logs a clear warning on boot.
