"""ErrorCode registry and API error handling.

Governance Process:
1. Check owner team before adding new code in range
2. Document new code in docs/error-code-governance.md
3. No code reuse across ranges (prevents ambiguity)
4. Deleted codes are never reused (maintains log stability)
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from typing import Any, Optional


class ErrorCode(IntEnum):
    """Application error codes with clear ownership ranges."""

    # 1000-1999: General/System (owner: core team)
    UNKNOWN_ERROR = 1000
    VALIDATION_ERROR = 1001
    INTERNAL_ERROR = 1002

    # 2000-2999: Auth/Security (owner: security team)
    AUTH_FAILED = 2000
    TOKEN_EXPIRED = 2001
    WEBHOOK_SIGNATURE_INVALID = 2002
    UNAUTHORIZED = 2003
    PREREQUISITES_INCOMPLETE = 2004
    MERCHANT_NOT_FOUND = 2005
    DEPLOYMENT_IN_PROGRESS = 2006
    DEPLOYMENT_FAILED = 2007
    DEPLOYMENT_CANCELLED = 2008
    DEPLOYMENT_TIMEOUT = 2009
    MERCHANT_ALREADY_EXISTS = 2010

    # 3000-3999: LLM Provider (owner: llm team)
    LLM_PROVIDER_ERROR = 3000
    LLM_RATE_LIMIT = 3001
    LLM_TIMEOUT = 3002
    LLM_QUOTA_EXCEEDED = 3003
    LLM_PROVIDER_NOT_FOUND = 3004  # Unknown provider in factory
    LLM_API_KEY_MISSING = 3005  # API key not provided
    LLM_API_KEY_INVALID = 3006  # API key validation failed
    LLM_CONNECTION_FAILED = 3007  # Provider connection failed
    LLM_TEST_FAILED = 3008  # Test call failed
    LLM_CONFIGURATION_MISSING = 3009  # No configuration found
    LLM_INVALID_MODEL = 3010  # Invalid model for provider
    LLM_SERVICE_UNAVAILABLE = 3011  # Provider service down
    LLM_TOKEN_COUNT_FAILED = 3012  # Token counting failed
    LLM_COST_CALCULATION_FAILED = 3013  # Cost estimation failed
    LLM_INPUT_SANITIZATION_FAILED = 3014  # Input sanitization failed
    LLM_RATE_LIMITER_ENABLED = 3015  # Rate limiter triggered
    LLM_ROUTER_BOTH_FAILED = 3016  # Both primary and backup providers failed
    LLM_HEALTH_CHECK_FAILED = 3017  # Health check endpoint failed

    # 4000-4999: Shopify Integration (owner: shopify team)
    SHOPIFY_API_ERROR = 4000
    CHECKOUT_GENERATION_FAILED = 4001
    PRODUCT_NOT_FOUND = 4002
    STOREFRONT_API_ERROR = 4003
    SHOPIFY_OAUTH_STATE_MISMATCH = 4011  # CSRF attack suspected
    SHOPIFY_OAUTH_DENIED = 4012  # User denied authorization
    SHOPIFY_TOKEN_EXCHANGE_FAILED = 4013  # Shopify API error
    SHOPIFY_ADMIN_API_ACCESS_DENIED = 4014  # Insufficient permissions
    SHOPIFY_STOREFRONT_TOKEN_FAILED = 4015  # Failed to create token
    SHOPIFY_STOREFRONT_API_DENIED = 4016  # Storefront API access denied
    SHOPIFY_ALREADY_CONNECTED = 4017  # Duplicate connection attempt
    SHOPIFY_NOT_CONNECTED = 4018  # Operation requires connection
    SHOPIFY_ENCRYPTION_KEY_MISSING = 4019  # Configuration error
    SHOPIFY_WEBHOOK_HMAC_INVALID = 4020  # Webhook security
    SHOPIFY_WEBHOOK_VERIFY_FAILED = 4021  # Webhook verification failed
    SHOPIFY_CHECKOUT_CREATE_FAILED = 4022  # Checkout generation failed
    SHOPIFY_CHECKOUT_URL_INVALID = 4023  # Checkout URL validation failed
    SHOPIFY_SHOP_DOMAIN_INVALID = 4024  # Invalid shop domain format
    SHOPIFY_PRODUCT_SEARCH_FAILED = 4025  # Product search failed
    SHOPIFY_TIMEOUT = 4026  # API timeout (Storefront)
    SHOPIFY_INVALID_QUERY = 4027  # Malformed query
    SHOPIFY_RATE_LIMITED = 4028  # Admin API rate limit (not Storefront)
    PRODUCT_MAPPING_FAILED = 4029  # Entity to filter mapping error
    SHOPIFY_PRODUCT_NOT_FOUND_SEARCH = 4030  # No products found in search

    # 5000-5999: Facebook/Messenger (owner: facebook team)
    MESSENGER_WEBHOOK_ERROR = 5000
    MESSAGE_SEND_FAILED = 5001
    WEBHOOK_VERIFICATION_FAILED = 5002
    FACEBOOK_TIMEOUT = 5026  # Send API timeout
    FACEBOOK_INVALID_RECIPIENT = 5027  # Invalid PSID
    FACEBOOK_MESSAGE_TOO_LARGE = 5028  # Message exceeds size limit
    FACEBOOK_RATE_LIMITED = 5029  # Rate limit exceeded
    MESSENGER_FORMATTING_FAILED = 5030  # Product formatting error
    IMAGE_VALIDATION_FAILED = 5031  # Invalid image URL
    FACEBOOK_OAUTH_STATE_MISMATCH = 5010  # CSRF attack suspected
    FACEBOOK_OAUTH_DENIED = 5011  # User denied authorization
    FACEBOOK_TOKEN_EXCHANGE_FAILED = 5012  # Facebook API error
    FACEBOOK_PAGE_ACCESS_DENIED = 5013  # Insufficient permissions
    FACEBOOK_WEBHOOK_SIGNATURE_INVALID = 5014  # Webhook security
    FACEBOOK_ALREADY_CONNECTED = 5015  # Duplicate connection attempt
    FACEBOOK_NOT_CONNECTED = 5016  # Operation requires connection
    FACEBOOK_ENCRYPTION_KEY_MISSING = 5017  # Configuration error
    FACEBOOK_WEBHOOK_VERIFY_FAILED = 5018  # Webhook verification failed

    # 6000-6999: Cart/Checkout (owner: checkout team)
    CART_NOT_FOUND = 6000
    INVALID_QUANTITY = 6001
    CHECKOUT_EXPIRED = 6002
    CART_SESSION_EXPIRED = 6003
    CART_ADD_FAILED = 6004  # Failed to add item to cart
    CART_REMOVE_FAILED = 6005  # Failed to remove item from cart
    CART_UPDATE_FAILED = 6006  # Failed to update cart quantity
    CART_RETRIEVAL_FAILED = 6007  # Failed to retrieve cart
    ITEM_NOT_FOUND = 6008  # Item not found in cart
    OUT_OF_STOCK = 6009  # Product variant not available
    INVALID_PRODUCT_ID = 6010  # Invalid product_id format
    INVALID_VARIANT_ID = 6011  # Invalid variant_id format
    CART_EXPIRED = 6012  # Cart session expired (24h)
    CART_CLEAR_FAILED = 6013  # Failed to clear cart

    # 7000-7999: Conversation/Session (owner: conversation team)
    SESSION_EXPIRED = 7000
    CONVERSATION_NOT_FOUND = 7001
    INVALID_CONTEXT = 7002
    CLARIFICATION_FLOW_FAILED = 7010  # Generic clarification error
    CLARIFICATION_TIMEOUT = 7011  # User didn't respond to question
    CLARIFICATION_MAX_ATTEMPTS = 7012  # Max 3 questions exceeded
    QUESTION_GENERATION_FAILED = 7013  # Failed to generate question
    CLARIFICATION_STATE_ERROR = 7014  # Invalid clarification state
    CONSTRAINT_EXTRACTION_FAILED = 7015  # Failed to extract constraints

    # 8000-8999: Tutorial (owner: onboarding team)
    TUTORIAL_NOT_STARTED = 8001
    TUTORIAL_ALREADY_COMPLETED = 8002
    TUTORIAL_INVALID_STEP = 8003
    TUTORIAL_COMPLETION_FAILED = 8004
    TUTORIAL_STATE_CORRUPT = 8005
    BOT_PREVIEW_TEST_FAILED = 8006
    BOT_PREVIEW_RATE_LIMITED = 8007

    # 9000-9999: Webhook Verification (owner: integration team)
    WEBHOOK_NOT_CONNECTED = 9001
    WEBHOOK_TEST_FAILED = 9002
    WEBHOOK_VERIFICATION_SIGNATURE_INVALID = 9003
    WEBHOOK_RESUBSCRIBE_FAILED = 9004
    WEBHOOK_TIMEOUT = 9005
    WEBHOOK_URL_NOT_ACCESSIBLE = 9006
    WEBHOOK_MISSING_SUBSCRIPTION = 9007
    WEBHOOK_EXPIRED_TOKEN = 9008
    WEBHOOK_RATE_LIMITED = 9009
    WEBHOOK_UNKNOWN_ERROR = 9010

    # 10000-10999: Data Deletion (owner: privacy team)
    DELETION_REQUEST_NOT_FOUND = 10001
    DELETION_ALREADY_IN_PROGRESS = 10002
    DELETION_FAILED = 10003


@dataclass
class ErrorDetail:
    """Structured error detail for API responses."""

    field: Optional[str] = None
    message: str = ""
    code: Optional[ErrorCode] = None


class APIError(Exception):
    """Base API exception with structured error response."""

    def __init__(
        self,
        code: ErrorCode,
        message: str,
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(message)

    def to_dict(self) -> dict[str, Any]:
        """Convert error to API response format."""
        result = {
            "error_code": int(self.code),
            "message": self.message,
        }
        if self.details:
            result["details"] = self.details
        return result


class ValidationError(APIError):
    """Validation error with field-specific details."""

    def __init__(
        self,
        message: str,
        fields: Optional[dict[str, str]] = None,
    ) -> None:
        details = {"fields": fields} if fields else None
        super().__init__(ErrorCode.VALIDATION_ERROR, message, details)


class AuthenticationError(APIError):
    """Authentication/authorization error."""

    def __init__(self, message: str = "Authentication failed") -> None:
        super().__init__(ErrorCode.AUTH_FAILED, message)


class NotFoundError(APIError):
    """Resource not found error."""

    def __init__(self, resource: str, identifier: Optional[str] = None) -> None:
        message = f"{resource} not found"
        if identifier:
            message += f": {identifier}"
        super().__init__(ErrorCode.UNKNOWN_ERROR, message)
