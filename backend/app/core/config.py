"""Application configuration with environment-based settings.

IS_TESTING Pattern:
When IS_TESTING=true, services use test doubles instead of real providers.
This prevents costs and ensures deterministic tests.

Security Notice:
SECRET_KEY must be set in non-debug environments. Use a strong, random value
in production. Generate with: python -c "import secrets; print(secrets.token_urlsafe(32))"
"""

from __future__ import annotations

import os
import secrets
from functools import lru_cache
from typing import Any


@lru_cache
def settings() -> dict[str, Any]:
    """Get cached application settings.

    Settings are loaded from environment variables with sensible defaults.
    The IS_TESTING flag controls whether real or mock services are used.

    Raises:
        ValueError: If SECRET_KEY is not set in non-debug environment
    """
    is_debug = os.getenv("DEBUG", "false").lower() == "true"
    secret_key = os.getenv("SECRET_KEY")

    # Security: Require SECRET_KEY in non-debug environments
    if not secret_key and not is_debug:
        raise ValueError(
            "SECRET_KEY environment variable must be set in production. "
            "Generate one with: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
        )

    # Use a dev key only in debug mode (never acceptable for production)
    if not secret_key:
        secret_key = "dev-secret-key-DO-NOT-USE-IN-PRODUCTION"

    return {
        # Testing mode - forces use of mock services
        "IS_TESTING": os.getenv("IS_TESTING", "false").lower() == "true",
        # Application
        "APP_NAME": os.getenv("APP_NAME", "shop-backend"),
        "APP_VERSION": "0.1.0",
        "DEBUG": is_debug,
        "API_PREFIX": "/api/v1",
        # Database
        "DATABASE_URL": os.getenv(
            "DATABASE_URL",
            "postgresql+asyncpg://developer:developer@localhost:5432/shop_dev",
        ),
        "DATABASE_ECHO": os.getenv("DATABASE_ECHO", "false").lower() == "true",
        # Redis
        "REDIS_URL": os.getenv("REDIS_URL", "redis://localhost:6379/0"),
        # Security (validated above)
        "SECRET_KEY": secret_key,
        "WEBHOOK_SECRET": os.getenv("WEBHOOK_SECRET", "webhook-secret-change-in-production"),
        "ALGORITHM": "HS256",
        "ACCESS_TOKEN_EXPIRE_MINUTES": 30,
        # Shopify
        "SHOPIFY_STORE_URL": os.getenv("SHOPIFY_STORE_URL", ""),
        "SHOPIFY_STOREFRONT_TOKEN": os.getenv("SHOPIFY_STOREFRONT_TOKEN", ""),
        "SHOPIFY_API_VERSION": "2024-01",
        # Facebook Messenger
        "FACEBOOK_PAGE_ID": os.getenv("FACEBOOK_PAGE_ID", ""),
        "FACEBOOK_PAGE_ACCESS_TOKEN": os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN", ""),
        "FACEBOOK_APP_SECRET": os.getenv("FACEBOOK_APP_SECRET", ""),
        "FACEBOOK_APP_ID": os.getenv("FACEBOOK_APP_ID", ""),
        "FACEBOOK_API_VERSION": os.getenv("FACEBOOK_API_VERSION", "v19.0"),
        "FACEBOOK_REDIRECT_URI": os.getenv("FACEBOOK_REDIRECT_URI", ""),
        "FACEBOOK_ENCRYPTION_KEY": os.getenv("FACEBOOK_ENCRYPTION_KEY", ""),
        "FACEBOOK_WEBHOOK_VERIFY_TOKEN": os.getenv("FACEBOOK_WEBHOOK_VERIFY_TOKEN", ""),
        "FACEBOOK_VERIFY_TOKEN": os.getenv("FACEBOOK_VERIFY_TOKEN", "verify_token"),  # Legacy alias
        # LLM Provider
        "LLM_PROVIDER": os.getenv("LLM_PROVIDER", "ollama"),  # ollama, openai, anthropic, gemini
        "LLM_API_KEY": os.getenv("LLM_API_KEY", ""),
        "LLM_API_BASE": os.getenv("LLM_API_BASE", ""),
        "LLM_MODEL": os.getenv("LLM_MODEL", ""),
        "LLM_TEMPERATURE": float(os.getenv("LLM_TEMPERATURE", "0.7")),
        "LLM_MAX_TOKENS": int(os.getenv("LLM_MAX_TOKENS", "1000")),
        # CORS
        "CORS_ORIGINS": os.getenv(
            "CORS_ORIGINS",
            "http://localhost:3000,http://localhost:5173",
        ).split(","),
    }


def get_settings() -> dict[str, Any]:
    """Get application settings (alias for settings())."""
    return settings()


def is_testing() -> bool:
    """Check if running in test mode."""
    return settings()["IS_TESTING"]


def is_debug() -> bool:
    """Check if running in debug mode."""
    return settings()["DEBUG"]
