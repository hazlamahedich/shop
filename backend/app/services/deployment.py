"""Deployment business logic service.

Handles deployment configuration, merchant key generation, and prerequisite migration.
"""

from __future__ import annotations

import secrets
import string
from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.merchant import Merchant
from app.models.onboarding import PrerequisiteChecklist


class DeploymentService:
    """Service for managing deployment configuration."""

    @staticmethod
    async def generate_merchant_key(db: AsyncSession) -> str:
        """Generate a unique merchant key with collision detection.

        Args:
            db: Database session

        Returns:
            A unique merchant key in format "shop-{random8chars}"
        """
        max_attempts = 10
        for _ in range(max_attempts):
            suffix = ''.join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(8))
            merchant_key = f"shop-{suffix}"

            # Check if key already exists
            result = await db.execute(
                select(Merchant).where(Merchant.merchant_key == merchant_key)
            )
            if result.scalars().first() is None:
                return merchant_key

        # Fallback: use timestamp to ensure uniqueness
        import time
        return f"shop-{secrets.token_hex(4)}-{int(time.time())}"

    @staticmethod
    def generate_secret_key() -> str:
        """Generate a 32-byte SECRET_KEY for production.

        Returns:
            A URL-safe 32-byte random key
        """
        return secrets.token_urlsafe(32)

    @staticmethod
    async def create_merchant(
        db: AsyncSession,
        merchant_key: str,
        platform: str,
        secret_key_hash: Optional[str] = None,
    ) -> Merchant:
        """Create a new merchant record.

        Args:
            db: Database session
            merchant_key: Unique merchant key
            platform: Deployment platform (flyio, railway, render)
            secret_key_hash: Hashed SECRET_KEY (optional)

        Returns:
            Created Merchant instance
        """
        merchant = Merchant(
            merchant_key=merchant_key,
            platform=platform,
            status="pending",
            secret_key_hash=secret_key_hash,
            config={"app_name": f"shop-bot-{merchant_key}"},
        )
        db.add(merchant)
        await db.commit()
        await db.refresh(merchant)
        return merchant

    @staticmethod
    async def migrate_prerequisites(
        db: AsyncSession,
        merchant_id: int,
        prerequisites: dict[str, bool],
    ) -> PrerequisiteChecklist:
        """Migrate prerequisites from localStorage to PostgreSQL.

        Args:
            db: Database session
            merchant_id: ID of the merchant to link prerequisites to
            prerequisites: Dictionary of prerequisite completion states

        Returns:
            Created PrerequisiteChecklist instance

        Raises:
            ValueError: If prerequisites dict is missing required keys
        """
        # Validate prerequisites structure
        required_keys = {"cloudAccount", "facebookAccount", "shopifyAccess", "llmProviderChoice"}
        if not all(key in prerequisites for key in required_keys):
            raise ValueError(
                f"Invalid prerequisites structure. Required keys: {required_keys}, "
                f"got: {set(prerequisites.keys())}"
            )

        # Validate all values are booleans
        for key, value in prerequisites.items():
            if not isinstance(value, bool):
                raise ValueError(f"Prerequisite '{key}' must be boolean, got {type(value).__name__}")

        checklist = PrerequisiteChecklist(
            merchant_id=merchant_id,
            has_cloud_account=prerequisites["cloudAccount"],
            has_facebook_account=prerequisites["facebookAccount"],
            has_shopify_access=prerequisites["shopifyAccess"],
            has_llm_provider_choice=prerequisites["llmProviderChoice"],
            completed_at=datetime.utcnow() if all(prerequisites.values()) else None,
        )
        db.add(checklist)
        await db.commit()
        await db.refresh(checklist)
        return checklist

    @staticmethod
    async def get_merchant_by_key(db: AsyncSession, merchant_key: str) -> Optional[Merchant]:
        """Get a merchant by merchant key.

        Args:
            db: Database session
            merchant_key: Merchant key to look up

        Returns:
            Merchant instance or None if not found
        """
        result = await db.execute(
            select(Merchant).where(Merchant.merchant_key == merchant_key)
        )
        return result.scalars().first()

    @staticmethod
    async def update_merchant_status(
        db: AsyncSession,
        merchant_key: str,
        status: str,
    ) -> Optional[Merchant]:
        """Update merchant status.

        Args:
            db: Database session
            merchant_key: Merchant key to update
            status: New status

        Returns:
            Updated Merchant instance or None if not found
        """
        merchant = await DeploymentService.get_merchant_by_key(db, merchant_key)
        if merchant:
            merchant.status = status
            if status == "active":
                merchant.deployed_at = datetime.utcnow()
            await db.commit()
            await db.refresh(merchant)
        return merchant
