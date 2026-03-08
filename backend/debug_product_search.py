#!/usr/bin/env python3
"""Debug script to test product search for merchant 4."""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import select
from app.core.database import async_session
from app.models.merchant import Merchant
from app.models.shopify_integration import ShopifyIntegration
from app.services.shopify.product_search_service import ProductSearchService
from app.services.intent.classification_schema import ExtractedEntities
from app.services.shopify_admin import ShopifyAdminClient
from app.core.security import decrypt_access_token


async def debug_product_search():
    """Debug product search for merchant 4."""
    async with async_session() as db:
        # Get merchant 4
        result = await db.execute(select(Merchant).where(Merchant.id == 4))
        merchant = result.scalar_one_or_none()

        if not merchant:
            print("❌ Merchant 4 not found")
            return

        print(f"✅ Merchant: {merchant.business_name}")

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
        print(f"   Admin API Verified: {integration.admin_api_verified}")

        # Test 1: Fetch all products from Shopify
        print("\n" + "=" * 60)
        print("TEST 1: Fetching ALL products from Shopify Admin API")
        print("=" * 60)

        try:
            admin_token = decrypt_access_token(integration.admin_token_encrypted)
            admin_client = ShopifyAdminClient(
                shop_domain=integration.shop_domain,
                access_token=admin_token,
                is_testing=False,
            )

            all_products = await admin_client.list_products(limit=100)
            print(f"\n✅ Fetched {len(all_products)} products from Shopify")

            if all_products:
                print("\nAll products:")
                for i, p in enumerate(all_products, 1):
                    price = float(p.get("price", 0)) if p.get("price") else 0
                    print(
                        f"{i}. {p['title']:<40} ${price:>7.2f}  Available: {p.get('available', 'N/A')}"
                    )

                # Check products under $50
                under_50 = [
                    p for p in all_products if p.get("price") and float(p.get("price", 0)) < 50
                ]
                print(f"\n✅ Products under $50: {len(under_50)}")
                if under_50:
                    for p in under_50:
                        print(f"   - {p['title']}: ${float(p.get('price', 0)):.2f}")
                else:
                    print("   ⚠️  NO PRODUCTS UNDER $50 IN STORE!")
            else:
                print("⚠️  No products found in Shopify store!")

        except Exception as e:
            print(f"❌ Error fetching products: {e}")
            import traceback

            traceback.print_exc()

        # Test 2: Test product search with budget filter
        print("\n" + "=" * 60)
        print("TEST 2: Product search with budget=50")
        print("=" * 60)

        try:
            search_service = ProductSearchService(db=db)

            # Test with budget filter
            entities = ExtractedEntities(
                budget=50.0,
                budget_currency="USD",
            )

            search_result = await search_service.search_products(
                entities=entities,
                merchant_id=4,
            )

            print(f"\n✅ Search completed in {search_result.search_time_ms:.2f}ms")
            print(f"   Total results: {search_result.total_count}")
            print(f"   Has alternatives: {search_result.has_alternatives}")

            if search_result.products:
                print(f"\n   Found {len(search_result.products)} products:")
                for p in search_result.products:
                    print(f"   - {p.title}: ${float(p.price):.2f}")
            else:
                print("   ⚠️  No products found matching budget filter!")

        except Exception as e:
            print(f"❌ Error in product search: {e}")
            import traceback

            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(debug_product_search())
