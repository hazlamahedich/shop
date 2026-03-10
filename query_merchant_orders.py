import asyncio
from sqlalchemy import select
from app.core.database import async_session
from app.models.merchant import Merchant
from app.models.order import Order

async def main():
    async with async_session() as db:
        result = await db.execute(select(Order.items))
        orders = result.scalars().all()
        for o in orders:
            print(o)

if __name__ == "__main__":
    asyncio.run(main())
