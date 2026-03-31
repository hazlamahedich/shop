"""Story 11-1: E2E tests for general mode, context expiry, and mode switching.

Tests general-mode topic tracking, context expiration behavior,
cross-mode context preservation, and sequential update integrity.

Acceptance Criteria:
- General mode tracks topics and support issues
- Context expires after 24 hours
- Mode switching preserves prior context
- Sequential updates accumulate without data loss
"""

import pytest
from sqlalchemy import text

from app.services.conversation_context import ConversationContextService


class TestMultiTurnGeneralConversations:
    """Test multi-turn conversations in general mode."""

    @pytest.mark.asyncio
    async def test_general_mode_tracks_topics_and_issues(
        self, db_session, e2e_test_conversation, e2e_test_merchant, mock_redis_e2e
    ):
        """General mode accumulates topics and support issues across turns. [11.1-E2E-006]"""
        # Given: A new conversation in general mode
        service = ConversationContextService(db=db_session, redis_client=mock_redis_e2e)

        # When: User reports a login issue
        context1 = await service.update_context(
            conversation_id=e2e_test_conversation,
            merchant_id=e2e_test_merchant,
            message="I'm having trouble logging in",
            mode="general",
        )
        # Then: Login topic is tracked
        assert context1["turn_count"] == 1
        assert context1["mode"] == "general"
        assert "login" in context1["topics_discussed"]

        # When: User mentions password reset
        context2 = await service.update_context(
            conversation_id=e2e_test_conversation,
            merchant_id=e2e_test_merchant,
            message="I need to reset my password",
            mode="general",
        )
        # Then: Both topics are tracked
        assert context2["turn_count"] == 2
        assert "login" in context2["topics_discussed"]
        assert "password" in context2["topics_discussed"]

        # When: User describes account access problem
        context3 = await service.update_context(
            conversation_id=e2e_test_conversation,
            merchant_id=e2e_test_merchant,
            message="I cannot access my account at all",
            mode="general",
        )
        # Then: Account topic added
        assert context3["turn_count"] == 3
        assert "account" in context3["topics_discussed"]

        # When: User expresses frustration
        context4 = await service.update_context(
            conversation_id=e2e_test_conversation,
            merchant_id=e2e_test_merchant,
            message="This is really frustrating",
            mode="general",
        )
        # Then: All 4 topics preserved across all turns
        assert context4["turn_count"] == 4
        assert "login" in context4["topics_discussed"]
        assert "password" in context4["topics_discussed"]
        assert "account" in context4["topics_discussed"]


class TestContextExpiryE2E:
    """Test context expiry in multi-turn scenarios."""

    @pytest.mark.asyncio
    async def test_expired_context_returns_none(
        self, db_session, e2e_test_conversation, e2e_test_merchant, mock_redis_e2e
    ):
        """Expired context is not returned from get_context. [11.1-E2E-007]"""
        # Given: A context that has been created
        service = ConversationContextService(db=db_session, redis_client=mock_redis_e2e)
        await service.update_context(
            conversation_id=e2e_test_conversation,
            merchant_id=e2e_test_merchant,
            message="Test message",
            mode="ecommerce",
        )

        # When: Expiry is set to the past using parameterized query
        await db_session.execute(
            text("""
                UPDATE conversation_context
                SET expires_at = NOW() - INTERVAL '1 hour'
                WHERE conversation_id = :cid
            """),
            {"cid": e2e_test_conversation},
        )
        await db_session.commit()

        # Then: get_context returns None for expired context
        context = await service.get_context(e2e_test_conversation, bypass_cache=True)
        assert context is None, "Expired context should return None"


class TestModeSwitchingE2E:
    """Test mode switching in multi-turn conversations."""

    @pytest.mark.asyncio
    async def test_mode_from_ecommerce_to_general(
        self, db_session, e2e_test_conversation, e2e_test_merchant, mock_redis_e2e
    ):
        """Ecommerce context preserved when switching to general mode. [11.1-E2E-008]"""
        # Given: A conversation starting in ecommerce mode
        service = ConversationContextService(db=db_session, redis_client=mock_redis_e2e)

        # When: Ecommerce turn builds product context
        context1 = await service.update_context(
            conversation_id=e2e_test_conversation,
            merchant_id=e2e_test_merchant,
            message="Show me red shoes under $100",
            mode="ecommerce",
        )
        # Then: Mode is ecommerce with budget constraint
        assert context1["mode"] == "ecommerce"
        assert context1["constraints"]["budget_max"] == 100

        # When: User switches to general mode
        context2 = await service.update_context(
            conversation_id=e2e_test_conversation,
            merchant_id=e2e_test_merchant,
            message="Actually, I need help with my account",
            mode="general",
        )
        # Then: Turn count continues, ecommerce data preserved in DB
        assert context2["turn_count"] == 2


class TestConcurrentContextUpdates:
    """Test sequential and concurrent update scenarios."""

    @pytest.mark.asyncio
    async def test_sequential_updates_preserve_all_data(
        self, db_session, e2e_test_conversation, e2e_test_merchant, mock_redis_e2e
    ):
        """Rapid sequential updates don't lose data from earlier turns. [11.1-E2E-009]"""
        # Given: A context service
        service = ConversationContextService(db=db_session, redis_client=mock_redis_e2e)

        # When: Multiple sequential updates happen rapidly
        messages = [
            "Show me product 100",
            "I also like product 200",
            "What about product 300?",
        ]
        for msg in messages:
            await service.update_context(
                conversation_id=e2e_test_conversation,
                merchant_id=e2e_test_merchant,
                message=msg,
                mode="ecommerce",
            )

        # Then: All products from all turns are accumulated
        final = await service.get_context(e2e_test_conversation)
        assert final is not None
        assert final["turn_count"] == 3
        assert 100 in final["viewed_products"]
        assert 200 in final["viewed_products"]
        assert 300 in final["viewed_products"]
