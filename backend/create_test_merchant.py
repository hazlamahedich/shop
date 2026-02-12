#!/usr/bin/env python3
"""Create test merchant for E2E tests."""

import asyncio
import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / 'backend'))

os.environ['DATABASE_URL'] = 'postgresql+asyncpg://shop_user:shop_password@localhost:5432/shop_db'
os.environ['SECRET_KEY'] = 'dev-secret-key-DO-NOT-USE-IN-PRODUCTION'

from app.core.database import async_session
from app.core.auth import hash_password
from app.models.merchant import Merchant


async def create_test_merchant():
    """Create a test merchant account."""
    async with async_session() as db:
        from sqlalchemy import select

        # Check if merchant already exists
        result = await db.execute(
            select(Merchant).where(Merchant.email == 'e2e-test@example.com')
        )
        existing = result.scalars().first()

        if existing:
            print("Test merchant already exists:")
            print(f"  Email: {existing.email}")
            print(f"  Merchant Key: {existing.merchant_key}")
            print(f"  Password: TestPass123")
            return

        # Create test merchant
        password_hash = hash_password("TestPass123")

        merchant = Merchant(
            merchant_key="e2e-test-merchant",
            platform="shopify",
            status="active",
            email="e2e-test@example.com",
            password_hash=password_hash,
        )

        db.add(merchant)
        await db.commit()
        await db.refresh(merchant)

        print("Test merchant created successfully!")
        print()
        print("Login credentials:")
        print(f"  Email: {merchant.email}")
        print(f"  Password: TestPass123")
        print(f"  Merchant Key: {merchant.merchant_key}")


if __name__ == "__main__":
    asyncio.run(create_test_merchant())
