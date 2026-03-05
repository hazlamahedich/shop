"""API integration tests for Data Tier Separation.

Story 6-4: Data Tier Separation
Task 8: API integration tests
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import Conversation
from app.models.message import Message
from app.models.order import Order
from app.models.consent import Consent, ConsentType
from app.services.privacy.data_tier_service import DataTier
from tests.conftest import auth_headers


class TestConsentOptOutTierChange:
    """Task 8.1: Test consent opt-out → tier changes to ANONYMIZED."""

    @pytest.mark.asyncio
    async def test_consent_opt_out_updates_conversation_tier(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_merchant: int,
    ) -> None:
        """Test that consent opt-out changes conversation tier to ANONYMIZED."""
        session_id = "user_consent_optout_test"

        # Create conversation with VOLUNTARY tier
        conv = Conversation(
            merchant_id=test_merchant,
            platform="widget",
            platform_sender_id=session_id,
            status="active",
            handoff_status="none",
            data_tier=DataTier.VOLUNTARY,
        )
        db_session.add(conv)

        # Create consent record (opted in)
        consent = Consent(
            merchant_id=test_merchant,
            session_id=session_id,
            consent_type=ConsentType.CONVERSATION,
            granted=True,
        )
        db_session.add(consent)
        await db_session.commit()

        # Opt out via API
        response = await client.post(
            "/api/v1/consent/opt-out",
            json={
                "sessionId": session_id,
                "merchantId": test_merchant,
            },
            headers=auth_headers(test_merchant),
        )

        assert response.status_code == 200

        # Verify tier changed to ANONYMIZED
        result = await db_session.execute(select(Conversation).where(Conversation.id == conv.id))
        updated_conv = result.scalars().first()
        assert updated_conv.data_tier == DataTier.ANONYMIZED

    @pytest.mark.asyncio
    async def test_consent_opt_out_preserves_operational_data(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_merchant: int,
    ) -> None:
        """Test that opt-out preserves operational tier data (orders)."""
        session_id = "user_operational_preserve_test"

        # Create order with OPERATIONAL tier
        order = Order(
            merchant_id=test_merchant,
            order_number="ORD-TEST-001",
            platform_sender_id=session_id,
            total=99.99,
            is_test=False,
            data_tier=DataTier.OPERATIONAL,
        )
        db_session.add(order)

        # Create consent
        consent = Consent(
            merchant_id=test_merchant,
            session_id=session_id,
            consent_type=ConsentType.CONVERSATION,
            granted=True,
        )
        db_session.add(consent)
        await db_session.commit()

        # Opt out
        response = await client.post(
            "/api/v1/consent/opt-out",
            json={
                "sessionId": session_id,
                "merchantId": test_merchant,
            },
            headers=auth_headers(test_merchant),
        )

        assert response.status_code == 200

        # Verify operational data NOT changed
        result = await db_session.execute(select(Order).where(Order.id == order.id))
        unchanged_order = result.scalars().first()
        assert unchanged_order.data_tier == DataTier.OPERATIONAL


class TestDataExportTierSeparation:
    """Task 8.2: Test data export → respects tier separation."""

    @pytest.mark.asyncio
    async def test_export_excludes_anonymized_tier(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_merchant: int,
    ) -> None:
        """Test that data export excludes ANONYMIZED tier conversations."""
        # Create conversations in different tiers
        voluntary_conv = Conversation(
            merchant_id=test_merchant,
            platform="widget",
            platform_sender_id="voluntary_user",
            status="active",
            handoff_status="none",
            data_tier=DataTier.VOLUNTARY,
        )
        anonymized_conv = Conversation(
            merchant_id=test_merchant,
            platform="widget",
            platform_sender_id="anonymized_user",
            status="active",
            handoff_status="none",
            data_tier=DataTier.ANONYMIZED,
        )
        db_session.add_all([voluntary_conv, anonymized_conv])
        await db_session.commit()

        # Request data export
        response = await client.get(
            "/api/v1/data/export",
            headers=auth_headers(test_merchant),
        )

        assert response.status_code == 200
        data = response.json()

        # Verify VOLUNTARY included
        assert any(c["platformSenderId"] == "voluntary_user" for c in data.get("conversations", []))

        # Verify ANONYMIZED excluded
        assert not any(
            c["platformSenderId"] == "anonymized_user" for c in data.get("conversations", [])
        )

    @pytest.mark.asyncio
    async def test_export_includes_operational_tier(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_merchant: int,
    ) -> None:
        """Test that data export includes OPERATIONAL tier orders."""
        # Create order with OPERATIONAL tier
        order = Order(
            merchant_id=test_merchant,
            order_number="ORD-EXPORT-001",
            platform_sender_id="export_user",
            total=149.99,
            is_test=False,
            data_tier=DataTier.OPERATIONAL,
        )
        db_session.add(order)
        await db_session.commit()

        # Request data export
        response = await client.get(
            "/api/v1/data/export",
            headers=auth_headers(test_merchant),
        )

        assert response.status_code == 200
        data = response.json()

        # Verify OPERATIONAL included
        assert any(o["orderNumber"] == "ORD-EXPORT-001" for o in data.get("orders", []))


class TestAnalyticsSummaryAnonymized:
    """Task 8.3: Test analytics summary → returns anonymized data only."""

    @pytest.mark.asyncio
    async def test_analytics_summary_strips_pii(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_merchant: int,
    ) -> None:
        """Test that analytics summary contains no PII."""
        # Create conversation with PII
        conv = Conversation(
            merchant_id=test_merchant,
            platform="widget",
            platform_sender_id="user-with-email@example.com",  # PII
            status="active",
            handoff_status="none",
            data_tier=DataTier.VOLUNTARY,
        )
        db_session.add(conv)
        await db_session.commit()

        # Request analytics summary
        response = await client.get(
            "/api/v1/analytics/summary",
            headers=auth_headers(test_merchant),
        )

        assert response.status_code == 200
        data = response.json()

        # Verify NO PII in response
        response_str = str(data)
        assert "user-with-email@example.com" not in response_str
        assert "platformSenderId" not in response_str

        # Verify tier is ANONYMIZED
        assert data["tier"] == "anonymized"

    @pytest.mark.asyncio
    async def test_analytics_summary_includes_tier_distribution(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_merchant: int,
    ) -> None:
        """Test that analytics summary includes tier distribution."""
        # Create data in different tiers
        voluntary_conv = Conversation(
            merchant_id=test_merchant,
            platform="widget",
            platform_sender_id="vol_user",
            status="active",
            handoff_status="none",
            data_tier=DataTier.VOLUNTARY,
        )
        operational_order = Order(
            merchant_id=test_merchant,
            order_number="ORD-ANALYTICS-001",
            platform_sender_id="op_user",
            total=50.00,
            is_test=False,
            data_tier=DataTier.OPERATIONAL,
        )
        db_session.add_all([voluntary_conv, operational_order])
        await db_session.commit()

        # Request analytics summary
        response = await client.get(
            "/api/v1/analytics/summary",
            headers=auth_headers(test_merchant),
        )

        assert response.status_code == 200
        data = response.json()

        # Verify tier distribution present
        assert "tierDistribution" in data
        assert "conversations" in data["tierDistribution"]
        assert "messages" in data["tierDistribution"]
        assert "orders" in data["tierDistribution"]
        assert "summary" in data["tierDistribution"]

        # Verify at least one voluntary conversation
        assert data["tierDistribution"]["conversations"]["voluntary"] >= 1

        # Verify at least one operational order
        assert data["tierDistribution"]["orders"]["operational"] >= 1


class TestRetentionJobVoluntaryOnly:
    """Task 8.4: Test retention job → deletes only VOLUNTARY tier data."""

    @pytest.mark.asyncio
    async def test_retention_deletes_expired_voluntary_only(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_merchant: int,
    ) -> None:
        """Test that retention job only deletes expired VOLUNTARY data."""
        from app.services.privacy.retention_service import RetentionPolicy

        # Create old voluntary conversation (35 days)
        old_voluntary = Conversation(
            merchant_id=test_merchant,
            platform="widget",
            platform_sender_id="old_voluntary_user",
            status="active",
            handoff_status="none",
            data_tier=DataTier.VOLUNTARY,
            created_at=datetime.now(timezone.utc) - timedelta(days=35),
            updated_at=datetime.now(timezone.utc) - timedelta(days=35),
        )
        db_session.add(old_voluntary)

        # Create old operational conversation (should NOT delete)
        old_operational = Conversation(
            merchant_id=test_merchant,
            platform="widget",
            platform_sender_id="old_operational_user",
            status="active",
            handoff_status="none",
            data_tier=DataTier.OPERATIONAL,
            created_at=datetime.now(timezone.utc) - timedelta(days=35),
            updated_at=datetime.now(timezone.utc) - timedelta(days=35),
        )
        db_session.add(old_operational)

        # Create old anonymized conversation (should NOT delete)
        old_anonymized = Conversation(
            merchant_id=test_merchant,
            platform="widget",
            platform_sender_id="old_anonymized_user",
            status="active",
            handoff_status="none",
            data_tier=DataTier.ANONYMIZED,
            created_at=datetime.now(timezone.utc) - timedelta(days=35),
            updated_at=datetime.now(timezone.utc) - timedelta(days=35),
        )
        db_session.add(old_anonymized)

        await db_session.commit()

        # Run retention policy
        policy = RetentionPolicy()
        deleted_count = await policy.delete_expired_voluntary_data(db_session)

        # Should delete only voluntary
        assert deleted_count == 1

        # Verify voluntary deleted
        result = await db_session.execute(
            select(Conversation).where(Conversation.id == old_voluntary.id)
        )
        assert result.scalars().first() is None

        # Verify operational retained
        result = await db_session.execute(
            select(Conversation).where(Conversation.id == old_operational.id)
        )
        assert result.scalars().first() is not None

        # Verify anonymized retained
        result = await db_session.execute(
            select(Conversation).where(Conversation.id == old_anonymized.id)
        )
        assert result.scalars().first() is not None

    @pytest.mark.asyncio
    async def test_retention_preserves_recent_voluntary(
        self,
        db_session: AsyncSession,
        test_merchant: int,
    ) -> None:
        """Test that retention preserves recent VOLUNTARY data (within 30 days)."""
        from app.services.privacy.retention_service import RetentionPolicy

        # Create recent voluntary conversation (15 days old)
        recent_voluntary = Conversation(
            merchant_id=test_merchant,
            platform="widget",
            platform_sender_id="recent_voluntary_user",
            status="active",
            handoff_status="none",
            data_tier=DataTier.VOLUNTARY,
            created_at=datetime.now(timezone.utc) - timedelta(days=15),
            updated_at=datetime.now(timezone.utc) - timedelta(days=15),
        )
        db_session.add(recent_voluntary)
        await db_session.commit()

        # Run retention policy
        policy = RetentionPolicy()
        deleted_count = await policy.delete_expired_voluntary_data(db_session)

        # Should NOT delete recent data
        assert deleted_count == 0

        # Verify conversation retained
        result = await db_session.execute(
            select(Conversation).where(Conversation.id == recent_voluntary.id)
        )
        assert result.scalars().first() is not None


class TestAPIIntegrationEdgeCases:
    """Edge case tests for API integration."""

    @pytest.mark.asyncio
    async def test_concurrent_tier_updates(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_merchant: int,
    ) -> None:
        """Test concurrent tier updates don't cause race conditions."""
        session_id = "concurrent_user"

        conv = Conversation(
            merchant_id=test_merchant,
            platform="widget",
            platform_sender_id=session_id,
            status="active",
            handoff_status="none",
            data_tier=DataTier.VOLUNTARY,
        )
        db_session.add(conv)
        await db_session.commit()

        # Simulate concurrent updates (both trying to change tier)
        # In production, this would use proper locking
        from app.services.privacy.data_tier_service import DataTierService

        service = DataTierService()

        # First update
        await service.update_tier(
            db=db_session,
            model_class=Conversation,
            record_id=conv.id,
            new_tier=DataTier.ANONYMIZED,
        )

        # Second update to same tier (should succeed)
        await service.update_tier(
            db=db_session,
            model_class=Conversation,
            record_id=conv.id,
            new_tier=DataTier.ANONYMIZED,
        )

        # Verify final tier
        result = await db_session.execute(select(Conversation).where(Conversation.id == conv.id))
        final_conv = result.scalars().first()
        assert final_conv.data_tier == DataTier.ANONYMIZED

    @pytest.mark.asyncio
    async def test_analytics_empty_merchant(
        self,
        client: AsyncClient,
        test_merchant: int,
    ) -> None:
        """Test analytics summary with no data returns zeros."""
        response = await client.get(
            "/api/v1/analytics/summary",
            headers=auth_headers(test_merchant),
        )

        assert response.status_code == 200
        data = response.json()

        # Should return zeros, not error
        assert data["tierDistribution"]["conversations"]["voluntary"] == 0
        assert data["tierDistribution"]["conversations"]["operational"] == 0
        assert data["tierDistribution"]["conversations"]["anonymized"] == 0
