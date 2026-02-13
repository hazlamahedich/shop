"""Email notification service for budget alerts.

Story 3-8: Budget Alert Notifications

Sends email notifications at:
- Warning (80%): "Budget Alert: 80% of your ${budget} budget used"
- Critical (95%): "Urgent: 95% of budget used - Action required"
- Hard Stop (100%): "Bot Paused: Budget limit reached"

Uses aiosmtplib for async email sending.
Rate limited to max 1 email per alert level per 24 hours per merchant.
"""

from __future__ import annotations

import os
from datetime import datetime
from decimal import Decimal
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any

import aiosmtplib
import structlog

from app.services.notification.base import NotificationProvider

logger = structlog.get_logger(__name__)

EMAIL_RATE_LIMIT_SECONDS = 86400  # 24 hours


class NotificationError(Exception):
    """Base exception for notification errors."""

    pass


class EmailNotificationProvider(NotificationProvider):
    """Email notification provider for budget alerts.

    Sends emails via SMTP with rate limiting to prevent spam.
    Uses templates for consistent messaging.
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
        alert_level: str,
    ) -> bool:
        """Check if we can send email (rate limiting).

        Args:
            merchant_id: Merchant ID
            alert_level: Alert level (warning/critical/hard_stop)

        Returns:
            True if email can be sent (not rate limited)
        """
        if not self.redis:
            return True

        redis_key = f"budget_alert_email:{merchant_id}:{alert_level}"

        try:
            last_sent = await self.redis.get(redis_key)
            if last_sent:
                logger.info(
                    "email_rate_limited",
                    merchant_id=merchant_id,
                    alert_level=alert_level,
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
        alert_level: str,
    ) -> None:
        """Mark email as sent for rate limiting.

        Args:
            merchant_id: Merchant ID
            alert_level: Alert level
        """
        if not self.redis:
            return

        redis_key = f"budget_alert_email:{merchant_id}:{alert_level}"

        try:
            await self.redis.set(
                redis_key,
                datetime.utcnow().isoformat(),
                ex=EMAIL_RATE_LIMIT_SECONDS,
            )
        except Exception as e:
            logger.warning(
                "email_rate_mark_failed",
                merchant_id=merchant_id,
                error=str(e),
            )

    def _get_template_content(
        self,
        alert_level: str,
        percentage: int,
        budget_cap: Decimal,
        remaining_budget: Decimal,
    ) -> tuple[str, str]:
        """Get email subject and body from template.

        Args:
            alert_level: Alert level (warning/critical/hard_stop)
            percentage: Budget usage percentage
            budget_cap: Total budget
            remaining_budget: Remaining budget

        Returns:
            Tuple of (subject, html_body)
        """
        template_map = {
            "warning": "budget_alert_warning.html",
            "critical": "budget_alert_critical.html",
            "hard_stop": "budget_alert_hard_stop.html",
        }

        subject_map = {
            "warning": f"Budget Alert: {percentage}% of your ${budget_cap:.2f} budget used",
            "critical": f"Urgent: {percentage}% of budget used - Action required",
            "hard_stop": "Bot Paused: Budget limit reached",
        }

        template_file = template_map.get(alert_level, "budget_alert_warning.html")
        template_path = self.template_dir / template_file

        try:
            html_body = template_path.read_text()
        except FileNotFoundError:
            html_body = self._get_fallback_template(
                alert_level, percentage, budget_cap, remaining_budget
            )

        html_body = html_body.replace("{{percentage}}", str(percentage))
        html_body = html_body.replace("{{budget_cap}}", f"${budget_cap:.2f}")
        html_body = html_body.replace("{{remaining_budget}}", f"${remaining_budget:.2f}")

        return (subject_map.get(alert_level, "Budget Alert"), html_body)

    def _get_fallback_template(
        self,
        alert_level: str,
        percentage: int,
        budget_cap: Decimal,
        remaining_budget: Decimal,
    ) -> str:
        """Get fallback HTML template if file not found.

        Args:
            alert_level: Alert level
            percentage: Budget percentage
            budget_cap: Budget cap
            remaining_budget: Remaining budget

        Returns:
            HTML string
        """
        color_map = {
            "warning": "#FEF3C7",
            "critical": "#FEE2E2",
            "hard_stop": "#FEE2E2",
        }

        bg_color = color_map.get(alert_level, "#FEF3C7")

        return f"""
        <!DOCTYPE html>
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background-color: {bg_color}; padding: 20px; border-radius: 8px;">
                <h2>Budget Alert</h2>
                <p>You have used {percentage}% of your monthly budget.</p>
                <p><strong>Budget:</strong> ${budget_cap:.2f}</p>
                <p><strong>Remaining:</strong> ${remaining_budget:.2f}</p>
                <p>
                    <a href="#" style="background-color: #3B82F6; color: white; padding: 10px 20px;
                       text-decoration: none; border-radius: 4px;">
                        Manage Budget
                    </a>
                </p>
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
        """Send a budget alert email.

        Args:
            merchant_id: Target merchant ID
            message: Alert message
            metadata: Must contain 'email', 'alert_level', 'percentage',
                     'budget_cap', 'remaining_budget'

        Returns:
            True if email was sent successfully

        Raises:
            NotificationError: If sending fails
        """
        email = metadata.get("email")
        alert_level = metadata.get("alert_level", "warning")
        percentage = metadata.get("percentage", 80)
        budget_cap = Decimal(str(metadata.get("budget_cap", 0)))
        remaining_budget = Decimal(str(metadata.get("remaining_budget", 0)))

        if not email:
            logger.warning("email_missing", merchant_id=merchant_id)
            return False

        if not await self._can_send_email(merchant_id, alert_level):
            return True

        subject, html_body = self._get_template_content(
            alert_level, percentage, budget_cap, remaining_budget
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

            await self._mark_email_sent(merchant_id, alert_level)

            logger.info(
                "budget_alert_email_sent",
                merchant_id=merchant_id,
                alert_level=alert_level,
                email=email,
            )

            return True

        except Exception as e:
            logger.error(
                "budget_alert_email_failed",
                merchant_id=merchant_id,
                alert_level=alert_level,
                error=str(e),
            )
            raise NotificationError(f"Failed to send email: {e}") from e

    async def send_batch(
        self,
        notifications: list[dict[str, Any]],
    ) -> int:
        """Send multiple email notifications.

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
                    "batch_email_failed",
                    merchant_id=notification.get("merchant_id"),
                    error=str(e),
                )

        return success_count
