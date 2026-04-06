"""Integration tests for Conversation Flow Analytics API endpoints.

Story 11.12b: Conversation Flow Analytics Dashboard

Tests all 6 API endpoints under /api/v1/analytics/conversation-flow/ with
real database operations via the async_client fixture.
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.models.conversation import Conversation
from app.models.conversation_context import ConversationTurn

CONVERSATION_FLOW_ENDPOINTS = [
    "/api/v1/analytics/conversation-flow/length-distribution",
    "/api/v1/analytics/conversation-flow/clarification-patterns",
    "/api/v1/analytics/conversation-flow/friction-points",
    "/api/v1/analytics/conversation-flow/sentiment-stages",
    "/api/v1/analytics/conversation-flow/handoff-correlation",
    "/api/v1/analytics/conversation-flow/context-utilization",
]


@pytest.mark.p0
@pytest.mark.test_id("STORY-11-12b-SEQ-07")
class TestConversationFlowAPIEndpoints:
    """Integration tests for all 6 conversation flow analytics endpoints."""

    async def test_all_endpoints_return_200_with_no_data(
        self, async_client: AsyncClient, test_merchant
    ):
        """All endpoints return 200 with has_data=False when no data exists."""
        headers = {"X-Test-Mode": "true", "X-Merchant-Id": str(test_merchant)}

        for endpoint in CONVERSATION_FLOW_ENDPOINTS:
            response = await async_client.get(endpoint, headers=headers, params={"days": 7})
            assert response.status_code == 200, f"{endpoint} returned {response.status_code}"
            data = response.json()
            assert data["has_data"] is False, f"{endpoint} should have no data"
            assert "message" in data, f"{endpoint} should include message"

    async def test_all_endpoints_accept_days_param(self, async_client: AsyncClient, test_merchant):
        """All endpoints accept days query parameter."""
        headers = {"X-Test-Mode": "true", "X-Merchant-Id": str(test_merchant)}

        for endpoint in CONVERSATION_FLOW_ENDPOINTS:
            response = await async_client.get(endpoint, headers=headers, params={"days": 90})
            assert response.status_code == 200, f"{endpoint} with days=90 failed"

    async def test_default_days_is_30(
        self, async_client: AsyncClient, test_merchant, async_session
    ):
        """Endpoints default to 30 days when no days param provided."""
        headers = {"X-Test-Mode": "true", "X-Merchant-Id": str(test_merchant)}

        response = await async_client.get(
            "/api/v1/analytics/conversation-flow/length-distribution", headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("period_days", 30) == 30

    async def test_length_distribution_endpoint_with_data(
        self, async_client: AsyncClient, test_merchant, async_session
    ):
        """Length distribution endpoint returns data when turns exist."""
        conv = Conversation(
            merchant_id=test_merchant,
            platform="messenger",
            platform_sender_id="api-test-conv-1",
        )
        async_session.add(conv)
        await async_session.flush()

        for i in range(1, 4):
            turn = ConversationTurn(
                conversation_id=conv.id,
                turn_number=i,
                user_message=f"User message {i}",
                bot_response=f"Bot response {i}",
                intent_detected="product_search" if i % 2 == 0 else "greeting",
                context_snapshot={
                    "confidence": 0.9,
                    "processing_time_ms": 100 + i * 10,
                    "has_context_reference": i > 1,
                    "mode": "ecommerce",
                },
            )
            async_session.add(turn)
        await async_session.flush()
        await async_session.commit()

        headers = {"X-Test-Mode": "true", "X-Merchant-Id": str(test_merchant)}
        response = await async_client.get(
            "/api/v1/analytics/conversation-flow/length-distribution",
            headers=headers,
            params={"days": 7},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["has_data"] is True
        assert data["data"]["total_conversations"] >= 1

    async def test_handoff_correlation_endpoint_with_handoff(
        self, async_client: AsyncClient, test_merchant, async_session
    ):
        """Handoff correlation endpoint returns data when handoff conversations exist."""
        conv = Conversation(
            merchant_id=test_merchant,
            platform="messenger",
            platform_sender_id="api-handoff-conv-1",
            handoff_status="active",
        )
        async_session.add(conv)
        await async_session.flush()

        for i in range(1, 3):
            turn = ConversationTurn(
                conversation_id=conv.id,
                turn_number=i,
                user_message=f"User message {i}",
                bot_response=f"Bot response {i}",
                intent_detected="escalate",
                context_snapshot={
                    "confidence": 0.5,
                    "processing_time_ms": 100,
                    "has_context_reference": True,
                    "mode": "ecommerce",
                },
            )
            async_session.add(turn)
        await async_session.flush()
        await async_session.commit()

        headers = {"X-Test-Mode": "true", "X-Merchant-Id": str(test_merchant)}
        response = await async_client.get(
            "/api/v1/analytics/conversation-flow/handoff-correlation",
            headers=headers,
            params={"days": 7},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["has_data"] is True
        assert data["data"]["total_handoff_conversations"] >= 1

    async def test_context_utilization_endpoint_with_data(
        self, async_client: AsyncClient, test_merchant, async_session
    ):
        """Context utilization endpoint returns utilization metrics."""
        conv = Conversation(
            merchant_id=test_merchant,
            platform="messenger",
            platform_sender_id="api-context-conv-1",
        )
        async_session.add(conv)
        await async_session.flush()

        for i in range(1, 5):
            turn = ConversationTurn(
                conversation_id=conv.id,
                turn_number=i,
                user_message=f"User message {i}",
                bot_response=f"Bot response {i}",
                intent_detected="product_search",
                context_snapshot={
                    "confidence": 0.9,
                    "processing_time_ms": 100,
                    "has_context_reference": True,
                    "mode": "ecommerce",
                },
            )
            async_session.add(turn)
        await async_session.flush()
        await async_session.commit()

        headers = {"X-Test-Mode": "true", "X-Merchant-Id": str(test_merchant)}
        response = await async_client.get(
            "/api/v1/analytics/conversation-flow/context-utilization",
            headers=headers,
            params={"days": 7},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["has_data"] is True
        assert data["data"]["utilization_rate"] == 100.0

    async def test_friction_points_endpoint_with_data(
        self, async_client: AsyncClient, test_merchant, async_session
    ):
        """Friction points endpoint detects repeated intents."""
        conv = Conversation(
            merchant_id=test_merchant,
            platform="messenger",
            platform_sender_id="api-friction-conv-1",
            status="closed",
        )
        async_session.add(conv)
        await async_session.flush()

        for i in range(1, 4):
            turn = ConversationTurn(
                conversation_id=conv.id,
                turn_number=i,
                user_message=f"User message {i}",
                bot_response=f"Bot response {i}",
                intent_detected="greeting",
                context_snapshot={
                    "confidence": 0.9,
                    "processing_time_ms": 100,
                    "has_context_reference": True,
                    "mode": "ecommerce",
                },
            )
            async_session.add(turn)
        await async_session.flush()
        await async_session.commit()

        headers = {"X-Test-Mode": "true", "X-Merchant-Id": str(test_merchant)}
        response = await async_client.get(
            "/api/v1/analytics/conversation-flow/friction-points",
            headers=headers,
            params={"days": 7},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["has_data"] is True

    async def test_sentiment_stages_endpoint_with_data(
        self, async_client: AsyncClient, test_merchant, async_session
    ):
        """Sentiment stages endpoint returns stage distribution."""
        conv = Conversation(
            merchant_id=test_merchant,
            platform="messenger",
            platform_sender_id="api-sentiment-conv-1",
        )
        async_session.add(conv)
        await async_session.flush()

        for i in range(1, 6):
            turn = ConversationTurn(
                conversation_id=conv.id,
                turn_number=i,
                user_message=f"User message {i}",
                bot_response=f"Bot response {i}",
                intent_detected="product_search",
                sentiment="POSITIVE" if i <= 3 else "NEGATIVE",
                context_snapshot={
                    "confidence": 0.9,
                    "processing_time_ms": 100,
                    "has_context_reference": True,
                    "mode": "ecommerce",
                },
            )
            async_session.add(turn)
        await async_session.flush()
        await async_session.commit()

        headers = {"X-Test-Mode": "true", "X-Merchant-Id": str(test_merchant)}
        response = await async_client.get(
            "/api/v1/analytics/conversation-flow/sentiment-stages",
            headers=headers,
            params={"days": 7},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["has_data"] is True
        assert "early" in data["data"]["stages"]
        assert "mid" in data["data"]["stages"]
        assert "late" in data["data"]["stages"]
