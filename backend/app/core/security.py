"""Security utilities for encryption and signature verification.

Provides Fernet symmetric encryption for sensitive data like access tokens,
and webhook signature verification for Facebook webhooks.
"""

from __future__ import annotations

import os
from base64 import urlsafe_b64encode
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.hmac import HMAC
from secrets import compare_digest
from typing import Optional
import redis
from redis import Redis

from app.core.config import settings


# Simple in-memory state storage (TODO: replace with Redis in production)
_oauth_state_store: dict[str, dict[str, any]] = {}
_redis_client: Optional[Redis] = None


def get_redis_client() -> Optional[Redis]:
    """Get Redis client for state storage.

    Returns:
        Redis client or None if Redis not configured
    """
    global _redis_client
    if _redis_client is None:
        try:
            redis_url = os.getenv("REDIS_URL")
            if redis_url:
                _redis_client = redis.from_url(redis_url, decode_responses=True)
        except Exception:
            pass
    return _redis_client


def store_oauth_state(state: str, merchant_id: int, ttl: int = 600) -> None:
    """Store OAuth state parameter for CSRF validation.

    Args:
        state: State parameter to store
        merchant_id: Associated merchant ID
        ttl: Time-to-live in seconds (default: 10 minutes)
    """
    redis_client = get_redis_client()
    if redis_client:
        redis_client.setex(f"oauth_state:{state}", ttl, str(merchant_id))
    else:
        # Fallback to in-memory storage
        import time
        _oauth_state_store[state] = {
            "merchant_id": merchant_id,
            "expires_at": time.time() + ttl
        }


def validate_oauth_state(state: str) -> Optional[int]:
    """Validate OAuth state parameter and return merchant_id.

    Args:
        state: State parameter to validate

    Returns:
        Merchant ID if valid, None otherwise
    """
    redis_client = get_redis_client()
    if redis_client:
        merchant_id_str = redis_client.get(f"oauth_state:{state}")
        if merchant_id_str:
            # Delete after validation (one-time use)
            redis_client.delete(f"oauth_state:{state}")
            return int(merchant_id_str)
    else:
        # Fallback to in-memory storage
        import time
        if state in _oauth_state_store:
            data = _oauth_state_store[state]
            if time.time() < data["expires_at"]:
                del _oauth_state_store[state]
                return data["merchant_id"]
    return None


def get_fernet() -> Fernet:
    """Get Fernet instance for token encryption.

    Returns:
        Fernet instance configured with FACEBOOK_ENCRYPTION_KEY

    Raises:
        ValueError: If FACEBOOK_ENCRYPTION_KEY is not set
    """
    key = os.getenv("FACEBOOK_ENCRYPTION_KEY")
    if not key:
        raise ValueError(
            "FACEBOOK_ENCRYPTION_KEY environment variable must be set. "
            "Generate one with: python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'"
        )
    return Fernet(key.encode())


def encrypt_access_token(token: str) -> str:
    """Encrypt Facebook page access token.

    Args:
        token: Plain text access token

    Returns:
        Encrypted token as base64 string
    """
    fernet = get_fernet()
    encrypted = fernet.encrypt(token.encode())
    return encrypted.decode()


def decrypt_access_token(encrypted: str) -> str:
    """Decrypt Facebook page access token.

    Args:
        encrypted: Encrypted token string

    Returns:
        Decrypted plain text token

    Raises:
        ValueError: If decryption fails
    """
    fernet = get_fernet()
    decrypted = fernet.decrypt(encrypted.encode())
    return decrypted.decode()


def verify_webhook_signature(
    raw_payload: bytes,
    signature: str | None,
    app_secret: str,
) -> bool:
    """Verify X-Hub-Signature-256 from Facebook webhook.

    Args:
        raw_payload: Raw request body bytes
        signature: X-Hub-Signature-256 header value (format: sha256=<hash>)
        app_secret: Facebook App Secret

    Returns:
        True if signature is valid, False otherwise
    """
    if not signature:
        return False

    # signature format: sha256=<hash>
    if not signature.startswith("sha256="):
        return False

    expected_hash = signature[7:]  # Remove "sha256=" prefix

    # Compute HMAC-SHA256 of raw payload
    h = HMAC(app_secret.encode(), hashes.SHA256())
    h.update(raw_payload)
    computed_hash = h.finalize().hex()

    # Use constant-time comparison to prevent timing attacks
    return compare_digest(computed_hash, expected_hash)


def generate_oauth_state(merchant_id: int) -> str:
    """Generate secure random state parameter for OAuth CSRF protection.

    Args:
        merchant_id: Associated merchant ID for validation

    Returns:
        URL-safe base64 encoded random string
    """
    import secrets
    state = secrets.token_urlsafe(32)
    store_oauth_state(state, merchant_id)
    return state


def generate_webhook_verify_token() -> str:
    """Generate a random verify token for Facebook webhook setup.

    Returns:
        URL-safe base64 encoded random string
    """
    import secrets
    return secrets.token_urlsafe(32)


def verify_shopify_webhook_hmac(
    raw_payload: bytes,
    hmac_header: str,
    api_secret: str,
) -> bool:
    """Verify Shopify webhook HMAC signature.

    Args:
        raw_payload: Raw webhook payload bytes
        hmac_header: X-Shopify-Hmac-Sha256 header value
        api_secret: Shopify API secret

    Returns:
        True if signature is valid
    """
    import hmac
    import hashlib
    import base64
    from secrets import compare_digest

    # Decode HMAC header (base64 encoded)
    expected_hmac = base64.b64decode(hmac_header)

    # Compute HMAC of payload
    computed_hmac = hmac.new(
        api_secret.encode(),
        raw_payload,
        hashlib.sha256
    ).digest()

    # Use constant-time comparison to prevent timing attacks
    return compare_digest(computed_hmac, expected_hmac)
