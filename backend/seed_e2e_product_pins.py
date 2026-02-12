import asyncio
import sys
import os
from pathlib import Path

# Add the directory containing the 'app' module to sys.path
# Since this script is in backend/, we add the backend/ directory.
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from app.core.database import async_session
from app.core.auth import hash_password
from app.models.merchant import Merchant
from app.models.product_pin import ProductPin
from app.models.llm_configuration import LLMConfiguration
from app.models.tutorial import Tutorial
from app.models.faq import Faq
from sqlalchemy import select


async def seed_merchant():
    """Seed the test merchant required for Story 1-15 E2E tests."""
    email = "e2e-product-pins@test.com"
    password = "TestPass123"

    async with async_session() as db:
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
