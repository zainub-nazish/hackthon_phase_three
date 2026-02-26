"""Unit tests for AI agent service (OpenAI Agents SDK)."""

import json
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from backend.tests.conftest import make_agent_run_result


# =============================================================================
# Tool Executor Tests (via MCP tools directly)
# =============================================================================


class TestAddTask:
    """Tests for add_task tool executor."""

    @pytest.mark.asyncio
    async def test_add_task_creates_task(self, agent_db):
        from backend.services.mcp_tools import add_task

        user_id = str(uuid4())
        result = await add_task(title="Buy milk", user_id=user_id)

        assert "id" in result
        assert result["title"] == "Buy milk"
        assert result["completed"] is False
        assert result["description"] is None

    @pytest.mark.asyncio
    async def test_add_task_with_description(self, agent_db):
        from backend.services.mcp_tools import add_task

        user_id = str(uuid4())
        result = await add_task(
            title="Meeting", description="Slides for Monday", user_id=user_id,
        )

        assert result["title"] == "Meeting"
        assert result["description"] == "Slides for Monday"

    @pytest.mark.asyncio
    async def test_add_task_empty_title_returns_error(self, agent_db):
        from backend.services.mcp_tools import add_task

        result = await add_task(title="", user_id=str(uuid4()))

        assert result["is_error"] is True
        assert "required" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_add_task_title_too_long_returns_error(self, agent_db):
        from backend.services.mcp_tools import add_task

        result = await add_task(title="x" * 256, user_id=str(uuid4()))

        assert result["is_error"] is True
        assert "200" in result["error"]


class TestListTasks:
    """Tests for list_tasks tool executor."""

    @pytest.mark.asyncio
    async def test_list_tasks_returns_all(self, agent_db):
        from backend.services.mcp_tools import add_task, list_tasks, complete_task

        user_id = str(uuid4())
        task1 = await add_task(title="Task 1", user_id=user_id)
        await add_task(title="Task 2", user_id=user_id)
        await complete_task(task_id=task1["id"], user_id=user_id)

        result = await list_tasks(user_id=user_id)

        assert result["count"] == 2
        assert len(result["tasks"]) == 2

    @pytest.mark.asyncio
    async def test_list_tasks_filter_pending(self, agent_db):
        from backend.services.mcp_tools import add_task, list_tasks, complete_task

        user_id = str(uuid4())
        task1 = await add_task(title="Done task", user_id=user_id)
        await add_task(title="Pending task", user_id=user_id)
        await complete_task(task_id=task1["id"], user_id=user_id)

        result = await list_tasks(user_id=user_id, status="pending")

        assert result["count"] == 1
        assert result["tasks"][0]["title"] == "Pending task"

    @pytest.mark.asyncio
    async def test_list_tasks_filter_completed(self, agent_db):
        from backend.services.mcp_tools import add_task, list_tasks, complete_task

        user_id = str(uuid4())
        task1 = await add_task(title="Done task", user_id=user_id)
        await add_task(title="Pending task", user_id=user_id)
        await complete_task(task_id=task1["id"], user_id=user_id)

        result = await list_tasks(user_id=user_id, status="completed")

        assert result["count"] == 1
        assert result["tasks"][0]["title"] == "Done task"

    @pytest.mark.asyncio
    async def test_list_tasks_empty(self, agent_db):
        from backend.services.mcp_tools import list_tasks

        result = await list_tasks(user_id=str(uuid4()))

        assert result["count"] == 0
        assert result["tasks"] == []

    @pytest.mark.asyncio
    async def test_list_tasks_user_isolation(self, agent_db):
        from backend.services.mcp_tools import add_task, list_tasks

        user_a = str(uuid4())
        user_b = str(uuid4())
        await add_task(title="User A task", user_id=user_a)
        await add_task(title="User B task", user_id=user_b)

        result_a = await list_tasks(user_id=user_a)
        result_b = await list_tasks(user_id=user_b)

        assert result_a["count"] == 1
        assert result_a["tasks"][0]["title"] == "User A task"
        assert result_b["count"] == 1
        assert result_b["tasks"][0]["title"] == "User B task"


class TestCompleteTask:
    """Tests for complete_task tool executor."""

    @pytest.mark.asyncio
    async def test_complete_task_success(self, agent_db):
        from backend.services.mcp_tools import add_task, complete_task

        user_id = str(uuid4())
        task = await add_task(title="To complete", user_id=user_id)

        result = await complete_task(task_id=task["id"], user_id=user_id)

        assert result["completed"] is True
        assert result["title"] == "To complete"

    @pytest.mark.asyncio
    async def test_complete_task_not_found(self, agent_db):
        from backend.services.mcp_tools import complete_task

        result = await complete_task(
            task_id=str(uuid4()), user_id=str(uuid4())
        )

        assert result["is_error"] is True
        assert "not found" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_complete_task_wrong_user(self, agent_db):
        from backend.services.mcp_tools import add_task, complete_task

        user_a = str(uuid4())
        user_b = str(uuid4())
        task = await add_task(title="User A task", user_id=user_a)

        result = await complete_task(task_id=task["id"], user_id=user_b)

        assert result["is_error"] is True
        assert "not found" in result["error"].lower()


class TestDeleteTask:
    """Tests for delete_task tool executor."""

    @pytest.mark.asyncio
    async def test_delete_task_success(self, agent_db):
        from backend.services.mcp_tools import add_task, delete_task, list_tasks

        user_id = str(uuid4())
        task = await add_task(title="To delete", user_id=user_id)

        result = await delete_task(task_id=task["id"], user_id=user_id)

        assert result["deleted"] is True
        assert result["title"] == "To delete"

        list_result = await list_tasks(user_id=user_id)
        assert list_result["count"] == 0

    @pytest.mark.asyncio
    async def test_delete_task_not_found(self, agent_db):
        from backend.services.mcp_tools import delete_task

        result = await delete_task(
            task_id=str(uuid4()), user_id=str(uuid4())
        )

        assert result["is_error"] is True
        assert "not found" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_delete_task_wrong_user(self, agent_db):
        from backend.services.mcp_tools import add_task, delete_task

        user_a = str(uuid4())
        user_b = str(uuid4())
        task = await add_task(title="User A task", user_id=user_a)

        result = await delete_task(task_id=task["id"], user_id=user_b)

        assert result["is_error"] is True


class TestUpdateTask:
    """Tests for update_task tool executor."""

    @pytest.mark.asyncio
    async def test_update_task_title(self, agent_db):
        from backend.services.mcp_tools import add_task, update_task

        user_id = str(uuid4())
        task = await add_task(title="Old title", user_id=user_id)

        result = await update_task(
            task_id=task["id"], title="New title", user_id=user_id
        )

        assert result["title"] == "New title"

    @pytest.mark.asyncio
    async def test_update_task_description(self, agent_db):
        from backend.services.mcp_tools import add_task, update_task

        user_id = str(uuid4())
        task = await add_task(title="Task", user_id=user_id)

        result = await update_task(
            task_id=task["id"], description="New desc", user_id=user_id
        )

        assert result["description"] == "New desc"

    @pytest.mark.asyncio
    async def test_update_task_not_found(self, agent_db):
        from backend.services.mcp_tools import update_task

        result = await update_task(
            task_id=str(uuid4()), title="X", user_id=str(uuid4())
        )

        assert result["is_error"] is True

    @pytest.mark.asyncio
    async def test_update_task_no_fields_returns_error(self, agent_db):
        from backend.services.mcp_tools import add_task, update_task

        user_id = str(uuid4())
        task = await add_task(title="Task", user_id=user_id)

        result = await update_task(
            task_id=task["id"], user_id=user_id
        )

        assert result["is_error"] is True
        assert "at least one" in result["error"].lower()


# =============================================================================
# Agent Service Tests (OpenAI Agents SDK)
# =============================================================================


class TestAgentWithToolCalls:
    """Test agent service processes messages and returns tool call data."""

    @pytest.mark.asyncio
    async def test_agent_single_tool_call(self, agent_db):
        from backend.services.ai_agent import AIAgentService

        agent = AIAgentService()
        messages = [{"role": "user", "content": "Add a task to buy milk"}]

        mock_result = make_agent_run_result(
            final_output="I've added 'Buy milk' to your task list!",
            tool_calls=[{
                "name": "add_task",
                "arguments": '{"title": "Buy milk", "user_id": "test-user"}',
                "output": '{"id": "123", "title": "Buy milk", "completed": false}',
            }],
        )

        with patch("backend.services.ai_agent.settings") as mock_settings:
            mock_settings.openai_api_key = "test-key"

            with patch("agents.Runner.run", new_callable=AsyncMock, return_value=mock_result):
                with patch("agents.mcp.MCPServerStdio") as MockMCP:
                    mock_mcp_instance = AsyncMock()
                    MockMCP.return_value.__aenter__ = AsyncMock(return_value=mock_mcp_instance)
                    MockMCP.return_value.__aexit__ = AsyncMock(return_value=None)

                    result = await agent.generate_response(messages, str(uuid4()))

        assert "Buy milk" in result.content
        assert len(result.tool_calls) == 1
        assert result.tool_calls[0].tool_name == "add_task"
        assert result.tool_calls[0].status == "success"

    @pytest.mark.asyncio
    async def test_agent_multi_step_tool_calls(self, agent_db):
        from backend.services.ai_agent import AIAgentService

        agent = AIAgentService()
        messages = [{"role": "user", "content": "Delete the old task"}]

        mock_result = make_agent_run_result(
            final_output="I've deleted 'Old task' for you.",
            tool_calls=[
                {
                    "name": "list_tasks",
                    "arguments": '{"user_id": "test-user"}',
                    "output": '{"tasks": [{"id": "456", "title": "Old task"}], "count": 1}',
                },
                {
                    "name": "delete_task",
                    "arguments": '{"task_id": "456", "user_id": "test-user"}',
                    "output": '{"deleted": true, "title": "Old task"}',
                },
            ],
        )

        with patch("backend.services.ai_agent.settings") as mock_settings:
            mock_settings.openai_api_key = "test-key"

            with patch("agents.Runner.run", new_callable=AsyncMock, return_value=mock_result):
                with patch("agents.mcp.MCPServerStdio") as MockMCP:
                    mock_mcp_instance = AsyncMock()
                    MockMCP.return_value.__aenter__ = AsyncMock(return_value=mock_mcp_instance)
                    MockMCP.return_value.__aexit__ = AsyncMock(return_value=None)

                    result = await agent.generate_response(messages, str(uuid4()))

        assert "Old task" in result.content
        assert len(result.tool_calls) == 2
        assert result.tool_calls[0].tool_name == "list_tasks"
        assert result.tool_calls[1].tool_name == "delete_task"


class TestAgentAPIError:
    """Test agent handles API errors."""

    @pytest.mark.asyncio
    async def test_api_error_raises_runtime_error(self, agent_db):
        from backend.services.ai_agent import AIAgentService

        agent = AIAgentService()
        messages = [{"role": "user", "content": "Hello"}]

        with patch("backend.services.ai_agent.settings") as mock_settings:
            mock_settings.openai_api_key = "test-key"

            with patch("agents.Runner.run", new_callable=AsyncMock, side_effect=Exception("Rate limit")):
                with patch("agents.mcp.MCPServerStdio") as MockMCP:
                    mock_mcp_instance = AsyncMock()
                    MockMCP.return_value.__aenter__ = AsyncMock(return_value=mock_mcp_instance)
                    MockMCP.return_value.__aexit__ = AsyncMock(return_value=None)

                    with pytest.raises(RuntimeError, match="OpenAI Agent error"):
                        await agent.generate_response(messages, str(uuid4()))


class TestAgentStubFallback:
    """Test stub fallback behavior."""

    @pytest.mark.asyncio
    async def test_missing_api_key_returns_stub(self, agent_db):
        from backend.services.ai_agent import AIAgentService

        agent = AIAgentService()
        messages = [{"role": "user", "content": "Hello"}]

        with patch("backend.services.ai_agent.settings") as mock_settings:
            mock_settings.openai_api_key = None

            result = await agent.generate_response(messages, str(uuid4()))

        assert "stub" in result.content.lower()
        assert result.tool_calls == []

    @pytest.mark.asyncio
    async def test_set_stub_response_works(self, agent_db):
        from backend.services.ai_agent import AIAgentService, ToolCallData

        agent = AIAgentService()
        tool_calls = [
            ToolCallData(
                tool_name="add_task",
                parameters='{"title": "Test"}',
                result='{"id": "123", "title": "Test"}',
                status="success",
            )
        ]
        agent.set_stub_response("Custom stub", tool_calls)

        result = await agent.generate_response(
            [{"role": "user", "content": "Test"}],
            str(uuid4()),
        )

        assert result.content == "Custom stub"
        assert len(result.tool_calls) == 1
        assert result.tool_calls[0].tool_name == "add_task"

    @pytest.mark.asyncio
    async def test_stub_response_resets_after_use(self, agent_db):
        from backend.services.ai_agent import AIAgentService

        agent = AIAgentService()
        agent.set_stub_response("First call")

        result1 = await agent.generate_response(
            [{"role": "user", "content": "Hello"}], str(uuid4())
        )
        assert result1.content == "First call"

        # Second call should fall back to stub (no API key)
        with patch("backend.services.ai_agent.settings") as mock_settings:
            mock_settings.openai_api_key = None
            result2 = await agent.generate_response(
                [{"role": "user", "content": "Hello"}], str(uuid4())
            )
        assert "stub" in result2.content.lower()
