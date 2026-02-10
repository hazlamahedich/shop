"""Pytest configuration for API tests."""

import pytest


@pytest.fixture(autouse=True)
def reset_rate_limiter_state():
    """Reset RateLimiter state before each test to ensure test isolation.

    The RateLimiter uses class-level state (_requests, _auth_attempts) that
    persists between tests. This fixture resets that state before each test.
    """
    from app.core.rate_limiter import RateLimiter
    RateLimiter.reset_all()
    yield
    # Clean up after test
    RateLimiter.reset_all()
