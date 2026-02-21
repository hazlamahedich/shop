"""Unified cart key strategy for cross-channel cart persistence.

Story 5-10: Widget Full App Integration
Task 3: Create Unified Cart Key Strategy

Provides consistent cart key generation for Widget, Messenger, and Preview.
"""

from __future__ import annotations

from app.services.conversation.schemas import ConversationContext


class CartKeyStrategy:
    """Unified cart key generation for all channels.

    Cart keys are used as Redis keys to persist cart state.
    Each channel has a unique key format to prevent collisions.
    """

    @staticmethod
    def for_messenger(psid: str) -> str:
        """Generate cart key for Facebook Messenger.

        Args:
            psid: Facebook Page-Scoped ID

        Returns:
            Cart key in format: cart:messenger:{psid}
        """
        return f"cart:messenger:{psid}"

    @staticmethod
    def for_widget(session_id: str) -> str:
        """Generate cart key for Widget.

        Args:
            session_id: Widget session UUID

        Returns:
            Cart key in format: cart:widget:{session_id}
        """
        return f"cart:widget:{session_id}"

    @staticmethod
    def for_preview(merchant_id: int, user_id: int) -> str:
        """Generate cart key for Preview mode.

        Args:
            merchant_id: Merchant ID
            user_id: User ID

        Returns:
            Cart key in format: cart:preview:{merchant_id}:{user_id}
        """
        return f"cart:preview:{merchant_id}:{user_id}"

    @staticmethod
    def get_key_for_context(context: ConversationContext) -> str:
        """Generate cart key based on conversation context.

        Args:
            context: Conversation context with channel info

        Returns:
            Appropriate cart key for the channel
        """
        if context.channel == "widget":
            return CartKeyStrategy.for_widget(context.session_id)
        elif context.channel == "messenger":
            psid = context.platform_sender_id or context.session_id
            return CartKeyStrategy.for_messenger(psid)
        elif context.channel == "preview":
            user_id = context.user_id or 0
            return CartKeyStrategy.for_preview(context.merchant_id, user_id)
        else:
            return f"cart:unknown:{context.session_id}"

    @staticmethod
    def parse(key: str) -> tuple[str, str]:
        """Parse cart key to extract channel and identifier.

        Args:
            key: Cart key string

        Returns:
            Tuple of (channel, identifier)
        """
        parts = key.split(":")
        if len(parts) >= 3:
            return parts[1], parts[2]
        return "unknown", key
