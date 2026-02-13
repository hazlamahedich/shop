"""Notification service package.

Provides notification providers for different channels (in-app, email, etc).
"""

from app.services.notification.base import NotificationProvider
from app.services.notification.in_app_provider import InAppNotificationProvider

__all__ = [
    "NotificationProvider",
    "InAppNotificationProvider",
]
