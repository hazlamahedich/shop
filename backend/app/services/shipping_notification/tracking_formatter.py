"""Tracking link formatter for shipping notifications.

Story 4-3 AC5: Tracking link formatting

Detects carriers from tracking number format and generates tracking URLs.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

import structlog

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
    def detect_carrier(tracking_number: str) -> Optional[CarrierInfo]:
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
        tracking_number: Optional[str],
        tracking_url: Optional[str] = None,
    ) -> str:
        """Format the tracking portion of the shipping notification.

        AC5: Include tracking number link to carrier website

        Args:
            order_number: The order number for display
            tracking_number: The tracking number
            tracking_url: Optional tracking URL (takes precedence)

        Returns:
            Formatted message string
        """
        if not tracking_number:
            logger.warning(
                "shipping_no_tracking_info",
                order_number=order_number,
                error_code=7042,
            )
            return f"Your order #{order_number} has been shipped."

        if tracking_url:
            return (
                f"Great news! Your order #{order_number} has been shipped. \U0001f4e6\n\n"
                f"Tracking: {tracking_url}\n\n"
                f'You can also check your order status anytime by typing "Where\'s my order?"'
            )

        carrier_info = TrackingFormatter.detect_carrier(tracking_number)
        if carrier_info:
            return (
                f"Great news! Your order #{order_number} has been shipped. \U0001f4e6\n\n"
                f"Tracking ({carrier_info.name}): {carrier_info.tracking_url}\n\n"
                f'You can also check your order status anytime by typing "Where\'s my order?"'
            )

        return (
            f"Great news! Your order #{order_number} has been shipped. \U0001f4e6\n\n"
            f"Tracking number: {tracking_number}\n\n"
            f'You can also check your order status anytime by typing "Where\'s my order?"'
        )

    @staticmethod
    def get_tracking_link(
        tracking_number: str,
        tracking_url: Optional[str] = None,
    ) -> Optional[str]:
        """Get the tracking URL for a tracking number.

        Args:
            tracking_number: The tracking number
            tracking_url: Optional tracking URL (takes precedence)

        Returns:
            Tracking URL or None if cannot determine
        """
        if tracking_url:
            return tracking_url

        carrier_info = TrackingFormatter.detect_carrier(tracking_number)
        if carrier_info:
            return carrier_info.tracking_url

        return None
