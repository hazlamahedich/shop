import asyncio

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.security import decrypt_access_token
from app.models.merchant import Merchant
from app.services.shopify_oauth import ShopifyService


async def test_logic():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        from app.core.database import Base

        await conn.run_sync(Base.metadata.create_all)

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        service = ShopifyService(db, is_testing=True)

        # Test 1: Save Credentials
        merchant = Merchant(id=1, email="test@example.com", name="Test Merchant", config={})
        db.add(merchant)
        await db.commit()

        await service.save_shopify_credentials(1, "my_api_key", "my_api_secret")

        await db.refresh(merchant)
        print(f"Merchant config: {merchant.config}")
        assert merchant.config["shopify_api_key"] == "my_api_key"
        assert (
            decrypt_access_token(merchant.config["shopify_api_secret_encrypted"]) == "my_api_secret"
        )
        print("Test 1 Passed: Credentials saved & encrypted correctly.")

        # Test 2: Prioritize Credentials in generate_oauth_url
        # We need to mock settings for this, or just check the logic in generate_oauth_url
        # Actually generate_oauth_url calls settings() directly.

        print("Diagnostic Complete.")


if __name__ == "__main__":
    asyncio.run(test_logic())
