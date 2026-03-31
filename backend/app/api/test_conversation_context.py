"""Test Conversation Context API endpoints (Task 5: API Endpoints).

Story 11-1: Conversation Context Memory
Tests for conversation context API endpoints.
"""

from datetime import datetime, timezone, timedelta

import pytest
from fastapi import status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation_context import ConversationContext


@pytest.fixture
async def client(async_client):
    """Use async_client with test mode header for auth bypass and CSRF tokens."""
    # Wrap the client to add X-Test-Mode header to all requests
    class TestClientWrapper:
        def __init__(self, client):
            self._client = client
            self.headers = {"X-Test-Mode": "true"}
            self.csrf_token = None
            self.csrf_cookies = {}

        async def get_csrf_token(self):
            """Get a fresh CSRF token for testing."""
            response = await self._client.get("/api/v1/csrf-token")
            assert response.status_code == 200
            data = response.json()
            self.csrf_token = data["csrf_token"]

            # Extract CSRF cookie from response
            set_cookie = response.headers.get("set-cookie", "")
            if "csrf_token=" in set_cookie:
                # Parse the cookie value (simple extraction)
                import re
                match = re.search(r'csrf_token=([^;]+)', set_cookie)
                if match:
                    self.csrf_cookies["csrf_token"] = match.group(1)

            return self.csrf_token

        async def get(self, url, **kwargs):
            headers = kwargs.get("headers", {})
            headers.update(self.headers)
            # Add CSRF token if available
            if self.csrf_token:
                headers["X-CSRF-Token"] = self.csrf_token
            kwargs["headers"] = headers

            # Add CSRF cookies if available
            if self.csrf_cookies:
                kwargs["cookies"] = kwargs.get("cookies", {})
                kwargs["cookies"].update(self.csrf_cookies)

            return await self._client.get(url, **kwargs)

        async def put(self, url, **kwargs):
            headers = kwargs.get("headers", {})
            headers.update(self.headers)
            # Add CSRF token if available
            if self.csrf_token:
                headers["X-CSRF-Token"] = self.csrf_token
            kwargs["headers"] = headers

            # Add CSRF cookies if available
            if self.csrf_cookies:
                kwargs["cookies"] = kwargs.get("cookies", {})
                kwargs["cookies"].update(self.csrf_cookies)

            return await self._client.put(url, **kwargs)

        async def post(self, url, **kwargs):
            headers = kwargs.get("headers", {})
            headers.update(self.headers)
            # Add CSRF token if available
            if self.csrf_token:
                headers["X-CSRF-Token"] = self.csrf_token
            kwargs["headers"] = headers

            # Add CSRF cookies if available
            if self.csrf_cookies:
                kwargs["cookies"] = kwargs.get("cookies", {})
                kwargs["cookies"].update(self.csrf_cookies)

            return await self._client.post(url, **kwargs)

        async def delete(self, url, **kwargs):
            headers = kwargs.get("headers", {})
            headers.update(self.headers)
            # Add CSRF token if available
            if self.csrf_token:
                headers["X-CSRF-Token"] = self.csrf_token
            kwargs["headers"] = headers

            # Add CSRF cookies if available
            if self.csrf_cookies:
                kwargs["cookies"] = kwargs.get("cookies", {})
                kwargs["cookies"].update(self.csrf_cookies)

            return await self._client.delete(url, **kwargs)

    return TestClientWrapper(async_client)


@pytest.fixture
async def db_session_with_conversation(db_session):
    """Set up test database with conversation."""
    # Insert merchant
    sql_merchant = text("""
        INSERT INTO merchants (merchant_key, platform, status, personality, store_provider, onboarding_mode, created_at, updated_at)
        VALUES ('test_ctx_api', 'widget', 'active', 'friendly', 'none', 'general', NOW(), NOW())
        ON CONFLICT (merchant_key) DO UPDATE SET platform = EXCLUDED.platform
        RETURNING id
    """)
    result = await db_session.execute(sql_merchant)
    merchant_id = result.fetchone()[0]

    # Create conversation
    sql_conversation = text(f"""
        INSERT INTO conversations (merchant_id, platform, platform_sender_id, status, created_at, updated_at)
        VALUES ({merchant_id}, 'widget', 'test_customer_api', 'active', NOW(), NOW())
        RETURNING id
    """)
    result = await db_session.execute(sql_conversation)
    conversation_id = result.fetchone()[0]

    await db_session.commit()

    yield {
        "merchant_id": merchant_id,
        "conversation_id": conversation_id,
        "db": db_session,
    }

    # Cleanup
    await db_session.execute(
        text(f"DELETE FROM conversation_context WHERE conversation_id = {conversation_id}")
    )
    await db_session.execute(text(f"DELETE FROM conversations WHERE id = {conversation_id}"))
    await db_session.execute(text("DELETE FROM merchants WHERE merchant_key = 'test_ctx_api'"))
    await db_session.commit()


class TestGetConversationContext:
    """Test GET /api/v1/conversations/{id}/context endpoint."""

    @pytest.mark.asyncio
    async def test_get_context_success(self, client, db_session_with_conversation):
        """Test successfully retrieving conversation context."""
        merchant_id = db_session_with_conversation["merchant_id"]
        conversation_id = db_session_with_conversation["conversation_id"]
        db = db_session_with_conversation["db"]

        # Setup: Create context
        context = ConversationContext(
            conversation_id=conversation_id,
            merchant_id=merchant_id,
            mode="ecommerce",
            context_data={"viewed_products": [123, 456]},
            viewed_products=[123, 456],
            turn_count=5,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
        )

        db.add(context)
        await db.commit()

        # Get CSRF token
        await client.get_csrf_token()

        # Execute
        response = await client.get(
            f"/api/v1/conversations/{conversation_id}/context",
            headers={"X-Merchant-Id": str(merchant_id)},
        )

        # Verify
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "data" in data
        assert data["data"]["conversationId"] == conversation_id
        assert data["data"]["mode"] == "ecommerce"

    @pytest.mark.asyncio
    async def test_get_context_not_found(self, client):
        """Test that missing context returns 404."""
        # Get CSRF token
        await client.get_csrf_token()

        response = await client.get(
            "/api/v1/conversations/99999/context",
            headers={"X-Merchant-Id": "1"},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestUpdateConversationContext:
    """Test PUT /api/v1/conversations/{id}/context endpoint."""

    @pytest.mark.asyncio
    async def test_update_context_ecommerce(self, client, db_session_with_conversation):
        """Test updating context in e-commerce mode."""
        conversation_id = db_session_with_conversation["conversation_id"]
        merchant_id = db_session_with_conversation["merchant_id"]

        # Get CSRF token
        await client.get_csrf_token()

        update_data = {
            "message": "Show me red shoes under $100",
            "mode": "ecommerce",
        }

        response = await client.put(
            f"/api/v1/conversations/{conversation_id}/context",
            json=update_data,
            headers={"X-Merchant-Id": str(merchant_id)},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["data"]["mode"] == "ecommerce"
        assert data["data"]["turnCount"] == 1

    @pytest.mark.asyncio
    async def test_update_context_general(self, client, db_session_with_conversation):
        """Test updating context in general mode."""
        conversation_id = db_session_with_conversation["conversation_id"]
        merchant_id = db_session_with_conversation["merchant_id"]

        # Get CSRF token
        await client.get_csrf_token()

        update_data = {
            "message": "I'm having login issues",
            "mode": "general",
        }

        response = await client.put(
            f"/api/v1/conversations/{conversation_id}/context",
            json=update_data,
            headers={"X-Merchant-Id": str(merchant_id)},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["data"]["mode"] == "general"


class TestSummarizeConversationContext:
    """Test POST /api/v1/conversations/{id}/context/summary endpoint."""

    @pytest.mark.asyncio
    async def test_summarize_context(self, client, db_session_with_conversation):
        """Test summarization endpoint."""
        merchant_id = db_session_with_conversation["merchant_id"]
        conversation_id = db_session_with_conversation["conversation_id"]
        db = db_session_with_conversation["db"]

        # Setup: Create context
        context = ConversationContext(
            conversation_id=conversation_id,
            merchant_id=merchant_id,
            mode="ecommerce",
            context_data={"viewed_products": [123, 456, 789]},
            viewed_products=[123, 456, 789],
            turn_count=10,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
        )

        db.add(context)
        await db.commit()

        # Get CSRF token
        await client.get_csrf_token()

        # Execute
        response = await client.post(
            f"/api/v1/conversations/{conversation_id}/context/summary",
            headers={"X-Merchant-Id": str(merchant_id)},
        )

        # Verify
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "data" in data
        assert "summary" in data["data"]
        assert "keyPoints" in data["data"]
        assert data["data"]["originalTurns"] == 10


class TestContextAPIValidation:
    """Test request validation in context API."""

    @pytest.mark.asyncio
    async def test_update_context_invalid_mode(self, client, db_session_with_conversation):
        """Test validation error for invalid mode."""
        conversation_id = db_session_with_conversation["conversation_id"]
        merchant_id = db_session_with_conversation["merchant_id"]

        # Get CSRF token
        await client.get_csrf_token()

        update_data = {
            "message": "Test",
            "mode": "invalid_mode",
        }

        response = await client.put(
            f"/api/v1/conversations/{conversation_id}/context",
            json=update_data,
            headers={"X-Merchant-Id": str(merchant_id)},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestContextAPIAuthorization:
    """Test authorization and access control."""

    @pytest.mark.asyncio
    async def test_conversation_not_found_for_merchant(self, client, db_session_with_conversation):
        """Test accessing conversation with wrong merchant ID."""
        # Get CSRF token
        await client.get_csrf_token()

        response = await client.get(
            "/api/v1/conversations/99999/context",
            headers={"X-Merchant-Id": str(db_session_with_conversation["merchant_id"])},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
