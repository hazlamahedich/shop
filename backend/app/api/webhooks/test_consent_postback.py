"""Unit tests for Facebook webhook consent postback handling.

Story 5-11: Messenger Unified Service Migration
GAP-4.3: Consent postback handler

Tests the consent postback handler that processes user responses to
cart consent prompts.

Priority Markers:
    @pytest.mark.p0 - Critical (run on every commit)
    @pytest.mark.p1 - High (run pre-merge)
    @pytest.mark.p2 - Medium (run nightly)

Test ID Format: 5.11-CONSENT-{SEQ} (e.g., 5.11-CONSENT-001)
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.schemas.messaging import MessengerResponse


@pytest.fixture
def psid() -> str:
    """Sample Facebook Page-Scoped ID."""
    return "psid_123456789"


class TestHandleConsentPostback:
    """Tests for handle_consent_postback().

    Test IDs: 5.11-CONSENT-001 through 5.11-CONSENT-010
    Priority: P1 (High) - cart consent is required for add operations.
    """

    @pytest.mark.asyncio
    @pytest.mark.p1
    @pytest.mark.test_id("5.11-CONSENT-001")
    async def test_non_consent_payload_returns_none(self, psid: str) -> None:
        """Test that non-consent payloads return None."""
        from app.api.webhooks.facebook import handle_consent_postback

        result = await handle_consent_postback(psid, "OTHER:payload")

        assert result is None

    @pytest.mark.asyncio
    @pytest.mark.p1
    @pytest.mark.test_id("5.11-CONSENT-002")
    async def test_invalid_format_returns_none(self, psid: str) -> None:
        """Test that invalid format returns None."""
        from app.api.webhooks.facebook import handle_consent_postback

        result = await handle_consent_postback(psid, "invalid")

        assert result is None

    @pytest.mark.asyncio
    @pytest.mark.p1
    @pytest.mark.test_id("5.11-CONSENT-003")
    async def test_consent_yes_records_consent(self, psid: str) -> None:
        """Test CONSENT:YES records consent."""
        from app.api.webhooks.facebook import handle_consent_postback

        mock_redis = AsyncMock()
        mock_redis.get.return_value = None
        mock_redis.close = AsyncMock()

        with (
            patch(
                "app.api.webhooks.facebook.settings",
                return_value={"REDIS_URL": "redis://localhost"},
            ),
            patch("app.api.webhooks.facebook.redis.from_url", return_value=mock_redis),
            patch("app.api.webhooks.facebook.ConsentService") as mock_consent_class,
        ):
            mock_consent = AsyncMock()
            mock_consent_class.return_value = mock_consent

            result = await handle_consent_postback(psid, "CONSENT:YES:prod_123:var_456")

            mock_consent.record_consent.assert_called_once_with(psid, consent_granted=True)

    @pytest.mark.asyncio
    @pytest.mark.p1
    @pytest.mark.test_id("5.11-CONSENT-004")
    async def test_consent_no_records_consent(self, psid: str) -> None:
        """Test CONSENT:NO records denied consent."""
        from app.api.webhooks.facebook import handle_consent_postback

        mock_redis = AsyncMock()
        mock_redis.close = AsyncMock()

        with (
            patch(
                "app.api.webhooks.facebook.settings",
                return_value={"REDIS_URL": "redis://localhost"},
            ),
            patch("app.api.webhooks.facebook.redis.from_url", return_value=mock_redis),
            patch("app.api.webhooks.facebook.ConsentService") as mock_consent_class,
        ):
            mock_consent = AsyncMock()
            mock_consent_class.return_value = mock_consent

            result = await handle_consent_postback(psid, "CONSENT:NO:prod_123:var_456")

            mock_consent.record_consent.assert_called_once_with(psid, consent_granted=False)

    @pytest.mark.asyncio
    @pytest.mark.p1
    @pytest.mark.test_id("5.11-CONSENT-005")
    async def test_consent_yes_with_pending_cart_adds_item(self, psid: str) -> None:
        """Test CONSENT:YES with pending cart data adds item to cart."""
        from app.api.webhooks.facebook import handle_consent_postback
        import json

        pending_data = {
            "product_id": "prod_123",
            "variant_id": "var_456",
            "title": "Test Product",
            "price": 29.99,
            "image_url": "https://example.com/image.jpg",
            "currency_code": "USD",
        }

        mock_redis = AsyncMock()
        mock_redis.get.return_value = json.dumps(pending_data)
        mock_redis.delete = AsyncMock()
        mock_redis.close = AsyncMock()

        mock_cart = MagicMock()
        mock_cart.item_count = 1

        with (
            patch(
                "app.api.webhooks.facebook.settings",
                return_value={"REDIS_URL": "redis://localhost"},
            ),
            patch("app.api.webhooks.facebook.redis.from_url", return_value=mock_redis),
            patch("app.api.webhooks.facebook.ConsentService") as mock_consent_class,
            patch("app.api.webhooks.facebook.CartService") as mock_cart_class,
        ):
            mock_consent = AsyncMock()
            mock_consent_class.return_value = mock_consent

            mock_cart_service = AsyncMock()
            mock_cart_service.add_item.return_value = mock_cart
            mock_cart_class.return_value = mock_cart_service

            result = await handle_consent_postback(psid, "CONSENT:YES:prod_123:var_456")

            assert result is not None
            assert isinstance(result, MessengerResponse)
            assert "added" in result.text.lower()
            assert "Test Product" in result.text
            mock_redis.delete.assert_called_once_with(f"pending_cart:{psid}")

    @pytest.mark.asyncio
    @pytest.mark.p1
    @pytest.mark.test_id("5.11-CONSENT-006")
    async def test_consent_yes_expired_pending_returns_error(self, psid: str) -> None:
        """Test CONSENT:YES with expired pending cart returns error message."""
        from app.api.webhooks.facebook import handle_consent_postback

        mock_redis = AsyncMock()
        mock_redis.get.return_value = None
        mock_redis.close = AsyncMock()

        with (
            patch(
                "app.api.webhooks.facebook.settings",
                return_value={"REDIS_URL": "redis://localhost"},
            ),
            patch("app.api.webhooks.facebook.redis.from_url", return_value=mock_redis),
            patch("app.api.webhooks.facebook.ConsentService") as mock_consent_class,
        ):
            mock_consent = AsyncMock()
            mock_consent_class.return_value = mock_consent

            result = await handle_consent_postback(psid, "CONSENT:YES:prod_123:var_456")

            assert result is not None
            assert "expired" in result.text.lower()

    @pytest.mark.asyncio
    @pytest.mark.p2
    @pytest.mark.test_id("5.11-CONSENT-007")
    async def test_consent_no_returns_friendly_message(self, psid: str) -> None:
        """Test CONSENT:NO returns friendly message."""
        from app.api.webhooks.facebook import handle_consent_postback

        mock_redis = AsyncMock()
        mock_redis.close = AsyncMock()

        with (
            patch(
                "app.api.webhooks.facebook.settings",
                return_value={"REDIS_URL": "redis://localhost"},
            ),
            patch("app.api.webhooks.facebook.redis.from_url", return_value=mock_redis),
            patch("app.api.webhooks.facebook.ConsentService") as mock_consent_class,
        ):
            mock_consent = AsyncMock()
            mock_consent_class.return_value = mock_consent

            result = await handle_consent_postback(psid, "CONSENT:NO:prod_123:var_456")

            assert result is not None
            assert "no problem" in result.text.lower()

    @pytest.mark.asyncio
    @pytest.mark.p2
    @pytest.mark.test_id("5.11-CONSENT-008")
    async def test_consent_handles_exception(self, psid: str) -> None:
        """Test consent handles exceptions gracefully."""
        from app.api.webhooks.facebook import handle_consent_postback

        with (
            patch(
                "app.api.webhooks.facebook.settings",
                side_effect=Exception("Config error"),
            ),
        ):
            result = await handle_consent_postback(psid, "CONSENT:YES:prod_123:var_456")

            assert result is not None
            assert "error" in result.text.lower()

    @pytest.mark.asyncio
    @pytest.mark.p2
    @pytest.mark.test_id("5.11-CONSENT-009")
    async def test_consent_closes_redis_connection(self, psid: str) -> None:
        """Test that Redis connection is closed after handling."""
        from app.api.webhooks.facebook import handle_consent_postback

        mock_redis = AsyncMock()
        mock_redis.get.return_value = None
        mock_redis.close = AsyncMock()

        with (
            patch(
                "app.api.webhooks.facebook.settings",
                return_value={"REDIS_URL": "redis://localhost"},
            ),
            patch("app.api.webhooks.facebook.redis.from_url", return_value=mock_redis),
            patch("app.api.webhooks.facebook.ConsentService") as mock_consent_class,
        ):
            mock_consent = AsyncMock()
            mock_consent_class.return_value = mock_consent

            await handle_consent_postback(psid, "CONSENT:NO:prod_123:var_456")

            mock_redis.close.assert_called_once()

    @pytest.mark.asyncio
    @pytest.mark.p2
    @pytest.mark.test_id("5.11-CONSENT-010")
    async def test_consent_missing_variant_id(self, psid: str) -> None:
        """Test consent with missing variant ID returns friendly message."""
        from app.api.webhooks.facebook import handle_consent_postback

        mock_redis = AsyncMock()
        mock_redis.get.return_value = None
        mock_redis.close = AsyncMock()

        with (
            patch(
                "app.api.webhooks.facebook.settings",
                return_value={"REDIS_URL": "redis://localhost"},
            ),
            patch("app.api.webhooks.facebook.redis.from_url", return_value=mock_redis),
            patch("app.api.webhooks.facebook.ConsentService") as mock_consent_class,
        ):
            mock_consent = AsyncMock()
            mock_consent_class.return_value = mock_consent

            result = await handle_consent_postback(psid, "CONSENT:YES:prod_123")

            assert result is not None
            assert "no problem" in result.text.lower() or "expired" in result.text.lower()
