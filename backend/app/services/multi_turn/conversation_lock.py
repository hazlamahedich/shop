"""Per-conversation lock manager for multi-turn state.

Story 11-2: Multi-Turn Query Handling
Prevents race conditions when concurrent messages arrive for the same conversation.
"""

from __future__ import annotations

import asyncio
import time

import structlog

logger = structlog.get_logger(__name__)

LOCK_TTL_SECONDS = 300  # 5 minutes


class ConversationLockManager:
    """Manages per-conversation asyncio.Lock instances with TTL cleanup.

    Prevents memory leaks by removing locks idle > 5 minutes.
    Thread-safe lock creation using a global lock.
    """

    def __init__(self, ttl_seconds: int = LOCK_TTL_SECONDS) -> None:
        self._locks: dict[int, asyncio.Lock] = {}
        self._last_access: dict[int, float] = {}
        self._creation_lock = asyncio.Lock()
        self._ttl_seconds = ttl_seconds
        self.logger = structlog.get_logger(__name__)

    async def get_lock(self, conversation_id: int) -> asyncio.Lock:
        async with self._creation_lock:
            self._cleanup_expired_locks()

            if conversation_id not in self._locks:
                self._locks[conversation_id] = asyncio.Lock()
                self.logger.debug(
                    "Created new conversation lock",
                    conversation_id=conversation_id,
                )

            self._last_access[conversation_id] = time.monotonic()
            return self._locks[conversation_id]

    def _cleanup_expired_locks(self) -> None:
        now = time.monotonic()
        expired_ids = [
            conv_id
            for conv_id, last_access in self._last_access.items()
            if now - last_access > self._ttl_seconds and not self._locks[conv_id].locked()
        ]

        for conv_id in expired_ids:
            del self._locks[conv_id]
            del self._last_access[conv_id]
            self.logger.debug(
                "Cleaned up expired conversation lock",
                conversation_id=conv_id,
            )

    @property
    def active_lock_count(self) -> int:
        return len(self._locks)
