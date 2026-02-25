"""Customer Lookup Service (Story 4-13).

Provides customer profile management and cross-device recognition.
Enables personalized greetings and order lookup by email.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Optional

import structlog
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import APIError, ErrorCode
from app.models.customer_profile import CustomerProfile
from app.models.order import Order

logger = structlog.get_logger(__name__)


class CustomerLookupService:
    """Service for customer profile management and cross-device recognition.

    Features:
    - Upsert customer profiles on order
    - Find customers by email or phone
    - Track order statistics (total_orders, total_spent)
    - Support personalized greetings
    """

    def __init__(self) -> None:
        """Initialize the customer lookup service."""
        pass

    async def upsert_customer_profile(
        self,
        db: AsyncSession,
        merchant_id: int,
        email: str,
        phone: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        order_total: Optional[Decimal] = None,
    ) -> CustomerProfile:
        """Create or update a customer profile.

        Uses INSERT ... ON CONFLICT for upsert pattern.

        Args:
            db: Database session
            merchant_id: Merchant ID
            email: Customer email (primary identifier)
            phone: Customer phone (optional)
            first_name: Customer first name (optional)
            last_name: Customer last name (optional)
            order_total: Order total to add to total_spent (optional)

        Returns:
            CustomerProfile instance
        """
        now = datetime.now(timezone.utc).replace(tzinfo=None)

        try:
            stmt = (
                insert(CustomerProfile)
                .values(
                    merchant_id=merchant_id,
                    email=email.lower(),
                    phone=phone,
                    first_name=first_name,
                    last_name=last_name,
                    total_orders=1,
                    total_spent=order_total or Decimal("0"),
                    first_order_at=now,
                    last_order_at=now,
                    created_at=now,
                    updated_at=now,
                )
                .on_conflict_do_update(
                    constraint="ix_customer_profiles_merchant_email",
                    set_={
                        "phone": phone or CustomerProfile.phone,
                        "first_name": first_name or CustomerProfile.first_name,
                        "last_name": last_name or CustomerProfile.last_name,
                        "total_orders": CustomerProfile.total_orders + 1,
                        "total_spent": CustomerProfile.total_spent + (order_total or Decimal("0")),
                        "last_order_at": now,
                        "updated_at": now,
                    },
                )
                .returning(
                    CustomerProfile.id,
                    CustomerProfile.merchant_id,
                    CustomerProfile.email,
                    CustomerProfile.phone,
                    CustomerProfile.first_name,
                    CustomerProfile.last_name,
                    CustomerProfile.total_orders,
                    CustomerProfile.total_spent,
                    CustomerProfile.first_order_at,
                    CustomerProfile.last_order_at,
                )
            )

            result = await db.execute(stmt)
            await db.commit()

            row = result.fetchone()
            if row:
                profile = CustomerProfile(
                    id=row.id,
                    merchant_id=row.merchant_id,
                    email=row.email,
                    phone=row.phone,
                    first_name=row.first_name,
                    last_name=row.last_name,
                    total_orders=row.total_orders,
                    total_spent=row.total_spent,
                    first_order_at=row.first_order_at,
                    last_order_at=row.last_order_at,
                )

                logger.info(
                    "customer_profile_upserted",
                    merchant_id=merchant_id,
                    email=email,
                    profile_id=profile.id,
                    total_orders=profile.total_orders,
                )

                return profile

            return await self._fetch_profile_by_email(db, merchant_id, email)

        except Exception as e:
            await db.rollback()
            logger.error(
                "customer_profile_upsert_failed",
                merchant_id=merchant_id,
                email=email,
                error=str(e),
            )
            raise APIError(
                ErrorCode.CUSTOMER_PROFILE_ERROR,
                f"Failed to upsert customer profile: {str(e)}",
            )

    async def find_by_email(
        self,
        db: AsyncSession,
        merchant_id: int,
        email: str,
    ) -> Optional[CustomerProfile]:
        """Find a customer profile by email.

        Args:
            db: Database session
            merchant_id: Merchant ID
            email: Customer email

        Returns:
            CustomerProfile if found, None otherwise
        """
        try:
            result = await db.execute(
                select(CustomerProfile).where(
                    CustomerProfile.merchant_id == merchant_id,
                    CustomerProfile.email == email.lower(),
                )
            )
            return result.scalars().first()
        except Exception as e:
            logger.error(
                "customer_lookup_failed",
                merchant_id=merchant_id,
                email=email,
                error=str(e),
            )
            return None

    async def find_by_phone(
        self,
        db: AsyncSession,
        merchant_id: int,
        phone: str,
    ) -> Optional[CustomerProfile]:
        """Find a customer profile by phone.

        Args:
            db: Database session
            merchant_id: Merchant ID
            phone: Customer phone number

        Returns:
            CustomerProfile if found, None otherwise
        """
        try:
            result = await db.execute(
                select(CustomerProfile).where(
                    CustomerProfile.merchant_id == merchant_id,
                    CustomerProfile.phone == phone,
                )
            )
            return result.scalars().first()
        except Exception as e:
            logger.error(
                "customer_lookup_by_phone_failed",
                merchant_id=merchant_id,
                phone=phone,
                error=str(e),
            )
            return None

    async def get_customer_orders(
        self,
        db: AsyncSession,
        customer_profile_id: int,
        limit: int = 10,
    ) -> list[Order]:
        """Get orders for a customer profile.

        Args:
            db: Database session
            customer_profile_id: Customer profile ID
            limit: Maximum orders to return

        Returns:
            List of Order instances
        """
        try:
            profile = await db.get(CustomerProfile, customer_profile_id)
            if not profile:
                return []

            result = await db.execute(
                select(Order)
                .where(
                    Order.merchant_id == profile.merchant_id,
                    Order.customer_email == profile.email,
                    Order.is_test == False,
                )
                .order_by(Order.created_at.desc())
                .limit(limit)
            )
            return list(result.scalars().all())
        except Exception as e:
            logger.error(
                "customer_orders_lookup_failed",
                customer_profile_id=customer_profile_id,
                error=str(e),
            )
            return []

    def get_personalized_greeting(
        self,
        profile: CustomerProfile,
    ) -> str:
        """Generate a personalized greeting for a returning customer.

        Args:
            profile: Customer profile

        Returns:
            Personalized greeting string
        """
        name = profile.first_name or "there"
        order_count = profile.total_orders

        if order_count == 1:
            return f"Welcome back, {name}!"
        elif order_count > 1:
            return f"Welcome back, {name}! You've placed {order_count} orders with us."
        else:
            return f"Hi {name}!"

    async def _fetch_profile_by_email(
        self,
        db: AsyncSession,
        merchant_id: int,
        email: str,
    ) -> CustomerProfile:
        """Fetch an existing profile by email after upsert.

        Args:
            db: Database session
            merchant_id: Merchant ID
            email: Customer email

        Returns:
            CustomerProfile instance

        Raises:
            APIError: If profile not found
        """
        result = await db.execute(
            select(CustomerProfile).where(
                CustomerProfile.merchant_id == merchant_id,
                CustomerProfile.email == email.lower(),
            )
        )
        profile = result.scalars().first()

        if not profile:
            raise APIError(
                ErrorCode.CUSTOMER_PROFILE_ERROR,
                f"Customer profile not found after upsert: {email}",
            )

        return profile

    async def link_device_to_profile(
        self,
        db: AsyncSession,
        profile: CustomerProfile,
        platform_sender_id: str,
        conversation_data: dict[str, Any],
    ) -> dict[str, Any]:
        """Update conversation data to link device to customer profile.

        Args:
            db: Database session
            profile: Customer profile to link
            platform_sender_id: Device/platform sender ID
            conversation_data: Current conversation data

        Returns:
            Updated conversation data with customer identity
        """
        data = conversation_data.copy() if conversation_data else {}

        data["customer_email"] = profile.email
        data["customer_first_name"] = profile.first_name
        data["customer_last_name"] = profile.last_name
        data["customer_phone"] = profile.phone
        data["customer_profile_id"] = profile.id
        data["device_linked_at"] = datetime.now(timezone.utc).isoformat()

        logger.info(
            "device_linked_to_customer",
            customer_profile_id=profile.id,
            email=profile.email,
            platform_sender_id=platform_sender_id,
        )

        return data
