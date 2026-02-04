"""Webhook Verification API schemas.

Request and response schemas for webhook verification endpoints.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional, TypeVar, Generic

from pydantic import BaseModel, Field

T = TypeVar("T")


class MetaData(BaseModel):
    """Metadata for API responses."""

    request_id: str = Field(..., alias="requestId", description="Unique request ID for tracing")
    timestamp: str = Field(..., alias="timestamp", description="ISO-8601 timestamp of response")

    model_config = {"populate_by_name": True}


class MinimalEnvelope(BaseModel, Generic[T]):
    """Minimal response envelope pattern.

    Used for all API responses with data and metadata.
    """

    data: T = Field(..., description="Response payload")
    meta: MetaData = Field(..., description="Response metadata")


class FacebookWebhookStatus(BaseModel):
    """Facebook webhook status details."""

    webhook_url: str = Field(..., alias="webhookUrl")
    connected: bool = Field(..., description="Whether webhook is connected and working")
    last_webhook_at: Optional[str] = Field(None, alias="lastWebhookAt")
    last_verified_at: Optional[str] = Field(None, alias="lastVerifiedAt")
    subscription_status: str = Field(..., alias="subscriptionStatus")
    topics: list[str] = Field(default_factory=list, description="Subscribed webhook topics")
    error: Optional[str] = Field(None, description="Error message if not connected")


class ShopifyWebhookStatus(BaseModel):
    """Shopify webhook status details."""

    webhook_url: str = Field(..., alias="webhookUrl")
    connected: bool = Field(..., description="Whether webhook is connected and working")
    last_webhook_at: Optional[str] = Field(None, alias="lastWebhookAt")
    last_verified_at: Optional[str] = Field(None, alias="lastVerifiedAt")
    subscription_status: str = Field(..., alias="subscriptionStatus")
    topics: list[str] = Field(default_factory=list, description="Subscribed webhook topics")
    error: Optional[str] = Field(None, description="Error message if not connected")


class WebhookStatusResponse(BaseModel):
    """Webhook verification status response."""

    facebook: FacebookWebhookStatus = Field(..., description="Facebook webhook status")
    shopify: ShopifyWebhookStatus = Field(..., description="Shopify webhook status")
    overall_status: str = Field(..., alias="overallStatus", description="Overall status: ready, partial, or not_connected")
    can_go_live: bool = Field(..., alias="canGoLive", description="Whether bot is ready to accept customers")


class WebhookTestResponse(BaseModel):
    """Webhook test response."""

    test_id: str = Field(..., alias="testId", description="Unique test identifier")
    status: str = Field(..., description="Test status: success or failed")
    message: str = Field(..., description="Human-readable test result message")
    test_message_id: Optional[str] = Field(None, alias="testMessageId", description="Facebook message ID (if applicable)")
    delivered_at: Optional[str] = Field(None, alias="deliveredAt", description="Delivery timestamp (if applicable)")
    conversation_created: Optional[bool] = Field(None, alias="conversationCreated", description="Whether conversation was created")
    test_order_id: Optional[str] = Field(None, alias="testOrderId", description="Shopify test order ID (if applicable)")
    webhook_received_at: Optional[str] = Field(None, alias="webhookReceivedAt", description="Webhook receipt timestamp (if applicable)")
    order_stored: Optional[bool] = Field(None, alias="orderStored", description="Whether order was stored")
    page_id: Optional[str] = Field(None, alias="pageId", description="Facebook Page ID (if applicable)")
    shop_domain: Optional[str] = Field(None, alias="shopDomain", description="Shopify shop domain (if applicable)")
    webhook_active: Optional[bool] = Field(None, alias="webhookActive", description="Whether webhook is active (Shopify)")


class WebhookResubscribeResponse(BaseModel):
    """Webhook re-subscription response."""

    platform: str = Field(..., description="Platform name: facebook or shopify")
    status: str = Field(..., description="Re-subscription status: success, partial, or failed")
    message: str = Field(..., description="Human-readable result message")
    topics: list[Any] = Field(default_factory=list, description="Re-subscribed topics with status")
    subscribed_at: Optional[str] = Field(None, alias="subscribedAt", description="Re-subscription timestamp")
