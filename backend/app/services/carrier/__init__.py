"""Carrier detection service module (Story 6.2)."""

from app.services.carrier.carrier_patterns import (
    CARRIER_PATTERNS,
    CarrierPattern,
    CarrierRegion,
    detect_carrier_by_pattern,
    get_sorted_patterns,
    get_tracking_url,
)
from app.services.carrier.shopify_carriers import (
    SHOPIFY_CARRIER_URLS,
    get_shopify_carrier_url,
)

__all__ = [
    "CarrierPattern",
    "CarrierRegion",
    "CARRIER_PATTERNS",
    "SHOPIFY_CARRIER_URLS",
    "detect_carrier_by_pattern",
    "get_shopify_carrier_url",
    "get_sorted_patterns",
    "get_tracking_url",
]
