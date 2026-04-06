import asyncio
import sys
from pathlib import Path

# Add the directory containing the 'app' module to sys.path
# Since this script is in backend/, we add the backend/ directory.
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from sqlalchemy import select

from app.core.auth import hash_password
from app.core.database import async_session
from app.models.merchant import Merchant


async def seed_merchant():
    """Seed the test merchant required for Story 1-15 E2E tests."""
    email = "e2e-product-pins@test.com"
    password = "TestPass123"

    async with async_session()() as db:
        # Check if merchant already exists
        result = await db.execute(select(Merchant).where(Merchant.email == email))
        existing = result.scalars().first()

        if existing:
            print(f"Merchant {email} already exists.")
            return

        print(f"Creating merchant {email}...")
        password_hash = hash_password(password)

        merchant = Merchant(
            merchant_key="e2e-product-pins-merchant",
            platform="shopify",
            status="active",
            email=email,
            password_hash=password_hash,
            business_name="Test Store",
            business_description="Test store for E2E product pins",
        )

        db.add(merchant)
        await db.commit()
        await db.refresh(merchant)
        print(f"Successfully created merchant with ID: {merchant.id}")


if __name__ == "__main__":
    asyncio.run(seed_merchant())
