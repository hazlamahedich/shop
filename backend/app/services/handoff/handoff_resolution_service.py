"""Handoff Resolution Service.

Story: LLM-powered handoff resolution messages for widget

Orchestrates the generation and delivery of context-aware resolution messages
when merchants resolve handoff items. Uses UnifiedConversationService for LLM
generation and WidgetConnectionManager for real-time delivery.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import Conversation
from app.models.merchant import Merchant
from app.models.message import Message

logger = structlog.get_logger(__name__)


class HandoffResolutionService:
    """Orchestrates handoff resolution message flow.

    Responsibilities:
    - Generate resolution message using UnifiedConversationService
    - Store message in database
    - Broadcast to widget via WebSocket
    - Track metrics via structured logging

    Usage:
        service = HandoffResolutionService(db)
        result = await service.send_resolution_message(conversation, merchant)
    """

    def __init__(self, db: AsyncSession):
        """Initialize Handoff Resolution Service.

        Args:
            db: AsyncSession for database operations
        """
        self.db = db

    async def send_resolution_message(
        self,
        conversation: Conversation,
        merchant: Merchant,
    ) -> dict[str, Any]:
        """Generate, store, and broadcast resolution message.

        Args:
            conversation: The handoff conversation being resolved
            merchant: Merchant configuration

        Returns:
            {
                "sent": bool,  # True if message was sent successfully
                "message_id": int,  # ID of stored message
                "content": str,  # Generated message content
                "fallback": bool,  # True if used fallback message
                "reason": str  # Success reason or error description
            }
        """
        from app.services.conversation.unified_conversation_service import (
            UnifiedConversationService,
        )

        # 1. Generate message using UnifiedConversationService
        unified_service = UnifiedConversationService()

        generation_result = await unified_service.generate_handoff_resolution_message(
            db=self.db,
            conversation_id=conversation.id,
            merchant_id=merchant.id,
        )

        message_content = generation_result["content"]
        is_fallback = generation_result["fallback"]
        reason = generation_result["reason"]

        # 2. Store in database
        message = await self._store_message(conversation, message_content)

        # 3. Broadcast to widget (if widget conversation)
        broadcast_sent = False
        if conversation.platform == "widget":
            broadcast_sent = await self._broadcast_to_widget(conversation, message)

        # 4. Track metrics
        logger.info(
            "handoff_resolution_message_sent",
            conversation_id=conversation.id,
            merchant_id=merchant.id,
            business_name=merchant.business_name,
            platform=conversation.platform,
            fallback=is_fallback,
            message_length=len(message_content),
            reason=reason,
            broadcast_sent=broadcast_sent,
            response_time_ms=generation_result.get("response_time_ms"),
        )

        return {
            "sent": True,
            "message_id": message.id,
            "content": message_content,
            "fallback": is_fallback,
            "reason": reason,
            "broadcast_sent": broadcast_sent,
        }

    async def _store_message(
        self,
        conversation: Conversation,
        content: str,
    ) -> Message:
        """Store resolution message in database.

        Args:
            conversation: The conversation
            content: Message content

        Returns:
            Created Message instance
        """
        message = Message(
            conversation_id=conversation.id,
            sender="bot",
            content=content,
            message_type="text",
            created_at=datetime.utcnow(),
        )
        self.db.add(message)
        await self.db.commit()
        await self.db.refresh(message)

        logger.info(
            "handoff_resolution_message_stored",
            conversation_id=conversation.id,
            message_id=message.id,
            message_length=len(content),
        )

        return message

    async def _broadcast_to_widget(
        self,
        conversation: Conversation,
        message: Message,
    ) -> bool:
        """Broadcast resolution message to widget via WebSocket.

        Args:
            conversation: The conversation
            message: The message to broadcast

        Returns:
            True if broadcast was sent successfully, False otherwise
        """
        try:
            from app.services.widget.connection_manager import get_connection_manager

            session_id = conversation.platform_sender_id
            if not session_id:
                logger.warning(
                    "handoff_resolution_no_session_id",
                    conversation_id=conversation.id,
                )
                return False

            # Prepare message payload
            message_payload = {
                "type": "handoff_resolved",
                "data": {
                    "id": message.id,
                    "content": message.content,
                    "sender": "bot",
                    "createdAt": message.created_at.isoformat(),
                },
            }

            # Broadcast via WebSocket
            ws_manager = get_connection_manager()

            # Write to log file for debugging
            with open("/tmp/ws_connections.log", "a") as log_file:
                log_file.write(
                    f"{datetime.now(UTC).isoformat()} - handoff_resolution_broadcast_attempt - session_id={session_id}, manager_id={id(ws_manager)}, connection_count={ws_manager.get_connection_count(session_id)}\n"
                )
                log_file.flush()

            logger.info(
                "handoff_resolution_broadcast_attempt",
                conversation_id=conversation.id,
                session_id=session_id,
                manager_id=id(ws_manager),
                connection_count=ws_manager.get_connection_count(session_id),
            )

            connection_count = await ws_manager.broadcast_to_session(
                session_id=session_id,
                message=message_payload,
            )

            # Log broadcast result
            with open("/tmp/ws_connections.log", "a") as log_file:
                log_file.write(
                    f"{datetime.now(UTC).isoformat()} - handoff_resolution_broadcast_result - session_id={session_id}, connection_count={connection_count}\n"
                )
                log_file.flush()

            logger.info(
                "handoff_resolution_websocket_sent",
                conversation_id=conversation.id,
                session_id=session_id,
                message_id=message.id,
                connection_count=connection_count,
            )

            return connection_count > 0

        except Exception as e:
            logger.error(
                "handoff_resolution_websocket_failed",
                conversation_id=conversation.id,
                error=str(e),
                error_type=type(e).__name__,
            )
            return False


__all__ = ["HandoffResolutionService"]
