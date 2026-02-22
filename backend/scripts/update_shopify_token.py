"""
Script to manually update Shopify storefront token.

Usage:
    source venv/bin/activate
    python scripts/update_shopify_token.py --merchant-id 4 --storefront-token "shpat_xxx..."

To create a storefront token:
1. Go to Shopify Admin > Settings > Apps and sales channels > Develop apps
2. Create app or select existing
3. Configure Storefront API scopes:
   - unauthenticated_read_product_listings
   - unauthenticated_write_checkouts  
   - unauthenticated_read_checkouts
4. Install app and copy the Storefront access token
"""
import asyncio
import argparse
from app.core.database import async_session
from app.core.security import encrypt_access_token
from app.models.shopify_integration import ShopifyIntegration
from sqlalchemy import select


async def update_storefront_token(merchant_id: int, storefront_token: str):
    async with async_session() as db:
        result = await db.execute(
            select(ShopifyIntegration).where(ShopifyIntegration.merchant_id == merchant_id)
        )
        integration = result.scalars().first()
        
        if not integration:
            print(f"No Shopify integration found for merchant {merchant_id}")
            return False
            
        print(f"Updating storefront token for shop: {integration.shop_domain}")
        
        integration.storefront_token_encrypted = encrypt_access_token(storefront_token)
        integration.storefront_api_verified = True
        
        await db.commit()
        print("Storefront token updated successfully!")
        return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Update Shopify storefront token")
    parser.add_argument("--merchant-id", type=int, required=True, help="Merchant ID")
    parser.add_argument("--storefront-token", type=str, required=True, help="Storefront access token")
    
    args = parser.parse_args()
    asyncio.run(update_storefront_token(args.merchant_id, args.storefront_token))
