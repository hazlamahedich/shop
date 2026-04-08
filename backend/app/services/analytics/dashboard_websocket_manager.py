"""Dashboard WebSocket Connection Manager.

Provides real-time analytics updates for dashboard connections.
Uses Redis Pub/Sub for scalable message delivery across multiple instances.

Story 10.7: Knowledge Effectiveness Widget - Real-time Updates
"""

from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime
from typing import Any

import redis.asyncio as redis
import structlog
from fastapi import WebSocket

from app.core.config import settings
from app.core.connection_limits import (
    MAX_CONNECTIONS_PER_DASHBOARD_MERCHANT,
    MAX_TOTAL_DASHBOARD_CONNECTIONS,
)

logger = structlog.get_logger(__name__)


class DashboardConnectionManager:
    """Manages WebSocket connections for dashboard analytics.

    Designed for merchant dashboard connections that receive real-time
    analytics updates when data changes (e.g., new RAG queries, metrics).

    Uses Redis Pub/Sub for cross-instance message delivery.

    Attributes:
        _connections: Map of merchant_id -> set of WebSocket connections
        _redis: Redis client for pub/sub
        _pubsub: Redis pubsub instances per merchant
        _tasks: Background tasks for listening to Redis channels
    """

    def __init__(self, redis_client: redis.Redis | None = None) -> None:
        """Initialize the dashboard connection manager.

        Args:
            redis_client: Optional Redis client (creates default if not provided)
        """
        self._connections: dict[int, set[WebSocket]] = {}
        self._redis: redis.Redis | None = redis_client
        self._pubsub_instances: dict[int, Any] = {}
        self._listener_tasks: dict[int, asyncio.Task] = {}
        self._lock = asyncio.Lock()
        self._logger = structlog.get_logger(__name__)
        self._total_connections = 0

    def _get_redis(self) -> redis.Redis:
        """Get or create Redis client."""
        if self._redis is None:
            config = settings()
            redis_url = config.get("REDIS_URL", "redis://localhost:6379/0")
            self._redis = redis.from_url(redis_url, decode_responses=True)
        return self._redis

    async def connect(self, merchant_id: int, websocket: WebSocket) -> None:
        """Accept and register a new dashboard WebSocket connection.

        Args:
            merchant_id: Merchant identifier
            websocket: WebSocket connection from FastAPI
        """
        async with self._lock:
            if self._total_connections >= MAX_TOTAL_DASHBOARD_CONNECTIONS:
                self._logger.warning(
                    "dashboard_ws_rejected_total_limit",
                    merchant_id=merchant_id,
                    total_connections=self._total_connections,
                    limit=MAX_TOTAL_DASHBOARD_CONNECTIONS,
                )
                await websocket.close(code=1013, reason="Server overloaded")
                return

            merchant_conns = len(self._connections.get(merchant_id, set()))
            if merchant_conns >= MAX_CONNECTIONS_PER_DASHBOARD_MERCHANT:
                self._logger.warning(
                    "dashboard_ws_rejected_merchant_limit",
                    merchant_id=merchant_id,
                    merchant_connections=merchant_conns,
                    limit=MAX_CONNECTIONS_PER_DASHBOARD_MERCHANT,
                )
                await websocket.close(code=1008, reason="Too many connections for merchant")
                return

        try:
            await websocket.accept()
        except Exception as e:
            self._logger.error(
                "dashboard_ws_accept_failed",
                merchant_id=merchant_id,
                error=str(e),
            )
            return

        async with self._lock:
            if merchant_id not in self._connections:
                self._connections[merchant_id] = set()
                await self._start_redis_listener(merchant_id)

            self._connections[merchant_id].add(websocket)
            self._total_connections += 1
            conn_count = len(self._connections[merchant_id])

        self._logger.info(
            "dashboard_ws_connected",
            merchant_id=merchant_id,
            connection_count=conn_count,
            total_merchants=len(self._connections),
        )

        # Send connection confirmation
        try:
            await self._send_to_websocket(
                websocket,
                {
                    "type": "connected",
                    "data": {
                        "merchantId": merchant_id,
                        "timestamp": datetime.now(UTC).isoformat(),
                    },
                },
            )
        except Exception as e:
            self._logger.error(
                "dashboard_ws_send_confirmation_failed",
                merchant_id=merchant_id,
                error=str(e),
            )

    async def disconnect(self, merchant_id: int, websocket: WebSocket) -> None:
        """Remove a dashboard WebSocket connection.

        Args:
            merchant_id: Merchant identifier
            websocket: WebSocket connection to remove
        """
        async with self._lock:
            if merchant_id in self._connections:
                self._connections[merchant_id].discard(websocket)
                self._total_connections = max(0, self._total_connections - 1)

                if not self._connections[merchant_id]:
                    del self._connections[merchant_id]
                    await self._stop_redis_listener(merchant_id)

        self._logger.info(
            "dashboard_ws_disconnected",
            merchant_id=merchant_id,
        )

    async def broadcast_to_merchant(
        self,
        merchant_id: int,
        message: dict[str, Any],
    ) -> int:
        """Broadcast analytics update to all dashboard connections for a merchant.

        Uses Redis Pub/Sub so messages work across multiple server instances.

        Args:
            merchant_id: Merchant identifier
            message: Analytics update message payload

        Returns:
            Number of connections the message was sent to
        """
        # Check if there are any connections first
        conn_count = self.get_connection_count(merchant_id)

        self._logger.info(
            "dashboard_broadcast_start",
            merchant_id=merchant_id,
            message_type=message.get("type"),
            connection_count=conn_count,
        )

        if conn_count == 0:
            # No connected dashboards - skip broadcast
            return 0

        # Publish to Redis for delivery
        redis_client = self._get_redis()
        channel = f"dashboard:merchant:{merchant_id}"

        try:
            await redis_client.publish(channel, json.dumps(message))
            self._logger.info(
                "dashboard_redis_published",
                channel=channel,
                message_type=message.get("type"),
                connection_count=conn_count,
            )
        except Exception as e:
            self._logger.error(
                "dashboard_redis_publish_failed",
                channel=channel,
                error=str(e),
            )
            # Fallback: deliver locally if Redis fails
            return await self._deliver_locally(merchant_id, message)

        # Return connection count (actual delivery happens via Redis listener)
        return conn_count

    async def _deliver_locally(
        self,
        merchant_id: int,
        message: dict[str, Any],
    ) -> int:
        """Deliver message to local WebSocket connections.

        Args:
            merchant_id: Merchant identifier
            message: Analytics update message payload

        Returns:
            Number of connections message was sent to
        """
        async with self._lock:
            connections = list(self._connections.get(merchant_id, set()))

        if not connections:
            return 0

        sent_count = 0
        for websocket in connections:
            try:
                await self._send_to_websocket(websocket, message)
                sent_count += 1
            except Exception as e:
                self._logger.warning(
                    "dashboard_ws_send_failed",
                    merchant_id=merchant_id,
                    error=str(e),
                )

        self._logger.info(
            "dashboard_broadcast_complete",
            merchant_id=merchant_id,
            message_type=message.get("type"),
            connections=sent_count,
        )

        return sent_count

    async def _send_to_websocket(
        self,
        websocket: WebSocket,
        message: dict[str, Any],
    ) -> None:
        """Send a message to a WebSocket connection.

        Args:
            websocket: WebSocket connection
            message: Message payload
        """
        message_str = json.dumps(message)
        await websocket.send_text(message_str)

    async def _start_redis_listener(self, merchant_id: int) -> None:
        """Start listening to Redis channel for a merchant.

        Args:
            merchant_id: Merchant identifier
        """
        if merchant_id in self._listener_tasks:
            return

        redis_client = self._get_redis()
        pubsub = redis_client.pubsub()

        try:
            await pubsub.subscribe(f"dashboard:merchant:{merchant_id}")
            self._pubsub_instances[merchant_id] = pubsub

            # Start listener task
            task = asyncio.create_task(self._redis_listener(merchant_id, pubsub))
            self._listener_tasks[merchant_id] = task

            self._logger.debug(
                "dashboard_redis_listener_started",
                merchant_id=merchant_id,
            )
        except Exception as e:
            self._logger.error(
                "dashboard_redis_subscribe_failed",
                merchant_id=merchant_id,
                error=str(e),
            )

    async def _stop_redis_listener(self, merchant_id: int) -> None:
        """Stop Redis listener for a merchant.

        Args:
            merchant_id: Merchant identifier
        """
        # Cancel listener task
        if merchant_id in self._listener_tasks:
            task = self._listener_tasks.pop(merchant_id)
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        # Close pubsub
        if merchant_id in self._pubsub_instances:
            pubsub = self._pubsub_instances.pop(merchant_id)
            try:
                await pubsub.unsubscribe(f"dashboard:merchant:{merchant_id}")
                await pubsub.close()
            except Exception:
                pass

        self._logger.debug(
            "dashboard_redis_listener_stopped",
            merchant_id=merchant_id,
        )

    async def _redis_listener(
        self,
        merchant_id: int,
        pubsub: Any,
    ) -> None:
        """Listen to Redis channel and forward messages to WebSocket.

        Args:
            merchant_id: Merchant identifier
            pubsub: Redis pubsub instance
        """
        try:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    try:
                        data = json.loads(message["data"])
                        await self._deliver_locally(merchant_id, data)
                    except json.JSONDecodeError:
                        self._logger.warning(
                            "dashboard_redis_invalid_message",
                            merchant_id=merchant_id,
                        )
        except asyncio.CancelledError:
            raise
        except Exception as e:
            self._logger.error(
                "dashboard_redis_listener_error",
                merchant_id=merchant_id,
                error=str(e),
            )

    def get_connection_count(self, merchant_id: int) -> int:
        """Get the number of active dashboard connections for a merchant.

        Args:
            merchant_id: Merchant identifier

        Returns:
            Number of active connections
        """
        return len(self._connections.get(merchant_id, set()))

    async def shutdown(self) -> None:
        """Gracefully shutdown all connections and listeners."""
        self._logger.info("dashboard_connection_manager_shutdown")

        # Cancel all listener tasks
        for task in self._listener_tasks.values():
            task.cancel()

        # Close all pubsub instances
        for pubsub in self._pubsub_instances.values():
            try:
                await pubsub.close()
            except Exception:
                pass

        self._listener_tasks.clear()
        self._pubsub_instances.clear()
        self._connections.clear()


# Global dashboard connection manager instance
_manager_state = {"manager": None}


def get_dashboard_connection_manager() -> DashboardConnectionManager:
    """Get or create the global dashboard connection manager instance."""
    if _manager_state["manager"] is None:
        _manager_state["manager"] = DashboardConnectionManager()
    return _manager_state["manager"]
