"""Test configuration and fixtures for JWT authentication and database tests."""

import asyncio
import time
from datetime import datetime, timezone
from typing import AsyncGenerator, Generator
from uuid import uuid4

import pytest
import pytest_asyncio
from fastapi import Path
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient
from jose import jwt
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

# Test secret - only for testing, never use in production
TEST_SECRET = "test-secret-key-for-jwt-testing-must-be-32-chars-or-more"
TEST_ALGORITHM = "HS256"

# Test database URL - use SQLite for testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_user_id() -> str:
    """Generate a test user ID."""
    return str(uuid4())


@pytest.fixture
def another_user_id() -> str:
    """Generate another test user ID for cross-user testing."""
    return str(uuid4())


@pytest.fixture
def valid_token(test_user_id: str) -> str:
    """
    Create a valid JWT token for testing.

    Token contains:
    - sub: user ID
    - exp: 1 hour from now
    - iat: current time
    - email: test email
    """
    now = int(time.time())
    payload = {
        "sub": test_user_id,
        "exp": now + 3600,  # 1 hour from now
        "iat": now,
        "email": "test@example.com",
    }
    return jwt.encode(payload, TEST_SECRET, algorithm=TEST_ALGORITHM)


@pytest.fixture
def another_user_token(another_user_id: str) -> str:
    """Create a valid JWT token for another user (cross-user testing)."""
    now = int(time.time())
    payload = {
        "sub": another_user_id,
        "exp": now + 3600,
        "iat": now,
        "email": "another@example.com",
    }
    return jwt.encode(payload, TEST_SECRET, algorithm=TEST_ALGORITHM)


@pytest.fixture
def expired_token(test_user_id: str) -> str:
    """
    Create an expired JWT token for testing expiration handling.

    Token expired 1 hour ago.
    """
    now = int(time.time())
    payload = {
        "sub": test_user_id,
        "exp": now - 3600,  # Expired 1 hour ago
        "iat": now - 7200,  # Issued 2 hours ago
        "email": "test@example.com",
    }
    return jwt.encode(payload, TEST_SECRET, algorithm=TEST_ALGORITHM)


@pytest.fixture
def token_near_expiry(test_user_id: str) -> str:
    """
    Create a token that is about to expire (within clock skew tolerance).

    Token expires in 5 seconds (within 10s leeway).
    """
    now = int(time.time())
    payload = {
        "sub": test_user_id,
        "exp": now + 5,  # Expires in 5 seconds
        "iat": now - 3595,  # Issued almost 1 hour ago
        "email": "test@example.com",
    }
    return jwt.encode(payload, TEST_SECRET, algorithm=TEST_ALGORITHM)


@pytest.fixture
def token_within_clock_skew(test_user_id: str) -> str:
    """
    Create a token that appears expired but is within clock skew tolerance.

    Token "expired" 5 seconds ago, but should still be valid with 10s leeway.
    """
    now = int(time.time())
    payload = {
        "sub": test_user_id,
        "exp": now - 5,  # "Expired" 5 seconds ago
        "iat": now - 3605,
        "email": "test@example.com",
    }
    return jwt.encode(payload, TEST_SECRET, algorithm=TEST_ALGORITHM)


@pytest.fixture
def malformed_token() -> str:
    """Create a malformed token (invalid JWT structure)."""
    return "not.a.valid.jwt.token"


@pytest.fixture
def wrong_signature_token(test_user_id: str) -> str:
    """Create a token signed with wrong secret."""
    now = int(time.time())
    payload = {
        "sub": test_user_id,
        "exp": now + 3600,
        "iat": now,
        "email": "test@example.com",
    }
    return jwt.encode(payload, "wrong-secret-key-that-is-definitely-different", algorithm=TEST_ALGORITHM)


@pytest.fixture
def tampered_token(valid_token: str) -> str:
    """
    Create a tampered token by modifying the payload after signing.

    Changes the payload portion of the JWT without re-signing.
    """
    parts = valid_token.split(".")
    # Modify the payload (middle part) - this breaks the signature
    import base64
    payload_b64 = parts[1]
    # Add padding if needed
    padding = 4 - len(payload_b64) % 4
    if padding != 4:
        payload_b64 += "=" * padding
    # Decode, modify, re-encode
    payload_bytes = base64.urlsafe_b64decode(payload_b64)
    # Just modify a byte to tamper
    tampered_bytes = payload_bytes[:-1] + bytes([payload_bytes[-1] ^ 0xFF])
    tampered_b64 = base64.urlsafe_b64encode(tampered_bytes).decode().rstrip("=")
    return f"{parts[0]}.{tampered_b64}.{parts[2]}"


@pytest.fixture
def token_missing_sub() -> str:
    """Create a token without the required 'sub' claim."""
    now = int(time.time())
    payload = {
        "exp": now + 3600,
        "iat": now,
        "email": "test@example.com",
        # Note: 'sub' is intentionally missing
    }
    return jwt.encode(payload, TEST_SECRET, algorithm=TEST_ALGORITHM)


@pytest.fixture
def token_missing_exp(test_user_id: str) -> str:
    """Create a token without the required 'exp' claim."""
    now = int(time.time())
    payload = {
        "sub": test_user_id,
        "iat": now,
        "email": "test@example.com",
        # Note: 'exp' is intentionally missing
    }
    # jwt.encode doesn't take options, it just encodes what we give it
    return jwt.encode(payload, TEST_SECRET, algorithm=TEST_ALGORITHM)


@pytest.fixture
def token_missing_iat(test_user_id: str) -> str:
    """Create a token without the required 'iat' claim."""
    now = int(time.time())
    payload = {
        "sub": test_user_id,
        "exp": now + 3600,
        "email": "test@example.com",
        # Note: 'iat' is intentionally missing
    }
    return jwt.encode(payload, TEST_SECRET, algorithm=TEST_ALGORITHM)


def _setup_test_app():
    """Reload modules and return a fresh app with test database."""
    import os

    os.environ["BETTER_AUTH_SECRET"] = TEST_SECRET
    os.environ["DATABASE_URL"] = TEST_DATABASE_URL

    import importlib
    import backend.config
    import backend.database
    import backend.services.mcp_tools
    import backend.services.mcp_bridge
    import backend.services.ai_agent
    import backend.routes.tasks
    import backend.routes.chat
    import backend.main

    importlib.reload(backend.config)
    importlib.reload(backend.database)
    importlib.reload(backend.services.mcp_tools)
    importlib.reload(backend.services.mcp_bridge)
    importlib.reload(backend.services.ai_agent)
    importlib.reload(backend.routes.tasks)
    importlib.reload(backend.routes.chat)
    importlib.reload(backend.main)

    from backend.main import app
    return app


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """
    Create a test client with mocked settings and test database.

    Patches BETTER_AUTH_SECRET and DATABASE_URL for testing.
    Uses SQLite in-memory database for fast, isolated tests.
    """
    app = _setup_test_app()

    with TestClient(app) as c:
        yield c


@pytest.fixture
def chat_client(test_user_id: str) -> Generator[TestClient, None, None]:
    """
    Create a test client with mocked auth for chat endpoint tests.

    Overrides verify_user_owns_resource to bypass DB session lookup,
    allowing tests to focus on chat logic rather than auth.
    """
    app = _setup_test_app()

    from backend.auth.dependencies import verify_user_owns_resource
    from backend.models.schemas import CurrentUser

    async def mock_verify_user(
        user_id: str = Path(..., description="User ID from URL path"),
    ) -> CurrentUser:
        return CurrentUser(user_id=user_id, email="test@example.com")

    app.dependency_overrides[verify_user_owns_resource] = mock_verify_user

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


@pytest.fixture
def raw_chat_client() -> Generator[TestClient, None, None]:
    """
    Test client WITHOUT auth override for testing 401 responses.

    Auth will fail because session/user tables don't exist in test DB.
    """
    app = _setup_test_app()

    with TestClient(app) as c:
        yield c


@pytest_asyncio.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """
    Create an async test client for async tests.

    Uses SQLite in-memory database for fast, isolated tests.
    """
    app = _setup_test_app()

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        yield client


@pytest.fixture
def auth_header(valid_token: str) -> dict[str, str]:
    """Create Authorization header with valid token."""
    return {"Authorization": f"Bearer {valid_token}"}


@pytest.fixture
def another_user_auth_header(another_user_token: str) -> dict[str, str]:
    """Create Authorization header for another user."""
    return {"Authorization": f"Bearer {another_user_token}"}


# =============================================================================
# Chat Test Helpers (T010)
# =============================================================================


def create_test_conversation(client: TestClient, user_id: str, message: str = "Hello") -> dict:
    """Create a test conversation by sending a message. Returns ChatResponse dict."""
    response = client.post(
        f"/api/v1/users/{user_id}/chat",
        json={"conversation_id": None, "message": message},
    )
    assert response.status_code == 200
    return response.json()


def create_test_message(
    client: TestClient, user_id: str, conversation_id: str, message: str
) -> dict:
    """Send a message to an existing conversation. Returns ChatResponse dict."""
    response = client.post(
        f"/api/v1/users/{user_id}/chat",
        json={"conversation_id": conversation_id, "message": message},
    )
    assert response.status_code == 200
    return response.json()


# =============================================================================
# AI Agent Test Helpers (T014)
# =============================================================================


@pytest_asyncio.fixture
async def agent_db(tmp_path):
    """Initialize test database for direct tool executor testing.

    Creates a file-based SQLite engine, creates tables, and patches
    _get_db_session in the ai_agent module to use this test engine.
    Uses unittest.mock.patch for reliable module-level patching.
    """
    from contextlib import asynccontextmanager
    from unittest.mock import patch

    db_file = tmp_path / "agent_test.db"
    db_url = f"sqlite+aiosqlite:///{db_file}"

    engine = create_async_engine(db_url)
    test_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    # Import models to register them with SQLModel.metadata BEFORE create_all
    import backend.models.database  # noqa: F401 — registers Task, Conversation, Message, ToolCall

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    @asynccontextmanager
    async def _test_get_db_session():
        async with test_session_maker() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise

    with patch("backend.services.mcp_tools._get_db_session", _test_get_db_session):
        yield

    await engine.dispose()


@pytest_asyncio.fixture
async def mcp_db(tmp_path):
    """Initialize test database for MCP tool handler testing.

    Same pattern as agent_db but patches _get_db_session in the
    mcp_tools module (where MCP tool handlers live).
    """
    from contextlib import asynccontextmanager
    from unittest.mock import patch

    db_file = tmp_path / "mcp_test.db"
    db_url = f"sqlite+aiosqlite:///{db_file}"

    engine = create_async_engine(db_url)
    test_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    import backend.models.database  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    @asynccontextmanager
    async def _test_get_db_session():
        async with test_session_maker() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise

    with patch("backend.services.mcp_tools._get_db_session", _test_get_db_session):
        yield

    await engine.dispose()


def make_tool_use_response(tool_name: str, tool_input: dict, tool_use_id: str = "toolu_test123"):
    """Create a mock Claude response with stop_reason='tool_use' and a tool_use content block."""
    from unittest.mock import MagicMock

    tool_block = MagicMock()
    tool_block.type = "tool_use"
    tool_block.name = tool_name
    tool_block.input = tool_input
    tool_block.id = tool_use_id

    response = MagicMock()
    response.stop_reason = "tool_use"
    response.content = [tool_block]

    return response


def make_text_response(text: str):
    """Create a mock Claude response with stop_reason='end_turn' and a text content block."""
    from unittest.mock import MagicMock

    text_block = MagicMock()
    text_block.type = "text"
    text_block.text = text

    response = MagicMock()
    response.stop_reason = "end_turn"
    response.content = [text_block]

    return response
