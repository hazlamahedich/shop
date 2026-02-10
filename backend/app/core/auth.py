"""Authentication core module for JWT and password operations.

Implements secure password hashing with bcrypt (work factor 12),
JWT creation/validation with key rotation support, and merchant
authentication.

Security Requirements:
- Password hashing with bcrypt (work factor 12)
- Constant-time password comparison
- JWT with key_version for rotation support
- SECRET_KEY validation at startup
- httpOnly Secure SameSite=Strict cookies

NFR-S2: User conversation data encrypted at rest
NFR-S4: API keys stored as environment variables
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from dataclasses import dataclass
from hashlib import sha256
from typing import Union

import bcrypt
from fastapi import HTTPException, status
from jose import JWTError, jwt, ExpiredSignatureError
from pydantic import ValidationError

from app.core.config import settings
from app.core.errors import ErrorCode, APIError


# JWT Configuration
JWT_SECRET = settings()["SECRET_KEY"]
JWT_ALGORITHM = settings()["ALGORITHM"]
JWT_EXPIRATION_HOURS = 24


@dataclass
class JWTPayload:
    """JWT token payload structure.

    Attributes:
        merchant_id: Merchant identifier
        key_version: Key version for rotation support
        exp: Expiration timestamp
        iat: Issued at timestamp
        session_id: Session identifier for revocation
    """

    merchant_id: int
    key_version: int
    exp: int
    iat: int
    session_id: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert payload to dictionary for JWT encoding."""
        return {
            "merchant_id": self.merchant_id,
            "key_version": self.key_version,
            "exp": self.exp,
            "iat": self.iat,
            "session_id": self.session_id,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "JWTPayload":
        """Create payload from dictionary (from JWT decoding)."""
        return cls(
            merchant_id=data["merchant_id"],
            key_version=data.get("key_version", 1),
            exp=data["exp"],
            iat=data["iat"],
            session_id=data["session_id"],
        )


def validate_secret_key() -> None:
    """Validate SECRET_KEY at startup.

    Raises:
        ValueError: If SECRET_KEY is the default dev key in production
    """
    secret_key = settings()["SECRET_KEY"]
    is_debug = settings()["DEBUG"]

    dev_keys = [
        "dev-secret-key-at-least-32-chars-long-1234567890",
        "dev-secret-key-DO-NOT-USE-IN-PRODUCTION",
    ]

    if not is_debug and secret_key in dev_keys:
        raise ValueError(
            "INVALID_SECRET_KEY: Production environment cannot use dev SECRET_KEY. "
            "Generate a secure key with: "
            "python -c 'import secrets; print(secrets.token_urlsafe(32))'"
        )


def hash_password(password: str) -> str:
    """Hash password with bcrypt (work factor 12).

    Args:
        password: Plain text password

    Returns:
        Salted password hash (60-character string)

    Raises:
        ValueError: If password is empty or too short
    """
    if not password:
        raise ValueError("Password cannot be empty")

    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters")

    # Generate salt with work factor 12
    salt = bcrypt.gensalt(rounds=12)

    # Hash password
    password_hash = bcrypt.hashpw(password.encode("utf-8"), salt)

    return password_hash.decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash using constant-time comparison.

    Args:
        password: Plain text password to verify
        hashed: Stored password hash

    Returns:
        True if password matches

    Note:
        Uses bcrypt.checkpw which provides constant-time comparison
        to prevent timing attacks.
    """
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))


def validate_password_requirements(password: str) -> tuple[bool, list[str]]:
    """Validate password meets requirements.

    Requirements:
    - Minimum 8 characters
    - Must contain uppercase and lowercase letters

    Args:
        password: Password to validate

    Returns:
        Tuple of (is_valid, error_messages)
    """
    errors = []

    if len(password) < 8:
        errors.append("Password must be at least 8 characters")

    if not any(c.isupper() for c in password):
        errors.append("Password must contain at least one uppercase letter")

    if not any(c.islower() for c in password):
        errors.append("Password must contain at least one lowercase letter")

    return len(errors) == 0, errors


def hash_token(token: str) -> str:
    """Hash token for storage (cannot be reversed).

    Uses SHA-256 for one-way hashing of JWT tokens.

    Args:
        token: Token to hash

    Returns:
        Hashed token string
    """
    return sha256(token.encode()).hexdigest()


def create_jwt(
    merchant_id: int,
    session_id: str,
    key_version: int = 1,
    expiration_hours: int = JWT_EXPIRATION_HOURS,
) -> str:
    """Create JWT token with merchant claims.

    Args:
        merchant_id: Merchant identifier
        session_id: Session identifier for revocation
        key_version: Key version for rotation support (default: 1)
        expiration_hours: Token lifetime in hours (default: 24)

    Returns:
        Encoded JWT token string

    Raises:
        APIError: If JWT creation fails
    """
    try:
        now = datetime.utcnow()
        exp = now + timedelta(hours=expiration_hours)

        payload = JWTPayload(
            merchant_id=merchant_id,
            key_version=key_version,
            exp=int(exp.timestamp()),
            iat=int(now.timestamp()),
            session_id=session_id,
        )

        token = jwt.encode(payload.to_dict(), JWT_SECRET, algorithm=JWT_ALGORITHM)

        return token

    except Exception as e:
        raise APIError(
            ErrorCode.AUTH_FAILED,
            "Failed to create authentication token",
            {"error": str(e)},
        )


def validate_jwt(token: str, secret_key: Optional[str] = None) -> JWTPayload:
    """Validate JWT and return payload.

    Supports key rotation by trying both current and previous keys.

    Args:
        token: JWT token string
        secret_key: Optional custom secret key (for testing)

    Returns:
        Decoded JWT payload

    Raises:
        HTTPException: If token is invalid, expired, or has mismatched key version
    """
    key = secret_key or JWT_SECRET

    try:
        # Try current key first
        payload_dict = jwt.decode(token, key, algorithms=[JWT_ALGORITHM])
        return JWTPayload.from_dict(payload_dict)

    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error_code": ErrorCode.TOKEN_EXPIRED,
                "message": "Authentication token has expired",
                "details": "Please log in again",
            },
        )

    except JWTError as e:
        # Try previous key version for rotation support (Story 1.8, AC 5)
        previous_key = settings().get("JWT_SECRET_PREVIOUS")
        if previous_key:
            try:
                payload_dict = jwt.decode(
                    token, previous_key, algorithms=[JWT_ALGORITHM]
                )
                return JWTPayload.from_dict(payload_dict)
            except JWTError:
                pass  # Fall through to error below

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error_code": ErrorCode.AUTH_FAILED,
                "message": "Invalid authentication token",
                "details": str(e),
            },
        )


def authenticate_merchant(
    email: str, password: str, stored_hash: str, merchant_id: int
) -> bool:
    """Authenticate merchant with email and password.

    Args:
        email: Merchant email
        password: Plain text password
        stored_hash: Stored password hash
        merchant_id: Merchant ID for logging

    Returns:
        True if authentication successful

    Raises:
        HTTPException: If authentication fails
    """
    # Verify password using constant-time comparison
    if not verify_password(password, stored_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error_code": ErrorCode.AUTH_FAILED,
                "message": "Invalid email or password",
                "details": "Please check your credentials and try again",
            },
        )

    return True


# Initialize: Validate SECRET_KEY on import
validate_secret_key()
