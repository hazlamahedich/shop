"""Comprehensive tests for checkout URL validation (NFR-S9).

Tests cover:
- Checkout URL generation with validation
- URL validation via HTTP HEAD request
- Retry logic for failed validations
- Timeout handling
- Redirect handling
- Edge cases and error conditions
"""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import HTTPStatusError, RequestError, TimeoutException

from app.services.shopify_storefront import ShopifyStorefrontClient
from app.core.errors import APIError, ErrorCode


class TestCheckoutURLValidation:
    """Comprehensive tests for checkout URL validation (NFR-S9)."""

    @pytest.mark.asyncio
    async def test_valid_checkout_url_passes_validation(self):
        """Test that valid checkout URL passes validation."""
        client = ShopifyStorefrontClient(
            shop_domain="test.myshopify.com",
            access_token="test_token",
            is_testing=False
        )

        # Mock HTTP client
        mock_response = MagicMock()
        mock_response.status_code = 200
        client.async_client.head = AsyncMock(return_value=mock_response)

        checkout_url = "https://checkout.shopify.com/12345"
        result = await client._validate_checkout_url(checkout_url)

        assert result is True
        client.async_client.head.assert_called_once_with(
            checkout_url,
            follow_redirects=True,
            timeout=5.0
        )

    @pytest.mark.asyncio
    async def test_invalid_checkout_url_fails_validation(self):
        """Test that invalid checkout URL fails validation."""
        client = ShopifyStorefrontClient(
            shop_domain="test.myshopify.com",
            access_token="test_token",
            is_testing=False
        )

        # Mock HTTP client to return non-200 status
        mock_response = MagicMock()
        mock_response.status_code = 404
        client.async_client.head = AsyncMock(return_value=mock_response)

        checkout_url = "https://invalid-url.com"
        result = await client._validate_checkout_url(checkout_url)

        assert result is False

    @pytest.mark.asyncio
    async def test_checkout_url_validation_with_timeout(self):
        """Test checkout URL validation handles timeout."""
        client = ShopifyStorefrontClient(
            shop_domain="test.myshopify.com",
            access_token="test_token",
            is_testing=False
        )

        # Mock timeout exception
        client.async_client.head = AsyncMock(
            side_effect=TimeoutException("Request timed out")
        )

        checkout_url = "https://checkout.shopify.com/12345"
        result = await client._validate_checkout_url(checkout_url)

        assert result is False

    @pytest.mark.asyncio
    async def test_checkout_url_validation_with_connection_error(self):
        """Test checkout URL validation handles connection errors."""
        client = ShopifyStorefrontClient(
            shop_domain="test.myshopify.com",
            access_token="test_token",
            is_testing=False
        )

        # Mock connection error
        client.async_client.head = AsyncMock(
            side_effect=RequestError("Connection error")
        )

        checkout_url = "https://checkout.shopify.com/12345"
        result = await client._validate_checkout_url(checkout_url)

        assert result is False

    @pytest.mark.asyncio
    async def test_checkout_url_validation_with_http_error(self):
        """Test checkout URL validation handles HTTP errors."""
        client = ShopifyStorefrontClient(
            shop_domain="test.myshopify.com",
            access_token="test_token",
            is_testing=False
        )

        # Mock HTTP error
        client.async_client.head = AsyncMock(
            side_effect=HTTPStatusError(
                "Server error",
                request=MagicMock(),
                response=MagicMock(status_code=500)
            )
        )

        checkout_url = "https://checkout.shopify.com/12345"
        result = await client._validate_checkout_url(checkout_url)

        assert result is False

    @pytest.mark.asyncio
    async def test_checkout_url_validation_with_redirect(self):
        """Test checkout URL validation follows redirects."""
        client = ShopifyStorefrontClient(
            shop_domain="test.myshopify.com",
            access_token="test_token",
            is_testing=False
        )

        # Mock redirect response (should follow and get final status)
        mock_response = MagicMock()
        mock_response.status_code = 200
        client.async_client.head = AsyncMock(return_value=mock_response)

        checkout_url = "https://checkout.shopify.com/12345"
        result = await client._validate_checkout_url(checkout_url)

        assert result is True


class TestCheckoutURLGenerationWithValidation:
    """Tests for checkout URL generation with built-in validation."""

    @pytest.mark.asyncio
    async def test_create_checkout_url_validates_before_return(self):
        """Test that checkout URL is validated before being returned (NFR-S9)."""
        client = ShopifyStorefrontClient(
            shop_domain="test.myshopify.com",
            access_token="test_token",
            is_testing=False
        )

        # Mock POST response for checkout creation
        mock_post_response = MagicMock()
        mock_post_response.status_code = 200
        mock_post_response.json.return_value = {
            "data": {
                "checkoutCreate": {
                    "checkout": {
                        "webUrl": "https://checkout.shopify.com/12345"
                    },
                    "checkoutUserErrors": []
                }
            }
        }
        client.async_client.post = AsyncMock(return_value=mock_post_response)

        # Mock HEAD response for URL validation
        mock_head_response = MagicMock()
        mock_head_response.status_code = 200
        client.async_client.head = AsyncMock(return_value=mock_head_response)

        items = [{"variant_id": "gid://shopify/ProductVariant/1", "quantity": 2}]
        checkout_url = await client.create_checkout_url(items)

        assert checkout_url == "https://checkout.shopify.com/12345"
        # Verify validation was called
        client.async_client.head.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_checkout_url_fails_on_invalid_url(self):
        """Test that invalid checkout URL raises error (NFR-S9)."""
        client = ShopifyStorefrontClient(
            shop_domain="test.myshopify.com",
            access_token="test_token",
            is_testing=False
        )

        # Mock POST response for checkout creation
        mock_post_response = MagicMock()
        mock_post_response.status_code = 200
        mock_post_response.json.return_value = {
            "data": {
                "checkoutCreate": {
                    "checkout": {
                        "webUrl": "https://invalid-checkout.com"
                    },
                    "checkoutUserErrors": []
                }
            }
        }
        client.async_client.post = AsyncMock(return_value=mock_post_response)

        # Mock HEAD response to return 404 (invalid URL)
        mock_head_response = MagicMock()
        mock_head_response.status_code = 404
        client.async_client.head = AsyncMock(return_value=mock_head_response)

        items = [{"variant_id": "gid://shopify/ProductVariant/1", "quantity": 2}]

        with pytest.raises(APIError) as exc_info:
            await client.create_checkout_url(items)

        assert exc_info.value.code == ErrorCode.SHOPIFY_CHECKOUT_URL_INVALID

    @pytest.mark.asyncio
    async def test_create_checkout_url_handles_validation_timeout(self):
        """Test checkout creation handles validation timeout gracefully."""
        client = ShopifyStorefrontClient(
            shop_domain="test.myshopify.com",
            access_token="test_token",
            is_testing=False
        )

        # Mock POST response for checkout creation
        mock_post_response = MagicMock()
        mock_post_response.status_code = 200
        mock_post_response.json.return_value = {
            "data": {
                "checkoutCreate": {
                    "checkout": {
                        "webUrl": "https://checkout.shopify.com/12345"
                    },
                    "checkoutUserErrors": []
                }
            }
        }
        client.async_client.post = AsyncMock(return_value=mock_post_response)

        # Mock validation timeout
        client.async_client.head = AsyncMock(
            side_effect=TimeoutException("Validation timeout")
        )

        items = [{"variant_id": "gid://shopify/ProductVariant/1", "quantity": 2}]

        with pytest.raises(APIError) as exc_info:
            await client.create_checkout_url(items)

        assert exc_info.value.code == ErrorCode.SHOPIFY_CHECKOUT_URL_INVALID

    @pytest.mark.asyncio
    async def test_create_checkout_url_in_testing_mode_skips_validation(self):
        """Test that testing mode skips validation and returns mock URL."""
        client = ShopifyStorefrontClient(
            shop_domain="test.myshopify.com",
            access_token="test_token",
            is_testing=True
        )

        items = [{"variant_id": "gid://shopify/ProductVariant/1", "quantity": 2}]
        checkout_url = await client.create_checkout_url(items)

        assert checkout_url == "https://checkout.shopify.com/test"
        # No HTTP calls should be made in testing mode
        assert not hasattr(client, '_async_client') or client._async_client is None


class TestCheckoutURLErrorHandling:
    """Tests for error handling in checkout URL validation."""

    @pytest.mark.asyncio
    async def test_malformed_checkout_url(self):
        """Test handling of malformed checkout URLs."""
        client = ShopifyStorefrontClient(
            shop_domain="test.myshopify.com",
            access_token="test_token",
            is_testing=False
        )

        # Mock POST response with malformed URL
        mock_post_response = MagicMock()
        mock_post_response.status_code = 200
        mock_post_response.json.return_value = {
            "data": {
                "checkoutCreate": {
                    "checkout": {
                        "webUrl": "not-a-valid-url"
                    },
                    "checkoutUserErrors": []
                }
            }
        }
        client.async_client.post = AsyncMock(return_value=mock_post_response)

        # Validation should fail for malformed URL
        client.async_client.head = AsyncMock(
            side_effect=RequestError("Invalid URL")
        )

        items = [{"variant_id": "gid://shopify/ProductVariant/1", "quantity": 2}]

        with pytest.raises(APIError) as exc_info:
            await client.create_checkout_url(items)

        assert exc_info.value.code == ErrorCode.SHOPIFY_CHECKOUT_URL_INVALID

    @pytest.mark.asyncio
    async def test_empty_checkout_url_from_api(self):
        """Test handling of empty checkout URL from API."""
        client = ShopifyStorefrontClient(
            shop_domain="test.myshopify.com",
            access_token="test_token",
            is_testing=False
        )

        # Mock POST response with empty URL
        mock_post_response = MagicMock()
        mock_post_response.status_code = 200
        mock_post_response.json.return_value = {
            "data": {
                "checkoutCreate": {
                    "checkout": {
                        "webUrl": None
                    },
                    "checkoutUserErrors": []
                }
            }
        }
        client.async_client.post = AsyncMock(return_value=mock_post_response)

        items = [{"variant_id": "gid://shopify/ProductVariant/1", "quantity": 2}]

        with pytest.raises(APIError) as exc_info:
            await client.create_checkout_url(items)

        assert exc_info.value.code == ErrorCode.SHOPIFY_CHECKOUT_CREATE_FAILED

    @pytest.mark.asyncio
    async def test_checkout_with_user_errors(self):
        """Test handling of checkout creation with user errors."""
        client = ShopifyStorefrontClient(
            shop_domain="test.myshopify.com",
            access_token="test_token",
            is_testing=False
        )

        # Mock POST response with user errors
        mock_post_response = MagicMock()
        mock_post_response.status_code = 200
        mock_post_response.json.return_value = {
            "data": {
                "checkoutCreate": {
                    "checkout": {
                        "webUrl": "https://checkout.shopify.com/12345"
                    },
                    "checkoutUserErrors": [
                        {
                            "code": "INVALID_PRODUCT",
                            "field": ["lineItems"],
                            "message": "Product is not available"
                        }
                    ]
                }
            }
        }
        client.async_client.post = AsyncMock(return_value=mock_post_response)

        items = [{"variant_id": "gid://shopify/ProductVariant/1", "quantity": 2}]

        with pytest.raises(APIError) as exc_info:
            await client.create_checkout_url(items)

        assert exc_info.value.code == ErrorCode.SHOPIFY_CHECKOUT_CREATE_FAILED

    @pytest.mark.asyncio
    async def test_checkout_with_api_errors(self):
        """Test handling of checkout creation with API errors."""
        client = ShopifyStorefrontClient(
            shop_domain="test.myshopify.com",
            access_token="test_token",
            is_testing=False
        )

        # Mock POST response with API errors
        mock_post_response = MagicMock()
        mock_post_response.status_code = 200
        mock_post_response.json.return_value = {
            "errors": [
                {
                    "message": "API rate limit exceeded",
                    "code": "RATE_LIMIT"
                }
            ]
        }
        client.async_client.post = AsyncMock(return_value=mock_post_response)

        items = [{"variant_id": "gid://shopify/ProductVariant/1", "quantity": 2}]

        with pytest.raises(APIError) as exc_info:
            await client.create_checkout_url(items)

        assert exc_info.value.code == ErrorCode.SHOPIFY_CHECKOUT_CREATE_FAILED


class TestCheckoutURLRetryLogic:
    """Tests for retry logic in checkout URL validation (future enhancement)."""

    @pytest.mark.asyncio
    async def test_validation_failure_no_retry_current(self):
        """Test that validation currently does not retry on failure.

        NOTE: Future enhancement should add retry logic with exponential backoff.
        Current implementation fails immediately on validation error.
        """
        client = ShopifyStorefrontClient(
            shop_domain="test.myshopify.com",
            access_token="test_token",
            is_testing=False
        )

        # Mock POST response
        mock_post_response = MagicMock()
        mock_post_response.status_code = 200
        mock_post_response.json.return_value = {
            "data": {
                "checkoutCreate": {
                    "checkout": {
                        "webUrl": "https://checkout.shopify.com/12345"
                    },
                    "checkoutUserErrors": []
                }
            }
        }
        client.async_client.post = AsyncMock(return_value=mock_post_response)

        # Mock validation to fail once
        mock_head_response = MagicMock()
        mock_head_response.status_code = 503
        client.async_client.head = AsyncMock(return_value=mock_head_response)

        items = [{"variant_id": "gid://shopify/ProductVariant/1", "quantity": 2}]

        with pytest.raises(APIError):
            await client.create_checkout_url(items)

        # Current implementation calls validation only once (no retry)
        assert client.async_client.head.call_count == 1
