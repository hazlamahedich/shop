#!/usr/bin/env python3
"""Create test@test.com merchant for manual testing and E2E tests."""

import asyncio
import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.database import async_session
from app.core.auth import hash_password
from app.models.merchant import Merchant
from sqlalchemy import select


async def create_test_merchant():
    """Create test@test.com merchant account."""
    email = "test@test.com"
    password = "Test12345"

    async with async_session() as db:
        # Check if merchant already exists
        result = await db.execute(select(Merchant).where(Merchant.email == email))
        existing = result.scalars().first()

        if existing:
            print(f"Merchant {email} already exists.")
            print(f"  Email: {email}")
            print(f"  Password: {password}")
            print(f"  Merchant Key: {existing.merchant_key}")
            return

        # Create test merchant
        print(f"Creating merchant {email}...")
        password_hash = hash_password(password)

        merchant = Merchant(
            merchant_key="test-merchant",
            platform="shopify",
            status="active",
            email=email,
            password_hash=password_hash,
            business_name="Test Store",
            business_description="Manual testing store",
        )

        db.add(merchant)
        await db.commit()
        await db.refresh(merchant)

        print(f"Successfully created merchant with ID: {merchant.id}")
        print()
        print("Login credentials:")
        print(f"  Email: {email}")
        print(f"  Password: {password}")
        print(f"  Merchant Key: {merchant.merchant_key}")


if __name__ == "__main__":
    asyncio.run(create_test_merchant())
