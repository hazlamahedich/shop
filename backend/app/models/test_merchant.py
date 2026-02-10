"""Tests for Merchant ORM model.

Tests model validation, relationships, and CRUD operations.
Including personality configuration fields (Story 1.10).
"""

from __future__ import annotations

import pytest
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.merchant import Merchant, PersonalityType
from app.core.database import async_session


@pytest.mark.asyncio
async def test_merchant_creation(db_session: AsyncSession) -> None:
    """Test creating a merchant record with basic fields."""

    merchant = Merchant(
        merchant_key="test-merchant-basic",
        platform="fly.io",
        status="active",
    )
    db_session.add(merchant)
    await db_session.commit()
    await db_session.refresh(merchant)

    assert merchant.id is not None
    assert merchant.merchant_key == "test-merchant-basic"
    assert merchant.platform == "fly.io"
    assert merchant.status == "active"


@pytest.mark.asyncio
async def test_merchant_with_personality_friendly(db_session: AsyncSession) -> None:
    """Test creating a merchant with friendly personality (Story 1.10 AC 3)."""

    merchant = Merchant(
        merchant_key="test-merchant-friendly",
        platform="fly.io",
        status="active",
        personality=PersonalityType.FRIENDLY,
    )
    db_session.add(merchant)
    await db_session.commit()
    await db_session.refresh(merchant)

    assert merchant.personality == PersonalityType.FRIENDLY
    assert merchant.personality == "friendly"


@pytest.mark.asyncio
async def test_merchant_with_personality_professional(db_session: AsyncSession) -> None:
    """Test creating a merchant with professional personality (Story 1.10 AC 3)."""

    merchant = Merchant(
        merchant_key="test-merchant-professional",
        platform="fly.io",
        status="active",
        personality=PersonalityType.PROFESSIONAL,
    )
    db_session.add(merchant)
    await db_session.commit()
    await db_session.refresh(merchant)

    assert merchant.personality == PersonalityType.PROFESSIONAL
    assert merchant.personality == "professional"


@pytest.mark.asyncio
async def test_merchant_with_personality_enthusiastic(db_session: AsyncSession) -> None:
    """Test creating a merchant with enthusiastic personality (Story 1.10 AC 3)."""

    merchant = Merchant(
        merchant_key="test-merchant-enthusiastic",
        platform="fly.io",
        status="active",
        personality=PersonalityType.ENTHUSIASTIC,
    )
    db_session.add(merchant)
    await db_session.commit()
    await db_session.refresh(merchant)

    assert merchant.personality == PersonalityType.ENTHUSIASTIC
    assert merchant.personality == "enthusiastic"


@pytest.mark.asyncio
async def test_merchant_default_personality(db_session: AsyncSession) -> None:
    """Test that merchant defaults to friendly personality when not specified (Story 1.10 AC 3)."""

    merchant = Merchant(
        merchant_key="test-merchant-default-personality",
        platform="fly.io",
        status="active",
    )
    db_session.add(merchant)
    await db_session.commit()
    await db_session.refresh(merchant)

    # Default personality should be friendly
    assert merchant.personality == PersonalityType.FRIENDLY


@pytest.mark.asyncio
async def test_merchant_with_custom_greeting(db_session: AsyncSession) -> None:
    """Test creating a merchant with custom greeting (Story 1.10 AC 2, 3)."""

    custom_greeting = "Hey! 👋 Welcome to Alex's Athletic Gear! How can I help you today?"

    merchant = Merchant(
        merchant_key="test-merchant-custom-greeting",
        platform="fly.io",
        status="active",
        personality=PersonalityType.FRIENDLY,
        custom_greeting=custom_greeting,
    )
    db_session.add(merchant)
    await db_session.commit()
    await db_session.refresh(merchant)

    assert merchant.custom_greeting == custom_greeting


@pytest.mark.asyncio
async def test_merchant_custom_greeting_nullable(db_session: AsyncSession) -> None:
    """Test that custom_greeting can be null (Story 1.10 AC 3)."""

    merchant = Merchant(
        merchant_key="test-merchant-null-greeting",
        platform="fly.io",
        status="active",
        personality=PersonalityType.PROFESSIONAL,
        custom_greeting=None,
    )
    db_session.add(merchant)
    await db_session.commit()
    await db_session.refresh(merchant)

    assert merchant.custom_greeting is None


@pytest.mark.asyncio
async def test_merchant_custom_greeting_max_length(db_session: AsyncSession) -> None:
    """Test that custom_greeting respects 500 character limit (Story 1.10 AC 2)."""

    # Create a greeting with exactly 500 characters
    long_greeting = "Hi! " * 125  # "Hi! " is 4 chars, 4 * 125 = 500 characters

    merchant = Merchant(
        merchant_key="test-merchant-long-greeting",
        platform="fly.io",
        status="active",
        personality=PersonalityType.ENTHUSIASTIC,
        custom_greeting=long_greeting,
    )
    db_session.add(merchant)
    await db_session.commit()
    await db_session.refresh(merchant)

    assert len(merchant.custom_greeting) == 500
    assert merchant.custom_greeting == long_greeting


@pytest.mark.asyncio
async def test_merchant_update_personality(db_session: AsyncSession) -> None:
    """Test updating merchant personality (Story 1.10 AC 5)."""

    merchant = Merchant(
        merchant_key="test-merchant-update-personality",
        platform="fly.io",
        status="active",
        personality=PersonalityType.FRIENDLY,
    )
    db_session.add(merchant)
    await db_session.commit()
    await db_session.refresh(merchant)

    # Update personality
    merchant.personality = PersonalityType.PROFESSIONAL
    await db_session.commit()
    await db_session.refresh(merchant)

    assert merchant.personality == PersonalityType.PROFESSIONAL


@pytest.mark.asyncio
async def test_merchant_update_custom_greeting(db_session: AsyncSession) -> None:
    """Test updating merchant custom greeting (Story 1.10 AC 5)."""

    merchant = Merchant(
        merchant_key="test-merchant-update-greeting",
        platform="fly.io",
        status="active",
        personality=PersonalityType.FRIENDLY,
        custom_greeting="Original greeting",
    )
    db_session.add(merchant)
    await db_session.commit()
    await db_session.refresh(merchant)

    original_updated_at = merchant.updated_at

    # Update custom greeting
    merchant.custom_greeting = "Updated greeting! Welcome to our store!"
    await db_session.commit()
    await db_session.refresh(merchant)

    assert merchant.custom_greeting == "Updated greeting! Welcome to our store!"
    assert merchant.updated_at > original_updated_at


@pytest.mark.asyncio
async def test_merchant_personality_index_query(db_session: AsyncSession) -> None:
    """Test efficient lookup of merchants by personality using index (Story 1.10 AC 3)."""

    # Create merchants with different personalities
    merchants = [
        Merchant(merchant_key=f"test-merchant-personality-query-{i}", platform="fly.io", status="active", personality=personality)
        for i, personality in enumerate([PersonalityType.FRIENDLY, PersonalityType.PROFESSIONAL, PersonalityType.ENTHUSIASTIC, PersonalityType.FRIENDLY])
    ]

    for merchant in merchants:
        db_session.add(merchant)
    await db_session.commit()

    # Query merchants with friendly personality
    result = await db_session.execute(
        select(Merchant).where(Merchant.personality == PersonalityType.FRIENDLY)
    )
    friendly_merchants = result.scalars().all()

    assert len(friendly_merchants) == 2
    assert all(m.personality == PersonalityType.FRIENDLY for m in friendly_merchants)


@pytest.mark.asyncio
async def test_merchant_repr_includes_personality(db_session: AsyncSession) -> None:
    """Test that merchant repr includes personality information."""

    merchant = Merchant(
        merchant_key="test-merchant-repr-personality",
        platform="fly.io",
        status="active",
        personality=PersonalityType.ENTHUSIASTIC,
        custom_greeting="Welcome!",
    )
    db_session.add(merchant)
    await db_session.commit()
    await db_session.refresh(merchant)

    repr_str = repr(merchant)
    assert "test-merchant-repr-personality" in repr_str
    assert "enthusiastic" in repr_str.lower()


# Story 1.11: Business Info & FAQ Configuration Tests


@pytest.mark.asyncio
async def test_merchant_with_business_name(db_session: AsyncSession) -> None:
    """Test creating a merchant with business name (Story 1.11 AC 1)."""

    merchant = Merchant(
        merchant_key="test-merchant-business-name",
        platform="fly.io",
        status="active",
        business_name="Alex's Athletic Gear",
    )
    db_session.add(merchant)
    await db_session.commit()
    await db_session.refresh(merchant)

    assert merchant.business_name == "Alex's Athletic Gear"


@pytest.mark.asyncio
async def test_merchant_with_business_description(db_session: AsyncSession) -> None:
    """Test creating a merchant with business description (Story 1.11 AC 1)."""

    business_description = "Premium athletic equipment for serious athletes"

    merchant = Merchant(
        merchant_key="test-merchant-business-description",
        platform="fly.io",
        status="active",
        business_description=business_description,
    )
    db_session.add(merchant)
    await db_session.commit()
    await db_session.refresh(merchant)

    assert merchant.business_description == business_description


@pytest.mark.asyncio
async def test_merchant_with_business_hours(db_session: AsyncSession) -> None:
    """Test creating a merchant with business hours (Story 1.11 AC 1)."""

    merchant = Merchant(
        merchant_key="test-merchant-business-hours",
        platform="fly.io",
        status="active",
        business_hours="9 AM - 6 PM PST, Mon-Fri",
    )
    db_session.add(merchant)
    await db_session.commit()
    await db_session.refresh(merchant)

    assert merchant.business_hours == "9 AM - 6 PM PST, Mon-Fri"


@pytest.mark.asyncio
async def test_merchant_business_info_all_fields(db_session: AsyncSession) -> None:
    """Test creating a merchant with all business info fields (Story 1.11 AC 1, 5)."""

    merchant = Merchant(
        merchant_key="test-merchant-full-business-info",
        platform="fly.io",
        status="active",
        business_name="Alex's Athletic Gear",
        business_description="Premium athletic equipment for serious athletes",
        business_hours="9 AM - 6 PM PST, Mon-Fri",
    )
    db_session.add(merchant)
    await db_session.commit()
    await db_session.refresh(merchant)

    assert merchant.business_name == "Alex's Athletic Gear"
    assert merchant.business_description == "Premium athletic equipment for serious athletes"
    assert merchant.business_hours == "9 AM - 6 PM PST, Mon-Fri"


@pytest.mark.asyncio
async def test_merchant_business_info_nullable(db_session: AsyncSession) -> None:
    """Test that business info fields can be null (Story 1.11 AC 1)."""

    merchant = Merchant(
        merchant_key="test-merchant-null-business-info",
        platform="fly.io",
        status="active",
        business_name=None,
        business_description=None,
        business_hours=None,
    )
    db_session.add(merchant)
    await db_session.commit()
    await db_session.refresh(merchant)

    assert merchant.business_name is None
    assert merchant.business_description is None
    assert merchant.business_hours is None


@pytest.mark.asyncio
async def test_merchant_business_name_max_length(db_session: AsyncSession) -> None:
    """Test that business_name respects 100 character limit (Story 1.11 AC 1)."""

    # Create a business name with exactly 100 characters
    long_name = "A" * 100

    merchant = Merchant(
        merchant_key="test-merchant-max-business-name",
        platform="fly.io",
        status="active",
        business_name=long_name,
    )
    db_session.add(merchant)
    await db_session.commit()
    await db_session.refresh(merchant)

    assert len(merchant.business_name) == 100
    assert merchant.business_name == long_name


@pytest.mark.asyncio
async def test_merchant_business_description_max_length(db_session: AsyncSession) -> None:
    """Test that business_description respects 500 character limit (Story 1.11 AC 1)."""

    # Create a description with exactly 500 characters
    long_description = "B" * 500

    merchant = Merchant(
        merchant_key="test-merchant-max-business-description",
        platform="fly.io",
        status="active",
        business_description=long_description,
    )
    db_session.add(merchant)
    await db_session.commit()
    await db_session.refresh(merchant)

    assert len(merchant.business_description) == 500
    assert merchant.business_description == long_description


@pytest.mark.asyncio
async def test_merchant_business_hours_max_length(db_session: AsyncSession) -> None:
    """Test that business_hours respects 200 character limit (Story 1.11 AC 1)."""

    # Create business hours with exactly 200 characters
    long_hours = "H" * 200

    merchant = Merchant(
        merchant_key="test-merchant-max-business-hours",
        platform="fly.io",
        status="active",
        business_hours=long_hours,
    )
    db_session.add(merchant)
    await db_session.commit()
    await db_session.refresh(merchant)

    assert len(merchant.business_hours) == 200
    assert merchant.business_hours == long_hours


@pytest.mark.asyncio
async def test_merchant_update_business_info(db_session: AsyncSession) -> None:
    """Test updating merchant business info (Story 1.11 AC 4)."""

    merchant = Merchant(
        merchant_key="test-merchant-update-business-info",
        platform="fly.io",
        status="active",
        business_name="Original Name",
        business_description="Original description",
        business_hours="Original hours",
    )
    db_session.add(merchant)
    await db_session.commit()
    await db_session.refresh(merchant)

    # Update business info
    merchant.business_name = "Updated Business Name"
    merchant.business_description = "Updated business description"
    merchant.business_hours = "10 AM - 7 PM EST, Mon-Sat"
    await db_session.commit()
    await db_session.refresh(merchant)

    assert merchant.business_name == "Updated Business Name"
    assert merchant.business_description == "Updated business description"
    assert merchant.business_hours == "10 AM - 7 PM EST, Mon-Sat"


@pytest.mark.asyncio
async def test_merchant_business_name_index_query(db_session: AsyncSession) -> None:
    """Test efficient lookup of merchants by business name using index (Story 1.11 AC 7)."""

    # Create merchants with different business names
    merchants = [
        Merchant(
            merchant_key=f"test-merchant-business-query-{i}",
            platform="fly.io",
            status="active",
            business_name=business_name,
        )
        for i, business_name in enumerate(
            ["Alex's Athletic Gear", "Betty's Boutique", "Charlie's Cafe", "Alex's Athletic Gear"]
        )
    ]

    for merchant in merchants:
        db_session.add(merchant)
    await db_session.commit()

    # Query merchants with specific business name
    result = await db_session.execute(
        select(Merchant).where(Merchant.business_name == "Alex's Athletic Gear")
    )
    matching_merchants = result.scalars().all()

    assert len(matching_merchants) == 2
    assert all(m.business_name == "Alex's Athletic Gear" for m in matching_merchants)
