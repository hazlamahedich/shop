"""Core application components."""

from app.core.config import settings, is_testing
from app.core.errors import (
    APIError,
    ErrorCode,
    ValidationError,
    AuthenticationError,
    NotFoundError,
)
from app.core.encryption import (
    encrypt_conversation_content,
    decrypt_conversation_content,
    encrypt_metadata,
    decrypt_metadata,
    get_conversation_fernet,
    is_encrypted,
)

__all__ = [
    "settings",
    "is_testing",
    "APIError",
    "ErrorCode",
    "ValidationError",
    "AuthenticationError",
    "NotFoundError",
    "encrypt_conversation_content",
    "decrypt_conversation_content",
    "encrypt_metadata",
    "decrypt_metadata",
    "get_conversation_fernet",
    "is_encrypted",
    "get_current_merchant",
]
