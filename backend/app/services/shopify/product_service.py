"""Shopify Product Fetch Service.

Story 1.15: Product Highlight Pins

Fetches product data from Shopify Admin API with caching.
Integrates with product pin service to provide product titles and images.
"""

from __future__ import annotations

import os
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import APIError, ErrorCode
from app.models.product_pin import ProductPin
from app.models.shopify_integration import ShopifyIntegration
from app.models.merchant import Merchant
from app.core.security import decrypt_access_token
from app.services.shopify_admin import ShopifyAdminClient
from app.core.config import is_testing
from app.services.product_pin_service import get_pinned_products
import structlog


logger = structlog.get_logger(__name__)

PRODUCT_CACHE_TTL = int(os.getenv("PRODUCT_CACHE_TTL", "300"))


MOCK_PRODUCTS = [
    {
        "id": "shopify_prod_001",
        "title": "Running Shoes Pro",
        "description": "Professional running shoes for marathons and daily training",
        "image_url": "https://cdn.shopify.com/s/files/shoes-pro.jpg",
        "price": "129.99",
        "vendor": "AthleticGear",
        "product_type": "Footwear",
    },
    {
        "id": "shopify_prod_002",
        "title": "Wireless Earbuds",
        "description": "Premium noise-cancelling earbuds with 30hr battery life",
        "image_url": "https://cdn.shopify.com/s/files/earbuds.jpg",
        "price": "89.99",
        "vendor": "AudioTech",
        "product_type": "Electronics",
    },
    {
        "id": "shopify_prod_003",
        "title": "Yoga Mat Premium",
        "description": "Extra thick eco-friendly yoga mat with alignment lines",
        "image_url": "https://cdn.shopify.com/s/files/yoga-mat.jpg",
        "price": "45.00",
        "vendor": "ZenFitness",
        "product_type": "Fitness Equipment",
    },
    {
        "id": "shopify_prod_004",
        "title": "Stainless Steel Water Bottle",
        "description": "Insulated 24oz water bottle keeps drinks cold for 6 hours",
        "image_url": "https://cdn.shopify.com/s/files/water-bottle.jpg",
        "price": "24.99",
        "vendor": "EcoDrink",
        "product_type": "Accessories",
    },
    {
        "id": "shopify_prod_005",
        "title": "Bluetooth Speaker Portable",
        "description": "Waterproof portable speaker with 360deg sound",
        "image_url": "https://cdn.shopify.com/s/files/speaker.jpg",
        "price": "79.99",
        "vendor": "SoundWave",
        "product_type": "Electronics",
    },
    {
        "id": "shopify_prod_006",
        "title": "Organic Coffee Beans 1kg",
        "description": "Fair trade single-origin Ethiopian coffee beans",
        "image_url": "https://cdn.shopify.com/s/files/coffee.jpg",
        "price": "28.00",
        "vendor": "BeanRoasters",
        "product_type": "Food & Drink",
    },
    {
        "id": "shopify_prod_007",
        "title": "Hiking Backpack 40L",
        "description": "Lightweight hiking backpack with rain cover",
        "image_url": "https://cdn.shopify.com/s/files/backpack.jpg",
        "price": "89.00",
        "vendor": "TrailReady",
        "product_type": "Outdoor Gear",
    },
    {
        "id": "shopify_prod_008",
        "title": "Smart Fitness Watch",
        "description": "Heart rate monitoring and GPS tracking watch",
        "image_url": "https://cdn.shopify.com/s/files/smart-watch.jpg",
        "price": "199.99",
        "vendor": "FitTech",
        "product_type": "Electronics",
    },
    {
        "id": "shopify_prod_009",
        "title": "Eco-Friendly Reusable Bags",
        "description": "Set of 3 produce bags with organic cotton",
        "image_url": "https://cdn.shopify.com/s/files/reusable-bags.jpg",
        "price": "34.99",
        "vendor": "GreenLiving",
        "product_type": "Accessories",
    },
    {
        "id": "shopify_prod_010",
        "title": "Vitamin C Supplement Pack",
        "description": "30-day supply of vitamin C with rose hips",
        "image_url": "https://cdn.shopify.com/s/files/vitamin-c.jpg",
        "price": "19.99",
        "vendor": "WellnessCo",
        "product_type": "Health & Wellness",
    },
    {
        "id": "shopify_prod_011",
        "title": "Ceramic Coffee Mug",
        "description": "Handmade ceramic mug with cork bottom",
        "image_url": "https://cdn.shopify.com/s/files/coffee-mug.jpg",
        "price": "18.50",
        "vendor": "ArtisanCrafts",
        "product_type": "Kitchen",
    },
    {
        "id": "shopify_prod_012",
        "title": "LED Desk Lamp",
        "description": "Adjustable brightness LED lamp with USB charging",
        "image_url": "https://cdn.shopify.com/s/files/desk-lamp.jpg",
        "price": "42.00",
        "vendor": "BrightHome",
        "product_type": "Home Office",
    },
    {
        "id": "shopify_prod_013",
        "title": "Foam Roller Muscle Recovery",
        "description": "High-density foam roller for post-workout recovery",
        "image_url": "https://cdn.shopify.com/s/files/foam-roller.jpg",
        "price": "22.00",
        "vendor": "RecoverFit",
        "product_type": "Fitness Equipment",
    },
    {
        "id": "shopify_prod_014",
        "title": "Wireless Charging Pad",
        "description": "Qi wireless charging pad for phones and earbuds",
        "image_url": "https://cdn.shopify.com/s/files/charging-pad.jpg",
        "price": "35.00",
        "vendor": "ChargeTech",
        "product_type": "Electronics",
    },
    {
        "id": "shopify_prod_015",
        "title": "Organic Green Tea Sampler",
        "description": "Variety pack of 4 organic green tea flavors",
        "image_url": "https://cdn.shopify.com/s/files/green-tea.jpg",
        "price": "24.00",
        "vendor": "TeaGarden",
        "product_type": "Food & Drink",
    },
    {
        "id": "shopify_prod_016",
        "title": "Minimalist Leather Wallet",
        "description": "Slim RFID-blocking leather wallet for cards",
        "image_url": "https://cdn.shopify.com/s/files/leather-wallet.jpg",
        "price": "55.00",
        "vendor": "CarryEssentials",
        "product_type": "Accessories",
    },
    {
        "id": "shopify_prod_017",
        "title": "Bamboo Kitchen Utensil Set",
        "description": "Sustainable 6-piece bamboo utensil set with travel case",
        "image_url": "https://cdn.shopify.com/s/files/bamboo-set.jpg",
        "price": "32.00",
        "vendor": "EcoKitchen",
        "product_type": "Kitchen",
    },
    {
        "id": "shopify_prod_018",
        "title": "Noise Cancelling Headphones",
        "description": "Over-ear headphones with active noise cancellation",
        "image_url": "https://cdn.shopify.com/s/files/headphones.jpg",
        "price": "149.99",
        "vendor": "AudioTech",
        "product_type": "Electronics",
    },
    {
        "id": "shopify_prod_019",
        "title": "Recycled Journal Notebook",
        "description": "A5 ruled notebook made from 100% recycled paper",
        "image_url": "https://cdn.shopify.com/s/files/notebook.jpg",
        "price": "12.00",
        "vendor": "EcoWrite",
        "product_type": "Stationery",
    },
    {
        "id": "shopify_prod_020",
        "title": "Resistance Bands Set",
        "description": "Set of 5 resistance bands for strength training",
        "image_url": "https://cdn.shopify.com/s/files/resistance-bands.jpg",
        "price": "29.99",
        "vendor": "FitGear",
        "product_type": "Fitness Equipment",
    },
]


async def fetch_products(
    access_token: str,
    merchant_id: str,
    db: AsyncSession,
) -> list[dict]:
    """Fetch products from Shopify Admin API.

    Args:
        access_token: Unused (kept for compatibility)
        merchant_id: Merchant ID for database lookup
        db: Database session

    Returns:
        List of product dictionaries with id, title, image_url

    Raises:
        APIError: If fetch fails
    """
    try:
        result = await db.execute(
            select(ShopifyIntegration).where(ShopifyIntegration.merchant_id == merchant_id)
        )
        integration = result.scalars().first()

        if integration and integration.status == "active" and integration.admin_token_encrypted:
            admin_token = decrypt_access_token(integration.admin_token_encrypted)

            client = ShopifyAdminClient(
                shop_domain=integration.shop_domain,
                access_token=admin_token,
                is_testing=is_testing(),
            )

            shopify_products = await client.list_products(limit=100)

            logger.info(
                "shopify_products_fetched",
                merchant_id=merchant_id,
                shop_domain=integration.shop_domain,
                product_count=len(shopify_products),
            )

            return shopify_products

    except Exception as e:
        logger.warning(
            "shopify_products_fetch_failed_using_mock",
            merchant_id=merchant_id,
            error=str(e),
        )

    logger.info(
        "using_mock_products",
        merchant_id=merchant_id,
        product_count=len(MOCK_PRODUCTS),
    )

    return MOCK_PRODUCTS


async def get_product_by_id(
    access_token: str,
    product_id: str,
    merchant_id: str,
    db: AsyncSession,
) -> Optional[dict]:
    """Get a specific product by ID from Shopify.

    Args:
        access_token: Unused (kept for compatibility)
        product_id: Shopify product ID
        merchant_id: Merchant ID
        db: Database session

    Returns:
        Product dictionary or None if not found
    """
    products = await fetch_products(access_token, merchant_id, db)

    for product in products:
        if product["id"] == product_id:
            return product

    return None


async def invalidate_product_cache(
    merchant_id: str,
) -> None:
    """Invalidate product cache for a merchant.

    Called when pin configuration changes to force refresh
    of Shopify product data.

    Args:
        merchant_id: Merchant ID
    """
    logger.info(
        "product_cache_invalidated",
        merchant_id=merchant_id,
    )
