"""Webhook Verification API schemas.

Request and response schemas for webhook verification endpoints.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from enum import Enum
from pydantic import Field

from app.schemas.base import BaseSchema, MetaData, MinimalEnvelope


# ==================== Enums ====================


class Platform(str, Enum):
    """Webhook platform identifiers."""

    FACEBOOK = "facebook"
    SHOPIFY = "shopify"


class WebhookStatus(str, Enum):
    """Webhook connection status values."""

    READY = "ready"
    PARTIAL = "partial"
    NOT_CONNECTED = "not_connected"
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    PENDING = "pending"
    FAILED = "failed"


class SubscriptionStatus(str, Enum):
    """Webhook subscription status values."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    FAILED = "failed"
    UNKNOWN = "unknown"


class TestStatus(str, Enum):
    """Webhook test status values."""

    SUCCESS = "success"
    FAILED = "failed"


class ResubscribeStatus(str, Enum):
    """Webhook resubscription status values."""

    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"


# ==================== Webhook Status Schemas ====================


class FacebookWebhookStatus(BaseSchema):
    """Facebook webhook status details."""

    webhook_url: str = Field(description="Webhook URL")
    connected: bool = Field(description="Whether webhook is connected and working")
    last_webhook_at: Optional[str] = Field(None, description="Last webhook received timestamp")
    last_verified_at: Optional[str] = Field(None, description="Last verification timestamp")
    subscription_status: SubscriptionStatus = Field(description="Subscription status")
    topics: list[str] = Field(default_factory=list, description="Subscribed webhook topics")
    error: Optional[str] = Field(None, description="Error message if not connected")


class ShopifyWebhookStatus(BaseSchema):
    """Shopify webhook status details."""

    webhook_url: str = Field(description="Webhook URL")
    connected: bool = Field(description="Whether webhook is connected and working")
    last_webhook_at: Optional[str] = Field(None, description="Last webhook received timestamp")
    last_verified_at: Optional[str] = Field(None, description="Last verification timestamp")
    subscription_status: SubscriptionStatus = Field(description="Subscription status")
    topics: list[str] = Field(default_factory=list, description="Subscribed webhook topics")
    error: Optional[str] = Field(None, description="Error message if not connected")


class WebhookStatusResponse(BaseSchema):
    """Webhook verification status response."""

    facebook: FacebookWebhookStatus = Field(description="Facebook webhook status")
    shopify: ShopifyWebhookStatus = Field(description="Shopify webhook status")
    overall_status: WebhookStatus = Field(description="Overall status: ready, partial, or not_connected")
    can_go_live: bool = Field(description="Whether bot is ready to accept customers")


# ==================== Webhook Test Schemas ====================


class WebhookTestResponse(BaseSchema):
    """Webhook test response."""

    test_id: str = Field(description="Unique test identifier")
    status: TestStatus = Field(description="Test status: success or failed")
    message: str = Field(description="Human-readable test result message")
    test_message_id: Optional[str] = Field(None, description="Facebook message ID (if applicable)")
    delivered_at: Optional[str] = Field(None, description="Delivery timestamp (if applicable)")
    conversation_created: Optional[bool] = Field(None, description="Whether conversation was created")
    test_order_id: Optional[str] = Field(None, description="Shopify test order ID (if applicable)")
    webhook_received_at: Optional[str] = Field(None, description="Webhook receipt timestamp (if applicable)")
    order_stored: Optional[bool] = Field(None, description="Whether order was stored")
    page_id: Optional[str] = Field(None, description="Facebook Page ID (if applicable)")
    shop_domain: Optional[str] = Field(None, description="Shopify shop domain (if applicable)")
    webhook_active: Optional[bool] = Field(None, description="Whether webhook is active (Shopify)")


# ==================== Webhook Resubscribe Schemas ====================


class WebhookResubscribeResponse(BaseSchema):
    """Webhook re-subscription response."""

    platform: Platform = Field(description="Platform name: facebook or shopify")
    status: ResubscribeStatus = Field(description="Re-subscription status: success, partial, or failed")
    message: str = Field(description="Human-readable result message")
    topics: list[Any] = Field(default_factory=list, description="Re-subscribed topics with status")
    subscribed_at: Optional[str] = Field(None, description="Re-subscription timestamp")


__all__ = [
    "MinimalEnvelope",
    "MetaData",
    "Platform",
    "WebhookStatus",
    "SubscriptionStatus",
    "TestStatus",
    "ResubscribeStatus",
    "FacebookWebhookStatus",
    "ShopifyWebhookStatus",
    "WebhookStatusResponse",
    "WebhookTestResponse",
    "WebhookResubscribeResponse",
]
