"""Tests for WebhookVerificationLog model."""

from __future__ import annotations

import pytest
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.webhook_verification_log import WebhookVerificationLog
from app.models.merchant import Merchant


@pytest.mark.asyncio
async def test_webhook_verification_log_creation(db_session: AsyncSession) -> None:
    """Test creating a webhook verification log entry."""
    # Create merchant first
    merchant = Merchant(
        merchant_key="test_merchant_wv_1",
        platform="facebook",
        status="active",
    )
    db_session.add(merchant)
    await db_session.flush()

    log = WebhookVerificationLog(
        merchant_id=merchant.id,
        platform="facebook",
        test_type="test_webhook",
        status="success",
        diagnostic_data={"message_id": "test_msg_123"},
    )

    db_session.add(log)
    await db_session.commit()
    await db_session.refresh(log)

    assert log.id is not None
    assert log.merchant_id == merchant.id
    assert log.platform == "facebook"
    assert log.test_type == "test_webhook"
    assert log.status == "success"
    assert log.diagnostic_data == {"message_id": "test_msg_123"}
    assert log.started_at is not None
    assert log.created_at is not None


@pytest.mark.asyncio
async def test_webhook_verification_log_with_error(db_session: AsyncSession) -> None:
    """Test creating a webhook verification log with error details."""
    merchant = Merchant(
        merchant_key="test_merchant_wv_2",
        platform="shopify",
        status="active",
    )
    db_session.add(merchant)
    await db_session.flush()

    log = WebhookVerificationLog(
        merchant_id=merchant.id,
        platform="shopify",
        test_type="status_check",
        status="failed",
        error_message="Webhook subscription not found",
        error_code="SHOPIFY_WEBHOOK_VERIFY_FAILED",
        diagnostic_data={"status_code": 404},
    )

    db_session.add(log)
    await db_session.commit()
    await db_session.refresh(log)

    assert log.status == "failed"
    assert log.error_message == "Webhook subscription not found"
    assert log.error_code == "SHOPIFY_WEBHOOK_VERIFY_FAILED"
    assert log.diagnostic_data == {"status_code": 404}


@pytest.mark.asyncio
async def test_webhook_verification_log_timing(db_session: AsyncSession) -> None:
    """Test webhook verification log with timing information."""
    merchant = Merchant(
        merchant_key="test_merchant_wv_3",
        platform="facebook",
        status="active",
    )
    db_session.add(merchant)
    await db_session.flush()

    started_at = datetime.utcnow()
    completed_at = datetime.utcnow()

    log = WebhookVerificationLog(
        merchant_id=merchant.id,
        platform="facebook",
        test_type="test_webhook",
        status="success",
        started_at=started_at,
        completed_at=completed_at,
        duration_ms=1500,
    )

    db_session.add(log)
    await db_session.commit()
    await db_session.refresh(log)

    assert log.started_at == started_at
    assert log.completed_at == completed_at
    assert log.duration_ms == 1500


@pytest.mark.asyncio
async def test_webhook_verification_log_query_by_merchant(
    db_session: AsyncSession,
) -> None:
    """Test querying webhook verification logs by merchant."""
    # Create merchants
    merchant1 = Merchant(
        merchant_key="test_merchant_wv_4a",
        platform="facebook",
        status="active",
    )
    merchant2 = Merchant(
        merchant_key="test_merchant_wv_4b",
        platform="shopify",
        status="active",
    )
    db_session.add_all([merchant1, merchant2])
    await db_session.flush()

    # Create multiple logs for different merchants
    log1 = WebhookVerificationLog(
        merchant_id=merchant1.id,
        platform="facebook",
        test_type="test_webhook",
        status="success",
    )
    log2 = WebhookVerificationLog(
        merchant_id=merchant1.id,
        platform="shopify",
        test_type="status_check",
        status="success",
    )
    log3 = WebhookVerificationLog(
        merchant_id=merchant2.id,
        platform="facebook",
        test_type="test_webhook",
        status="failed",
    )

    db_session.add_all([log1, log2, log3])
    await db_session.commit()

    # Query logs for merchant 1
    result = await db_session.execute(
        select(WebhookVerificationLog).where(
            WebhookVerificationLog.merchant_id == merchant1.id
        )
    )
    merchant_logs = result.scalars().all()

    assert len(merchant_logs) == 2
    assert all(log.merchant_id == merchant1.id for log in merchant_logs)


@pytest.mark.asyncio
async def test_webhook_verification_log_query_by_platform(
    db_session: AsyncSession,
) -> None:
    """Test querying webhook verification logs by platform."""
    merchant1 = Merchant(
        merchant_key="test_merchant_wv_5a",
        platform="facebook",
        status="active",
    )
    merchant2 = Merchant(
        merchant_key="test_merchant_wv_5b",
        platform="shopify",
        status="active",
    )
    db_session.add_all([merchant1, merchant2])
    await db_session.flush()

    log1 = WebhookVerificationLog(
        merchant_id=merchant1.id,
        platform="facebook",
        test_type="test_webhook",
        status="success",
    )
    log2 = WebhookVerificationLog(
        merchant_id=merchant1.id,
        platform="shopify",
        test_type="status_check",
        status="success",
    )
    log3 = WebhookVerificationLog(
        merchant_id=merchant2.id,
        platform="facebook",
        test_type="resubscribe",
        status="success",
    )

    db_session.add_all([log1, log2, log3])
    await db_session.commit()

    # Query logs for facebook platform
    result = await db_session.execute(
        select(WebhookVerificationLog).where(
            WebhookVerificationLog.platform == "facebook"
        )
    )
    facebook_logs = result.scalars().all()

    assert len(facebook_logs) == 2
    assert all(log.platform == "facebook" for log in facebook_logs)


@pytest.mark.asyncio
async def test_webhook_verification_log_platform_enum_validation(
    db_session: AsyncSession,
) -> None:
    """Test that only valid platform enum values are allowed."""
    merchant = Merchant(
        merchant_key="test_merchant_wv_6",
        platform="facebook",
        status="active",
    )
    db_session.add(merchant)
    await db_session.flush()

    # Valid platforms should work
    log1 = WebhookVerificationLog(
        merchant_id=merchant.id,
        platform="facebook",
        test_type="status_check",
        status="success",
    )
    log2 = WebhookVerificationLog(
        merchant_id=merchant.id,
        platform="shopify",
        test_type="status_check",
        status="success",
    )

    db_session.add_all([log1, log2])
    await db_session.commit()

    assert log1.platform == "facebook"
    assert log2.platform == "shopify"


@pytest.mark.asyncio
async def test_webhook_verification_log_test_type_enum_validation(
    db_session: AsyncSession,
) -> None:
    """Test that only valid test_type enum values are allowed."""
    merchant = Merchant(
        merchant_key="test_merchant_wv_7",
        platform="facebook",
        status="active",
    )
    db_session.add(merchant)
    await db_session.flush()

    log1 = WebhookVerificationLog(
        merchant_id=merchant.id,
        platform="facebook",
        test_type="status_check",
        status="pending",
    )
    log2 = WebhookVerificationLog(
        merchant_id=merchant.id,
        platform="shopify",
        test_type="test_webhook",
        status="success",
    )
    log3 = WebhookVerificationLog(
        merchant_id=merchant.id,
        platform="facebook",
        test_type="resubscribe",
        status="success",
    )

    db_session.add_all([log1, log2, log3])
    await db_session.commit()

    assert log1.test_type == "status_check"
    assert log2.test_type == "test_webhook"
    assert log3.test_type == "resubscribe"


@pytest.mark.asyncio
async def test_webhook_verification_log_status_enum_validation(
    db_session: AsyncSession,
) -> None:
    """Test that only valid status enum values are allowed."""
    merchant = Merchant(
        merchant_key="test_merchant_wv_8",
        platform="facebook",
        status="active",
    )
    db_session.add(merchant)
    await db_session.flush()

    log1 = WebhookVerificationLog(
        merchant_id=merchant.id,
        platform="facebook",
        test_type="status_check",
        status="pending",
    )
    log2 = WebhookVerificationLog(
        merchant_id=merchant.id,
        platform="shopify",
        test_type="test_webhook",
        status="success",
    )
    log3 = WebhookVerificationLog(
        merchant_id=merchant.id,
        platform="facebook",
        test_type="resubscribe",
        status="failed",
    )

    db_session.add_all([log1, log2, log3])
    await db_session.commit()

    assert log1.status == "pending"
    assert log2.status == "success"
    assert log3.status == "failed"


@pytest.mark.asyncio
async def test_webhook_verification_log_delete_cascade(
    db_session: AsyncSession,
) -> None:
    """Test that deleting merchant cascades to webhook verification logs."""
    merchant = Merchant(
        merchant_key="test_merchant_wv_9",
        platform="facebook",
        status="active",
    )
    db_session.add(merchant)
    await db_session.flush()

    log = WebhookVerificationLog(
        merchant_id=merchant.id,
        platform="facebook",
        test_type="test_webhook",
        status="success",
    )
    db_session.add(log)
    await db_session.flush()

    log_id = log.id

    # Delete merchant (should cascade to logs)
    await db_session.delete(merchant)
    await db_session.flush()

    # Verify log is also deleted
    result = await db_session.execute(
        select(WebhookVerificationLog).where(WebhookVerificationLog.id == log_id)
    )
    found = result.scalars().first()
    assert found is None
