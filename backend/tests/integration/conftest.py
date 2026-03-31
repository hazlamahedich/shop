"""Shared fixtures for Story 11-1 integration tests.

Provides parameterized SQL fixtures with proper logging for
conversation context E2E tests.
"""

import logging

from unittest.mock import MagicMock

import pytest
from redis import Redis
from sqlalchemy import text

logger = logging.getLogger(__name__)


@pytest.fixture
async def e2e_test_merchant(db_session):
    """Create test merchant for E2E tests."""
    sql = text("""
        INSERT INTO merchants (merchant_key, platform, status, personality, store_provider, onboarding_mode, created_at, updated_at)
        VALUES ('test_e2e_ctx', 'widget', 'active', 'friendly', 'none', 'ecommerce', NOW(), NOW())
        ON CONFLICT (merchant_key) DO UPDATE SET platform = EXCLUDED.platform
        RETURNING id
    """)
    result = await db_session.execute(sql)
    merchant_id = result.fetchone()[0]
    await db_session.commit()
    yield merchant_id

    try:
        await db_session.rollback()
    except Exception as e:
        logger.warning("Merchant cleanup rollback failed: %s", e)

    try:
        await db_session.execute(
            text("DELETE FROM conversation_context WHERE merchant_id = :mid"),
            {"mid": merchant_id},
        )
        await db_session.execute(
            text("DELETE FROM conversations WHERE merchant_id = :mid"),
            {"mid": merchant_id},
        )
        await db_session.execute(
            text("DELETE FROM merchants WHERE id = :mid"),
            {"mid": merchant_id},
        )
        await db_session.commit()
    except Exception as e:
        logger.warning("Merchant cleanup DELETE failed: %s", e)
        try:
            await db_session.rollback()
        except Exception as rollback_err:
            logger.warning("Merchant cleanup rollback after DELETE failed: %s", rollback_err)


@pytest.fixture
async def e2e_test_conversation(db_session, e2e_test_merchant):
    """Create test conversation for E2E tests."""
    sql = text("""
        INSERT INTO conversations (merchant_id, platform, platform_sender_id, status, created_at, updated_at)
        VALUES (:mid, 'widget', 'test_e2e_customer', 'active', NOW(), NOW())
        RETURNING id
    """)
    result = await db_session.execute(sql, {"mid": e2e_test_merchant})
    conversation_id = result.fetchone()[0]
    await db_session.commit()
    yield conversation_id

    try:
        await db_session.rollback()
    except Exception as e:
        logger.warning("Conversation cleanup rollback failed: %s", e)

    try:
        await db_session.execute(
            text("DELETE FROM conversation_context WHERE conversation_id = :cid"),
            {"cid": conversation_id},
        )
        await db_session.execute(
            text("DELETE FROM conversations WHERE id = :cid"),
            {"cid": conversation_id},
        )
        await db_session.commit()
    except Exception as e:
        logger.warning("Conversation cleanup DELETE failed: %s", e)
        try:
            await db_session.rollback()
        except Exception as rollback_err:
            logger.warning("Conversation cleanup rollback after DELETE failed: %s", rollback_err)


@pytest.fixture
def mock_redis_e2e():
    """Mock Redis client for E2E tests with proper spec."""
    return MagicMock(spec=Redis)
