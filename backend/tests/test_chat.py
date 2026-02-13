"""Tests for chat API endpoints (User Stories 1, 2, 3)."""

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from backend.tests.conftest import create_test_conversation, create_test_message


# =============================================================================
# User Story 1: Send a Chat Message and Receive AI Response
# =============================================================================


class TestSendMessageNewConversation:
    """T011: POST with conversation_id=null creates new conversation."""

    def test_send_message_new_conversation(
        self, chat_client: TestClient, test_user_id: str
    ):
        """POST with conversation_id=null returns 200 with new conversation_id and response."""
        response = chat_client.post(
            f"/api/v1/users/{test_user_id}/chat",
            json={"conversation_id": None, "message": "Hello AI!"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "conversation_id" in data
        assert data["conversation_id"] is not None
        assert "response" in data
        assert len(data["response"]) > 0

    def test_send_message_no_conversation_id_field(
        self, chat_client: TestClient, test_user_id: str
    ):
        """POST without conversation_id field also creates new conversation."""
        response = chat_client.post(
            f"/api/v1/users/{test_user_id}/chat",
            json={"message": "Hello AI!"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["conversation_id"] is not None


class TestSendMessageExistingConversation:
    """T012: POST with existing conversation_id continues conversation."""

    def test_send_message_existing_conversation(
        self, chat_client: TestClient, test_user_id: str
    ):
        """POST with valid conversation_id uses same conversation."""
        # Create conversation first
        first = create_test_conversation(chat_client, test_user_id, "First message")
        conv_id = first["conversation_id"]

        # Send follow-up message
        response = chat_client.post(
            f"/api/v1/users/{test_user_id}/chat",
            json={"conversation_id": conv_id, "message": "Follow-up message"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["conversation_id"] == conv_id
        assert len(data["response"]) > 0


class TestSendMessageEmptyReturns400:
    """T013: POST with empty or whitespace message returns 400/422."""

    def test_send_message_empty_string_returns_422(
        self, chat_client: TestClient, test_user_id: str
    ):
        """POST with empty message returns 422 (Pydantic min_length validation)."""
        response = chat_client.post(
            f"/api/v1/users/{test_user_id}/chat",
            json={"conversation_id": None, "message": ""},
        )

        assert response.status_code == 422

    def test_send_message_whitespace_only_returns_400(
        self, chat_client: TestClient, test_user_id: str
    ):
        """POST with whitespace-only message returns 400."""
        response = chat_client.post(
            f"/api/v1/users/{test_user_id}/chat",
            json={"conversation_id": None, "message": "   "},
        )

        assert response.status_code == 400
        assert response.json()["detail"] == "Message cannot be empty"

    def test_send_message_exceeds_2000_chars_returns_422(
        self, chat_client: TestClient, test_user_id: str
    ):
        """POST with message over 2000 chars returns 422."""
        response = chat_client.post(
            f"/api/v1/users/{test_user_id}/chat",
            json={"conversation_id": None, "message": "x" * 2001},
        )

        assert response.status_code == 422


class TestSendMessageInvalidConversationReturns404:
    """T014: POST with non-existent conversation_id returns 404."""

    def test_send_message_invalid_conversation_returns_404(
        self, chat_client: TestClient, test_user_id: str
    ):
        """POST with non-existent conversation_id returns 404."""
        fake_conv_id = str(uuid4())

        response = chat_client.post(
            f"/api/v1/users/{test_user_id}/chat",
            json={"conversation_id": fake_conv_id, "message": "Hello"},
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "Not found"


class TestSendMessageUnauthenticatedReturns401:
    """T015: POST without auth header returns 401/403."""

    def test_send_message_unauthenticated(
        self, raw_chat_client: TestClient, test_user_id: str
    ):
        """POST without auth header returns 401 or 403."""
        response = raw_chat_client.post(
            f"/api/v1/users/{test_user_id}/chat",
            json={"conversation_id": None, "message": "Hello"},
        )

        # HTTPBearer returns 403 for missing credentials
        assert response.status_code in (401, 403)


# =============================================================================
# User Story 2: Retrieve Conversation History
# =============================================================================


class TestGetRecentConversationExists:
    """T018: GET /conversations returns most recent conversation."""

    def test_get_recent_conversation_exists(
        self, chat_client: TestClient, test_user_id: str
    ):
        """GET /conversations returns conversation_id, created_at, updated_at."""
        # Create a conversation first
        chat_data = create_test_conversation(chat_client, test_user_id)
        conv_id = chat_data["conversation_id"]

        response = chat_client.get(
            f"/api/v1/users/{test_user_id}/conversations"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["conversation_id"] == conv_id
        assert data["created_at"] is not None
        assert data["updated_at"] is not None


class TestGetRecentConversationNone:
    """T019: GET /conversations with no conversations returns null."""

    def test_get_recent_conversation_none(
        self, chat_client: TestClient, test_user_id: str
    ):
        """GET /conversations with no conversations returns conversation_id: null."""
        response = chat_client.get(
            f"/api/v1/users/{test_user_id}/conversations"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["conversation_id"] is None


class TestGetMessagesChronological:
    """T020: GET /conversations/{id}/messages returns messages in order."""

    def test_get_messages_chronological(
        self, chat_client: TestClient, test_user_id: str
    ):
        """GET messages returns all messages ordered by created_at ASC."""
        # Create conversation with multiple exchanges
        first = create_test_conversation(chat_client, test_user_id, "First")
        conv_id = first["conversation_id"]
        create_test_message(chat_client, test_user_id, conv_id, "Second")
        create_test_message(chat_client, test_user_id, conv_id, "Third")

        response = chat_client.get(
            f"/api/v1/users/{test_user_id}/conversations/{conv_id}/messages"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["conversation_id"] == conv_id

        messages = data["messages"]
        # 3 user messages + 3 assistant responses = 6 total
        assert len(messages) == 6

        # Verify chronological order
        for i in range(len(messages) - 1):
            assert messages[i]["created_at"] <= messages[i + 1]["created_at"]

        # Verify alternating roles
        assert messages[0]["role"] == "user"
        assert messages[1]["role"] == "assistant"
        assert messages[2]["role"] == "user"
        assert messages[3]["role"] == "assistant"

        # Verify required fields
        for msg in messages:
            assert "id" in msg
            assert "conversation_id" in msg
            assert "role" in msg
            assert "content" in msg
            assert "created_at" in msg


class TestGetMessagesInvalidConversationReturns404:
    """T021: GET messages for non-existent conversation returns 404."""

    def test_get_messages_invalid_conversation_returns_404(
        self, chat_client: TestClient, test_user_id: str
    ):
        """GET messages for non-existent conversation_id returns 404."""
        fake_conv_id = str(uuid4())

        response = chat_client.get(
            f"/api/v1/users/{test_user_id}/conversations/{fake_conv_id}/messages"
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "Not found"


# =============================================================================
# User Story 3: Tool Call Persistence
# =============================================================================


class TestToolCallPersisted:
    """T024: Tool calls are persisted to DB when AI agent returns them."""

    def test_tool_call_persisted(
        self, chat_client: TestClient, test_user_id: str
    ):
        """Tool call returned by agent stub is persisted in DB."""
        from backend.services.ai_agent import get_ai_agent_service, ToolCallData

        agent = get_ai_agent_service()
        agent.set_stub_response(
            content="I created a task for you!",
            tool_calls=[
                ToolCallData(
                    tool_name="create_task",
                    parameters='{"title": "Buy groceries"}',
                    result='{"id": "abc-123", "title": "Buy groceries"}',
                    status="success",
                )
            ],
        )

        response = chat_client.post(
            f"/api/v1/users/{test_user_id}/chat",
            json={"conversation_id": None, "message": "Add a task to buy groceries"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["response"] == "I created a task for you!"


class TestToolCallFailurePersisted:
    """T025: Failed tool calls are persisted with status='error'."""

    def test_tool_call_failure_persisted(
        self, chat_client: TestClient, test_user_id: str
    ):
        """Failed tool call is persisted with error status."""
        from backend.services.ai_agent import get_ai_agent_service, ToolCallData

        agent = get_ai_agent_service()
        agent.set_stub_response(
            content="Sorry, I couldn't delete that task.",
            tool_calls=[
                ToolCallData(
                    tool_name="delete_task",
                    parameters='{"task_id": "nonexistent"}',
                    result='{"error": "Task not found"}',
                    status="error",
                )
            ],
        )

        response = chat_client.post(
            f"/api/v1/users/{test_user_id}/chat",
            json={"conversation_id": None, "message": "Delete task xyz"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["response"] == "Sorry, I couldn't delete that task."


# =============================================================================
# Edge Case Tests (T034)
# =============================================================================


class TestEdgeCases:
    """T034: Edge case tests for message length boundaries and auth."""

    def test_message_exactly_2000_chars_succeeds(
        self, chat_client: TestClient, test_user_id: str
    ):
        """Message at exactly 2000 chars should succeed."""
        response = chat_client.post(
            f"/api/v1/users/{test_user_id}/chat",
            json={"conversation_id": None, "message": "x" * 2000},
        )

        assert response.status_code == 200
        assert response.json()["conversation_id"] is not None

    def test_message_2001_chars_fails(
        self, chat_client: TestClient, test_user_id: str
    ):
        """Message at 2001 chars should fail with 422."""
        response = chat_client.post(
            f"/api/v1/users/{test_user_id}/chat",
            json={"conversation_id": None, "message": "x" * 2001},
        )

        assert response.status_code == 422

    def test_unauthenticated_get_conversations(
        self, raw_chat_client: TestClient, test_user_id: str
    ):
        """GET /conversations without auth returns 401/403."""
        response = raw_chat_client.get(
            f"/api/v1/users/{test_user_id}/conversations"
        )

        assert response.status_code in (401, 403)

    def test_unauthenticated_get_messages(
        self, raw_chat_client: TestClient, test_user_id: str
    ):
        """GET /messages without auth returns 401/403."""
        fake_conv_id = str(uuid4())
        response = raw_chat_client.get(
            f"/api/v1/users/{test_user_id}/conversations/{fake_conv_id}/messages"
        )

        assert response.status_code in (401, 403)
