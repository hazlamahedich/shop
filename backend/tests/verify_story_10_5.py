
import asyncio

from sqlalchemy import select, update

from app.core.database import async_session
from app.models.merchant import Merchant


async def verify_contact_options():
    print("Starting verification for Story 10-5: Contact Card Widget")

    async with async_session() as db:
        # 1. Find a test merchant (or use ID 1)
        result = await db.execute(select(Merchant).order_by(Merchant.id).limit(1))
        merchant = result.scalars().first()

        if not merchant:
            print("No merchant found to test with.")
            return

        print(f"Testing with merchant: {merchant.business_name} (ID: {merchant.id})")

        # 2. Set contact options
        contact_options = [
            {"type": "phone", "label": "Call Support", "value": "+1234567890"},
            {"type": "email", "label": "Email Us", "value": "support@example.com"},
            {"type": "custom", "label": "Help Center", "value": "https://help.example.com"}
        ]

        await db.execute(
            update(Merchant)
            .where(Merchant.id == merchant.id)
            .values(contact_options=contact_options)
        )
        await db.commit()
        print("Updated merchant with contact_options.")

        # 3. Verify the update
        await db.refresh(merchant)
        print(f"Merchant contact_options from DB: {merchant.contact_options}")

        if merchant.contact_options != contact_options:
            print("ERROR: contact_options mismatch in DB!")
            print(f"Expected: {contact_options}")
            print(f"Actual: {merchant.contact_options}")
            return

        print("SUCCESS: Database persistence verified.")

if __name__ == "__main__":
    asyncio.run(verify_contact_options())
