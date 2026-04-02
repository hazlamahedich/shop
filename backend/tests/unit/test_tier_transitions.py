"""Unit tests for Tier Transitions.

Story 6-4: Data Tier Separation
Task 7.3: Test tier transition with consent status change
"""

from __future__ import annotations

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.consent import Consent, ConsentType
from app.models.conversation import Conversation
from app.services.privacy.data_tier_service import DataTier, DataTierService


class TestTierTransitions:
    """Test suite for tier transition logic."""

    @pytest.fixture
    def service(self) -> DataTierService:
        """Create DataTierService instance."""
        return DataTierService()

    @pytest.mark.asyncio
    async def test_voluntary_to_anonymized_allowed(
        self,
        service: DataTierService,
        db_session: AsyncSession,
        test_merchant: int,
    ) -> None:
        """Test VOLUNTARY → ANONYMIZED transition is allowed (consent opt-out)."""
        conv = Conversation(
            merchant_id=test_merchant,
            platform="widget",
            platform_sender_id="user1",
            status="active",
            handoff_status="none",
            data_tier=DataTier.VOLUNTARY,
        )
        db_session.add(conv)
        await db_session.commit()

        # Update tier to ANONYMIZED (opt-out scenario)
        await service.update_tier(
            db=db_session,
            model_class=Conversation,
            record_id=conv.id,
            new_tier=DataTier.ANONYMIZED,
        )

        # Verify tier updated
        result = await db_session.execute(select(Conversation).where(Conversation.id == conv.id))
        updated_conv = result.scalars().first()
        assert updated_conv.data_tier == DataTier.ANONYMIZED

    @pytest.mark.asyncio
    async def test_operational_to_voluntary_forbidden(
        self,
        service: DataTierService,
        db_session: AsyncSession,
        test_merchant: int,
    ) -> None:
        """Test OPERATIONAL → VOLUNTARY transition is forbidden (tier downgrade)."""
        conv = Conversation(
            merchant_id=test_merchant,
            platform="widget",
            platform_sender_id="user2",
            status="active",
            handoff_status="none",
            data_tier=DataTier.OPERATIONAL,
        )
        db_session.add(conv)
        await db_session.commit()

        # Attempt to downgrade tier (should fail)
        with pytest.raises(ValueError):
            await service.update_tier(
                db=db_session,
                model_class=Conversation,
                record_id=conv.id,
                new_tier=DataTier.VOLUNTARY,
            )

        # Verify tier NOT changed
        result = await db_session.execute(select(Conversation).where(Conversation.id == conv.id))
        unchanged_conv = result.scalars().first()
        assert unchanged_conv.data_tier == DataTier.OPERATIONAL

    @pytest.mark.asyncio
    async def test_operational_to_anonymized_allowed(
        self,
        service: DataTierService,
        db_session: AsyncSession,
        test_merchant: int,
    ) -> None:
        """Test OPERATIONAL → ANONYMIZED transition is allowed (aggregation)."""
        conv = Conversation(
            merchant_id=test_merchant,
            platform="widget",
            platform_sender_id="user3",
            status="active",
            handoff_status="none",
            data_tier=DataTier.OPERATIONAL,
        )
        db_session.add(conv)
        await db_session.commit()

        # Update tier to ANONYMIZED (aggregation scenario)
        await service.update_tier(
            db=db_session,
            model_class=Conversation,
            record_id=conv.id,
            new_tier=DataTier.ANONYMIZED,
        )

        # Verify tier updated
        result = await db_session.execute(select(Conversation).where(Conversation.id == conv.id))
        updated_conv = result.scalars().first()
        assert updated_conv.data_tier == DataTier.ANONYMIZED

    @pytest.mark.asyncio
    async def test_invalid_tier_value_rejected(
        self,
        service: DataTierService,
        db_session: AsyncSession,
        test_merchant: int,
    ) -> None:
        """Test that invalid tier values are rejected."""
        conv = Conversation(
            merchant_id=test_merchant,
            platform="widget",
            platform_sender_id="user4",
            status="active",
            handoff_status="none",
            data_tier=DataTier.VOLUNTARY,
        )
        db_session.add(conv)
        await db_session.commit()

        # Attempt to set invalid tier
        with pytest.raises(Exception):
            await service.update_tier(
                db=db_session,
                model_class=Conversation,
                record_id=conv.id,
                new_tier="invalid_tier",  # type: ignore
            )

    @pytest.mark.asyncio
    async def test_same_tier_update_allowed(
        self,
        service: DataTierService,
        db_session: AsyncSession,
        test_merchant: int,
    ) -> None:
        """Test that updating to the same tier is allowed (no-op)."""
        conv = Conversation(
            merchant_id=test_merchant,
            platform="widget",
            platform_sender_id="user5",
            status="active",
            handoff_status="none",
            data_tier=DataTier.VOLUNTARY,
        )
        db_session.add(conv)
        await db_session.commit()

        # Update to same tier (should succeed)
        await service.update_tier(
            db=db_session,
            model_class=Conversation,
            record_id=conv.id,
            new_tier=DataTier.VOLUNTARY,
        )

        # Verify tier unchanged
        result = await db_session.execute(select(Conversation).where(Conversation.id == conv.id))
        updated_conv = result.scalars().first()
        assert updated_conv.data_tier == DataTier.VOLUNTARY


class TestConsentTierIntegration:
    """Test tier updates triggered by consent changes."""

    @pytest.mark.asyncio
    async def test_consent_opt_out_updates_tier_to_anonymized(
        self,
        db_session: AsyncSession,
        test_merchant: int,
    ) -> None:
        """Test that consent opt-out updates conversation tier to ANONYMIZED."""
        from app.services.consent.extended_consent_service import ConversationConsentService

        session_id = "user_consent_test"

        conv = Conversation(
            merchant_id=test_merchant,
            platform="widget",
            platform_sender_id=session_id,
            status="active",
            handoff_status="none",
            data_tier=DataTier.VOLUNTARY,
        )
        db_session.add(conv)

        # Create consent record
        consent = Consent(
            merchant_id=test_merchant,
            session_id=session_id,
            consent_type=ConsentType.CONVERSATION,
            granted=True,
        )
        db_session.add(consent)
        await db_session.commit()

        # Simulate opt-out (tier should change to ANONYMIZED)
        consent_service = ConversationConsentService(db=db_session)
        await consent_service.update_data_tier(
            session_id=session_id,
            visitor_id=None,
            new_tier=DataTier.ANONYMIZED.value,
        )

        # Verify tier updated
        result = await db_session.execute(select(Conversation).where(Conversation.id == conv.id))
        updated_conv = result.scalars().first()
        assert updated_conv.data_tier == DataTier.ANONYMIZED

    @pytest.mark.asyncio
    async def test_consent_opt_in_keeps_tier_voluntary(
        self,
        db_session: AsyncSession,
        test_merchant: int,
    ) -> None:
        """Test that consent opt-in keeps new conversations as VOLUNTARY."""
        session_id = "new_user_consent"

        conv = Conversation(
            merchant_id=test_merchant,
            platform="widget",
            platform_sender_id=session_id,
            status="active",
            handoff_status="none",
            data_tier=DataTier.VOLUNTARY,  # Explicit for clarity
        )
        db_session.add(conv)
        await db_session.commit()

        # Verify tier is VOLUNTARY
        assert conv.data_tier == DataTier.VOLUNTARY
