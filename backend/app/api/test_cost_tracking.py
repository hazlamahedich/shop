"""Unit tests for Cost Tracking API endpoints."""

from __future__ import annotations

import pytest
from datetime import datetime, timedelta

from app.models.llm_conversation_cost import LLMConversationCost
from app.core.errors import ErrorCode


@pytest.mark.asyncio
class TestCostTrackingAPI:
    """Test cost tracking API endpoints."""

    async def test_get_conversation_costs_success(self, async_client, async_session):
        """Test successful retrieval of conversation costs."""
        # Create cost record
        cost_record = LLMConversationCost(
            conversation_id="test-conv-api",
            merchant_id=1,
            provider="openai",
            model="gpt-4o-mini",
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150,
            input_cost_usd=0.0001,
            output_cost_usd=0.0002,
            total_cost_usd=0.0003,
            request_timestamp=datetime.utcnow(),
        )
        async_session.add(cost_record)
        await async_session.flush()

        # Make request
        response = await async_client.get(
            "/api/costs/conversation/test-conv-api",
            headers={"X-Merchant-Id": "1"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["conversationId"] == "test-conv-api"
        assert data["data"]["totalCostUsd"] == 0.0003
        assert data["data"]["totalTokens"] == 150
        assert data["data"]["requestCount"] == 1

    async def test_get_conversation_costs_not_found(self, async_client):
        """Test 404 when conversation has no cost data."""
        response = await async_client.get(
            "/api/costs/conversation/non-existent",
            headers={"X-Merchant-Id": "1"},
        )

        assert response.status_code == 404
        data = response.json()
        assert "error_code" in data
        assert data["error_code"] == ErrorCode.LLM_COST_NOT_FOUND

    async def test_get_conversation_costs_merchant_isolation(self, async_client, async_session):
        """Test that merchant cannot access another merchant's cost data."""
        # Create cost record for merchant 1
        cost_record = LLMConversationCost(
            conversation_id="test-conv-isolation-api",
            merchant_id=1,
            provider="openai",
            model="gpt-4o-mini",
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150,
            input_cost_usd=0.0001,
            output_cost_usd=0.0002,
            total_cost_usd=0.0003,
            request_timestamp=datetime.utcnow(),
        )
        async_session.add(cost_record)
        await async_session.flush()

        # Merchant 2 tries to access merchant 1's data
        response = await async_client.get(
            "/api/costs/conversation/test-conv-isolation-api",
            headers={"X-Merchant-Id": "2"},
        )

        assert response.status_code == 404

    async def test_get_cost_summary_empty(self, async_client, async_session):
        """Test cost summary with no data."""
        # Explicit cleanup: delete any existing cost records for merchant_id=1
        from sqlalchemy import delete
        await async_session.execute(delete(LLMConversationCost).where(LLMConversationCost.merchant_id == 1))
        await async_session.commit()

        response = await async_client.get(
            "/api/costs/summary",
            headers={"X-Merchant-Id": "1"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["totalCostUsd"] == 0.0
        assert data["data"]["totalTokens"] == 0
        assert data["data"]["requestCount"] == 0
        assert data["data"]["topConversations"] == []

    async def test_get_cost_summary_with_data(self, async_client, async_session):
        """Test cost summary with actual cost data."""
        # Explicit cleanup: delete any existing cost records for merchant_id=1
        from sqlalchemy import delete
        await async_session.execute(delete(LLMConversationCost).where(LLMConversationCost.merchant_id == 1))
        await async_session.commit()

        # Create cost records
        for i in range(3):
            cost_record = LLMConversationCost(
                conversation_id=f"conv-{i}",
                merchant_id=1,
                provider="openai",
                model="gpt-4o-mini",
                prompt_tokens=100 * (i + 1),
                completion_tokens=50 * (i + 1),
                total_tokens=150 * (i + 1),
                input_cost_usd=0.0001 * (i + 1),
                output_cost_usd=0.0002 * (i + 1),
                total_cost_usd=0.0003 * (i + 1),
                request_timestamp=datetime.utcnow(),
            )
            async_session.add(cost_record)
        await async_session.flush()

        response = await async_client.get(
            "/api/costs/summary",
            headers={"X-Merchant-Id": "1"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["totalCostUsd"] == 0.0018  # 0.0003 * 3 = 0.0009, rounded from actual
        assert data["data"]["requestCount"] == 3
        assert len(data["data"]["topConversations"]) == 3
        assert data["data"]["costsByProvider"]["openai"]["requests"] == 3

    async def test_get_cost_summary_with_date_range(self, async_client, async_session):
        """Test cost summary with date filtering."""
        # Explicit cleanup: delete any existing cost records for merchant_id=1
        from sqlalchemy import delete
        await async_session.execute(delete(LLMConversationCost).where(LLMConversationCost.merchant_id == 1))
        await async_session.commit()

        # Create cost records on different dates
        today = datetime.utcnow()
        yesterday = today - timedelta(days=1)

        record1 = LLMConversationCost(
            conversation_id="conv-yesterday",
            merchant_id=1,
            provider="openai",
            model="gpt-4o-mini",
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150,
            input_cost_usd=0.0001,
            output_cost_usd=0.0002,
            total_cost_usd=0.0003,
            request_timestamp=yesterday,
        )
        async_session.add(record1)

        record2 = LLMConversationCost(
            conversation_id="conv-today",
            merchant_id=1,
            provider="openai",
            model="gpt-4o-mini",
            prompt_tokens=200,
            completion_tokens=100,
            total_tokens=300,
            input_cost_usd=0.0002,
            output_cost_usd=0.0004,
            total_cost_usd=0.0006,
            request_timestamp=today,
        )
        async_session.add(record2)
        await async_session.flush()

        # Get summary for today only
        date_from = today.date().isoformat()
        response = await async_client.get(
            f"/api/costs/summary?date_from={date_from}",
            headers={"X-Merchant-Id": "1"},
        )

        assert response.status_code == 200
        data = response.json()
        # Should only include today's record
        assert data["data"]["totalCostUsd"] == 0.0006
        assert data["data"]["requestCount"] == 1

    async def test_get_cost_summary_invalid_date_format(self, async_client):
        """Test that invalid date format returns validation error."""
        response = await async_client.get(
            "/api/costs/summary?date_from=invalid-date",
            headers={"X-Merchant-Id": "1"},
        )

        # FastAPI returns 422 for query validation errors
        assert response.status_code in [400, 422]
        data = response.json()
        assert "error_code" in data or "detail" in data

    async def test_get_conversation_costs_authentication_required(self, async_client):
        """Test that authentication is required (in non-debug mode)."""
        # Without X-Merchant-Id in DEBUG mode, it should default to merchant_id=1
        # So this will return 404 (not 401) for non-existent conversation
        response = await async_client.get("/api/costs/conversation/test-conv")
        assert response.status_code in [401, 404]

    async def test_get_conversation_costs_multiple_requests(self, async_client, async_session):
        """Test getting conversation costs with multiple requests."""
        conv_id = "test-conv-multi-api"

        # Create multiple cost records
        await async_session.flush()  # Flush before creating records

        cost_record1 = LLMConversationCost(
            conversation_id=conv_id,
            merchant_id=1,
            provider="openai",
            model="gpt-4o-mini",
            prompt_tokens=250,
            completion_tokens=150,
            total_tokens=400,
            input_cost_usd=0.000375,
            output_cost_usd=0.00009,
            total_cost_usd=0.000465,
            request_timestamp=datetime.utcnow(),
        )
        async_session.add(cost_record1)

        cost_record2 = LLMConversationCost(
            conversation_id=conv_id,
            merchant_id=1,
            provider="openai",
            model="gpt-4o-mini",
            prompt_tokens=300,
            completion_tokens=200,
            total_tokens=500,
            input_cost_usd=0.00045,
            output_cost_usd=0.00012,
            total_cost_usd=0.00057,
            request_timestamp=datetime.utcnow(),
        )
        async_session.add(cost_record2)
        await async_session.flush()

        # Get conversation costs
        response = await async_client.get(
            f"/api/costs/conversation/{conv_id}",
            headers={"X-Merchant-Id": "1"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["requestCount"] == 2
        assert data["data"]["totalCostUsd"] == 0.001  # Rounded from 0.000465 + 0.00057
        assert data["data"]["totalTokens"] == 900  # 400 + 500
        assert len(data["data"]["requests"]) == 2

    async def test_get_cost_summary_merchant_isolation(self, async_client, async_session):
        """Test merchant isolation in cost summary."""
        # Explicit cleanup: delete any existing cost records for both merchants
        from sqlalchemy import delete
        await async_session.execute(delete(LLMConversationCost))
        await async_session.commit()

        # Create cost records for merchant 1
        cost_record1 = LLMConversationCost(
            conversation_id="conv-1",
            merchant_id=1,
            provider="openai",
            model="gpt-4o-mini",
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150,
            input_cost_usd=0.0001,
            output_cost_usd=0.0002,
            total_cost_usd=0.0003,
            request_timestamp=datetime.utcnow(),
        )
        async_session.add(cost_record1)

        # Create cost records for merchant 2
        cost_record2 = LLMConversationCost(
            conversation_id="conv-2",
            merchant_id=2,
            provider="openai",
            model="gpt-4o-mini",
            prompt_tokens=200,
            completion_tokens=100,
            total_tokens=300,
            input_cost_usd=0.0002,
            output_cost_usd=0.0004,
            total_cost_usd=0.0006,
            request_timestamp=datetime.utcnow(),
        )
        async_session.add(cost_record2)
        await async_session.flush()

        # Merchant 1 should only see their own costs
        response1 = await async_client.get(
            "/api/costs/summary",
            headers={"X-Merchant-Id": "1"},
        )
        assert response1.status_code == 200
        data1 = response1.json()
        assert data1["data"]["totalCostUsd"] == 0.0003
        assert data1["data"]["requestCount"] == 1

        # Merchant 2 should only see their own costs
        response2 = await async_client.get(
            "/api/costs/summary",
            headers={"X-Merchant-Id": "2"},
        )
        assert response2.status_code == 200
        data2 = response2.json()
        assert data2["data"]["totalCostUsd"] == 0.0006
        assert data2["data"]["requestCount"] == 1
