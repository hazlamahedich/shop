#!/usr/bin/env python3
"""Debug script to test Shopify Admin API directly."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import httpx
from sqlalchemy import select

from app.core.database import async_session
from app.core.security import decrypt_access_token
from app.models.shopify_integration import ShopifyIntegration


async def test_shopify_admin_api():
    """Test Shopify Admin API directly."""
    async with async_session() as db:
        # Get Shopify integration
        result = await db.execute(
            select(ShopifyIntegration).where(ShopifyIntegration.merchant_id == 4)
        )
        integration = result.scalar_one_or_none()

        if not integration:
            print("❌ No Shopify integration found")
            return

        print(f"✅ Shopify Store: {integration.shop_domain}")
        print(f"   Status: {integration.status}")
        print(f"   Scopes: {integration.scopes}")

        # Decrypt admin token
        admin_token = decrypt_access_token(integration.admin_token_encrypted)
        print(f"\n✅ Admin token decrypted (length: {len(admin_token)})")

        # Test direct API call
        url = f"https://{integration.shop_domain}/admin/api/2024-01/products.json?limit=10"

        print("\n📡 Testing Admin API...")
        print(f"   URL: {url}")
        print(f"   Token: {admin_token[:20]}...")

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    url,
                    headers={
                        "X-Shopify-Access-Token": admin_token,
                        "Accept": "application/json",
                    },
                    timeout=30.0,
                )

                print(f"\n   Status Code: {response.status_code}")

                if response.status_code == 200:
                    data = response.json()
                    products = data.get("products", [])
                    print(f"   ✅ Found {len(products)} products")

                    if products:
                        print("\n   Products:")
                        for i, p in enumerate(products[:5], 1):
                            variants = p.get("variants", [])
                            price = variants[0].get("price") if variants else "N/A"
                            print(f"   {i}. {p['title']:<40} ${price}")
                    else:
                        print("   ⚠️  No products returned (empty array)")
                        print(f"   Response: {data}")
                else:
                    print(f"   ❌ API Error: {response.status_code}")
                    print(f"   Response: {response.text}")

            except Exception as e:
                print(f"   ❌ Error: {e}")
                import traceback

                traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_shopify_admin_api())
