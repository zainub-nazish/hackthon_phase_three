---
id: 002
title: AI Chatbot Constitution Amendment
stage: constitution
date: 2026-02-08
surface: agent
model: claude-opus-4-6
feature: none
branch: 003-frontend-app
user: system
command: /sp.constitution
labels: ["constitution", "governance", "ai-chatbot", "mcp", "openai-agents"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - .specify/memory/constitution.md
tests:
  - null
---

## Prompt

 Todo AI Chatbot

## Overview

This constitution defines the complete specification structure for **Phase-3: Todo AI Chatbot** built using MCP architecture, OpenAI Agents SDK, and a stateless conversation backend.

All implementation will follow the Agentic Dev Stack workflow:

Write Spec → Generate Plan → Break into Tasks → Implement via Claude Code

---

# Spec Structure Index

- Spec-4 — Chat UI (Frontend)
- Spec-5 — Chat API & Conversation System
- Spec-6 — AI Agent Logic
- Spec-7 — MCP Server & Tools
- Spec-8 — Database & Models

---

# Spec-4 — Chat UI (Frontend)

## 1. Overview
Chatbot interface for managing todos via natural language.

## 2. Objectives
- Send user messages
- Display AI responses
- Maintain conversation context visually

## 3. Tech Stack
- OpenAI ChatKit
- React
- Tailwind CSS (optional)

## 4. UI Components
- Chat Container
- Message List
- Message Item
- Chat Input
- Typing Indicator

## 5. Message Rendering
- User vs Assistant alignment
- Timestamp support

## 6. Send Message Flow
- Capture input
- Call Chat API
- Render response

## 7. Conversation Handling
- Store conversation_id
- Load history

## 8. Loading & Error States

## 9. API Integration

## 10. State Management

## 11. UX Requirements

## 12. Deliverables

---

# Spec-5 — Chat API & Conversation System

## 1. Overview
Backend system handling stateless chat requests.

## 2. Objectives
- Process messages
- Persist conversations
- Invoke AI agent

## 3. Tech Stack
- FastAPI
- OpenAI Agents SDK
- SQLModel
- Neon PostgreSQL

## 4. API Endpoint

### POST /api/{user_id}/chat

## 5. Request Schema

## 6. Response Schema

## 7. Stateless Conversation Flow

1. Receive message
2. Fetch conversation history
3. Store user message
4. Run agent
5. Store response
6. Return output

## 8. Conversation Persistence Logic

## 9. Error Handling

## 10. Authentication Handling

## 11. Deliverables

---

# Spec-6 — AI Agent Logic

## 1. Overview
AI agent that interprets natural language todo commands.

## 2. Objectives
- Detect user intent
- Select MCP tools
- Generate confirmations

## 3. Tech Stack
- OpenAI Agents SDK

## 4. Agent Architecture
- Agent
- Runner
- Tool registry

## 5. System Prompt Design

## 6. Tool Selection Logic

## 7. Behavior Mapping

- Task Creation
- Task Listing
- Task Completion
- Task Deletion
- Task Update

## 8. Confirmation Responses

## 9. Error Handling Strategy

## 10. Multi-Tool Calls

## 11. Context Handling

## 12. Deliverables

---

# Spec-7 — MCP Server & Tools

## 1. Overview
MCP server exposing task operations as tools.

## 2. Objectives
- Enable agent tool execution
- Manage todo operations

## 3. Tech Stack
- Official MCP SDK
- FastAPI
- SQLModel

## 4. MCP Server Architecture

## 5. Tool Registry

## 6. Tool Specifications

### add_task
- Parameters
- Response schema

### list_tasks
- Filters
- Output format

### complete_task

### delete_task

### update_task

## 7. Database Integration

## 8. Stateless Tool Design

## 9. Error Handling

## 10. Logging & Monitoring

## 11. Deliverables

---

# Spec-8 — Database & Models

## 1. Overview
Database schema for tasks and conversations.

## 2. Objectives
- Persist todos
- Store chat history

## 3. Tech Stack
- SQLModel
- Neon PostgreSQL

## 4. Database Architecture

## 5. Models

### Task
- id
- user_id
- title
- description
- completed
- created_at
- updated_at

### Conversation
- id
- user_id
- created_at
- updated_at

### Message
- id
- user_id
- conversation_id
- role
- content
- created_at

## 6. Relationships

- Conversation → Messages (1-Many)
- User → Tasks (1-Many)

## 7. Migrations

## 8. Indexing Strategy

## 9. Validation Rules

## 10. Deliverables

---

# Implementation Order

1. Spec-8 — Database
2. Spec-7 — MCP Tools
3. Spec-6 — Agent Logic
4. Spec-5 — Chat API
5. Spec-4 — Chat UI

---

# Final Deliverable

A fully functional AI Todo Chatbot that:

- Understands natural language
- Uses MCP tools
- Persists conversations
- Runs stateless backend requests
- Provides confirmation responses

## Response snapshot

Amended the project constitution from v1.0.0 to v1.1.0 (MINOR bump) for the Todo AI Chatbot phase:

- Kept all 6 original principles (Spec-First, Security by Design, Deterministic Behavior, Separation of Concerns, Reproducibility, API Standards) and extended them for AI/MCP context.
- Added 2 new principles: VII. AI Agent Safety (tool boundaries, logging, graceful failure handling) and VIII. Stateless Conversation Architecture (per-request self-containment, DB-backed context).
- Added Technology Stack Constraints table with OpenAI Agents SDK, MCP SDK, and OpenAI ChatKit.
- Added Spec Structure Index (Spec-4 through Spec-8) with implementation order.
- Performed consistency checks against plan, spec, and tasks templates.
- Included Sync Impact Report as HTML comment in constitution file.

## Outcome

- ✅ Impact: Constitution amended to v1.1.0 with AI Chatbot governance principles
- 🧪 Tests: N/A (governance document)
- 📁 Files: .specify/memory/constitution.md updated
- 🔁 Next prompts: /sp.specify for Spec-8 (Database & Models) as first implementation target
- 🧠 Reflection: MINOR bump appropriate — added new principles and sections without removing or redefining existing ones. The 8-principle structure covers all architectural layers of the AI Chatbot system.

## Evaluation notes (flywheel)

- Failure modes observed: None
- Graders run and results (PASS/FAIL): N/A
- Prompt variant (if applicable): Standard constitution amendment with AI/MCP extensions
- Next experiment (smallest change to try): Validate new constitution gates during first /sp.plan for Spec-8
