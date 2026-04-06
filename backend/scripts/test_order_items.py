import asyncio
import json

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.models.order import Order


async def main():
    async with AsyncSessionLocal() as db:
        order = (
            await db.execute(select(Order).where(Order.items != None).limit(1))
        ).scalar_one_or_none()
        if order:
            print(json.dumps(order.items, indent=2))
        else:
            print("No orders found with items")


if __name__ == "__main__":
    asyncio.run(main())
