"""Tests for Preview API endpoints (Story 1.13).

Tests the preview mode API endpoints that allow merchants to test
their bot configuration in a sandbox environment.
"""

from __future__ import annotations

import pytest


class TestCreatePreviewConversation:
    """Tests for POST /api/v1/preview/conversation"""

    @pytest.fixture
    def merchant_headers(self):
        """Get merchant authentication headers for DEBUG mode."""
        return {"X-Merchant-Id": "1"}

    @pytest.mark.asyncio
    async def test_create_preview_conversation_success(
        self,
        async_client,
        merchant,
        merchant_headers: dict,
    ) -> None:
        """Test successfully creating a preview conversation (Story 1.13 AC 1)."""
        response = await async_client.post(
            "/api/v1/preview/conversation",
            headers=merchant_headers,
        )

        assert response.status_code == 200

        data = response.json()
        assert "data" in data
        assert "meta" in data
        assert "previewSessionId" in data["data"]
        assert data["data"]["merchantId"] == 1
        assert "starterPrompts" in data["data"]
        assert len(data["data"]["starterPrompts"]) == 5

    @pytest.mark.asyncio
    async def test_create_preview_conversation_includes_starters(
        self,
        async_client,
        merchant,
        merchant_headers: dict,
    ) -> None:
        """Test that starter prompts are included in response (Story 1.13 AC 4)."""
        response = await async_client.post(
            "/api/v1/preview/conversation",
            headers=merchant_headers,
        )

        data = response.json()
        starters = data["data"]["starterPrompts"]

        # Verify all required starters are present
        assert "What products do you have under $50?" in starters
        assert "What are your business hours?" in starters
        assert "Show me running shoes" in starters
        assert "I need help with my order" in starters
        assert "Tell me about your return policy" in starters


class TestSendPreviewMessage:
    """Tests for POST /api/v1/preview/message"""

    @pytest.fixture
    def merchant_headers(self):
        """Get merchant authentication headers for DEBUG mode."""
        return {"X-Merchant-Id": "1"}

    @pytest.fixture
    async def preview_session_id(self, async_client, merchant, merchant_headers):
        """Create a preview session and return its ID.

        Note: Must include 'merchant' fixture to ensure merchant exists in database
        before creating preview session.
        """
        response = await async_client.post(
            "/api/v1/preview/conversation",
            headers=merchant_headers,
        )
        assert response.status_code == 200, f"Failed to create preview session: {response.text}"
        data = response.json()
        return data["data"]["previewSessionId"]

    @pytest.mark.asyncio
    async def test_send_message_success(
        self,
        async_client,
        merchant,
        merchant_headers: dict,
        preview_session_id: str,
    ) -> None:
        """Test successfully sending a message and getting bot response (Story 1.13 AC 3)."""
        response = await async_client.post(
            "/api/v1/preview/message",
            json={
                "message": "What shoes do you have?",
                "previewSessionId": preview_session_id,
            },
            headers=merchant_headers,
        )

        # Should succeed (returns bot response or error handled gracefully)
        # The actual bot response should work with mock FAQ in test environment
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_send_message_empty_error(
        self,
        async_client,
        merchant_headers: dict,
        preview_session_id: str,
    ) -> None:
        """Test sending an empty message returns validation error."""
        response = await async_client.post(
            "/api/v1/preview/message",
            json={
                "message": "   ",
                "previewSessionId": preview_session_id,
            },
            headers=merchant_headers,
        )

        # Schema validation should catch this
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_send_message_too_long_error(
        self,
        async_client,
        merchant_headers: dict,
        preview_session_id: str,
    ) -> None:
        """Test sending a message that's too long returns error."""
        # Create a message that exceeds 1000 characters
        long_message = "x" * 1001

        response = await async_client.post(
            "/api/v1/preview/message",
            json={
                "message": long_message,
                "previewSessionId": preview_session_id,
            },
            headers=merchant_headers,
        )

        # Schema validation should catch this
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_send_message_session_not_found(
        self,
        async_client,
        merchant_headers: dict,
    ) -> None:
        """Test sending message to non-existent session."""
        response = await async_client.post(
            "/api/v1/preview/message",
            json={
                "message": "Test message",
                "previewSessionId": "non-existent-session-id",
            },
            headers=merchant_headers,
        )

        assert response.status_code == 404


class TestResetPreviewConversation:
    """Tests for DELETE /api/v1/preview/conversation"""

    @pytest.fixture
    def merchant_headers(self):
        """Get merchant authentication headers for DEBUG mode."""
        return {"X-Merchant-Id": "1"}

    @pytest.fixture
    async def preview_session_id(self, async_client, merchant, merchant_headers):
        """Create a preview session and return its ID.

        Note: Must include 'merchant' fixture to ensure merchant exists in database
        before creating preview session.
        """
        response = await async_client.post(
            "/api/v1/preview/conversation",
            headers=merchant_headers,
        )
        assert response.status_code == 200, f"Failed to create preview session: {response.text}"
        data = response.json()
        return data["data"]["previewSessionId"]

    @pytest.mark.asyncio
    async def test_reset_conversation_success(
        self,
        async_client,
        merchant_headers: dict,
        preview_session_id: str,
    ) -> None:
        """Test successfully resetting a preview conversation (Story 1.13 AC 1)."""
        response = await async_client.delete(
            f"/api/v1/preview/conversation/{preview_session_id}",
            headers=merchant_headers,
        )

        assert response.status_code == 200

        data = response.json()
        assert "data" in data
        assert data["data"]["cleared"] is True

    @pytest.mark.asyncio
    async def test_reset_conversation_session_not_found(
        self,
        async_client,
        merchant_headers: dict,
    ) -> None:
        """Test resetting a non-existent session."""
        response = await async_client.delete(
            "/api/v1/preview/conversation/non-existent-session",
            headers=merchant_headers,
        )

        assert response.status_code == 404


class TestPreviewIntegration:
    """Integration tests for preview API flow."""

    @pytest.fixture
    def merchant_headers(self):
        """Get merchant authentication headers for DEBUG mode."""
        return {"X-Merchant-Id": "1"}

    @pytest.mark.asyncio
    async def test_full_preview_flow(
        self,
        async_client,
        merchant,
        merchant_headers: dict,
    ) -> None:
        """Test complete preview flow: create, send message, reset."""
        # Step 1: Create preview session
        create_response = await async_client.post(
            "/api/v1/preview/conversation",
            headers=merchant_headers,
        )
        assert create_response.status_code == 200
        session_data = create_response.json()["data"]
        session_id = session_data["previewSessionId"]

        # Step 2: Send a message (endpoint should handle gracefully)
        message_response = await async_client.post(
            "/api/v1/preview/message",
            json={
                "message": "Test message",
                "previewSessionId": session_id,
            },
            headers=merchant_headers,
        )
        # Should succeed (returns bot response or handled error)
        assert message_response.status_code == 200

        # Step 3: Reset conversation
        reset_response = await async_client.delete(
            f"/api/v1/preview/conversation/{session_id}",
            headers=merchant_headers,
        )
        assert reset_response.status_code == 200
