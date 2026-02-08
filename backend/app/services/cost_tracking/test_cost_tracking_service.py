"""Unit tests for Cost Tracking Service."""

from __future__ import annotations

from datetime import datetime, timedelta
import pytest

from app.services.cost_tracking.cost_tracking_service import CostTrackingService
from app.models.llm_conversation_cost import LLMConversationCost


@pytest.mark.asyncio
async def test_create_cost_record_with_valid_data(db_session):
    """Test cost record creation with valid data."""
    service = CostTrackingService()

    cost_record = await service.create_cost_record(
        db=db_session,
        conversation_id="test-conv-1",
        merchant_id=1,
        provider="openai",
        model="gpt-4o-mini",
        prompt_tokens=100,
        completion_tokens=50,
        total_tokens=150,
        input_cost_usd=0.0001,
        output_cost_usd=0.0002,
        total_cost_usd=0.0003,
        processing_time_ms=1250.0,
    )

    assert cost_record.conversation_id == "test-conv-1"
    assert cost_record.merchant_id == 1
    assert cost_record.provider == "openai"
    assert cost_record.model == "gpt-4o-mini"
    assert cost_record.prompt_tokens == 100
    assert cost_record.completion_tokens == 50
    assert cost_record.total_tokens == 150
    assert cost_record.input_cost_usd == 0.0001
    assert cost_record.output_cost_usd == 0.0002
    assert cost_record.total_cost_usd == 0.0003
    assert cost_record.processing_time_ms == 1250.0
    assert cost_record.id is not None


@pytest.mark.asyncio
async def test_create_cost_record_with_zero_cost_ollama(db_session):
    """Test cost record creation for Ollama (zero cost)."""
    service = CostTrackingService()

    cost_record = await service.create_cost_record(
        db=db_session,
        conversation_id="test-conv-2",
        merchant_id=1,
        provider="ollama",
        model="llama2",
        prompt_tokens=500,
        completion_tokens=300,
        total_tokens=800,
        input_cost_usd=0.0,
        output_cost_usd=0.0,
        total_cost_usd=0.0,
        processing_time_ms=2000.0,
    )

    assert cost_record.total_cost_usd == 0.0
    assert cost_record.provider == "ollama"


@pytest.mark.asyncio
async def test_create_cost_record_validation_empty_conversation_id(db_session):
    """Test that empty conversation_id raises ValueError."""
    service = CostTrackingService()

    with pytest.raises(ValueError, match="conversation_id is required"):
        await service.create_cost_record(
            db=db_session,
            conversation_id="",
            merchant_id=1,
            provider="openai",
            model="gpt-4o-mini",
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150,
            input_cost_usd=0.0001,
            output_cost_usd=0.0002,
            total_cost_usd=0.0003,
        )


@pytest.mark.asyncio
async def test_create_cost_record_validation_negative_tokens(db_session):
    """Test that negative token counts raise ValueError."""
    service = CostTrackingService()

    with pytest.raises(ValueError, match="token counts must be non-negative"):
        await service.create_cost_record(
            db=db_session,
            conversation_id="test-conv",
            merchant_id=1,
            provider="openai",
            model="gpt-4o-mini",
            prompt_tokens=-10,
            completion_tokens=50,
            total_tokens=40,
            input_cost_usd=0.0001,
            output_cost_usd=0.0002,
            total_cost_usd=0.0003,
        )


@pytest.mark.asyncio
async def test_create_cost_record_validation_negative_cost(db_session):
    """Test that negative cost raises ValueError."""
    service = CostTrackingService()

    with pytest.raises(ValueError, match="total_cost_usd must be non-negative"):
        await service.create_cost_record(
            db=db_session,
            conversation_id="test-conv",
            merchant_id=1,
            provider="openai",
            model="gpt-4o-mini",
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150,
            input_cost_usd=0.0001,
            output_cost_usd=0.0002,
            total_cost_usd=-0.0003,
        )


@pytest.mark.asyncio
async def test_create_cost_record_validation_missing_merchant_id(db_session):
    """Test that missing merchant_id raises ValueError."""
    service = CostTrackingService()

    with pytest.raises(ValueError, match="merchant_id is required"):
        await service.create_cost_record(
            db=db_session,
            conversation_id="test-conv",
            merchant_id=0,  # Invalid merchant ID
            provider="openai",
            model="gpt-4o-mini",
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150,
            input_cost_usd=0.0001,
            output_cost_usd=0.0002,
            total_cost_usd=0.0003,
        )


@pytest.mark.asyncio
async def test_get_conversation_costs_single_request(db_session):
    """Test getting conversation costs with single request."""
    service = CostTrackingService()

    # Create a cost record
    await service.create_cost_record(
        db=db_session,
        conversation_id="test-conv-single",
        merchant_id=1,
        provider="openai",
        model="gpt-4o-mini",
        prompt_tokens=250,
        completion_tokens=150,
        total_tokens=400,
        input_cost_usd=0.000375,
        output_cost_usd=0.00009,
        total_cost_usd=0.000465,
        processing_time_ms=1250.0,
    )

    # Get conversation costs
    costs = await service.get_conversation_costs(
        db=db_session,
        merchant_id=1,
        conversation_id="test-conv-single",
    )

    assert costs["conversationId"] == "test-conv-single"
    assert costs["totalCostUsd"] == 0.0005  # Rounded from 0.000465
    assert costs["totalTokens"] == 400
    assert costs["requestCount"] == 1
    assert costs["avgCostPerRequest"] == 0.0005  # Rounded from 0.000465
    assert costs["provider"] == "openai"
    assert costs["model"] == "gpt-4o-mini"
    assert len(costs["requests"]) == 1
    assert costs["requests"][0]["totalTokens"] == 400


@pytest.mark.asyncio
async def test_get_conversation_costs_multiple_requests(db_session):
    """Test getting conversation costs with multiple requests."""
    service = CostTrackingService()
    conv_id = "test-conv-multi"

    # Create multiple cost records
    await service.create_cost_record(
        db=db_session,
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
        processing_time_ms=1250.0,
    )

    await service.create_cost_record(
        db=db_session,
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
        processing_time_ms=1500.0,
    )

    # Get conversation costs
    costs = await service.get_conversation_costs(
        db=db_session,
        merchant_id=1,
        conversation_id=conv_id,
    )

    assert costs["requestCount"] == 2
    assert costs["totalCostUsd"] == 0.0010  # 0.000465 + 0.00057 rounded
    assert costs["totalTokens"] == 900  # 400 + 500
    assert costs["avgCostPerRequest"] == 0.0005  # Average of 2 requests
    assert len(costs["requests"]) == 2


@pytest.mark.asyncio
async def test_get_conversation_costs_not_found(db_session):
    """Test that non-existent conversation raises ValueError."""
    service = CostTrackingService()

    with pytest.raises(ValueError, match="No cost data found for conversation"):
        await service.get_conversation_costs(
            db=db_session,
            merchant_id=1,
            conversation_id="non-existent-conv",
        )


@pytest.mark.asyncio
async def test_merchant_isolation_conversation_costs(db_session):
    """Test that merchants can only access their own cost data."""
    service = CostTrackingService()
    conv_id = "test-conv-isolation"

    # Create cost record for merchant 1
    await service.create_cost_record(
        db=db_session,
        conversation_id=conv_id,
        merchant_id=1,
        provider="openai",
        model="gpt-4o-mini",
        prompt_tokens=100,
        completion_tokens=50,
        total_tokens=150,
        input_cost_usd=0.0001,
        output_cost_usd=0.0002,
        total_cost_usd=0.0003,
    )

    # Merchant 2 should not see merchant 1's costs
    with pytest.raises(ValueError, match="No cost data found for conversation"):
        await service.get_conversation_costs(
            db=db_session,
            merchant_id=2,  # Different merchant
            conversation_id=conv_id,
        )


@pytest.mark.asyncio
async def test_get_cost_summary_empty(db_session):
    """Test cost summary with no data."""
    service = CostTrackingService()

    # Explicit cleanup: delete any existing cost records for merchant_id=1
    from sqlalchemy import delete
    from app.models.llm_conversation_cost import LLMConversationCost
    await db_session.execute(delete(LLMConversationCost).where(LLMConversationCost.merchant_id == 1))
    await db_session.commit()

    summary = await service.get_cost_summary(
        db=db_session,
        merchant_id=1,
    )

    assert summary["totalCostUsd"] == 0.0
    assert summary["totalTokens"] == 0
    assert summary["requestCount"] == 0
    assert summary["avgCostPerRequest"] == 0.0
    assert summary["topConversations"] == []
    assert summary["costsByProvider"] == {}
    assert summary["dailyBreakdown"] == []


@pytest.mark.asyncio
async def test_get_cost_summary_with_data(db_session):
    """Test cost summary with actual cost data."""
    service = CostTrackingService()

    # Explicit cleanup: delete any existing cost records for merchant_id=1
    from sqlalchemy import delete
    from app.models.llm_conversation_cost import LLMConversationCost
    await db_session.execute(delete(LLMConversationCost).where(LLMConversationCost.merchant_id == 1))
    await db_session.commit()

    # Create cost records for multiple conversations
    await service.create_cost_record(
        db=db_session,
        conversation_id="conv-1",
        merchant_id=1,
        provider="openai",
        model="gpt-4o-mini",
        prompt_tokens=1000,
        completion_tokens=500,
        total_tokens=1500,
        input_cost_usd=0.0015,
        output_cost_usd=0.0003,
        total_cost_usd=0.0018,
    )

    await service.create_cost_record(
        db=db_session,
        conversation_id="conv-2",
        merchant_id=1,
        provider="ollama",
        model="llama2",
        prompt_tokens=500,
        completion_tokens=300,
        total_tokens=800,
        input_cost_usd=0.0,
        output_cost_usd=0.0,
        total_cost_usd=0.0,
    )

    await service.create_cost_record(
        db=db_session,
        conversation_id="conv-1",
        merchant_id=1,
        provider="openai",
        model="gpt-4o-mini",
        prompt_tokens=200,
        completion_tokens=100,
        total_tokens=300,
        input_cost_usd=0.0003,
        output_cost_usd=0.00006,
        total_cost_usd=0.00036,
    )

    # Get summary
    summary = await service.get_cost_summary(
        db=db_session,
        merchant_id=1,
    )

    assert summary["totalCostUsd"] == 0.0022  # 0.0018 + 0.0 + 0.00036
    assert summary["totalTokens"] == 2600  # 1500 + 800 + 300
    assert summary["requestCount"] == 3
    assert summary["avgCostPerRequest"] == 0.0007  # 0.0022 / 3
    assert len(summary["topConversations"]) == 2
    assert summary["costsByProvider"]["openai"]["costUsd"] == 0.0022
    assert summary["costsByProvider"]["openai"]["requests"] == 2
    assert summary["costsByProvider"]["ollama"]["costUsd"] == 0.0
    assert summary["costsByProvider"]["ollama"]["requests"] == 1


@pytest.mark.asyncio
async def test_get_cost_summary_with_date_range(db_session):
    """Test cost summary with date range filtering."""
    service = CostTrackingService()

    # Explicit cleanup: delete any existing cost records for merchant_id=1
    from sqlalchemy import delete
    await db_session.execute(delete(LLMConversationCost).where(LLMConversationCost.merchant_id == 1))
    await db_session.commit()

    # Create cost records on different dates
    today = datetime.utcnow()
    yesterday = today - timedelta(days=1)

    # Create records directly with specific timestamps
    record1 = LLMConversationCost(
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
        request_timestamp=yesterday,
    )
    db_session.add(record1)

    record2 = LLMConversationCost(
        conversation_id="conv-2",
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
    db_session.add(record2)
    await db_session.flush()

    # Get summary for today only
    date_from_str = today.date().isoformat()
    summary = await service.get_cost_summary(
        db=db_session,
        merchant_id=1,
        date_from=date_from_str,
    )

    # Should only include today's record
    assert summary["totalCostUsd"] == 0.0006
    assert summary["requestCount"] == 1


@pytest.mark.asyncio
async def test_calculate_daily_costs_multiple_days(db_session):
    """Test daily breakdown calculation across multiple days."""
    service = CostTrackingService()

    # Explicit cleanup: delete any existing cost records for merchant_id=1
    from sqlalchemy import delete
    await db_session.execute(delete(LLMConversationCost).where(LLMConversationCost.merchant_id == 1))
    await db_session.commit()

    # Create records across 3 days
    today = datetime.utcnow()
    yesterday = today - timedelta(days=1)
    day_before = today - timedelta(days=2)

    for date, count in [(day_before, 3), (yesterday, 2), (today, 1)]:
        for i in range(count):
            record = LLMConversationCost(
                conversation_id=f"conv-{date.day}-{i}",
                merchant_id=1,
                provider="openai",
                model="gpt-4o-mini",
                prompt_tokens=100,
                completion_tokens=50,
                total_tokens=150,
                input_cost_usd=0.0001,
                output_cost_usd=0.0002,
                total_cost_usd=0.0003,
                request_timestamp=date,
            )
            db_session.add(record)

    await db_session.flush()

    # Get summary with date range
    date_from = (today - timedelta(days=3)).date().isoformat()
    summary = await service.get_cost_summary(
        db=db_session,
        merchant_id=1,
        date_from=date_from,
    )

    # Should have 3 days of breakdown
    assert len(summary["dailyBreakdown"]) == 3
    # Check total counts
    total_requests = sum(d["requestCount"] for d in summary["dailyBreakdown"])
    assert total_requests == 6  # 3 + 2 + 1


@pytest.mark.asyncio
async def test_merchant_isolation_cost_summary(db_session):
    """Test merchant isolation in cost summary."""
    service = CostTrackingService()

    # Explicit cleanup: delete any existing cost records for both merchants
    from sqlalchemy import delete
    await db_session.execute(delete(LLMConversationCost))
    await db_session.commit()

    # Create cost records for merchant 1
    await service.create_cost_record(
        db=db_session,
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
    )

    # Create cost records for merchant 2
    await service.create_cost_record(
        db=db_session,
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
    )

    # Merchant 1 should only see their own costs
    summary1 = await service.get_cost_summary(
        db=db_session,
        merchant_id=1,
    )
    assert summary1["totalCostUsd"] == 0.0003
    assert summary1["requestCount"] == 1

    # Merchant 2 should only see their own costs
    summary2 = await service.get_cost_summary(
        db=db_session,
        merchant_id=2,
    )
    assert summary2["totalCostUsd"] == 0.0006
    assert summary2["requestCount"] == 1
