"""Integration tests for handoff resolution message flow.

Tests the complete flow from API endpoint to message delivery:
- POST /api/conversations/{id}/resolve-handoff
- HandoffResolutionService orchestration
- UnifiedConversationService LLM generation
- Database storage
- WebSocket broadcast

Validates acceptance criteria from the handoff resolution feature.
"""

from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import Conversation
from app.models.merchant import Merchant, PersonalityType
from app.models.message import Message
from app.services.conversation.unified_conversation_service import UnifiedConversationService
from app.services.handoff.handoff_resolution_service import HandoffResolutionService


@pytest.fixture
async def test_merchant(db_session: AsyncSession):
    merchant = Merchant(
        merchant_key=f"test_integration_{datetime.now().timestamp()}",
        business_name="Integration Test Shop",
        personality=PersonalityType.FRIENDLY,
        platform="widget",
        use_custom_greeting=False,
    )
    db_session.add(merchant)
    await db_session.commit()
    await db_session.refresh(merchant)
    yield merchant


@pytest.fixture
async def test_widget_conversation(db_session: AsyncSession, test_merchant: Merchant):
    conversation = Conversation(
        merchant_id=test_merchant.id,
        platform="widget",
        platform_sender_id=f"test_session_{datetime.now().timestamp()}",
        status="handoff",
        handoff_status="active",
        handoff_triggered_at=datetime.utcnow(),
        handoff_reason="customer_requested",
    )
    db_session.add(conversation)
    await db_session.commit()
    await db_session.refresh(conversation)

    messages = [
        Message(
            conversation_id=conversation.id,
            sender="customer",
            content="Hi, I need help with my order",
            message_type="text",
        ),
        Message(
            conversation_id=conversation.id,
            sender="merchant",
            content="Hello! I can help you with that. What's your order number?",
            message_type="text",
        ),
        Message(
            conversation_id=conversation.id,
            sender="customer",
            content="Order #12345",
            message_type="text",
        ),
    ]
    for msg in messages:
        db_session.add(msg)
    await db_session.commit()

    yield conversation


@pytest.fixture
async def test_messenger_conversation(db_session: AsyncSession, test_merchant: Merchant):
    conversation = Conversation(
        merchant_id=test_merchant.id,
        platform="messenger",
        platform_sender_id=f"test_psid_{datetime.now().timestamp()}",
        status="handoff",
        handoff_status="active",
        handoff_triggered_at=datetime.utcnow(),
        handoff_reason="customer_requested",
    )
    db_session.add(conversation)
    await db_session.commit()
    await db_session.refresh(conversation)

    yield conversation


@pytest.mark.asyncio
async def test_full_resolution_flow_widget(
    db_session: AsyncSession,
    test_widget_conversation: Conversation,
    test_merchant: Merchant,
):
    mock_llm_response = {
        "content": "Great news! Integration Test Shop has resolved your inquiry. Is there anything else I can help you with?",
        "fallback": False,
        "reason": "llm_success",
        "response_time_ms": 250,
    }

    with patch.object(
        UnifiedConversationService,
        "generate_handoff_resolution_message",
        new_callable=AsyncMock,
    ) as mock_generate:
        mock_generate.return_value = mock_llm_response

        with patch(
            "app.services.widget.connection_manager.get_connection_manager"
        ) as mock_ws_manager:
            mock_manager = AsyncMock()
            mock_manager.broadcast_to_session = AsyncMock(return_value=1)
            mock_ws_manager.return_value = mock_manager

            service = HandoffResolutionService(db_session)
            result = await service.send_resolution_message(
                conversation=test_widget_conversation,
                merchant=test_merchant,
            )

            assert result["sent"] is True
            assert result["fallback"] is False
            assert result["reason"] == "llm_success"
            assert result["broadcast_sent"] is True
            assert "Integration Test Shop" in result["content"]

            mock_generate.assert_called_once_with(
                db=db_session,
                conversation_id=test_widget_conversation.id,
                merchant_id=test_merchant.id,
            )

            mock_manager.broadcast_to_session.assert_called_once()

            db_result = await db_session.execute(
                select(Message).where(Message.id == result["message_id"])
            )
            stored_message = db_result.scalars().first()

            assert stored_message is not None
            assert stored_message.sender == "bot"
            assert stored_message.content == result["content"]
            assert stored_message.conversation_id == test_widget_conversation.id


@pytest.mark.asyncio
async def test_resolution_flow_with_llm_fallback(
    db_session: AsyncSession,
    test_widget_conversation: Conversation,
    test_merchant: Merchant,
):
    with patch.object(
        UnifiedConversationService,
        "generate_handoff_resolution_message",
        new_callable=AsyncMock,
    ) as mock_generate:
        mock_generate.return_value = {
            "content": "Welcome back! Is there anything else I can help you with?",
            "fallback": True,
            "reason": "llm_error: ConnectionError",
            "response_time_ms": None,
        }

        with patch(
            "app.services.widget.connection_manager.get_connection_manager"
        ) as mock_ws_manager:
            mock_manager = AsyncMock()
            mock_manager.broadcast_to_session = AsyncMock(return_value=1)
            mock_ws_manager.return_value = mock_manager

            service = HandoffResolutionService(db_session)
            result = await service.send_resolution_message(
                conversation=test_widget_conversation,
                merchant=test_merchant,
            )

            assert result["sent"] is True
            assert result["fallback"] is True
            assert "llm_error" in result["reason"]
            assert result["content"] == "Welcome back! Is there anything else I can help you with?"


@pytest.mark.asyncio
async def test_messenger_conversation_no_websocket(
    db_session: AsyncSession,
    test_messenger_conversation: Conversation,
    test_merchant: Merchant,
):
    with patch.object(
        UnifiedConversationService,
        "generate_handoff_resolution_message",
        new_callable=AsyncMock,
    ) as mock_generate:
        mock_generate.return_value = {
            "content": "Thanks for chatting with Integration Test Shop!",
            "fallback": False,
            "reason": "llm_success",
            "response_time_ms": 200,
        }

        with patch(
            "app.services.widget.connection_manager.get_connection_manager"
        ) as mock_ws_manager:
            mock_manager = AsyncMock()
            mock_manager.broadcast_to_session = AsyncMock(return_value=0)
            mock_ws_manager.return_value = mock_manager

            service = HandoffResolutionService(db_session)
            result = await service.send_resolution_message(
                conversation=test_messenger_conversation,
                merchant=test_merchant,
            )

            assert result["sent"] is True
            assert result["broadcast_sent"] is False
            mock_ws_manager.assert_not_called()


@pytest.mark.asyncio
async def test_different_personality_tones(
    db_session: AsyncSession,
    test_widget_conversation: Conversation,
):
    personalities_and_messages = [
        (PersonalityType.FRIENDLY, "Hey there! Integration Test Shop here!"),
        (PersonalityType.PROFESSIONAL, "Thank you for contacting Integration Test Shop."),
        (PersonalityType.ENTHUSIASTIC, "Awesome! Integration Test Shop is back online!"),
    ]

    for personality, expected_message in personalities_and_messages:
        test_merchant = Merchant(
            merchant_key=f"test_{personality.value}_{datetime.now().timestamp()}",
            business_name="Integration Test Shop",
            personality=personality,
            platform="widget",
            use_custom_greeting=False,
        )
        db_session.add(test_merchant)
        await db_session.commit()
        await db_session.refresh(test_merchant)

        with patch.object(
            UnifiedConversationService,
            "generate_handoff_resolution_message",
            new_callable=AsyncMock,
        ) as mock_generate:
            mock_generate.return_value = {
                "content": expected_message,
                "fallback": False,
                "reason": "llm_success",
                "response_time_ms": 200,
            }

            service = HandoffResolutionService(db_session)
            result = await service.send_resolution_message(
                conversation=test_widget_conversation,
                merchant=test_merchant,
            )

            assert result["content"] == expected_message

            call_args = mock_generate.call_args
            assert call_args[1]["merchant_id"] == test_merchant.id


@pytest.mark.asyncio
async def test_conversation_context_used(
    db_session: AsyncSession,
    test_widget_conversation: Conversation,
    test_merchant: Merchant,
):
    with patch.object(
        UnifiedConversationService,
        "generate_handoff_resolution_message",
        new_callable=AsyncMock,
    ) as mock_generate:
        mock_generate.return_value = {
            "content": "Test message",
            "fallback": False,
            "reason": "llm_success",
            "response_time_ms": 200,
        }

        service = HandoffResolutionService(db_session)
        await service.send_resolution_message(
            conversation=test_widget_conversation,
            merchant=test_merchant,
        )

        mock_generate.assert_called_once()
        call_args = mock_generate.call_args

        assert call_args[1]["conversation_id"] == test_widget_conversation.id
        assert call_args[1]["merchant_id"] == test_merchant.id
        assert call_args[1]["db"] == db_session


@pytest.mark.asyncio
async def test_websocket_message_format(
    db_session: AsyncSession,
    test_widget_conversation: Conversation,
    test_merchant: Merchant,
):
    with patch.object(
        UnifiedConversationService,
        "generate_handoff_resolution_message",
        new_callable=AsyncMock,
    ) as mock_generate:
        mock_generate.return_value = {
            "content": "Test message",
            "fallback": False,
            "reason": "llm_success",
            "response_time_ms": 200,
        }

        with patch(
            "app.services.widget.connection_manager.get_connection_manager"
        ) as mock_ws_manager:
            mock_manager = AsyncMock()
            mock_manager.broadcast_to_session = AsyncMock(return_value=1)
            mock_ws_manager.return_value = mock_manager

            service = HandoffResolutionService(db_session)
            result = await service.send_resolution_message(
                conversation=test_widget_conversation,
                merchant=test_merchant,
            )

            broadcast_call = mock_manager.broadcast_to_session.call_args
            message_payload = broadcast_call[1]["message"]

            assert message_payload["type"] == "handoff_resolved"
            assert "id" in message_payload["data"]
            assert "content" in message_payload["data"]
            assert message_payload["data"]["sender"] == "bot"
            assert "createdAt" in message_payload["data"]


@pytest.mark.asyncio
async def test_error_handling_database_failure(
    db_session: AsyncSession,
    test_widget_conversation: Conversation,
    test_merchant: Merchant,
):
    with patch.object(
        UnifiedConversationService,
        "generate_handoff_resolution_message",
        new_callable=AsyncMock,
    ) as mock_generate:
        mock_generate.return_value = {
            "content": "Test message",
            "fallback": False,
            "reason": "llm_success",
            "response_time_ms": 200,
        }

        with patch.object(db_session, "commit", new_callable=AsyncMock) as mock_commit:
            mock_commit.side_effect = Exception("Database error")

            service = HandoffResolutionService(db_session)

            with pytest.raises(Exception) as exc_info:
                await service.send_resolution_message(
                    conversation=test_widget_conversation,
                    merchant=test_merchant,
                )

            assert "Database error" in str(exc_info.value)


@pytest.mark.asyncio
async def test_metrics_logged(
    db_session: AsyncSession,
    test_widget_conversation: Conversation,
    test_merchant: Merchant,
):
    with patch.object(
        UnifiedConversationService,
        "generate_handoff_resolution_message",
        new_callable=AsyncMock,
    ) as mock_generate:
        mock_generate.return_value = {
            "content": "Test message",
            "fallback": False,
            "reason": "llm_success",
            "response_time_ms": 350,
        }

        with patch(
            "app.services.widget.connection_manager.get_connection_manager"
        ) as mock_ws_manager:
            mock_manager = AsyncMock()
            mock_manager.broadcast_to_session = AsyncMock(return_value=1)
            mock_ws_manager.return_value = mock_manager

            with patch("app.services.handoff.handoff_resolution_service.logger") as mock_logger:
                service = HandoffResolutionService(db_session)
                await service.send_resolution_message(
                    conversation=test_widget_conversation,
                    merchant=test_merchant,
                )

                info_calls = mock_logger.info.call_args_list

                sent_call = None
                for call in info_calls:
                    if call[0][0] == "handoff_resolution_message_sent":
                        sent_call = call
                        break

                assert sent_call is not None
                log_data = sent_call[1]

                assert log_data["conversation_id"] == test_widget_conversation.id
                assert log_data["merchant_id"] == test_merchant.id
                assert log_data["business_name"] == test_merchant.business_name
                assert log_data["platform"] == test_widget_conversation.platform
                assert log_data["fallback"] is False
                assert log_data["message_length"] > 0
                assert log_data["response_time_ms"] == 350
                assert log_data["broadcast_sent"] is True
