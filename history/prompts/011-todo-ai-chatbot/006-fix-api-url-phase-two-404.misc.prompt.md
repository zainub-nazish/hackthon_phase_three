---
id: 006
title: Fix API URL Phase Two 404 Errors
stage: misc
date: 2026-02-19
surface: agent
model: claude-sonnet-4-6
feature: 011-todo-ai-chatbot
branch: 011-todo-ai-chatbot
user: danish
command: chat
labels: ["bugfix","env","vercel","api-url"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - frontend/.env.local.example
tests:
  - none
---

## Prompt

Browser console errors showing:
```
[API] GET https://zainubnazish-phase-two.hf.space/api/v1/users/{id}/tasks (token attached)
[API] GET https://zainubnazish-phase-two.hf.space/api/v1/users/{id}/conversations (token attached)
zainubnazish-phase-two.hf.space/api/v1/users/{id}/conversations:1 Failed to load resource: 404
[API] POST https://zainubnazish-phase-two.hf.space/api/v1/users/{id}/chat (token attached)
zainubnazish-phase-two.hf.space/api/v1/users/{id}/chat:1 Failed to load resource: 404
[Chat] sendMessage error: ApiError: Not Found
[Chat] ApiError status: 404 data: Object
```

## Response snapshot

Root cause: Vercel has `NEXT_PUBLIC_API_URL=https://zainubnazish-phase-two.hf.space` set as an environment variable. This overrides the phase-three fallback in `api-client.ts`. The `/conversations` and `/chat` endpoints don't exist on the phase-two backend — they live on phase-three.

Fix applied:
- Updated `frontend/.env.local.example` to use the correct phase-three URL for `NEXT_PUBLIC_API_URL`
- Removed duplicate/conflicting `NEXT_PUBLIC_API_URL` and `NEXT_PUBLIC_BACKEND_URL` lines
- Updated Vercel deployment instructions in the example file to reference phase-three URL

**User action required:** Update Vercel Environment Variable `NEXT_PUBLIC_API_URL` from `https://zainubnazish-phase-two.hf.space` to `https://zainubnazish-phase-three-huggies.hf.space`, then redeploy.

## Outcome

- ✅ Impact: Corrected the example env file so future deploys use the right backend; documented required Vercel action
- 🧪 Tests: none run (env config change)
- 📁 Files: frontend/.env.local.example
- 🔁 Next prompts: Update Vercel env var and redeploy to fix production 404s
- 🧠 Reflection: The old phase-two URL was hardcoded in both `.env.local.example` and Vercel deployment instructions — both needed to be corrected together

## Evaluation notes (flywheel)

- Failure modes observed: Wrong HF Space URL persisted in Vercel env vars after backend migration to phase-three
- Graders run and results (PASS/FAIL): none
- Prompt variant (if applicable): none
- Next experiment (smallest change to try): Update Vercel env var and confirm 200 responses on /conversations and /chat
