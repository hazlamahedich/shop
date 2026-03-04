"""Merchant Data Export Service

Story 6-3: Merchant CSV Export

Complete merchant data export for GDPR/CCPA compliance.
Different from csv_export_service.py (Story 3.2):
- Story 3.2: Filtered conversation exports for dashboard UI
- Story 6-3: Complete merchant data export for data sovereignty
"""

from __future__ import annotations

import csv
import io
from datetime import datetime, timezone
from typing import AsyncGenerator, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.core.errors import APIError, ErrorCode
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.llm_conversation_cost import LLMConversationCost
from app.models.merchant import Merchant
from app.models.data_export_audit_log import DataExportAuditLog
from app.models.consent import Consent, ConsentType
from app.schemas.consent import ConsentStatus


logger = structlog.get_logger(__name__)


class MerchantDataExportService:
    """Complete merchant data export for GDPR compliance.

    Exports ALL merchant data (conversations, messages, costs, config).
    Implements consent-based filtering for GDPR/CCPA compliance.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def export_merchant_data(
        self,
        merchant_id: int,
    ) -> AsyncGenerator[str, None]:
        """Export ALL merchant data as streaming CSV.

        Args:
            merchant_id: Merchant ID to export

        Yields:
            CSV rows as strings (streaming response)

        Raises:
            APIError: If merchant not found or export fails
        """
        audit_log = await self._create_audit_log(merchant_id)

        try:
            # Get accurate counts from database
            total_conversations = await self._count_conversations(merchant_id)
            total_messages = await self._count_messages(merchant_id)
            total_cost = await self._calculate_total_cost(merchant_id)

            # Stream metadata section
            for chunk in self._generate_metadata_section(
                merchant_id, total_conversations, total_messages, total_cost
            ):
                yield chunk

            # Generate sections (consent map loaded once for efficiency)
            consent_map = await self._batch_load_consent_statuses(merchant_id)

            opted_out_count = 0
            # Stream conversations section
            async for chunk in self._generate_conversations_section(merchant_id, consent_map):
                yield chunk
                if (
                    chunk.strip()
                    and "," in chunk
                    and not chunk.startswith("#")
                    and not chunk.startswith("##")
                ):
                    parts = chunk.split(",")
                    if len(parts) > 3 and parts[3].strip() in ['"opted_out"', '"pending"']:
                        opted_out_count += 1

            # Stream messages section
            async for chunk in self._generate_messages_section(merchant_id, consent_map):
                yield chunk

            # Stream costs section
            async for chunk in self._generate_costs_section(merchant_id):
                yield chunk

            # Stream configuration section
            async for chunk in self._generate_configuration_section(merchant_id):
                yield chunk

            # Update audit log with final counts
            audit_log.mark_completed(
                conversations=total_conversations,
                messages=total_messages,
                excluded=opted_out_count,
                size=0,  # Size not known in streaming mode
            )
            await self.db.commit()

        except Exception as e:
            logger.error("export_failed", merchant_id=merchant_id, error=str(e))
            audit_log.error_message = str(e)
            await self.db.commit()
            raise APIError(
                ErrorCode.EXPORT_GENERATION_FAILED,
                f"Export generation failed: {str(e)}",
            )

    def _generate_metadata_section(
        self,
        merchant_id: int,
        total_conversations: int,
        total_messages: int,
        total_cost: float,
    ):
        """Generate CSV metadata header."""
        yield "# Merchant Data Export\n"
        yield f"# Export Date: {datetime.now(timezone.utc).isoformat()}\n"
        yield f"# Merchant ID: {merchant_id}\n"
        yield f"# Total Conversations: {total_conversations}\n"
        yield f"# Total Messages: {total_messages}\n"
        yield f"# Total LLM Cost: ${total_cost:.2f}\n"
        yield "\n"

    async def _generate_conversations_section(
        self,
        merchant_id: int,
        consent_map: dict[str, ConsentStatus],
    ) -> AsyncGenerator[str, None]:
        """Generate conversations section with consent-based filtering."""
        yield "## SECTION: CONVERSATIONS\n"
        yield "conversation_id,platform,customer_id,consent_status,started_at,ended_at,message_count\n"

        offset = 0
        chunk_size = 1000

        while True:
            result = await self.db.execute(
                select(Conversation)
                .where(Conversation.merchant_id == merchant_id)
                .order_by(Conversation.created_at)
                .offset(offset)
                .limit(chunk_size)
            )
            conversations = result.scalars().all()

            if not conversations:
                break

            for conv in conversations:
                # Use visitor_id-first lookup pattern from Story 6-1
                # visitor_id may not exist for pre-6-1 conversations
                visitor_id = getattr(conv, "visitor_id", None)
                consent_status = self._get_consent_from_map(
                    consent_map, conv.platform_sender_id, visitor_id
                )

                if consent_status == ConsentStatus.OPTED_OUT:
                    customer_id = f"anon_{conv.id}"
                    status_str = "opted_out"
                elif consent_status == ConsentStatus.PENDING:
                    customer_id = f"anon_{conv.id}"
                    status_str = "pending"
                else:
                    customer_id = conv.platform_sender_id or f"customer_{conv.id}"
                    status_str = "opted_in"

                ended_at = conv.updated_at.isoformat() if conv.updated_at else ""

                row = self._sanitize_csv_row(
                    [
                        str(conv.id),
                        conv.platform,
                        customer_id,
                        status_str,
                        conv.created_at.isoformat() if conv.created_at else "",
                        ended_at,
                        "0",  # Message count not available without eager loading
                    ]
                )

                yield ",".join(row) + "\n"

            offset += chunk_size

    async def _generate_messages_section(
        self,
        merchant_id: int,
        consent_map: dict[str, ConsentStatus],
    ) -> AsyncGenerator[str, None]:
        """Generate messages section with consent-based content filtering."""
        yield "\n## SECTION: MESSAGES\n"
        yield "message_id,conversation_id,role,content,created_at\n"

        offset = 0
        chunk_size = 1000

        while True:
            result = await self.db.execute(
                select(Message)
                .join(Conversation, Message.conversation_id == Conversation.id)
                .where(Conversation.merchant_id == merchant_id)
                .order_by(Message.created_at)
                .offset(offset)
                .limit(chunk_size)
            )
            messages = result.scalars().all()

            if not messages:
                break

            for msg in messages:
                conversation_result = await self.db.execute(
                    select(Conversation).where(Conversation.id == msg.conversation_id)
                )
                conv = conversation_result.scalars().first()

                if not conv:
                    continue

                # Use visitor_id-first lookup pattern from Story 6-1
                # visitor_id may not exist for pre-6-1 conversations
                visitor_id = getattr(conv, "visitor_id", None)
                consent_status = self._get_consent_from_map(
                    consent_map, conv.platform_sender_id, visitor_id
                )

                if consent_status in [ConsentStatus.OPTED_OUT, ConsentStatus.PENDING]:
                    content = ""
                else:
                    try:
                        content = msg.decrypted_content
                    except Exception as e:
                        logger.warning("decryption_failed", message_id=msg.id, error=str(e))
                        content = ""

                row = self._sanitize_csv_row(
                    [
                        str(msg.id),
                        str(msg.conversation_id),
                        msg.sender,  # Message model uses 'sender' not 'role'
                        content,
                        msg.created_at.isoformat() if msg.created_at else "",
                    ]
                )

                yield ",".join(row) + "\n"

            offset += chunk_size

    async def _generate_costs_section(
        self,
        merchant_id: int,
    ) -> AsyncGenerator[str, None]:
        """Generate LLM costs section (operational data, always included)."""
        yield "\n## SECTION: LLM COSTS\n"
        yield "cost_id,conversation_id,provider,model,input_tokens,output_tokens,cost_usd,created_at\n"

        offset = 0
        chunk_size = 1000

        while True:
            result = await self.db.execute(
                select(LLMConversationCost)
                .where(LLMConversationCost.merchant_id == merchant_id)
                .order_by(LLMConversationCost.request_timestamp)
                .offset(offset)
                .limit(chunk_size)
            )
            costs = result.scalars().all()

            if not costs:
                break

            for cost in costs:
                row = self._sanitize_csv_row(
                    [
                        str(cost.id),
                        str(cost.conversation_id),
                        cost.provider or "",
                        cost.model or "",
                        str(cost.prompt_tokens),  # LLMConversationCost uses prompt_tokens
                        str(cost.completion_tokens),  # LLMConversationCost uses completion_tokens
                        f"{cost.total_cost_usd:.4f}" if cost.total_cost_usd else "0.0000",
                        cost.request_timestamp.isoformat() if cost.request_timestamp else "",
                    ]
                )

                yield ",".join(row) + "\n"

            offset += chunk_size

    async def _generate_configuration_section(
        self,
        merchant_id: int,
    ) -> AsyncGenerator[str, None]:
        """Generate configuration section (operational data, always included)."""
        yield "\n## SECTION: CONFIGURATION\n"
        yield "setting_name,setting_value\n"

        result = await self.db.execute(select(Merchant).where(Merchant.id == merchant_id))
        merchant = result.scalars().first()

        if not merchant:
            return

        if merchant.bot_name:
            row = self._sanitize_csv_row(["bot_name", merchant.bot_name])
            yield ",".join(row) + "\n"

        if merchant.personality:
            row = self._sanitize_csv_row(
                [
                    "personality",
                    merchant.personality.value
                    if hasattr(merchant.personality, "value")
                    else str(merchant.personality),
                ]
            )
            yield ",".join(row) + "\n"

        if merchant.custom_greeting:
            row = self._sanitize_csv_row(["custom_greeting", merchant.custom_greeting])
            yield ",".join(row) + "\n"

    async def _get_consent_status(
        self,
        merchant_id: int,
        session_id: str,
    ) -> ConsentStatus:
        """Get consent status for a session.

        Args:
            merchant_id: Merchant ID
            session_id: Session ID (platform_sender_id from conversation)

        Returns:
            Consent status (OPTED_IN, OPTED_OUT, or PENDING)
        """
        result = await self.db.execute(
            select(Consent).where(
                Consent.session_id == session_id,
                Consent.merchant_id == merchant_id,
                Consent.consent_type == ConsentType.CONVERSATION,
            )
        )
        consent = result.scalars().first()

        if not consent:
            return ConsentStatus.PENDING

        if consent.granted:
            return ConsentStatus.OPTED_IN
        else:
            return ConsentStatus.OPTED_OUT

    def _sanitize_csv_row(self, values: list[str]) -> list[str]:
        """Sanitize CSV row to prevent formula injection.

        Args:
            values: List of string values

        Returns:
            Sanitized values with proper escaping
        """
        sanitized = []
        for value in values:
            sanitized_value = self._sanitize_csv_field(str(value))
            sanitized.append(f'"{sanitized_value}"')
        return sanitized

    def _sanitize_csv_field(self, value: str) -> str:
        """Prevent CSV formula injection by escaping dangerous characters.

        Args:
            value: Field value to sanitize

        Returns:
            Sanitized value
        """
        if not value:
            return ""

        dangerous_chars = ("=", "+", "-", "@", "\t", "\r")
        if value.startswith(dangerous_chars):
            return "'" + value

        return value.replace('"', '""')

    async def _create_audit_log(self, merchant_id: int) -> DataExportAuditLog:
        """Create audit log entry for this export.

        Args:
            merchant_id: Merchant ID

        Returns:
            Created audit log entry
        """
        audit_log = DataExportAuditLog(merchant_id=merchant_id)
        self.db.add(audit_log)
        await self.db.flush()
        return audit_log

    async def _count_conversations(self, merchant_id: int) -> int:
        """Count total conversations for merchant.

        Args:
            merchant_id: Merchant ID

        Returns:
            Total conversation count
        """
        from sqlalchemy import func

        result = await self.db.execute(
            select(func.count(Conversation.id)).where(Conversation.merchant_id == merchant_id)
        )
        return result.scalar() or 0

    async def _count_messages(self, merchant_id: int) -> int:
        """Count total messages for merchant.

        Args:
            merchant_id: Merchant ID

        Returns:
            Total message count
        """
        from sqlalchemy import func

        result = await self.db.execute(
            select(func.count(Message.id))
            .join(Conversation, Message.conversation_id == Conversation.id)
            .where(Conversation.merchant_id == merchant_id)
        )
        return result.scalar() or 0

    async def _calculate_total_cost(self, merchant_id: int) -> float:
        """Calculate total LLM cost for merchant.

        Args:
            merchant_id: Merchant ID

        Returns:
            Total cost in USD
        """
        from sqlalchemy import func

        result = await self.db.execute(
            select(func.sum(LLMConversationCost.total_cost_usd)).where(
                LLMConversationCost.merchant_id == merchant_id
            )
        )
        return float(result.scalar() or 0.0)

    async def _batch_load_consent_statuses(self, merchant_id: int) -> dict[str, ConsentStatus]:
        """Batch load all consent statuses for merchant to avoid N+1 queries.

        Args:
            merchant_id: Merchant ID

        Returns:
            Dict mapping session_id to consent status
        """
        result = await self.db.execute(
            select(Consent).where(
                Consent.merchant_id == merchant_id,
                Consent.consent_type == ConsentType.CONVERSATION,
            )
        )
        consents = result.scalars().all()

        consent_map = {}
        for consent in consents:
            if consent.granted:
                status = ConsentStatus.OPTED_IN
            else:
                status = ConsentStatus.OPTED_OUT

            # Key by BOTH visitor_id AND session_id so lookups work from either
            if consent.visitor_id:
                consent_map[consent.visitor_id] = status
            if consent.session_id:
                consent_map[consent.session_id] = status

        return consent_map

    def _get_consent_from_map(
        self,
        consent_map: dict[str, ConsentStatus],
        session_id: str | None,
        visitor_id: str | None,
    ) -> ConsentStatus:
        """Get consent status from pre-loaded map using visitor_id-first pattern.

        Story 6-1: visitor_id is PRIMARY, session_id is FALLBACK.

        Args:
            consent_map: Pre-loaded consent map
            session_id: Session ID (fallback)
            visitor_id: Visitor ID (primary)

        Returns:
            Consent status (defaults to PENDING if not found)
        """
        # Try visitor_id first (Story 6-1 pattern)
        if visitor_id and visitor_id in consent_map:
            return consent_map[visitor_id]

        # Fallback to session_id
        if session_id and session_id in consent_map:
            return consent_map[session_id]

        # Default to PENDING if no consent record found
        return ConsentStatus.PENDING
