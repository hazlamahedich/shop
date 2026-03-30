# Story 12-1: Rate Limiting Redis Migration

**Epic**: 12 - Security Hardening
**Priority**: P0 (Critical)
**Status**: backlog
**Estimate**: 8 hours
**Dependencies**: None

## Problem Statement

Current rate limiting uses in-memory storage (`backend/app/core/rate_limiter.py`), which:
- Does not work across multiple server instances
- Loses state on server restart
- Cannot scale horizontally
- Creates security gaps in production

## Acceptance Criteria

- [ ] Redis client configured in `backend/app/core/redis.py`
- [ ] Rate limiter updated to use Redis backend
- [ ] Fallback to in-memory for development/testing
- [ ] Redis connection pooling configured
- [ ] Environment variables for Redis URL added
- [ ] Docker Compose includes Redis service
- [ ] Tests updated to mock Redis in unit tests
- [ ] Integration tests use real Redis
- [ ] Documentation updated with Redis setup

## Technical Design

### Redis Client

```python
# backend/app/core/redis.py
from redis.asyncio import Redis
from app.core.config import settings

redis_client: Redis | None = None

async def get_redis() -> Redis:
    global redis_client
    if redis_client is None:
        redis_client = Redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )
    return redis_client
```

### Rate Limiter Changes

```python
# backend/app/core/rate_limiter.py
class RateLimiter:
    def __init__(self, use_redis: bool = True):
        self.use_redis = use_redis and settings.REDIS_URL
        
    async def is_rate_limited(self, key: str, limit: int, window: int) -> bool:
        if self.use_redis:
            return await self._redis_check(key, limit, window)
        return await self._memory_check(key, limit, window)
```

### Configuration

```python
# backend/app/core/config.py
REDIS_URL: str | None = os.getenv("REDIS_URL")
```

## Testing Strategy

1. Unit tests with mocked Redis
2. Integration tests with real Redis (Docker)
3. Load testing to verify distributed rate limiting
4. Failover testing (Redis unavailable)

## Rollback Plan

- Feature flag to disable Redis and use in-memory
- Environment variable `USE_REDIS_RATE_LIMITER=false`

## Related Files

- `backend/app/core/rate_limiter.py`
- `backend/app/core/redis.py` (new)
- `backend/app/core/config.py`
- `docker-compose.yml`
- `backend/tests/unit/test_rate_limiter.py`
- `backend/tests/integration/test_redis_rate_limiter.py`
