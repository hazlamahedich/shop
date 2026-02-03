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

    # 3000-3999: LLM Provider (owner: llm team)
    LLM_PROVIDER_ERROR = 3000
    LLM_RATE_LIMIT = 3001
    LLM_TIMEOUT = 3002
    LLM_QUOTA_EXCEEDED = 3003

    # 4000-4999: Shopify Integration (owner: shopify team)
    SHOPIFY_API_ERROR = 4000
    CHECKOUT_GENERATION_FAILED = 4001
    PRODUCT_NOT_FOUND = 4002
    STOREFRONT_API_ERROR = 4003

    # 5000-5999: Facebook/Messenger (owner: facebook team)
    MESSENGER_WEBHOOK_ERROR = 5000
    MESSAGE_SEND_FAILED = 5001
    WEBHOOK_VERIFICATION_FAILED = 5002

    # 6000-6999: Cart/Checkout (owner: checkout team)
    CART_NOT_FOUND = 6000
    INVALID_QUANTITY = 6001
    CHECKOUT_EXPIRED = 6002
    CART_SESSION_EXPIRED = 6003

    # 7000-7999: Conversation/Session (owner: conversation team)
    SESSION_EXPIRED = 7000
    CONVERSATION_NOT_FOUND = 7001
    INVALID_CONTEXT = 7002


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
