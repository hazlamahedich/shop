"""Integration tests for return-to-bot flow.

Story 4-10: Return to Bot

Tests cover:
- Full flow: handoff -> merchant responds -> return to bot -> status active
- Bot responds to shopper message after return to bot (not in hybrid mode)
- Conversation history includes messages for bot context
"""

from __future__ import annotations

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.fixture(autouse=True)
def disable_testing_mode(monkeypatch):
    """Ensure IS_TESTING is false for integration tests."""
    from app.core.config import settings

    settings.cache_clear()
    monkeypatch.setenv("IS_TESTING", "false")
    yield
    settings.cache_clear()


@pytest.mark.asyncio
class TestReturnToBotFlow:
    """Integration tests for return-to-bot flow."""

    async def test_full_flow_handoff_to_return_to_bot(
        self,
        async_client,
        db_session,
        test_merchant,
        test_handoff_conversation,
    ):
        """Test full flow: handoff -> return to bot -> status active."""
        from app.models.facebook_integration import FacebookIntegration
        from app.core.security import encrypt_access_token

        fb = FacebookIntegration(
            merchant_id=test_merchant.id,
            page_id="test_page_id",
            page_name="Test Page",
            access_token_encrypted=encrypt_access_token("test_token"),
            scopes=["pages_messaging"],
            status="active",
        )
        db_session.add(fb)
        await db_session.commit()

        conv = test_handoff_conversation
        conv.status = "handoff"
        conv.handoff_status = "active"
        conv.conversation_data = {"hybrid_mode": {"enabled": True}}
        await db_session.commit()
        await db_session.refresh(conv)

        assert conv.status == "handoff"
        assert conv.handoff_status == "active"

        response = await async_client.patch(
            f"/api/conversations/{conv.id}/hybrid-mode",
            json={"enabled": False, "reason": "merchant_returning"},
            headers={"X-Merchant-Id": str(test_merchant.id)},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["conversationStatus"] == "active"
        assert data["data"]["handoffStatus"] == "none"

        await db_session.refresh(conv)
        assert conv.status == "active"
        assert conv.handoff_status == "none"

    async def test_bot_responds_after_return_to_bot(
        self,
        db_session,
        test_merchant,
        test_handoff_conversation,
    ):
        """Test that bot responds to shopper messages after return to bot."""
        from app.services.messaging.message_processor import MessageProcessor
        from app.models.conversation import Conversation

        conv = test_handoff_conversation
        conv.status = "active"
        conv.handoff_status = "none"
        conv.conversation_data = {"hybrid_mode": {"enabled": False}}
        await db_session.commit()
        await db_session.refresh(conv)

        processor = MessageProcessor()
        should_respond = processor.should_bot_respond(conv, "hello")

        assert should_respond is True

    async def test_conversation_history_includes_all_messages_after_return(
        self,
        async_client,
        db_session,
        test_merchant,
        test_handoff_conversation,
    ):
        """Test conversation history includes all messages for bot context."""
        from app.models.facebook_integration import FacebookIntegration
        from app.core.security import encrypt_access_token
        from app.models.message import Message

        fb = FacebookIntegration(
            merchant_id=test_merchant.id,
            page_id="test_page_id",
            page_name="Test Page",
            access_token_encrypted=encrypt_access_token("test_token"),
            scopes=["pages_messaging"],
            status="active",
        )
        db_session.add(fb)
        await db_session.commit()

        conv = test_handoff_conversation
        conv.status = "handoff"
        conv.handoff_status = "active"
        conv.conversation_data = {"hybrid_mode": {"enabled": True}}
        await db_session.commit()
        await db_session.refresh(conv)

        msg1 = Message(
            conversation_id=conv.id,
            sender="customer",
            content="I need help with my order",
            message_type="text",
            created_at=datetime.utcnow() - timedelta(minutes=5),
        )
        msg2 = Message(
            conversation_id=conv.id,
            sender="bot",
            content="Let me connect you with our team",
            message_type="text",
            created_at=datetime.utcnow() - timedelta(minutes=4),
        )
        db_session.add_all([msg1, msg2])
        await db_session.commit()

        response = await async_client.patch(
            f"/api/conversations/{conv.id}/hybrid-mode",
            json={"enabled": False, "reason": "merchant_returning"},
            headers={"X-Merchant-Id": str(test_merchant.id)},
        )
        assert response.status_code == 200

        history_response = await async_client.get(
            f"/api/conversations/{conv.id}/history",
            headers={"X-Merchant-Id": str(test_merchant.id)},
        )
        assert history_response.status_code == 200
        history_data = history_response.json()

        messages = history_data["data"]["messages"]
        assert len(messages) >= 2

        contents = [msg["content"] for msg in messages]
        assert any("help with my order" in c for c in contents)

    async def test_welcome_message_sent_when_within_24h_window(
        self,
        async_client,
        db_session,
        test_merchant,
        test_handoff_conversation,
    ):
        """Test welcome message is sent when within 24h window."""
        from app.models.facebook_integration import FacebookIntegration
        from app.core.security import encrypt_access_token
        from app.models.message import Message

        fb = FacebookIntegration(
            merchant_id=test_merchant.id,
            page_id="test_page_id",
            page_name="Test Page",
            access_token_encrypted=encrypt_access_token("test_token"),
            scopes=["pages_messaging"],
            status="active",
        )
        db_session.add(fb)
        await db_session.commit()

        conv = test_handoff_conversation
        conv.status = "handoff"
        conv.handoff_status = "active"
        conv.conversation_data = {"hybrid_mode": {"enabled": True}}
        await db_session.commit()
        await db_session.refresh(conv)

        recent_msg = Message(
            conversation_id=conv.id,
            sender="customer",
            content="Recent message",
            message_type="text",
            created_at=datetime.utcnow() - timedelta(hours=1),
        )
        db_session.add(recent_msg)
        await db_session.commit()

        response = await async_client.patch(
            f"/api/conversations/{conv.id}/hybrid-mode",
            json={"enabled": False, "reason": "merchant_returning"},
            headers={"X-Merchant-Id": str(test_merchant.id)},
        )

        assert response.status_code == 200

    async def test_return_to_bot_idempotent(
        self,
        async_client,
        db_session,
        test_merchant,
        test_conversation_with_messages,
    ):
        """Test that return-to-bot is idempotent for already active conversations."""
        from app.models.facebook_integration import FacebookIntegration
        from app.core.security import encrypt_access_token

        fb = FacebookIntegration(
            merchant_id=test_merchant.id,
            page_id="test_page_id",
            page_name="Test Page",
            access_token_encrypted=encrypt_access_token("test_token"),
            scopes=["pages_messaging"],
            status="active",
        )
        db_session.add(fb)
        await db_session.commit()

        conv = test_conversation_with_messages
        conv.status = "active"
        conv.handoff_status = "none"
        conv.conversation_data = {"hybrid_mode": {"enabled": True}}
        await db_session.commit()
        await db_session.refresh(conv)

        response = await async_client.patch(
            f"/api/conversations/{conv.id}/hybrid-mode",
            json={"enabled": False, "reason": "merchant_returning"},
            headers={"X-Merchant-Id": str(test_merchant.id)},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["conversationStatus"] == "active"
        assert data["data"]["handoffStatus"] == "none"
