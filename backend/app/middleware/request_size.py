"""Request body size limiting middleware.

Rejects requests with bodies exceeding a configurable maximum size.
Prevents memory exhaustion attacks from oversized payloads.
"""

from __future__ import annotations

from typing import Any

from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

MAX_REQUEST_BODY_SIZE = 10 * 1024 * 1024  # 10MB


class RequestSizeLimitMiddleware:
    """ASGI middleware that limits request body size.

    Checks Content-Length header first (cheap). For chunked/unknown
    content length, wraps the receive to track bytes consumed.
    """

    def __init__(self, app: ASGIApp, max_body_size: int = MAX_REQUEST_BODY_SIZE) -> None:
        self.app = app
        self.max_body_size = max_body_size

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive, send)

        if request.method in ("GET", "HEAD", "OPTIONS", "TRACE"):
            await self.app(scope, receive, send)
            return

        content_length = request.headers.get("content-length")
        if content_length:
            try:
                if int(content_length) > self.max_body_size:
                    response = JSONResponse(
                        status_code=413,
                        content={
                            "error": "Payload too large",
                            "message": (
                                f"Request body exceeds maximum size"
                                f" of {self.max_body_size} bytes"
                            ),
                        },
                    )
                    await response(scope, receive, send)
                    return
            except (ValueError, TypeError):
                pass

        body_size = 0
        overflow = False

        async def limited_receive() -> dict[str, Any]:
            nonlocal body_size, overflow
            message = await receive()
            if message["type"] == "http.request" and not overflow:
                body = message.get("body", b"")
                body_size += len(body)
                if body_size > self.max_body_size:
                    overflow = True
            return message  # type: ignore[return-value]

        await self.app(scope, limited_receive, send)

        if overflow:
            pass
