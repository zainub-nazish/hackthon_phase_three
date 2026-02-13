"""AI agent service with Anthropic Claude integration and MCP tool dispatch.

Processes natural language messages, selects and executes MCP tools via the
bridge, and returns friendly confirmation responses. Tool definitions and
execution are handled by the MCP tool server (mcp_tools.py) through the
bridge (mcp_bridge.py).
"""

import json
from dataclasses import dataclass, field

from backend.config import settings
from backend.services.mcp_bridge import execute_tool, get_tool_schemas


# =============================================================================
# System Prompt (D-004: inline constant)
# =============================================================================

SYSTEM_PROMPT = """\
You are a friendly AI todo assistant. You help users manage their tasks through natural language conversation.

## Your Capabilities
You can create, list, complete, delete, and update tasks for the user.

## Guidelines
- Always confirm actions with a brief, friendly message
- When the user asks to complete, delete, or update a task by name, use list_tasks first to find the correct task_id
- If multiple tasks match the user's description, show the matches and ask which one they mean
- Never make up or hallucinate task data — only reference tasks that exist in the user's list
- Resolve references like "it", "that task", or "the last one" from conversation context
- If you can't determine what the user wants, ask for clarification
- For non-task messages (greetings, questions about capabilities), respond helpfully without using tools
- Keep responses concise and conversational

## Response Format
- Task created: include the task title in your confirmation
- Task listed: present tasks in a readable format with titles and status
- Task completed/deleted/updated: confirm the specific task that was changed
- Errors: explain what went wrong in simple terms and suggest what to try

## Important
- You can only manage tasks — you cannot browse the web, send emails, or perform other actions
- All task operations only affect the current user's tasks
- If a tool call fails, explain the error to the user without exposing technical details"""


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
# AI Agent Service (D-001: manual agent loop with MCP tool dispatch)
# =============================================================================


class AIAgentService:
    """AI agent service powered by Anthropic Claude with MCP tool dispatch."""

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

        Implements the agent loop: call Claude → tool_use → execute via MCP → tool_result → repeat.

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

        # D-006: Graceful fallback when API key is not configured
        if not settings.anthropic_api_key:
            return AgentResponse(
                content="I'm an AI assistant stub. Real AI integration coming soon!",
            )

        # Lazy import — anthropic not required when API key is missing
        import anthropic

        client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
        tool_calls_data: list[ToolCallData] = []
        api_messages = list(messages)  # Copy to avoid modifying original

        try:
            while True:
                response = await client.messages.create(
                    model=settings.anthropic_model,
                    max_tokens=1024,
                    system=SYSTEM_PROMPT,
                    tools=get_tool_schemas(),
                    messages=api_messages,
                )

                if response.stop_reason == "end_turn":
                    # Extract text content from response
                    text_parts = []
                    for block in response.content:
                        if hasattr(block, "text"):
                            text_parts.append(block.text)
                    return AgentResponse(
                        content="".join(text_parts) or "I processed your request.",
                        tool_calls=tool_calls_data,
                    )

                elif response.stop_reason == "tool_use":
                    # Add assistant response to message history
                    api_messages.append({
                        "role": "assistant",
                        "content": response.content,
                    })

                    # Execute each tool via MCP bridge and collect results
                    tool_results = []
                    for block in response.content:
                        if block.type == "tool_use":
                            result = await execute_tool(block.name, block.input, user_id)
                            is_error = result.get("is_error", False)
                            tool_status = "error" if is_error else "success"

                            # Record tool call for DB persistence
                            tool_calls_data.append(ToolCallData(
                                tool_name=block.name,
                                parameters=json.dumps(block.input),
                                result=json.dumps(result),
                                status=tool_status,
                            ))

                            # Build tool result for Claude
                            tool_result_block = {
                                "type": "tool_result",
                                "tool_use_id": block.id,
                                "content": json.dumps(result),
                            }
                            if is_error:
                                tool_result_block["is_error"] = True
                            tool_results.append(tool_result_block)

                    # Send tool results back to Claude
                    api_messages.append({
                        "role": "user",
                        "content": tool_results,
                    })

                else:
                    # Unexpected stop reason — return whatever text is available
                    text_parts = []
                    for block in response.content:
                        if hasattr(block, "text"):
                            text_parts.append(block.text)
                    return AgentResponse(
                        content="".join(text_parts) or "I encountered an issue. Please try again.",
                        tool_calls=tool_calls_data,
                    )

        except anthropic.APIError as e:
            raise RuntimeError(f"Anthropic API error: {e}") from e


# FastAPI dependency
_agent_service = AIAgentService()


def get_ai_agent_service() -> AIAgentService:
    """FastAPI dependency for AI agent service."""
    return _agent_service
