"""Chat API routes with conversation persistence and AI agent invocation."""

import json
import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Path

logger = logging.getLogger(__name__)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from backend.auth.dependencies import verify_user_owns_resource
from backend.config import settings
from backend.models.schemas import (
    CurrentUser,
    ChatRequest,
    ChatResponse,
    ToolCallResponse,
    MessageResponse,
    MessagesResponse,
    ConversationResponse,
)
from backend.services.ai_agent import AIAgentService, get_ai_agent_service

router = APIRouter(
    prefix="/api/v1/users/{user_id}",
    tags=["Chat"],
)


# =============================================================================
# Database Session Dependency
# =============================================================================


async def get_db_session():
    """Get database session - uses DB if configured, otherwise raises error."""
    if not settings.database_url:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not configured",
        )
    from backend.database import get_session
    async for session in get_session():
        yield session


# =============================================================================
# Chat Endpoints
# =============================================================================

MAX_CONTEXT_MESSAGES = 20


@router.post("/chat", response_model=ChatResponse)
async def send_message(
    chat_request: ChatRequest,
    user_id: str = Path(..., description="User ID"),
    current_user: CurrentUser = Depends(verify_user_owns_resource),
    session: AsyncSession = Depends(get_db_session),
    agent: AIAgentService = Depends(get_ai_agent_service),
) -> ChatResponse:
    """Send a chat message and receive an AI response.

    Creates a new conversation if conversation_id is null,
    otherwise continues an existing conversation.
    """
    from backend.models.database import Conversation, Message, ToolCall

    # Strip whitespace and validate non-empty
    stripped_message = chat_request.message.strip()
    if not stripped_message:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message cannot be empty",
        )

    # Create or verify conversation
    if chat_request.conversation_id is not None:
        # Verify conversation exists and belongs to user
        query = select(Conversation).where(
            Conversation.id == chat_request.conversation_id,
            Conversation.owner_id == user_id,
        )
        result = await session.execute(query)
        conversation = result.scalar_one_or_none()
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Not found",
            )
    else:
        # Create new conversation
        conversation = Conversation(owner_id=user_id)
        session.add(conversation)
        await session.flush()  # Get the ID without committing

    # Persist user message BEFORE calling AI agent (FR-003)
    user_msg = Message(
        conversation_id=conversation.id,
        role="user",
        content=stripped_message,
    )
    session.add(user_msg)
    await session.commit()
    await session.refresh(conversation)

    # Load conversation context (last N messages)
    context_query = (
        select(Message)
        .where(Message.conversation_id == conversation.id)
        .order_by(Message.created_at.desc())
        .limit(MAX_CONTEXT_MESSAGES)
    )
    context_result = await session.execute(context_query)
    context_messages = list(reversed(context_result.scalars().all()))

    messages_for_agent = [
        {"role": msg.role, "content": msg.content}
        for msg in context_messages
    ]

    # Call AI agent
    try:
        agent_response = await agent.generate_response(messages_for_agent, user_id)
    except Exception as e:
        import traceback
        print(f"[CHAT ERROR] AI agent error: {e}")
        traceback.print_exc()
        # User message already persisted - update conversation timestamp and return error
        conversation.updated_at = datetime.utcnow()
        session.add(conversation)
        await session.commit()
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="AI service unavailable",
        )

    # Persist assistant message
    assistant_msg = Message(
        conversation_id=conversation.id,
        role="assistant",
        content=agent_response.content,
    )
    session.add(assistant_msg)

    # Persist tool calls if any
    for tc in agent_response.tool_calls:
        tool_call = ToolCall(
            message_id=assistant_msg.id,
            tool_name=tc.tool_name,
            parameters=tc.parameters,
            result=tc.result,
            status=tc.status,
        )
        session.add(tool_call)

    # Update conversation timestamp
    conversation.updated_at = datetime.utcnow()
    session.add(conversation)
    await session.commit()

    return ChatResponse(
        conversation_id=conversation.id,
        response=agent_response.content,
        tool_calls=[
            ToolCallResponse(
                tool_name=tc.tool_name,
                parameters=tc.parameters,
                result=tc.result,
                status=tc.status,
            )
            for tc in agent_response.tool_calls
        ],
    )


@router.get("/conversations", response_model=ConversationResponse)
async def get_recent_conversation(
    user_id: str = Path(..., description="User ID"),
    current_user: CurrentUser = Depends(verify_user_owns_resource),
    session: AsyncSession = Depends(get_db_session),
) -> ConversationResponse:
    """Get the user's most recent conversation."""
    from backend.models.database import Conversation

    query = (
        select(Conversation)
        .where(Conversation.owner_id == user_id)
        .order_by(Conversation.updated_at.desc())
        .limit(1)
    )
    result = await session.execute(query)
    conversation = result.scalar_one_or_none()

    if not conversation:
        return ConversationResponse(conversation_id=None)

    return ConversationResponse(
        conversation_id=conversation.id,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
    )


@router.get(
    "/conversations/{conversation_id}/messages",
    response_model=MessagesResponse,
)
async def get_conversation_messages(
    user_id: str = Path(..., description="User ID"),
    conversation_id: UUID = Path(..., description="Conversation ID"),
    current_user: CurrentUser = Depends(verify_user_owns_resource),
    session: AsyncSession = Depends(get_db_session),
) -> MessagesResponse:
    """Get all messages for a conversation in chronological order."""
    from backend.models.database import Conversation, Message

    # Verify conversation exists and belongs to user
    conv_query = select(Conversation).where(
        Conversation.id == conversation_id,
        Conversation.owner_id == user_id,
    )
    conv_result = await session.execute(conv_query)
    conversation = conv_result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not found",
        )

    # Load all messages chronologically
    msg_query = (
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
    )
    msg_result = await session.execute(msg_query)
    messages = msg_result.scalars().all()

    return MessagesResponse(
        conversation_id=conversation_id,
        messages=[MessageResponse.model_validate(m) for m in messages],
    )
