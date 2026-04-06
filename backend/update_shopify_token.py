#!/usr/bin/env python3
"""Script to manually update Shopify admin token for merchant 4."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import select

from app.core.database import async_session
from app.core.security import encrypt_access_token
from app.models.shopify_integration import ShopifyIntegration


async def update_shopify_token():
    """Update Shopify admin token for merchant 4."""

    print("=== Shopify Token Update Script ===")
    print("This will update the admin access token for merchant 4")
    print()

    # Get the new token from user input
    print("Enter your Shopify Admin API access token:")
    print("(This should start with 'shpat_' for a custom app)")
    print()
    new_token = input("Token: ").strip()

    if not new_token:
        print("❌ No token provided. Exiting.")
        return

    if not new_token.startswith("shpat_"):
        print("⚠️  Warning: Token doesn't start with 'shpat_'. Are you sure this is correct?")
        confirm = input("Continue anyway? (yes/no): ").strip().lower()
        if confirm != "yes":
            print("Exiting.")
            return

    print()
    print(f"Token length: {len(new_token)} characters")
    confirm = input("Update token for merchant 4? (yes/no): ").strip().lower()

    if confirm != "yes":
        print("Exiting.")
        return

    async with async_session()() as db:
        # Get current integration
        result = await db.execute(
            select(ShopifyIntegration).where(ShopifyIntegration.merchant_id == 4)
        )
        integration = result.scalar_one_or_none()

        if not integration:
            print("❌ No Shopify integration found for merchant 4")
            return

        print(f"✅ Found integration for shop: {integration.shop_domain}")

        # Encrypt and update token
        encrypted_token = encrypt_access_token(new_token)

        integration.admin_token_encrypted = encrypted_token
        integration.admin_api_verified = True

        await db.commit()

        print()
        print("✅ Token updated successfully!")
        print()
        print("Next steps:")
        print("1. Test the product search by running: python debug_product_search.py")
        print("2. Try asking the widget: 'What products do you have under $50?'")
        print()


if __name__ == "__main__":
    asyncio.run(update_shopify_token())
