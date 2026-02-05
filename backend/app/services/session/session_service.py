"""Session service for managing shopper session persistence.

Provides activity tracking, returning shopper detection,
and voluntary data clearing with GDPR/CCPA compliance.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Optional

import redis
import structlog

from app.core.config import settings
from app.services.consent import ConsentService


class SessionService:
    """Service for managing shopper session persistence.

    Session Management:
    1. Store cart data with TTL-based expiry
    2. Track session activity for expiry calculation
    3. Restore sessions on return visits
    4. Clear sessions on forget preferences

    Data Storage:
    - Cart: cart:{psid} with 24-hour TTL (from Story 2.5)
    - Consent: consent:{psid} with 30-day TTL
    - Activity: last_activity:{psid} with 24-hour TTL

    Data Tier:
    - Voluntary: Cart, consent, context, activity (deletable)
    - Operational: Order references, active checkout (not deletable)
    """

    CART_TTL_HOURS = 24
    ACTIVITY_TTL_HOURS = 24

    def __init__(
        self,
        redis_client: Optional[redis.Redis] = None,
        consent_service: Optional[ConsentService] = None
    ) -> None:
        """Initialize session service.

        Args:
            redis_client: Redis client instance
            consent_service: Consent service instance
        """
        if redis_client is None:
            import redis
            config = settings()
            redis_url = config.get("REDIS_URL", "redis://localhost:6379/0")
            self.redis = redis.from_url(redis_url, decode_responses=True)
        else:
            self.redis = redis_client

        self.consent_service = consent_service or ConsentService(self.redis)
        self.logger = structlog.get_logger(__name__)

    def _get_activity_key(self, psid: str) -> str:
        """Generate Redis key for activity tracking.

        Args:
            psid: Facebook Page-Scoped ID

        Returns:
            Redis activity key
        """
        return f"last_activity:{psid}"

    async def update_activity(self, psid: str) -> None:
        """Update last activity timestamp for shopper.

        Args:
            psid: Facebook Page-Scoped ID
        """
        activity_key = self._get_activity_key(psid)
        ttl_seconds = self.ACTIVITY_TTL_HOURS * 60 * 60

        activity_data: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "psid": psid
        }

        self.redis.setex(
            activity_key,
            ttl_seconds,
            json.dumps(activity_data)
        )

        self.logger.info(
            "activity_updated",
            psid=psid
        )

    async def get_last_activity(self, psid: str) -> Optional[datetime]:
        """Get last activity timestamp for shopper.

        Args:
            psid: Facebook Page-Scoped ID

        Returns:
            Datetime of last activity or None if not found
        """
        activity_key = self._get_activity_key(psid)
        activity_data = self.redis.get(activity_key)

        if not activity_data:
            return None

        data = json.loads(activity_data)
        return datetime.fromisoformat(data["timestamp"])

    async def is_returning_shopper(self, psid: str) -> bool:
        """Check if shopper is returning (has existing cart and consent).

        Args:
            psid: Facebook Page-Scoped ID

        Returns:
            True if shopper has existing cart and consent
        """
        # Check for existing cart
        cart_key = f"cart:{psid}"
        has_cart = self.redis.exists(cart_key) > 0

        # Check for consent (not pending)
        consent_status = await self.consent_service.get_consent(psid)
        has_consent = consent_status != "pending"

        return has_cart and has_consent

    async def get_cart_item_count(self, psid: str) -> int:
        """Get number of items in shopper's cart.

        Args:
            psid: Facebook Page-Scoped ID

        Returns:
            Number of items in cart (count of distinct items, not quantity)
        """
        cart_key = f"cart:{psid}"
        cart_data = self.redis.get(cart_key)

        if not cart_data:
            return 0

        cart_dict = json.loads(cart_data)
        items = cart_dict.get("items", [])
        return len(items)

    async def clear_session(self, psid: str) -> None:
        """Clear all session data for shopper (voluntary data only).

        Args:
            psid: Facebook Page-Scoped ID

        Note:
            This clears voluntary data only (cart, consent, context).
            Operational data (order references) is NOT cleared.

        Data Tier Separation:
            - Voluntary (cleared): cart, consent, context, activity
            - Operational (preserved): order_ref, active checkout
        """
        # Clear cart
        cart_key = f"cart:{psid}"
        self.redis.delete(cart_key)

        # Clear consent
        await self.consent_service.revoke_consent(psid)

        # Clear activity
        activity_key = self._get_activity_key(psid)
        self.redis.delete(activity_key)

        # Clear conversation context (if exists)
        context_key = f"context:{psid}"
        self.redis.delete(context_key)

        self.logger.info(
            "session_cleared",
            psid=psid,
            voluntary_data_cleared=True
        )
