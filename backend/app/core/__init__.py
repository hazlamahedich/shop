"""Core application components."""

from app.core.config import is_testing, settings
from app.core.encryption import (
    decrypt_conversation_content,
    decrypt_metadata,
    encrypt_conversation_content,
    encrypt_metadata,
    get_conversation_fernet,
    is_encrypted,
)
from app.core.errors import (
    APIError,
    AuthenticationError,
    ErrorCode,
    NotFoundError,
    ValidationError,
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
