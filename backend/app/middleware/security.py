"""Security middleware for HTTPS enforcement and security headers.

NFR-S1: HTTPS Enforcement
- Redirect all HTTP traffic to HTTPS
- Add HSTS (HTTP Strict Transport Security) header
- HSTS configuration: max-age=31536000; includeSubDomains; preload
- HTTPS enforcement active only in production (DEBUG=false)

NFR-S7: Content Security Policy Headers
- Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline';
  style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; connect-src 'self'
- X-Frame-Options: DENY
- X-Content-Type-Options: nosniff
- X-XSS-Protection: 1; mode=block
- Referrer-Policy: strict-origin-when-cross-origin
- Permissions-Policy: geolocation=(), microphone=(), camera=()
"""

from __future__ import annotations

from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware

from app.core.config import settings


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all HTTP responses.

    This middleware adds comprehensive security headers to prevent
    common web vulnerabilities including XSS, clickjacking, and
    other injection attacks.

    Security Headers Added:
    - X-Frame-Options: DENY - Prevents clickjacking
    - X-Content-Type-Options: nosniff - Prevents MIME sniffing
    - X-XSS-Protection: 1; mode=block - Enables XSS filtering
    - Referrer-Policy: strict-origin-when-cross-origin - Controls referrer info
    - Permissions-Policy: Restricts browser features (geolocation, mic, camera)
    - Content-Security-Policy: Defines content sources (default-src 'self', etc.)
    - Strict-Transport-Security: HSTS for HTTPS enforcement (production only)
    """

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Process request and add security headers to response.

        Args:
            request: The incoming HTTP request
            call_next: The next middleware or route handler

        Returns:
            Response with security headers added
        """
        response = await call_next(request)

        # Prevent clickjacking attacks
        response.headers["X-Frame-Options"] = "DENY"

        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Enable XSS protection (legacy but still useful)
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Control referrer information leakage
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Disable browser features that could be exploited
        response.headers["Permissions-Policy"] = (
            "geolocation=(), "
            "microphone=(), "
            "camera=(), "
            "payment=(), "
            "usb=(), "
            "magnetometer=(), "
            "gyroscope=(), "
            "accelerometer=()"
        )

        # Content Security Policy to prevent XSS and data injection
        # Note: 'unsafe-inline' and 'unsafe-eval' are needed for FastAPI docs
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self';"
        )

        # HSTS header only in production (DEBUG=false)
        # This tells browsers to always use HTTPS for this domain
        if not settings()["DEBUG"]:
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )

        return response


def setup_security_middleware(app) -> None:
    """Setup security middleware for FastAPI application.

    This function configures all security-related middleware including:
    - SecurityHeadersMiddleware: Adds security headers
    - HTTPSRedirectMiddleware: Redirects HTTP to HTTPS (production only)

    Args:
        app: The FastAPI application instance
    """
    # Add security headers middleware (always enabled)
    app.add_middleware(SecurityHeadersMiddleware)

    # Add HTTPS redirect middleware only in production
    # This prevents issues with local development (http://localhost)
    if not settings()["DEBUG"]:
        app.add_middleware(HTTPSRedirectMiddleware)
