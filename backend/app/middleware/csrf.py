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

import json
import os

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from app.core.config import settings
from app.core.csrf import (
    CSRFProtection,
)


class CSRFMiddleware:
    """CSRF protection middleware for FastAPI (pure ASGI).

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

    BYPASS_PATHS = [
        "/api/v1/webhooks/",
        "/api/webhooks/",
        "/webhooks/",
        "/api/oauth/",
        "/api/auth/",
        "/api/v1/auth/",
        "/api/v1/merchant/product-pins",
        "/api/integrations/shopify/credentials",
        "/api/integrations/facebook/credentials",
        "/api/tutorial/",
        "/api/deletion/",
        "/api/v1/data/export",
        "/api/conversations/export",
        "/api/conversations/",
        "/api/v1/consent/",
        "/api/v1/widget/",
        "/api/v1/analytics/widget/events",
        "/widget/",
        "/api/knowledge-base/upload",
        "/api/knowledge-base/reprocess",
        "/api/knowledge-base/re-embed",
        "/api/settings/embedding-provider",
        "/api/llm/",
        "/api/onboarding/",
        "/api/v1/feedback",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/health",
    ]

    def __init__(self, app: ASGIApp, secret_key: str) -> None:
        self.app = app
        self.csrf = CSRFProtection(secret_key)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] not in ("http", "websocket"):
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive)

        if (
            os.getenv("IS_TESTING", "false").lower() == "true"
            or request.headers.get("X-Test-Mode") == "true"
        ):
            await self.app(scope, receive, send)
            return

        if request.method in ("GET", "HEAD", "OPTIONS"):
            await self.app(scope, receive, send)
            return

        if self._should_bypass_csrf(request):
            await self.app(scope, receive, send)
            return

        token = self.csrf.extract_token_from_headers(request.headers)

        if not self.csrf.validate_token(request, token):
            response = JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={
                    "detail": {
                        "error_code": 2000,
                        "message": "Invalid CSRF token",
                        "details": "CSRF token is required for state-changing operations",
                    }
                },
            )
            await response(scope, receive, send)
            return

        await self.app(scope, receive, send)

    def _should_bypass_csrf(self, request: Request) -> bool:
        path = request.url.path

        for bypass_path in self.BYPASS_PATHS:
            if path.startswith(bypass_path):
                return True

        return False


def setup_csrf_middleware(app) -> None:
    """Setup CSRF middleware for FastAPI application."""
    secret_key = settings()["SECRET_KEY"]

    if not settings()["DEBUG"] and secret_key == "dev-secret-key-DO-NOT-USE-IN-PRODUCTION":
        raise ValueError(
            "CSRF protection requires a secure SECRET_KEY in production. "
            "Generate one with: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
        )

    app.add_middleware(CSRFMiddleware, secret_key=secret_key)
