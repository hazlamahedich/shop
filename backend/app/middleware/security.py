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

from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware
from starlette.types import ASGIApp, Receive, Scope, Send

from app.core.config import settings


class SecurityHeadersMiddleware:
    """Add security headers to all HTTP responses (pure ASGI).

    This middleware adds comprehensive security headers to prevent
    common web vulnerabilities including XSS, clickjacking, and
    other injection attacks.

    Security Headers Added:
    - X-Frame-Options: SAMEORIGIN - Prevents clickjacking (allows Shopify embedding)
    - X-Content-Type-Options: nosniff - Prevents MIME sniffing
    - X-XSS-Protection: 1; mode=block - Enables XSS filtering
    - Referrer-Policy: strict-origin-when-cross-origin - Controls referrer info
    - Permissions-Policy: Restricts browser features (geolocation, mic, camera)
    - Content-Security-Policy: Defines content sources (default-src 'self', etc.)
    - Strict-Transport-Security: HSTS for HTTPS enforcement (production only)
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] not in ("http", "websocket"):
            await self.app(scope, receive, send)
            return

        sent = False

        async def send_with_security_headers(message: dict) -> None:
            nonlocal sent
            if message["type"] == "http.response.start" and not sent:
                headers = dict(
                    (
                        h[0].decode() if isinstance(h[0], bytes) else h[0],
                        h[1].decode() if isinstance(h[1], bytes) else h[1],
                    )
                    for h in message.get("headers", [])
                )

                headers["X-Frame-Options"] = "SAMEORIGIN"
                headers["X-Content-Type-Options"] = "nosniff"
                headers["X-XSS-Protection"] = "1; mode=block"
                headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
                headers["Permissions-Policy"] = (
                    "geolocation=(), "
                    "microphone=(), "
                    "camera=(), "
                    "payment=(), "
                    "usb=(), "
                    "magnetometer=(), "
                    "gyroscope=(), "
                    "accelerometer=()"
                )

                app_url = settings()["APP_URL"]
                headers["Content-Security-Policy"] = (
                    f"default-src 'self'; "
                    f"script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                    f"style-src 'self' 'unsafe-inline'; "
                    f"img-src 'self' data: https:; "
                    f"connect-src 'self' {app_url} wss://*.zrok.io; "
                    f"frame-ancestors 'self' https://*.myshopify.com https://admin.shopify.com; "
                    f"base-uri 'self'; "
                    f"form-action 'self';"
                )

                if not settings()["DEBUG"]:
                    headers["Strict-Transport-Security"] = (
                        "max-age=31536000; includeSubDomains; preload"
                    )

                message["headers"] = [(k.encode(), v.encode()) for k, v in headers.items()]
                sent = True
            await send(message)

        await self.app(scope, receive, send_with_security_headers)


def setup_security_middleware(app) -> None:
    """Setup security middleware for FastAPI application."""
    app.add_middleware(SecurityHeadersMiddleware)

    if not settings()["DEBUG"]:
        app.add_middleware(HTTPSRedirectMiddleware)
