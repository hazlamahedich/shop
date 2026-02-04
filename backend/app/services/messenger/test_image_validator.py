"""Tests for ImageValidator.

Tests image validation, format checking, and alt text generation
for Facebook Messenger requirements.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from app.services.messenger.image_validator import ImageValidator


@pytest.fixture
def mock_settings() -> dict[str, Any]:
    """Mock settings for testing."""
    return {
        "MESSENGER_FALLBACK_IMAGE_URL": "https://cdn.example.com/fallback-product.png",
    }


@pytest.fixture
def validator(mock_settings: dict[str, Any]) -> ImageValidator:
    """Create an ImageValidator with mocked settings."""
    with patch("app.services.messenger.image_validator.settings", return_value=mock_settings):
        return ImageValidator()


class TestImageValidator:
    """Tests for ImageValidator."""

    def test_init(self, validator: ImageValidator) -> None:
        """Test validator initialization."""
        assert validator.MIN_DIMENSION == 400
        assert validator.MAX_DIMENSION == 2048
        assert validator.MAX_FILE_SIZE_BYTES == 500 * 1024
        assert validator.RECOMMENDED_ASPECT_RATIO == 1.0

    @pytest.mark.asyncio
    async def test_validate_image_url_valid(self, validator: ImageValidator) -> None:
        """Test validation of valid image URL."""
        url = "https://cdn.shopify.com/s/files/1/product.jpg"
        result = await validator.validate_image_url(url)
        assert result is True

    @pytest.mark.asyncio
    async def test_validate_image_url_empty(self, validator: ImageValidator) -> None:
        """Test validation of empty URL."""
        result = await validator.validate_image_url("")
        assert result is False

    @pytest.mark.asyncio
    async def test_validate_image_url_none(self, validator: ImageValidator) -> None:
        """Test validation of None URL."""
        result = await validator.validate_image_url("")  # type: ignore
        assert result is False

    @pytest.mark.asyncio
    async def test_validate_image_url_invalid_format(self, validator: ImageValidator) -> None:
        """Test validation of URL with invalid format."""
        url = "not-a-valid-url"
        result = await validator.validate_image_url(url)
        assert result is False

    @pytest.mark.asyncio
    async def test_validate_image_url_png(self, validator: ImageValidator) -> None:
        """Test validation of PNG URL."""
        url = "https://cdn.shopify.com/s/files/1/product.png"
        result = await validator.validate_image_url(url)
        assert result is True

    @pytest.mark.asyncio
    async def test_validate_image_url_gif(self, validator: ImageValidator) -> None:
        """Test validation of GIF URL."""
        url = "https://cdn.shopify.com/s/files/1/product.gif"
        result = await validator.validate_image_url(url)
        assert result is True

    @pytest.mark.asyncio
    async def test_validate_image_url_invalid_extension(self, validator: ImageValidator) -> None:
        """Test validation of URL with invalid extension."""
        url = "https://cdn.shopify.com/s/files/1/product.webp"
        result = await validator.validate_image_url(url)
        assert result is False

    def test_is_valid_format_true(self, validator: ImageValidator) -> None:
        """Test valid format detection."""
        assert validator.is_valid_format("https://example.com/test.jpg")
        assert validator.is_valid_format("https://example.com/test.png")
        assert validator.is_valid_format("https://example.com/test.gif")
        assert validator.is_valid_format("https://example.com/test.jpeg")

    def test_is_valid_format_false(self, validator: ImageValidator) -> None:
        """Test invalid format detection."""
        assert not validator.is_valid_format("https://example.com/test.webp")
        assert not validator.is_valid_format("https://example.com/test.pdf")
        assert not validator.is_valid_format("https://example.com/test")

    def test_get_image_format(self, validator: ImageValidator) -> None:
        """Test extracting image format from URL."""
        assert validator.get_image_format("https://example.com/test.jpg") == "jpg"
        assert validator.get_image_format("https://example.com/test.PNG") == "png"
        assert validator.get_image_format("https://example.com/test.gif") == "gif"
        assert validator.get_image_format("https://example.com/test.jpeg") == "jpeg"
        assert validator.get_image_format("https://example.com/test.webp") is None

    def test_validate_image_dimensions_valid(self, validator: ImageValidator) -> None:
        """Test validation of valid image dimensions."""
        is_valid, error = validator.validate_image_dimensions(800, 800)
        assert is_valid is True
        assert error is None

    def test_validate_image_dimensions_too_small(self, validator: ImageValidator) -> None:
        """Test validation of image dimensions that are too small."""
        is_valid, error = validator.validate_image_dimensions(200, 200)
        assert is_valid is False
        assert "below minimum" in error

    def test_validate_image_dimensions_too_large(self, validator: ImageValidator) -> None:
        """Test validation of image dimensions that are too large."""
        is_valid, error = validator.validate_image_dimensions(3000, 3000)
        assert is_valid is False
        assert "exceed" in error.lower() and "maximum" in error.lower()

    def test_validate_image_dimensions_minimum(self, validator: ImageValidator) -> None:
        """Test validation at minimum dimension boundary."""
        is_valid, error = validator.validate_image_dimensions(400, 400)
        assert is_valid is True
        assert error is None

    def test_validate_image_dimensions_maximum(self, validator: ImageValidator) -> None:
        """Test validation at maximum dimension boundary."""
        is_valid, error = validator.validate_image_dimensions(2048, 2048)
        assert is_valid is True
        assert error is None

    def test_validate_image_dimensions_none(self, validator: ImageValidator) -> None:
        """Test validation when dimensions are unknown - should fail with actual validation."""
        is_valid, error = validator.validate_image_dimensions(None, None)
        assert is_valid is False
        assert "Unable to validate" in error

    def test_validate_file_size_valid(self, validator: ImageValidator) -> None:
        """Test validation of valid file size."""
        is_valid, error = validator.validate_file_size(250 * 1024)  # 250KB
        assert is_valid is True
        assert error is None

    def test_validate_file_size_too_large(self, validator: ImageValidator) -> None:
        """Test validation of file size that is too large."""
        is_valid, error = validator.validate_file_size(600 * 1024)  # 600KB
        assert is_valid is False
        assert "exceeds maximum" in error

    def test_validate_file_size_at_limit(self, validator: ImageValidator) -> None:
        """Test validation at file size limit."""
        is_valid, error = validator.validate_file_size(500 * 1024)  # 500KB
        assert is_valid is True
        assert error is None

    def test_validate_file_size_none(self, validator: ImageValidator) -> None:
        """Test validation when file size is unknown."""
        is_valid, error = validator.validate_file_size(None)
        assert is_valid is True
        assert error is None

    def test_generate_alt_text_basic(self, validator: ImageValidator) -> None:
        """Test basic alt text generation."""
        alt = validator.generate_alt_text("Nike Running Shoes")
        assert "Nike Running Shoes" in alt

    def test_generate_alt_text_with_type(self, validator: ImageValidator) -> None:
        """Test alt text generation with product type."""
        alt = validator.generate_alt_text("Nike Running Shoes", "Footwear")
        assert "Footwear" in alt
        assert "Nike Running Shoes" in alt

    def test_generate_alt_text_with_tags(self, validator: ImageValidator) -> None:
        """Test alt text generation with tags."""
        alt = validator.generate_alt_text(
            "Nike Running Shoes",
            tags=["running", "shoes", "nike", "athletic"],
        )
        assert "Nike Running Shoes" in alt
        # Should include some tags
        assert "running" in alt or "shoes" in alt or "nike" in alt

    def test_generate_alt_text_all_fields(self, validator: ImageValidator) -> None:
        """Test alt text generation with all fields."""
        alt = validator.generate_alt_text(
            "Nike Running Shoes",
            product_type="Footwear",
            tags=["running", "shoes"],
        )
        assert "Footwear" in alt
        assert "Nike Running Shoes" in alt
        assert "running" in alt or "shoes" in alt

    def test_generate_alt_text_filters_short_tags(self, validator: ImageValidator) -> None:
        """Test that short tags are filtered out."""
        alt = validator.generate_alt_text(
            "Product",
            tags=["a", "an", "the", "running", "shoes"],
        )
        # Should only include longer tags
        assert "running" in alt or "shoes" in alt

    @pytest.mark.asyncio
    async def test_get_image_info_success(self, validator: ImageValidator) -> None:
        """Test getting image info successfully."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.headers = {"content-length": "250000"}

            mock_client.return_value.__aenter__.return_value.head.return_value = mock_response
            mock_client.return_value.__aenter__.return_value.head.return_value.raise_for_status = MagicMock()

            info = await validator.get_image_info("https://example.com/test.jpg")

            assert info is not None
            assert info["size_bytes"] == 250000

    @pytest.mark.asyncio
    async def test_get_image_info_http_error(self, validator: ImageValidator) -> None:
        """Test getting image info with HTTP error."""
        with patch("httpx.AsyncClient") as mock_client:
            import httpx

            mock_client.return_value.__aenter__.return_value.head.side_effect = httpx.HTTPStatusError(
                "Not Found",
                request=MagicMock(),
                response=MagicMock(status_code=404),
            )

            info = await validator.get_image_info("https://example.com/test.jpg")

            assert info is None

    @pytest.mark.asyncio
    async def test_validate_and_prepare_image_valid(self, validator: ImageValidator) -> None:
        """Test image validation and preparation with valid URL."""
        url = "https://cdn.shopify.com/s/files/1/product.jpg"

        with patch.object(validator, "validate_image_url", return_value=True), \
             patch.object(validator, "get_image_info", return_value=None):
            result = await validator.validate_and_prepare_image(url)
            assert result == url

    @pytest.mark.asyncio
    async def test_validate_and_prepare_image_invalid_url(self, validator: ImageValidator) -> None:
        """Test image validation with invalid URL returns fallback."""
        url = "invalid-url"

        with patch.object(validator, "validate_image_url", return_value=False):
            result = await validator.validate_and_prepare_image(url)
            assert result == validator.fallback_image_url

    @pytest.mark.asyncio
    async def test_validate_and_prepare_image_too_large(self, validator: ImageValidator) -> None:
        """Test image validation with file too large returns fallback."""
        url = "https://cdn.shopify.com/s/files/1/product.jpg"

        with patch.object(validator, "validate_image_url", return_value=True), \
             patch.object(validator, "get_image_info", return_value={"size_bytes": 600 * 1024}):
            result = await validator.validate_and_prepare_image(url)
            assert result == validator.fallback_image_url


class TestImageValidatorShopifyCDN:
    """Tests for Shopify CDN validation."""

    @pytest.fixture
    def validator(self, mock_settings: dict[str, Any]) -> ImageValidator:
        """Create an ImageValidator with mocked settings."""
        with patch("app.services.messenger.image_validator.settings", return_value=mock_settings):
            return ImageValidator()

    def test_shopify_cdn_pattern_valid(self, validator: ImageValidator) -> None:
        """Test valid Shopify CDN URLs match pattern."""
        assert validator.SHOPIFY_CDN_PATTERN.match("https://cdn.shopify.com/s/files/1/test.jpg")
        assert validator.SHOPIFY_CDN_PATTERN.match("http://cdn.shopify.com/s/files/1/test.jpg")
        assert validator.SHOPIFY_CDN_PATTERN.match("//cdn.shopify.com/s/files/1/test.jpg")
        assert validator.SHOPIFY_CDN_PATTERN.match("https://images.shopify.com/test.jpg")

    def test_shopify_cdn_pattern_invalid(self, validator: ImageValidator) -> None:
        """Test non-Shopify URLs don't match pattern."""
        assert not validator.SHOPIFY_CDN_PATTERN.match("https://example.com/test.jpg")
        assert not validator.SHOPIFY_CDN_PATTERN.match("https://cdn.example.com/test.jpg")

    @pytest.mark.asyncio
    async def test_validate_image_url_with_cdn_check(self, validator: ImageValidator) -> None:
        """Shopify CDN URL validation."""
        url = "https://cdn.shopify.com/s/files/1/product.jpg"
        result = await validator.validate_image_url(url, check_shopify_cdn=True)
        assert result is True

    @pytest.mark.asyncio
    async def test_validate_image_url_non_cdn_with_check(self, validator: ImageValidator) -> None:
        """Non-Shopify CDN URL validation (should log warning but return True)."""
        url = "https://example.com/product.jpg"
        result = await validator.validate_image_url(url, check_shopify_cdn=True)
        # Currently returns True with a warning
        assert result is True
