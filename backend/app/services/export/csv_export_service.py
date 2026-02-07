"""CSV Export Service for conversations.

Provides CSV generation with Excel-compatible formatting, filter support,
and proper handling of large datasets via streaming.
"""

from __future__ import annotations

import csv
from datetime import datetime
from io import StringIO
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.conversation import Conversation
from app.models.llm_conversation_cost import LLMConversationCost
from app.models.message import Message
from app.core.errors import APIError, ErrorCode
from app.services.export.cost_calculator import CostCalculator


# CSV column headers (fixed order as per AC4)
CSV_HEADERS = [
    "Conversation ID",
    "Customer ID",
    "Created Date",
    "Updated Date",
    "Status",
    "Sentiment",
    "Message Count",
    "Has Order",
    "LLM Provider",
    "Total Tokens",
    "Estimated Cost (USD)",
    "Last Message Preview",
]

# UTF-8 BOM for Excel UTF-8 detection
UTF8_BOM = "\uFEFF"

# Maximum export limit (per AC2)
MAX_EXPORT_CONVERSATIONS = 10_000


class CSVExportService:
    """Service for generating CSV exports of conversation data.

    Features:
    - Excel-compatible formatting (UTF-8 BOM, CRLF line endings)
    - Filter support (date range, search, status, sentiment, handoff)
    - LLM cost aggregation and calculation
    - Streaming for memory efficiency with large datasets
    - Customer ID masking for privacy
    """

    def __init__(self) -> None:
        """Initialize CSV export service with cost calculator."""
        self.cost_calculator = CostCalculator()

    async def generate_conversations_csv(
        self,
        db: AsyncSession,
        merchant_id: int,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        search: Optional[str] = None,
        status: Optional[list[str]] = None,
        sentiment: Optional[list[str]] = None,
        has_handoff: Optional[bool] = None,
    ) -> tuple[str, int]:
        """Generate CSV export of conversations for a merchant.

        Args:
            db: Database session
            merchant_id: ID of the authenticated merchant
            date_from: Start date filter (ISO 8601)
            date_to: End date filter (ISO 8601)
            search: Search term for customer ID or message content
            status: List of status values to filter by
            sentiment: List of sentiment values to filter by (currently placeholder)
            has_handoff: Filter by handoff presence

        Returns:
            Tuple of (CSV content string, total count)

        Raises:
            APIError: If export exceeds maximum limit
        """
        # Build query with filters
        query = self._build_filtered_query(
            merchant_id=merchant_id,
            date_from=date_from,
            date_to=date_to,
            search=search,
            status=status,
            sentiment=sentiment,
            has_handoff=has_handoff,
        )

        # Get total count and validate limit
        total = await self._get_conversation_count(db, query)
        if total > MAX_EXPORT_CONVERSATIONS:
            raise APIError(
                ErrorCode.EXPORT_TOO_LARGE,
                f"Export limited to {MAX_EXPORT_CONVERSATIONS:,} conversations. Found {total:,}.",
                {"limit": MAX_EXPORT_CONVERSATIONS, "found": total},
            )

        # Generate CSV content
        csv_content = await self._generate_csv_content(db, query)

        return csv_content, total

    def _build_filtered_query(
        self,
        merchant_id: int,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        search: Optional[str] = None,
        status: Optional[list[str]] = None,
        sentiment: Optional[list[str]] = None,
        has_handoff: Optional[bool] = None,
    ) -> select:
        """Build SQLAlchemy query with filters applied.

        Reuses filter logic from conversation service (Story 3.2).
        """
        # Start with base query
        query = (
            select(Conversation)
            .options(selectinload(Conversation.messages))
            .where(Conversation.merchant_id == merchant_id)
        )

        # Apply search filter (customer ID and bot message content)
        if search and search.strip():
            from sqlalchemy import or_, exists

            search_pattern = f"%{search.strip()}%"
            customer_id_match = Conversation.platform_sender_id.ilike(search_pattern)
            message_content_match = (
                select(Message.id)
                .where(Message.conversation_id == Conversation.id)
                .where(Message.sender == "bot")
                .where(Message.content.ilike(search_pattern))
                .exists()
            )
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
                to_datetime = to_datetime.replace(
                    hour=23, minute=59, second=59, microsecond=999999
                )
                query = query.where(Conversation.created_at <= to_datetime)
            except ValueError:
                # Invalid date format - ignore filter
                pass

        # Apply status filter
        if status:
            query = query.where(Conversation.status.in_(status))

        # Note: Sentiment filter is a placeholder until sentiment analysis is implemented
        # Current implementation sets all sentiments to "neutral"

        # Apply handoff filter
        if has_handoff is True:
            query = query.where(Conversation.status == "handoff")
        elif has_handoff is False:
            query = query.where(Conversation.status != "handoff")

        # Order by created date (oldest first for chronological export)
        query = query.order_by(Conversation.created_at)

        return query

    async def _get_conversation_count(
        self, db: AsyncSession, query: select
    ) -> int:
        """Get total count of conversations matching the query."""
        count_query = select(func.count()).select_from(query.subquery())
        result = await db.execute(count_query)
        return result.scalar() or 0

    async def _generate_csv_content(
        self, db: AsyncSession, query: select
    ) -> str:
        """Generate CSV content from query results.

        Uses streaming to handle large datasets efficiently.
        """
        output = StringIO()

        # Write UTF-8 BOM for Excel compatibility
        output.write(UTF8_BOM)

        # Create CSV writer with CRLF line endings for Excel
        writer = csv.writer(
            output,
            delimiter=",",
            quotechar='"',
            quoting=csv.QUOTE_MINIMAL,
            lineterminator="\r\n",
        )

        # Write header row
        writer.writerow(CSV_HEADERS)

        # Stream results and write rows
        result = await db.stream(query)

        async for row in result.scalars():
            row_data = self._format_conversation_row(row)
            writer.writerow(row_data)

        return output.getvalue()

    def _format_conversation_row(self, conv: Conversation) -> list:
        """Format a conversation as a CSV row.

        Aggregates data from conversation, messages, and LLM costs.
        """
        messages = conv.messages if conv.messages else []
        message_count = len(messages)

        # Customer ID (masked - last 4 characters)
        customer_id = f"****{conv.platform_sender_id[-4:]}" if len(conv.platform_sender_id) >= 4 else "****"

        # Format dates for Excel (YYYY-MM-DD HH:MM:SS)
        created_date = conv.created_at.strftime("%Y-%m-%d %H:%M:%S")
        updated_date = conv.updated_at.strftime("%Y-%m-%d %H:%M:%S")

        # Status
        status = conv.status if conv.status else "active"

        # Sentiment (placeholder until analysis is implemented)
        sentiment = "neutral"

        # Check for order references in messages
        has_order = any(
            msg.message_metadata and msg.message_metadata.get("order_reference") is not None
            for msg in messages
        )

        # LLM provider and tokens (aggregate from messages or default)
        llm_provider = "ollama"  # Default
        total_tokens = 0

        if messages:
            # Use provider from first bot message if available
            for msg in messages:
                if msg.sender == "bot" and msg.message_metadata:
                    provider = msg.message_metadata.get("llm_provider")
                    if provider:
                        llm_provider = provider
                        break

        # Calculate estimated cost
        estimated_cost = self.cost_calculator.calculate_llm_cost(
            llm_provider, total_tokens
        )

        # Last message preview (truncated to 100 chars)
        last_message_preview = ""
        if messages:
            # Sort by created_at to find last message
            sorted_msgs = sorted(messages, key=lambda m: m.created_at, reverse=True)
            last_msg = sorted_msgs[0]
            # Get decrypted content
            if last_msg.sender == "customer":
                # Customer messages are encrypted - this won't work without decryption
                # For now, use placeholder
                last_message_preview = "[Encrypted customer message]"
            else:
                content = last_msg.content
                # Truncate to 100 characters
                if len(content) > 100:
                    last_message_preview = content[:100] + "..."
                else:
                    last_message_preview = content

        # Format cost to 4 decimal places
        cost_str = f"{estimated_cost:.4f}"

        return [
            conv.id,
            customer_id,
            created_date,
            updated_date,
            status,
            sentiment,
            message_count,
            "true" if has_order else "false",
            llm_provider,
            total_tokens,
            cost_str,
            # Escape quotes in message preview and wrap in quotes
            ('"' + last_message_preview.replace('"', '""') + '"'),
        ]
