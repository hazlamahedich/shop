"""Tests/integration/test_bot_quality.py - Bot Quality API tests.

Story 7: Dashboard Widgets - BotQualityWidget

"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import Conversation
from app.models.llm_conversation_cost import LLMConversationCost
from tests.conftest import auth_headers


@pytest.mark.asyncio
async def test_bot_quality_endpoint_returns_data(
    client: AsyncClient, async_session: AsyncSession, test_merchant: int
):
    """Test bot quality endpoint returns expected data structure."""
    # Create a test conversation with resolved status (no handoff)
    conversation = Conversation(
        merchant_id=test_merchant,
        status="closed",
        handoff_status="none",
    )
    async_session.add(conversation)
    await async_session.commit()

    # Create an LLM cost record with response time
    cost = LLMConversationCost(
        conversation_id=conversation.id,
        merchant_id=test_merchant,
        model="gpt-4",
        input_tokens=100,
        output_tokens=50,
        total_cost=0.01,
        processing_time_ms=500.0,
    )
    async_session.add(cost)
    await async_session.commit()

    # Call the endpoint
    response = await client.get(
        "/api/v1/analytics/bot-quality?days=30", headers=auth_headers(test_merchant)
    )

    assert response.status_code == 200
    data = response.json()

    # Verify expected fields exist
    assert "avgResponseTimeMs" in data
    assert "fallbackRatePercent" in data
    assert "resolutionRatePercent" in data
    assert "csatScore" in data
    assert "totalConversations" in data
    assert "periodDays" in data
    assert "status" in data

    # Verify the response time matches our test data
    assert data["avgResponseTimeMs"] == 500.0
    assert data["totalConversations"] == 1
    assert data["periodDays"] == 30


@pytest.mark.asyncio
async def test_bot_quality_endpoint_empty_data(client: AsyncClient, test_merchant: int):
    """Test bot quality endpoint handles empty data gracefully."""
    response = await client.get(
        "/api/v1/analytics/bot-quality?days=30", headers=auth_headers(test_merchant)
    )

    assert response.status_code == 200
    data = response.json()

    # Should return defaults for empty data
    assert data["avgResponseTimeMs"] == 0
    assert data["totalConversations"] == 0
    assert data["status"] in ["healthy", "no_data"]
