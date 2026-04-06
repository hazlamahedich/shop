import asyncio

from app.database import AsyncSessionLocal
from sqlalchemy import select

from app.models.merchant import Merchant
from app.services.shopify_storefront import ShopifyStorefrontClient


async def main():
    async with AsyncSessionLocal() as db:
        merchant = (await db.execute(select(Merchant).limit(1))).scalar_one_or_none()
        if not merchant:
            print("No merchant found")
            return

        client = ShopifyStorefrontClient(merchant.shop_domain, merchant.storefront_access_token)
        products = await client.list_products(first=5)
        print("First 5 products:", products)


if __name__ == "__main__":
    asyncio.run(main())
