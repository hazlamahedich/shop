"""CORS middleware to ensure headers are always present.

This middleware ensures CORS headers are properly set even when behind
proxies like zrok that might strip headers.
"""

from __future__ import annotations

from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp, Receive, Scope, Send


class CORSHeaderMiddleware:
    """Middleware to ensure CORS headers are always present in responses (pure ASGI).

    This is needed when running behind proxies (like zrok) that might strip
    CORS headers from responses.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] not in ("http", "websocket"):
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive)
        origin = request.headers.get("origin", "")

        allowed_patterns = [
            "vercel.app",
            "localhost",
            "127.0.0.1",
            "myshopify.com",
            "trycloudflare.com",
            "zrok.io",
        ]

        is_allowed = any(pattern in origin.lower() for pattern in allowed_patterns)

        if request.method == "OPTIONS":
            cors_headers: dict[str, str] = {
                "Access-Control-Allow-Credentials": "true",
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, PATCH",
                "Access-Control-Allow-Headers": (
                    "Content-Type, Authorization, X-Webhook-Signature, "
                    "X-CSRF-Token, X-Merchant-Id, X-Test-Mode, Accept"
                ),
                "Access-Control-Max-Age": "600",
            }

            if origin:
                if is_allowed:
                    cors_headers["Access-Control-Allow-Origin"] = origin
            else:
                cors_headers["Access-Control-Allow-Origin"] = "*"

            response = Response(status_code=200, headers=cors_headers)
            await response(scope, receive, send)
            return

        initial_message: dict | None = None
        sent = False

        async def send_with_cors(message: dict) -> None:
            nonlocal sent
            if message["type"] == "http.response.start" and not sent:
                headers = dict(
                    (
                        h[0].decode() if isinstance(h[0], bytes) else h[0],
                        h[1].decode() if isinstance(h[1], bytes) else h[1],
                    )
                    for h in message.get("headers", [])
                )
                if origin and is_allowed:
                    headers["Access-Control-Allow-Origin"] = origin
                    headers["Access-Control-Allow-Credentials"] = "true"
                    headers["Access-Control-Allow-Methods"] = (
                        "GET, POST, PUT, DELETE, OPTIONS, PATCH"
                    )
                    headers["Access-Control-Allow-Headers"] = (
                        "Content-Type, Authorization, X-Webhook-Signature, "
                        "X-CSRF-Token, X-Merchant-Id, X-Test-Mode, Accept"
                    )
                    headers["Access-Control-Expose-Headers"] = (
                        "Content-Type, X-CSRF-Token, X-Merchant-Id"
                    )

                message["headers"] = [(k.encode(), v.encode()) for k, v in headers.items()]
                sent = True
            await send(message)

        await self.app(scope, receive, send_with_cors)
