"""Pytest configuration for cost tracking service tests."""

import pytest
from sqlalchemy import select
from app.models.merchant import Merchant


@pytest.fixture(autouse=True)
async def setup_test_merchant(db_session):
    """Create test merchants for all cost tracking tests.

    This fixture creates merchants with IDs 1 and 2 automatically for all tests
    in the cost_tracking directory, since most tests need a merchant.
    """
    # Create merchant 1 if it doesn't exist
    result = await db_session.execute(select(Merchant).where(Merchant.id == 1))
    merchant1 = result.scalars().first()

    if not merchant1:
        # Create test merchant
        merchant1 = Merchant(
            merchant_key="test-cost-tracking",
            platform="facebook",
            status="active",
        )
        db_session.add(merchant1)
        await db_session.commit()
        await db_session.refresh(merchant1)

    # Create merchant 2 for isolation tests
    result = await db_session.execute(select(Merchant).where(Merchant.id == 2))
    merchant2 = result.scalars().first()

    if not merchant2:
        merchant2 = Merchant(
            merchant_key="test-cost-tracking-2",
            platform="facebook",
            status="active",
        )
        db_session.add(merchant2)
        await db_session.commit()

    yield merchant1

    # Cleanup is handled by the parent db_session fixture
