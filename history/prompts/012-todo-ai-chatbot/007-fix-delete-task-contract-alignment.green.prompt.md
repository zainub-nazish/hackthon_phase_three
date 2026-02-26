---
id: "007"
title: Fix delete_task Contract Alignment
stage: green
date: 2026-02-21
surface: agent
model: claude-sonnet-4-6
feature: 012-todo-ai-chatbot
branch: 012-todo-ai-chatbot
user: zainub-nazish
command: fix delete_task return keys to match contract
labels: ["bugfix","contract","mcp-tools","delete-task"]
links:
  spec: specs/012-todo-ai-chatbot/contracts/mcp-tools.yaml
  ticket: null
  adr: null
  pr: null
files:
  - backend/services/mcp_tools.py
  - huggies_face_three/phase_three_huggies/backend/services/mcp_tools.py
  - backend/tests/test_mcp_tools.py
tests:
  - backend/tests/test_mcp_tools.py::TestMCPDeleteTask::test_delete_task_success
  - backend/tests/test_mcp_tools.py::TestMCPDeleteTask::test_delete_task_not_found
  - backend/tests/test_mcp_tools.py::TestMCPDeleteTask::test_delete_task_wrong_user
---

## Prompt

Haan, yeh fix apply karein `delete_task` mein.

## Response snapshot

Fixed `delete_task` return keys in both copies:

**Before:**
```python
return {"deleted": True, "id": str(task_id), "title": task_title}
```

**After:**
```python
return {"success": True, "deleted_task_id": str(task_id)}
```

Updated test assertion from `result["deleted"]` / `result["title"]`
to `result["success"]` / `result["deleted_task_id"]`.

All 3 TestMCPDeleteTask tests pass. Committed as `cbf78d5`.

## Outcome

- ✅ Impact: `delete_task` return shape now matches `specs/012-todo-ai-chatbot/contracts/mcp-tools.yaml` exactly
- 🧪 Tests: 3/3 TestMCPDeleteTask PASSED
- 📁 Files: backend/services/mcp_tools.py, backend/tests/test_mcp_tools.py (+ HF copy)
- 🔁 Next prompts: Push to remote; ready for judge review
- 🧠 Reflection: Contract-first — when contract and code diverge, change code to match the contract (authoritative spec). Test updated to assert on new keys.

## Evaluation notes (flywheel)

- Failure modes observed: none
- Graders run and results (PASS/FAIL): TestMCPDeleteTask — 3 PASS
- Prompt variant (if applicable): n/a
- Next experiment (smallest change to try): n/a
