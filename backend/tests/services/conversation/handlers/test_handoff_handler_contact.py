"""Test HandoffHandler contact options.

Story 10-5: Contact Card Widget
"""


from app.models.merchant import Merchant
from app.services.conversation.handlers.handoff_handler import HandoffHandler


class TestHandoffHandlerContactOptions:
    """Test contact options are extracted from merchant config."""

    def test_get_contact_options_returns_none_when_empty(self):
        """Test that _get_contact_options returns None when widget_config is empty."""
        handler = HandoffHandler()
        merchant = Merchant(
            merchant_key="test",
            platform="widget",
            widget_config=None,
        )

        result = handler._get_contact_options(merchant)
        assert result is None

    def test_get_contact_options_returns_options_when_configured(self):
        """Test that _get_contact_options returns contact options when configured."""
        handler = HandoffHandler()
        merchant = Merchant(
            merchant_key="test",
            platform="widget",
            widget_config={
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
                        "value": "support@example.com",
                    },
                ]
            },
        )

        result = handler._get_contact_options(merchant)

        assert result is not None
        assert len(result) == 2
        assert result[0]["type"] == "phone"
        assert result[0]["label"] == "Call Us"
        assert result[0]["value"] == "+1-555-1234"
        assert result[1]["type"] == "email"
        assert result[1]["label"] == "Email Support"

    def test_get_contact_options_filters_invalid_options(self):
        """Test that _get_contact_options filters out options missing required fields."""
        handler = HandoffHandler()
        merchant = Merchant(
            merchant_key="test",
            platform="widget",
            widget_config={
                "contactOptions": [
                    {
                        "type": "phone",
                        "label": "Valid",
                        "value": "+1-555-1234",
                    },
                    {
                        "type": "email",
                        "label": "Missing value",
                    },
                    {
                        "type": "custom",
                        "value": "https://example.com",
                    },
                ]
            },
        )

        result = handler._get_contact_options(merchant)

        assert result is not None
        assert len(result) == 1
        assert result[0]["label"] == "Valid"
