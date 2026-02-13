"""Tests for Tutorial ORM model.

Tests ORM operations, state transitions, and merchant relationships.
"""

import pytest
from datetime import datetime
from sqlalchemy import select, text
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.tutorial import Tutorial
from app.models.merchant import Merchant


def create_tutorial(**kwargs) -> Tutorial:
    """Factory function for creating Tutorial instances.

    Args:
        **kwargs: Field values to override defaults

    Returns:
        Tutorial instance
    """
    defaults = {
        "current_step": 1,
        "completed_steps": [],
        "skipped": False,
        "tutorial_version": "1.0",
        "steps_total": 8,  # Updated for 8-step tutorial
    }
    defaults.update(kwargs)
    return Tutorial(**defaults)


@pytest.mark.asyncio
async def test_create_tutorial(db_session: AsyncSession):
    """Test creating a tutorial record."""
    # Create merchant first
    merchant = Merchant(
        merchant_key="test-merchant",
        platform="messenger",
        status="active",
    )
    db_session.add(merchant)
    await db_session.flush()

    # Create tutorial
    tutorial = Tutorial(
        merchant_id=merchant.id,
        current_step=1,
        completed_steps=[],
        skipped=False,
    )
    db_session.add(tutorial)
    await db_session.commit()
    await db_session.refresh(tutorial)

    assert tutorial.id is not None
    assert tutorial.merchant_id == merchant.id
    assert tutorial.current_step == 1
    assert tutorial.completed_steps == []
    assert tutorial.skipped is False


@pytest.mark.asyncio
async def test_tutorial_merchant_relationship(db_session: AsyncSession):
    """Test the relationship between Tutorial and Merchant."""
    # Create merchant
    merchant = Merchant(
        merchant_key="test-merchant-rel",
        platform="messenger",
        status="active",
    )
    db_session.add(merchant)
    await db_session.flush()

    # Create tutorial
    tutorial = create_tutorial(merchant_id=merchant.id)
    db_session.add(tutorial)
    await db_session.commit()
    await db_session.refresh(tutorial)

    # Query via relationship with eager loading
    result = await db_session.execute(
        select(Merchant)
        .options(selectinload(Merchant.tutorial))
        .where(Merchant.id == merchant.id)
    )
    retrieved_merchant = result.scalar_one()

    assert retrieved_merchant.tutorial is not None
    assert retrieved_merchant.tutorial.id == tutorial.id


@pytest.mark.asyncio
async def test_tutorial_state_transitions(db_session: AsyncSession):
    """Test tutorial state transitions."""
    # Create merchant and tutorial
    merchant = Merchant(
        merchant_key="test-merchant-state",
        platform="messenger",
        status="active",
    )
    db_session.add(merchant)
    await db_session.flush()

    tutorial = create_tutorial(merchant_id=merchant.id)
    db_session.add(tutorial)
    await db_session.commit()
    await db_session.refresh(tutorial)

    # Start tutorial
    tutorial.started_at = datetime.utcnow()
    tutorial.current_step = 2
    tutorial.completed_steps = ["step-1"]
    await db_session.commit()
    await db_session.refresh(tutorial)

    assert tutorial.started_at is not None
    assert tutorial.current_step == 2
    assert "step-1" in tutorial.completed_steps

    # Complete tutorial
    tutorial.completed_at = datetime.utcnow()
    tutorial.current_step = 8  # Updated for 8-step tutorial
    tutorial.completed_steps = ["step-1", "step-2", "step-3", "step-4", "step-5", "step-6", "step-7", "step-8"]  # All 8 steps
    await db_session.commit()
    await db_session.refresh(tutorial)

    assert tutorial.completed_at is not None
    assert len(tutorial.completed_steps) == 8  # All 8 steps completed


@pytest.mark.asyncio
async def test_tutorial_skip(db_session: AsyncSession):
    """Test skipping tutorial."""
    # Create merchant and tutorial
    merchant = Merchant(
        merchant_key="test-merchant-skip",
        platform="messenger",
        status="active",
    )
    db_session.add(merchant)
    await db_session.flush()

    tutorial = create_tutorial(merchant_id=merchant.id)
    db_session.add(tutorial)
    await db_session.commit()
    await db_session.refresh(tutorial)

    # Skip tutorial
    tutorial.skipped = True
    tutorial.completed_at = datetime.utcnow()
    await db_session.commit()
    await db_session.refresh(tutorial)

    assert tutorial.skipped is True
    assert tutorial.completed_at is not None


@pytest.mark.asyncio
async def test_tutorial_unique_merchant_constraint(db_session: AsyncSession):
    """Test that each merchant can only have one tutorial record.

    Uses reset_test_database fixture to ensure clean database state.
    """
    # Create merchant
    merchant = Merchant(
        merchant_key="test-merchant-unique",
        platform="messenger",
        status="active",
    )
    db_session.add(merchant)
    await db_session.flush()

    # Create first tutorial
    tutorial1 = create_tutorial(merchant_id=merchant.id)
    db_session.add(tutorial1)
    await db_session.commit()

    # Try to create second tutorial for same merchant
    tutorial2 = create_tutorial(merchant_id=merchant.id)
    db_session.add(tutorial2)

    # Should raise integrity error due to unique constraint
    with pytest.raises(Exception):  # IntegrityError
        await db_session.commit()


@pytest.mark.asyncio
async def test_tutorial_cascade_delete(db_session: AsyncSession):
    """Test that tutorial is deleted when merchant is deleted."""
    # Create merchant and tutorial
    merchant = Merchant(
        merchant_key="test-merchant-cascade",
        platform="messenger",
        status="active",
    )
    db_session.add(merchant)
    await db_session.flush()

    tutorial = create_tutorial(merchant_id=merchant.id)
    db_session.add(tutorial)
    await db_session.commit()
    tutorial_id = tutorial.id

    # Verify FK constraint exists
    fk_check = await db_session.execute(text("""
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'tutorials_merchant_id_fkey';
    """))
    print(f"FK constraint exists during test: {fk_check.scalar_one_or_none()}")

    # Delete merchant
    await db_session.delete(merchant)
    await db_session.commit()

    # Tutorial should be deleted (CASCADE)
    result = await db_session.execute(
        select(Tutorial).where(Tutorial.id == tutorial_id)
    )
    assert result.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_tutorial_default_values(db_session: AsyncSession):
    """Test default values for tutorial fields."""
    merchant = Merchant(
        merchant_key="test-merchant-defaults",
        platform="messenger",
        status="active",
    )
    db_session.add(merchant)
    await db_session.flush()

    tutorial = Tutorial(merchant_id=merchant.id)
    db_session.add(tutorial)
    await db_session.commit()
    await db_session.refresh(tutorial)

    assert tutorial.current_step == 1
    assert tutorial.completed_steps == []
    assert tutorial.skipped is False
    assert tutorial.tutorial_version == "1.0"
    assert tutorial.steps_total == 8  # Updated for 8-step tutorial
