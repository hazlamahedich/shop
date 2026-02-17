"""Order polling service for Shopify Admin API.

Story 4-4 Task 2 & 3: Polling with distributed locking, order comparison, and processing

Features:
- 5-minute polling interval for orders <24 hours old
- Redis-based distributed locking (10-min TTL)
- Sequential merchant polling with 100ms delay
- Order comparison by shopify_updated_at timestamp
- Reuses ShopifyOrderProcessor for processing
- Shipping notification integration for newly fulfilled orders
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import Enum

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order import Order
from app.models.shopify_integration import ShopifyIntegration
from app.services.shopify.admin_client import (
    ShopifyAdminClient,
    ShopifyAPIError,
    ShopifyAuthError,
    ShopifyRateLimitError,
)
from app.services.shopify.order_processor import (
    ShopifyOrderProcessor,
    parse_shopify_order,
    resolve_customer_psid,
    upsert_order,
)

logger = structlog.get_logger(__name__)


class PollingStatus(str, Enum):
    """Status of a polling attempt."""

    SUCCESS = "success"
    SKIPPED_NO_INTEGRATION = "skipped_no_integration"
    SKIPPED_LOCK_EXISTS = "skipped_lock_exists"
    SKIPPED_EMPTY_RESPONSE = "skipped_empty_response"
    ERROR_API = "error_api"
    ERROR_AUTH = "error_auth"
    ERROR_RATE_LIMITED = "error_rate_limited"
    ERROR_DATABASE = "error_database"
    ERROR_UNKNOWN = "error_unknown"


@dataclass
class PollingResult:
    """Result of a polling attempt for a single merchant."""

    status: PollingStatus
    merchant_id: int
    orders_polled: int = 0
    orders_created: int = 0
    orders_updated: int = 0
    notifications_sent: int = 0
    error_code: int | None = None
    error_message: str | None = None
    duration_ms: float | None = None


@dataclass
class MerchantPollingStatus:
    """Per-merchant polling status."""

    last_poll: datetime | None = None
    status: str = "unknown"
    error_count: int = 0


class OrderPollingService:
    """Service for polling Shopify for order updates.

    Polls Shopify Admin API every 5 minutes for orders updated in the last
    5 minutes. Uses distributed locking to prevent concurrent polling in
    multi-instance deployments.
    """

    LOCK_TTL_SECONDS = 600
    POLLING_INTERVAL_MINUTES = 5
    ORDER_AGE_LIMIT_HOURS = 24

    def __init__(self, redis_client=None) -> None:
        """Initialize polling service.

        Args:
            redis_client: Async Redis client for distributed locking
        """
        self.redis = redis_client
        self.order_processor = ShopifyOrderProcessor()

        self._last_poll_timestamp: datetime | None = None
        self._total_orders_synced: int = 0
        self._errors_last_hour: int = 0
        self._errors_this_hour: list[datetime] = []
        self._merchant_status: dict[int, MerchantPollingStatus] = {}
        self._scheduler_running: bool = False

    def set_scheduler_running(self, running: bool) -> None:
        self._scheduler_running = running

    async def acquire_lock(self, merchant_id: int) -> bool:
        """Acquire distributed lock for merchant polling.

        Args:
            merchant_id: Merchant ID to lock

        Returns:
            True if lock acquired, False if already locked
        """
        if self.redis is None:
            logger.warning(
                "polling_lock_redis_unavailable",
                merchant_id=merchant_id,
                degraded_mode=True,
            )
            return True

        lock_key = f"polling_lock:{merchant_id}"

        try:
            acquired = await self.redis.set(lock_key, "1", nx=True, ex=self.LOCK_TTL_SECONDS)
            if acquired:
                logger.debug(
                    "polling_lock_acquired",
                    merchant_id=merchant_id,
                    lock_ttl_seconds=self.LOCK_TTL_SECONDS,
                )
                return True
            else:
                logger.info(
                    "polling_lock_exists_skipping",
                    merchant_id=merchant_id,
                    lock_key=lock_key,
                )
                return False
        except Exception as e:
            logger.warning(
                "polling_lock_error_degraded_mode",
                merchant_id=merchant_id,
                error=str(e),
            )
            return True

    async def release_lock(self, merchant_id: int) -> None:
        """Release distributed lock after polling.

        Args:
            merchant_id: Merchant ID to unlock
        """
        if self.redis is None:
            return

        lock_key = f"polling_lock:{merchant_id}"

        try:
            await self.redis.delete(lock_key)
            logger.debug(
                "polling_lock_released",
                merchant_id=merchant_id,
            )
        except Exception as e:
            logger.warning(
                "polling_lock_release_failed",
                merchant_id=merchant_id,
                error=str(e),
            )

    def filter_orders_within_24_hours(self, orders: list[dict]) -> list[dict]:
        """Filter orders to only those <24 hours old.

        Args:
            orders: List of order dicts from Shopify API

        Returns:
            Filtered list of orders created within last 24 hours
        """
        cutoff = datetime.now(UTC) - timedelta(hours=self.ORDER_AGE_LIMIT_HOURS)
        filtered = []

        for order in orders:
            created_at_str = order.get("created_at")
            if not created_at_str:
                continue

            try:
                if created_at_str.endswith("Z"):
                    created_at_str = created_at_str[:-1] + "+00:00"
                created_at = datetime.fromisoformat(created_at_str)

                if created_at > cutoff:
                    filtered.append(order)
            except (ValueError, TypeError):
                continue

        return filtered

    async def _get_shopify_credentials(
        self,
        merchant_id: int,
        db: AsyncSession,
    ) -> dict[str, str] | None:
        """Get Shopify credentials for a merchant.

        Args:
            merchant_id: Merchant ID
            db: Database session

        Returns:
            Dict with shop_domain and admin_token, or None if not configured
        """
        try:
            result = await db.execute(
                select(ShopifyIntegration).where(ShopifyIntegration.merchant_id == merchant_id)
            )
            integration = result.scalar_one_or_none()

            if not integration:
                logger.debug(
                    "polling_no_integration",
                    merchant_id=merchant_id,
                )
                return None

            if not integration.admin_api_verified:
                logger.debug(
                    "polling_integration_not_verified",
                    merchant_id=merchant_id,
                )
                return None

            from app.core.security import decrypt_access_token

            admin_token = decrypt_access_token(integration.admin_token_encrypted)

            return {
                "shop_domain": integration.shop_domain,
                "admin_token": admin_token,
            }
        except Exception as e:
            logger.error(
                "polling_credentials_error",
                merchant_id=merchant_id,
                error=str(e),
                error_code=7054,
            )
            return None

    async def _fetch_orders_from_shopify(
        self,
        shop_domain: str,
        admin_token: str,
    ) -> list[dict]:
        """Fetch recently updated orders from Shopify Admin API.

        Args:
            shop_domain: Shopify shop domain
            admin_token: Admin API access token

        Returns:
            List of order dicts
        """
        async with ShopifyAdminClient(
            shop_domain=shop_domain,
            access_token=admin_token,
        ) as client:
            orders = await client.get_orders_updated_since(minutes=self.POLLING_INTERVAL_MINUTES)
            return orders

    async def _get_existing_order(
        self,
        shopify_order_id: str,
        db: AsyncSession,
    ) -> Order | None:
        """Get existing order from database.

        Args:
            shopify_order_id: Shopify order GID
            db: Database session

        Returns:
            Order if found, None otherwise
        """
        try:
            result = await db.execute(
                select(Order).where(Order.shopify_order_id == shopify_order_id)
            )
            return result.scalars().first()
        except Exception as e:
            logger.warning(
                "polling_order_lookup_failed",
                shopify_order_id=shopify_order_id,
                error=str(e),
            )
            return None

    async def compare_and_identify_updates(
        self,
        shopify_orders: list[dict],
        db: AsyncSession,
    ) -> dict[str, list]:
        """Compare Shopify orders with local DB to identify updates.

        Args:
            shopify_orders: Orders from Shopify API
            db: Database session

        Returns:
            Dict with 'new_orders' and 'updated_orders' lists
        """
        new_orders = []
        updated_orders = []

        for shopify_order in shopify_orders:
            order_id = shopify_order.get("id")
            if not order_id:
                continue

            shopify_order_gid = f"gid://shopify/Order/{order_id}"
            existing_order = await self._get_existing_order(shopify_order_gid, db)

            if not existing_order:
                new_orders.append(shopify_order)
                continue

            incoming_updated_at = self._parse_timestamp(shopify_order.get("updated_at"))

            if (
                incoming_updated_at
                and existing_order.shopify_updated_at
                and incoming_updated_at > existing_order.shopify_updated_at
            ):
                updated_orders.append((existing_order, shopify_order))

        return {
            "new_orders": new_orders,
            "updated_orders": updated_orders,
        }

    def _parse_timestamp(self, ts_str: str | None) -> datetime | None:
        """Parse ISO timestamp string."""
        if not ts_str:
            return None
        try:
            if ts_str.endswith("Z"):
                ts_str = ts_str[:-1] + "+00:00"
            return datetime.fromisoformat(ts_str).replace(tzinfo=None)
        except (ValueError, TypeError):
            return None

    def is_newly_fulfilled(self, existing_order: Order, shopify_order: dict) -> bool:
        """Check if order was just fulfilled.

        Args:
            existing_order: Existing order from DB
            shopify_order: Order data from Shopify

        Returns:
            True if order changed from not fulfilled to fulfilled
        """
        existing_fulfillment = existing_order.fulfillment_status
        new_fulfillment = shopify_order.get("fulfillment_status")

        was_not_fulfilled = existing_fulfillment is None or existing_fulfillment == "null"
        now_fulfilled = new_fulfillment is not None and new_fulfillment != "null"

        return was_not_fulfilled and now_fulfilled

    async def _process_orders(
        self,
        merchant_id: int,
        new_orders: list[dict],
        updated_orders: list[tuple],
        db: AsyncSession,
    ) -> dict[str, int]:
        """Process new and updated orders.

        Args:
            merchant_id: Merchant ID
            new_orders: New orders to create
            updated_orders: Orders to update (existing, shopify_data tuples)
            db: Database session

        Returns:
            Dict with counts: created, updated, notifications
        """
        created = 0
        updated = 0
        notifications = 0

        for shopify_order in new_orders:
            try:
                order_data = parse_shopify_order(shopify_order)
                platform_sender_id = await resolve_customer_psid(shopify_order, db, merchant_id)
                order = await upsert_order(db, order_data, merchant_id, platform_sender_id)
                created += 1

                logger.info(
                    "polling_order_created",
                    merchant_id=merchant_id,
                    shopify_order_id=order.shopify_order_id,
                )
            except Exception as e:
                logger.error(
                    "polling_order_create_failed",
                    merchant_id=merchant_id,
                    shopify_order_id=shopify_order.get("id"),
                    error=str(e),
                )

        for existing_order, shopify_order in updated_orders:
            try:
                was_newly_fulfilled = self.is_newly_fulfilled(existing_order, shopify_order)

                order_data = parse_shopify_order(shopify_order)
                platform_sender_id = await resolve_customer_psid(shopify_order, db, merchant_id)
                order = await upsert_order(db, order_data, merchant_id, platform_sender_id)
                updated += 1

                if was_newly_fulfilled and order.tracking_number:
                    try:
                        from app.services.shipping_notification.service import (
                            ShippingNotificationService,
                        )

                        notification_service = ShippingNotificationService()
                        result = await notification_service.send_shipping_notification(order, db)
                        if result.status.value == "success":
                            notifications += 1
                            logger.info(
                                "polling_notification_sent",
                                merchant_id=merchant_id,
                                order_id=order.id,
                            )
                    except Exception as e:
                        logger.warning(
                            "polling_notification_failed",
                            merchant_id=merchant_id,
                            order_id=order.id,
                            error=str(e),
                        )

                logger.info(
                    "polling_order_updated",
                    merchant_id=merchant_id,
                    shopify_order_id=order.shopify_order_id,
                )
            except Exception as e:
                logger.error(
                    "polling_order_update_failed",
                    merchant_id=merchant_id,
                    shopify_order_id=shopify_order.get("id"),
                    error=str(e),
                )

        return {
            "created": created,
            "updated": updated,
            "notifications": notifications,
        }

    async def poll_recent_orders(
        self,
        merchant_id: int,
        db: AsyncSession,
    ) -> PollingResult:
        """Poll Shopify for recent order updates for a single merchant.

        Args:
            merchant_id: Merchant ID to poll
            db: Database session

        Returns:
            PollingResult with status and counts
        """
        start_time = datetime.now(UTC)

        try:
            credentials = await self._get_shopify_credentials(merchant_id, db)
            if not credentials:
                return PollingResult(
                    status=PollingStatus.SKIPPED_NO_INTEGRATION,
                    merchant_id=merchant_id,
                )

            lock_acquired = await self.acquire_lock(merchant_id)
            if not lock_acquired:
                return PollingResult(
                    status=PollingStatus.SKIPPED_LOCK_EXISTS,
                    merchant_id=merchant_id,
                )

            try:
                shopify_orders = await self._fetch_orders_from_shopify(
                    credentials["shop_domain"],
                    credentials["admin_token"],
                )

                filtered_orders = self.filter_orders_within_24_hours(shopify_orders)

                if not filtered_orders:
                    logger.info(
                        "polling_no_orders",
                        merchant_id=merchant_id,
                        raw_count=len(shopify_orders),
                        filtered_count=0,
                    )
                    return PollingResult(
                        status=PollingStatus.SKIPPED_EMPTY_RESPONSE,
                        merchant_id=merchant_id,
                        orders_polled=len(shopify_orders),
                    )

                updates = await self.compare_and_identify_updates(filtered_orders, db)

                process_result = await self._process_orders(
                    merchant_id,
                    updates["new_orders"],
                    updates["updated_orders"],
                    db,
                )

                self._last_poll_timestamp = datetime.now(UTC)
                self._total_orders_synced += process_result["created"] + process_result["updated"]
                self._update_merchant_status(merchant_id, "healthy")

                duration_ms = (datetime.now(UTC) - start_time).total_seconds() * 1000

                logger.info(
                    "polling_cycle_complete",
                    merchant_id=merchant_id,
                    orders_polled=len(filtered_orders),
                    orders_created=process_result["created"],
                    orders_updated=process_result["updated"],
                    notifications_sent=process_result["notifications"],
                    duration_ms=round(duration_ms, 2),
                )

                return PollingResult(
                    status=PollingStatus.SUCCESS,
                    merchant_id=merchant_id,
                    orders_polled=len(filtered_orders),
                    orders_created=process_result["created"],
                    orders_updated=process_result["updated"],
                    notifications_sent=process_result["notifications"],
                    duration_ms=duration_ms,
                )

            finally:
                await self.release_lock(merchant_id)

        except ShopifyAuthError:
            self._record_error()
            self._update_merchant_status(merchant_id, "auth_error")
            logger.error(
                "polling_auth_failed",
                merchant_id=merchant_id,
                error_code=7052,
            )
            return PollingResult(
                status=PollingStatus.ERROR_AUTH,
                merchant_id=merchant_id,
                error_code=7052,
                error_message="Shopify authentication failed",
            )

        except ShopifyRateLimitError as e:
            self._record_error()
            self._update_merchant_status(merchant_id, "rate_limited")
            logger.warning(
                "polling_rate_limited",
                merchant_id=merchant_id,
                retry_after=e.retry_after,
                error_code=7051,
            )
            return PollingResult(
                status=PollingStatus.ERROR_RATE_LIMITED,
                merchant_id=merchant_id,
                error_code=7051,
                error_message=f"Rate limited, retry after {e.retry_after}s",
            )

        except ShopifyAPIError as e:
            self._record_error()
            self._update_merchant_status(merchant_id, "api_error")
            logger.error(
                "polling_api_error",
                merchant_id=merchant_id,
                error=str(e),
                error_code=7050,
            )
            return PollingResult(
                status=PollingStatus.ERROR_API,
                merchant_id=merchant_id,
                error_code=7050,
                error_message=str(e),
            )

        except Exception as e:
            self._record_error()
            self._update_merchant_status(merchant_id, "error")
            logger.error(
                "polling_unknown_error",
                merchant_id=merchant_id,
                error=str(e),
                error_code=7050,
            )
            return PollingResult(
                status=PollingStatus.ERROR_UNKNOWN,
                merchant_id=merchant_id,
                error_code=7050,
                error_message=str(e),
            )

    async def poll_all_merchants(
        self,
        merchant_ids: list[int],
        db: AsyncSession,
        delay_between_merchants: float = 0.1,
    ) -> list[PollingResult]:
        """Poll all merchants sequentially with delay between each.

        Args:
            merchant_ids: List of merchant IDs to poll
            db: Database session
            delay_between_merchants: Delay in seconds between merchants (default: 100ms)

        Returns:
            List of PollingResults for each merchant
        """
        logger.info(
            "polling_cycle_started",
            merchant_count=len(merchant_ids),
        )

        results = []

        for merchant_id in merchant_ids:
            try:
                result = await self.poll_recent_orders(merchant_id, db)
                results.append(result)
            except Exception as e:
                logger.error(
                    "polling_merchant_unexpected_error",
                    merchant_id=merchant_id,
                    error=str(e),
                )
                results.append(
                    PollingResult(
                        status=PollingStatus.ERROR_UNKNOWN,
                        merchant_id=merchant_id,
                        error_message=str(e),
                    )
                )

            if delay_between_merchants > 0:
                await asyncio.sleep(delay_between_merchants)

        success_count = sum(1 for r in results if r.status == PollingStatus.SUCCESS)
        logger.info(
            "polling_cycle_all_complete",
            total_merchants=len(merchant_ids),
            success_count=success_count,
        )

        return results

    def _record_error(self) -> None:
        """Record an error for health tracking."""
        now = datetime.now(UTC)
        hour_ago = now - timedelta(hours=1)

        self._errors_this_hour = [t for t in self._errors_this_hour if t > hour_ago]
        self._errors_this_hour.append(now)
        self._errors_last_hour = len(self._errors_this_hour)

    def _update_merchant_status(self, merchant_id: int, status: str) -> None:
        """Update per-merchant polling status."""
        if merchant_id not in self._merchant_status:
            self._merchant_status[merchant_id] = MerchantPollingStatus()

        self._merchant_status[merchant_id].last_poll = datetime.now(UTC)
        self._merchant_status[merchant_id].status = status

        if status != "healthy":
            self._merchant_status[merchant_id].error_count += 1

    def get_health_status(self) -> dict:
        """Get polling service health status.

        Returns:
            Dict with health status information
        """
        merchant_status_list = []
        for merchant_id, status in self._merchant_status.items():
            merchant_status_list.append(
                {
                    "merchant_id": merchant_id,
                    "last_poll": status.last_poll.isoformat() if status.last_poll else None,
                    "status": status.status,
                }
            )

        return {
            "scheduler_running": self._scheduler_running,
            "last_poll_timestamp": (
                self._last_poll_timestamp.isoformat() if self._last_poll_timestamp else None
            ),
            "merchants_polled": len(self._merchant_status),
            "total_orders_synced": self._total_orders_synced,
            "errors_last_hour": self._errors_last_hour,
            "merchant_status": merchant_status_list,
        }
