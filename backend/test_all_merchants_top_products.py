import asyncio
from sqlalchemy import select
from app.core.database import async_session
from app.models.merchant import Merchant
from app.services.analytics.aggregated_analytics_service import AggregatedAnalyticsService
import logging

logging.basicConfig(level=logging.INFO)

async def main():
    async with async_session() as db:
        result = await db.execute(select(Merchant))
        merchants = result.scalars().all()
        
        for merchant in merchants:
            print(f"Merchant ID: {merchant.id}")
            service = AggregatedAnalyticsService(db)
            
            try:
                top_products = await service.get_top_products(merchant.id, days=30)
                if top_products:
                    print(f"Top products for merchant {merchant.id}:")
                    for p in top_products:
                        print(p)
                else:
                    print(f"No top products for merchant {merchant.id}")
            except Exception as e:
                print(f"EXCEPTION for merchant {merchant.id}:", e)

if __name__ == "__main__":
    asyncio.run(main())
