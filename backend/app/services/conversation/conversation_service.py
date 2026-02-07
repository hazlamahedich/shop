from typing import List, Tuple
from sqlalchemy import select, func, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.conversation import Conversation


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
    ) -> Tuple[List[dict], int]:
        """
        Get paginated conversations for a merchant with last message preview.

        Args:
            db: Database session
            merchant_id: ID of the authenticated merchant
            page: Page number (1-based)
            per_page: Items per page
            sort_by: Column to sort by (updated_at, status, created_at)
            sort_order: Sort direction (asc, desc)

        Returns:
            Tuple of (list of conversation dicts, total count)
        """
        # Determine sort column
        sort_column = getattr(Conversation, sort_by, Conversation.updated_at)
        if sort_order == "desc":
            order_clause = desc(sort_column)
        else:
            order_clause = asc(sort_column)

        # 1. Get total count
        count_query = (
            select(func.count())
            .select_from(Conversation)
            .where(Conversation.merchant_id == merchant_id)
        )
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        # 2. Get paginated conversations with messages loaded
        # Note: In a high-scale environment, we would use a more optimized query
        # to fetch only the last message, but for now selectinload is sufficient.
        query = (
            select(Conversation)
            .options(selectinload(Conversation.messages))
            .where(Conversation.merchant_id == merchant_id)
            .order_by(order_clause)
            .limit(per_page)
            .offset((page - 1) * per_page)
        )

        result = await db.execute(query)
        conversations = result.scalars().all()

        # 3. Format result
        formatted_conversations = []
        for conv in conversations:
            # Get last message if exists
            # Messages are not guaranteed to be sorted by default in relationship unless configured
            # But usually append order works. Ideally we'd sort messages.
            # For robustness, let's find the latest message in the loaded list.
            last_msg = None
            if conv.messages:
                # Sort messages by created_at in memory to find the last one
                # This is acceptable for reasonable conversation lengths
                sorted_msgs = sorted(conv.messages, key=lambda m: m.created_at, reverse=True)
                last_msg = sorted_msgs[0]

            formatted_conversations.append(
                {
                    "id": conv.id,
                    "platform_sender_id": conv.platform_sender_id,  # Masking handled in API/Serializer if needed, or here? Plan said component. Let's do it here or let frontend do it. Plan said "Display masked customer ID", implies frontend. But usually better in backend. Validating plan... plan said "Display masked customer ID (show first 4 chars, rest asterisks)" in frontend tasks. But API response example showed masked. Let's mask here for security.
                    "platform_sender_id_masked": (
                        f"{conv.platform_sender_id[:4]}****"
                        if len(conv.platform_sender_id) > 4
                        else "****"
                    ),
                    "last_message": last_msg.decrypted_content if last_msg else None,
                    "status": conv.status,
                    "sentiment": "neutral",  # Placeholder
                    "message_count": len(conv.messages),
                    "updated_at": conv.updated_at,
                    "created_at": conv.created_at,
                }
            )

        return formatted_conversations, total
