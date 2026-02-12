"""Seed script for creating a development merchant account.

Story 1.8: Merchant Dashboard Authentication
Creates a test merchant for local development.

Usage:
    python scripts/seed_merchant.py
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.app.core.database import async_session
from backend.app.core.auth import hash_password
from backend.app.models.merchant import Merchant


async def seed_development_merchant() -> None:
    """Create a development merchant account."""
    async with async_session() as db:
        # Check if dev merchant already exists
        from sqlalchemy import select

        result = await db.execute(
            select(Merchant).where(Merchant.email == "dev@example.com")
        )
        existing = result.scalars().first()

        if existing:
            print("Development merchant already exists:")
            print(f"  Email: {existing.email}")
            print(f"  Merchant Key: {existing.merchant_key}")
            print(f"  Password: DevPass123")
            return

        # Create development merchant
        password_hash = hash_password("DevPass123")

        merchant = Merchant(
            merchant_key="dev-merchant-01",
            platform="shopify",
            status="active",
            email="dev@example.com",
            password_hash=password_hash,
        )

        db.add(merchant)
        await db.commit()
        await db.refresh(merchant)

        print("Development merchant created successfully!")
        print()
        print("Login credentials:")
        print(f"  Email: {merchant.email}")
        print(f"  Password: DevPass123")
        print(f"  Merchant Key: {merchant.merchant_key}")
        print()
        print("Use these credentials to log in to the dashboard.")


if __name__ == "__main__":
    asyncio.run(seed_development_merchant())
