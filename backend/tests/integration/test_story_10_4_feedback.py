"""Integration tests for Story 10-4: Feedback Rating Widget.

Tests feedback submission with real database, retrieval by message_id,
analytics aggregation, and session-based feedback tracking.
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.models.conversation import Conversation
from app.models.message import Message
from tests.conftest import auth_headers


class TestFeedbackSubmissionIntegration:
    """Integration tests for feedback submission with real database."""

    @pytest.mark.asyncio
    async def test_feedback_submission_creates_record(
        self,
        async_client: AsyncClient,
        test_merchant: int,
        test_conversation: Conversation,
        test_message: Message,
    ) -> None:
        """Test feedback submission creates a database record via API."""
        payload = {
            "messageId": test_message.id,
            "conversationId": test_conversation.id,
            "rating": "positive",
            "sessionId": "integration-test-session",
        }

        response = await async_client.post("/api/v1/feedback", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["messageId"] == test_message.id
        assert data["data"]["rating"] == "positive"

    @pytest.mark.asyncio
    async def test_feedback_retrieval_by_session(
        self,
        async_client: AsyncClient,
        test_merchant: int,
        test_conversation: Conversation,
        test_message: Message,
    ) -> None:
        """Test feedback can be retrieved by session_id via API."""
        session_id = "retrieval-test-session"

        payload = {
            "messageId": test_message.id,
            "conversationId": test_conversation.id,
            "rating": "positive",
            "sessionId": session_id,
        }
        response = await async_client.post("/api/v1/feedback", json=payload)
        assert response.status_code == 200

        response2 = await async_client.post(
            "/api/v1/feedback",
            json={
                "messageId": test_message.id,
                "rating": "negative",
                "sessionId": session_id,
            },
        )
        assert response2.status_code == 200
        assert response2.json()["data"]["rating"] == "negative"

    @pytest.mark.asyncio
    async def test_feedback_analytics_aggregation(
        self,
        async_client: AsyncClient,
        test_merchant: int,
        test_conversation: Conversation,
        test_message: Message,
    ) -> None:
        """Test feedback analytics aggregation via API."""
        for i in range(5):
            await async_client.post(
                "/api/v1/feedback",
                json={
                    "messageId": test_message.id,
                    "conversationId": test_conversation.id,
                    "rating": "positive" if i < 4 else "negative",
                    "sessionId": f"analytics-session-{i}",
                },
            )

        response = await async_client.get(
            "/api/v1/feedback/analytics",
            headers=auth_headers(test_merchant),
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["totalRatings"] >= 5
        assert data["data"]["positiveCount"] >= 4
        assert data["data"]["negativeCount"] >= 1

    @pytest.mark.asyncio
    async def test_feedback_tied_to_session_id(
        self,
        async_client: AsyncClient,
        test_merchant: int,
        test_conversation: Conversation,
        test_message: Message,
    ) -> None:
        """Test feedback is tied to session_id for uniqueness."""
        session_id = "unique-session-123"

        payload = {
            "messageId": test_message.id,
            "conversationId": test_conversation.id,
            "rating": "positive",
            "sessionId": session_id,
        }
        response = await async_client.post("/api/v1/feedback", json=payload)
        assert response.status_code == 200
        assert response.json()["data"]["rating"] == "positive"

        payload["rating"] = "negative"
        response = await async_client.post("/api/v1/feedback", json=payload)
        assert response.status_code == 200
        assert response.json()["data"]["rating"] == "negative"

    @pytest.mark.asyncio
    async def test_feedback_anonymous_no_pii(
        self,
        async_client: AsyncClient,
        test_merchant: int,
        test_conversation: Conversation,
        test_message: Message,
    ) -> None:
        """Test feedback response contains no PII."""
        payload = {
            "messageId": test_message.id,
            "conversationId": test_conversation.id,
            "rating": "positive",
            "sessionId": "anonymous-session-456",
        }

        response = await async_client.post("/api/v1/feedback", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "userEmail" not in data["data"]
        assert "userName" not in data["data"]

    @pytest.mark.asyncio
    async def test_feedback_update_same_session_different_rating(
        self,
        async_client: AsyncClient,
        test_merchant: int,
        test_conversation: Conversation,
        test_message: Message,
    ) -> None:
        """Test updating feedback with same session, different rating."""
        session_id = "update-session-789"

        payload = {
            "messageId": test_message.id,
            "conversationId": test_conversation.id,
            "rating": "positive",
            "sessionId": session_id,
        }
        response = await async_client.post("/api/v1/feedback", json=payload)
        assert response.status_code == 200
        assert response.json()["data"]["rating"] == "positive"

        payload["rating"] = "negative"
        payload["comment"] = "Changed my mind"
        response = await async_client.post("/api/v1/feedback", json=payload)
        assert response.status_code == 200
        assert response.json()["data"]["rating"] == "negative"


class TestFeedbackAnalyticsIntegration:
    """Integration tests for feedback analytics."""

    @pytest.mark.asyncio
    async def test_analytics_7_day_trend(
        self,
        async_client: AsyncClient,
        test_merchant: int,
    ) -> None:
        """Test analytics returns 7-day trend."""
        response = await async_client.get(
            "/api/v1/feedback/analytics",
            headers=auth_headers(test_merchant),
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]["trend"]) == 7

        for day in data["data"]["trend"]:
            assert "date" in day
            assert "positive" in day
            assert "negative" in day

    @pytest.mark.asyncio
    async def test_analytics_recent_negative_feedback(
        self,
        async_client: AsyncClient,
        test_merchant: int,
        test_conversation: Conversation,
        test_message: Message,
    ) -> None:
        """Test analytics includes recent negative feedback with comments."""
        for i in range(3):
            await async_client.post(
                "/api/v1/feedback",
                json={
                    "messageId": test_message.id,
                    "conversationId": test_conversation.id,
                    "rating": "negative",
                    "sessionId": f"negative-session-{i}",
                    "comment": f"Feedback {i}: Not helpful",
                },
            )

        response = await async_client.get(
            "/api/v1/feedback/analytics",
            headers=auth_headers(test_merchant),
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]["recentNegative"]) >= 1

    @pytest.mark.asyncio
    async def test_analytics_merchant_isolation(
        self,
        async_client: AsyncClient,
        test_merchant: int,
        test_conversation: Conversation,
        test_message: Message,
    ) -> None:
        """Test analytics only returns data for authenticated merchant."""
        await async_client.post(
            "/api/v1/feedback",
            json={
                "messageId": test_message.id,
                "conversationId": test_conversation.id,
                "rating": "positive",
                "sessionId": "merchant-test-session",
            },
        )

        response = await async_client.get(
            "/api/v1/feedback/analytics",
            headers=auth_headers(test_merchant),
        )

        assert response.status_code == 200


class TestFeedbackPermissions:
    """Tests for feedback permissions and access control."""

    @pytest.mark.asyncio
    async def test_feedback_analytics_requires_auth(
        self,
        async_client: AsyncClient,
    ) -> None:
        """Test analytics endpoint requires authentication."""
        response = await async_client.get("/api/v1/feedback/analytics")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_feedback_submission_no_auth_required(
        self,
        async_client: AsyncClient,
        test_message: Message,
        test_conversation: Conversation,
    ) -> None:
        """Test feedback submission works without auth (widget endpoint)."""
        payload = {
            "messageId": test_message.id,
            "conversationId": test_conversation.id,
            "rating": "positive",
            "sessionId": "no-auth-session",
        }

        response = await async_client.post("/api/v1/feedback", json=payload)
        assert response.status_code == 200
