# Research: Todo AI Chatbot (011)

**Date**: 2026-02-14
**Branch**: `011-todo-ai-chatbot`

## Research Questions & Findings

### RQ-1: OpenAI Agents SDK vs Existing Anthropic Integration

**Decision**: Migrate from Anthropic Claude to OpenAI Agents SDK

**Rationale**:
- User explicitly specifies OpenAI Agents SDK as the AI framework
- OpenAI Agents SDK provides native tool calling, handoffs, and guardrails
- Agents SDK has built-in MCP server support via `mcp` parameter on Agent
- Simplifies agent loop — SDK handles tool dispatch internally (no manual loop needed)

**Alternatives considered**:
- Keep Anthropic Claude: Already working, but contradicts user requirements
- LangChain/LangGraph: Over-engineered for this use case
- Raw OpenAI API: Agents SDK adds agent abstractions (tools, instructions, runner)

**Impact on existing code**:
- `backend/services/ai_agent.py` — Full rewrite (Anthropic → OpenAI Agents SDK)
- `backend/services/mcp_bridge.py` — Remove (Agents SDK has native MCP support)
- `backend/config.py` — Replace `ANTHROPIC_API_KEY` with `OPENAI_API_KEY`
- `backend/requirements.txt` — Replace `anthropic>=0.79.0` with `openai-agents`

### RQ-2: OpenAI Agents SDK + MCP Integration Pattern

**Decision**: Use Agents SDK's native `MCPServerStdio` for tool registration

**Rationale**:
- The `openai-agents` package provides `MCPServerStdio` and `MCPServerStreamableHTTP`
- Agent constructor accepts `mcp_servers=[server]` parameter
- Tools are auto-discovered from MCP server — no manual schema extraction needed
- Agent runner handles the tool call → execute → feed back loop automatically

**Pattern**:
```python
from agents import Agent, Runner
from agents.mcp import MCPServerStdio

mcp_server = MCPServerStdio(command="python", args=["mcp_tools.py"])
agent = Agent(name="TodoBot", instructions="...", mcp_servers=[mcp_server])
result = await Runner.run(agent, messages=[...])
```

**Alternatives considered**:
- Manual tool registration via `@function_tool`: Works but loses MCP abstraction
- HTTP MCP server: Adds network hop; stdio is simpler for co-located processes

### RQ-3: Neon PostgreSQL Async Connection with SQLModel

**Decision**: Use existing `asyncpg` driver with SQLModel async sessions

**Rationale**:
- Existing `backend/database.py` already supports async PostgreSQL via `asyncpg`
- SQLModel integrates with SQLAlchemy async engine
- Neon Serverless PostgreSQL works with standard `asyncpg` connections
- Connection string format: `postgresql+asyncpg://user:pass@host/db?ssl=require`

**Alternatives considered**:
- `psycopg[async]`: Valid but project already uses asyncpg
- Prisma Python: Not mature enough for production async usage
- Raw asyncpg without ORM: Loses SQLModel validation benefits

### RQ-4: Stateless Backend Architecture

**Decision**: Maintain fully stateless request handling — no in-memory state

**Rationale**:
- Every request fetches conversation history from Neon DB
- Agent is instantiated per-request with conversation context
- No WebSocket or server-sent events — pure request/response
- Horizontal scalability: any instance can serve any request

**Key constraint**:
- Conversation history must be loaded from DB on every `/chat` request
- Agent receives full message history as input, not just latest message
- After agent completes, save user message + assistant response to DB

### RQ-5: OpenAI ChatKit Frontend Integration

**Decision**: Keep existing `@openai/chatkit-react` integration, update domain config

**Rationale**:
- ChatKit is already integrated in `frontend/components/chat/chat-container.tsx`
- Uses Full Proxy architecture with authenticated fetch
- Domain allowlist configured via `NEXT_PUBLIC_CHATKIT_DOMAIN_KEY`
- No frontend changes needed for backend AI framework migration

**Alternatives considered**:
- Custom chat UI: More work, less polish than ChatKit
- Vercel AI SDK: Different paradigm, would require frontend rewrite

### RQ-6: API Endpoint Path Convention

**Decision**: Use existing `/api/v1/users/{user_id}/chat` path (not `/api/{user_id}/chat`)

**Rationale**:
- Existing codebase uses `/api/v1/users/{user_id}/` pattern consistently
- Frontend API client and chat hooks already target this path
- Changing breaks existing frontend integration without benefit
- Version prefix (`v1`) follows REST best practices

**User's spec said** `/api/{user_id}/chat` but the existing convention is better — we preserve it.
