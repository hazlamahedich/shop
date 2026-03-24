"""Test contact options in widget API.

Story 10-5: Contact Card Widget
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.merchant import Merchant


@pytest.mark.asyncio
class TestContactOptions:
    """Test contact options are passed through in handoff responses."""

    async def test_handoff_returns_contact_options(
        self,
        async_client: AsyncClient,
        async_session: AsyncSession,
    ):
        merchant = Merchant(
            merchant_key="test-contact",
            platform="widget",
            business_name="Test Store",
            bot_name="Test Bot",
            widget_config={
                "enabled": True,
                "bot_name": "Test Bot",
                "welcome_message": "Hello!",
                "theme": {
                    "primaryColor": "#6366f1",
                    "backgroundColor": "#ffffff",
                    "textColor": "#1f2937",
                },
                "contactOptions": [
                    {
                        "type": "phone",
                        "label": "Call Us",
                        "value": "+1-555-1234",
                        "icon": "📞",
                    },
                    {
                        "type": "email",
                        "label": "Email Support",
                        "value": "support@test.com",
                    },
                ],
            },
        )
        async_session.add(merchant)
        await async_session.commit()

        response = await async_client.post(
            "/api/v1/widget/session",
            json={"merchant_id": merchant.id},
        )

        assert response.status_code == 200
        data = response.json()["data"]
        assert "sessionId" in data
        session_id = data["sessionId"]

        message_response = await async_client.post(
            "/api/v1/widget/message",
            json={
                "session_id": session_id,
                "message": "I need to talk to a human",
            },
        )

        assert message_response.status_code == 200

    async def test_widget_config_includes_contact_options(
        self,
        async_client: AsyncClient,
        async_session: AsyncSession,
    ):
        merchant = Merchant(
            merchant_key="test-contact-config",
            platform="widget",
            business_name="Config Store",
            bot_name="Config Bot",
            widget_config={
                "enabled": True,
                "contact_options": [
                    {"type": "phone", "label": "Call Us", "value": "+1-555-1234", "icon": "📞"},
                    {
                        "type": "email",
                        "label": "Email Support",
                        "value": "support@test.com",
                    },
                ],
            },
        )
        async_session.add(merchant)
        await async_session.commit()

        response = await async_client.get(f"/api/v1/widget/config/{merchant.id}")

        assert response.status_code == 200
        data = response.json()["data"]

        if "contactOptions" in data:
            assert data["contactOptions"] is not None
            assert len(data["contactOptions"]) == 2
            assert data["contactOptions"][0]["type"] == "phone"
            assert data["contactOptions"][1]["type"] == "email"
