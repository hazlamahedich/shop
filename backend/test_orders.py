import asyncio
from sqlalchemy import select
from app.core.database import async_session
from app.models.merchant import Merchant
from app.models.order import Order

async def main():
    async with async_session() as db:
        result = await db.execute(select(Order).limit(10))
        orders = result.scalars().all()
        for o in orders:
            print(f"Order ID: {o.id}, merchant_id: {o.merchant_id}, is_test: {o.is_test}")

if __name__ == "__main__":
    asyncio.run(main())
