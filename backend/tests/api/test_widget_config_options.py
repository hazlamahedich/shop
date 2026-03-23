import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.merchant import Merchant


@pytest.mark.asyncio
async def test_update_widget_config_contact_options(
    async_client: AsyncClient,
    async_session: AsyncSession,
):
    """Test updating widget configuration with contact options."""
    # Ensure merchant exists (merchant_id=1 is default for debug)
    merchant = await async_session.get(Merchant, 1)
    if not merchant:
        merchant = Merchant(
            id=1,
            merchant_key="test-merchant",
            platform="shopify",
            widget_config={}
        )
        async_session.add(merchant)
        await async_session.commit()

    # Initial state
    response = await async_client.get(
        "/api/v1/merchants/widget-config",
        headers={"X-Merchant-Id": "1"}
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert "contactOptions" in data

    # Update contact options
    update_data = {
        "contactOptions": [
            {
                "type": "email",
                "label": "Neural Support",
                "value": "neural@antigravity.ai",
                "icon": "mail"
            },
            {
                "type": "phone",
                "label": "Direct Link",
                "value": "+123456789",
                "icon": "phone"
            }
        ]
    }
    
    response = await async_client.patch(
        "/api/v1/merchants/widget-config",
        json=update_data,
        headers={"X-Merchant-Id": "1"}
    )
    assert response.status_code == 200
    
    # Verify persistence
    response = await async_client.get(
        "/api/v1/merchants/widget-config",
        headers={"X-Merchant-Id": "1"}
    )
    assert response.status_code == 200
    config = response.json()["data"]
    assert len(config["contactOptions"]) == 2
    assert config["contactOptions"][0]["label"] == "Neural Support"
    assert config["contactOptions"][1]["type"] == "phone"
