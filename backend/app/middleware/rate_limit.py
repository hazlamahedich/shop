"""Global rate limiting middleware (Redis-backed).

Provides application-wide rate limiting for all HTTP requests.
Uses Redis INCR+EXPIRE for distributed rate counting with
in-memory fallback when Redis is unavailable.
"""

from __future__ import annotations

import os
import time
from collections import defaultdict

import structlog
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

logger = structlog.get_logger(__name__)

GLOBAL_RATE_LIMIT = 300
GLOBAL_RATE_PERIOD = 60

AUTH_RATE_LIMIT = 20
AUTH_RATE_PERIOD = 60

HEALTH_CHECK_PATHS = {"/health", "/api/health/", "/"}

_in_memory_counters: dict[str, list[float]] = defaultdict(list)
_redis_client = None


def _get_redis():
    global _redis_client
    if _redis_client is not None:
        return _redis_client
    try:
        import redis.asyncio as aioredis

        from app.core.config import settings

        config = settings()
        redis_url = config.get("REDIS_URL", "redis://localhost:6379/0")
        _redis_client = aioredis.from_url(redis_url, decode_responses=True)
        return _redis_client
    except Exception:
        return None


async def _check_rate_limit_redis(key: str, limit: int, period: int) -> bool:
    redis_client = _get_redis()  # type: ignore[func-returns-value]
    if redis_client is None:
        return _check_rate_limit_memory(key, limit, period)

    try:
        pipe = redis_client.pipeline()

        current = await redis_client.get(key)
        if current is not None and int(current) >= limit:
            return True

        await pipe.incr(key)
        await pipe.expire(key, period)
        await pipe.execute()
        return False
    except Exception:
        logger.warning("global_rate_limit_redis_fallback", key=key)
        return _check_rate_limit_memory(key, limit, period)


def _check_rate_limit_memory(key: str, limit: int, period: int) -> bool:
    now = time.time()
    window_start = now - period
    _in_memory_counters[key] = [ts for ts in _in_memory_counters[key] if ts > window_start]
    if len(_in_memory_counters[key]) >= limit:
        return True
    _in_memory_counters[key].append(now)
    return False


def _get_client_ip(request: Request) -> str:
    from app.core.config import settings

    config = settings()
    trusted_proxies_str = config.get("TRUSTED_PROXIES", "")
    trusted_proxies = set(trusted_proxies_str.split(",")) if trusted_proxies_str else set()

    remote_ip = request.client.host if request.client else "unknown"

    if trusted_proxies and remote_ip in trusted_proxies:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()

    return remote_ip


class GlobalRateLimitMiddleware:
    """ASGI middleware for global request rate limiting.

    Limits:
    - Global: 300 req/min per IP
    - Auth endpoints: 20 req/min per IP
    - Health checks: exempted
    """

    def __init__(
        self,
        app: ASGIApp,
        global_limit: int = GLOBAL_RATE_LIMIT,
        global_period: int = GLOBAL_RATE_PERIOD,
        auth_limit: int = AUTH_RATE_LIMIT,
        auth_period: int = AUTH_RATE_PERIOD,
    ) -> None:
        self.app = app
        self.global_limit = global_limit
        self.global_period = global_period
        self.auth_limit = auth_limit
        self.auth_period = auth_period

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        if os.getenv("IS_TESTING", "false").lower() == "true":
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive)

        path = request.url.path
        if path in HEALTH_CHECK_PATHS:
            await self.app(scope, receive, send)
            return

        client_ip = _get_client_ip(request)

        auth_paths = ("/api/v1/auth/login", "/api/v1/auth/register", "/api/v1/auth/forgot-password")
        if any(path.startswith(p) for p in auth_paths):
            key = f"global:auth:{client_ip}"
            limited = await _check_rate_limit_redis(key, self.auth_limit, self.auth_period)
            if limited:
                response = JSONResponse(
                    status_code=429,
                    content={
                        "error": "Too many requests",
                        "message": (
                            f"Rate limit exceeded. Maximum {self.auth_limit}"
                            f" requests per {self.auth_period} seconds."
                        ),
                        "retry_after": self.auth_period,
                    },
                )
                await response(scope, receive, send)
                return

        key = f"global:{client_ip}"
        limited = await _check_rate_limit_redis(key, self.global_limit, self.global_period)
        if limited:
            response = JSONResponse(
                status_code=429,
                content={
                    "error": "Too many requests",
                    "message": (
                        f"Rate limit exceeded. Maximum {self.global_limit}"
                        f" requests per {self.global_period} seconds."
                    ),
                    "retry_after": self.global_period,
                },
            )
            await response(scope, receive, send)
            return

        await self.app(scope, receive, send)
