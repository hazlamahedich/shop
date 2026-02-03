"""Tests for onboarding ORM model."""

import pytest
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.onboarding import PrerequisiteChecklist
from app.models.merchant import Merchant


class TestPrerequisiteChecklistModel:
    """Tests for PrerequisiteChecklist ORM model."""

    @pytest.mark.asyncio
    async def test_create_prerequisite_checklist(self, async_session: AsyncSession):
        """Test creating a prerequisite checklist."""
        # Create a merchant first
        merchant = Merchant(
            merchant_key="shop-prereq",
            platform="flyio",
        )
        async_session.add(merchant)
        await async_session.commit()
        await async_session.refresh(merchant)

        # Create checklist
        checklist = PrerequisiteChecklist(
            merchant_id=merchant.id,
            has_cloud_account=True,
            has_facebook_account=True,
            has_shopify_access=True,
            has_llm_provider_choice=False,
        )
        async_session.add(checklist)
        await async_session.commit()
        await async_session.refresh(checklist)

        assert checklist.id is not None
        assert checklist.merchant_id == merchant.id
        assert checklist.has_cloud_account is True
        assert checklist.has_facebook_account is True
        assert checklist.has_shopify_access is True
        assert checklist.has_llm_provider_choice is False
        assert checklist.completed_at is None

    @pytest.mark.asyncio
    async def test_is_complete_property(self, async_session: AsyncSession):
        """Test the is_complete property."""
        # Create a merchant first
        merchant = Merchant(
            merchant_key="shop-complete",
            platform="railway",
        )
        async_session.add(merchant)
        await async_session.commit()
        await async_session.refresh(merchant)

        # Create incomplete checklist
        checklist = PrerequisiteChecklist(
            merchant_id=merchant.id,
            has_cloud_account=True,
            has_facebook_account=True,
            has_shopify_access=True,
            has_llm_provider_choice=False,  # Missing this one
        )
        async_session.add(checklist)
        await async_session.commit()
        await async_session.refresh(checklist)

        assert checklist.is_complete is False

        # Mark as complete
        checklist.has_llm_provider_choice = True
        checklist.update_completed_at()  # Update the completed_at timestamp
        await async_session.commit()
        await async_session.refresh(checklist)

        assert checklist.is_complete is True
        assert checklist.completed_at is not None

    @pytest.mark.asyncio
    async def test_checklist_defaults(self, async_session: AsyncSession):
        """Test default values for checklist."""
        # Create a merchant first
        merchant = Merchant(
            merchant_key="shop-defaults",
            platform="render",
        )
        async_session.add(merchant)
        await async_session.commit()
        await async_session.refresh(merchant)

        checklist = PrerequisiteChecklist(
            merchant_id=merchant.id,
        )
        async_session.add(checklist)
        await async_session.commit()
        await async_session.refresh(checklist)

        assert checklist.has_cloud_account is False
        assert checklist.has_facebook_account is False
        assert checklist.has_shopify_access is False
        assert checklist.has_llm_provider_choice is False
        assert checklist.created_at is not None
        assert checklist.updated_at is not None
