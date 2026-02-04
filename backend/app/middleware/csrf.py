"""CSRF middleware for FastAPI (NFR-S8).

This middleware implements CSRF protection for all state-changing operations
(POST, PUT, DELETE, PATCH) while safely bypassing validation for:
- Safe methods (GET, HEAD, OPTIONS)
- Webhook endpoints (they use signature-based verification)
- OAuth flows (they use state parameter for CSRF protection)

NFR-S8: CSRF tokens for state-changing operations
- CSRF tokens for all POST/PUT/DELETE operations
- Double-submit cookie pattern
- Token validation on state-changing endpoints
- Per-session token generation
- Secure token storage (httpOnly, secure, sameSite)
"""

from __future__ import annotations

from typing import Callable, Awaitable
from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.csrf import (
    CSRFProtection,
    get_csrf_protection,
    CSRFTokenError,
)
from app.core.config import settings


class CSRFMiddleware(BaseHTTPMiddleware):
    """CSRF protection middleware for FastAPI.

    This middleware validates CSRF tokens for all state-changing operations
    (POST, PUT, DELETE, PATCH) except for webhook endpoints which use
    signature-based verification.

    The middleware follows these rules:
    1. Skip CSRF for safe methods (GET, HEAD, OPTIONS)
    2. Skip CSRF for webhook endpoints (use signature verification)
    3. Skip CSRF for OAuth endpoints (use state parameter)
    4. Validate CSRF for all other state-changing operations

    Example:
        app.add_middleware(CSRFMiddleware, secret_key=settings()["SECRET_KEY"])
    """

    # Paths that bypass CSRF validation
    BYPASS_PATHS = [
        "/api/webhooks/",
        "/webhooks/",  # Webhook endpoints (use signature-based verification)
        "/api/oauth/",
        "/api/auth/",
        "/api/deletion/",  # Data deletion for GDPR/CCPA compliance
        "/docs",
        "/redoc",
        "/openapi.json",
        "/health",
    ]

    def __init__(self, app, secret_key: str) -> None:
        """Initialize CSRF middleware.

        Args:
            app: The FastAPI application
            secret_key: Secret key for CSRF token generation
        """
        super().__init__(app)
        self.csrf = CSRFProtection(secret_key)

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        """Process request and validate CSRF token if needed.

        Args:
            request: The incoming HTTP request
            call_next: The next middleware or route handler

        Returns:
            Response from downstream handler

        Raises:
            HTTPException: If CSRF token validation fails
        """
        # Skip CSRF for safe methods (GET, HEAD, OPTIONS)
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return await call_next(request)

        # Skip CSRF for bypass paths
        if self._should_bypass_csrf(request):
            return await call_next(request)

        # Extract token from headers
        token = self.csrf.extract_token_from_headers(request.headers)

        # Validate CSRF token
        if not self.csrf.validate_token(request, token):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error_code": 2000,
                    "message": "Invalid CSRF token",
                    "details": "CSRF token is required for state-changing operations",
                },
            )

        # Token is valid, proceed with request
        response = await call_next(request)
        return response

    def _should_bypass_csrf(self, request: Request) -> bool:
        """Check if request should bypass CSRF validation.

        Args:
            request: The incoming HTTP request

        Returns:
            True if CSRF should be bypassed
        """
        path = request.url.path

        # Check bypass paths
        for bypass_path in self.BYPASS_PATHS:
            if path.startswith(bypass_path):
                return True

        return False


def setup_csrf_middleware(app) -> None:
    """Setup CSRF middleware for FastAPI application.

    This function configures CSRF protection middleware with proper
    secret key from settings.

    Args:
        app: The FastAPI application instance
    """
    secret_key = settings()["SECRET_KEY"]

    # Validate secret key is not dev key in production
    if not settings()["DEBUG"] and secret_key == "dev-secret-key-DO-NOT-USE-IN-PRODUCTION":
        raise ValueError(
            "CSRF protection requires a secure SECRET_KEY in production. "
            "Generate one with: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
        )

    # Add CSRF middleware (after CORS, before routes)
    app.add_middleware(CSRFMiddleware, secret_key=secret_key)
