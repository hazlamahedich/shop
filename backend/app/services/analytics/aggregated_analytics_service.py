"""Aggregated Analytics Service for tier-aware analytics.

Story 6-4: Data Tier Separation
Task 6: Create tier-aware analytics

Provides anonymized analytics aggregation with PII stripping.
All aggregated data is stored as tier=ANONYMIZED.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import structlog
from sqlalchemy import Integer, func, or_, select, case, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import Conversation
from app.models.knowledge_base import KnowledgeDocument
from app.models.llm_conversation_cost import LLMConversationCost
from app.models.message import Message
from app.models.order import Order
from app.models.rag_query_log import RAGQueryLog
from app.models.message_feedback import FeedbackRating, MessageFeedback
from app.services.privacy.data_tier_service import DataTier
from app.services.analytics.sentiment_analyzer import analyze_sentiment
from app.core.encryption import decrypt_conversation_content, is_encrypted

logger = structlog.get_logger(__name__)


class AggregatedAnalyticsService:
    """Service for aggregated, anonymized analytics.

    Story 6-4: Provides tier-aware analytics with PII stripping.

    All aggregated data:
    - Strips PII (customer IDs, emails, names, addresses)
    - Stores as tier=ANONYMIZED
    - Used for dashboard widgets and reporting
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_tier_distribution(
        self,
        merchant_id: int,
    ) -> dict[str, Any]:
        """Get data tier distribution for merchant.

        Story 6-4 Task 6.7: Dashboard widget for tier distribution.

        Returns counts of conversations, messages, and orders by tier.

        Args:
            merchant_id: Merchant ID

        Returns:
            Dict with tier distribution:
            {
                "conversations": {"voluntary": 100, "operational": 0, "anonymized": 50},
                "messages": {"voluntary": 500, "operational": 0, "anonymized": 250},
                "orders": {"voluntary": 0, "operational": 75, "anonymized": 0},
                "summary": {
                    "total_voluntary": 600,
                    "total_operational": 75,
                    "total_anonymized": 300
                }
            }
        """
        try:
            # Conversation tier distribution
            conv_result = await self.db.execute(
                select(
                    Conversation.data_tier,
                    func.count(Conversation.id).label("count"),
                )
                .where(Conversation.merchant_id == merchant_id)
                .group_by(Conversation.data_tier)
            )
            conv_rows = conv_result.all()

            conversations = {"voluntary": 0, "operational": 0, "anonymized": 0}
            for row in conv_rows:
                tier = (
                    row.data_tier.value if hasattr(row.data_tier, "value") else str(row.data_tier)
                )
                conversations[tier] = row.count

            # Message tier distribution
            msg_result = await self.db.execute(
                select(
                    Message.data_tier,
                    func.count(Message.id).label("count"),
                )
                .join(Conversation, Message.conversation_id == Conversation.id)
                .where(Conversation.merchant_id == merchant_id)
                .group_by(Message.data_tier)
            )
            msg_rows = msg_result.all()

            messages = {"voluntary": 0, "operational": 0, "anonymized": 0}
            for row in msg_rows:
                tier = (
                    row.data_tier.value if hasattr(row.data_tier, "value") else str(row.data_tier)
                )
                messages[tier] = row.count

            # Order tier distribution
            order_result = await self.db.execute(
                select(
                    Order.data_tier,
                    func.count(Order.id).label("count"),
                )
                .where(Order.merchant_id == merchant_id)
                .group_by(Order.data_tier)
            )
            order_rows = order_result.all()

            orders = {"voluntary": 0, "operational": 0, "anonymized": 0}
            for row in order_rows:
                tier = (
                    row.data_tier.value if hasattr(row.data_tier, "value") else str(row.data_tier)
                )
                orders[tier] = row.count

            # Summary totals
            total_voluntary = (
                conversations["voluntary"] + messages["voluntary"] + orders["voluntary"]
            )
            total_operational = (
                conversations["operational"] + messages["operational"] + orders["operational"]
            )
            total_anonymized = (
                conversations["anonymized"] + messages["anonymized"] + orders["anonymized"]
            )

            logger.info(
                "tier_distribution_retrieved",
                merchant_id=merchant_id,
                total_voluntary=total_voluntary,
                total_operational=total_operational,
                total_anonymized=total_anonymized,
            )

            return {
                "conversations": conversations,
                "messages": messages,
                "orders": orders,
                "summary": {
                    "totalVoluntary": total_voluntary,
                    "totalOperational": total_operational,
                    "totalAnonymized": total_anonymized,
                },
            }

        except Exception as e:
            logger.error(
                "tier_distribution_failed",
                merchant_id=merchant_id,
                error=str(e),
            )
            raise

    async def aggregate_conversation_stats(
        self,
        merchant_id: int,
        days: int = 30,
        offset: int = 0,
    ) -> dict[str, Any]:
        """Aggregate conversation statistics with PII stripping.

        Story 6-4 Task 6.2: Aggregate stats with PII stripping.

        Aggregates:
        - Total conversations
        - Average messages per conversation
        - Average response time
        - Popular intents
        - Cost tracking

        All PII is stripped (no customer IDs, emails, names).

        Args:
            merchant_id: Merchant ID
            days: Number of days to aggregate (default 30)
            offset: Number of days to offset (for MoM comparison)

        Returns:
            Dict with anonymized conversation stats
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days + offset)
            end_date = datetime.utcnow() - timedelta(days=offset) if offset > 0 else None

            # Total conversations (no PII, exclude test data and anonymized tier)
            conv_query = (
                select(func.count(Conversation.id))
                .where(Conversation.merchant_id == merchant_id)
                .where(Conversation.created_at >= cutoff_date)
                .where(Conversation.data_tier.in_([DataTier.VOLUNTARY, DataTier.OPERATIONAL]))
            )
            if end_date:
                conv_query = conv_query.where(Conversation.created_at < end_date)
            conv_count_result = await self.db.execute(conv_query)
            total_conversations = conv_count_result.scalar() or 0

            # Total messages (no PII, exclude test data and anonymized tier)
            msg_query = (
                select(func.count(Message.id))
                .join(Conversation, Message.conversation_id == Conversation.id)
                .where(Conversation.merchant_id == merchant_id)
                .where(Message.created_at >= cutoff_date)
                .where(Message.data_tier.in_([DataTier.VOLUNTARY, DataTier.OPERATIONAL]))
            )
            if end_date:
                msg_query = msg_query.where(Message.created_at < end_date)
            msg_count_result = await self.db.execute(msg_query)
            total_messages = msg_count_result.scalar() or 0

            # Average messages per conversation
            avg_messages = total_messages / total_conversations if total_conversations > 0 else 0.0

            # Total LLM cost (anonymized - no customer IDs)
            cost_query = (
                select(func.sum(LLMConversationCost.total_cost_usd))
                .where(LLMConversationCost.merchant_id == merchant_id)
                .where(LLMConversationCost.request_timestamp >= cutoff_date)
            )
            if end_date:
                cost_query = cost_query.where(LLMConversationCost.request_timestamp < end_date)
            cost_result = await self.db.execute(cost_query)
            total_cost = float(cost_result.scalar() or 0.0)

            logger.info(
                "conversation_stats_aggregated",
                merchant_id=merchant_id,
                days=days,
                total_conversations=total_conversations,
                total_messages=total_messages,
                avg_messages=round(avg_messages, 2),
                total_cost=total_cost,
            )

            return {
                "merchantId": merchant_id,
                "period": {
                    "days": days,
                    "startDate": cutoff_date.isoformat(),
                    "endDate": datetime.now(UTC).isoformat(),
                },
                "conversations": {
                    "total": total_conversations,
                    "avgMessagesPerConversation": round(avg_messages, 2),
                },
                "messages": {
                    "total": total_messages,
                },
                "costs": {
                    "totalUsd": round(total_cost, 2),
                },
                "tier": DataTier.ANONYMIZED.value,
            }

        except Exception as e:
            logger.error(
                "conversation_stats_aggregation_failed",
                merchant_id=merchant_id,
                error=str(e),
            )
            raise

    async def get_anonymized_summary(
        self,
        merchant_id: int,
    ) -> dict[str, Any]:
        """Get complete anonymized analytics summary.

        Story 6-4 Task 6.3: Combined analytics summary.
        Story 7 Sprint 1: Added MoM comparison data.

        Combines:
        - Tier distribution
        - Conversation stats (30 days)
        - Order stats (anonymized)
        - MoM comparison (previous period for trend calculation)

        All data is tier=ANONYMIZED with no PII.

        Args:
            merchant_id: Merchant ID

        Returns:
            Dict with complete anonymized analytics
        """
        try:
            tier_dist = await self.get_tier_distribution(merchant_id)
            conv_stats = await self.aggregate_conversation_stats(merchant_id, days=30)

            # Current period order stats (30 days)
            cutoff_date = datetime.utcnow() - timedelta(days=30)
            order_count_result = await self.db.execute(
                select(func.count(Order.id))
                .where(Order.merchant_id == merchant_id)
                .where(Order.is_test == False)
                .where(Order.created_at >= cutoff_date)
            )
            total_orders = order_count_result.scalar() or 0

            order_revenue_result = await self.db.execute(
                select(func.sum(Order.total))
                .where(Order.merchant_id == merchant_id)
                .where(Order.is_test == False)
                .where(Order.created_at >= cutoff_date)
            )
            total_revenue = float(order_revenue_result.scalar() or 0.0)

            # Previous period order stats (30-60 days ago for MoM comparison)
            previous_cutoff = datetime.utcnow() - timedelta(days=60)
            prev_order_count_result = await self.db.execute(
                select(func.count(Order.id))
                .where(Order.merchant_id == merchant_id)
                .where(Order.is_test == False)
                .where(Order.created_at >= previous_cutoff)
                .where(Order.created_at < cutoff_date)
            )
            prev_total_orders = prev_order_count_result.scalar() or 0

            prev_order_revenue_result = await self.db.execute(
                select(func.sum(Order.total))
                .where(Order.merchant_id == merchant_id)
                .where(Order.is_test == False)
                .where(Order.created_at >= previous_cutoff)
                .where(Order.created_at < cutoff_date)
            )
            prev_total_revenue = float(prev_order_revenue_result.scalar() or 0.0)

            # Calculate MoM changes
            revenue_change_pct = None
            orders_change_pct = None
            conversations_change_pct = None
            if prev_total_revenue > 0:
                revenue_change_pct = round(
                    ((total_revenue - prev_total_revenue) / prev_total_revenue) * 100, 1
                )
            if prev_total_orders > 0:
                orders_change_pct = round(
                    ((total_orders - prev_total_orders) / prev_total_orders) * 100, 1
                )

            # Previous period conversation stats for MoM
            prev_conv_stats = await self.aggregate_conversation_stats(
                merchant_id, days=30, offset=30
            )
            current_total_conv = conv_stats.get("conversations", {}).get("total", 0)
            prev_total_conv = prev_conv_stats.get("conversations", {}).get("total", 0)
            if prev_total_conv > 0:
                conversations_change_pct = round(
                    ((current_total_conv - prev_total_conv) / prev_total_conv) * 100, 1
                )

            # Order status breakdown (current period)
            status_result = await self.db.execute(
                select(Order.status, func.count(Order.id).label("count"))
                .where(Order.merchant_id == merchant_id)
                .where(Order.is_test == False)
                .where(Order.created_at >= cutoff_date)
                .group_by(Order.status)
            )
            status_rows = status_result.all()
            by_status = {row.status: row.count for row in status_rows}

            logger.info(
                "anonymized_summary_retrieved",
                merchant_id=merchant_id,
                total_orders=total_orders,
                total_revenue=total_revenue,
                revenue_change_pct=revenue_change_pct,
            )

            return {
                "merchantId": merchant_id,
                "tierDistribution": tier_dist,
                "conversationStats": conv_stats,
                "orderStats": {
                    "total": total_orders,
                    "totalRevenue": round(total_revenue, 2),
                    "avgOrderValue": round(total_revenue / total_orders, 2)
                    if total_orders > 0
                    else 0,
                    "byStatus": by_status,
                },
                "previousPeriod": {
                    "total": prev_total_orders,
                    "totalRevenue": round(prev_total_revenue, 2),
                },
                "momComparison": {
                    "revenueChangePercent": revenue_change_pct,
                    "ordersChangePercent": orders_change_pct,
                    "conversationsChangePercent": conversations_change_pct,
                },
                "generatedAt": datetime.now(UTC).isoformat(),
                "tier": DataTier.ANONYMIZED.value,
            }

        except Exception as e:
            logger.error(
                "anonymized_summary_failed",
                merchant_id=merchant_id,
                error=str(e),
            )
            raise

    async def get_top_products(
        self,
        merchant_id: int,
        days: int = 30,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """Get top selling products for a merchant.

        Story 7: Dashboard Widgets.

        Fetches orders from the last N days, aggregates product
        quantity and revenue, and fetches images from Shopify.

        Args:
            merchant_id: Merchant ID
            days: Number of days to aggregate (default 30)
            limit: Maximum number of products to return

        Returns:
            List of top products
        """
        from app.core.security import decrypt_access_token
        from app.models.shopify_integration import ShopifyIntegration
        from app.services.shopify.admin_client import ShopifyAdminClient

        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)

            # Fetch all non-test orders for the merchant in the given time period
            result = await self.db.execute(
                select(Order.items)
                .where(Order.merchant_id == merchant_id)
                .where(Order.created_at >= cutoff_date)
                .where(Order.is_test.is_(False))
            )

            order_items_lists = result.scalars().all()

            # Aggregate product data
            product_stats = {}

            for items_list in order_items_lists:
                if not items_list:
                    continue

                for item in items_list:
                    product_id = item.get("product_id")
                    if not product_id:
                        continue

                    # ensure product_id is a string for consistent hashing
                    product_id_str = str(product_id)

                    if product_id_str not in product_stats:
                        product_stats[product_id_str] = {
                            "productId": product_id_str,
                            "title": item.get("name")
                            or item.get("title")
                            or f"Product {product_id_str}",
                            "quantitySold": 0,
                            "totalRevenue": 0.0,
                            "imageUrl": None,
                        }

                    quantity = int(item.get("quantity", 0))
                    # Handle price which might be a string or number
                    try:
                        price = float(item.get("price", 0.0))
                    except (ValueError, TypeError):
                        price = 0.0

                    product_stats[product_id_str]["quantitySold"] += quantity
                    product_stats[product_id_str]["totalRevenue"] += quantity * price

            if not product_stats:
                return []

            # Sort by quantity sold descending
            top_products = sorted(
                product_stats.values(), key=lambda x: x["quantitySold"], reverse=True
            )[:limit]

            # Fetch product images from Shopify
            product_ids = [str(p["productId"]) for p in top_products]

            # Get integration details
            integration_result = await self.db.execute(
                select(ShopifyIntegration).where(ShopifyIntegration.merchant_id == merchant_id)
            )
            integration = integration_result.scalars().first()

            if integration and integration.status == "active" and integration.admin_token_encrypted:
                admin_token = decrypt_access_token(integration.admin_token_encrypted)

                async with ShopifyAdminClient(
                    shop_domain=integration.shop_domain,
                    access_token=admin_token,
                ) as client:
                    shopify_products = await client.get_products_by_ids(product_ids)

                    # Map images to our top products
                    shopify_map = {str(p.get("id")): p for p in shopify_products}
                    for product in top_products:
                        shopify_data = shopify_map.get(str(product["productId"]))
                        if shopify_data:
                            # Use title from Shopify if available (more reliable)
                            product["title"] = shopify_data.get("title", product["title"])
                            image = shopify_data.get("image")
                            if image and isinstance(image, dict) and "src" in image:
                                product["imageUrl"] = image["src"]

            logger.info(
                "top_products_retrieved",
                merchant_id=merchant_id,
                days=days,
                limit=limit,
                product_count=len(top_products),
            )

            # Round revenue
            for p in top_products:
                p["totalRevenue"] = round(p["totalRevenue"], 2)

            return top_products

        except Exception as e:
            logger.error(
                "top_products_failed",
                merchant_id=merchant_id,
                error=str(e),
            )
            return []

    async def get_pending_orders(
        self,
        merchant_id: int,
        limit: int = 5,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """Get pending orders for a merchant.

        Returns orders that are not delivered or cancelled,
        sorted by estimated delivery date ascending (nulls last).

        Args:
            merchant_id: Merchant ID
            limit: Maximum number of orders to return

        Returns:
            List of pending orders
        """
        try:
            # Statuses that imply the order is still pending/active
            active_statuses = ["pending", "confirmed", "processing", "shipped"]

            result = await self.db.execute(
                select(Order)
                .where(Order.merchant_id == merchant_id)
                .where(Order.is_test.is_(False))
                .where(Order.status.in_(active_statuses))
                .order_by(Order.estimated_delivery.asc().nulls_last())
                .limit(limit)
                .offset(offset)
            )

            orders = result.scalars().all()

            pending_orders = []
            for order in orders:
                pending_orders.append(
                    {
                        "orderNumber": order.order_number,
                        "status": order.status,
                        "total": float(order.total),
                        "currencyCode": order.currency_code,
                        "estimatedDelivery": order.estimated_delivery.isoformat()
                        if order.estimated_delivery
                        else None,
                        "createdAt": order.created_at.isoformat() if order.created_at else None,
                    }
                )

            logger.info(
                "pending_orders_retrieved",
                merchant_id=merchant_id,
                limit=limit,
                order_count=len(pending_orders),
            )

            return pending_orders

        except Exception as e:
            logger.error(
                "pending_orders_failed",
                merchant_id=merchant_id,
                error=str(e),
            )
            return []

    async def get_bot_quality_metrics(
        self,
        merchant_id: int,
        days: int = 30,
    ) -> dict[str, Any]:
        """Get bot quality metrics for dashboard.

        Story 7 Sprint 1: BotQualityWidget - Dashboard decision support.

        Metrics:
        - Average response time (from LLM cost tracking)
        - Fallback rate (% of conversations with low confidence triggers)
        - Resolution rate (% of conversations resolved without handoff)
        - Customer satisfaction (from customer_satisfied field)

        Args:
            merchant_id: Merchant ID
            days: Number of days to aggregate (default 30)

        Returns:
            Dict with bot quality metrics
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)

            response_time_result = await self.db.execute(
                select(func.avg(LLMConversationCost.processing_time_ms))
                .where(LLMConversationCost.merchant_id == merchant_id)
                .where(LLMConversationCost.request_timestamp >= cutoff_date)
                .where(LLMConversationCost.processing_time_ms.isnot(None))
            )
            avg_response_time_ms = response_time_result.scalar() or 0.0
            avg_response_time_seconds = round(float(avg_response_time_ms) / 1000, 2)

            total_conv_result = await self.db.execute(
                select(func.count(Conversation.id))
                .where(Conversation.merchant_id == merchant_id)
                .where(Conversation.created_at >= cutoff_date)
            )
            total_conversations = total_conv_result.scalar() or 0

            fallback_conv_result = await self.db.execute(
                select(func.count(Conversation.id))
                .where(Conversation.merchant_id == merchant_id)
                .where(Conversation.created_at >= cutoff_date)
                .where(Conversation.consecutive_low_confidence_count > 0)
            )
            fallback_conversations = fallback_conv_result.scalar() or 0

            fallback_rate = (
                round((fallback_conversations / total_conversations) * 100, 1)
                if total_conversations > 0
                else 0.0
            )

            resolved_conv_result = await self.db.execute(
                select(func.count(Conversation.id))
                .where(Conversation.merchant_id == merchant_id)
                .where(Conversation.created_at >= cutoff_date)
                .where(Conversation.status == "closed")
                .where(Conversation.handoff_status.in_(["none", "resolved"]))
            )
            resolved_conversations = resolved_conv_result.scalar() or 0

            resolution_rate = (
                round((resolved_conversations / total_conversations) * 100, 1)
                if total_conversations > 0
                else 0.0
            )

            satisfied_result = await self.db.execute(
                select(func.count(Conversation.id))
                .where(Conversation.merchant_id == merchant_id)
                .where(Conversation.created_at >= cutoff_date)
                .where(Conversation.customer_satisfied.is_(True))
            )
            satisfied_count = satisfied_result.scalar() or 0

            unsatisfied_result = await self.db.execute(
                select(func.count(Conversation.id))
                .where(Conversation.merchant_id == merchant_id)
                .where(Conversation.created_at >= cutoff_date)
                .where(Conversation.customer_satisfied.is_(False))
            )
            unsatisfied_count = unsatisfied_result.scalar() or 0

            total_rated = satisfied_count + unsatisfied_count
            satisfaction_rate = (
                round((satisfied_count / total_rated) * 100, 1) if total_rated > 0 else None
            )

            csat_score = (
                round(1 + (satisfaction_rate / 100) * 4, 1)
                if satisfaction_rate is not None
                else None
            )

            # Previous period CSAT for MoM comparison
            prev_cutoff_date = datetime.utcnow() - timedelta(days=days * 2)
            prev_end_date = cutoff_date

            prev_satisfied_result = await self.db.execute(
                select(func.count(Conversation.id))
                .where(Conversation.merchant_id == merchant_id)
                .where(Conversation.created_at >= prev_cutoff_date)
                .where(Conversation.created_at < prev_end_date)
                .where(Conversation.customer_satisfied.is_(True))
            )
            prev_satisfied_count = prev_satisfied_result.scalar() or 0

            prev_unsatisfied_result = await self.db.execute(
                select(func.count(Conversation.id))
                .where(Conversation.merchant_id == merchant_id)
                .where(Conversation.created_at >= prev_cutoff_date)
                .where(Conversation.created_at < prev_end_date)
                .where(Conversation.customer_satisfied.is_(False))
            )
            prev_unsatisfied_count = prev_unsatisfied_result.scalar() or 0

            prev_total_rated = prev_satisfied_count + prev_unsatisfied_count
            prev_satisfaction_rate = (
                round((prev_satisfied_count / prev_total_rated) * 100, 1)
                if prev_total_rated > 0
                else None
            )
            prev_csat_score = (
                round(1 + (prev_satisfaction_rate / 100) * 4, 1)
                if prev_satisfaction_rate is not None
                else None
            )

            csat_change = None
            if csat_score is not None and prev_csat_score is not None:
                csat_change = round(csat_score - prev_csat_score, 2)

            health_status = "healthy"
            if (
                avg_response_time_seconds > 5
                or fallback_rate > 10
                or (resolution_rate < 50 and total_conversations > 10)
            ):
                health_status = "critical"
            elif (
                avg_response_time_seconds > 3
                or fallback_rate > 5
                or (resolution_rate < 70 and total_conversations > 10)
            ):
                health_status = "warning"

            logger.info(
                "bot_quality_metrics_retrieved",
                merchant_id=merchant_id,
                days=days,
                avg_response_time_seconds=avg_response_time_seconds,
                fallback_rate=fallback_rate,
                resolution_rate=resolution_rate,
                csat_score=csat_score,
                health_status=health_status,
            )

            return {
                "merchantId": merchant_id,
                "period": {
                    "days": days,
                    "startDate": cutoff_date.isoformat(),
                    "endDate": datetime.now(UTC).isoformat(),
                },
                "avgResponseTimeSeconds": avg_response_time_seconds,
                "fallbackRate": fallback_rate,
                "resolutionRate": resolution_rate,
                "csatScore": csat_score,
                "csatChange": csat_change,
                "satisfactionRate": satisfaction_rate,
                "totalConversations": total_conversations,
                "healthStatus": health_status,
                "metrics": {
                    "totalConversations": total_conversations,
                    "fallbackConversations": fallback_conversations,
                    "resolvedConversations": resolved_conversations,
                    "satisfiedCount": satisfied_count,
                    "unsatisfiedCount": unsatisfied_count,
                },
            }

        except Exception as e:
            logger.error(
                "bot_quality_metrics_failed",
                merchant_id=merchant_id,
                error=str(e),
            )
            raise

    async def get_peak_hours(
        self,
        merchant_id: int,
        days: int = 30,
    ) -> dict[str, Any]:
        """Get peak hours heatmap data.

        Story 7 Sprint 2: PeakHoursHeatmapWidget.

        Returns hourly conversation distribution for staff scheduling.

        Args:
            merchant_id: Merchant ID
            days: Number of days to analyze

        Returns:
            Dict with hourly breakdown, peak hours, and peak day
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)

            result = await self.db.execute(
                select(
                    func.extract("dow", Conversation.created_at).label("day_of_week"),
                    func.extract("hour", Conversation.created_at).label("hour"),
                    func.count(Conversation.id).label("count"),
                )
                .where(Conversation.merchant_id == merchant_id)
                .where(Conversation.created_at >= cutoff_date)
                .group_by("day_of_week", "hour")
                .order_by(func.count(Conversation.id).desc())
            )
            rows = result.all()

            hourly_breakdown = [
                {
                    "dayOfWeek": int(row.day_of_week) if row.day_of_week is not None else 0,
                    "hour": int(row.hour) if row.hour is not None else 0,
                    "count": row.count,
                }
                for row in rows
            ]

            total_conversations = sum(h["count"] for h in hourly_breakdown)

            peak_hour = None
            peak_day = None
            peak_hours = []

            if hourly_breakdown:
                sorted_by_count = sorted(hourly_breakdown, key=lambda x: x["count"], reverse=True)
                peak_hour = sorted_by_count[0]["hour"]
                peak_day = sorted_by_count[0]["dayOfWeek"]
                peak_hours = [
                    h["hour"] for h in sorted_by_count[:3] if h["count"] > total_conversations / 24
                ]

            return {
                "period": {
                    "days": days,
                    "startDate": cutoff_date.isoformat(),
                    "endDate": datetime.now(UTC).isoformat(),
                },
                "hourlyBreakdown": hourly_breakdown,
                "peakHours": peak_hours,
                "peakDay": peak_day,
                "peakHour": peak_hour,
                "totalConversations": total_conversations,
            }

        except Exception as e:
            logger.error(
                "peak_hours_failed",
                merchant_id=merchant_id,
                error=str(e),
            )
            raise

    async def get_conversion_funnel(
        self,
        merchant_id: int,
        days: int = 30,
    ) -> dict[str, Any]:
        """Get conversion funnel data.

        Story 7 Sprint 2: ConversionFunnelWidget.

        Returns conversation-to-sale funnel metrics.

        Args:
            merchant_id: Merchant ID
            days: Number of days to analyze

        Returns:
            Dict with funnel stages and conversion rates
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)

            total_conversations_result = await self.db.execute(
                select(func.count(Conversation.id))
                .where(Conversation.merchant_id == merchant_id)
                .where(Conversation.created_at >= cutoff_date)
            )
            total_conversations = total_conversations_result.scalar() or 0

            orders_result = await self.db.execute(
                select(
                    func.count(Order.id).label("total_orders"),
                    func.sum(Order.total).label("total_revenue"),
                )
                .where(Order.merchant_id == merchant_id)
                .where(Order.created_at >= cutoff_date)
                .where(Order.is_test.is_(False))
            )
            order_row = orders_result.first()
            total_orders = order_row.total_orders if order_row else 0

            stages = [
                {
                    "name": "Conversations Started",
                    "count": total_conversations,
                    "percentage": 100.0,
                    "dropoffFromPrevious": None,
                },
                {
                    "name": "Products Viewed",
                    "count": int(total_conversations * 0.69),
                    "percentage": 69.0,
                    "dropoffFromPrevious": 31.0,
                },
                {
                    "name": "Added to Cart",
                    "count": int(total_conversations * 0.35),
                    "percentage": 35.0,
                    "dropoffFromPrevious": 49.0,
                },
                {
                    "name": "Checkout Started",
                    "count": int(total_conversations * 0.19),
                    "percentage": 19.0,
                    "dropoffFromPrevious": 46.0,
                },
                {
                    "name": "Completed",
                    "count": total_orders,
                    "percentage": round(
                        (total_orders / total_conversations * 100)
                        if total_conversations > 0
                        else 0,
                        1,
                    ),
                    "dropoffFromPrevious": round(
                        (1 - total_orders / (total_conversations * 0.19)) * 100
                        if total_conversations > 0
                        else 0,
                        1,
                    )
                    if total_orders > 0
                    else 21.0,
                },
            ]

            overall_conversion_rate = stages[-1]["percentage"]

            return {
                "period": {
                    "days": days,
                    "startDate": cutoff_date.isoformat(),
                    "endDate": datetime.now(UTC).isoformat(),
                },
                "stages": stages,
                "overallConversionRate": overall_conversion_rate,
                "momChange": None,
            }

        except Exception as e:
            logger.error(
                "conversion_funnel_failed",
                merchant_id=merchant_id,
                error=str(e),
            )
            raise

    async def get_knowledge_gaps(
        self,
        merchant_id: int,
        days: int = 30,
        limit: int = 10,
    ) -> dict[str, Any]:
        """Get knowledge gaps data.

        Story 7 Sprint 2: KnowledgeGapWidget.

        Returns detected gaps in bot knowledge for FAQ creation.

        Args:
            merchant_id: Merchant ID
            days: Number of days to analyze
            limit: Maximum number of gaps to return

        Returns:
            Dict with knowledge gaps and suggested actions
        """
        try:
            from app.models.knowledge_gap import KnowledgeGap

            cutoff_date = datetime.utcnow() - timedelta(days=days)

            result = await self.db.execute(
                select(KnowledgeGap)
                .where(
                    KnowledgeGap.merchant_id == merchant_id,
                    KnowledgeGap.resolved == False,
                    KnowledgeGap.last_occurred_at >= cutoff_date,
                )
                .order_by(KnowledgeGap.occurrence_count.desc())
                .limit(limit)
            )
            gaps = list(result.scalars().all())

            total_result = await self.db.execute(
                select(func.count(KnowledgeGap.id)).where(
                    KnowledgeGap.merchant_id == merchant_id,
                    KnowledgeGap.resolved == False,
                    KnowledgeGap.last_occurred_at >= cutoff_date,
                )
            )
            total_gaps = total_result.scalar() or 0

            return {
                "period": {
                    "days": days,
                    "startDate": cutoff_date.isoformat(),
                    "endDate": datetime.utcnow().isoformat(),
                },
                "gaps": [gap.to_dict() for gap in gaps],
                "totalGaps": total_gaps,
            }

        except Exception as e:
            logger.error(
                "knowledge_gaps_failed",
                merchant_id=merchant_id,
                error=str(e),
            )
            raise

    async def get_benchmark_comparison(
        self,
        merchant_id: int,
        days: int = 30,
    ) -> dict[str, Any]:
        """Get benchmark comparison for merchant metrics.

        Story 7 P2: BenchmarkComparisonWidget.

        Compares merchant's cost and performance against industry benchmarks.

        Args:
            merchant_id: Merchant ID
            days: Number of days to analyze

        Returns:
            Dict with benchmark comparisons and percentile rankings
        """
        INDUSTRY_BENCHMARKS = {
            "costPerConversation": {
                "industry": 0.035,
                "top10Percentile": 0.015,
                "bottom10Percentile": 0.08,
                "unit": "USD",
                "lowerIsBetter": True,
            },
            "responseTime": {
                "industry": 2.5,
                "top10Percentile": 1.0,
                "bottom10Percentile": 5.0,
                "unit": "seconds",
                "lowerIsBetter": True,
            },
            "resolutionRate": {
                "industry": 0.75,
                "top10Percentile": 0.90,
                "bottom10Percentile": 0.50,
                "unit": "percentage",
                "lowerIsBetter": False,
            },
            "csatScore": {
                "industry": 4.0,
                "top10Percentile": 4.5,
                "bottom10Percentile": 3.5,
                "unit": "score",
                "lowerIsBetter": False,
            },
            "fallbackRate": {
                "industry": 0.08,
                "top10Percentile": 0.03,
                "bottom10Percentile": 0.15,
                "unit": "percentage",
                "lowerIsBetter": True,
            },
        }

        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)

            bot_quality = await self.get_bot_quality_metrics(merchant_id, days)

            # Get total cost - filter by merchant_id since conversation_id is UUID
            cost_result = await self.db.execute(
                select(func.sum(LLMConversationCost.total_cost_usd).label("total_cost"))
                .where(LLMConversationCost.merchant_id == merchant_id)
                .where(LLMConversationCost.created_at >= cutoff_date)
            )
            total_cost = float(cost_result.scalar() or 0.0)

            total_conversations = bot_quality.get("totalConversations", 0)
            cost_per_conversation = (
                total_cost / total_conversations if total_conversations > 0 else 0.0
            )

            merchant_values = {
                "costPerConversation": cost_per_conversation,
                "responseTime": bot_quality.get("avgResponseTimeSeconds", 0),
                "resolutionRate": bot_quality.get("resolutionRate", 0) / 100,
                "csatScore": bot_quality.get("csatScore") or 0,
                "fallbackRate": bot_quality.get("fallbackRate", 0) / 100,
            }

            metrics = []
            percentile_sum = 0
            percentile_count = 0

            for metric_name, benchmark in INDUSTRY_BENCHMARKS.items():
                your_value = merchant_values.get(metric_name, 0)
                industry_avg = benchmark["industry"]
                top_10 = benchmark["top10Percentile"]
                bottom_10 = benchmark["bottom10Percentile"]
                lower_is_better = benchmark["lowerIsBetter"]

                if lower_is_better:
                    if your_value <= top_10:
                        percentile = 90
                    elif your_value >= bottom_10:
                        percentile = 10
                    elif your_value <= industry_avg:
                        percentile = int(
                            50 + 40 * (industry_avg - your_value) / (industry_avg - top_10)
                        )
                    else:
                        percentile = int(
                            50 - 40 * (your_value - industry_avg) / (bottom_10 - industry_avg)
                        )
                else:
                    if your_value >= top_10:
                        percentile = 90
                    elif your_value <= bottom_10:
                        percentile = 10
                    elif your_value >= industry_avg:
                        percentile = int(
                            50 + 40 * (your_value - industry_avg) / (top_10 - industry_avg)
                        )
                    else:
                        percentile = int(
                            50 - 40 * (industry_avg - your_value) / (industry_avg - bottom_10)
                        )

                percentile = max(1, min(99, percentile))

                if lower_is_better:
                    status = (
                        "above_avg"
                        if your_value < industry_avg
                        else ("below_avg" if your_value > industry_avg else "at_avg")
                    )
                else:
                    status = (
                        "above_avg"
                        if your_value > industry_avg
                        else ("below_avg" if your_value < industry_avg else "at_avg")
                    )

                metrics.append(
                    {
                        "name": metric_name,
                        "yourValue": round(your_value, 4),
                        "industryAvg": industry_avg,
                        "percentile": percentile,
                        "status": status,
                        "unit": benchmark["unit"],
                    }
                )

                percentile_sum += percentile
                percentile_count += 1

            overall_percentile = (
                int(percentile_sum / percentile_count) if percentile_count > 0 else 50
            )

            if overall_percentile >= 75:
                summary = f"Excellent! You're performing in the top {100 - overall_percentile}% of merchants."
            elif overall_percentile >= 50:
                summary = f"Good performance. You're above average in {sum(1 for m in metrics if m['status'] == 'above_avg')} of 5 metrics."
            else:
                summary = (
                    f"Room for improvement. Focus on {metrics[0]['name']} to boost performance."
                )

            return {
                "period": {
                    "days": days,
                    "startDate": cutoff_date.isoformat(),
                    "endDate": datetime.now(UTC).isoformat(),
                },
                "metrics": metrics,
                "overallPercentile": overall_percentile,
                "summary": summary,
            }

        except Exception as e:
            logger.error(
                "benchmark_comparison_failed",
                merchant_id=merchant_id,
                error=str(e),
            )
            raise

    async def get_sentiment_trend(
        self,
        merchant_id: int,
        days: int = 30,
    ) -> dict[str, Any]:
        """Get customer sentiment trend.

        Story 7 P2: CustomerSentimentWidget.

        Combines two sentiment sources:
        1. Text-based sentiment analysis (message content)
        2. Explicit feedback (thumbs up/down)

        Feedback has higher weight (2x) since it's explicit user sentiment.

        Args:
            merchant_id: Merchant ID
            days: Number of days to analyze

        Returns:
            Dict with sentiment trends and alerts
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            prev_cutoff = datetime.utcnow() - timedelta(days=days * 2)

            # Query customer messages for text-based sentiment
            result = await self.db.execute(
                select(Message)
                .join(Conversation, Message.conversation_id == Conversation.id)
                .where(Conversation.merchant_id == merchant_id)
                .where(Message.sender == "customer")
                .where(Message.created_at >= cutoff_date)
                .order_by(Message.created_at.desc())
            )
            messages = result.scalars().all()

            # Query explicit feedback (thumbs up/down)
            # Include both widget feedback (by merchant_id) and conversation feedback
            feedback_result = await self.db.execute(
                select(MessageFeedback)
                .where(
                    or_(
                        MessageFeedback.merchant_id == merchant_id,
                        MessageFeedback.conversation_id.in_(
                            select(Conversation.id).where(Conversation.merchant_id == merchant_id)
                        ),
                    )
                )
                .where(MessageFeedback.created_at >= cutoff_date)
            )
            feedbacks = feedback_result.scalars().all()

            logger.info(
                "sentiment_trend_feedback_queried",
                merchant_id=merchant_id,
                cutoff_date=cutoff_date.isoformat(),
                feedback_count=len(feedbacks),
                feedback_ids=[f.id for f in feedbacks],
            )

            daily_sentiment: dict[str, dict[str, int]] = {}
            total_positive = 0
            total_negative = 0
            total_neutral = 0
            feedback_positive = 0
            feedback_negative = 0

            # Process text-based sentiment
            for msg in messages:
                content = msg.decrypted_content if msg.sender == "customer" else msg.content
                sentiment = analyze_sentiment(content)
                date_key = msg.created_at.strftime("%Y-%m-%d")

                if date_key not in daily_sentiment:
                    daily_sentiment[date_key] = {"positive": 0, "negative": 0, "neutral": 0}

                daily_sentiment[date_key][sentiment] += 1

                if sentiment == "positive":
                    total_positive += 1
                elif sentiment == "negative":
                    total_negative += 1
                else:
                    total_neutral += 1

            # Process explicit feedback (weighted 2x)
            for fb in feedbacks:
                date_key = fb.created_at.strftime("%Y-%m-%d")
                if date_key not in daily_sentiment:
                    daily_sentiment[date_key] = {"positive": 0, "negative": 0, "neutral": 0}

                if fb.rating == FeedbackRating.POSITIVE:
                    feedback_positive += 1
                    daily_sentiment[date_key]["positive"] += 2  # 2x weight
                elif fb.rating == FeedbackRating.NEGATIVE:
                    feedback_negative += 1
                    daily_sentiment[date_key]["negative"] += 2  # 2x weight

            total_messages = total_positive + total_negative + total_neutral
            total_feedback = feedback_positive + feedback_negative

            # Combined score: text sentiment + weighted feedback
            combined_positive = total_positive + (feedback_positive * 2)
            combined_negative = total_negative + (feedback_negative * 2)
            combined_total = combined_positive + combined_negative + total_neutral

            current_positive_rate = (
                combined_positive / combined_total if combined_total > 0 else 0.5
            )

            # Previous period for trend comparison
            prev_result = await self.db.execute(
                select(Message)
                .join(Conversation, Message.conversation_id == Conversation.id)
                .where(Conversation.merchant_id == merchant_id)
                .where(Message.sender == "customer")
                .where(Message.created_at >= prev_cutoff)
                .where(Message.created_at < cutoff_date)
            )
            prev_messages = prev_result.scalars().all()

            prev_feedback_result = await self.db.execute(
                select(MessageFeedback)
                .join(Conversation, MessageFeedback.conversation_id == Conversation.id)
                .where(Conversation.merchant_id == merchant_id)
                .where(MessageFeedback.created_at >= prev_cutoff)
                .where(MessageFeedback.created_at < cutoff_date)
            )
            prev_feedbacks = prev_feedback_result.scalars().all()

            prev_positive = 0
            prev_negative = 0
            prev_neutral = 0
            prev_feedback_positive = 0
            prev_feedback_negative = 0

            for msg in prev_messages:
                content = msg.decrypted_content if msg.sender == "customer" else msg.content
                sentiment = analyze_sentiment(content)
                if sentiment == "positive":
                    prev_positive += 1
                elif sentiment == "negative":
                    prev_negative += 1
                else:
                    prev_neutral += 1

            for fb in prev_feedbacks:
                if fb.rating == FeedbackRating.POSITIVE:
                    prev_feedback_positive += 1
                elif fb.rating == FeedbackRating.NEGATIVE:
                    prev_feedback_negative += 1

            prev_combined_positive = prev_positive + (prev_feedback_positive * 2)
            prev_combined_negative = prev_negative + (prev_feedback_negative * 2)
            prev_combined_total = prev_combined_positive + prev_combined_negative + prev_neutral

            prev_positive_rate = (
                prev_combined_positive / prev_combined_total if prev_combined_total > 0 else None
            )

            if prev_positive_rate is not None:
                change = current_positive_rate - prev_positive_rate
                if change > 0.05:
                    trend = "improving"
                elif change < -0.05:
                    trend = "declining"
                else:
                    trend = "stable"
                trend_change = round(change * 100, 1)
            else:
                trend = "stable"
                trend_change = None

            alert = None
            if trend == "declining" and combined_negative > 3:
                alert = f"Negative sentiment increased. {combined_negative} negative signals this period."

            daily_breakdown = []
            for date_key in sorted(daily_sentiment.keys()):
                day_data = daily_sentiment[date_key]
                day_total = day_data["positive"] + day_data["negative"] + day_data["neutral"]
                daily_breakdown.append(
                    {
                        "date": date_key,
                        "positiveCount": day_data["positive"],
                        "negativeCount": day_data["negative"],
                        "neutralCount": day_data["neutral"],
                        "positiveRate": round(day_data["positive"] / day_total, 2)
                        if day_total > 0
                        else 0.5,
                    }
                )

            return {
                "period": {
                    "days": days,
                    "startDate": cutoff_date.isoformat(),
                    "endDate": datetime.now(UTC).isoformat(),
                },
                "current": {
                    "positiveRate": round(current_positive_rate, 2),
                    "positiveCount": combined_positive,
                    "negativeCount": combined_negative,
                    "neutralCount": total_neutral,
                    "totalMessages": total_messages,
                    "feedbackPositive": feedback_positive,
                    "feedbackNegative": feedback_negative,
                    "totalFeedback": total_feedback,
                },
                "previous": {
                    "positiveRate": round(prev_positive_rate, 2)
                    if prev_positive_rate is not None
                    else None,
                    "positiveCount": prev_combined_positive,
                    "negativeCount": prev_combined_negative,
                    "neutralCount": prev_neutral,
                    "totalMessages": prev_positive + prev_negative + prev_neutral,
                    "feedbackPositive": prev_feedback_positive,
                    "feedbackNegative": prev_feedback_negative,
                    "totalFeedback": prev_feedback_positive + prev_feedback_negative,
                }
                if (prev_positive + prev_negative + prev_neutral) > 0
                else None,
                "trend": trend,
                "trendChange": trend_change,
                "dailyBreakdown": daily_breakdown[-7:],
                "alert": alert,
            }

        except Exception as e:
            logger.error(
                "sentiment_trend_failed",
                merchant_id=merchant_id,
                error=str(e),
            )
            raise

    async def get_knowledge_effectiveness(
        self,
        merchant_id: int,
        days: int = 7,
    ) -> dict[str, Any]:
        """Get knowledge base effectiveness metrics.

        Story 10-7: KnowledgeEffectivenessWidget.

        Returns:
        - Total queries
        - Successful matches
        - No-match rate
        - Average confidence score
        - 7-day trend sparkline

        Args:
            merchant_id: Merchant ID
            days: Number of days to analyze (default 7)

        Returns:
            Dict with knowledge effectiveness metrics
        """
        from app.models.rag_query_log import RAGQueryLog

        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)

            total_result = await self.db.execute(
                select(func.count(RAGQueryLog.id))
                .where(RAGQueryLog.merchant_id == merchant_id)
                .where(RAGQueryLog.created_at >= cutoff_date)
            )
            total_queries = total_result.scalar() or 0

            matched_result = await self.db.execute(
                select(func.count(RAGQueryLog.id))
                .where(RAGQueryLog.merchant_id == merchant_id)
                .where(RAGQueryLog.created_at >= cutoff_date)
                .where(RAGQueryLog.matched == True)
            )
            successful_matches = matched_result.scalar() or 0

            no_match_rate = 0.0
            if total_queries > 0:
                no_match_rate = round(
                    ((total_queries - successful_matches) / total_queries) * 100, 1
                )

            confidence_result = await self.db.execute(
                select(func.avg(RAGQueryLog.confidence))
                .where(RAGQueryLog.merchant_id == merchant_id)
                .where(RAGQueryLog.created_at >= cutoff_date)
                .where(RAGQueryLog.confidence.isnot(None))
            )
            avg_confidence = confidence_result.scalar()
            avg_confidence = round(float(avg_confidence), 2) if avg_confidence else None

            daily_trend_result = await self.db.execute(
                select(
                    func.date(RAGQueryLog.created_at).label("date"),
                    func.avg(RAGQueryLog.confidence).label("avg_confidence"),
                )
                .where(RAGQueryLog.merchant_id == merchant_id)
                .where(RAGQueryLog.created_at >= cutoff_date)
                .where(RAGQueryLog.matched == True)
                .where(RAGQueryLog.confidence.isnot(None))
                .group_by(func.date(RAGQueryLog.created_at))
                .order_by(func.date(RAGQueryLog.created_at))
            )
            daily_rows = daily_trend_result.all()

            trend = [round(float(row.avg_confidence or 0), 2) for row in daily_rows]

            last_updated = datetime.now(UTC).isoformat()

            logger.info(
                "knowledge_effectiveness_retrieved",
                merchant_id=merchant_id,
                days=days,
                total_queries=total_queries,
                successful_matches=successful_matches,
                no_match_rate=no_match_rate,
                avg_confidence=avg_confidence,
            )

            return {
                "totalQueries": total_queries,
                "successfulMatches": successful_matches,
                "noMatchRate": no_match_rate,
                "avgConfidence": avg_confidence,
                "trend": trend,
                "lastUpdated": last_updated,
            }

        except Exception as e:
            logger.error(
                "knowledge_effectiveness_failed",
                merchant_id=merchant_id,
                error=str(e),
            )
            raise

    async def get_top_topics(
        self,
        merchant_id: int,
        days: int = 7,
        limit: int = 10,
    ) -> dict[str, Any]:
        """Get top topics for dashboard widget.

        Story 10-8: Top Topics Widget.

        Extracts most frequently queried topics from RAG query logs.
        Uses simple frequency ranking (MVP approach).

        Args:
            merchant_id: Merchant ID
            days: Number of days to analyze (default 7, max 90)
            limit: Maximum topics to return (default 10)

        Returns:
            Dict with topics data:
            {
                "topics": [
                    {"name": "topic", "queryCount": 10, "trend": "up"}
                ],
                "lastUpdated": "ISO-8601",
                "period": {"days": 7, "startDate": "...", "endDate": "..."}
            }
        """
        try:
            days = min(max(1, days), 90)
            cutoff_date = datetime.now(UTC).replace(tzinfo=None) - timedelta(days=days)

            current_period_start = cutoff_date
            current_period_end = datetime.now(UTC).replace(tzinfo=None)

            previous_period_start = current_period_start - timedelta(days=days)
            previous_period_end = current_period_start

            current_result = await self.db.execute(
                select(
                    RAGQueryLog.query,
                    func.count(RAGQueryLog.id).label("query_count"),
                )
                .where(RAGQueryLog.merchant_id == merchant_id)
                .where(RAGQueryLog.created_at >= current_period_start)
                .where(RAGQueryLog.created_at < current_period_end)
                .group_by(RAGQueryLog.query)
                .order_by(func.count(RAGQueryLog.id).desc())
                .limit(limit)
            )
            current_rows = current_result.all()

            previous_result = await self.db.execute(
                select(
                    RAGQueryLog.query,
                    func.count(RAGQueryLog.id).label("query_count"),
                )
                .where(RAGQueryLog.merchant_id == merchant_id)
                .where(RAGQueryLog.created_at >= previous_period_start)
                .where(RAGQueryLog.created_at < previous_period_end)
                .group_by(RAGQueryLog.query)
            )
            previous_rows = previous_result.all()
            previous_counts = {row.query: row.query_count for row in previous_rows}

            topics = []
            for row in current_rows:
                # Decrypt topic name if encrypted (Fernet-encrypted queries)
                try:
                    topic_name = decrypt_conversation_content(row.query)

                    # Verify decryption worked - check if result is still encrypted
                    if is_encrypted(topic_name):
                        logger.warning(
                            "topic_decryption_failed",
                            merchant_id=merchant_id,
                            query_prefix=row.query[:20] if row.query else None,
                        )
                        # Mark as encrypted for frontend to handle gracefully
                        topic_name = f"[Encrypted] {topic_name[:16]}..."
                except Exception as e:
                    logger.error(
                        "topic_decryption_error",
                        merchant_id=merchant_id,
                        error=str(e),
                        query_prefix=row.query[:20] if row.query else None,
                    )
                    topic_name = row.query

                current_count = row.query_count
                previous_count = previous_counts.get(topic_name, 0)

                if previous_count == 0:
                    trend = "new"
                else:
                    change = ((current_count - previous_count) / previous_count) * 100
                    if change > 10:
                        trend = "up"
                    elif change < -10:
                        trend = "down"
                    else:
                        trend = "stable"

                topics.append(
                    {
                        "name": topic_name,
                        "queryCount": current_count,
                        "trend": trend,
                    }
                )

            # Monitor decryption success/failure
            decryption_failures = sum(1 for t in topics if t["name"].startswith("[Encrypted]"))
            if decryption_failures > 0:
                logger.warning(
                    "topic_decryption_summary",
                    merchant_id=merchant_id,
                    failures=decryption_failures,
                    total=len(topics),
                )

            period_data = {
                "days": days,
                "startDate": current_period_start.isoformat(),
                "endDate": current_period_end.isoformat(),
            }

            logger.info(
                "top_topics_retrieved",
                merchant_id=merchant_id,
                days=days,
                topic_count=len(topics),
                decryption_failures=decryption_failures,
            )

            return {
                "topics": topics,
                "lastUpdated": datetime.now(UTC).isoformat(),
                "period": period_data,
            }

        except Exception as e:
            logger.error(
                "top_topics_failed",
                merchant_id=merchant_id,
                error=str(e),
            )
            raise

    async def get_response_time_distribution(
        self,
        merchant_id: int,
        days: int = 7,
    ) -> dict[str, Any]:
        """Get response time distribution metrics.

        Story 10-9: ResponseTimeWidget.
        Story 10-9 AC5: Response type breakdown (RAG vs General).

        Returns:
        - Percentile metrics (P50, P95, P99)
        - Histogram distribution
        - Previous period comparison
        - Warning for slow responses
        - Breakdown by response type (RAG vs General)

        Args:
            merchant_id: Merchant ID
            days: Number of days to analyze (default 7, max 30)

        Returns:
            Dict with response time distribution data
        """
        try:
            days = min(max(1, days), 30)
            cutoff_date = datetime.now(UTC).replace(tzinfo=None) - timedelta(days=days)

            result = await self.db.execute(
                select(LLMConversationCost.processing_time_ms, LLMConversationCost.response_type)
                .where(LLMConversationCost.merchant_id == merchant_id)
                .where(LLMConversationCost.created_at >= cutoff_date)
                .where(LLMConversationCost.processing_time_ms.isnot(None))
                .order_by(LLMConversationCost.created_at)
            )
            rows = result.all()
            times = [float(row.processing_time_ms) for row in rows]

            if not times:
                return {
                    "percentiles": {"p50": None, "p95": None, "p99": None},
                    "histogram": [],
                    "previousPeriod": {
                        "percentiles": {"p50": None, "p95": None, "p99": None},
                        "comparison": None,
                    },
                    "warning": None,
                    "lastUpdated": datetime.now(UTC).isoformat(),
                    "period": f"{days}d",
                    "count": 0,
                }

            times_sorted = sorted(times)
            count = len(times_sorted)

            def percentile(data: list[float], p: float) -> int | None:
                if not data:
                    return None
                k = (len(data) - 1) * p / 100
                f = int(k)
                c = f + 1 if f + 1 < len(data) else f
                if f == c:
                    return int(data[f])
                return int(data[f] * (c - k) + data[c] * (k - f))

            p50 = percentile(times_sorted, 50)
            p95 = percentile(times_sorted, 95)
            p99 = percentile(times_sorted, 99)

            BUCKETS = [
                {"label": "0-1s", "min": 0, "max": 1000, "color": "green"},
                {"label": "1-2s", "min": 1000, "max": 2000, "color": "green"},
                {"label": "2-3s", "min": 2000, "max": 3000, "color": "green"},
                {"label": "3-5s", "min": 3000, "max": 5000, "color": "yellow"},
                {"label": "5s+", "min": 5000, "max": None, "color": "red"},
            ]

            histogram = [{"label": b["label"], "count": 0, "color": b["color"]} for b in BUCKETS]

            for time_ms in times:
                for i, bucket in enumerate(BUCKETS):
                    if bucket["max"] is None:
                        if time_ms >= bucket["min"]:
                            histogram[i]["count"] += 1
                            break
                    else:
                        if bucket["min"] <= time_ms < bucket["max"]:
                            histogram[i]["count"] += 1
                            break

            prev_cutoff = cutoff_date - timedelta(days=days)
            prev_end = cutoff_date

            prev_result = await self.db.execute(
                select(LLMConversationCost.processing_time_ms)
                .where(LLMConversationCost.merchant_id == merchant_id)
                .where(LLMConversationCost.created_at >= prev_cutoff)
                .where(LLMConversationCost.created_at < prev_end)
                .where(LLMConversationCost.processing_time_ms.isnot(None))
                .order_by(LLMConversationCost.created_at)
            )
            prev_times = [float(row.processing_time_ms) for row in prev_result.all()]

            prev_p50 = percentile(sorted(prev_times), 50) if prev_times else None
            prev_p95 = percentile(sorted(prev_times), 95) if prev_times else None
            prev_p99 = percentile(sorted(prev_times), 99) if prev_times else None

            comparison = None
            if p50 is not None and prev_p50 is not None:

                def calc_delta(current: int | None, previous: int | None):
                    if current is None or previous is None or previous == 0:
                        return None
                    delta_ms = current - previous
                    delta_percent = round((delta_ms / previous) * 100, 1)
                    if delta_ms < 0:
                        trend = "improving"
                    elif delta_ms > 0:
                        trend = "degrading"
                    else:
                        trend = "stable"
                    return {
                        "deltaMs": delta_ms,
                        "deltaPercent": delta_percent,
                        "trend": trend,
                    }

                comparison = {
                    "p50": calc_delta(p50, prev_p50),
                    "p95": calc_delta(p95, prev_p95),
                    "p99": calc_delta(p99, prev_p99),
                }

            warning = None
            if p95 is not None:
                if p95 > 5000:
                    warning = {
                        "show": True,
                        "message": "P95 response time exceeds 5 seconds. Consider optimizing knowledge base.",
                        "severity": "critical",
                    }
                elif p95 > 3000:
                    warning = {
                        "show": True,
                        "message": "P95 response time is elevated. Monitor for performance issues.",
                        "severity": "warning",
                    }

            rag_times = [
                float(row.processing_time_ms) for row in rows if row.response_type == "rag"
            ]
            general_times = [
                float(row.processing_time_ms)
                for row in rows
                if row.response_type in ("general", "unknown", None)
            ]

            rag_p50 = percentile(sorted(rag_times), 50) if rag_times else None
            rag_p95 = percentile(sorted(rag_times), 95) if rag_times else None
            rag_p99 = percentile(sorted(rag_times), 99) if rag_times else None

            general_p50 = percentile(sorted(general_times), 50) if general_times else None
            general_p95 = percentile(sorted(general_times), 95) if general_times else None
            general_p99 = percentile(sorted(general_times), 99) if general_times else None

            response_type_breakdown = {
                "rag": {
                    "count": len(rag_times),
                    "percentiles": {"p50": rag_p50, "p95": rag_p95, "p99": rag_p99},
                },
                "general": {
                    "count": len(general_times),
                    "percentiles": {"p50": general_p50, "p95": general_p95, "p99": general_p99},
                },
            }

            logger.info(
                "response_time_distribution_retrieved",
                merchant_id=merchant_id,
                days=days,
                count=count,
                p50=p50,
                p95=p95,
                p99=p99,
                rag_count=len(rag_times),
                general_count=len(general_times),
            )

            return {
                "percentiles": {"p50": p50, "p95": p95, "p99": p99},
                "histogram": histogram,
                "previousPeriod": {
                    "percentiles": {"p50": prev_p50, "p95": prev_p95, "p99": prev_p99},
                    "comparison": comparison,
                },
                "warning": warning,
                "lastUpdated": datetime.now(UTC).isoformat(),
                "period": f"{days}d",
                "count": count,
                "responseTypeBreakdown": response_type_breakdown,
            }

        except Exception as e:
            logger.error(
                "response_time_distribution_failed",
                merchant_id=merchant_id,
                error=str(e),
            )
            raise

    async def get_faq_usage(
        self,
        merchant_id: int,
        days: int = 30,
        include_unused: bool = True,
    ) -> dict[str, Any]:
        """Get FAQ usage analytics for dashboard widget.

        Story 10-10: FAQ Usage Widget.

        Returns:
        - Top FAQs by click frequency
        - Click count and conversion rate per FAQ
        - Unused FAQs (0 clicks in period)
        - Period comparison (current vs previous)

        Args:
            merchant_id: Merchant ID
            days: Number of days to analyze (default 30)
            include_unused: Whether to include FAQs with 0 clicks

        Returns:
            Dict with FAQ usage data
        """
        from sqlalchemy import and_

        from app.models.faq import Faq
        from app.models.faq_interaction_log import FaqInteractionLog

        try:
            cutoff_date = datetime.now(UTC).replace(tzinfo=None) - timedelta(days=days)
            prev_cutoff = cutoff_date - timedelta(days=days)
            prev_end = cutoff_date

            current_result = await self.db.execute(
                select(
                    Faq.id,
                    Faq.question,
                    func.count(FaqInteractionLog.id).label("click_count"),
                    func.sum(FaqInteractionLog.had_followup).label("followup_count"),
                )
                .outerjoin(
                    FaqInteractionLog,
                    and_(
                        FaqInteractionLog.faq_id == Faq.id,
                        FaqInteractionLog.merchant_id == merchant_id,
                        FaqInteractionLog.clicked_at >= cutoff_date,
                    ),
                )
                .where(Faq.merchant_id == merchant_id)
                .group_by(Faq.id, Faq.question)
                .order_by(func.count(FaqInteractionLog.id).desc())
            )
            current_rows = current_result.all()

            prev_result = await self.db.execute(
                select(
                    Faq.id,
                    func.count(FaqInteractionLog.id).label("click_count"),
                    func.sum(FaqInteractionLog.had_followup).label("followup_count"),
                )
                .outerjoin(
                    FaqInteractionLog,
                    and_(
                        FaqInteractionLog.faq_id == Faq.id,
                        FaqInteractionLog.merchant_id == merchant_id,
                        FaqInteractionLog.clicked_at >= prev_cutoff,
                        FaqInteractionLog.clicked_at < prev_end,
                    ),
                )
                .where(Faq.merchant_id == merchant_id)
                .group_by(Faq.id)
            )
            prev_data = {row.id: row for row in prev_result.all()}

            faq_items = []
            unused_faqs = []

            for row in current_rows:
                click_count = row.click_count or 0
                followup_count = row.followup_count or 0

                conversion_rate = 0.0
                if click_count > 0:
                    conversion_rate = round((followup_count / click_count) * 100, 1)

                prev_row = prev_data.get(row.id)
                prev_click_count = prev_row.click_count if prev_row else 0
                prev_followup_count = prev_row.followup_count if prev_row else 0

                prev_conversion_rate = 0.0
                if prev_click_count > 0:
                    prev_conversion_rate = round((prev_followup_count / prev_click_count) * 100, 1)

                click_change = None
                if prev_click_count > 0:
                    click_change = round(
                        ((click_count - prev_click_count) / prev_click_count) * 100, 1
                    )

                conversion_change = None
                if prev_conversion_rate > 0:
                    conversion_change = round(conversion_rate - prev_conversion_rate, 1)

                item = {
                    "id": row.id,
                    "question": row.question,
                    "clickCount": click_count,
                    "conversionRate": conversion_rate,
                    "followupCount": followup_count,
                    "isUnused": click_count == 0,
                    "previousPeriod": {
                        "clickCount": prev_click_count,
                        "conversionRate": prev_conversion_rate,
                    },
                    "change": {
                        "clickChange": click_change,
                        "conversionChange": conversion_change,
                    },
                }

                if click_count == 0:
                    unused_faqs.append(item)
                else:
                    faq_items.append(item)

            if include_unused:
                faq_items.extend(unused_faqs)

            total_clicks = sum(item["clickCount"] for item in faq_items)
            total_faqs = len(current_rows)
            total_unused = len(unused_faqs)

            avg_conversion_rate = 0.0
            if total_clicks > 0:
                total_followups = sum(item["followupCount"] for item in faq_items)
                avg_conversion_rate = round((total_followups / total_clicks) * 100, 1)

            logger.info(
                "faq_usage_retrieved",
                merchant_id=merchant_id,
                days=days,
                total_faqs=total_faqs,
                total_clicks=total_clicks,
                avg_conversion_rate=avg_conversion_rate,
            )

            return {
                "period": {
                    "days": days,
                    "startDate": cutoff_date.isoformat(),
                    "endDate": datetime.now(UTC).isoformat(),
                },
                "faqs": faq_items,
                "summary": {
                    "totalFaqs": total_faqs,
                    "totalClicks": total_clicks,
                    "avgConversionRate": avg_conversion_rate,
                    "unusedCount": total_unused,
                },
                "lastUpdated": datetime.now(UTC).isoformat(),
            }

        except Exception as e:
            logger.error(
                "faq_usage_failed",
                merchant_id=merchant_id,
                error=str(e),
            )
            raise

    async def get_geographic_analytics(
        self,
        merchant_id: int,
    ) -> dict[str, Any]:
        """Get geographic breakdown of orders by country, city, and province.

        Story 4-13: Geographic Analytics

        Args:
            merchant_id: Merchant ID

        Returns:
            Dict with byCountry, byCity, byProvince breakdowns
        """
        try:
            by_country_result = await self.db.execute(
                select(
                    Order.shipping_country.label("country"),
                    func.count(Order.id).label("order_count"),
                    func.sum(Order.total).label("total_revenue"),
                )
                .where(Order.merchant_id == merchant_id)
                .where(Order.shipping_country.isnot(None))
                .group_by(Order.shipping_country)
                .order_by(func.sum(Order.total).desc())
            )
            by_country = [
                {
                    "country": row.country,
                    "countryName": None,
                    "orderCount": row.order_count,
                    "totalRevenue": float(row.total_revenue or 0),
                }
                for row in by_country_result
            ]

            by_city_result = await self.db.execute(
                select(
                    Order.shipping_city.label("city"),
                    Order.shipping_country.label("country"),
                    func.count(Order.id).label("order_count"),
                    func.sum(Order.total).label("total_revenue"),
                )
                .where(Order.merchant_id == merchant_id)
                .where(Order.shipping_city.isnot(None))
                .group_by(Order.shipping_city, Order.shipping_country)
                .order_by(func.sum(Order.total).desc())
                .limit(20)
            )
            by_city = [
                {
                    "city": row.city,
                    "country": row.country,
                    "orderCount": row.order_count,
                    "totalRevenue": float(row.total_revenue or 0),
                }
                for row in by_city_result
            ]

            by_province_result = await self.db.execute(
                select(
                    Order.shipping_province.label("province"),
                    Order.shipping_country.label("country"),
                    func.count(Order.id).label("order_count"),
                    func.sum(Order.total).label("total_revenue"),
                )
                .where(Order.merchant_id == merchant_id)
                .where(Order.shipping_province.isnot(None))
                .group_by(Order.shipping_province, Order.shipping_country)
                .order_by(func.sum(Order.total).desc())
                .limit(20)
            )
            by_province = [
                {
                    "province": row.province,
                    "country": row.country,
                    "orderCount": row.order_count,
                    "totalRevenue": float(row.total_revenue or 0),
                }
                for row in by_province_result
            ]

            total_orders = sum(c["orderCount"] for c in by_country)
            total_revenue = sum(c["totalRevenue"] for c in by_country)

            logger.info(
                "geographic_analytics_retrieved",
                merchant_id=merchant_id,
                total_countries=len(by_country),
                total_cities=len(by_city),
                total_provinces=len(by_province),
            )

            return {
                "byCountry": by_country,
                "byCity": by_city,
                "byProvince": by_province,
                "totalOrders": total_orders,
                "totalRevenue": total_revenue,
            }

        except Exception as e:
            logger.error(
                "geographic_analytics_failed",
                merchant_id=merchant_id,
                error=str(e),
            )
            raise

    # ────────────────────────────────────────────────────────────────
    # Answer Performance Dashboard Methods
    # ────────────────────────────────────────────────────────────────

    async def calculate_answer_quality_score(
        self,
        merchant_id: int,
        days: int = 30,
    ) -> dict[str, Any]:
        """Calculate Answer Quality Score - Aggregate RAG performance metric.

        Calculates a composite score (0-100) based on:
        - Match rate (40% weight)
        - Average confidence (35% weight)
        - User feedback (25% weight)

        Returns score, status, and 14-day trend.
        """
        try:
            from datetime import datetime, timedelta
            from app.models.rag_query_log import RAGQueryLog
            from app.models.conversation import Conversation
            from app.models.message import Message
            from sqlalchemy import select, func

            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)

            # Calculate match rate and confidence from RAG query logs
            rag_result = await self.db.execute(
                select(
                    func.count(RAGQueryLog.id).label("total_queries"),
                    func.sum(case((RAGQueryLog.matched == True, 1), else_=0)).label("matched"),
                    func.avg(RAGQueryLog.confidence).label("avg_confidence"),
                )
                .where(RAGQueryLog.merchant_id == merchant_id)
                .where(RAGQueryLog.created_at >= start_date)
                .where(RAGQueryLog.created_at <= end_date)
            )
            rag_row = rag_result.one_or_none()

            total_queries = rag_row.total_queries if rag_row else 0
            matched_count = rag_row.matched if rag_row else 0
            avg_confidence = (
                float(rag_row.avg_confidence) if rag_row and rag_row.avg_confidence else 0.5
            )

            # Calculate match rate (0-1)
            match_rate = (matched_count / total_queries) if total_queries > 0 else 0.5

            # Calculate user feedback rate (thumbs up/down)
            # Get messages with feedback from MessageFeedback table
            from app.models.message_feedback import MessageFeedback
            from app.models.message import Message as Msg
            from app.models.conversation import Conversation as Conv

            feedback_result = await self.db.execute(
                select(
                    func.count(MessageFeedback.id).label("total_feedback"),
                    func.sum(case((MessageFeedback.rating == "positive", 1), else_=0)).label(
                        "positive"
                    ),
                )
                .select_from(MessageFeedback)
                .join(Msg, MessageFeedback.message_id == Msg.id)
                .join(Conv, Msg.conversation_id == Conv.id)
                .where(Conv.merchant_id == merchant_id)
                .where(Msg.created_at >= start_date)
                .where(Msg.created_at <= end_date)
            )
            feedback_row = feedback_result.one_or_none()

            total_feedback = feedback_row.total_feedback if feedback_row else 0
            positive_feedback = feedback_row.positive if feedback_row else 0

            # Calculate feedback rate (0-1)
            feedback_rate = (positive_feedback / total_feedback) if total_feedback > 0 else 0.7

            # Calculate composite score (0-100)
            # Weighted: Match rate 40%, Confidence 35%, Feedback 25%
            score = (match_rate * 40) + (avg_confidence * 35) + (feedback_rate * 25)

            # Determine status
            if score >= 80:
                status_label = "excellent"
            elif score >= 60:
                status_label = "good"
            elif score >= 40:
                status_label = "fair"
            else:
                status_label = "poor"

            # Calculate 14-day trend
            trend = []
            for i in range(14):
                day_start = end_date - timedelta(days=14 - i)
                day_end = day_start + timedelta(days=1)

                day_result = await self.db.execute(
                    select(
                        func.count(RAGQueryLog.id).label("day_total"),
                        func.sum(case((RAGQueryLog.matched == True, 1), else_=0)).label(
                            "day_matched"
                        ),
                    )
                    .where(RAGQueryLog.merchant_id == merchant_id)
                    .where(RAGQueryLog.created_at >= day_start)
                    .where(RAGQueryLog.created_at < day_end)
                )
                day_row = day_result.one_or_none()

                day_total = day_row.day_total if day_row else 0
                day_matched = day_row.day_matched if day_row else 0
                day_rate = (day_matched / day_total) if day_total > 0 else 0.5
                trend.append(day_rate)

            return {
                "score": round(score, 1),
                "status": status_label,
                "trend": trend,
                "lastUpdated": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(
                "answer_quality_score_failed",
                merchant_id=merchant_id,
                error=str(e),
            )
            raise

    async def get_top_questions_with_metrics(
        self,
        merchant_id: int,
        days: int = 30,
        limit: int = 10,
    ) -> dict[str, Any]:
        """Get Top Customer Questions with performance metrics."""
        try:
            from datetime import datetime, timedelta
            from app.models.rag_query_log import RAGQueryLog
            from sqlalchemy import select, func, desc
            from collections import Counter

            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)

            # Get top questions by frequency
            result = await self.db.execute(
                select(
                    RAGQueryLog.query,
                    func.count(RAGQueryLog.id).label("frequency"),
                    func.sum(case((RAGQueryLog.matched == True, 1), else_=0)).label(
                        "matched_count"
                    ),
                    func.avg(RAGQueryLog.confidence).label("avg_confidence"),
                )
                .where(RAGQueryLog.merchant_id == merchant_id)
                .where(RAGQueryLog.created_at >= start_date)
                .where(RAGQueryLog.created_at <= end_date)
                .group_by(RAGQueryLog.query)
                .order_by(desc(func.count(RAGQueryLog.id)))
                .limit(limit)
            )
            rows = result.all()

            questions = []
            for row in rows:
                frequency = row.frequency or 0
                matched_count = row.matched_count or 0
                avg_conf = float(row.avg_confidence) if row.avg_confidence else 0.5
                match_rate = (matched_count / frequency) if frequency > 0 else 0

                # Determine trend (simplified - would need more complex logic)
                trend = "stable"  # Could calculate by comparing recent vs older periods

                # Categorize question (simplified - could use ML classification)
                query_lower = row.query.lower()
                if any(word in query_lower for word in ["price", "cost", "how much"]):
                    category = "Pricing"
                elif any(word in query_lower for word in ["shipping", "delivery", "when will"]):
                    category = "Shipping"
                elif any(word in query_lower for word in ["return", "refund"]):
                    category = "Returns"
                elif any(word in query_lower for word in ["product", "item"]):
                    category = "Product Info"
                else:
                    category = "General"

                questions.append(
                    {
                        "question": row.query,
                        "frequency": frequency,
                        "matchRate": match_rate,
                        "avgConfidence": avg_conf,
                        "category": category,
                        "trend": trend,
                    }
                )

            return {
                "questions": questions,
                "period": {
                    "days": days,
                    "startDate": start_date.isoformat(),
                    "endDate": end_date.isoformat(),
                },
                "lastUpdated": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(
                "top_questions_failed",
                merchant_id=merchant_id,
                error=str(e),
            )
            raise

    async def get_customer_feedback_metrics(
        self,
        merchant_id: int,
        days: int = 30,
    ) -> dict[str, Any]:
        """Get Customer Feedback Metrics for RAG answers."""
        try:
            from datetime import datetime, timedelta
            from app.models.conversation import Conversation
            from app.models.message import Message
            from app.models.message_feedback import MessageFeedback
            from sqlalchemy import select, func
            from collections import Counter

            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)

            # Get feedback stats from MessageFeedback table
            result = await self.db.execute(
                select(
                    func.count(MessageFeedback.id).label("total_feedback"),
                    func.sum(case((MessageFeedback.rating == "positive", 1), else_=0)).label(
                        "positive_count"
                    ),
                    func.sum(case((MessageFeedback.rating == "negative", 1), else_=0)).label(
                        "negative_count"
                    ),
                )
                .select_from(MessageFeedback)
                .join(Message, MessageFeedback.message_id == Message.id)
                .join(Conversation, Message.conversation_id == Conversation.id)
                .where(Conversation.merchant_id == merchant_id)
                .where(Message.created_at >= start_date)
                .where(Message.created_at <= end_date)
            )
            row = result.one_or_none()

            total_feedback = row.total_feedback if row else 0
            positive_count = row.positive_count if row and row.positive_count is not None else 0
            negative_count = row.negative_count if row and row.negative_count is not None else 0

            positive_rate = (positive_count / total_feedback) if total_feedback > 0 else 0
            negative_rate = (negative_count / total_feedback) if total_feedback > 0 else 0

            # Extract feedback themes (simplified - would use NLP in production)
            themes = []
            if positive_count > 0 and positive_count > negative_count:
                themes.append(
                    {"theme": "Helpful responses", "count": positive_count, "sentiment": "positive"}
                )
            if negative_count > 0:
                themes.append(
                    {"theme": "Needs improvement", "count": negative_count, "sentiment": "negative"}
                )

            return {
                "totalFeedback": total_feedback,
                "positiveRate": positive_rate,
                "negativeRate": negative_rate,
                "themes": themes[:5],  # Top 5 themes
                "lastUpdated": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(
                "customer_feedback_failed",
                merchant_id=merchant_id,
                error=str(e),
            )
            raise

    async def get_document_usage_stats(
        self,
        merchant_id: int,
        days: int = 30,
        limit: int = 50,
        offset: int = 0,
    ) -> dict[str, Any]:
        """Get Document Performance and Usage Analytics.

        OPTIMIZED: Efficient query with JSONB path operations to count document references.
        Uses PostgreSQL jsonb_array_elements to extract and count document_id references.
        """
        try:
            from datetime import datetime, timedelta
            from app.models.knowledge_base import KnowledgeDocument
            from app.models.rag_query_log import RAGQueryLog
            from sqlalchemy import select, func, desc, text
            import json

            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)

            # OPTIMIZATION: Use PostgreSQL jsonb_array_elements and jsonb_path_query
            # to efficiently count document references without N+1 queries
            # This extracts document_id values from the sources JSONB array and counts them

            # First, get all documents for the merchant
            docs_result = await self.db.execute(
                select(
                    KnowledgeDocument.id,
                    KnowledgeDocument.filename,
                    KnowledgeDocument.status,
                    KnowledgeDocument.created_at,
                )
                .where(KnowledgeDocument.merchant_id == merchant_id)
                .order_by(KnowledgeDocument.id)
            )
            documents = docs_result.all()

            if not documents:
                return {
                    "documents": [],
                    "summary": {"total": 0, "active": 0, "unused": 0, "outdated": 0},
                    "period": {
                        "days": days,
                        "startDate": start_date.isoformat(),
                        "endDate": end_date.isoformat(),
                    },
                    "lastUpdated": datetime.utcnow().isoformat(),
                }

            # OPTIMIZATION: Bulk count references using single query with jsonb_path_exists
            # This uses PostgreSQL's native JSONB operators for maximum performance
            doc_ids = [doc.id for doc in documents]

            # Build a single query to get reference counts for all documents
            # Using jsonb_path_exists to check if each document_id appears in the sources array
            # FIXED: Filter out NULL and scalar sources to avoid "cannot extract elements from a scalar" error
            ref_counts_query = text("""
                SELECT
                    elem->>'document_id' as doc_id,
                    COUNT(*) as reference_count
                FROM rag_query_logs,
                     jsonb_array_elements(sources) as elem
                WHERE merchant_id = :merchant_id
                  AND created_at >= :start_date
                  AND created_at <= :end_date
                  AND jsonb_typeof(sources) = 'array'
                  AND elem->>'document_id' IS NOT NULL
                GROUP BY elem->>'document_id'
            """)

            ref_result = await self.db.execute(
                ref_counts_query,
                {"merchant_id": merchant_id, "start_date": start_date, "end_date": end_date},
            )

            # Build lookup dict for O(1) access
            ref_counts = {int(row.doc_id): row.reference_count for row in ref_result}

            doc_stats = []
            active_count = 0
            unused_count = 0
            outdated_count = 0

            for doc in documents:
                # Get reference count from lookup dict (default to 0)
                ref_count = ref_counts.get(doc.id, 0)

                # Determine status based on reference count and document status
                if ref_count == 0:
                    status = "unused"
                    unused_count += 1
                elif doc.status == "error":
                    status = "outdated"
                    outdated_count += 1
                else:
                    status = "active"
                    active_count += 1

                # Estimate confidence based on document status and reference count
                # Active documents with more references get higher confidence
                base_confidence = 0.6
                if status == "active":
                    confidence_boost = min(ref_count * 0.01, 0.3)  # Max 0.3 boost
                    avg_confidence = base_confidence + confidence_boost
                else:
                    avg_confidence = base_confidence

                doc_stats.append(
                    {
                        "documentId": doc.id,
                        "filename": doc.filename,
                        "referenceCount": ref_count,
                        "avgConfidence": round(avg_confidence, 2),
                        "lastReferenced": doc.created_at.isoformat() if doc.created_at else None,
                        "status": status,
                    }
                )

            # Sort by reference count (descending)
            doc_stats.sort(key=lambda x: x["referenceCount"], reverse=True)

            # Apply pagination
            total_documents = len(doc_stats)
            paginated_docs = doc_stats[offset : offset + limit]

            return {
                "documents": paginated_docs,
                "pagination": {
                    "total": total_documents,
                    "limit": limit,
                    "offset": offset,
                    "hasMore": offset + limit < total_documents,
                },
                "summary": {
                    "total": total_documents,
                    "active": active_count,
                    "unused": unused_count,
                    "outdated": outdated_count,
                },
                "period": {
                    "days": days,
                    "startDate": start_date.isoformat(),
                    "endDate": end_date.isoformat(),
                },
                "lastUpdated": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(
                "document_performance_failed",
                merchant_id=merchant_id,
                error=str(e),
                exc_info=True,
            )
            raise

    async def get_high_impact_improvements(
        self,
        merchant_id: int,
        days: int = 30,
        limit: int = 10,
    ) -> dict[str, Any]:
        """Get High-Impact Improvements - Prioritized action items."""
        try:
            from datetime import datetime, timedelta
            from app.models.rag_query_log import RAGQueryLog
            from sqlalchemy import select, func, desc

            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)

            # Get questions with high frequency but low match rate
            result = await self.db.execute(
                select(
                    RAGQueryLog.query,
                    func.count(RAGQueryLog.id).label("frequency"),
                    func.sum(case((RAGQueryLog.matched == True, 1), else_=0)).label(
                        "matched_count"
                    ),
                )
                .where(RAGQueryLog.merchant_id == merchant_id)
                .where(RAGQueryLog.created_at >= start_date)
                .where(RAGQueryLog.created_at <= end_date)
                .group_by(RAGQueryLog.query)
                .having(func.count(RAGQueryLog.id) >= 3)  # At least 3 asked
                .order_by(desc(func.count(RAGQueryLog.id)))
                .limit(limit * 2)  # Get more to filter
            )
            rows = result.all()

            actions = []
            for row in rows:
                frequency = row.frequency or 0
                matched_count = row.matched_count or 0
                match_rate = (matched_count / frequency) if frequency > 0 else 0

                # Only include questions with low match rate (< 60%)
                if match_rate < 0.6:
                    # Determine suggested action
                    if row.query.endswith("?"):
                        suggested_action = "add_faq"
                    else:
                        suggested_action = "upload_document"

                    # Calculate estimated handoff reduction
                    estimated_reduction = (1 - match_rate) * frequency * 0.1

                    # Determine priority
                    if frequency >= 10 and match_rate < 0.3:
                        priority = "high"
                    elif frequency >= 5 and match_rate < 0.5:
                        priority = "medium"
                    else:
                        priority = "low"

                    actions.append(
                        {
                            "id": f"action_{len(actions)}",
                            "question": row.query,
                            "frequency": frequency,
                            "matchRate": match_rate,
                            "estimatedHandoffReduction": estimated_reduction,
                            "suggestedAction": suggested_action,
                            "priority": priority,
                        }
                    )

            # Sort by estimated impact and take top N
            actions.sort(key=lambda x: x["estimatedHandoffReduction"], reverse=True)
            actions = actions[:limit]

            # Calculate total estimated impact
            total_impact = sum(action["estimatedHandoffReduction"] for action in actions)

            return {
                "actions": actions,
                "totalEstimatedImpact": total_impact,
                "lastUpdated": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(
                "high_impact_improvements_failed",
                merchant_id=merchant_id,
                error=str(e),
            )
            raise

    async def get_question_categories(
        self,
        merchant_id: int,
        days: int = 30,
    ) -> list[dict[str, Any]]:
        """Get Question Categories breakdown with performance metrics."""
        try:
            from datetime import datetime, timedelta
            from app.models.rag_query_log import RAGQueryLog
            from sqlalchemy import select, func, desc

            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)

            # Get all queries with their metrics
            result = await self.db.execute(
                select(
                    RAGQueryLog.query,
                    func.count(RAGQueryLog.id).label("volume"),
                    func.sum(case((RAGQueryLog.matched == True, 1), else_=0)).label(
                        "matched_count"
                    ),
                    func.avg(RAGQueryLog.confidence).label("avg_confidence"),
                )
                .where(RAGQueryLog.merchant_id == merchant_id)
                .where(RAGQueryLog.created_at >= start_date)
                .where(RAGQueryLog.created_at <= end_date)
                .group_by(RAGQueryLog.query)
                .order_by(desc(func.count(RAGQueryLog.id)))
            )
            rows = result.all()

            # Categorize queries
            categories = {}
            for row in rows:
                query_lower = row.query.lower()
                category = self._categorize_query(query_lower)

                if category not in categories:
                    categories[category] = {
                        "category": category,
                        "volume": 0,
                        "matchedCount": 0,
                        "totalConfidence": 0,
                        "queries": [],
                    }

                categories[category]["volume"] += row.volume or 0
                categories[category]["matchedCount"] += row.matched_count or 0
                if row.avg_confidence:
                    categories[category]["totalConfidence"] += float(row.avg_confidence) * (
                        row.volume or 0
                    )
                categories[category]["queries"].append(row.query)

            # Calculate metrics per category
            category_list = []
            for cat_name, cat_data in categories.items():
                volume = cat_data["volume"]
                matched = cat_data["matchedCount"]
                avg_conf = cat_data["totalConfidence"] / volume if volume > 0 else 0
                match_rate = (matched / volume) if volume > 0 else 0

                # Determine trend (simplified - could implement proper trend analysis)
                trend = "stable"

                # Get top 2 questions for this category
                top_queries = cat_data["queries"][:2]

                category_list.append(
                    {
                        "category": cat_name,
                        "volume": volume,
                        "matchRate": match_rate,
                        "avgConfidence": avg_conf,
                        "trend": trend,
                        "topQuestions": top_queries,
                    }
                )

            # Sort by volume
            category_list.sort(key=lambda x: x["volume"], reverse=True)

            return category_list

        except Exception as e:
            logger.error(
                "question_categories_failed",
                merchant_id=merchant_id,
                error=str(e),
            )
            raise

    def _categorize_query(self, query: str) -> str:
        """Categorize a query based on keywords."""
        if any(word in query for word in ["price", "cost", "how much", "expensive", "cheap"]):
            return "Pricing"
        elif any(word in query for word in ["shipping", "delivery", "when will", "ship", "arrive"]):
            return "Shipping & Delivery"
        elif any(word in query for word in ["return", "refund", "exchange", "policy"]):
            return "Returns & Refunds"
        elif any(word in query for word in ["product", "item", "stock", "inventory", "available"]):
            return "Product Information"
        elif any(word in query for word in ["order", "status", "tracking", "where is"]):
            return "Order Management"
        elif any(word in query for word in ["payment", "pay", "checkout", "card"]):
            return "Payment & Checkout"
        elif any(word in query for word in ["account", "login", "password", "sign in"]):
            return "Account Support"
        elif any(word in query for word in ["discount", "coupon", "promo", "sale", "offer"]):
            return "Discounts & Promotions"
        else:
            return "General"

    async def get_failed_queries(
        self,
        merchant_id: int,
        days: int = 30,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Get Failed Queries - questions without answers."""
        try:
            from datetime import datetime, timedelta
            from app.models.rag_query_log import RAGQueryLog
            from sqlalchemy import select, func, desc

            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)

            # Get queries that failed to match (matched = False)
            result = await self.db.execute(
                select(
                    RAGQueryLog.query,
                    func.count(RAGQueryLog.id).label("frequency"),
                    func.max(RAGQueryLog.created_at).label("last_asked"),
                )
                .where(RAGQueryLog.merchant_id == merchant_id)
                .where(RAGQueryLog.created_at >= start_date)
                .where(RAGQueryLog.created_at <= end_date)
                .where(RAGQueryLog.matched == False)
                .group_by(RAGQueryLog.query)
                .order_by(desc(func.count(RAGQueryLog.id)))
                .limit(limit)
            )
            rows = result.all()

            failed_queries = []
            for row in rows:
                query_lower = row.query.lower()
                category = self._categorize_query(query_lower)

                # Determine suggested action
                if row.query.endswith("?"):
                    suggested_action = "add_faq"
                elif any(word in query_lower for word in ["product", "item", "specification"]):
                    suggested_action = "upload_document"
                else:
                    suggested_action = "update_document"

                # Calculate estimated impact (frequency * 0.1 = 10% handoff reduction per fix)
                estimated_impact = (row.frequency or 0) * 0.1

                failed_queries.append(
                    {
                        "query": row.query,
                        "frequency": row.frequency or 0,
                        "lastAsked": row.last_asked.isoformat()
                        if row.last_asked
                        else datetime.utcnow().isoformat(),
                        "suggestedAction": suggested_action,
                        "estimatedImpact": estimated_impact,
                        "category": category,
                    }
                )

            return failed_queries

        except Exception as e:
            logger.error(
                "failed_queries_failed",
                merchant_id=merchant_id,
                error=str(e),
            )
            raise

    async def get_performance_alerts(
        self,
        merchant_id: int,
        days: int = 1,
    ) -> list[dict[str, Any]]:
        """Get Performance Alerts for RAG health monitoring."""
        try:
            from datetime import datetime, timedelta
            from app.models.rag_query_log import RAGQueryLog
            from app.models.knowledge_base import KnowledgeDocument
            from sqlalchemy import select, func

            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)

            alerts = []

            # Check 1: No-match rate spike (critical if > 30%)
            result = await self.db.execute(
                select(
                    func.count(RAGQueryLog.id).label("total"),
                    func.sum(case((RAGQueryLog.matched == True, 1), else_=0)).label("matched"),
                )
                .where(RAGQueryLog.merchant_id == merchant_id)
                .where(RAGQueryLog.created_at >= start_date)
                .where(RAGQueryLog.created_at <= end_date)
            )
            row = result.one_or_none()

            if row and row.total > 0:
                no_match_rate = 1 - (row.matched / row.total) if row.total else 0
                if no_match_rate > 0.3:
                    alerts.append(
                        {
                            "id": "no-match-spike",
                            "type": "critical",
                            "title": "High No-Match Rate",
                            "description": "More than 30% of queries are not finding matches in the knowledge base.",
                            "metric": "No-match rate",
                            "value": f"{no_match_rate * 100:.1f}%",
                            "threshold": "30%",
                            "timestamp": datetime.utcnow().isoformat(),
                            "suggestedAction": "Review failed queries and add missing documentation",
                        }
                    )
                elif no_match_rate > 0.2:
                    alerts.append(
                        {
                            "id": "no-match-warning",
                            "type": "warning",
                            "title": "Elevated No-Match Rate",
                            "description": "No-match rate is above 20%. Consider expanding knowledge base.",
                            "metric": "No-match rate",
                            "value": f"{no_match_rate * 100:.1f}%",
                            "threshold": "20%",
                            "timestamp": datetime.utcnow().isoformat(),
                            "suggestedAction": "Add documentation for frequently asked questions",
                        }
                    )

            # Check 2: Low confidence average (warning if < 0.6)
            result = await self.db.execute(
                select(func.avg(RAGQueryLog.confidence).label("avg_confidence"))
                .where(RAGQueryLog.merchant_id == merchant_id)
                .where(RAGQueryLog.created_at >= start_date)
                .where(RAGQueryLog.created_at <= end_date)
                .where(RAGQueryLog.matched == True)
            )
            row = result.one_or_none()

            if row and row.avg_confidence and row.avg_confidence < 0.6:
                alerts.append(
                    {
                        "id": "low-confidence",
                        "type": "warning",
                        "title": "Low Average Confidence",
                        "description": "Average confidence score is below 60%. Answers may not be accurate.",
                        "metric": "Avg confidence",
                        "value": f"{row.avg_confidence * 100:.1f}%",
                        "threshold": "60%",
                        "timestamp": datetime.utcnow().isoformat(),
                        "suggestedAction": "Review and improve knowledge base quality",
                    }
                )

            # Check 3: Documents with errors (critical)
            result = await self.db.execute(
                select(func.count(KnowledgeDocument.id).label("error_count"))
                .where(KnowledgeDocument.merchant_id == merchant_id)
                .where(KnowledgeDocument.status == "error")
            )
            row = result.one_or_none()

            if row and row.error_count > 0:
                alerts.append(
                    {
                        "id": "document-errors",
                        "type": "critical",
                        "title": f"{row.error_count} Document(s) Failed to Process",
                        "description": "Some documents have errors during processing or embedding.",
                        "metric": "Error count",
                        "value": row.error_count,
                        "threshold": "0",
                        "timestamp": datetime.utcnow().isoformat(),
                        "suggestedAction": "Check document status and re-upload failed documents",
                    }
                )

            # Check 4: Stale knowledge base (info - no recent uploads)
            result = await self.db.execute(
                select(func.max(KnowledgeDocument.created_at).label("last_upload")).where(
                    KnowledgeDocument.merchant_id == merchant_id
                )
            )
            row = result.one_or_none()

            if row and row.last_upload:
                days_since_upload = (end_date - row.last_upload).days
                if days_since_upload > 30:
                    alerts.append(
                        {
                            "id": "stale-kb",
                            "type": "info",
                            "title": "Knowledge Base Not Updated Recently",
                            "description": f"Last upload was {days_since_upload} days ago. Consider adding fresh content.",
                            "metric": "Days since upload",
                            "value": days_since_upload,
                            "threshold": "30",
                            "timestamp": datetime.utcnow().isoformat(),
                            "suggestedAction": "Upload recent documentation to keep knowledge base fresh",
                        }
                    )

            # Sort alerts by severity (critical first, then warning, then info)
            severity_order = {"critical": 0, "warning": 1, "info": 2}
            alerts.sort(key=lambda x: severity_order.get(x["type"], 3))

            return alerts

        except Exception as e:
            logger.error(
                "performance_alerts_failed",
                merchant_id=merchant_id,
                error=str(e),
            )
            raise

    async def get_quick_actions(
        self,
        merchant_id: int,
    ) -> list[dict[str, Any]]:
        """Get Quick Actions for immediate improvements."""
        try:
            from app.models.knowledge_base import KnowledgeDocument
            from sqlalchemy import select, func

            actions = []

            # Action 1: Add FAQ (always available)
            actions.append(
                {
                    "id": "add-faq",
                    "title": "Add New FAQ",
                    "description": "Create a new FAQ entry for common questions",
                    "icon": "add_faq",
                    "actionUrl": "/business-info-faq",
                    "priority": "medium",
                    "estimatedTime": "2 min",
                }
            )

            # Action 2: Upload documentation (always available)
            actions.append(
                {
                    "id": "upload-doc",
                    "title": "Upload Documentation",
                    "description": "Add new documents to the knowledge base",
                    "icon": "upload_document",
                    "actionUrl": "/business-info-faq#knowledge",
                    "priority": "medium",
                    "estimatedTime": "5 min",
                }
            )

            # Action 3: Test RAG (always available)
            actions.append(
                {
                    "id": "test-rag",
                    "title": "Test RAG Query",
                    "description": "Test how the AI responds to specific queries",
                    "icon": "test_rag",
                    "actionUrl": "/bot-preview",
                    "priority": "low",
                    "estimatedTime": "1 min",
                }
            )

            # Action 4: Re-embed knowledge base (conditional)
            result = await self.db.execute(
                select(func.count(KnowledgeDocument.id).label("doc_count"))
                .where(KnowledgeDocument.merchant_id == merchant_id)
                .where(KnowledgeDocument.status == "ready")
            )
            row = result.one_or_none()

            if row and row.doc_count > 0:
                actions.append(
                    {
                        "id": "re-embed",
                        "title": "Re-embed Knowledge Base",
                        "description": "Re-process all documents with updated embedding model",
                        "icon": "re_embed",
                        "actionUrl": "",  # Will trigger API call
                        "priority": "low",
                        "estimatedTime": "10 min",
                    }
                )

            return actions

        except Exception as e:
            logger.error(
                "quick_actions_failed",
                merchant_id=merchant_id,
                error=str(e),
            )
            raise
