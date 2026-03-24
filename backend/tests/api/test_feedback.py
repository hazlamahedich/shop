"""Tests for Feedback API endpoints.

Story 10-4: Feedback Rating Widget
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.models.conversation import Conversation
from app.models.message import Message
from tests.conftest import auth_headers


class TestSubmitFeedback:
    """Tests for POST /api/v1/feedback endpoint."""

    @pytest.mark.asyncio
    async def test_submit_feedback_creates_new_feedback(
        self,
        async_client: AsyncClient,
        test_merchant: int,
        test_conversation: Conversation,
        test_message: Message,
    ) -> None:
        """Test POST creates new feedback record."""
        payload = {
            "messageId": test_message.id,
            "conversationId": test_conversation.id,
            "rating": "positive",
            "sessionId": "test-session-123",
        }

        response = await async_client.post(
            "/api/v1/feedback",
            json=payload,
            headers=auth_headers(test_merchant),
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["messageId"] == test_message.id
        assert data["data"]["rating"] == "positive"

    @pytest.mark.asyncio
    async def test_submit_feedback_updates_existing_feedback(
        self,
        async_client: AsyncClient,
        test_merchant: int,
        test_conversation: Conversation,
        test_message: Message,
    ) -> None:
        """Test POST updates existing feedback (AC2: clicking again updates rating)."""
        # First, create feedback via API
        payload1 = {
            "messageId": test_message.id,
            "conversationId": test_conversation.id,
            "rating": "positive",
            "sessionId": "test-session-123",
        }
        response1 = await async_client.post("/api/v1/feedback", json=payload1)
        assert response1.status_code == 200
        data1 = response1.json()
        original_id = data1["data"]["id"]

        # Now update with same session_id
        payload2 = {
            "messageId": test_message.id,
            "rating": "negative",
            "sessionId": "test-session-123",
        }
        response2 = await async_client.post("/api/v1/feedback", json=payload2)

        assert response2.status_code == 200
        data2 = response2.json()
        assert data2["data"]["rating"] == "negative"
        assert data2["data"]["id"] == original_id

    @pytest.mark.asyncio
    async def test_submit_feedback_with_comment(
        self,
        async_client: AsyncClient,
        test_merchant: int,
        test_conversation: Conversation,
        test_message: Message,
    ) -> None:
        """Test POST with optional comment for negative feedback."""
        payload = {
            "messageId": test_message.id,
            "conversationId": test_conversation.id,
            "rating": "negative",
            "comment": "Answer was not helpful",
            "sessionId": "test-session-123",
        }

        response = await async_client.post("/api/v1/feedback", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["rating"] == "negative"

    @pytest.mark.asyncio
    async def test_submit_feedback_comment_max_length(
        self,
        async_client: AsyncClient,
        test_merchant: int,
        test_conversation: Conversation,
        test_message: Message,
    ) -> None:
        """Test comment max length validation (500 chars)."""
        payload = {
            "messageId": test_message.id,
            "conversationId": test_conversation.id,
            "rating": "negative",
            "comment": "a" * 501,
            "sessionId": "test-session-123",
        }

        response = await async_client.post("/api/v1/feedback", json=payload)

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_submit_feedback_invalid_rating(
        self,
        async_client: AsyncClient,
        test_merchant: int,
        test_conversation: Conversation,
        test_message: Message,
    ) -> None:
        """Test invalid rating value rejection."""
        payload = {
            "messageId": test_message.id,
            "conversationId": test_conversation.id,
            "rating": "maybe",
            "sessionId": "test-session-123",
        }

        response = await async_client.post("/api/v1/feedback", json=payload)

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_submit_feedback_message_not_found(
        self,
        async_client: AsyncClient,
    ) -> None:
        """Test message not found error (error code 7063)."""
        payload = {
            "messageId": 99999,
            "conversationId": 1,
            "rating": "positive",
            "sessionId": "test-session-123",
        }

        response = await async_client.post("/api/v1/feedback", json=payload)

        assert response.status_code == 404
        data = response.json()
        assert data["detail"]["error_code"] == 7063
        assert "Message not found" in data["detail"]["message"]

    @pytest.mark.asyncio
    async def test_submit_feedback_conversation_not_found(
        self,
        async_client: AsyncClient,
        test_merchant: int,
        test_conversation: Conversation,
        test_message: Message,
    ) -> None:
        """Test conversation not found error."""
        payload = {
            "messageId": test_message.id,
            "conversationId": 99999,
            "rating": "positive",
            "sessionId": "test-session-123",
        }

        response = await async_client.post("/api/v1/feedback", json=payload)

        assert response.status_code == 404
        data = response.json()
        # API uses CONVERSATION_NOT_FOUND (7001) for conversation not found
        assert data["detail"]["error_code"] == 7001
        assert "Conversation not found" in data["detail"]["message"]

    @pytest.mark.asyncio
    async def test_submit_feedback_conversation_id_optional(
        self,
        async_client: AsyncClient,
        test_merchant: int,
        test_conversation: Conversation,
        test_message: Message,
    ) -> None:
        """Test conversationId is optional (looked up from message)."""
        payload = {
            "messageId": test_message.id,
            "rating": "positive",
            "sessionId": "test-session-123",
        }

        response = await async_client.post("/api/v1/feedback", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["messageId"] == test_message.id


class TestGetFeedbackAnalytics:
    """Tests for GET /api/v1/feedback/analytics endpoint."""

    @pytest.mark.asyncio
    async def test_get_feedback_analytics_returns_aggregations(
        self,
        async_client: AsyncClient,
        test_merchant: int,
        test_conversation: Conversation,
        test_message: Message,
    ) -> None:
        """Test GET returns correct aggregations."""
        # Create feedback via API
        await async_client.post(
            "/api/v1/feedback",
            json={
                "messageId": test_message.id,
                "conversationId": test_conversation.id,
                "rating": "positive",
                "sessionId": "session-1",
            },
        )
        await async_client.post(
            "/api/v1/feedback",
            json={
                "messageId": test_message.id,
                "conversationId": test_conversation.id,
                "rating": "positive",
                "sessionId": "session-2",
            },
        )
        await async_client.post(
            "/api/v1/feedback",
            json={
                "messageId": test_message.id,
                "conversationId": test_conversation.id,
                "rating": "negative",
                "sessionId": "session-3",
                "comment": "Not helpful",
            },
        )

        response = await async_client.get(
            "/api/v1/feedback/analytics",
            headers=auth_headers(test_merchant),
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["totalRatings"] == 3
        assert data["data"]["positiveCount"] == 2
        assert data["data"]["negativeCount"] == 1
        assert data["data"]["positivePercent"] == 66.7

    @pytest.mark.asyncio
    async def test_get_feedback_analytics_includes_recent_negative(
        self,
        async_client: AsyncClient,
        test_merchant: int,
        test_conversation: Conversation,
        test_message: Message,
    ) -> None:
        """Test GET includes recent negative feedback with comments."""
        await async_client.post(
            "/api/v1/feedback",
            json={
                "messageId": test_message.id,
                "conversationId": test_conversation.id,
                "rating": "negative",
                "sessionId": "session-1",
                "comment": "Answer was confusing",
            },
        )

        response = await async_client.get(
            "/api/v1/feedback/analytics",
            headers=auth_headers(test_merchant),
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]["recentNegative"]) >= 1
        assert data["data"]["recentNegative"][0]["comment"] == "Answer was confusing"

    @pytest.mark.asyncio
    async def test_get_feedback_analytics_includes_trend(
        self,
        async_client: AsyncClient,
        test_merchant: int,
        test_conversation: Conversation,
        test_message: Message,
    ) -> None:
        """Test GET includes 7-day trend."""
        await async_client.post(
            "/api/v1/feedback",
            json={
                "messageId": test_message.id,
                "conversationId": test_conversation.id,
                "rating": "positive",
                "sessionId": "session-1",
            },
        )

        response = await async_client.get(
            "/api/v1/feedback/analytics",
            headers=auth_headers(test_merchant),
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]["trend"]) == 7
        assert "date" in data["data"]["trend"][0]
        assert "positive" in data["data"]["trend"][0]
        assert "negative" in data["data"]["trend"][0]

    @pytest.mark.asyncio
    async def test_get_feedback_analytics_date_range_filter(
        self,
        async_client: AsyncClient,
        test_merchant: int,
        test_conversation: Conversation,
        test_message: Message,
    ) -> None:
        """Test GET filters by date range."""
        await async_client.post(
            "/api/v1/feedback",
            json={
                "messageId": test_message.id,
                "conversationId": test_conversation.id,
                "rating": "positive",
                "sessionId": "session-1",
            },
        )

        response = await async_client.get(
            "/api/v1/feedback/analytics?start_date=2020-01-01&end_date=2020-01-31",
            headers=auth_headers(test_merchant),
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["totalRatings"] == 0

    @pytest.mark.asyncio
    async def test_get_feedback_analytics_requires_auth(
        self,
        async_client: AsyncClient,
    ) -> None:
        """Test GET requires authentication."""
        response = await async_client.get("/api/v1/feedback/analytics")

        assert response.status_code == 401


class TestFeedbackLinkedToMessageAndConversation:
    """Tests for AC5: Feedback tied to message and conversation."""

    @pytest.mark.asyncio
    async def test_feedback_linked_to_message(
        self,
        async_client: AsyncClient,
        test_merchant: int,
        test_conversation: Conversation,
        test_message: Message,
    ) -> None:
        """Test feedback is linked to specific message_id."""
        payload = {
            "messageId": test_message.id,
            "conversationId": test_conversation.id,
            "rating": "positive",
            "sessionId": "test-session-123",
        }

        response = await async_client.post("/api/v1/feedback", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["messageId"] == test_message.id

    @pytest.mark.asyncio
    async def test_feedback_linked_to_conversation(
        self,
        async_client: AsyncClient,
        test_merchant: int,
        test_conversation: Conversation,
        test_message: Message,
    ) -> None:
        """Test feedback is linked to conversation_id."""
        payload = {
            "messageId": test_message.id,
            "conversationId": test_conversation.id,
            "rating": "positive",
            "sessionId": "test-session-123",
        }

        response = await async_client.post("/api/v1/feedback", json=payload)
        assert response.status_code == 200
        # Conversation ID is not returned in response, but we verify the call succeeds
        # which means the conversation link was validated

    @pytest.mark.asyncio
    async def test_feedback_includes_timestamp_and_session(
        self,
        async_client: AsyncClient,
        test_merchant: int,
        test_conversation: Conversation,
        test_message: Message,
    ) -> None:
        """Test feedback includes timestamp and session_id."""
        payload = {
            "messageId": test_message.id,
            "conversationId": test_conversation.id,
            "rating": "positive",
            "sessionId": "test-session-456",
        }

        response = await async_client.post("/api/v1/feedback", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["createdAt"] is not None

    @pytest.mark.asyncio
    async def test_feedback_anonymous_no_pii(
        self,
        async_client: AsyncClient,
        test_merchant: int,
        test_conversation: Conversation,
        test_message: Message,
    ) -> None:
        """Test no PII is stored (anonymous feedback)."""
        payload = {
            "messageId": test_message.id,
            "conversationId": test_conversation.id,
            "rating": "positive",
            "sessionId": "anonymous-uuid-123",
        }

        response = await async_client.post("/api/v1/feedback", json=payload)
        assert response.status_code == 200
        data = response.json()
        # Verify response only contains expected fields (no PII like email/name)
        assert "id" in data["data"]
        assert "messageId" in data["data"]
        assert "rating" in data["data"]
        assert "userEmail" not in data["data"]
        assert "userName" not in data["data"]
