#!/usr/bin/env python
"""Backfill customer names from Shopify Admin API for orders missing first/last name.

Finds all orders where customer_first_name IS NULL, groups by merchant,
fetches matching orders from Shopify, and updates names from the API response.

Usage:
    source venv/bin/activate
    python scripts/backfill_customer_names.py [--dry-run]
"""

from __future__ import annotations

import argparse
import asyncio
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session
from app.core.security import decrypt_access_token
from app.models.order import Order
from app.models.shopify_integration import ShopifyIntegration
from app.services.shopify.admin_client import ShopifyAdminClient


def extract_shopify_numeric_id(gid: str) -> str | None:
    m = re.search(r"/Order/(\d+)$", gid)
    return m.group(1) if m else None


def extract_names_from_shopify_order(shopify_order: dict) -> tuple[str | None, str | None]:
    customer = shopify_order.get("customer") or {}
    first = customer.get("first_name") or None
    last = customer.get("last_name") or None

    if not first or not last:
        shipping = shopify_order.get("shipping_address") or {}
        first = first or shipping.get("first_name") or None
        last = last or shipping.get("last_name") or None

    return first, last


async def get_credentials(db: AsyncSession, merchant_id: int) -> dict | None:
    result = await db.execute(
        select(ShopifyIntegration).where(ShopifyIntegration.merchant_id == merchant_id)
    )
    integration = result.scalar_one_or_none()
    if not integration or not integration.admin_api_verified:
        return None

    admin_token = decrypt_access_token(integration.admin_token_encrypted)
    return {"shop_domain": integration.shop_domain, "admin_token": admin_token}


async def fetch_order_from_shopify(client: ShopifyAdminClient, numeric_id: str) -> dict | None:
    import aiohttp

    url = f"{client.base_url}/orders/{numeric_id}.json"
    session = await client._get_session()
    try:
        async with session.get(url, headers=client._get_headers()) as resp:
            if resp.status == 200:
                data = await resp.json()
                return data.get("order")
            else:
                print(f"    Shopify API returned {resp.status} for order {numeric_id}")
                return None
    except Exception as e:
        print(f"    Error fetching order {numeric_id}: {e}")
        return None


async def backfill(dry_run: bool = False) -> None:
    async with async_session()() as db:
        result = await db.execute(
            select(Order).where(
                Order.customer_first_name.is_(None),
                Order.shopify_order_id.isnot(None),
            )
        )
        orders = result.scalars().all()

        if not orders:
            print("No orders found with missing customer names.")
            return

        print(f"Found {len(orders)} orders with missing customer names.")

        merchant_ids = {o.merchant_id for o in orders}
        credentials_cache: dict[int, dict | None] = {}

        updated_count = 0
        skipped_count = 0

        for merchant_id in merchant_ids:
            if merchant_id not in credentials_cache:
                credentials_cache[merchant_id] = await get_credentials(db, merchant_id)

            creds = credentials_cache[merchant_id]
            if not creds:
                print(f"  Skipping merchant {merchant_id}: no Shopify credentials")
                merchant_orders = [o for o in orders if o.merchant_id == merchant_id]
                skipped_count += len(merchant_orders)
                continue

            merchant_orders = [o for o in orders if o.merchant_id == merchant_id]
            print(
                f"\nMerchant {merchant_id} ({creds['shop_domain']}): {len(merchant_orders)} orders"
            )

            async with ShopifyAdminClient(creds["shop_domain"], creds["admin_token"]) as client:
                for order in merchant_orders:
                    shopify_id = order.shopify_order_id or ""
                    numeric_id = extract_shopify_numeric_id(shopify_id)
                    if not numeric_id:
                        print(
                            f"  Order {order.order_number}: cannot extract numeric ID from '{shopify_id}'"
                        )
                        skipped_count += 1
                        continue

                    shopify_order = await fetch_order_from_shopify(client, numeric_id)
                    if not shopify_order:
                        skipped_count += 1
                        continue

                    first, last = extract_names_from_shopify_order(shopify_order)
                    if not first and not last:
                        print(f"  Order {order.order_number}: no names found in Shopify data")
                        skipped_count += 1
                        continue

                    print(f"  Order {order.order_number}: {first or '(none)'} {last or '(none)'}")

                    if not dry_run:
                        await db.execute(
                            update(Order)
                            .where(Order.id == order.id)
                            .values(customer_first_name=first, customer_last_name=last)
                        )
                    updated_count += 1

                    await client.wait_for_rate_limit_if_needed(min_headroom=50)

        if not dry_run and updated_count > 0:
            await db.commit()

        action = "Would update" if dry_run else "Updated"
        print(f"\n{action} {updated_count} orders, skipped {skipped_count}")


async def backfill_profiles(dry_run: bool = False) -> None:
    from app.models.customer_profile import CustomerProfile

    async with async_session()() as db:
        result = await db.execute(
            select(CustomerProfile).where(CustomerProfile.first_name.is_(None))
        )
        profiles = result.scalars().all()

        if not profiles:
            print("No customer profiles with missing names.")
            return

        print(f"\nFound {len(profiles)} customer profiles with missing names.")
        updated = 0

        for profile in profiles:
            result = await db.execute(
                select(Order)
                .where(
                    Order.customer_email == profile.email,
                    Order.merchant_id == profile.merchant_id,
                    Order.customer_first_name.isnot(None),
                )
                .limit(1)
            )
            order = result.scalar_one_or_none()
            if not order:
                continue

            first = order.customer_first_name
            last = order.customer_last_name

            if not dry_run:
                await db.execute(
                    update(CustomerProfile)
                    .where(CustomerProfile.id == profile.id)
                    .values(first_name=first, last_name=last)
                )
            updated += 1
            print(f"  Profile {profile.email}: {first or '(none)'} {last or '(none)'}")

        if not dry_run and updated > 0:
            await db.commit()

        action = "Would update" if dry_run else "Updated"
        print(f"\n{action} {updated} customer profiles")


async def main() -> None:
    parser = argparse.ArgumentParser(description="Backfill customer names from Shopify")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without writing")
    args = parser.parse_args()

    print("=== Backfill: Order customer names ===\n")
    await backfill(dry_run=args.dry_run)

    print("\n=== Backfill: Customer profile names ===\n")
    await backfill_profiles(dry_run=args.dry_run)


if __name__ == "__main__":
    asyncio.run(main())
