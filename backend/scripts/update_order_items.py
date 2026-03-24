#!/usr/bin/env python
"""Update test orders with product IDs and estimated delivery dates.

Story 5-13: Enhanced order status with product images and delivery estimates.
"""

import asyncio
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, update

from app.core.database import async_session
from app.models.order import Order


async def update_orders():
    """Update test orders with product IDs and estimated delivery."""
    async with async_session() as db:
        result = await db.execute(select(Order).where(Order.order_number.in_(["1003", "1234"])))
        orders = result.scalars().all()

        for order in orders:
            if not order.items:
                continue

            updated_items = []
            for item in order.items:
                updated_item = item.copy()

                if not updated_item.get("product_id"):
                    title = updated_item.get("title", "").lower()
                    if "shoes" in title:
                        updated_item["product_id"] = "shopify_prod_001"
                    elif "earbuds" in title or "wireless" in title:
                        updated_item["product_id"] = "shopify_prod_002"
                    elif "yoga" in title:
                        updated_item["product_id"] = "shopify_prod_003"
                    elif "bottle" in title or "water" in title:
                        updated_item["product_id"] = "shopify_prod_004"
                    elif "speaker" in title:
                        updated_item["product_id"] = "shopify_prod_005"
                    elif "coffee" in title and "bean" in title:
                        updated_item["product_id"] = "shopify_prod_006"
                    elif "backpack" in title:
                        updated_item["product_id"] = "shopify_prod_007"
                    elif "watch" in title or "fitness" in title:
                        updated_item["product_id"] = "shopify_prod_008"
                    else:
                        import hashlib

                        hash_obj = hashlib.md5(title.encode())
                        num = int(hash_obj.hexdigest(), 16) % 12
                        updated_item["product_id"] = f"shopify_prod_{num + 1:03d}"

                updated_items.append(updated_item)

            estimated_delivery = datetime.utcnow() + timedelta(days=5)

            await db.execute(
                update(Order)
                .where(Order.id == order.id)
                .values(items=updated_items, estimated_delivery=estimated_delivery)
            )

            print(f"Updated order {order.order_number}:")
            print(f"  Items: {len(updated_items)}")
            for item in updated_items:
                print(f"    - {item.get('title')}: product_id={item.get('product_id')}")
            print(f"  Estimated Delivery: {estimated_delivery.strftime('%B %d, %Y')}")
            print()

        await db.commit()
        print(f"Successfully updated {len(orders)} orders")


if __name__ == "__main__":
    asyncio.run(update_orders())
