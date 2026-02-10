"""Unit tests for Projection Calculation (Story 3-7)."""

from __future__ import annotations

from datetime import datetime, timedelta
from sqlalchemy import delete, select
import pytest

from app.services.cost_tracking.cost_tracking_service import CostTrackingService
from app.models.llm_conversation_cost import LLMConversationCost
from app.models.merchant import Merchant


@pytest.mark.asyncio
async def test_get_projection_with_sufficient_data(db_session):
    """Test projection calculation with > 3 days of data."""
    service = CostTrackingService()

    # Clean up existing data
    from sqlalchemy import delete
    await db_session.execute(delete(LLMConversationCost).where(LLMConversationCost.merchant_id == 1))
    await db_session.commit()

    # Set budget cap
    from app.models.merchant import Merchant
    from sqlalchemy import select
    result = await db_session.execute(select(Merchant).where(Merchant.id == 1))
    merchant = result.scalars().first()
    if merchant:
        current_config = merchant.config or {}
        new_config = dict(current_config)
        new_config["budget_cap"] = 100.0
        merchant.config = new_config
        await db_session.commit()

    # Day 15 of 30-day month with $25 spent so far
    today = datetime.utcnow()
    month_start = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # Create 15 days of cost data: $25 total, so $1.67/day average
    for day in range(15):
        daily_spend = 25.0 / 15  # ~$1.67 per day
        record = LLMConversationCost(
            conversation_id=f"conv-day-{day}",
            merchant_id=1,
            provider="openai",
            model="gpt-4o-mini",
            prompt_tokens=1000,
            completion_tokens=500,
            total_tokens=1500,
            input_cost_usd=daily_spend * 0.2,
            output_cost_usd=daily_spend * 0.8,
            total_cost_usd=daily_spend,
            request_timestamp=month_start + timedelta(days=day),
        )
        db_session.add(record)
    await db_session.commit()

    # Get projection
    projection_data = await service.get_monthly_projection(db=db_session, merchant_id=1)

    # Expected: daily avg = $25/15 = $1.67, projected = $1.67 * 30 = $50
    assert projection_data["monthlySpend"] == 25.0
    assert projection_data["daysSoFar"] == 15
    assert projection_data["daysInMonth"] in [28, 29, 30, 31]
    assert projection_data["dailyAverage"] == pytest.approx(1.67, rel=0.01)
    assert projection_data["projectedSpend"] == pytest.approx(50.0, rel=0.1)
    assert projection_data["projectionAvailable"] is True


@pytest.mark.asyncio
async def test_get_projection_insufficient_data(db_session):
    """Test projection is suppressed with < 3 days of data."""
    service = CostTrackingService()

    # Clean up existing data
    from sqlalchemy import delete
    await db_session.execute(delete(LLMConversationCost).where(LLMConversationCost.merchant_id == 1))
    await db_session.commit()

    # Set budget cap
    from app.models.merchant import Merchant
    from sqlalchemy import select
    result = await db_session.execute(select(Merchant).where(Merchant.id == 1))
    merchant = result.scalars().first()
    if merchant:
        current_config = merchant.config or {}
        new_config = dict(current_config)
        new_config["budget_cap"] = 100.0
        merchant.config = new_config
        await db_session.commit()

    # Day 2 of month with only 2 days of data
    today = datetime.utcnow()
    month_start = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    for day in range(2):
        record = LLMConversationCost(
            conversation_id=f"conv-day-{day}",
            merchant_id=1,
            provider="openai",
            model="gpt-4o-mini",
            prompt_tokens=1000,
            completion_tokens=500,
            total_tokens=1500,
            input_cost_usd=1.0,
            output_cost_usd=4.0,
            total_cost_usd=5.0,
            request_timestamp=month_start + timedelta(days=day),
        )
        db_session.add(record)
    await db_session.commit()

    # Get projection
    projection_data = await service.get_monthly_projection(db=db_session, merchant_id=1)

    # Projection should not be available
    assert projection_data["monthlySpend"] == 10.0
    assert projection_data["daysSoFar"] == 2
    assert projection_data["projectionAvailable"] is False
    assert projection_data["projectedSpend"] is None


@pytest.mark.asyncio
async def test_get_projection_first_day_of_month(db_session):
    """Test projection on day 1 (no projection available)."""
    service = CostTrackingService()

    # Clean up existing data
    from sqlalchemy import delete
    await db_session.execute(delete(LLMConversationCost).where(LLMConversationCost.merchant_id == 1))
    await db_session.commit()

    # Set budget cap
    from app.models.merchant import Merchant
    from sqlalchemy import select
    result = await db_session.execute(select(Merchant).where(Merchant.id == 1))
    merchant = result.scalars().first()
    if merchant:
        current_config = merchant.config or {}
        new_config = dict(current_config)
        new_config["budget_cap"] = 100.0
        merchant.config = new_config
        await db_session.commit()

    # First day of month with only 1 day of data
    today = datetime.utcnow()
    month_start = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    record = LLMConversationCost(
        conversation_id="conv-day-0",
        merchant_id=1,
        provider="openai",
        model="gpt-4o-mini",
        prompt_tokens=1000,
        completion_tokens=500,
        total_tokens=1500,
        input_cost_usd=1.0,
        output_cost_usd=4.0,
        total_cost_usd=5.0,
        request_timestamp=month_start,
    )
    db_session.add(record)
    await db_session.commit()

    # Get projection
    projection_data = await service.get_monthly_projection(db=db_session, merchant_id=1)

    assert projection_data["monthlySpend"] == 5.0
    assert projection_data["daysSoFar"] == 1
    assert projection_data["projectionAvailable"] is False


@pytest.mark.asyncio
async def test_get_projection_zero_spend(db_session):
    """Test projection with zero spend (edge case)."""
    service = CostTrackingService()

    # Clean up existing data
    from sqlalchemy import delete
    await db_session.execute(delete(LLMConversationCost).where(LLMConversationCost.merchant_id == 1))
    await db_session.commit()

    # Set budget cap
    from app.models.merchant import Merchant
    from sqlalchemy import select
    result = await db_session.execute(select(Merchant).where(Merchant.id == 1))
    merchant = result.scalars().first()
    if merchant:
        current_config = merchant.config or {}
        new_config = dict(current_config)
        new_config["budget_cap"] = 100.0
        merchant.config = new_config
        await db_session.commit()

    # No cost records for current month
    projection_data = await service.get_monthly_projection(db=db_session, merchant_id=1)

    assert projection_data["monthlySpend"] == 0.0
    assert projection_data["projectionAvailable"] is False


@pytest.mark.asyncio
async def test_get_projection_high_daily_spend(db_session):
    """Test projection with high daily spend rate."""
    service = CostTrackingService()

    # Clean up existing data
    from sqlalchemy import delete
    await db_session.execute(delete(LLMConversationCost).where(LLMConversationCost.merchant_id == 1))
    await db_session.commit()

    # Set budget cap to $100
    from app.models.merchant import Merchant
    from sqlalchemy import select
    result = await db_session.execute(select(Merchant).where(Merchant.id == 1))
    merchant = result.scalars().first()
    if merchant:
        current_config = merchant.config or {}
        new_config = dict(current_config)
        new_config["budget_cap"] = 100.0
        merchant.config = new_config
        await db_session.commit()

    # Day 10 with $80 spent (very high daily rate)
    today = datetime.utcnow()
    month_start = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    for day in range(10):
        daily_spend = 8.0  # $8 per day
        record = LLMConversationCost(
            conversation_id=f"conv-day-{day}",
            merchant_id=1,
            provider="openai",
            model="gpt-4o-mini",
            prompt_tokens=1000,
            completion_tokens=500,
            total_tokens=1500,
            input_cost_usd=daily_spend * 0.2,
            output_cost_usd=daily_spend * 0.8,
            total_cost_usd=daily_spend,
            request_timestamp=month_start + timedelta(days=day),
        )
        db_session.add(record)
    await db_session.commit()

    # Get projection
    projection_data = await service.get_monthly_projection(db=db_session, merchant_id=1)

    # Expected: daily avg = $8, projected = $8 * days_in_month (~$240)
    assert projection_data["monthlySpend"] == 80.0
    assert projection_data["daysSoFar"] == 10
    assert projection_data["dailyAverage"] == 8.0
    assert projection_data["projectedSpend"] == pytest.approx(8.0 * projection_data["daysInMonth"], rel=0.1)
    assert projection_data["projectionAvailable"] is True
    assert projection_data["projectedExceedsBudget"] is True
