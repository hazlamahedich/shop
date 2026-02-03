"""Tests for error handling and error codes."""

import pytest

from app.core.errors import (
    ErrorCode,
    APIError,
    ValidationError,
    AuthenticationError,
    NotFoundError,
)


class TestErrorCode:
    """Test ErrorCode enum values."""

    def test_error_code_ranges(self):
        """Verify error codes are in correct ranges."""
        # 1000-1999: General/System
        assert ErrorCode.UNKNOWN_ERROR == 1000
        assert ErrorCode.VALIDATION_ERROR == 1001

        # 2000-2999: Auth/Security
        assert ErrorCode.AUTH_FAILED == 2000
        assert ErrorCode.WEBHOOK_SIGNATURE_INVALID == 2002

        # 3000-3999: LLM Provider
        assert ErrorCode.LLM_PROVIDER_ERROR == 3000
        assert ErrorCode.LLM_RATE_LIMIT == 3001

        # 4000-4999: Shopify Integration
        assert ErrorCode.SHOPIFY_API_ERROR == 4000
        assert ErrorCode.CHECKOUT_GENERATION_FAILED == 4001

        # 5000-5999: Facebook/Messenger
        assert ErrorCode.MESSENGER_WEBHOOK_ERROR == 5000

        # 6000-6999: Cart/Checkout
        assert ErrorCode.CART_NOT_FOUND == 6000

        # 7000-7999: Conversation/Session
        assert ErrorCode.SESSION_EXPIRED == 7000

    def test_error_codes_are_unique(self):
        """Verify no duplicate error codes."""
        codes = [code.value for code in ErrorCode]
        assert len(codes) == len(set(codes)), "Error codes must be unique"


class TestAPIError:
    """Test APIError base class."""

    def test_to_dict_basic(self):
        """Test basic error conversion to dict."""
        error = APIError(ErrorCode.UNKNOWN_ERROR, "Something went wrong")
        result = error.to_dict()

        assert result["error_code"] == 1000
        assert result["message"] == "Something went wrong"
        assert "details" not in result

    def test_to_dict_with_details(self):
        """Test error conversion with details."""
        error = APIError(
            ErrorCode.VALIDATION_ERROR,
            "Validation failed",
            details={"field": "email", "reason": "invalid format"}
        )
        result = error.to_dict()

        assert result["error_code"] == 1001
        assert result["details"]["field"] == "email"

    def test_error_message_attribute(self):
        """Test error message is accessible."""
        error = APIError(ErrorCode.AUTH_FAILED, "Not authenticated")
        assert str(error) == "Not authenticated"
        assert error.message == "Not authenticated"


class TestValidationError:
    """Test ValidationError subclass."""

    def test_basic_validation_error(self):
        """Test basic validation error."""
        error = ValidationError("Invalid input")

        assert error.code == ErrorCode.VALIDATION_ERROR
        assert error.message == "Invalid input"

    def test_validation_error_with_fields(self):
        """Test validation error with field details."""
        error = ValidationError(
            "Multiple validation errors",
            fields={"email": "Invalid email", "age": "Must be positive"}
        )
        result = error.to_dict()

        assert result["details"]["fields"]["email"] == "Invalid email"
        assert result["details"]["fields"]["age"] == "Must be positive"


class TestAuthenticationError:
    """Test AuthenticationError subclass."""

    def test_default_message(self):
        """Test default authentication error message."""
        error = AuthenticationError()
        assert error.message == "Authentication failed"
        assert error.code == ErrorCode.AUTH_FAILED

    def test_custom_message(self):
        """Test custom authentication error message."""
        error = AuthenticationError("Token expired")
        assert error.message == "Token expired"


class TestNotFoundError:
    """Test NotFoundError subclass."""

    def test_basic_not_found(self):
        """Test basic not found error."""
        error = NotFoundError("User")
        assert "User not found" in error.message
        assert error.code == ErrorCode.UNKNOWN_ERROR

    def test_not_found_with_identifier(self):
        """Test not found error with identifier."""
        error = NotFoundError("Product", "12345")
        assert "Product not found: 12345" in error.message
