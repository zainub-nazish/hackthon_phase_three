"""Tests for chat data integrity and user isolation (User Story 4)."""

from uuid import uuid4

import pytest
from fastapi import Path
from fastapi.testclient import TestClient

from backend.tests.conftest import create_test_conversation, create_test_message


# =============================================================================
# Fixtures for cross-user testing
# =============================================================================


@pytest.fixture
def user_a_id() -> str:
    """User A's ID."""
    return str(uuid4())


@pytest.fixture
def user_b_id() -> str:
    """User B's ID."""
    return str(uuid4())


@pytest.fixture
def isolation_client(user_a_id: str, user_b_id: str):
    """
    Test client with auth override that allows any user_id from path.

    Both user A and user B can make authenticated requests.
    """
    from backend.tests.conftest import _setup_test_app
    from backend.auth.dependencies import verify_user_owns_resource
    from backend.models.schemas import CurrentUser

    app = _setup_test_app()

    async def mock_verify_user(
        user_id: str = Path(..., description="User ID from URL path"),
    ) -> CurrentUser:
        return CurrentUser(user_id=user_id, email=f"{user_id}@test.com")

    app.dependency_overrides[verify_user_owns_resource] = mock_verify_user

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


# =============================================================================
# User Story 4: Conversation Data Integrity and Isolation
# =============================================================================


class TestCrossUserChatReturns404:
    """T028: User B cannot send message to user A's conversation."""

    def test_cross_user_chat_returns_404(
        self, isolation_client: TestClient, user_a_id: str, user_b_id: str
    ):
        """User B sends message with user A's conversation_id → 404."""
        # User A creates a conversation
        conv = create_test_conversation(isolation_client, user_a_id, "Hello from A")
        conv_id = conv["conversation_id"]

        # User B tries to send a message to user A's conversation
        response = isolation_client.post(
            f"/api/v1/users/{user_b_id}/chat",
            json={"conversation_id": conv_id, "message": "Intruder!"},
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "Not found"


class TestCrossUserConversationsReturns404:
    """T029: User B's GET /conversations only shows their own."""

    def test_cross_user_conversations_isolation(
        self, isolation_client: TestClient, user_a_id: str, user_b_id: str
    ):
        """User B calls GET /conversations and only sees their own (or null)."""
        # User A creates a conversation
        create_test_conversation(isolation_client, user_a_id, "A's conversation")

        # User B has no conversations
        response = isolation_client.get(
            f"/api/v1/users/{user_b_id}/conversations"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["conversation_id"] is None  # User B has no conversations

    def test_cross_user_conversations_each_sees_own(
        self, isolation_client: TestClient, user_a_id: str, user_b_id: str
    ):
        """Each user sees only their own conversation."""
        # Both users create conversations
        conv_a = create_test_conversation(isolation_client, user_a_id, "A's msg")
        conv_b = create_test_conversation(isolation_client, user_b_id, "B's msg")

        # User A sees only their conversation
        resp_a = isolation_client.get(f"/api/v1/users/{user_a_id}/conversations")
        assert resp_a.json()["conversation_id"] == conv_a["conversation_id"]

        # User B sees only their conversation
        resp_b = isolation_client.get(f"/api/v1/users/{user_b_id}/conversations")
        assert resp_b.json()["conversation_id"] == conv_b["conversation_id"]


class TestCrossUserMessagesReturns404:
    """T030: User B cannot GET messages for user A's conversation."""

    def test_cross_user_messages_returns_404(
        self, isolation_client: TestClient, user_a_id: str, user_b_id: str
    ):
        """User B tries to GET messages for user A's conversation → 404."""
        # User A creates a conversation
        conv = create_test_conversation(isolation_client, user_a_id, "Secret msg")
        conv_id = conv["conversation_id"]

        # User B tries to access user A's messages
        response = isolation_client.get(
            f"/api/v1/users/{user_b_id}/conversations/{conv_id}/messages"
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "Not found"


class TestAIFailurePreservesUserMessage:
    """T031: AI failure preserves user message and returns 502."""

    def test_ai_failure_preserves_user_message(
        self, isolation_client: TestClient, user_a_id: str
    ):
        """When AI agent fails, user message is persisted and 502 returned."""
        from backend.services.ai_agent import get_ai_agent_service

        # First create a conversation
        conv = create_test_conversation(isolation_client, user_a_id, "Setup")
        conv_id = conv["conversation_id"]

        # Configure agent to raise an exception
        agent = get_ai_agent_service()
        original_generate = agent.generate_response

        async def failing_generate(*args, **kwargs):
            raise RuntimeError("AI service down!")

        agent.generate_response = failing_generate

        try:
            # Send message - should fail with 502
            response = isolation_client.post(
                f"/api/v1/users/{user_a_id}/chat",
                json={"conversation_id": conv_id, "message": "This should be saved"},
            )

            assert response.status_code == 502
            assert response.json()["detail"] == "AI service unavailable"

            # Verify user message was persisted by loading messages
            msg_response = isolation_client.get(
                f"/api/v1/users/{user_a_id}/conversations/{conv_id}/messages"
            )
            assert msg_response.status_code == 200
            messages = msg_response.json()["messages"]

            # Should have: setup user msg, setup assistant msg, failed user msg
            user_messages = [m for m in messages if m["role"] == "user"]
            assert any(m["content"] == "This should be saved" for m in user_messages)

            # Should NOT have an assistant message for the failed request
            assistant_messages = [m for m in messages if m["role"] == "assistant"]
            assert len(assistant_messages) == 1  # Only the setup response
        finally:
            agent.generate_response = original_generate
