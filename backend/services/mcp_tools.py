"""MCP tool server for todo management operations.

Defines five MCP tools (add_task, list_tasks, complete_task, delete_task, update_task)
using the official MCP Python SDK. Tool handlers interact with the database through
async sessions and enforce user isolation via server-side user_id injection.

The MCP bridge (mcp_bridge.py) extracts tool schemas and dispatches tool calls
to this server. The AI agent never calls these handlers directly.
"""

from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional
from uuid import UUID

from mcp.server.fastmcp import FastMCP

from backend.config import settings


# =============================================================================
# MCP Server Instance
# =============================================================================

server = FastMCP("todo-tools")


# =============================================================================
# Database Session Helper
# =============================================================================


@asynccontextmanager
async def _get_db_session():
    """Create an async database session for tool execution."""
    from backend.database import get_async_session_maker

    async_session = get_async_session_maker()
    async with async_session() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


# =============================================================================
# MCP Tool Handlers
# =============================================================================


@server.tool()
async def add_task(title: str, user_id: str, description: Optional[str] = None) -> dict:
    """Create a new task for the user. Use this tool when the user wants to add,
    create, or make a new task. Extract the task title from the user's message.
    If the user also provides a description or details, include those as well.
    The title is required and should be a clear, concise summary of the task."""
    from backend.models.database import Task

    title = title.strip()
    if not title:
        return {"is_error": True, "error": "Task title is required"}
    if len(title) > 200:
        return {"is_error": True, "error": "Task title must be 200 characters or less"}

    if description and len(description) > 2000:
        return {"is_error": True, "error": "Task description must be 2000 characters or less"}

    async with _get_db_session() as session:
        task = Task(
            owner_id=user_id,
            title=title,
            description=description,
        )
        session.add(task)
        await session.commit()
        await session.refresh(task)

        return {
            "id": str(task.id),
            "title": task.title,
            "description": task.description,
            "completed": task.completed,
        }


@server.tool()
async def list_tasks(user_id: str, status: Optional[str] = None) -> dict:
    """List the user's tasks. Use this tool when the user wants to see, show, view,
    or check their tasks. You can filter by status: "all" shows everything, "pending"
    shows only incomplete tasks, and "completed" shows only finished tasks. Also use
    this tool when you need to find a specific task by name before performing an action
    like complete, delete, or update — this helps you get the correct task_id."""
    from backend.models.database import Task
    from sqlmodel import select

    status_filter = status or "all"

    async with _get_db_session() as session:
        query = select(Task).where(Task.owner_id == user_id)

        if status_filter == "pending":
            query = query.where(Task.completed == False)  # noqa: E712
        elif status_filter == "completed":
            query = query.where(Task.completed == True)  # noqa: E712

        query = query.order_by(Task.created_at.desc())
        result = await session.execute(query)
        tasks = result.scalars().all()

        return {
            "tasks": [
                {
                    "id": str(t.id),
                    "title": t.title,
                    "description": t.description,
                    "completed": t.completed,
                }
                for t in tasks
            ],
            "count": len(tasks),
        }


@server.tool()
async def complete_task(task_id: str, user_id: str) -> dict:
    """Mark a task as completed/done. Use this tool when the user wants to complete,
    finish, or mark a task as done. Requires the task_id (UUID) of the task to complete.
    If the user refers to a task by name instead of ID, first use list_tasks to find
    the matching task and get its task_id, then call this tool."""
    from backend.models.database import Task
    from sqlmodel import select

    if not task_id:
        return {"is_error": True, "error": "task_id is required"}

    try:
        task_uuid = UUID(task_id)
    except (ValueError, AttributeError):
        return {"is_error": True, "error": "Invalid task_id format"}

    async with _get_db_session() as session:
        query = select(Task).where(Task.id == task_uuid, Task.owner_id == user_id)
        result = await session.execute(query)
        task = result.scalar_one_or_none()

        if not task:
            return {"is_error": True, "error": "Task not found"}

        task.completed = True
        task.updated_at = datetime.utcnow()
        session.add(task)
        await session.commit()
        await session.refresh(task)

        return {
            "id": str(task.id),
            "title": task.title,
            "completed": task.completed,
        }


@server.tool()
async def delete_task(task_id: str, user_id: str) -> dict:
    """Delete/remove a task permanently. Use this tool when the user wants to delete,
    remove, or get rid of a task. Requires the task_id (UUID) of the task to delete.
    If the user refers to a task by name instead of ID, first use list_tasks to find
    the matching task and get its task_id, then call this tool. This action cannot
    be undone."""
    from backend.models.database import Task
    from sqlmodel import select

    if not task_id:
        return {"is_error": True, "error": "task_id is required"}

    try:
        task_uuid = UUID(task_id)
    except (ValueError, AttributeError):
        return {"is_error": True, "error": "Invalid task_id format"}

    async with _get_db_session() as session:
        query = select(Task).where(Task.id == task_uuid, Task.owner_id == user_id)
        result = await session.execute(query)
        task = result.scalar_one_or_none()

        if not task:
            return {"is_error": True, "error": "Task not found"}

        task_title = task.title
        await session.delete(task)
        await session.commit()

        return {
            "success": True,
            "deleted_task_id": str(task_id),
        }


@server.tool()
async def update_task(
    task_id: str,
    user_id: str,
    title: Optional[str] = None,
    description: Optional[str] = None,
) -> dict:
    """Update/modify an existing task's title or description. Use this tool when the
    user wants to change, rename, edit, or update a task. Requires the task_id (UUID)
    of the task to update, plus at least one field to change (title and/or description).
    If the user refers to a task by name instead of ID, first use list_tasks to find
    the matching task and get its task_id, then call this tool."""
    from backend.models.database import Task
    from sqlmodel import select

    if not task_id:
        return {"is_error": True, "error": "task_id is required"}

    if title is None and description is None:
        return {"is_error": True, "error": "At least one of title or description must be provided"}

    if title is not None:
        title = title.strip()
        if not title:
            return {"is_error": True, "error": "Title cannot be empty"}
        if len(title) > 200:
            return {"is_error": True, "error": "Title must be 200 characters or less"}

    if description is not None and len(description) > 2000:
        return {"is_error": True, "error": "Description must be 2000 characters or less"}

    try:
        task_uuid = UUID(task_id)
    except (ValueError, AttributeError):
        return {"is_error": True, "error": "Invalid task_id format"}

    async with _get_db_session() as session:
        query = select(Task).where(Task.id == task_uuid, Task.owner_id == user_id)
        result = await session.execute(query)
        task = result.scalar_one_or_none()

        if not task:
            return {"is_error": True, "error": "Task not found"}

        if title is not None:
            task.title = title
        if description is not None:
            task.description = description

        task.updated_at = datetime.utcnow()
        session.add(task)
        await session.commit()
        await session.refresh(task)

        return {
            "id": str(task.id),
            "title": task.title,
            "description": task.description,
            "completed": task.completed,
        }


# =============================================================================
# Stdio Entry Point (for MCPServerStdio in OpenAI Agents SDK)
# =============================================================================

if __name__ == "__main__":
    server.run(transport="stdio")
