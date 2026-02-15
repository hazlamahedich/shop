from typing import List, Tuple, Optional
from datetime import datetime
from sqlalchemy import select, func, desc, asc, or_, and_, exists
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.conversation import Conversation
from app.models.message import Message
from app.models.handoff_alert import HandoffAlert


class ConversationService:
    """Service for managing conversation data retrieval."""

    async def get_conversations(
        self,
        db: AsyncSession,
        merchant_id: int,
        page: int = 1,
        per_page: int = 20,
        sort_by: str = "updated_at",
        sort_order: str = "desc",
        search: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        status: Optional[List[str]] = None,
        sentiment: Optional[List[str]] = None,
        has_handoff: Optional[bool] = None,
    ) -> Tuple[List[dict], int]:
        """
        Get paginated conversations for a merchant with last message preview.

        Supports search and filtering by:
        - Search term: customer ID or message content
        - Date range: created_at date range
        - Status: active, handoff, closed
        - Sentiment: positive, neutral, negative
        - Handoff: has/doesn't have handoff

        Args:
            db: Database session
            merchant_id: ID of the authenticated merchant
            page: Page number (1-based)
            per_page: Items per page
            sort_by: Column to sort by (updated_at, status, created_at)
            sort_order: Sort direction (asc, desc)
            search: Search term for customer ID or message content
            date_from: Start date filter (ISO 8601 string)
            date_to: End date filter (ISO 8601 string)
            status: List of status values to filter by
            sentiment: List of sentiment values to filter by
            has_handoff: Filter by handoff presence

        Returns:
            Tuple of (list of conversation dicts, total count)
        """
        # Start with base query
        query = (
            select(Conversation)
            .options(selectinload(Conversation.messages))
            .where(Conversation.merchant_id == merchant_id)
        )

        # Apply search filter (searches customer ID and message content)
        if search and search.strip():
            search_pattern = f"%{search.strip()}%"
            # Search customer ID directly (plaintext)
            customer_id_match = Conversation.platform_sender_id.ilike(search_pattern)

            # For message content search, we need to check both encrypted and potential plaintext
            # In production, a proper full-text search index with decrypted content should be used
            # For now, we'll search on the encrypted content as-is - this won't find encrypted messages
            # A proper implementation would require either:
            # 1. Storing a separate decrypted copy for search (privacy consideration)
            # 2. Using pgcrypto with deterministic encryption for search
            # 3. Full-text search engine with decrypted content

            # For this implementation, we search:
            # - Customer ID (plaintext, always works)
            # - Message content (only works for bot messages which are plaintext)
            # This is a known limitation - message content search for customer messages
            # will require infrastructure updates for full-text search on decrypted data

            # Note: bot messages are stored in plaintext, customer messages are encrypted
            # So we can search bot message content, but customer message content search
            # requires decryption (which is expensive at scale)

            # For now, implement customer ID search + bot message content search
            # Document that customer message search requires full-text search infrastructure
            message_content_match = (
                select(Message.id)
                .where(Message.conversation_id == Conversation.id)
                .where(Message.sender == "bot")  # Only bot messages are plaintext
                .where(Message.content.ilike(search_pattern))
                .exists()
            )

            # For customer messages, we would need to decrypt each message and search
            # This is too expensive for database-level filtering
            # A proper solution would be a full-text search index with decrypted content

            query = query.where(or_(customer_id_match, message_content_match))

        # Apply date range filter
        if date_from:
            try:
                from_datetime = datetime.fromisoformat(date_from)
                query = query.where(Conversation.created_at >= from_datetime)
            except ValueError:
                # Invalid date format - ignore filter
                pass

        if date_to:
            try:
                to_datetime = datetime.fromisoformat(date_to)
                # End of day
                to_datetime = to_datetime.replace(hour=23, minute=59, second=59, microsecond=999999)
                query = query.where(Conversation.created_at <= to_datetime)
            except ValueError:
                # Invalid date format - ignore filter
                pass

        # Apply status filter (multi-select)
        if status:
            query = query.where(Conversation.status.in_(status))

        # Apply sentiment filter (multi-select)
        # Note: Currently mocked as "neutral" for all conversations
        if sentiment:
            # When sentiment analysis is implemented, this will filter properly
            # For now, this is a placeholder
            pass

        # Apply handoff filter
        if has_handoff is True:
            # Has handoff status
            query = query.where(Conversation.status == "handoff")
        elif has_handoff is False:
            # No handoff status
            query = query.where(Conversation.status != "handoff")

        # Get total count with filters applied
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        # Apply sorting and pagination
        sort_column = getattr(Conversation, sort_by, Conversation.updated_at)
        if sort_order == "desc":
            order_clause = desc(sort_column)
        else:
            order_clause = asc(sort_column)

        query = query.order_by(order_clause).limit(per_page).offset((page - 1) * per_page)

        result = await db.execute(query)
        conversations = result.scalars().all()

        # Format result
        formatted_conversations = []
        for conv in conversations:
            # Get last message if exists
            last_msg = None
            if conv.messages:
                # Sort messages by created_at in memory to find the last one
                sorted_msgs = sorted(conv.messages, key=lambda m: m.created_at, reverse=True)
                last_msg = sorted_msgs[0]

            formatted_conversations.append(
                {
                    "id": conv.id,
                    "platform_sender_id": conv.platform_sender_id,
                    "platform_sender_id_masked": (
                        f"{conv.platform_sender_id[:4]}****"
                        if len(conv.platform_sender_id) > 4
                        else "****"
                    ),
                    "last_message": last_msg.decrypted_content if last_msg else None,
                    "status": conv.status,
                    "sentiment": "neutral",  # Placeholder until sentiment analysis is implemented
                    "message_count": len(conv.messages),
                    "updated_at": conv.updated_at,
                    "created_at": conv.created_at,
                }
            )

        return formatted_conversations, total

    async def get_active_count(
        self,
        db: AsyncSession,
        merchant_id: int,
    ) -> int:
        """Get count of active conversations for a merchant.

        Active conversations are those where status='active' (not in handoff or closed).

        Args:
            db: Database session
            merchant_id: ID of the authenticated merchant

        Returns:
            Count of active conversations
        """
        query = select(func.count()).where(
            Conversation.merchant_id == merchant_id,
            Conversation.status == "active",
        )
        result = await db.execute(query)
        return result.scalar() or 0

    async def get_conversation_history(
        self,
        db: AsyncSession,
        conversation_id: int,
        merchant_id: int,
    ) -> Optional[dict]:
        """
        Get full conversation history with context for handoff.

        Args:
            db: Database session
            conversation_id: ID of the conversation
            merchant_id: ID of the authenticated merchant

        Returns:
            Dictionary with conversation history data, or None if not found
        """
        query = (
            select(Conversation)
            .options(
                selectinload(Conversation.messages),
                selectinload(Conversation.handoff_alert),
            )
            .where(
                Conversation.id == conversation_id,
                Conversation.merchant_id == merchant_id,
            )
        )

        result = await db.execute(query)
        conversation = result.scalars().first()

        if not conversation:
            return None

        messages = []
        for msg in sorted(conversation.messages, key=lambda m: m.created_at):
            confidence_score = None
            if msg.sender == "bot" and msg.message_metadata:
                confidence_score = msg.message_metadata.get("confidence_score")

            messages.append(
                {
                    "id": msg.id,
                    "sender": msg.sender,
                    "content": msg.decrypted_content,
                    "created_at": msg.created_at,
                    "confidence_score": confidence_score,
                }
            )

        context_data = conversation.decrypted_metadata or {}
        cart_state = None
        extracted_constraints = None

        if context_data:
            cart_data = context_data.get("cart", {})
            if cart_data:
                cart_state = {
                    "items": cart_data.get("items", []),
                }

            constraints_data = context_data.get("constraints", {})
            if constraints_data:
                extracted_constraints = {
                    "budget": constraints_data.get("budget"),
                    "size": constraints_data.get("size"),
                    "category": constraints_data.get("category"),
                }

        urgency_level = "low"
        if conversation.handoff_alert:
            urgency_level = conversation.handoff_alert.urgency_level

        wait_time_seconds = 0
        if conversation.handoff_triggered_at:
            wait_time_seconds = int(
                (datetime.utcnow() - conversation.handoff_triggered_at).total_seconds()
            )

        handoff = {
            "trigger_reason": conversation.handoff_reason or "unknown",
            "triggered_at": conversation.handoff_triggered_at or datetime.utcnow(),
            "urgency_level": urgency_level,
            "wait_time_seconds": wait_time_seconds,
        }

        masked_id = (
            f"{conversation.platform_sender_id[:4]}****"
            if len(conversation.platform_sender_id) > 4
            else "****"
        )

        customer = {
            "masked_id": masked_id,
            "order_count": 0,
        }

        return {
            "conversation_id": conversation.id,
            "messages": messages,
            "context": {
                "cart_state": cart_state,
                "extracted_constraints": extracted_constraints,
            },
            "handoff": handoff,
            "customer": customer,
        }
