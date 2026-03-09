"""Carrier detection service for tracking URL resolution (Story 6.2).

This service implements priority-based carrier detection:
1. tracking_url from webhook (if set)
2. Merchant's custom carrier config (from database)
3. tracking_company → Shopify carrier mapping
4. Pattern detection (290+ carriers)
5. Fallback: just tracking number (no link)
"""

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.carrier_config import CarrierConfig
from app.services.carrier.carrier_patterns import (
    CarrierPattern,
    detect_carrier_by_pattern,
    get_sorted_patterns,
)
from app.services.carrier.shopify_carriers import get_shopify_carrier_url

if TYPE_CHECKING:
    from app.models.order import Order

logger = logging.getLogger(__name__)


class CarrierService:
    """Service for detecting carriers and generating tracking URLs.

    Priority order:
    1. tracking_url from webhook (if set)
    2. Merchant's custom carrier config (from database)
    3. tracking_company → Shopify carrier mapping
    4. Pattern detection (290+ carriers)
    5. Fallback: just tracking number (no link)
    """

    def __init__(self, db: AsyncSession):
        """Initialize carrier service.

        Args:
            db: Database session for querying custom carrier configs.
        """
        self.db = db

    async def get_tracking_url(
        self,
        order: Order,
    ) -> str | None:
        """Get tracking URL for an order using priority resolution.

        Args:
            order: Order with tracking information.

        Returns:
            Tracking URL if found, None otherwise.
        """
        if not order.tracking_number:
            return None

        if order.tracking_url:
            logger.debug(
                f"Using webhook tracking_url for order {order.order_number}",
            )
            return order.tracking_url

        if order.merchant_id:
            custom_url = await self._get_custom_carrier_url(order)
            if custom_url:
                logger.debug(
                    f"Using custom carrier URL for order {order.order_number}",
                )
                return custom_url

        if order.tracking_company:
            shopify_url = get_shopify_carrier_url(
                order.tracking_company,
                order.tracking_number,
            )
            if shopify_url:
                logger.debug(
                    f"Using Shopify carrier URL for order {order.order_number}",
                )
                return shopify_url

        detected = detect_carrier_by_pattern(order.tracking_number)
        if detected:
            logger.debug(
                f"Detected carrier {detected.name} for order {order.order_number}",
            )
            return detected.url_template.format(
                tracking_number=order.tracking_number,
            )

        logger.debug(
            f"No carrier detected for order {order.order_number}, returning None",
        )
        return None

    async def _get_custom_carrier_url(
        self,
        order: Order,
    ) -> str | None:
        """Get tracking URL from merchant's custom carrier configs.

        Args:
            order: Order with tracking information.

        Returns:
            Tracking URL if custom carrier found, None otherwise.
        """
        if not order.tracking_number:
            return None

        result = await self.db.execute(
            select(CarrierConfig)
            .where(
                CarrierConfig.merchant_id == order.merchant_id,
                CarrierConfig.is_active == True,
            )
            .order_by(CarrierConfig.priority.desc()),
        )
        custom_carriers = result.scalars().all()

        for carrier in custom_carriers:
            if carrier.tracking_number_pattern:
                try:
                    pattern = re.compile(
                        carrier.tracking_number_pattern,
                        re.IGNORECASE,
                    )
                    if pattern.match(order.tracking_number):
                        return carrier.tracking_url_template.format(
                            tracking_number=order.tracking_number,
                        )
                except re.error:
                    logger.warning(
                        f"Invalid regex pattern for custom carrier {carrier.id}: {carrier.tracking_number_pattern}",
                    )
                    continue

        return None

    async def detect_carrier(
        self,
        tracking_number: str,
        merchant_id: int | None = None,
        tracking_company: str | None = None,
    ) -> dict[str, str | None]:
        """Detect carrier and get tracking URL.

        This method is used by the API endpoint to detect carriers.

        Args:
            tracking_number: The tracking number.
            merchant_id: Optional merchant ID for custom carrier lookup.
            tracking_company: Optional carrier name from webhook.

        Returns:
            Dictionary with carrier_name and tracking_url.
        """
        if not tracking_number:
            return {"carrier_name": None, "tracking_url": None}

        if merchant_id:
            custom_result = await self._detect_custom_carrier(
                tracking_number,
                merchant_id,
            )
            if custom_result["carrier_name"]:
                return custom_result

        if tracking_company:
            shopify_url = get_shopify_carrier_url(
                tracking_company,
                tracking_number,
            )
            if shopify_url:
                return {
                    "carrier_name": tracking_company,
                    "tracking_url": shopify_url,
                }

        detected = detect_carrier_by_pattern(tracking_number)
        if detected:
            return {
                "carrier_name": detected.name,
                "tracking_url": detected.url_template.format(
                    tracking_number=tracking_number,
                ),
            }

        return {"carrier_name": None, "tracking_url": None}

    async def _detect_custom_carrier(
        self,
        tracking_number: str,
        merchant_id: int,
    ) -> dict[str, str | None]:
        """Detect carrier from merchant's custom configs.

        Args:
            tracking_number: The tracking number.
            merchant_id: Merchant ID.

        Returns:
            Dictionary with carrier_name and tracking_url.
        """
        result = await self.db.execute(
            select(CarrierConfig)
            .where(
                CarrierConfig.merchant_id == merchant_id,
                CarrierConfig.is_active == True,
            )
            .order_by(CarrierConfig.priority.desc()),
        )
        custom_carriers = result.scalars().all()

        for carrier in custom_carriers:
            if carrier.tracking_number_pattern:
                try:
                    pattern = re.compile(
                        carrier.tracking_number_pattern,
                        re.IGNORECASE,
                    )
                    if pattern.match(tracking_number):
                        return {
                            "carrier_name": carrier.carrier_name,
                            "tracking_url": carrier.tracking_url_template.format(
                                tracking_number=tracking_number,
                            ),
                        }
                except re.error:
                    logger.warning(
                        f"Invalid regex pattern for custom carrier {carrier.id}: {carrier.tracking_number_pattern}",
                    )
                    continue

        return {"carrier_name": None, "tracking_url": None}

    @staticmethod
    def get_supported_carriers() -> list[dict[str, str | int]]:
        """Get list of all supported carriers.

        Returns:
            List of carrier info dictionaries.
        """
        carriers = []
        for pattern in get_sorted_patterns():
            carriers.append(
                {
                    "name": pattern.name,
                    "region": pattern.region.value,
                    "priority": pattern.priority,
                    "url_template": pattern.url_template,
                },
            )
        return carriers

    @staticmethod
    def get_carriers_by_region(region: str) -> list[dict[str, str | int]]:
        """Get carriers filtered by region.

        Args:
            region: Region code (e.g., "us", "uk", "ph").

        Returns:
            List of carrier info dictionaries for the region.
        """
        carriers = []
        for pattern in get_sorted_patterns():
            if pattern.region.value == region.lower():
                carriers.append(
                    {
                        "name": pattern.name,
                        "region": pattern.region.value,
                        "priority": pattern.priority,
                        "url_template": pattern.url_template,
                    },
                )
        return carriers
