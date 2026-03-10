import asyncio
from app.db.session import get_db
from sqlalchemy import select
from app.models.order import Order

async def main():
    async for db in get_db():
        result = await db.execute(select(Order).where(Order.order_number == "1003"))
        order = result.scalar_one_or_none()
        if order:
            print(f"Order: {order.order_number}, Status: {order.status}, Fulfillment: {order.fulfillment_status}, Created At: {order.created_at}")
        else:
            print("Not found")
        break

asyncio.run(main())
