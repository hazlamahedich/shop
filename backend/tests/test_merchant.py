"""Tests for merchant ORM model."""

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.merchant import Merchant


class TestMerchantModel:
    """Tests for Merchant ORM model."""

    @pytest.mark.asyncio
    async def test_create_merchant(self, async_session: AsyncSession):
        """Test creating a merchant record."""
        merchant = Merchant(
            merchant_key="shop-test123",
            status="pending",
            config={"app_name": "shop-bot-shop-test123"},
        )
        async_session.add(merchant)
        await async_session.commit()
        await async_session.refresh(merchant)

        assert merchant.id is not None
        assert merchant.merchant_key == "shop-test123"
        assert merchant.status == "pending"
        assert merchant.config is not None
        assert merchant.config["app_name"] == "shop-bot-shop-test123"

    @pytest.mark.asyncio
    async def test_merchant_defaults(self, async_session: AsyncSession):
        """Test merchant model default values."""
        merchant = Merchant(
            merchant_key="shop-defaults",
        )
        async_session.add(merchant)
        await async_session.commit()
        await async_session.refresh(merchant)

        assert merchant.status == "pending"
        assert merchant.created_at is not None
        assert merchant.updated_at is not None
        assert merchant.deployed_at is None
        assert merchant.secret_key_hash is None

    @pytest.mark.asyncio
    async def test_merchant_unique_constraint(self, async_session: AsyncSession):
        """Test that merchant_key must be unique."""
        merchant1 = Merchant(
            merchant_key="shop-unique",
        )
        merchant2 = Merchant(
            merchant_key="shop-unique",
        )
        async_session.add(merchant1)
        await async_session.commit()

        async_session.add(merchant2)
        with pytest.raises(Exception):
            await async_session.commit()

    @pytest.mark.asyncio
    async def test_merchant_updated_at_auto_updates(self, async_session: AsyncSession):
        """Test that updated_at auto-updates on save."""
        merchant = Merchant(
            merchant_key="shop-updated",
        )
        async_session.add(merchant)
        await async_session.commit()
        original_updated_at = merchant.updated_at

        merchant.status = "active"
        await async_session.commit()
        await async_session.refresh(merchant)

        assert merchant.updated_at > original_updated_at

    @pytest.mark.asyncio
    async def test_merchant_query_by_key(self, async_session: AsyncSession):
        """Test querying merchant by merchant_key."""
        merchant = Merchant(
            merchant_key="shop-findme",
        )
        async_session.add(merchant)
        await async_session.commit()

        result = await async_session.execute(
            select(Merchant).where(Merchant.merchant_key == "shop-findme")
        )
        found = result.scalars().first()

        assert found is not None
        assert found.merchant_key == "shop-findme"
