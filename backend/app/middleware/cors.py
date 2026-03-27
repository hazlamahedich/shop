"""CORS middleware to ensure headers are always present.

This middleware ensures CORS headers are properly set even when behind
proxies like zrok that might strip headers.
"""

from __future__ import annotations

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class CORSHeaderMiddleware(BaseHTTPMiddleware):
    """Middleware to ensure CORS headers are always present in responses.

    This is needed when running behind proxies (like zrok) that might strip
    CORS headers from responses.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request and ensure CORS headers are set.

        Args:
            request: Incoming request
            call_next: Next middleware/route handler

        Returns:
            Response with CORS headers
        """
        # Get the origin from the request
        origin = request.headers.get("origin", "")

        # Define allowed origin patterns
        allowed_patterns = [
            "vercel.app",
            "localhost",
            "127.0.0.1",
            "myshopify.com",
            "trycloudflare.com",
            "zrok.io",
        ]

        # Check if origin is allowed
        is_allowed = any(pattern in origin.lower() for pattern in allowed_patterns)

        # Process the request
        response = await call_next(request)

        # Add CORS headers for allowed origins
        if origin and is_allowed:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Allow-Methods"] = (
                "GET, POST, PUT, DELETE, OPTIONS, PATCH"
            )
            response.headers["Access-Control-Allow-Headers"] = (
                "Content-Type, Authorization, X-Webhook-Signature, "
                "X-CSRF-Token, X-Merchant-Id, X-Test-Mode, Accept"
            )
            response.headers["Access-Control-Expose-Headers"] = (
                "Content-Type, X-CSRF-Token, X-Merchant-Id"
            )

        # Handle preflight OPTIONS requests
        if request.method == "OPTIONS":
            # Always return 200 OK for preflight
            from fastapi.responses import Response

            response = Response(status_code=200)
            if origin:
                if is_allowed:
                    response.headers["Access-Control-Allow-Origin"] = origin
                else:
                    # If origin not in allowed list, don't set the header
                    # This will cause the browser to block the request
                    pass
            else:
                # No origin header (direct API access, same-origin, etc.)
                response.headers["Access-Control-Allow-Origin"] = "*"

            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Allow-Methods"] = (
                "GET, POST, PUT, DELETE, OPTIONS, PATCH"
            )
            response.headers["Access-Control-Allow-Headers"] = (
                "Content-Type, Authorization, X-Webhook-Signature, "
                "X-CSRF-Token, X-Merchant-Id, X-Test-Mode, Accept"
            )
            response.headers["Access-Control-Max-Age"] = "600"

        return response
