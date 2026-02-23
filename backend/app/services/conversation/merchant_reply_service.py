"""Merchant Reply Service.

Handles merchant-initiated replies to conversations across platforms.
Supports Messenger, Widget, and rejects Preview (read-only).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import APIError, ErrorCode
from app.models.conversation import Conversation
from app.models.message import Message

logger = structlog.get_logger(__name__)


class MerchantReplyService:
    """Service for sending merchant replies to conversations.

    Platform-specific behavior:
    - Messenger: Sends via Facebook Send API
    - Widget: Stores message and publishes to SSE channel
    - Preview: Returns error (preview is read-only)
    """

    def __init__(self, db: AsyncSession) -> None:
        """Initialize the merchant reply service.

        Args:
            db: Database session for persistence
        """
        self.db = db
        self.logger = structlog.get_logger(__name__)

        # SSE connection manager reference (set by SSE endpoint)
        self._sse_manager: Any | None = None

    def set_sse_manager(self, manager: Any) -> None:
        """Set the SSE connection manager for widget broadcasts.

        Args:
            manager: SSE manager instance with broadcast_message method
        """
        self._sse_manager = manager

    async def send_reply(
        self,
        conversation_id: int,
        merchant_id: int,
        content: str,
    ) -> dict[str, Any]:
        """Send a merchant reply to a conversation.

        Args:
            conversation_id: The conversation ID
            merchant_id: The merchant ID (for authorization)
            content: The reply message content

        Returns:
            Dict with message details and platform-specific response

        Raises:
            APIError: If conversation not found, access denied, or send fails
        """
        # Get and validate conversation
        conversation = await self._get_conversation(conversation_id, merchant_id)
        platform = conversation.platform

        # Validate content
        if not content or not content.strip():
            raise APIError(
                ErrorCode.VALIDATION_ERROR,
                "Message content cannot be empty",
            )

        if len(content) > 5000:
            raise APIError(
                ErrorCode.VALIDATION_ERROR,
                "Message content exceeds 5000 character limit",
            )

        # Route to platform-specific handler
        if platform == "messenger" or platform == "facebook":
            return await self._send_messenger_reply(conversation, content)
        elif platform == "widget":
            return await self._send_widget_reply(conversation, content)
        elif platform == "preview":
            raise APIError(
                ErrorCode.VALIDATION_ERROR,
                "Cannot reply to preview conversations. Preview is read-only.",
            )
        else:
            raise APIError(
                ErrorCode.VALIDATION_ERROR,
                f"Unsupported platform: {platform}",
            )

    async def _get_conversation(
        self,
        conversation_id: int,
        merchant_id: int,
    ) -> Conversation:
        """Get conversation and verify merchant access.

        Args:
            conversation_id: The conversation ID
            merchant_id: The merchant ID

        Returns:
            Conversation if found and authorized

        Raises:
            APIError: If not found or access denied
        """
        result = await self.db.execute(
            select(Conversation).where(
                Conversation.id == conversation_id,
                Conversation.merchant_id == merchant_id,
            )
        )
        conversation = result.scalars().first()

        if not conversation:
            raise APIError(
                ErrorCode.CONVERSATION_NOT_FOUND,
                "Conversation not found or access denied",
            )

        return conversation

    async def _save_merchant_message(
        self,
        conversation_id: int,
        content: str,
    ) -> Message:
        """Save merchant message to database.

        Args:
            conversation_id: The conversation ID
            content: Message content

        Returns:
            The created Message object

        Raises:
            APIError: If message save fails
        """
        try:
            message = Message(
                conversation_id=conversation_id,
                sender="merchant",
                content=content,
                message_type="text",
            )
            self.db.add(message)
            await self.db.commit()
            await self.db.refresh(message)

            if not message.id:
                raise APIError(
                    ErrorCode.INTERNAL_ERROR,
                    "Message was not saved - no ID returned",
                )

            self.logger.info(
                "merchant_message_saved",
                conversation_id=conversation_id,
                message_id=message.id,
            )

            return message
        except APIError:
            raise
        except Exception as e:
            self.logger.error(
                "merchant_message_save_failed",
                conversation_id=conversation_id,
                error=str(e),
            )
            raise APIError(
                ErrorCode.INTERNAL_ERROR,
                f"Failed to save message: {str(e)}",
            )

    async def _send_messenger_reply(
        self,
        conversation: Conversation,
        content: str,
    ) -> dict[str, Any]:
        """Send reply via Facebook Messenger.

        Args:
            conversation: The conversation
            content: Message content

        Returns:
            Dict with message and Facebook response

        Raises:
            APIError: If Facebook API call fails
        """
        from app.core.security import decrypt_access_token
        from app.models.facebook_integration import FacebookIntegration
        from app.services.messenger.send_service import MessengerSendService

        # Get Facebook integration
        result = await self.db.execute(
            select(FacebookIntegration).where(
                FacebookIntegration.merchant_id == conversation.merchant_id
            )
        )
        fb_integration = result.scalars().first()

        if not fb_integration or not fb_integration.access_token_encrypted:
            raise APIError(
                ErrorCode.NO_FACEBOOK_PAGE_CONNECTION,
                "Merchant has not connected a Facebook page",
            )

        # Decrypt access token and send message
        access_token = decrypt_access_token(fb_integration.access_token_encrypted)
        messenger_service = MessengerSendService(access_token=access_token)

        # Get recipient PSID
        recipient_id = conversation.platform_sender_id

        try:
            # Send via Facebook API
            fb_response = await messenger_service.send_message(
                recipient_id=recipient_id,
                message_payload={"text": content},
            )

            # Save to database
            message = await self._save_merchant_message(conversation.id, content)

            # Update conversation timestamp
            conversation.updated_at = datetime.utcnow()

            # Track merchant message time for handoff resolution
            from app.services.handoff.resolution_service import HandoffResolutionService

            resolution_service = HandoffResolutionService(self.db)
            await resolution_service.update_merchant_message_time(conversation.id)

            await self.db.commit()

            self.logger.info(
                "merchant_messenger_reply_sent",
                conversation_id=conversation.id,
                message_id=message.id,
                fb_message_id=fb_response.get("message_id"),
            )

            return {
                "message": {
                    "id": message.id,
                    "content": message.content,
                    "sender": "merchant",
                    "createdAt": message.created_at.isoformat(),
                },
                "platform": "messenger",
                "facebookResponse": fb_response,
            }

        except APIError:
            raise
        except Exception as e:
            self.logger.error(
                "merchant_messenger_reply_failed",
                conversation_id=conversation.id,
                error=str(e),
            )
            raise APIError(
                ErrorCode.MESSAGE_SEND_FAILED,
                f"Failed to send message via Messenger: {str(e)}",
            )

    async def _send_widget_reply(
        self,
        conversation: Conversation,
        content: str,
    ) -> dict[str, Any]:
        """Send reply to widget session.

        Args:
            conversation: The conversation
            content: Message content

        Returns:
            Dict with message details

        Raises:
            APIError: If session not found or broadcast fails
        """
        from app.services.widget.widget_session_service import WidgetSessionService

        # Get session ID from conversation
        session_id = conversation.platform_sender_id

        if not session_id:
            raise APIError(
                ErrorCode.VALIDATION_ERROR,
                "Conversation has no associated widget session",
            )

        try:
            # Save message to database
            message = await self._save_merchant_message(conversation.id, content)

            # Add to widget session message history (non-critical, log failures)
            try:
                session_service = WidgetSessionService()
                await session_service.add_message_to_history(
                    session_id=session_id,
                    role="merchant",
                    content=content,
                )
            except Exception as e:
                self.logger.warning(
                    "widget_message_history_add_failed",
                    session_id=session_id,
                    error=str(e),
                )

            # Prepare message payload
            message_payload = {
                "type": "merchant_message",
                "data": {
                    "id": message.id,
                    "content": message.content,
                    "sender": "merchant",
                    "createdAt": message.created_at.isoformat(),
                },
            }

            # Broadcast via WebSocket (preferred)
            ws_sent = False
            try:
                from app.services.widget.connection_manager import get_connection_manager

                ws_manager = get_connection_manager()
                await ws_manager.broadcast_to_session(session_id, message_payload)
                ws_sent = True
                self.logger.info(
                    "websocket_broadcast_sent",
                    session_id=session_id,
                    message_id=message.id,
                )
            except Exception as e:
                self.logger.warning(
                    "websocket_broadcast_failed",
                    session_id=session_id,
                    error=str(e),
                )

            # Fallback: Broadcast via SSE if manager is available (legacy support)
            sse_sent = False
            if self._sse_manager:
                try:
                    await self._sse_manager.broadcast_message(
                        session_id=session_id,
                        message=message_payload,
                    )
                    sse_sent = True
                except Exception as e:
                    self.logger.warning(
                        "widget_sse_broadcast_failed",
                        session_id=session_id,
                        error=str(e),
                    )

            # Update conversation timestamp
            conversation.updated_at = datetime.utcnow()

            # Track merchant message time for handoff resolution
            from app.services.handoff.resolution_service import HandoffResolutionService

            resolution_service = HandoffResolutionService(self.db)
            await resolution_service.update_merchant_message_time(conversation.id)

            await self.db.commit()

            self.logger.info(
                "merchant_widget_reply_sent",
                conversation_id=conversation.id,
                message_id=message.id,
                session_id=session_id,
                ws_sent=ws_sent,
                sse_sent=sse_sent,
            )

            return {
                "message": {
                    "id": message.id,
                    "content": message.content,
                    "sender": "merchant",
                    "createdAt": message.created_at.isoformat(),
                },
                "platform": "widget",
                "sessionId": session_id,
                "wsSent": ws_sent,
                "sseSent": sse_sent,
            }
        except APIError:
            raise
        except Exception as e:
            self.logger.error(
                "merchant_widget_reply_failed",
                conversation_id=conversation.id,
                session_id=session_id,
                error=str(e),
            )
            raise APIError(
                ErrorCode.INTERNAL_ERROR,
                f"Failed to send widget reply: {str(e)}",
            )
