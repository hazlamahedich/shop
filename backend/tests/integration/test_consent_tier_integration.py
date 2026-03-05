"""Integration tests for Story 6-4: Consent-Tier Integration.

Tests verify:
- Consent opt-out updates data tier to ANONYMIZED
- Consent opt-in keeps data tier as VOLUNTARY
- Tier updates are atomic with consent status changes
- ConversationConsentService integrates with DataTierService
"""

from __future__ import annotations

import pytest
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import Conversation
from app.models.message import Message
from app.models.consent import Consent
from app.services.consent.extended_consent_service import ConversationConsentService
from app.services.privacy.data_tier_service import DataTier


class TestConsentTierIntegration:
    """Test suite for consent-tier integration (Story 6-4 Task 3)."""

    @pytest.mark.asyncio
    async def test_consent_opt_in_keeps_voluntary_tier(
        self, db_session: AsyncSession, test_merchant: int
    ) -> None:
        """Test that consent opt-in keeps data tier as VOLUNTARY."""
        merchant_id = test_merchant
        session_id = "test-session-1"
        visitor_id = "test-visitor-1"
        platform_sender_id = "user123"

        async with db_session as session:
            # Create conversation
            conversation = Conversation(
                merchant_id=merchant_id,
                platform="facebook",
                platform_sender_id=platform_sender_id,
                data_tier=DataTier.VOLUNTARY,
            )
            session.add(conversation)
            await session.commit()
            await session.refresh(conversation)

            # Create consent record (opted in)
            consent = Consent(
                merchant_id=merchant_id,
                session_id=session_id,
                visitor_id=visitor_id,
                consent_type="conversation",
                granted=True,
                granted_at=datetime.now(timezone.utc),
            )
            session.add(consent)
            await session.commit()

            # Verify tier is VOLUNTARY
            assert conversation.data_tier == DataTier.VOLUNTARY

    @pytest.mark.asyncio
    async def test_consent_opt_out_updates_tier_to_anonymized(
        self, db_session: AsyncSession, test_merchant: int
    ) -> None:
        """Test that consent opt-out updates tier to ANONYMIZED after deletion."""
        merchant_id = test_merchant
        session_id = "test-session-2"
        visitor_id = "test-visitor-2"
        platform_sender_id = session_id  # Match session_id for join to work

        async with db_session as session:
            # Create conversation with VOLUNTARY tier
            conversation = Conversation(
                merchant_id=merchant_id,
                platform="facebook",
                platform_sender_id=platform_sender_id,
                data_tier=DataTier.VOLUNTARY,
            )
            session.add(conversation)
            await session.commit()
            await session.refresh(conversation)

            # Create message with VOLUNTARY tier
            message = Message(
                conversation_id=conversation.id,
                message_id="msg123",
                text="test message",
                sender_type="user",
                timestamp=datetime.now(timezone.utc),
                data_tier=DataTier.VOLUNTARY,
            )
            session.add(message)
            await session.commit()
            await session.refresh(message)

            # Create consent record (opted out)
            consent = Consent(
                merchant_id=merchant_id,
                session_id=session_id,
                visitor_id=visitor_id,
                consent_type="conversation",
                granted=False,
                revoked_at=datetime.now(timezone.utc),
            )
            session.add(consent)
            await session.commit()

            # Simulate opt-out flow: update tier to ANONYMIZED
            consent_service = ConversationConsentService(db=session)
            await consent_service.update_data_tier(
                session_id=session_id,
                visitor_id=visitor_id,
                new_tier=DataTier.ANONYMIZED.value,
            )
            await session.refresh(conversation)
            await session.refresh(message)

            # Verify tier is ANONYMIZED
            assert conversation.data_tier == DataTier.ANONYMIZED
            assert message.data_tier == DataTier.ANONYMIZED

    @pytest.mark.asyncio
    async def test_update_data_tier_atomic_with_consent_change(
        self, db_session: AsyncSession, test_merchant: int
    ) -> None:
        """Test that tier updates are atomic with consent status changes."""
        merchant_id = test_merchant
        session_id = "test-session-3"
        visitor_id = "test-visitor-3"
        platform_sender_id = session_id  # Match session_id for join to work

        async with db_session as session:
            # Create conversation
            conversation = Conversation(
                merchant_id=merchant_id,
                platform="facebook",
                platform_sender_id=platform_sender_id,
                data_tier=DataTier.VOLUNTARY,
            )
            session.add(conversation)
            await session.commit()
            await session.refresh(conversation)

            # Update consent status and tier atomically
            consent = Consent(
                merchant_id=merchant_id,
                session_id=session_id,
                visitor_id=visitor_id,
                consent_type="conversation",
                granted=False,
                revoked_at=datetime.now(timezone.utc),
            )
            session.add(consent)

            # Update tier in same transaction
            consent_service = ConversationConsentService(db=session)
            await consent_service.update_data_tier(
                session_id=session_id,
                visitor_id=visitor_id,
                new_tier=DataTier.ANONYMIZED.value,
            )

            # Both changes should commit together
            await session.commit()
            await session.refresh(conversation)

            assert conversation.data_tier == DataTier.ANONYMIZED

    @pytest.mark.asyncio
    async def test_update_data_tier_by_session_id(
        self, db_session: AsyncSession, test_merchant: int
    ) -> None:
        """Test updating tier by session_id (fallback when visitor_id unavailable)."""
        merchant_id = test_merchant
        session_id = "test-session-4"
        platform_sender_id = session_id  # Match session_id for fallback query to work

        async with db_session as session:
            conversation = Conversation(
                merchant_id=merchant_id,
                platform="facebook",
                platform_sender_id=platform_sender_id,
                data_tier=DataTier.VOLUNTARY,
            )
            session.add(conversation)

            consent = Consent(
                merchant_id=merchant_id,
                session_id=session_id,
                visitor_id=None,  # No visitor_id
                consent_type="conversation",
                granted=False,
                revoked_at=datetime.now(timezone.utc),
            )
            session.add(consent)
            await session.commit()
            await session.refresh(conversation)

            # Update tier by session_id only
            consent_service = ConversationConsentService(db=session)
            await consent_service.update_data_tier(
                session_id=session_id,
                visitor_id=None,
                new_tier=DataTier.ANONYMIZED.value,
            )
            await session.commit()
            await session.refresh(conversation)

            assert conversation.data_tier == DataTier.ANONYMIZED

    @pytest.mark.asyncio
    async def test_update_data_tier_updates_all_conversations(
        self, db_session: AsyncSession, test_merchant: int
    ) -> None:
        """Test that update_data_tier updates all conversations for visitor."""
        merchant_id = test_merchant
        session_id = "test-session-5"
        visitor_id = "test-visitor-5"

        async with db_session as session:
            # Create multiple conversations with matching session_id
            conv1 = Conversation(
                merchant_id=merchant_id,
                platform="facebook",
                platform_sender_id=session_id,  # Match session_id for join
                data_tier=DataTier.VOLUNTARY,
            )
            conv2 = Conversation(
                merchant_id=merchant_id,
                platform="facebook",
                platform_sender_id=session_id,  # Match session_id for join
                data_tier=DataTier.VOLUNTARY,
            )
            session.add_all([conv1, conv2])

            # Create consent record
            consent = Consent(
                merchant_id=merchant_id,
                session_id=session_id,
                visitor_id=visitor_id,
                consent_type="conversation",
                granted=False,
                revoked_at=datetime.now(timezone.utc),
            )
            session.add(consent)
            await session.commit()

            # Update tier for all conversations
            consent_service = ConversationConsentService(db=session)
            await consent_service.update_data_tier(
                session_id=session_id,
                visitor_id=visitor_id,
                new_tier=DataTier.ANONYMIZED.value,
            )
            await session.commit()

            # Refresh and verify both updated
            await session.refresh(conv1)
            await session.refresh(conv2)

            assert conv1.data_tier == DataTier.ANONYMIZED
            assert conv2.data_tier == DataTier.ANONYMIZED
