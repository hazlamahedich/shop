#!/usr/bin/env python3
"""Create blank test merchant with minimal data - NO mock products.

This creates a merchant account ready for real Shopify integration.
All product data will come from the connected Shopify store.

Usage:
    python seed_blank_account.py           # Create blank account
    python seed_blank_account.py --reset   # Delete and recreate
"""

import argparse
import asyncio
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

import os
from cryptography.fernet import Fernet

if not os.getenv("FACEBOOK_ENCRYPTION_KEY"):
    temp_key = Fernet.generate_key().decode()
    os.environ["FACEBOOK_ENCRYPTION_KEY"] = temp_key
    print("  Generated temporary encryption key for this session")

from sqlalchemy import delete, select
from app.core.database import async_session
from app.core.auth import hash_password
from app.core.security import encrypt_access_token
from app.models.merchant import Merchant, PersonalityType, StoreProvider
from app.models.llm_configuration import LLMConfiguration
from app.models.onboarding import PrerequisiteChecklist
from app.models.tutorial import Tutorial


BLANK_EMAIL = "test@test.com"
BLANK_PASSWORD = "Test12345"
BLANK_MERCHANT_KEY = "test-merchant"


async def clear_blank_data(db):
    """Delete all blank test account data."""
    result = await db.execute(select(Merchant).where(Merchant.email == BLANK_EMAIL))
    merchant = result.scalars().first()
    if merchant:
        await db.execute(delete(Merchant).where(Merchant.id == merchant.id))
        print(f"  Deleted existing test account (ID: {merchant.id})")


async def seed_blank_merchant(db) -> Merchant:
    """Create minimal test merchant - no mock products, no seed data."""
    merchant = Merchant(
        merchant_key=BLANK_MERCHANT_KEY,
        platform="shopify",
        status="active",
        email=BLANK_EMAIL,
        password_hash=hash_password(BLANK_PASSWORD),
        business_name="My Store",
        business_description="",
        business_hours="Mon-Fri 9AM-6PM",
        bot_name="ShopBot",
        personality=PersonalityType.FRIENDLY,
        custom_greeting=None,
        use_custom_greeting=False,
        store_provider=StoreProvider.SHOPIFY,
        deployed_at=datetime.utcnow() - timedelta(days=1),
    )
    db.add(merchant)
    await db.flush()
    return merchant


async def seed_llm_configuration(db, merchant: Merchant):
    """Create LLM configuration with Anthropic (placeholder key)."""
    config = LLMConfiguration(
        merchant_id=merchant.id,
        provider="anthropic",
        api_key_encrypted=encrypt_access_token("sk-ant-placeholder-replace-with-real-key"),
        cloud_model="claude-3-haiku-20240307",
        status="active",
        configured_at=datetime.utcnow(),
        total_tokens_used=0,
        total_cost_usd=0.0,
    )
    db.add(config)


async def seed_prerequisite_checklist(db, merchant: Merchant):
    """Create prerequisite checklist (NOT completed - needs integrations)."""
    checklist = PrerequisiteChecklist(
        merchant_id=merchant.id,
        has_cloud_account=True,
        has_facebook_account=False,
        has_shopify_access=False,
        has_llm_provider_choice=True,
        completed_at=None,
    )
    db.add(checklist)


async def seed_tutorial(db, merchant: Merchant):
    """Create tutorial (fresh start)."""
    tutorial = Tutorial(
        merchant_id=merchant.id,
        current_step=1,
        completed_steps=["welcome"],
        started_at=datetime.utcnow(),
        completed_at=None,
        skipped=False,
        tutorial_version="1.0",
        steps_total=8,
    )
    db.add(tutorial)


async def main():
    parser = argparse.ArgumentParser(description="Seed blank test account with minimal data")
    parser.add_argument("--reset", action="store_true", help="Delete and recreate test account")
    args = parser.parse_args()

    print("=" * 60)
    print("BLANK TEST ACCOUNT SEED SCRIPT")
    print("=" * 60)
    print()

    async with async_session() as db:
        if args.reset:
            print("Resetting test account...")
            await clear_blank_data(db)
            await db.commit()
            print()

        result = await db.execute(select(Merchant).where(Merchant.email == BLANK_EMAIL))
        existing = result.scalars().first()

        if existing:
            print(f"Test account already exists: {BLANK_EMAIL}")
            print("  Use --reset to delete and recreate")
            print()
            print(f"  Email: {BLANK_EMAIL}")
            print(f"  Password: {BLANK_PASSWORD}")
            print(f"  Merchant Key: {existing.merchant_key}")
            return

        print("Creating blank test merchant...")
        merchant = await seed_blank_merchant(db)
        print(f"  Created merchant ID: {merchant.id}")

        print("Creating LLM configuration...")
        await seed_llm_configuration(db, merchant)

        print("Creating prerequisite checklist...")
        await seed_prerequisite_checklist(db, merchant)

        print("Creating tutorial progress...")
        await seed_tutorial(db, merchant)

        await db.commit()

        print()
        print("=" * 60)
        print("BLANK TEST ACCOUNT CREATED SUCCESSFULLY")
        print("=" * 60)
        print()
        print("Login credentials:")
        print(f"  Email:    {BLANK_EMAIL}")
        print(f"  Password: {BLANK_PASSWORD}")
        print()
        print("Account setup:")
        print("  - Minimal merchant account (no seed data)")
        print("  - NO integrations connected (connect yours)")
        print("  - NO mock products - uses real Shopify data")
        print("  - NO conversations, FAQs, or product pins")
        print()
        print("Next steps:")
        print("  1. Go through the tutorial")
        print("  2. Connect your Shopify store")
        print("  3. Connect your Facebook Page")
        print("  4. Add FAQs and pin products")
        print("  5. Test your bot!")
        print()
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
