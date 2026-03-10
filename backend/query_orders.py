import asyncio
from sqlalchemy import select
from app.core.database import async_session
from app.models.order import Order

async def main():
    async with async_session() as db:
        result = await db.execute(select(Order.items).limit(10))
        items_lists = result.scalars().all()
        for items in items_lists:
            print(items)

if __name__ == "__main__":
    asyncio.run(main())
