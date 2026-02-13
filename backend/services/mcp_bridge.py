"""MCP bridge — schema converter and tool dispatch for the AI agent.

Converts MCP tool definitions to Anthropic API format and dispatches tool calls
from the agent loop to MCP tool handlers. The bridge injects user_id server-side
so the LLM never controls which user's tasks it accesses.
"""

from typing import Any

from backend.services.mcp_tools import server


# =============================================================================
# Schema Conversion (MCP → Anthropic API format)
# =============================================================================

# user_id is injected server-side — never exposed to the LLM
_HIDDEN_PARAMS = {"user_id"}


def _convert_tool_schema(tool) -> dict:
    """Convert a single MCP tool definition to Anthropic API format.

    Strips hidden parameters (user_id) from the input schema so the LLM
    cannot control which user's tasks it accesses.
    """
    params = tool.parameters or {}
    properties = dict(params.get("properties", {}))
    required = list(params.get("required", []))

    # Strip hidden parameters
    for param in _HIDDEN_PARAMS:
        properties.pop(param, None)
        if param in required:
            required.remove(param)

    input_schema = {
        "type": "object",
        "properties": properties,
        "required": required,
    }

    return {
        "name": tool.name,
        "description": tool.description or "",
        "input_schema": input_schema,
    }


def _build_schemas() -> list[dict]:
    """Build and return all tool schemas from the MCP server."""
    tools = server._tool_manager.list_tools()
    return [_convert_tool_schema(t) for t in tools]


# Cached schemas — computed once at first access
_cached_schemas: list[dict] | None = None


def get_tool_schemas() -> list[dict]:
    """Get Anthropic-format tool schemas from the MCP server.

    Returns a cached list of tool definitions, each with:
    - name: Tool name (e.g., "add_task")
    - description: Tool description for Claude
    - input_schema: JSON Schema for parameters (user_id stripped)
    """
    global _cached_schemas
    if _cached_schemas is None:
        _cached_schemas = _build_schemas()
    return _cached_schemas


# =============================================================================
# Tool Dispatch
# =============================================================================

# Build a lookup of tool name → MCP tool object for dispatch
def _get_tool_map() -> dict:
    """Get a mapping of tool name → MCP Tool object."""
    return {t.name: t for t in server._tool_manager.list_tools()}


_tool_map: dict | None = None


def _ensure_tool_map() -> dict:
    global _tool_map
    if _tool_map is None:
        _tool_map = _get_tool_map()
    return _tool_map


async def execute_tool(name: str, params: dict[str, Any], user_id: str) -> dict:
    """Execute an MCP tool by name, injecting user_id.

    Args:
        name: Tool name (e.g., "add_task").
        params: Parameters from Claude's tool_use block.
        user_id: Authenticated user's ID (injected server-side).

    Returns:
        Tool result dict. On error: {"is_error": True, "error": "..."}.
    """
    tool_map = _ensure_tool_map()
    tool = tool_map.get(name)

    if tool is None:
        return {"is_error": True, "error": f"Unknown tool: {name}"}

    # Inject user_id into parameters
    call_params = dict(params)
    call_params["user_id"] = user_id

    try:
        result = await tool.run(call_params)
        return result
    except Exception as e:
        return {"is_error": True, "error": str(e)}
