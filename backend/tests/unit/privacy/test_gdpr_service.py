"""Unit tests for GDPR deletion service.

Story 6-6: GDPR Deletion Processing

Tests for:
- GDPR request creation and tracking
- Voluntary data deletion
- Duplicate request prevention
- Customer processing restriction checks
- Request revocation
- Compliance monitoring
"""

import pytest
from datetime import datetime, timezone, timedelta
from sqlalchemy import select

from app.core.errors import APIError, ErrorCode
from app.models.deletion_audit_log import DeletionAuditLog, DeletionRequestType, DeletionTrigger
from app.models.conversation import Conversation
from app.services.privacy.gdpr_service import GDPRDeletionService
from app.services.privacy.data_tier_service import DataTier


@pytest.fixture
def gdpr_service():
    return GDPRDeletionService()


@pytest.mark.asyncio
async def test_gdpr_request_logging(async_session, gdpr_service, test_merchant):
    merchant_id = test_merchant
    customer_id = "test_gdpr_customer"

    conv = Conversation(
        merchant_id=merchant_id,
        platform_sender_id=customer_id,
        platform="facebook",
        data_tier=DataTier.VOLUNTARY.value,
    )
    async_session.add(conv)
    await async_session.commit()

    audit_log = await gdpr_service.process_deletion_request(
        db=async_session,
        customer_id=customer_id,
        merchant_id=merchant_id,
        request_type=DeletionRequestType.GDPR_FORMAL,
    )

    assert audit_log.customer_id == customer_id
    assert audit_log.merchant_id == merchant_id
    assert audit_log.request_type == DeletionRequestType.GDPR_FORMAL.value
    assert audit_log.request_timestamp is not None
    assert audit_log.processing_deadline == audit_log.request_timestamp + timedelta(days=30)
    assert audit_log.completion_date is None

    result = await async_session.execute(
        select(Conversation).where(Conversation.platform_sender_id == customer_id)
    )
    assert result.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_voluntary_data_deletion(async_session, gdpr_service, test_merchant):
    merchant_id = test_merchant
    customer_id = "gdpr_delete_customer"

    for i in range(3):
        conv = Conversation(
            merchant_id=merchant_id,
            platform_sender_id=customer_id,
            platform="facebook",
            data_tier=DataTier.VOLUNTARY.value if i == 0 else DataTier.OPERATIONAL.value,
        )
        async_session.add(conv)

    await async_session.commit()

    await gdpr_service.process_deletion_request(
        db=async_session,
        customer_id=customer_id,
        merchant_id=merchant_id,
        request_type=DeletionRequestType.GDPR_FORMAL,
    )

    result = await async_session.execute(
        select(Conversation)
        .where(Conversation.platform_sender_id == customer_id)
        .where(Conversation.data_tier == DataTier.VOLUNTARY.value)
    )
    voluntary_convs = result.scalars().all()
    assert len(voluntary_convs) == 0

    result = await async_session.execute(
        select(Conversation)
        .where(Conversation.platform_sender_id == customer_id)
        .where(Conversation.data_tier == DataTier.OPERATIONAL.value)
    )
    operational_convs = result.scalars().all()
    assert len(operational_convs) == 2


@pytest.mark.asyncio
async def test_duplicate_request_prevention(async_session, gdpr_service, test_merchant):
    merchant_id = test_merchant
    customer_id = "duplicate_customer"

    await gdpr_service.process_deletion_request(
        db=async_session,
        customer_id=customer_id,
        merchant_id=merchant_id,
        request_type=DeletionRequestType.GDPR_FORMAL,
    )

    with pytest.raises(APIError) as exc:
        await gdpr_service.process_deletion_request(
            db=async_session,
            customer_id=customer_id,
            merchant_id=merchant_id,
            request_type=DeletionRequestType.GDPR_FORMAL,
        )

    assert exc.value.code == ErrorCode.GDPR_REQUEST_PENDING


@pytest.mark.asyncio
async def test_is_customer_processing_restricted(async_session, gdpr_service, test_merchant):
    merchant_id = test_merchant
    customer_id = "restricted_customer"

    await gdpr_service.process_deletion_request(
        db=async_session,
        customer_id=customer_id,
        merchant_id=merchant_id,
        request_type=DeletionRequestType.GDPR_FORMAL,
    )

    is_restricted = await gdpr_service.is_customer_processing_restricted(
        async_session, customer_id, merchant_id
    )
    assert is_restricted is True

    customer_id_2 = "manual_only_customer"
    await gdpr_service.process_deletion_request(
        db=async_session,
        customer_id=customer_id_2,
        merchant_id=merchant_id,
        request_type=DeletionRequestType.MANUAL,
    )

    is_restricted = await gdpr_service.is_customer_processing_restricted(
        async_session, customer_id_2, merchant_id
    )
    assert is_restricted is False


@pytest.mark.asyncio
async def test_revoke_gdpr_request(async_session, gdpr_service, test_merchant):
    merchant_id = test_merchant
    customer_id = "revoke_customer"

    await gdpr_service.process_deletion_request(
        db=async_session,
        customer_id=customer_id,
        merchant_id=merchant_id,
        request_type=DeletionRequestType.GDPR_FORMAL,
    )

    revoked = await gdpr_service.revoke_gdpr_request(async_session, customer_id, merchant_id)
    assert revoked is True

    is_restricted = await gdpr_service.is_customer_processing_restricted(
        async_session, customer_id, merchant_id
    )
    assert is_restricted is False


@pytest.mark.asyncio
async def test_mark_deletion_complete(async_session, gdpr_service, test_merchant):
    audit_log = DeletionAuditLog(
        merchant_id=test_merchant,
        customer_id="complete_customer",
        session_id="gdpr_complete_customer",
        request_type=DeletionRequestType.GDPR_FORMAL.value,
        request_timestamp=datetime.now(timezone.utc),
        processing_deadline=datetime.now(timezone.utc) + timedelta(days=30),
        deletion_trigger=DeletionTrigger.MANUAL.value,
    )
    async_session.add(audit_log)
    await async_session.commit()

    result = await gdpr_service.mark_deletion_complete(async_session, audit_log.id)

    assert result.completion_date is not None

    await async_session.refresh(audit_log)
    assert audit_log.completion_date is not None
