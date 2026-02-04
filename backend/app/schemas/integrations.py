"""Pydantic schemas for Facebook and Shopify integration APIs.

Request/response schemas with camelCase conversion for API compatibility.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional, Any
from pydantic import Field

from app.schemas.base import BaseSchema, MinimalEnvelope, MetaData


# ==================== Facebook OAuth Schemas ====================


class FacebookAuthorizeRequest(BaseSchema):
    """Request to initiate Facebook OAuth flow."""

    merchant_id: int = Field(..., description="Merchant ID initiating OAuth")


class FacebookAuthorizeResponse(BaseSchema):
    """Response with Facebook OAuth URL and state token."""

    auth_url: str = Field(..., description="Facebook OAuth dialog URL")
    state: str = Field(..., description="CSRF state token for callback validation")


class FacebookCallbackRequest(BaseSchema):
    """Facebook OAuth callback request."""

    code: str = Field(..., description="Authorization code from Facebook")
    state: str = Field(..., description="State token for CSRF validation")


class FacebookCallbackResponse(BaseSchema):
    """Response after successful Facebook OAuth callback."""

    page_id: str = Field(..., description="Facebook Page ID")
    page_name: str = Field(..., description="Facebook Page name")
    page_picture_url: Optional[str] = Field(None, description="Page profile picture URL")
    connected_at: datetime = Field(..., description="Connection timestamp")


class FacebookStatusResponse(BaseSchema):
    """Response with Facebook connection status."""

    connected: bool = Field(..., description="Whether Facebook is connected")
    page_id: Optional[str] = Field(None, description="Facebook Page ID")
    page_name: Optional[str] = Field(None, description="Facebook Page name")
    page_picture_url: Optional[str] = Field(None, description="Page profile picture URL")
    connected_at: Optional[datetime] = Field(None, description="Connection timestamp")
    webhook_verified: bool = Field(False, description="Whether webhook is verified")


class FacebookDisconnectResponse(BaseSchema):
    """Response after disconnecting Facebook integration."""

    disconnected: bool = Field(..., description="Whether disconnection was successful")


# ==================== Facebook Webhook Schemas ====================


class FacebookWebhookVerifyRequest(BaseSchema):
    """Facebook webhook verification challenge request."""

    hub_mode: str = Field(..., alias="hub.mode")
    hub_challenge: str = Field(..., alias="hub.challenge")
    hub_verify_token: str = Field(..., alias="hub.verify_token")


class FacebookWebhookMessage(BaseSchema):
    """Incoming Facebook Messenger message."""

    sender_id: str = Field(..., description="Facebook PSID")
    recipient_id: str = Field(..., description="Page ID")
    message_text: Optional[str] = Field(None, description="Message text content")
    attachment_url: Optional[str] = Field(None, description="Attachment URL if present")
    postback_payload: Optional[str] = Field(None, description="Postback payload if present")
    timestamp: int = Field(..., description="Message timestamp from Facebook")


class WebhookTestResponse(BaseSchema):
    """Response after testing webhook."""

    success: bool = Field(..., description="Whether webhook test was successful")
    message: str = Field(..., description="Test result message")
    webhook_status: Optional[str] = Field(None, description="Current webhook status")


class WebhookResubscribeResponse(BaseSchema):
    """Response after resubscribing to webhook."""

    success: bool = Field(..., description="Whether resubscription was successful")
    message: str = Field(..., description="Resubscription result message")


# ==================== Error Response Schemas ====================


class ErrorResponse(BaseSchema):
    """Standard error response."""

    error_code: int = Field(...)
    message: str = Field(..., description="Human-readable error message")
    details: Optional[dict[str, Any]] = Field(None, description="Additional error details")


# ==================== Shopify OAuth Schemas ====================


class ShopifyAuthorizeRequest(BaseSchema):
    """Request to initiate Shopify OAuth flow."""

    merchant_id: int = Field(..., description="Merchant ID initiating OAuth")
    shop_domain: str = Field(..., description="Shopify shop domain")


class ShopifyAuthorizeResponse(BaseSchema):
    """Response with Shopify OAuth URL and state token."""

    auth_url: str = Field(..., description="Shopify OAuth dialog URL")
    state: str = Field(..., description="CSRF state token for callback validation")


class ShopifyCallbackRequest(BaseSchema):
    """Shopify OAuth callback request."""

    code: str = Field(..., description="Authorization code from Shopify")
    state: str = Field(..., description="State token for CSRF validation")
    shop: str = Field(..., description="Shopify shop domain")


class ShopifyCallbackResponse(BaseSchema):
    """Response after successful Shopify OAuth callback."""

    shop_domain: str = Field(..., description="Shopify shop domain")
    shop_name: str = Field(..., description="Shopify shop name")
    connected_at: datetime = Field(..., description="Connection timestamp")


class ShopifyStatusResponse(BaseSchema):
    """Response with Shopify connection status."""

    connected: bool = Field(..., description="Whether Shopify is connected")
    shop_domain: Optional[str] = Field(None, description="Shopify shop domain")
    shop_name: Optional[str] = Field(None, description="Shopify shop name")
    storefront_api_connected: bool = Field(False, description="Storefront API verified")
    admin_api_connected: bool = Field(False, description="Admin API verified")
    webhook_subscribed: bool = Field(False, description="Webhook subscribed")
    connected_at: Optional[datetime] = Field(None, description="Connection timestamp")


class ShopifyDisconnectResponse(BaseSchema):
    """Response after disconnecting Shopify integration."""

    disconnected: bool = Field(..., description="Whether disconnection was successful")


__all__ = [
    "MinimalEnvelope",
    "MetaData",
    "FacebookAuthorizeRequest",
    "FacebookAuthorizeResponse",
    "FacebookCallbackRequest",
    "FacebookCallbackResponse",
    "FacebookStatusResponse",
    "FacebookDisconnectResponse",
    "FacebookWebhookVerifyRequest",
    "FacebookWebhookMessage",
    "WebhookTestResponse",
    "WebhookResubscribeResponse",
    "ErrorResponse",
    "ShopifyAuthorizeRequest",
    "ShopifyAuthorizeResponse",
    "ShopifyCallbackRequest",
    "ShopifyCallbackResponse",
    "ShopifyStatusResponse",
    "ShopifyDisconnectResponse",
]
