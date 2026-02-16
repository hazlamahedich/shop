"""Handoff email notification provider.

Story 4-6: Handoff Notifications

Sends email notifications when conversations need human attention.
Uses templates with urgency-based color coding.
Rate limited to max 1 email per urgency level per merchant per 24 hours.
"""

from __future__ import annotations

import os
from datetime import datetime, UTC
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any

import aiosmtplib
import structlog

from app.services.notification.base import NotificationProvider

logger = structlog.get_logger(__name__)

HANDOFF_EMAIL_RATE_KEY = "handoff_email:{merchant_id}:{urgency}"
EMAIL_RATE_TTL = 86400  # 24 hours


class NotificationError(Exception):
    """Base exception for notification errors."""

    pass


class HandoffEmailProvider(NotificationProvider):
    """Email notification provider for handoff alerts.

    Sends emails via SMTP with rate limiting to prevent spam.
    Uses urgency-colored templates for consistent messaging.
    """

    def __init__(self, redis_client: Any | None = None) -> None:
        """Initialize email provider.

        Args:
            redis_client: Optional Redis client for rate limiting
        """
        self.redis = redis_client
        self.smtp_host = os.getenv("SMTP_HOST", "localhost")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.email_from = os.getenv("EMAIL_FROM_ADDRESS", "alerts@shop.local")

        template_dir = Path(__file__).parent / "templates"
        self.template_dir = template_dir

    async def _can_send_email(
        self,
        merchant_id: int,
        urgency: str,
    ) -> bool:
        """Check if we can send email (rate limiting).

        Args:
            merchant_id: Merchant ID
            urgency: Urgency level (high/medium/low)

        Returns:
            True if email can be sent (not rate limited)
        """
        if not self.redis:
            return True

        redis_key = HANDOFF_EMAIL_RATE_KEY.format(
            merchant_id=merchant_id,
            urgency=urgency,
        )

        try:
            last_sent = await self.redis.get(redis_key)
            if last_sent:
                logger.info(
                    "handoff_email_rate_limited",
                    merchant_id=merchant_id,
                    urgency=urgency,
                )
                return False
            return True
        except Exception as e:
            logger.warning(
                "email_rate_check_failed",
                merchant_id=merchant_id,
                error=str(e),
            )
            return True

    async def _mark_email_sent(
        self,
        merchant_id: int,
        urgency: str,
    ) -> None:
        """Mark email as sent for rate limiting.

        Args:
            merchant_id: Merchant ID
            urgency: Urgency level
        """
        if not self.redis:
            return

        redis_key = HANDOFF_EMAIL_RATE_KEY.format(
            merchant_id=merchant_id,
            urgency=urgency,
        )

        try:
            await self.redis.set(
                redis_key,
                datetime.now(UTC).isoformat(),
                ex=EMAIL_RATE_TTL,
            )
        except Exception as e:
            logger.warning(
                "email_rate_mark_failed",
                merchant_id=merchant_id,
                error=str(e),
            )

    def _get_template_content(
        self,
        urgency: str,
        customer_name: str,
        wait_time: str,
        handoff_reason: str,
        conversation_preview: str,
        dashboard_url: str,
    ) -> tuple[str, str]:
        """Get email subject and body from template.

        Args:
            urgency: Urgency level (high/medium/low)
            customer_name: Customer display name
            wait_time: Formatted wait time
            handoff_reason: Reason for handoff
            conversation_preview: Last 3 messages preview
            dashboard_url: Link to conversation in dashboard

        Returns:
            Tuple of (subject, html_body)
        """
        urgency_config = {
            "high": {
                "emoji": "🔴",
                "label": "HIGH",
                "color": "#DC2626",
                "bg_color": "#FEE2E2",
            },
            "medium": {
                "emoji": "🟡",
                "label": "MEDIUM",
                "color": "#D97706",
                "bg_color": "#FEF3C7",
            },
            "low": {
                "emoji": "🟢",
                "label": "LOW",
                "color": "#059669",
                "bg_color": "#D1FAE5",
            },
        }

        config = urgency_config.get(urgency, urgency_config["low"])

        template_file = f"handoff_notification_{urgency}.html"
        template_path = self.template_dir / template_file

        try:
            html_body = template_path.read_text()
        except FileNotFoundError:
            html_body = self._get_fallback_template(
                config,
                customer_name,
                wait_time,
                handoff_reason,
                conversation_preview,
                dashboard_url,
            )

        html_body = html_body.replace("{{customer_name}}", customer_name)
        html_body = html_body.replace("{{wait_time}}", wait_time)
        html_body = html_body.replace("{{handoff_reason}}", handoff_reason)
        html_body = html_body.replace("{{conversation_preview}}", conversation_preview)
        html_body = html_body.replace("{{dashboard_url}}", dashboard_url)

        subject = f"{config['emoji']} Customer Needs Help - {config['label']} Priority"

        return (subject, html_body)

    def _get_fallback_template(
        self,
        config: dict[str, str],
        customer_name: str,
        wait_time: str,
        handoff_reason: str,
        conversation_preview: str,
        dashboard_url: str,
    ) -> str:
        """Get fallback HTML template if file not found.

        Args:
            config: Urgency configuration dict
            customer_name: Customer display name
            wait_time: Formatted wait time
            handoff_reason: Reason for handoff
            conversation_preview: Last 3 messages preview
            dashboard_url: Link to conversation in dashboard

        Returns:
            HTML string
        """
        return f"""
        <!DOCTYPE html>
        <html>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                     background-color: #f3f4f6; margin: 0; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; background-color: white;
                        border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">

                <div style="background-color: {config["bg_color"]}; padding: 24px; text-align: center;">
                    <span style="font-size: 48px;">{config["emoji"]}</span>
                    <h1 style="color: {config["color"]}; margin: 16px 0 0 0;">Customer Needs Help</h1>
                    <p style="color: {config["color"]}; margin: 8px 0 0 0;">{config["label"]} Priority</p>
                </div>

                <div style="padding: 24px;">
                    <p style="font-size: 16px; color: #374151; margin-bottom: 16px;">
                        A customer conversation needs human attention.
                    </p>

                    <div style="background-color: #F9FAFB; border-radius: 8px; padding: 16px; margin-bottom: 24px;">
                        <table style="width: 100%; border-collapse: collapse;">
                            <tr>
                                <td style="color: #6B7280; padding: 8px 0;">Customer:</td>
                                <td style="text-align: right; font-weight: 600; color: #111827;">{customer_name}</td>
                            </tr>
                            <tr>
                                <td style="color: #6B7280; padding: 8px 0; border-top: 1px solid #E5E7EB;">Wait Time:</td>
                                <td style="text-align: right; font-weight: 600; color: #111827; border-top: 1px solid #E5E7EB;">
                                    {wait_time}
                                </td>
                            </tr>
                            <tr>
                                <td style="color: #6B7280; padding: 8px 0; border-top: 1px solid #E5E7EB;">Reason:</td>
                                <td style="text-align: right; font-weight: 600; color: #111827; border-top: 1px solid #E5E7EB;">
                                    {handoff_reason}
                                </td>
                            </tr>
                        </table>
                    </div>

                    <div style="background-color: #F9FAFB; border-radius: 8px; padding: 16px; margin-bottom: 24px;">
                        <h3 style="color: #374151; margin: 0 0 12px 0; font-size: 14px;">Conversation Preview:</h3>
                        <pre style="white-space: pre-wrap; font-family: inherit; color: #6B7280; margin: 0; font-size: 14px;">{conversation_preview}</pre>
                    </div>

                    <div style="text-align: center;">
                        <a href="{dashboard_url}"
                           style="display: inline-block; background-color: {config["color"]}; color: white;
                                  padding: 12px 24px; text-decoration: none; border-radius: 6px;
                                  font-weight: 600;">
                            View Conversation
                        </a>
                    </div>
                </div>

                <div style="background-color: #F9FAFB; padding: 16px 24px; border-top: 1px solid #E5E7EB;">
                    <p style="font-size: 12px; color: #9CA3AF; margin: 0;">
                        This is an automated alert from your shop bot dashboard.
                        Please respond promptly to assist this customer.
                    </p>
                </div>
            </div>
        </body>
        </html>
        """

    async def send(
        self,
        merchant_id: int,
        message: str,
        metadata: dict[str, Any],
    ) -> bool:
        """Send a handoff notification email.

        Args:
            merchant_id: Target merchant ID
            message: Alert message (plain text body)
            metadata: Must contain 'email', 'urgency', 'customer_name',
                     'wait_time', 'handoff_reason', 'conversation_preview',
                     'dashboard_url', 'conversation_id'

        Returns:
            True if email was sent successfully

        Raises:
            NotificationError: If sending fails
        """
        email = metadata.get("email")
        urgency = metadata.get("urgency", "low")
        customer_name = metadata.get("customer_name", "Unknown Customer")
        wait_time = metadata.get("wait_time", "0s")
        handoff_reason = metadata.get("handoff_reason", "unknown")
        conversation_preview = metadata.get("conversation_preview", "")
        dashboard_url = metadata.get("dashboard_url", "#")
        conversation_id = metadata.get("conversation_id")

        if not email:
            logger.warning("handoff_email_missing", merchant_id=merchant_id)
            return False

        if not await self._can_send_email(merchant_id, urgency):
            return True

        subject, html_body = self._get_template_content(
            urgency=urgency,
            customer_name=customer_name,
            wait_time=wait_time,
            handoff_reason=handoff_reason,
            conversation_preview=conversation_preview,
            dashboard_url=dashboard_url,
        )

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.email_from
            msg["To"] = email

            text_body = message
            msg.attach(MIMEText(text_body, "plain"))
            msg.attach(MIMEText(html_body, "html"))

            await aiosmtplib.send(
                msg,
                hostname=self.smtp_host,
                port=self.smtp_port,
                username=self.smtp_user if self.smtp_user else None,
                password=self.smtp_password if self.smtp_password else None,
                start_tls=True,
            )

            await self._mark_email_sent(merchant_id, urgency)

            logger.info(
                "handoff_email_sent",
                merchant_id=merchant_id,
                conversation_id=conversation_id,
                urgency=urgency,
                email=email,
            )

            return True

        except Exception as e:
            logger.error(
                "handoff_email_failed",
                merchant_id=merchant_id,
                conversation_id=conversation_id,
                urgency=urgency,
                error=str(e),
            )
            raise NotificationError(f"Failed to send handoff email: {e}") from e

    async def send_batch(
        self,
        notifications: list[dict[str, Any]],
    ) -> int:
        """Send multiple handoff email notifications.

        Args:
            notifications: List of dicts with merchant_id, message, metadata

        Returns:
            Number of successfully sent notifications
        """
        success_count = 0

        for notification in notifications:
            try:
                await self.send(
                    merchant_id=notification["merchant_id"],
                    message=notification["message"],
                    metadata=notification.get("metadata", {}),
                )
                success_count += 1
            except NotificationError as e:
                logger.warning(
                    "batch_handoff_email_failed",
                    merchant_id=notification.get("merchant_id"),
                    error=str(e),
                )

        return success_count


__all__ = [
    "HandoffEmailProvider",
    "NotificationError",
    "HANDOFF_EMAIL_RATE_KEY",
    "EMAIL_RATE_TTL",
]
