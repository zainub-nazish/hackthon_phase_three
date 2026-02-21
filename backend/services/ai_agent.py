"""AI agent service with OpenAI Agents SDK integration and MCP tool dispatch.

Processes natural language messages using the OpenAI Agents SDK with MCP tools
for todo task management. The agent is stateless — instantiated per-request with
conversation history loaded from the database.
"""

import json
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path

from backend.config import settings


# =============================================================================
# System Prompt
# =============================================================================

SYSTEM_PROMPT = """\
You are a Todo AI. Use the provided MCP tools for every action.

You help users manage their tasks through natural conversation.

CAPABILITIES:
- Create tasks (add_task)
- List tasks with optional status filter (list_tasks)
- Mark tasks as completed (complete_task)
- Delete tasks (delete_task)
- Update task details (update_task)

RULES:
- Always use the user_id provided in tool parameters — never use a different user's ID.
- When a user refers to a task by name/description (not by ID), FIRST call list_tasks to find the
  matching task ID, THEN perform the requested action (complete, delete, or update).
  Never guess task IDs.
- After any task operation, confirm what was done with specific details.
- For ambiguous requests matching multiple tasks, list the matches and ask the user
  to clarify which one they mean.
- For non-task messages (greetings, questions about capabilities), respond conversationally
  without calling any tools.
- Never expose internal IDs unless helpful for disambiguation.
- Keep responses concise and conversational.
- You can only manage tasks — you cannot browse the web, send emails, or perform other actions.
- All task operations only affect the current user's tasks.
- If a tool call fails, explain the error to the user without exposing technical details."""


# =============================================================================
# Data Classes
# =============================================================================


@dataclass
class ToolCallData:
    """Data for a single tool call made by the AI agent."""

    tool_name: str
    parameters: str  # JSON-encoded
    result: str  # JSON-encoded
    status: str  # "success" or "error"


@dataclass
class AgentResponse:
    """Response from the AI agent."""

    content: str
    tool_calls: list[ToolCallData] = field(default_factory=list)


# =============================================================================
# AI Agent Service (OpenAI Agents SDK with MCP)
# =============================================================================


class AIAgentService:
    """AI agent service powered by OpenAI Agents SDK with MCP tool dispatch."""

    def __init__(self):
        self._stub_response: AgentResponse | None = None

    def set_stub_response(self, content: str, tool_calls: list[ToolCallData] | None = None):
        """Configure a custom stub response (for testing)."""
        self._stub_response = AgentResponse(
            content=content,
            tool_calls=tool_calls or [],
        )

    async def generate_response(
        self, messages: list[dict], user_id: str
    ) -> AgentResponse:
        """Generate an AI response given conversation history.

        Uses the OpenAI Agents SDK with MCP tools. The SDK runner handles
        the tool-call loop automatically (call tool → feed result → repeat).

        Args:
            messages: List of {"role": str, "content": str} dicts.
            user_id: The authenticated user's ID.

        Returns:
            AgentResponse with content and optional tool calls.
        """
        # Test stub override
        if self._stub_response is not None:
            response = self._stub_response
            self._stub_response = None
            return response

        # Graceful fallback when API key is not configured
        if not settings.openai_api_key:
            return AgentResponse(
                content="I'm an AI assistant stub. Real AI integration coming soon!",
            )

        # Set the API key for the SDK
        os.environ["OPENAI_API_KEY"] = settings.openai_api_key

        # Lazy imports — not required when API key is missing
        from agents import Agent, Runner
        from agents.mcp import MCPServerStdio

        # Resolve project root for subprocess module execution
        project_root = str(Path(__file__).parent.parent.parent)

        # Inject user_id into the system prompt so the agent passes it to tools
        system_with_user = (
            f"{SYSTEM_PROMPT}\n\n"
            f"IMPORTANT: The current user's ID is: {user_id}\n"
            f"Always pass this exact user_id when calling any tool."
        )

        tool_calls_data: list[ToolCallData] = []

        try:
            async with MCPServerStdio(
                params={
                    "command": sys.executable,
                    "args": ["-m", "backend.services.mcp_tools"],
                    "cwd": project_root,
                    "env": {**os.environ},
                },
                cache_tools_list=True,
                client_session_timeout_seconds=30,
            ) as mcp_server:
                agent = Agent(
                    name="TodoBot",
                    instructions=system_with_user,
                    mcp_servers=[mcp_server],
                )

                result = await Runner.run(
                    agent,
                    input=messages,
                )

                # Extract tool calls from the run result
                for item in result.new_items:
                    if hasattr(item, "raw_item"):
                        raw = item.raw_item
                        # Check for tool call items
                        if hasattr(raw, "type") and raw.type == "function_call":
                            tool_calls_data.append(ToolCallData(
                                tool_name=raw.name,
                                parameters=raw.arguments,
                                result="",
                                status="success",
                            ))
                        elif hasattr(raw, "type") and raw.type == "function_call_output":
                            # Match output to the last tool call
                            if tool_calls_data:
                                tool_calls_data[-1].result = raw.output if hasattr(raw, "output") else ""

                # Extract the final text response
                final_text = result.final_output or "I processed your request."

                return AgentResponse(
                    content=final_text,
                    tool_calls=tool_calls_data,
                )

        except Exception as e:
            raise RuntimeError(f"OpenAI Agent error: {e}") from e


# FastAPI dependency
_agent_service = AIAgentService()


def get_ai_agent_service() -> AIAgentService:
    """FastAPI dependency for AI agent service."""
    return _agent_service
