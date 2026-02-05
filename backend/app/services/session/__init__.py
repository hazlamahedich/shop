"""Session service package.

Manages shopper session persistence with activity tracking,
returning shopper detection, and voluntary data clearing.
"""

from app.services.session.session_service import SessionService

__all__ = ["SessionService"]
