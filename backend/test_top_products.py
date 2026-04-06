import asyncio

from sqlalchemy import select

from app.core.database import async_session
from app.models.merchant import Merchant
from app.services.analytics.aggregated_analytics_service import AggregatedAnalyticsService


async def main():
    async with async_session()() as db:
        # Get the first merchant
        result = await db.execute(select(Merchant).limit(1))
        merchant = result.scalar_one_or_none()
        if not merchant:
            print("No merchant found")
            return

        print(f"Merchant ID: {merchant.id}")
        service = AggregatedAnalyticsService(db)

        top_products = await service.get_top_products(merchant.id, days=30)

        for p in top_products:
            print(
                f"ID: {p['product_id']} | Title: {p['title']} | Qty: {p['quantity']} | Rev: {p['revenue']}"
            )


if __name__ == "__main__":
    asyncio.run(main())
