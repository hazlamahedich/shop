"""Tests for LLM Conversation Cost ORM model.

Tests cost tracking, token counting, and merchant relationship.
"""

from __future__ import annotations

import pytest
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.llm_conversation_cost import LLMConversationCost
from app.models.merchant import Merchant
from app.core.database import async_session


@pytest.mark.asyncio
async def test_conversation_cost_creation(db_session: AsyncSession) -> None:
    """Test creating a conversation cost record."""

    # Create merchant
    merchant = Merchant(
        merchant_key="test-merchant-cost",
        platform="fly.io",
        status="active",
    )
    db_session.add(merchant)
    await db_session.commit()
    await db_session.refresh(merchant)

    # Create conversation cost record
    cost = LLMConversationCost(
        conversation_id="fb_psid_12345",
        merchant_id=merchant.id,
        provider="openai",
        model="gpt-4o-mini",
        prompt_tokens=100,
        completion_tokens=50,
        total_tokens=150,
        input_cost_usd=0.000015,
        output_cost_usd=0.000030,
        total_cost_usd=0.000045,
        processing_time_ms=234.5,
    )
    db_session.add(cost)
    await db_session.commit()
    await db_session.refresh(cost)

    assert cost.id is not None
    assert cost.conversation_id == "fb_psid_12345"
    assert cost.merchant_id == merchant.id
    assert cost.provider == "openai"
    assert cost.model == "gpt-4o-mini"
    assert cost.prompt_tokens == 100
    assert cost.completion_tokens == 50
    assert cost.total_tokens == 150
    assert cost.total_cost_usd == 0.000045
    assert cost.processing_time_ms == 234.5


@pytest.mark.asyncio
async def test_conversation_cost_ollama_free(db_session: AsyncSession) -> None:
    """Test that Ollama costs are zero (free, local)."""

    # Create merchant
    merchant = Merchant(
        merchant_key="test-merchant-ollama-cost",
        platform="fly.io",
        status="active",
    )
    db_session.add(merchant)
    await db_session.commit()
    await db_session.refresh(merchant)

    # Create Ollama cost record (should be free)
    cost = LLMConversationCost(
        conversation_id="fb_psid_ollama",
        merchant_id=merchant.id,
        provider="ollama",
        model="llama3",
        prompt_tokens=1000,
        completion_tokens=500,
        total_tokens=1500,
        input_cost_usd=0.0,
        output_cost_usd=0.0,
        total_cost_usd=0.0,
        processing_time_ms=1234.5,
    )
    db_session.add(cost)
    await db_session.commit()
    await db_session.refresh(cost)

    assert cost.provider == "ollama"
    assert cost.total_cost_usd == 0.0
    assert cost.input_cost_usd == 0.0
    assert cost.output_cost_usd == 0.0


@pytest.mark.asyncio
async def test_conversation_cost_multiple_requests(db_session: AsyncSession) -> None:
    """Test tracking multiple requests for same conversation."""

    # Create merchant
    merchant = Merchant(
        merchant_key="test-merchant-multiple-costs",
        platform="fly.io",
        status="active",
    )
    db_session.add(merchant)
    await db_session.commit()
    await db_session.refresh(merchant)

    conversation_id = "fb_psid_multi"

    # Create first request
    cost1 = LLMConversationCost(
        conversation_id=conversation_id,
        merchant_id=merchant.id,
        provider="openai",
        model="gpt-4o-mini",
        prompt_tokens=100,
        completion_tokens=50,
        total_tokens=150,
        input_cost_usd=0.000015,
        output_cost_usd=0.000030,
        total_cost_usd=0.000045,
    )
    db_session.add(cost1)
    await db_session.commit()

    # Create second request for same conversation
    cost2 = LLMConversationCost(
        conversation_id=conversation_id,
        merchant_id=merchant.id,
        provider="openai",
        model="gpt-4o-mini",
        prompt_tokens=200,
        completion_tokens=100,
        total_tokens=300,
        input_cost_usd=0.000030,
        output_cost_usd=0.000060,
        total_cost_usd=0.000090,
    )
    db_session.add(cost2)
    await db_session.commit()

    # Query all costs for this conversation
    result = await db_session.execute(
        select(LLMConversationCost)
        .where(LLMConversationCost.conversation_id == conversation_id)
        .order_by(LLMConversationCost.created_at)
    )
    costs = result.scalars().all()

    assert len(costs) == 2
    assert costs[0].total_cost_usd == 0.000045
    assert costs[1].total_cost_usd == 0.000090


@pytest.mark.asyncio
async def test_conversation_cost_aggregation_query(db_session: AsyncSession) -> None:
    """Test aggregating costs by conversation."""

    # Create merchant
    merchant = Merchant(
        merchant_key="test-merchant-agg-costs",
        platform="fly.io",
        status="active",
    )
    db_session.add(merchant)
    await db_session.commit()
    await db_session.refresh(merchant)

    conversation_id = "fb_psid_aggregation"

    # Add multiple cost records
    for i in range(3):
        cost = LLMConversationCost(
            conversation_id=conversation_id,
            merchant_id=merchant.id,
            provider="openai",
            model="gpt-4o-mini",
            prompt_tokens=100 * (i + 1),
            completion_tokens=50 * (i + 1),
            total_tokens=150 * (i + 1),
            input_cost_usd=0.000015 * (i + 1),
            output_cost_usd=0.000030 * (i + 1),
            total_cost_usd=0.000045 * (i + 1),
        )
        db_session.add(cost)
    await db_session.commit()

    # Aggregate costs for conversation
    from sqlalchemy import func

    result = await db_session.execute(
        select(
            func.sum(LLMConversationCost.total_tokens).label("total_tokens"),
            func.sum(LLMConversationCost.total_cost_usd).label("total_cost"),
            func.count(LLMConversationCost.id).label("request_count"),
        ).where(LLMConversationCost.conversation_id == conversation_id)
    )
    row = result.one()

    assert row.total_tokens == 900  # 150 + 300 + 450
    assert row.total_cost == pytest.approx(0.00027)  # 0.000045 + 0.00009 + 0.000135
    assert row.request_count == 3


@pytest.mark.asyncio
async def test_conversation_cost_timestamp_index(db_session: AsyncSession) -> None:
    """Test that request_timestamp is indexed for efficient queries."""

    # Create merchant
    merchant = Merchant(
        merchant_key="test-merchant-timestamp-index",
        platform="fly.io",
        status="active",
    )
    db_session.add(merchant)
    await db_session.commit()
    await db_session.refresh(merchant)

    # Create cost with specific timestamp
    from datetime import timedelta

    past_time = datetime.utcnow() - timedelta(hours=1)
    cost = LLMConversationCost(
        conversation_id="fb_psid_timestamp",
        merchant_id=merchant.id,
        provider="openai",
        model="gpt-4o-mini",
        prompt_tokens=100,
        completion_tokens=50,
        total_tokens=150,
        input_cost_usd=0.000015,
        output_cost_usd=0.000030,
        total_cost_usd=0.000045,
        request_timestamp=past_time,
    )
    db_session.add(cost)
    await db_session.commit()
    await db_session.refresh(cost)

    # Query by timestamp range
    result = await db_session.execute(
        select(LLMConversationCost)
        .where(
            LLMConversationCost.request_timestamp
            >= datetime.utcnow() - timedelta(hours=2)
        )
        .where(LLMConversationCost.merchant_id == merchant.id)
    )
    costs = result.scalars().all()

    assert len(costs) == 1
    assert costs[0].request_timestamp == past_time
