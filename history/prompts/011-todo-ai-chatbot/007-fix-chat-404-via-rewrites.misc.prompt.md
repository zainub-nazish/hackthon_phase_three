---
id: 007
title: Fix Chat 404 via Vercel Rewrites
stage: misc
date: 2026-02-19
surface: agent
model: claude-sonnet-4-6
feature: 011-todo-ai-chatbot
branch: 011-todo-ai-chatbot
user: user
command: debug chat 404 errors
labels: ["bug", "chat", "api", "vercel", "rewrites"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - frontend/lib/api-client.ts
  - frontend/vercel.json
  - frontend/next.config.mjs
tests:
  - none
---

## Prompt

[API] GET https://zainubnazish-phase-two.hf.space/api/v1/users/.../tasks (token attached)
[API] GET https://zainubnazish-phase-two.hf.space/api/v1/users/.../conversations (token attached)
zainubnazish-phase-two.hf.space/api/v1/users/.../conversations: Failed to load resource: 404
[API] POST https://zainubnazish-phase-two.hf.space/api/v1/users/.../chat (token attached)
zainubnazish-phase-two.hf.space/api/v1/users/.../chat: Failed to load resource: 404
[Chat] sendMessage error: ApiError: Not Found — sai karo

## Response snapshot

Root cause: Vercel has `NEXT_PUBLIC_API_URL=https://zainubnazish-phase-two.hf.space` set as an env var. Phase-two backend has no `/chat` or `/conversations` routes. Although `api-client.ts` had phase-three as a fallback, the Vercel env var overrides it.

Fix: Switch to relative URLs + Vercel/Next.js rewrites so the env var is bypassed entirely.

1. `frontend/lib/api-client.ts` — changed `API_URL` from `process.env.NEXT_PUBLIC_API_URL || "phase-three-url"` to `""` (empty string / relative URL)
2. `frontend/vercel.json` — added rewrite: `/api/v1/:path*` → `https://zainubnazish-phase-three-huggies.hf.space/api/v1/:path*` (production)
3. `frontend/next.config.mjs` — added rewrite (dev only): `/api/v1/:path*` → `NEXT_PUBLIC_API_URL || localhost:8000` (local dev)

Now in production, Vercel edge rewrites all `/api/v1/*` traffic to phase-three backend regardless of env vars. In local dev, Next.js rewrites to whatever `NEXT_PUBLIC_API_URL` is set to (defaults to localhost:8000).

## Outcome

- ✅ Impact: Chat and conversations endpoints now route to phase-three backend (which has chat routes)
- 🧪 Tests: none run
- 📁 Files: api-client.ts, vercel.json, next.config.mjs
- 🔁 Next prompts: deploy and verify chat works end-to-end
- 🧠 Reflection: NEXT_PUBLIC_* build-time env vars on Vercel can silently override code-level fallbacks; using Vercel rewrites decouples routing from env vars

## Evaluation notes (flywheel)

- Failure modes observed: env var on Vercel overriding hardcoded fallback URL in api-client.ts
- Graders run and results (PASS/FAIL): none
- Prompt variant (if applicable): none
- Next experiment (smallest change to try): verify by checking browser network tab for relative `/api/v1/*` requests after redeploy
