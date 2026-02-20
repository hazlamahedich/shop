"""Shared HTTP client utilities with SSL certificate handling.

Provides a consistent way to create httpx clients with proper SSL
certificate verification for macOS compatibility.
"""

from __future__ import annotations

import ssl
from typing import Optional

import certifi
import httpx


def get_ssl_context() -> ssl.SSLContext:
    """Get SSL context with certifi certificates.

    Required for macOS where Python doesn't use system certificates by default.

    Returns:
        SSL context configured with certifi certificate bundle
    """
    return ssl.create_default_context(cafile=certifi.where())


def create_async_client(
    timeout: float = 30.0,
    **kwargs,
) -> httpx.AsyncClient:
    """Create an async HTTP client with proper SSL verification.

    Args:
        timeout: Request timeout in seconds
        **kwargs: Additional arguments passed to httpx.AsyncClient

    Returns:
        Configured httpx.AsyncClient with SSL support
    """
    ssl_context = get_ssl_context()
    return httpx.AsyncClient(
        verify=ssl_context,
        timeout=timeout,
        **kwargs,
    )


def create_sync_client(
    timeout: float = 30.0,
    **kwargs,
) -> httpx.Client:
    """Create a sync HTTP client with proper SSL verification.

    Args:
        timeout: Request timeout in seconds
        **kwargs: Additional arguments passed to httpx.Client

    Returns:
        Configured httpx.Client with SSL support
    """
    ssl_context = get_ssl_context()
    return httpx.Client(
        verify=ssl_context,
        timeout=timeout,
        **kwargs,
    )
