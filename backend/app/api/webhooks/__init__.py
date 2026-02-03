"""Webhooks API module."""

from __future__ import annotations

from app.api.webhooks.facebook import router as facebook_router

__all__ = ["facebook_router"]
