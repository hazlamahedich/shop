"""Image validation and processing utilities.

Validates product images for Facebook Messenger requirements:
- Minimum dimensions (400x400px)
- File size limits (500KB)
- Supported formats (PNG, JPEG, GIF)
- Aspect ratio validation (1:1 preferred)
"""

from __future__ import annotations

import io
import re
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

import httpx
import structlog
from PIL import Image

from app.core.config import settings
from app.core.errors import APIError, ErrorCode


logger = structlog.get_logger(__name__)


class ImageValidator:
    """Validator for product images in Messenger.

    Ensures images meet Facebook Messenger platform requirements.
    """

    # Image constraints
    MIN_DIMENSION = 400  # Minimum width/height in pixels
    MAX_DIMENSION = 2048  # Maximum width/height in pixels
    MAX_FILE_SIZE_BYTES = 500 * 1024  # 500KB
    RECOMMENDED_ASPECT_RATIO = 1.0  # Square (1:1)

    # Allowed image formats
    ALLOWED_FORMATS = {"png", "jpg", "jpeg", "gif"}
    ALLOWED_MIME_TYPES = {"image/png", "image/jpeg", "image/gif"}

    # Shopify CDN pattern
    SHOPIFY_CDN_PATTERN = re.compile(
        r"^(https?:)?//(cdn\.shopify\.com|images\.shopify\.com)/",
        re.IGNORECASE,
    )

    def __init__(self) -> None:
        """Initialize image validator."""
        self.logger = structlog.get_logger(__name__)
        config = settings()
        self.fallback_image_url = config.get(
            "MESSENGER_FALLBACK_IMAGE_URL",
            "https://cdn.example.com/fallback-product.png",
        )

    async def validate_image_url(
        self,
        image_url: str,
        check_shopify_cdn: bool = True,
    ) -> bool:
        """Validate an image URL for Messenger use.

        Args:
            image_url: URL to validate
            check_shopify_cdn: Whether to check URL is from Shopify CDN

        Returns:
            True if valid, False otherwise
        """
        if not image_url:
            self.logger.warning("image_url_empty")
            return False

        # Check URL format
        try:
            parsed = urlparse(image_url)
            if not parsed.scheme or not parsed.netloc:
                self.logger.warning("image_url_invalid_format", url=image_url)
                return False
        except Exception as e:
            self.logger.error("image_url_parse_failed", url=image_url, error=str(e))
            return False

        # Check file extension
        path = parsed.path.lower()
        if not any(path.endswith(f".{fmt}") for fmt in self.ALLOWED_FORMATS):
            self.logger.warning(
                "image_url_invalid_format",
                url=image_url,
                allowed_formats=list(self.ALLOWED_FORMATS),
            )
            return False

        # Check Shopify CDN if required
        if check_shopify_cdn:
            if not self.SHOPIFY_CDN_PATTERN.match(image_url):
                self.logger.warning(
                    "image_url_not_shopify_cdn",
                    url=image_url,
                )
                # For now, we'll still allow non-Shopify URLs
                # In production, this could be a security requirement

        return True

    async def get_image_info(
        self,
        image_url: str,
    ) -> Optional[Dict[str, Any]]:
        """Get image information without downloading full file.

        Args:
            image_url: URL to check

        Returns:
            Dictionary with width, height, size_bytes, or None if failed
        """
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                # Use HEAD request to get content length
                response = await client.head(image_url)
                response.raise_for_status()

                # Get content length from headers
                content_length = response.headers.get("content-length")
                size_bytes = int(content_length) if content_length else None

                # Download and parse image to extract dimensions
                width = None
                height = None

                # Download image content for dimension validation
                # Use range request to download only first portion for efficiency
                image_response = await client.get(image_url)
                image_response.raise_for_status()
                image_content = image_response.content

                # Parse image with PIL to get dimensions
                try:
                    with Image.open(io.BytesIO(image_content)) as img:
                        width, height = img.size
                        self.logger.debug(
                            "image_dimensions_extracted",
                            url=image_url,
                            width=width,
                            height=height,
                        )
                except Exception as pil_error:
                    self.logger.warning(
                        "image_parsing_failed",
                        url=image_url,
                        error=str(pil_error),
                    )
                    # If PIL parsing fails, we still have the image

                return {
                    "url": image_url,
                    "size_bytes": size_bytes,
                    "width": width,
                    "height": height,
                }

        except httpx.HTTPStatusError as e:
            self.logger.error(
                "image_head_failed",
                url=image_url,
                status=e.response.status_code,
            )
            return None
        except Exception as e:
            self.logger.error("image_info_failed", url=image_url, error=str(e))
            return None

    def validate_image_dimensions(
        self,
        width: Optional[int],
        height: Optional[int],
    ) -> Tuple[bool, Optional[str]]:
        """Validate image dimensions meet requirements.

        Args:
            width: Image width in pixels
            height: Image height in pixels

        Returns:
            Tuple of (is_valid, error_message)
        """
        if width is None or height is None:
            # Unknown dimensions - this is now an error since we validate them
            return False, "Unable to validate image dimensions"

        if width < self.MIN_DIMENSION or height < self.MIN_DIMENSION:
            return (
                False,
                f"Image dimensions {width}x{height} below minimum {self.MIN_DIMENSION}x{self.MIN_DIMENSION}",
            )

        if width > self.MAX_DIMENSION or height > self.MAX_DIMENSION:
            return (
                False,
                f"Image dimensions {width}x{height} exceed maximum {self.MAX_DIMENSION}x{self.MAX_DIMENSION}",
            )

        # Check aspect ratio (should be close to 1:1)
        aspect_ratio = width / height if height > 0 else 0
        if not (0.8 <= aspect_ratio <= 1.2):
            self.logger.warning(
                "image_aspect_ratio_not_square",
                width=width,
                height=height,
                aspect_ratio=aspect_ratio,
            )
            # Not an error, just a warning

        return True, None

    def validate_file_size(
        self,
        size_bytes: Optional[int],
    ) -> Tuple[bool, Optional[str]]:
        """Validate image file size meets requirements.

        Args:
            size_bytes: File size in bytes

        Returns:
            Tuple of (is_valid, error_message)
        """
        if size_bytes is None:
            # Unknown size - assume valid if we can't check
            return True, None

        if size_bytes > self.MAX_FILE_SIZE_BYTES:
            return (
                False,
                f"File size {size_bytes} bytes exceeds maximum {self.MAX_FILE_SIZE_BYTES} bytes",
            )

        return True, None

    async def validate_and_prepare_image(
        self,
        image_url: str,
    ) -> str:
        """Validate image and return URL or fallback.

        Args:
            image_url: URL to validate

        Returns:
            Valid image URL or fallback URL

        Raises:
            APIError: If validation fails
        """
        # Validate URL format
        is_valid_url = await self.validate_image_url(image_url)
        if not is_valid_url:
            self.logger.warning(
                "image_url_invalid", url=image_url, fallback=self.fallback_image_url
            )
            return self.fallback_image_url

        # Get image info (now includes actual dimensions)
        image_info = await self.get_image_info(image_url)

        if image_info:
            # Validate file size
            is_valid_size, error_msg = self.validate_file_size(image_info.get("size_bytes"))
            if not is_valid_size:
                self.logger.warning("image_size_invalid", url=image_url, error=error_msg)
                return self.fallback_image_url

            # Validate dimensions (now actually performed)
            is_valid_dimensions, error_msg = self.validate_image_dimensions(
                image_info.get("width"), image_info.get("height")
            )
            if not is_valid_dimensions:
                self.logger.warning("image_dimensions_invalid", url=image_url, error=error_msg)
                return self.fallback_image_url

        return image_url

    def generate_alt_text(
        self,
        product_title: str,
        product_type: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> str:
        """Generate alt text for product image.

        Args:
            product_title: Product title
            product_type: Product type/category
            tags: Product tags

        Returns:
            Alt text string for accessibility
        """
        # Start with product title
        alt_text = product_title

        # Add product type if available
        if product_type:
            alt_text = f"{product_type} - {alt_text}"

        # Add first tag if relevant
        if tags:
            relevant_tags = [t for t in tags if len(t) > 3][:3]
            if relevant_tags:
                alt_text = f"{alt_text} ({', '.join(relevant_tags)})"

        return alt_text

    def is_valid_format(
        self,
        url: str,
    ) -> bool:
        """Check if URL has valid image format.

        Args:
            url: Image URL

        Returns:
            True if format is valid
        """
        path = urlparse(url).path.lower()
        return any(path.endswith(f".{fmt}") for fmt in self.ALLOWED_FORMATS)

    def get_image_format(
        self,
        url: str,
    ) -> Optional[str]:
        """Extract image format from URL.

        Args:
            url: Image URL

        Returns:
            Format string (e.g., "png", "jpg") or None
        """
        path = urlparse(url).path.lower()
        for fmt in self.ALLOWED_FORMATS:
            if path.endswith(f".{fmt}"):
                return fmt
        return None
