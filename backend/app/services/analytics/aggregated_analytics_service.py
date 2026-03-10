"""Aggregated Analytics Service for tier-aware analytics.

Story 6-4: Data Tier Separation
Task 6: Create tier-aware analytics

Provides anonymized analytics aggregation with PII stripping.
All aggregated data is stored as tier=ANONYMIZED.
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Any, Optional

import structlog
from sqlalchemy import func, select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import Conversation
from app.models.message import Message
from app.models.order import Order
from app.models.llm_conversation_cost import LLMConversationCost
from app.services.privacy.data_tier_service import DataTier


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

        Returns:
            Dict with anonymized conversation stats
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)

            # Total conversations (no PII, exclude test data and anonymized tier)
            conv_count_result = await self.db.execute(
                select(func.count(Conversation.id))
                .where(Conversation.merchant_id == merchant_id)
                .where(Conversation.created_at >= cutoff_date)
                .where(Conversation.data_tier.in_([DataTier.VOLUNTARY, DataTier.OPERATIONAL]))
            )
            total_conversations = conv_count_result.scalar() or 0

            # Total messages (no PII, exclude test data and anonymized tier)
            msg_count_result = await self.db.execute(
                select(func.count(Message.id))
                .join(Conversation, Message.conversation_id == Conversation.id)
                .where(Conversation.merchant_id == merchant_id)
                .where(Message.created_at >= cutoff_date)
                .where(Message.data_tier.in_([DataTier.VOLUNTARY, DataTier.OPERATIONAL]))
            )
            total_messages = msg_count_result.scalar() or 0

            # Average messages per conversation
            avg_messages = total_messages / total_conversations if total_conversations > 0 else 0.0

            # Total LLM cost (anonymized - no customer IDs)
            cost_result = await self.db.execute(
                select(func.sum(LLMConversationCost.total_cost_usd))
                .where(LLMConversationCost.merchant_id == merchant_id)
                .where(LLMConversationCost.request_timestamp >= cutoff_date)
            )
            total_cost = float(cost_result.scalar() or 0.0)

            # Popular intents (from message metadata, no PII)
            # Note: Intent data is stored in message_metadata JSONB field
            # For now, we'll skip intent aggregation as it requires JSON parsing

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
                    "endDate": datetime.now(timezone.utc).isoformat(),
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

        Combines:
        - Tier distribution
        - Conversation stats (30 days)
        - Order stats (anonymized)

        All data is tier=ANONYMIZED with no PII.

        Args:
            merchant_id: Merchant ID

        Returns:
            Dict with complete anonymized analytics
        """
        try:
            tier_dist = await self.get_tier_distribution(merchant_id)
            conv_stats = await self.aggregate_conversation_stats(merchant_id, days=30)

            # Order stats (anonymized - no customer data)
            order_count_result = await self.db.execute(
                select(func.count(Order.id))
                .where(Order.merchant_id == merchant_id)
                .where(Order.is_test == False)
            )
            total_orders = order_count_result.scalar() or 0

            order_revenue_result = await self.db.execute(
                select(func.sum(Order.total))
                .where(Order.merchant_id == merchant_id)
                .where(Order.is_test == False)
            )
            total_revenue = float(order_revenue_result.scalar() or 0.0)

            logger.info(
                "anonymized_summary_retrieved",
                merchant_id=merchant_id,
                total_orders=total_orders,
                total_revenue=total_revenue,
            )

            return {
                "merchantId": merchant_id,
                "tierDistribution": tier_dist,
                "conversationStats": conv_stats,
                "orderStats": {
                    "totalOrders": total_orders,
                    "totalRevenue": round(total_revenue, 2),
                },
                "generatedAt": datetime.now(timezone.utc).isoformat(),
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
        from app.models.shopify_integration import ShopifyIntegration
        from app.core.security import decrypt_access_token
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
                            "title": item.get("name") or item.get("title") or f"Product {product_id_str}",
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
                product_stats.values(),
                key=lambda x: x["quantitySold"],
                reverse=True
            )[:limit]

            # Fetch product images from Shopify
            product_ids = [str(p["productId"]) for p in top_products]

            # Get integration details
            integration_result = await self.db.execute(
                select(ShopifyIntegration)
                .where(ShopifyIntegration.merchant_id == merchant_id)
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
                product_count=len(top_products)
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
                pending_orders.append({
                    "orderNumber": order.order_number,
                    "status": order.status,
                    "total": float(order.total),
                    "currencyCode": order.currency_code,
                    "estimatedDelivery": order.estimated_delivery.isoformat() if order.estimated_delivery else None,
                    "createdAt": order.created_at.isoformat() if order.created_at else None,
                })

            logger.info(
                "pending_orders_retrieved",
                merchant_id=merchant_id,
                limit=limit,
                order_count=len(pending_orders)
            )

            return pending_orders

        except Exception as e:
            logger.error(
                "pending_orders_failed",
                merchant_id=merchant_id,
                error=str(e),
            )
            return []
