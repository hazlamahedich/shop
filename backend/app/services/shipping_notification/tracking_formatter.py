"""Tracking link formatter for shipping notifications.

Story 4-3 AC5: Tracking link formatting
Story 5-12: Bot Personality Consistency - Task 3.3
Story 6.2: International carrier support

Detects carriers from tracking number format and generates tracking URLs.
Supports 290+ international carriers with priority-based detection.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

import structlog

from app.models.merchant import PersonalityType
from app.services.carrier.carrier_patterns import detect_carrier_by_pattern
from app.services.carrier.shopify_carriers import get_shopify_carrier_url
from app.services.personality.response_formatter import PersonalityAwareResponseFormatter

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.models.order import Order

logger = structlog.get_logger(__name__)


@dataclass
class CarrierInfo:
    """Carrier information for tracking."""

    name: str
    tracking_url: str


CARRIER_PATTERNS = {
    "UPS": {
        "pattern": r"^1Z[A-Z0-9]{16}$",
        "url_template": "https://www.ups.com/track?tracknum={tracking_number}",
    },
    "FedEx": {
        "pattern": r"^\d{12}$",
        "url_template": "https://www.fedex.com/fedextrack/?trknbr={tracking_number}",
    },
    "FedEx_14": {
        "pattern": r"^\d{14}$",
        "url_template": "https://www.fedex.com/fedextrack/?trknbr={tracking_number}",
    },
    "FedEx_15": {
        "pattern": r"^\d{15}$",
        "url_template": "https://www.fedex.com/fedextrack/?trknbr={tracking_number}",
    },
    "USPS": {
        "pattern": r"^(94|93|92|91)\d{20}$",
        "url_template": "https://tools.usps.com/go/TrackConfirmAction?tLabels={tracking_number}",
    },
    "USPS_22": {
        "pattern": r"^\d{22}$",
        "url_template": "https://tools.usps.com/go/TrackConfirmAction?tLabels={tracking_number}",
    },
    "DHL": {
        "pattern": r"^\d{10}$",
        "url_template": "https://www.dhl.com/us-en/home/tracking/tracking-parcel.html?submit=1&tracking-id={tracking_number}",
    },
    "DHL_Express": {
        "pattern": r"^[A-Z]{3}\d{9}$",
        "url_template": "https://www.dhl.com/us-en/home/tracking/tracking-parcel.html?submit=1&tracking-id={tracking_number}",
    },
    "CanadaPost": {
        "pattern": r"^00\d{14}$",
        "url_template": "https://www.canadapost-postescanada.ca/track-reperage/en#/resultList?searchFor={tracking_number}",
    },
    "RoyalMail": {
        "pattern": r"^[A-Z]{2}\d{9}GB$",
        "url_template": "https://www.royalmail.com/track-your-item#/tracking-results/{tracking_number}",
    },
}


class TrackingFormatter:
    """Format tracking information for shipping notifications.

    Detects carrier from tracking number format and generates tracking URLs.
    Falls back gracefully for unknown carriers.
    """

    @staticmethod
    def detect_carrier(tracking_number: str) -> CarrierInfo | None:
        """Detect carrier from tracking number format.

        Args:
            tracking_number: The tracking number to analyze

        Returns:
            CarrierInfo if carrier detected, None otherwise
        """
        for carrier_name, config in CARRIER_PATTERNS.items():
            pattern = config["pattern"]
            if re.match(pattern, tracking_number.upper()):
                display_name = carrier_name.split("_")[0]
                return CarrierInfo(
                    name=display_name,
                    tracking_url=config["url_template"].format(tracking_number=tracking_number),
                )

        logger.info(
            "shipping_carrier_unknown",
            tracking_number_prefix=tracking_number[:4]
            if len(tracking_number) >= 4
            else tracking_number,
            tracking_number_length=len(tracking_number),
        )
        return None

    @staticmethod
    def format_tracking_message(
        order_number: str,
        tracking_number: str | None,
        tracking_url: str | None = None,
        personality: PersonalityType = PersonalityType.FRIENDLY,
        tracking_company: str | None = None,
    ) -> str:
        """Format the tracking portion of the shipping notification.

        AC5: Include tracking number link to carrier website
        Story 5-12: Uses PersonalityAwareResponseFormatter for personality-based messages.
        Story 6.2: Supports tracking_company for better carrier detection.

        Args:
            order_number: The order number for display
            tracking_number: The tracking number
            tracking_url: Optional tracking URL (takes precedence)
            personality: Merchant's personality type for message formatting
            tracking_company: Optional carrier name from webhook

        Returns:
            Formatted message string
        """
        if not tracking_number:
            logger.warning(
                "shipping_no_tracking_info",
                order_number=order_number,
                error_code=7042,
            )
            return PersonalityAwareResponseFormatter.format_response(
                "order_tracking",
                "found_shipped",
                personality,
                order_details=f"Order #{order_number}",
                tracking_info="Tracking information not yet available",
            )

        tracking_link = TrackingFormatter.get_tracking_link(
            tracking_number,
            tracking_url,
            tracking_company,
        )

        if tracking_company:
            carrier_name = tracking_company
        else:
            carrier_info = TrackingFormatter.detect_carrier(tracking_number)
            carrier_name = carrier_info.name if carrier_info else None

        if tracking_link:
            tracking_info = (
                f"Tracking{' (' + carrier_name + ')' if carrier_name else ''}: {tracking_link}"
            )
        else:
            tracking_info = f"Tracking number: {tracking_number}"

        return PersonalityAwareResponseFormatter.format_response(
            "order_tracking",
            "found_shipped",
            personality,
            order_details=f"Order #{order_number}",
            tracking_info=tracking_info,
        )

    @staticmethod
    def get_tracking_link(
        tracking_number: str,
        tracking_url: str | None = None,
        tracking_company: str | None = None,
    ) -> str | None:
        """Get the tracking URL for a tracking number.

        Priority order:
        1. tracking_url parameter (from webhook)
        2. Shopify carrier mapping (if tracking_company provided)
        3. Pattern detection (290+ carriers)

        Args:
            tracking_number: The tracking number
            tracking_url: Optional tracking URL (takes precedence)
            tracking_company: Optional carrier name from webhook

        Returns:
            Tracking URL or None if cannot determine
        """
        if tracking_url:
            return tracking_url

        if tracking_company:
            shopify_url = get_shopify_carrier_url(tracking_company, tracking_number)
            if shopify_url:
                return shopify_url

        detected = detect_carrier_by_pattern(tracking_number)
        if detected:
            return detected.url_template.format(tracking_number=tracking_number)

        carrier_info = TrackingFormatter.detect_carrier(tracking_number)
        if carrier_info:
            return carrier_info.tracking_url

        return None

    @staticmethod
    async def get_tracking_link_with_custom_carriers(
        db: AsyncSession,
        order: Order,
    ) -> str | None:
        """Get tracking URL with support for merchant's custom carriers.

        Priority order:
        1. tracking_url from webhook (if set on order)
        2. Merchant's custom carrier config (from database)
        3. Shopify carrier mapping (if tracking_company provided)
        4. Pattern detection (290+ carriers)
        5. Fallback: None (no link)

        Args:
            db: Database session for querying custom carrier configs
            order: Order with tracking information

        Returns:
            Tracking URL or None if cannot determine
        """
        if not order.tracking_number:
            return None

        if order.tracking_url:
            logger.debug(
                "Using webhook tracking_url",
                order_number=order.order_number,
            )
            return order.tracking_url

        from sqlalchemy import select

        from app.models.carrier_config import CarrierConfig

        if order.merchant_id:
            result = await db.execute(
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
                            logger.debug(
                                "Using custom carrier URL",
                                order_number=order.order_number,
                                carrier_name=carrier.carrier_name,
                            )
                            return carrier.tracking_url_template.format(
                                tracking_number=order.tracking_number,
                            )
                    except re.error:
                        logger.warning(
                            "Invalid regex pattern for custom carrier",
                            carrier_id=carrier.id,
                            pattern=carrier.tracking_number_pattern,
                        )
                        continue

        if order.tracking_company:
            shopify_url = get_shopify_carrier_url(
                order.tracking_company,
                order.tracking_number,
            )
            if shopify_url:
                logger.debug(
                    "Using Shopify carrier URL",
                    order_number=order.order_number,
                    carrier_name=order.tracking_company,
                )
                return shopify_url

        detected = detect_carrier_by_pattern(order.tracking_number)
        if detected:
            logger.debug(
                "Detected carrier via pattern",
                order_number=order.order_number,
                carrier_name=detected.name,
            )
            return detected.url_template.format(
                tracking_number=order.tracking_number,
            )

        logger.debug(
            "No carrier detected",
            order_number=order.order_number,
        )
        return None
