"""Merchant Data Export Service

Story 6-3: Merchant CSV Export

Complete merchant data export for GDPR/CCPA compliance.
Different from csv_export_service.py (Story 3.2):
- Story 3.2: Filtered conversation exports for dashboard UI
- Story 6-3: Complete merchant data export for data sovereignty
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from datetime import UTC, datetime

import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import APIError, ErrorCode
from app.models.consent import Consent, ConsentType
from app.models.conversation import Conversation
from app.models.data_export_audit_log import DataExportAuditLog
from app.models.handoff_alert import HandoffAlert
from app.models.llm_conversation_cost import LLMConversationCost
from app.models.merchant import Merchant
from app.models.message import Message
from app.models.order import Order
from app.schemas.consent import ConsentStatus
from app.services.privacy.data_tier_service import DataTier

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
            total_handoffs = await self._count_handoffs(merchant_id)
            total_orders = await self._count_orders(merchant_id)

            # Stream metadata section
            for chunk in self._generate_metadata_section(
                merchant_id,
                total_conversations,
                total_messages,
                total_cost,
                total_handoffs,
                total_orders,
            ):
                yield chunk

            # Generate sections (consent map loaded once for efficiency)
            consent_map = await self._batch_load_consent_statuses(merchant_id)
            message_count_map = await self._batch_load_message_counts(merchant_id)
            handoff_alerts_map = await self._batch_load_handoff_alerts(merchant_id)

            opted_out_count = 0
            # Stream conversations section
            async for chunk in self._generate_conversations_section(
                merchant_id, consent_map, message_count_map
            ):
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

            # Stream handoffs section
            async for chunk in self._generate_handoffs_section(
                merchant_id, consent_map, handoff_alerts_map
            ):
                yield chunk

            # Stream costs section
            async for chunk in self._generate_costs_section(merchant_id):
                yield chunk

            # Stream orders section
            async for chunk in self._generate_orders_section(merchant_id):
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
        total_handoffs: int,
        total_orders: int,
    ):
        """Generate CSV metadata header."""
        yield "# Merchant Data Export\n"
        yield f"# Export Date: {datetime.now(UTC).isoformat()}\n"
        yield f"# Merchant ID: {merchant_id}\n"
        yield f"# Total Conversations: {total_conversations}\n"
        yield f"# Total Messages: {total_messages}\n"
        yield f"# Total LLM Cost: ${total_cost:.2f}\n"
        yield f"# Total Handoffs: {total_handoffs}\n"
        yield f"# Total Orders: {total_orders}\n"
        yield "\n"

    async def _generate_conversations_section(
        self,
        merchant_id: int,
        consent_map: dict[str, ConsentStatus],
        message_count_map: dict[int, int],
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
                .where(Conversation.data_tier.in_([DataTier.VOLUNTARY, DataTier.OPERATIONAL]))
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
                        str(message_count_map.get(conv.id, 0)),
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
                .where(Message.data_tier.in_([DataTier.VOLUNTARY, DataTier.OPERATIONAL]))
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
                    content = "[Content redacted - no consent]"
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

    async def _generate_handoffs_section(
        self,
        merchant_id: int,
        consent_map: dict[str, ConsentStatus],
        handoff_alerts_map: dict[int, list[HandoffAlert]],
    ) -> AsyncGenerator[str, None]:
        """Generate handoffs section with all handoff alerts.

        Optimized for 1000+ records - uses pre-loaded alerts_map.
        One row per HandoffAlert. If conversation has handoff but no alert,
        shows single row with "[No alert]" placeholders.

        Args:
            merchant_id: Merchant ID
            consent_map: Pre-loaded consent map for preview filtering
            handoff_alerts_map: Pre-loaded alerts grouped by conversation_id

        Yields:
            CSV rows for handoff section
        """
        yield "\n## SECTION: HANDOFFS\n"
        yield "conversation_id,handoff_status,handoff_reason,triggered_at,resolved_at,resolution_type,reopened_count,alert_id,urgency_level,wait_time_seconds,is_offline,is_read,conversation_preview\n"

        # Get all conversations with handoff data
        result = await self.db.execute(
            select(Conversation)
            .where(
                Conversation.merchant_id == merchant_id,
                Conversation.handoff_status != "none",
            )
            .order_by(Conversation.handoff_triggered_at.desc())
        )
        conversations = result.scalars().all()

        for conv in conversations:
            # Get pre-loaded alerts for this conversation
            alerts = handoff_alerts_map.get(conv.id, [])

            # Get consent status for preview filtering
            visitor_id = getattr(conv, "visitor_id", None)
            consent_status = self._get_consent_from_map(
                consent_map, conv.platform_sender_id, visitor_id
            )

            if not alerts:
                # No alerts: show single row with placeholders
                row = self._sanitize_csv_row(
                    [
                        str(conv.id),
                        conv.handoff_status or "",
                        conv.handoff_reason or "",
                        conv.handoff_triggered_at.isoformat() if conv.handoff_triggered_at else "",
                        conv.handoff_resolved_at.isoformat() if conv.handoff_resolved_at else "",
                        conv.handoff_resolution_type or "",
                        str(conv.handoff_reopened_count or 0),
                        "[No alert]",  # alert_id placeholder
                        "[No alert]",  # urgency_level placeholder
                        "[No alert]",  # wait_time_seconds placeholder
                        "[No alert]",  # is_offline placeholder
                        "[No alert]",  # is_read placeholder
                        "[No alert]",  # conversation_preview placeholder
                    ]
                )
                yield ",".join(row) + "\n"
            else:
                # Show one row per alert
                for alert in alerts:
                    # Filter preview based on consent
                    if consent_status in [
                        ConsentStatus.OPTED_OUT,
                        ConsentStatus.PENDING,
                    ]:
                        preview = "[Preview redacted - no consent]"
                    else:
                        preview = alert.conversation_preview or ""

                    row = self._sanitize_csv_row(
                        [
                            str(conv.id),
                            conv.handoff_status or "",
                            conv.handoff_reason or "",
                            conv.handoff_triggered_at.isoformat()
                            if conv.handoff_triggered_at
                            else "",
                            conv.handoff_resolved_at.isoformat()
                            if conv.handoff_resolved_at
                            else "",
                            conv.handoff_resolution_type or "",
                            str(conv.handoff_reopened_count or 0),
                            str(alert.id),
                            alert.urgency_level or "",
                            str(alert.wait_time_seconds or 0),
                            (
                                str(alert.is_offline).lower()
                                if alert.is_offline is not None
                                else "false"
                            ),
                            (str(alert.is_read).lower() if alert.is_read is not None else "false"),
                            preview,
                        ]
                    )
                    yield ",".join(row) + "\n"

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

    async def _generate_orders_section(
        self,
        merchant_id: int,
    ) -> AsyncGenerator[str, None]:
        """Generate orders section (filtered by data tier)."""
        yield "\n## SECTION: ORDERS\n"
        yield "order_id,order_number,customer_id,status,subtotal,total,currency,created_at\n"

        offset = 0
        chunk_size = 1000

        while True:
            result = await self.db.execute(
                select(Order)
                .where(Order.merchant_id == merchant_id)
                .where(Order.data_tier.in_([DataTier.VOLUNTARY, DataTier.OPERATIONAL]))
                .order_by(Order.created_at)
                .offset(offset)
                .limit(chunk_size)
            )
            orders = result.scalars().all()

            if not orders:
                break

            for order in orders:
                row = self._sanitize_csv_row(
                    [
                        str(order.id),
                        order.order_number or "",
                        order.platform_sender_id or "",
                        order.status or "",
                        f"{order.subtotal:.2f}" if order.subtotal else "0.00",
                        f"{order.total:.2f}" if order.total else "0.00",
                        order.currency_code or "USD",
                        order.created_at.isoformat() if order.created_at else "",
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
        """Count total conversations for merchant (filtered by data tier).

        Args:
            merchant_id: Merchant ID

        Returns:
            Total conversation count (VOLUNTARY + OPERATIONAL only)
        """
        from sqlalchemy import func

        result = await self.db.execute(
            select(func.count(Conversation.id))
            .where(Conversation.merchant_id == merchant_id)
            .where(Conversation.data_tier.in_([DataTier.VOLUNTARY, DataTier.OPERATIONAL]))
        )
        return result.scalar() or 0

    async def _count_messages(self, merchant_id: int) -> int:
        """Count total messages for merchant (filtered by data tier).

        Args:
            merchant_id: Merchant ID

        Returns:
            Total message count (VOLUNTARY + OPERATIONAL only)
        """
        from sqlalchemy import func

        result = await self.db.execute(
            select(func.count(Message.id))
            .join(Conversation, Message.conversation_id == Conversation.id)
            .where(Conversation.merchant_id == merchant_id)
            .where(Message.data_tier.in_([DataTier.VOLUNTARY, DataTier.OPERATIONAL]))
        )
        return result.scalar() or 0

    async def _count_handoffs(self, merchant_id: int) -> int:
        """Count conversations with handoff data.

        Args:
            merchant_id: Merchant ID

        Returns:
            Number of conversations with handoff_status != 'none'
        """
        result = await self.db.execute(
            select(func.count(Conversation.id)).where(
                Conversation.merchant_id == merchant_id,
                Conversation.handoff_status != "none",
            )
        )
        return result.scalar() or 0

    async def _count_orders(self, merchant_id: int) -> int:
        """Count orders for merchant (filtered by data tier).

        Args:
            merchant_id: Merchant ID

        Returns:
            Total order count (VOLUNTARY + OPERATIONAL only)
        """
        result = await self.db.execute(
            select(func.count(Order.id))
            .where(Order.merchant_id == merchant_id)
            .where(Order.data_tier.in_([DataTier.VOLUNTARY, DataTier.OPERATIONAL]))
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

    async def _batch_load_message_counts(self, merchant_id: int) -> dict[int, int]:
        """Batch load message counts to avoid N+1 queries.

        Args:
            merchant_id: Merchant ID

        Returns:
            Dict mapping conversation_id to message count
        """
        result = await self.db.execute(
            select(
                Message.conversation_id,
                func.count(Message.id).label("count"),
            )
            .select_from(Message)
            .join(Conversation, Message.conversation_id == Conversation.id)
            .where(Conversation.merchant_id == merchant_id)
            .group_by(Message.conversation_id)
        )
        message_counts: dict[int, int] = {}
        for row in result.all():
            message_counts[int(row[0])] = int(row[1])  # type: ignore
        return message_counts

    async def _batch_load_handoff_alerts(self, merchant_id: int) -> dict[int, list[HandoffAlert]]:
        """Batch load handoff alerts to avoid N+1 queries.

        Optimized for 1000+ records - single query for all alerts.

        Args:
            merchant_id: Merchant ID

        Returns:
            Dict mapping conversation_id to list of HandoffAlert objects
        """
        result = await self.db.execute(
            select(HandoffAlert)
            .join(Conversation, HandoffAlert.conversation_id == Conversation.id)
            .where(Conversation.merchant_id == merchant_id)
            .order_by(HandoffAlert.created_at.desc())
        )
        alerts = result.scalars().all()

        # Group alerts by conversation_id
        alerts_map: dict[int, list[HandoffAlert]] = {}
        for alert in alerts:
            conv_id = alert.conversation_id
            if conv_id not in alerts_map:
                alerts_map[conv_id] = []
            alerts_map[conv_id].append(alert)

        return alerts_map

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
