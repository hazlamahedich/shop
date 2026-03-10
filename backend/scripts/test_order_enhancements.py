#!/usr/bin/env python
"""Test enhanced order status with product images and delivery estimates.

Story 5-13: Product images and estimated delivery.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import async_session
from app.services.order_tracking.order_tracking_service import OrderTrackingService
from app.services.shopify.product_service import get_products_by_ids
from sqlalchemy import select
from app.models.order import Order


async def test_order_status():
    """Test order status response with product images and delivery."""
    async with async_session() as db:
        tracking_service = OrderTrackingService()

        result = await tracking_service.track_order_by_number(
            db=db,
            merchant_id=6,
            order_number="1234",
        )

        if not result.found or not result.order:
            print("Order not found!")
            return

        order = result.order
        print(f"Order #{order.order_number}")
        print(f"Status: {order.status}")
        print(f"Created: {order.created_at}")
        print(f"Estimated Delivery: {order.estimated_delivery}")
        print(f"\nItems ({len(order.items)}):")
        for item in order.items:
            print(f"  - {item.get('title')}: {item.get('price')} x {item.get('quantity')}")

        product_ids = []
        for item in order.items:
            product_id = item.get("product_id") or item.get("id")
            if product_id and isinstance(product_id, int):
                product_ids.append(str(product_id))
            elif product_id:
                product_ids.append(str(product_id))

        print(f"\nFetching product images for {len(product_ids)} products...")
        products = await get_products_by_ids(
            access_token="",
            merchant_id=6,
            product_ids=product_ids,
            db=db,
        )

        product_images = {}
        for product_id, product_data in products.items():
            image_url = product_data.get("image_url") or (
                product_data.get("images", [{}])[0].get("url")
                if product_data.get("images")
                else None
            )
            if image_url:
                product_images[product_id] = image_url
                print(f"  {product_data.get('title')}: {image_url}")

        print("\n" + "=" * 60)
        print("Formatted Response:")
        print("=" * 60)
        response = tracking_service.format_order_response(order, product_images)
        print(response)
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_order_status())
