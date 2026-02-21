"""Tests for MCP tool handlers.

Tests are organized by user story, matching the structure in tasks.md:
- TestMCPAddTask: US1 add_task tool handler
- TestMCPListTasks: US2 list_tasks tool handler
- TestMCPCompleteTask: US3 complete_task tool handler
- TestMCPUpdateTask: US4 update_task tool handler
- TestMCPDeleteTask: US5 delete_task tool handler
- TestMCPUserIsolation: Cross-cutting user isolation (Phase 9)
"""

from uuid import uuid4

import pytest


# =============================================================================
# Phase 3: US1 — add_task Tests (T007-T010)
# =============================================================================


class TestMCPAddTask:
    """Tests for add_task MCP tool handler."""

    @pytest.mark.asyncio
    async def test_add_task_creates_task(self, mcp_db):
        from backend.services.mcp_tools import add_task

        user_id = str(uuid4())
        result = await add_task(title="Buy milk", user_id=user_id)

        assert "id" in result
        assert result["title"] == "Buy milk"
        assert result["completed"] is False
        assert result["description"] is None

    @pytest.mark.asyncio
    async def test_add_task_with_description(self, mcp_db):
        from backend.services.mcp_tools import add_task

        user_id = str(uuid4())
        result = await add_task(
            title="Meeting", description="Slides for Monday", user_id=user_id
        )

        assert result["title"] == "Meeting"
        assert result["description"] == "Slides for Monday"

    @pytest.mark.asyncio
    async def test_add_task_empty_title_returns_error(self, mcp_db):
        from backend.services.mcp_tools import add_task

        result = await add_task(title="", user_id=str(uuid4()))

        assert result["is_error"] is True
        assert "required" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_add_task_title_too_long(self, mcp_db):
        from backend.services.mcp_tools import add_task

        result = await add_task(title="x" * 256, user_id=str(uuid4()))

        assert result["is_error"] is True
        assert "200" in result["error"]


# =============================================================================
# Phase 4: US2 — list_tasks Tests (T014-T018)
# =============================================================================


class TestMCPListTasks:
    """Tests for list_tasks MCP tool handler."""

    @pytest.mark.asyncio
    async def test_list_all_tasks(self, mcp_db):
        from backend.services.mcp_tools import add_task, list_tasks

        user_id = str(uuid4())
        await add_task(title="Task 1", user_id=user_id)
        await add_task(title="Task 2", user_id=user_id)

        result = await list_tasks(user_id=user_id)

        assert result["count"] == 2
        assert len(result["tasks"]) == 2

    @pytest.mark.asyncio
    async def test_list_pending_tasks(self, mcp_db):
        from backend.services.mcp_tools import add_task, list_tasks, complete_task

        user_id = str(uuid4())
        task1 = await add_task(title="Done task", user_id=user_id)
        await add_task(title="Pending task", user_id=user_id)
        await complete_task(task_id=task1["id"], user_id=user_id)

        result = await list_tasks(user_id=user_id, status="pending")

        assert result["count"] == 1
        assert result["tasks"][0]["title"] == "Pending task"

    @pytest.mark.asyncio
    async def test_list_completed_tasks(self, mcp_db):
        from backend.services.mcp_tools import add_task, list_tasks, complete_task

        user_id = str(uuid4())
        task1 = await add_task(title="Done task", user_id=user_id)
        await add_task(title="Pending task", user_id=user_id)
        await complete_task(task_id=task1["id"], user_id=user_id)

        result = await list_tasks(user_id=user_id, status="completed")

        assert result["count"] == 1
        assert result["tasks"][0]["title"] == "Done task"

    @pytest.mark.asyncio
    async def test_list_empty(self, mcp_db):
        from backend.services.mcp_tools import list_tasks

        result = await list_tasks(user_id=str(uuid4()))

        assert result["count"] == 0
        assert result["tasks"] == []

    @pytest.mark.asyncio
    async def test_list_user_isolation(self, mcp_db):
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


# =============================================================================
# Phase 5: US3 — complete_task Tests (T022-T025)
# =============================================================================


class TestMCPCompleteTask:
    """Tests for complete_task MCP tool handler."""

    @pytest.mark.asyncio
    async def test_complete_task_success(self, mcp_db):
        from backend.services.mcp_tools import add_task, complete_task

        user_id = str(uuid4())
        task = await add_task(title="To complete", user_id=user_id)

        result = await complete_task(task_id=task["id"], user_id=user_id)

        assert result["completed"] is True
        assert result["title"] == "To complete"

    @pytest.mark.asyncio
    async def test_complete_task_not_found(self, mcp_db):
        from backend.services.mcp_tools import complete_task

        result = await complete_task(task_id=str(uuid4()), user_id=str(uuid4()))

        assert result["is_error"] is True
        assert "not found" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_complete_task_wrong_user(self, mcp_db):
        from backend.services.mcp_tools import add_task, complete_task

        user_a = str(uuid4())
        user_b = str(uuid4())
        task = await add_task(title="User A task", user_id=user_a)

        result = await complete_task(task_id=task["id"], user_id=user_b)

        assert result["is_error"] is True
        assert "not found" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_complete_task_invalid_uuid(self, mcp_db):
        from backend.services.mcp_tools import complete_task

        result = await complete_task(task_id="not-a-uuid", user_id=str(uuid4()))

        assert result["is_error"] is True
        assert "Invalid" in result["error"]


# =============================================================================
# Phase 6: US4 — update_task Tests (T029-T032)
# =============================================================================


class TestMCPUpdateTask:
    """Tests for update_task MCP tool handler."""

    @pytest.mark.asyncio
    async def test_update_title(self, mcp_db):
        from backend.services.mcp_tools import add_task, update_task

        user_id = str(uuid4())
        task = await add_task(title="Old title", user_id=user_id)

        result = await update_task(task_id=task["id"], title="New title", user_id=user_id)

        assert result["title"] == "New title"

    @pytest.mark.asyncio
    async def test_update_description(self, mcp_db):
        from backend.services.mcp_tools import add_task, update_task

        user_id = str(uuid4())
        task = await add_task(title="Task", user_id=user_id)

        result = await update_task(task_id=task["id"], description="New desc", user_id=user_id)

        assert result["description"] == "New desc"

    @pytest.mark.asyncio
    async def test_update_not_found(self, mcp_db):
        from backend.services.mcp_tools import update_task

        result = await update_task(
            task_id=str(uuid4()), title="X", user_id=str(uuid4())
        )

        assert result["is_error"] is True

    @pytest.mark.asyncio
    async def test_update_no_fields(self, mcp_db):
        from backend.services.mcp_tools import add_task, update_task

        user_id = str(uuid4())
        task = await add_task(title="Task", user_id=user_id)

        result = await update_task(task_id=task["id"], user_id=user_id)

        assert result["is_error"] is True
        assert "at least one" in result["error"].lower()


# =============================================================================
# Phase 7: US5 — delete_task Tests (T036-T038)
# =============================================================================


class TestMCPDeleteTask:
    """Tests for delete_task MCP tool handler."""

    @pytest.mark.asyncio
    async def test_delete_task_success(self, mcp_db):
        from backend.services.mcp_tools import add_task, delete_task, list_tasks

        user_id = str(uuid4())
        task = await add_task(title="To delete", user_id=user_id)

        result = await delete_task(task_id=task["id"], user_id=user_id)

        assert result["success"] is True
        assert result["deleted_task_id"] == task["id"]

        # Verify it's actually gone
        list_result = await list_tasks(user_id=user_id)
        assert list_result["count"] == 0

    @pytest.mark.asyncio
    async def test_delete_task_not_found(self, mcp_db):
        from backend.services.mcp_tools import delete_task

        result = await delete_task(task_id=str(uuid4()), user_id=str(uuid4()))

        assert result["is_error"] is True
        assert "not found" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_delete_task_wrong_user(self, mcp_db):
        from backend.services.mcp_tools import add_task, delete_task

        user_a = str(uuid4())
        user_b = str(uuid4())
        task = await add_task(title="User A task", user_id=user_a)

        result = await delete_task(task_id=task["id"], user_id=user_b)

        assert result["is_error"] is True


# =============================================================================
# Phase 9: Cross-Cutting User Isolation (T048)
# =============================================================================


class TestMCPUserIsolation:
    """Verify user isolation across all MCP tools."""

    @pytest.mark.asyncio
    async def test_full_isolation(self, mcp_db):
        from backend.services.mcp_tools import (
            add_task, list_tasks, complete_task, update_task, delete_task,
        )

        user_a = str(uuid4())
        user_b = str(uuid4())

        # User A creates a task
        task = await add_task(title="Private task", user_id=user_a)

        # User B cannot list User A's tasks
        result_b = await list_tasks(user_id=user_b)
        assert result_b["count"] == 0

        # User B cannot complete User A's task
        result = await complete_task(task_id=task["id"], user_id=user_b)
        assert result["is_error"] is True

        # User B cannot update User A's task
        result = await update_task(task_id=task["id"], title="Hacked", user_id=user_b)
        assert result["is_error"] is True

        # User B cannot delete User A's task
        result = await delete_task(task_id=task["id"], user_id=user_b)
        assert result["is_error"] is True

        # User A's task is still intact
        result_a = await list_tasks(user_id=user_a)
        assert result_a["count"] == 1
        assert result_a["tasks"][0]["title"] == "Private task"
