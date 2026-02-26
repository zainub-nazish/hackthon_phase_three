"""Pydantic models for request/response schemas."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


# =============================================================================
# Authentication Models
# =============================================================================

class TokenPayload(BaseModel):
    """JWT claims structure from Better Auth."""

    sub: str = Field(..., description="User ID (subject claim)")
    exp: int = Field(..., description="Expiration timestamp (Unix)")
    iat: int = Field(..., description="Issued-at timestamp (Unix)")
    email: Optional[str] = Field(None, description="User email")
    session_id: Optional[str] = Field(None, alias="sessionId")

    model_config = {"populate_by_name": True}


class CurrentUser(BaseModel):
    """Verified user extracted from JWT token."""

    user_id: str = Field(..., description="Authenticated user ID from JWT sub claim")
    email: Optional[str] = Field(None, description="User email if available")


class SessionResponse(BaseModel):
    """Response for session verification endpoint."""

    user_id: str = Field(..., description="Authenticated user ID")
    email: Optional[str] = Field(None, description="User email if available")
    authenticated: bool = Field(default=True, description="Authentication status")


# =============================================================================
# Error Models
# =============================================================================

class ErrorResponse(BaseModel):
    """Standard error response."""

    detail: str = Field(..., description="Human-readable error message")


# =============================================================================
# Task Models
# =============================================================================

class TaskBase(BaseModel):
    """Base task attributes."""

    title: str = Field(..., min_length=1, max_length=200, description="Task title")
    description: Optional[str] = Field(None, max_length=2000, description="Task details")
    completed: bool = Field(default=False, description="Completion status")


class TaskCreate(TaskBase):
    """Request body for creating a task."""

    pass


class TaskUpdate(BaseModel):
    """Request body for updating a task (partial update)."""

    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    completed: Optional[bool] = None


class TaskResponse(TaskBase):
    """Response body for a task."""

    id: UUID = Field(..., description="Unique task identifier")
    owner_id: str = Field(..., description="User ID of task owner")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = {"from_attributes": True}


class TaskListResponse(BaseModel):
    """Response body for listing tasks."""

    items: list[TaskResponse] = Field(default_factory=list, description="List of tasks")
    total: int = Field(..., description="Total number of tasks")
    limit: Optional[int] = Field(None, description="Requested limit")
    offset: Optional[int] = Field(None, description="Requested offset")


# =============================================================================
# Chat Models (007-chat-api)
# =============================================================================


class ChatRequest(BaseModel):
    """Request body for sending a chat message."""

    conversation_id: Optional[UUID] = Field(
        None, description="UUID of existing conversation, or null to create new"
    )
    message: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="User's natural language message"
    )


class ToolCallResponse(BaseModel):
    """Response body for a single tool call made by the AI agent."""

    tool_name: str = Field(..., description="Name of the MCP tool invoked")
    parameters: str = Field(..., description="JSON-encoded tool parameters")
    result: str = Field(..., description="JSON-encoded tool result")
    status: str = Field(..., description="'success' or 'error'")


class ChatResponse(BaseModel):
    """Response body for a chat message."""

    conversation_id: UUID = Field(..., description="Conversation UUID (new if first message)")
    response: str = Field(..., description="AI assistant's response text")
    tool_calls: list[ToolCallResponse] = Field(
        default_factory=list, description="Tool calls made during this response"
    )


class MessageResponse(BaseModel):
    """Response body for a single message."""

    id: UUID = Field(..., description="Unique message identifier")
    conversation_id: UUID = Field(..., description="Parent conversation ID")
    role: str = Field(..., description="Sender role: 'user' or 'assistant'")
    content: str = Field(..., description="Message text content")
    created_at: datetime = Field(..., description="Message timestamp")

    model_config = {"from_attributes": True}


class MessagesResponse(BaseModel):
    """Response body for conversation messages."""

    conversation_id: UUID = Field(..., description="Conversation UUID")
    messages: list[MessageResponse] = Field(
        default_factory=list, description="Messages in chronological order"
    )


class ConversationResponse(BaseModel):
    """Response body for conversation metadata."""

    conversation_id: Optional[UUID] = Field(
        None, description="Most recent conversation UUID, or null if none"
    )
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last activity timestamp")
