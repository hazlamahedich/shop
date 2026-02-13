#!/usr/bin/env python3
"""Create first-time test user merchant for testing full onboarding flow.

This merchant has NO completed onboarding steps, ensuring they will
see the complete flow: personality selection, business info, bot naming,
greetings, product pins, and the interactive tutorial.
"""

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


async def create_first_time_user():
    """Create a first-time test user with no onboarding completed."""
    email = "firsttime@test.com"
    password = "FirstTime123"

    async with async_session() as db:
        # Check if merchant already exists
        result = await db.execute(select(Merchant).where(Merchant.email == email))
        existing = result.scalars().first()

        if existing:
            print(f"Merchant {email} already exists.")
            print(f"  Email: {email}")
            print(f"  Password: {password}")
            print(f"  Merchant Key: {existing.merchant_key}")
            print()
            print("To reset this account to first-time user, delete the row from DB and re-run this script.")
            return

        # Create first-time merchant with minimal setup
        print(f"Creating first-time merchant {email}...")
        password_hash = hash_password(password)

        merchant = Merchant(
            merchant_key="firsttime-test-merchant",
            platform="shopify",
            status="active",
            email=email,
            password_hash=password_hash,
            # No onboarding fields set - they'll go through full flow
            business_name=None,
            business_description=None,
        )

        db.add(merchant)
        await db.commit()
        await db.refresh(merchant)

        print(f"Successfully created merchant with ID: {merchant.id}")
        print()
        print("=" * 60)
        print("FIRST-TIME TEST USER CREATED")
        print("=" * 60)
        print()
        print("Login credentials:")
        print(f"  Email:    {email}")
        print(f"  Password: {password}")
        print(f"  Merchant Key: {merchant.merchant_key}")
        print()
        print("This user will go through the complete onboarding flow:")
        print("  1. Select bot personality")
        print("  2. Configure business info & FAQ")
        print("  3. Set bot name")
        print("  4. Configure greeting templates")
        print("  5. Pin featured products")
        print("  6. Complete interactive tutorial (4 steps)")
        print()
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(create_first_time_user())
