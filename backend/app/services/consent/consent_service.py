"""Consent service for managing user consent for cart persistence.

Provides opt-in/opt-out consent tracking with GDPR/CCPA compliance
including consent revocation and logging.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Optional


import redis.asyncio as redis
import structlog

from app.core.config import settings
from app.schemas.consent import ConsentRecord, ConsentStatus
from app.services.cart.cart_retention import CartRetentionService


class ConsentService:
    """Service for managing user consent for cart and session persistence.

    Consent Management:
    1. Track opt-in consent for cart persistence
    2. Store consent preference in Redis
    3. Handle consent withdrawal (forget preferences)
    4. Log consent changes for GDPR/CCPA compliance

    Data Storage:
    - Key: consent:{psid}
    - TTL: 30 days (consent records)

    Data Tier:
    - Voluntary: Consent preference (deletable via "forget my preferences")
    """

    CONSENT_TTL_DAYS = 30  # Consent records kept for 30 days

    def __init__(self, redis_client: Optional[redis.Redis] = None) -> None:
        """Initialize consent service.

        Args:
            redis_client: Redis client instance (creates default if not provided)
        """
        if redis_client is None:
            config = settings()
            redis_url = config.get("REDIS_URL", "redis://localhost:6379/0")
            self.redis = redis.from_url(redis_url, decode_responses=True)
        else:
            self.redis = redis_client

        self.logger = structlog.get_logger(__name__)

    def _get_consent_key(self, psid: str) -> str:
        """Generate Redis key for consent data.

        Args:
            psid: Facebook Page-Scoped ID

        Returns:
            Redis consent key
        """
        return f"consent:{psid}"

    async def get_consent(self, psid: str) -> ConsentStatus:
        """Get consent status for shopper.

        Args:
            psid: Facebook Page-Scoped ID

        Returns:
            ConsentStatus value
        """
        consent_key = self._get_consent_key(psid)
        consent_data = await self.redis.get(consent_key)

        if not consent_data:
            return ConsentStatus.PENDING

        data = json.loads(consent_data)
        return ConsentStatus(data.get("status", ConsentStatus.PENDING.value))

    async def record_consent(self, psid: str, consent_granted: bool) -> dict[str, Any]:
        """Record shopper's consent choice.

        Args:
            psid: Facebook Page-Scoped ID
            consent_granted: True if user opted in, False if opted out

        Returns:
            Consent record dict with timestamp and status
        """
        consent_key = self._get_consent_key(psid)

        consent_data: dict[str, Any] = {
            "status": ConsentStatus.OPTED_IN if consent_granted else ConsentStatus.OPTED_OUT,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "psid": psid,
        }

        # Store consent with 30-day TTL
        ttl_seconds = self.CONSENT_TTL_DAYS * 24 * 60 * 60
        await self.redis.setex(consent_key, ttl_seconds, json.dumps(consent_data))

        # Enable extended 30-day cart retention if granted (Story 2.7)
        if consent_granted:
            retention_service = CartRetentionService(redis_client=self.redis)
            await retention_service.enable_extended_retention(psid)

        self.logger.info(
            "consent_recorded",
            psid=psid,
            consent_granted=consent_granted,
            status=consent_data["status"].value,
        )

        return consent_data

    async def revoke_consent(self, psid: str) -> None:
        """Revoke user consent and clear consent record.

        Args:
            psid: Facebook Page-Scoped ID
        """
        consent_key = self._get_consent_key(psid)

        # Clear consent record
        await self.redis.delete(consent_key)

        self.logger.info("consent_revoked", psid=psid)

    async def can_persist_cart(self, psid: str) -> bool:
        """Check if cart can be persisted for shopper.

        Args:
            psid: Facebook Page-Scoped ID

        Returns:
            True if user has opted in to persistence
        """
        consent_status = await self.get_consent(psid)
        return consent_status == ConsentStatus.OPTED_IN
