"""Unit tests for Monthly Spend Calculation (Story 3-7)."""

from __future__ import annotations

from datetime import datetime, timedelta
from sqlalchemy import delete, select
import pytest

from app.services.cost_tracking.cost_tracking_service import CostTrackingService
from app.models.llm_conversation_cost import LLMConversationCost
from app.models.merchant import Merchant


@pytest.mark.asyncio
async def test_get_monthly_spend_below_budget(db_session):
    """Test monthly spend calculation when below budget (< 50%)."""
    service = CostTrackingService()

    # Clean up existing data
    from sqlalchemy import delete
    await db_session.execute(delete(LLMConversationCost).where(LLMConversationCost.merchant_id == 1))
    await db_session.commit()

    # Set budget cap to $100
    from app.models.merchant import Merchant
    result = await db_session.execute(select(Merchant).where(Merchant.id == 1))
    merchant = result.scalars().first()
    if merchant:
        current_config = merchant.config or {}
        new_config = dict(current_config)
        new_config["budget_cap"] = 100.0
        merchant.config = new_config
        await db_session.commit()

    # Create cost records for current month (total $25)
    today = datetime.utcnow()
    month_start = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    for i in range(5):
        record = LLMConversationCost(
            conversation_id=f"conv-{i}",
            merchant_id=1,
            provider="openai",
            model="gpt-4o-mini",
            prompt_tokens=1000,
            completion_tokens=500,
            total_tokens=1500,
            input_cost_usd=0.001,
            output_cost_usd=0.004,
            total_cost_usd=5.0,
            request_timestamp=month_start + timedelta(days=i),
        )
        db_session.add(record)
    await db_session.commit()

    # Get monthly spend
    monthly_data = await service.get_monthly_spend(db=db_session, merchant_id=1)

    assert monthly_data["monthlySpend"] == 25.0
    assert monthly_data["budgetCap"] == 100.0
    assert monthly_data["budgetPercentage"] == 25.0
    assert monthly_data["budgetStatus"] == "green"


@pytest.mark.asyncio
async def test_get_monthly_spend_medium_budget(db_session):
    """Test monthly spend at medium budget level (50-80%)."""
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

    # Create cost records for current month (total $60 = 60%)
    today = datetime.utcnow()
    month_start = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    for i in range(12):
        record = LLMConversationCost(
            conversation_id=f"conv-{i}",
            merchant_id=1,
            provider="openai",
            model="gpt-4o-mini",
            prompt_tokens=1000,
            completion_tokens=500,
            total_tokens=1500,
            input_cost_usd=0.001,
            output_cost_usd=0.004,
            total_cost_usd=5.0,
            request_timestamp=month_start + timedelta(days=i),
        )
        db_session.add(record)
    await db_session.commit()

    # Get monthly spend
    monthly_data = await service.get_monthly_spend(db=db_session, merchant_id=1)

    assert monthly_data["monthlySpend"] == 60.0
    assert monthly_data["budgetCap"] == 100.0
    assert monthly_data["budgetPercentage"] == 60.0
    assert monthly_data["budgetStatus"] == "yellow"


@pytest.mark.asyncio
async def test_get_monthly_spend_high_budget(db_session):
    """Test monthly spend at high budget level (> 80%)."""
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

    # Create cost records for current month (total $85 = 85%)
    today = datetime.utcnow()
    month_start = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    for i in range(17):
        record = LLMConversationCost(
            conversation_id=f"conv-{i}",
            merchant_id=1,
            provider="openai",
            model="gpt-4o-mini",
            prompt_tokens=1000,
            completion_tokens=500,
            total_tokens=1500,
            input_cost_usd=0.001,
            output_cost_usd=0.004,
            total_cost_usd=5.0,
            request_timestamp=month_start + timedelta(hours=i * 2),
        )
        db_session.add(record)
    await db_session.commit()

    # Get monthly spend
    monthly_data = await service.get_monthly_spend(db=db_session, merchant_id=1)

    assert monthly_data["monthlySpend"] == 85.0
    assert monthly_data["budgetCap"] == 100.0
    assert monthly_data["budgetPercentage"] == 85.0
    assert monthly_data["budgetStatus"] == "red"


@pytest.mark.asyncio
async def test_get_monthly_spend_null_budget_cap(db_session):
    """Test monthly spend when no budget cap is set."""
    service = CostTrackingService()

    # Clean up existing data
    from sqlalchemy import delete
    await db_session.execute(delete(LLMConversationCost).where(LLMConversationCost.merchant_id == 1))
    await db_session.commit()

    # Remove budget cap
    from app.models.merchant import Merchant
    from sqlalchemy import select
    result = await db_session.execute(select(Merchant).where(Merchant.id == 1))
    merchant = result.scalars().first()
    if merchant:
        current_config = merchant.config or {}
        new_config = dict(current_config)
        if "budget_cap" in new_config:
            del new_config["budget_cap"]
        merchant.config = new_config
        await db_session.commit()

    # Create cost records for current month
    today = datetime.utcnow()
    month_start = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    record = LLMConversationCost(
        conversation_id="conv-1",
        merchant_id=1,
        provider="openai",
        model="gpt-4o-mini",
        prompt_tokens=1000,
        completion_tokens=500,
        total_tokens=1500,
        input_cost_usd=0.001,
        output_cost_usd=0.004,
        total_cost_usd=5.0,
        request_timestamp=month_start,
    )
    db_session.add(record)
    await db_session.commit()

    # Get monthly spend
    monthly_data = await service.get_monthly_spend(db=db_session, merchant_id=1)

    assert monthly_data["monthlySpend"] == 5.0
    assert monthly_data["budgetCap"] is None
    assert monthly_data["budgetPercentage"] is None
    assert monthly_data["budgetStatus"] == "no_limit"


@pytest.mark.asyncio
async def test_get_monthly_spend_no_cost_data(db_session):
    """Test monthly spend when there's no cost data for current month."""
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

    # Get monthly spend with no data
    monthly_data = await service.get_monthly_spend(db=db_session, merchant_id=1)

    assert monthly_data["monthlySpend"] == 0.0
    assert monthly_data["budgetCap"] == 100.0
    assert monthly_data["budgetPercentage"] == 0.0
    assert monthly_data["budgetStatus"] == "green"


@pytest.mark.asyncio
async def test_get_monthly_spend_month_boundary(db_session):
    """Test that monthly spend only includes current month's data."""
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

    # Create cost records: some in previous month, some in current month
    today = datetime.utcnow()
    month_start = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    last_month = month_start - timedelta(days=1)

    # Previous month record (should NOT be included)
    record_prev = LLMConversationCost(
        conversation_id="conv-prev",
        merchant_id=1,
        provider="openai",
        model="gpt-4o-mini",
        prompt_tokens=1000,
        completion_tokens=500,
        total_tokens=1500,
        input_cost_usd=0.01,
        output_cost_usd=0.04,
        total_cost_usd=50.0,
        request_timestamp=last_month,
    )
    db_session.add(record_prev)

    # Current month record (should be included)
    record_curr = LLMConversationCost(
        conversation_id="conv-curr",
        merchant_id=1,
        provider="openai",
        model="gpt-4o-mini",
        prompt_tokens=1000,
        completion_tokens=500,
        total_tokens=1500,
        input_cost_usd=0.001,
        output_cost_usd=0.004,
        total_cost_usd=5.0,
        request_timestamp=month_start + timedelta(days=5),
    )
    db_session.add(record_curr)
    await db_session.commit()

    # Get monthly spend
    monthly_data = await service.get_monthly_spend(db=db_session, merchant_id=1)

    # Should only include current month's data
    assert monthly_data["monthlySpend"] == 5.0
    assert monthly_data["budgetPercentage"] == 5.0
