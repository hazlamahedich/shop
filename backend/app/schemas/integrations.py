"""Pydantic schemas for Facebook integration API.

Request/response schemas with camelCase conversion for API compatibility.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, Field, field_validator


class MinimalEnvelope(BaseModel):
    """Minimal response envelope with metadata."""

    data: dict[str, Any]
    meta: MetaData


class MetaData(BaseModel):
    """Response metadata."""

    request_id: str
    timestamp: datetime


# ==================== Facebook OAuth Schemas ====================


class FacebookAuthorizeRequest(BaseModel):
    """Request to initiate Facebook OAuth flow."""

    merchant_id: int = Field(..., description="Merchant ID initiating OAuth")


class FacebookAuthorizeResponse(BaseModel):
    """Response with Facebook OAuth URL and state token."""

    auth_url: str = Field(..., alias="authUrl", description="Facebook OAuth dialog URL")
    state: str = Field(..., description="CSRF state token for callback validation")


class FacebookCallbackRequest(BaseModel):
    """Facebook OAuth callback request."""

    code: str = Field(..., description="Authorization code from Facebook")
    state: str = Field(..., description="State token for CSRF validation")


class FacebookCallbackResponse(BaseModel):
    """Response after successful Facebook OAuth callback."""

    page_id: str = Field(..., alias="pageId", description="Facebook Page ID")
    page_name: str = Field(..., alias="pageName", description="Facebook Page name")
    page_picture_url: Optional[str] = Field(None, alias="pagePictureUrl", description="Page profile picture URL")
    connected_at: datetime = Field(..., alias="connectedAt", description="Connection timestamp")


class FacebookStatusResponse(BaseModel):
    """Response with Facebook connection status."""

    connected: bool = Field(..., description="Whether Facebook is connected")
    page_id: Optional[str] = Field(None, alias="pageId", description="Facebook Page ID")
    page_name: Optional[str] = Field(None, alias="pageName", description="Facebook Page name")
    page_picture_url: Optional[str] = Field(None, alias="pagePictureUrl", description="Page profile picture URL")
    connected_at: Optional[datetime] = Field(None, alias="connectedAt", description="Connection timestamp")
    webhook_verified: bool = Field(False, alias="webhookVerified", description="Whether webhook is verified")


class FacebookDisconnectResponse(BaseModel):
    """Response after disconnecting Facebook integration."""

    disconnected: bool = Field(..., description="Whether disconnection was successful")


# ==================== Facebook Webhook Schemas ====================


class FacebookWebhookVerifyRequest(BaseModel):
    """Facebook webhook verification challenge request."""

    hub_mode: str = Field(..., alias="hub.mode")
    hub_challenge: str = Field(..., alias="hub.challenge")
    hub_verify_token: str = Field(..., alias="hub.verify_token")


class FacebookWebhookMessage(BaseModel):
    """Incoming Facebook Messenger message."""

    sender_id: str = Field(..., alias="senderId", description="Facebook PSID")
    recipient_id: str = Field(..., alias="recipientId", description="Page ID")
    message_text: Optional[str] = Field(None, alias="messageText", description="Message text content")
    attachment_url: Optional[str] = Field(None, alias="attachmentUrl", description="Attachment URL if present")
    postback_payload: Optional[str] = Field(None, alias="postbackPayload", description="Postback payload if present")
    timestamp: int = Field(..., description="Message timestamp from Facebook")


class WebhookTestResponse(BaseModel):
    """Response after testing webhook."""

    success: bool = Field(..., description="Whether webhook test was successful")
    message: str = Field(..., description="Test result message")
    webhook_status: Optional[str] = Field(None, alias="webhookStatus", description="Current webhook status")


class WebhookResubscribeResponse(BaseModel):
    """Response after resubscribing to webhook."""

    success: bool = Field(..., description="Whether resubscription was successful")
    message: str = Field(..., description="Resubscription result message")


# ==================== Error Response Schemas ====================


class ErrorResponse(BaseModel):
    """Standard error response."""

    error_code: int = Field(..., alias="errorCode")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[dict[str, Any]] = Field(None, description="Additional error details")
