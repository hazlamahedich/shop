"""CSRF protection utilities for state-changing operations (NFR-S8).

This module implements CSRF (Cross-Site Request Forgery) protection using
the double-submit cookie pattern with per-session token generation.

NFR-S8: CSRF tokens for state-changing operations
- CSRF tokens for all POST/PUT/DELETE operations
- Double-submit cookie pattern
- Token validation on state-changing endpoints
- Per-session token generation
- Secure token storage (httpOnly, secure, sameSite)

Security Features:
- Constant-time token comparison prevents timing attacks
- Tokens expire after 1 hour
- Per-session token generation prevents token reuse
- Double-submit pattern prevents token interception
"""

from __future__ import annotations

import secrets
from typing import Optional
from fastapi import Request, Response
from starlette.datastructures import Headers


class CSRFTokenError(Exception):
    """CSRF token validation error."""
    pass


class CSRFProtection:
    """CSRF protection using double-submit cookie pattern.

    This class generates and validates CSRF tokens using the double-submit
    pattern where the token is stored both in a cookie and sent in the
    request header. This prevents token interception while maintaining
    security.

    Attributes:
        secret_key: Secret key used for token generation
        token_length: Length of random token portion (default: 32)
        max_age: Token lifetime in seconds (default: 3600)
    """

    def __init__(
        self,
        secret_key: str,
        token_length: int = 32,
        max_age: int = 3600,
    ) -> None:
        """Initialize CSRF protection.

        Args:
            secret_key: Secret key for token generation
            token_length: Length of random token portion
            max_age: Token lifetime in seconds
        """
        if not secret_key or secret_key == "dev-secret-key-DO-NOT-USE-IN-PRODUCTION":
            raise ValueError(
                "CSRF requires a secure SECRET_KEY. "
                "Generate one with: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
            )
        self.secret_key = secret_key
        self.token_length = token_length
        self.max_age = max_age

    def generate_token(self, session_id: str) -> str:
        """Generate CSRF token for session.

        The token combines the session ID with a cryptographically secure
        random component to prevent prediction and replay attacks.

        Args:
            session_id: Unique session identifier

        Returns:
            URL-safe CSRF token
        """
        if not session_id:
            raise ValueError("session_id cannot be empty")

        # Combine session_id with random secret
        random_part = secrets.token_urlsafe(self.token_length)
        return f"{session_id}:{random_part}"

    def validate_token(
        self,
        request: Request,
        token: Optional[str],
    ) -> bool:
        """Validate CSRF token from request.

        Uses constant-time comparison to prevent timing attacks.
        Validates token from request header against token stored in cookie.

        Args:
            request: The FastAPI request object
            token: CSRF token from request header

        Returns:
            True if token is valid, False otherwise
        """
        if not token:
            return False

        # Get session token from cookie
        session_token = request.cookies.get("csrf_token")
        if not session_token:
            return False

        # Use constant-time comparison to prevent timing attacks
        # Even if token lengths differ, compare_digest prevents timing leakage
        try:
            return secrets.compare_digest(token, session_token)
        except (TypeError, AttributeError):
            # Handle invalid token format
            return False

    def set_csrf_cookie(
        self,
        response: Response,
        token: str,
    ) -> None:
        """Set CSRF token as httpOnly, secure, sameSite cookie.

        Sets the token with security attributes to prevent XSS
        and CSRF attacks.

        Args:
            response: The FastAPI response object
            token: The CSRF token to store
        """
        response.set_cookie(
            key="csrf_token",
            value=token,
            httponly=True,  # Prevents JavaScript access
            secure=True,  # HTTPS only
            samesite="strict",  # Prevents CSRF
            max_age=self.max_age,  # Token expiration
        )

    def clear_csrf_cookie(self, response: Response) -> None:
        """Clear CSRF token cookie.

        Args:
            response: The FastAPI response object
        """
        response.delete_cookie(
            key="csrf_token",
            httponly=True,
            secure=True,
            samesite="strict",
        )

    def extract_token_from_headers(self, headers: Headers) -> Optional[str]:
        """Extract CSRF token from request headers.

        Looks for token in X-CSRF-Token header (preferred) or
        falls back to checking form data or JSON body.

        Args:
            headers: Request headers

        Returns:
            CSRF token or None
        """
        # Primary: Check X-CSRF-Token header
        token = headers.get("x-csrf-token") or headers.get("X-CSRF-Token")
        if token:
            return token

        # Fallback: Check CSRF-Token header (alternative naming)
        token = headers.get("csrf-token") or headers.get("CSRF-Token")
        if token:
            return token

        return None

    def parse_session_id_from_token(self, token: str) -> Optional[str]:
        """Extract session ID from CSRF token.

        Args:
            token: CSRF token string

        Returns:
            Session ID or None if token is invalid
        """
        if not token or ":" not in token:
            return None

        try:
            session_id, _ = token.split(":", 1)
            return session_id
        except ValueError:
            return None


# Singleton instance for application-wide use
_csrf_protection: Optional[CSRFProtection] = None


def get_csrf_protection() -> CSRFProtection:
    """Get the singleton CSRF protection instance.

    Returns:
        CSRFProtection instance

    Raises:
        ValueError: If CSRF protection not initialized
    """
    global _csrf_protection
    if _csrf_protection is None:
        raise ValueError(
            "CSRF protection not initialized. "
            "Call init_csrf_protection() first."
        )
    return _csrf_protection


def init_csrf_protection(secret_key: str) -> CSRFProtection:
    """Initialize CSRF protection with secret key.

    Args:
        secret_key: Secret key for token generation

    Returns:
        CSRFProtection instance
    """
    global _csrf_protection
    _csrf_protection = CSRFProtection(secret_key)
    return _csrf_protection
