"""WebSocket Connection Manager for Widget.

Manages WebSocket connections with Redis Pub/Sub for scalable
message delivery across multiple server instances.

Design:
- Each widget opens one WebSocket connection
- Connection manager subscribes to Redis channel per session
- Messages are published to Redis and broadcast to all connections
- Supports 1,000+ concurrent connections per instance
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set
from weakref import WeakSet

import redis.asyncio as redis
import structlog
from fastapi import WebSocket, WebSocketDisconnect

from app.core.config import settings

logger = structlog.get_logger(__name__)


class WidgetConnectionManager:
    """Manages WebSocket connections for widget sessions.

    Uses Redis Pub/Sub for cross-instance message delivery.
    Each instance subscribes to session channels and forwards
    messages to connected WebSocket clients.

    Attributes:
        _connections: Map of session_id -> set of WebSocket connections
        _redis: Redis client for pub/sub
        _pubsub: Redis pubsub instance per session
        _tasks: Background tasks for listening to Redis channels
    """

    HEARTBEAT_INTERVAL = 30  # seconds
    HEARTBEAT_TIMEOUT = 45  # seconds (client should respond within this)

    def __init__(self, redis_client: Optional[redis.Redis] = None) -> None:
        """Initialize the connection manager.

        Args:
            redis_client: Optional Redis client (creates default if not provided)
        """
        self._connections: Dict[str, Set[WebSocket]] = {}
        self._redis: Optional[redis.Redis] = redis_client
        self._pubsub_instances: Dict[str, Any] = {}
        self._listener_tasks: Dict[str, asyncio.Task] = {}
        self._lock = asyncio.Lock()
        self._logger = structlog.get_logger(__name__)

    def _get_redis(self) -> redis.Redis:
        """Get or create Redis client."""
        if self._redis is None:
            config = settings()
            redis_url = config.get("REDIS_URL", "redis://localhost:6379/0")
            self._redis = redis.from_url(redis_url, decode_responses=True)
        return self._redis

    async def connect(self, session_id: str, websocket: WebSocket) -> None:
        """Accept and register a new WebSocket connection.

        Args:
            session_id: Widget session identifier
            websocket: WebSocket connection from FastAPI
        """
        try:
            await websocket.accept()
        except Exception as e:
            self._logger.error(
                "websocket_accept_failed",
                session_id=session_id,
                error=str(e),
                error_type=type(e).__name__,
            )
            return

        async with self._lock:
            if session_id not in self._connections:
                self._connections[session_id] = set()
                # Start Redis listener for this session
                await self._start_redis_listener(session_id)

            self._connections[session_id].add(websocket)
            conn_count = len(self._connections[session_id])

        self._logger.info(
            "websocket_connected",
            session_id=session_id,
            connection_count=conn_count,
            total_sessions=len(self._connections),
        )

        # Send connection confirmation
        try:
            await self._send_to_websocket(
                websocket,
                {
                    "type": "connected",
                    "data": {
                        "sessionId": session_id,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    },
                },
            )
        except Exception as e:
            self._logger.error(
                "websocket_send_confirmation_failed",
                session_id=session_id,
                error=str(e),
            )

    async def disconnect(self, session_id: str, websocket: WebSocket) -> None:
        """Remove a WebSocket connection.

        Args:
            session_id: Widget session identifier
            websocket: WebSocket connection to remove
        """
        async with self._lock:
            if session_id in self._connections:
                self._connections[session_id].discard(websocket)

                # Clean up if no more connections for this session
                if not self._connections[session_id]:
                    del self._connections[session_id]
                    await self._stop_redis_listener(session_id)

        self._logger.info(
            "websocket_disconnected",
            session_id=session_id,
        )

    async def broadcast_to_session(
        self,
        session_id: str,
        message: Dict[str, Any],
    ) -> int:
        """Broadcast a message to all connections for a session.

        Uses Redis Pub/Sub so messages work across multiple server instances.

        Args:
            session_id: Widget session identifier
            message: Message payload to broadcast

        Returns:
            Number of connections the message was sent to
        """
        # Check if there are any connections first
        conn_count = self.get_connection_count(session_id)

        self._logger.info(
            "broadcast_to_session_start",
            session_id=session_id,
            message_type=message.get("type"),
            connection_count=conn_count,
        )

        if conn_count == 0:
            self._logger.warning(
                "broadcast_to_session_no_connections",
                session_id=session_id,
                message_type=message.get("type"),
            )
            return 0

        # Publish to Redis for delivery (works for both local and cross-instance)
        redis_client = self._get_redis()
        channel = f"widget:{session_id}"

        try:
            await redis_client.publish(channel, json.dumps(message))
            self._logger.info(
                "redis_message_published",
                channel=channel,
                message_type=message.get("type"),
                connection_count=conn_count,
            )
        except Exception as e:
            self._logger.error(
                "redis_publish_failed",
                channel=channel,
                error=str(e),
                error_type=type(e).__name__,
            )
            # Fallback: deliver locally if Redis fails
            return await self._deliver_locally(session_id, message)

        # Return connection count (actual delivery happens via Redis listener)
        return conn_count

    async def _deliver_locally(
        self,
        session_id: str,
        message: Dict[str, Any],
    ) -> int:
        """Deliver message to local WebSocket connections.

        Args:
            session_id: Widget session identifier
            message: Message payload

        Returns:
            Number of connections message was sent to
        """
        # Log delivery attempt
        with open("/tmp/ws_connections.log", "a") as log_file:
            log_file.write(
                f"{datetime.now(timezone.utc).isoformat()} - deliver_locally_start - session_id={session_id}, message_type={message.get('type')}\n"
            )
            log_file.flush()

        async with self._lock:
            connections = list(self._connections.get(session_id, set()))

        if not connections:
            with open("/tmp/ws_connections.log", "a") as log_file:
                log_file.write(
                    f"{datetime.now(timezone.utc).isoformat()} - deliver_locally_no_connections - session_id={session_id}\n"
                )
                log_file.flush()
            return 0

        sent_count = 0
        for websocket in connections:
            try:
                await self._send_to_websocket(websocket, message)
                sent_count += 1
                with open("/tmp/ws_connections.log", "a") as log_file:
                    log_file.write(
                        f"{datetime.now(timezone.utc).isoformat()} - deliver_locally_sent - session_id={session_id}, sent_count={sent_count}\n"
                    )
                    log_file.flush()
            except Exception as e:
                self._logger.warning(
                    "websocket_send_failed",
                    session_id=session_id,
                    error=str(e),
                )
                with open("/tmp/ws_connections.log", "a") as log_file:
                    log_file.write(
                        f"{datetime.now(timezone.utc).isoformat()} - deliver_locally_failed - session_id={session_id}, error={str(e)}\n"
                    )
                    log_file.flush()

        self._logger.info(
            "websocket_broadcast",
            session_id=session_id,
            message_type=message.get("type"),
            connections=sent_count,
        )

        return sent_count

    async def _send_to_websocket(
        self,
        websocket: WebSocket,
        message: Dict[str, Any],
    ) -> None:
        """Send a message to a WebSocket connection.

        Args:
            websocket: WebSocket connection
            message: Message payload
        """
        message_str = json.dumps(message)

        # Log before send
        with open("/tmp/ws_connections.log", "a") as log_file:
            log_file.write(
                f"{datetime.now(timezone.utc).isoformat()} - send_to_ws_start - message_type={message.get('type')}, size={len(message_str)}\n"
            )
            log_file.flush()

        try:
            await websocket.send_text(message_str)

            # Log success
            with open("/tmp/ws_connections.log", "a") as log_file:
                log_file.write(
                    f"{datetime.now(timezone.utc).isoformat()} - send_to_ws_success - message_type={message.get('type')}\n"
                )
                log_file.flush()
        except Exception as e:
            # Log failure
            with open("/tmp/ws_connections.log", "a") as log_file:
                log_file.write(
                    f"{datetime.now(timezone.utc).isoformat()} - send_to_ws_failed - error={str(e)}, error_type={type(e).__name__}\n"
                )
                log_file.flush()
            raise

    async def _start_redis_listener(self, session_id: str) -> None:
        """Start listening to Redis channel for a session.

        Args:
            session_id: Widget session identifier
        """
        if session_id in self._listener_tasks:
            return

        redis_client = self._get_redis()
        pubsub = redis_client.pubsub()

        try:
            await pubsub.subscribe(f"widget:{session_id}")
            self._pubsub_instances[session_id] = pubsub

            # Start listener task
            task = asyncio.create_task(self._redis_listener(session_id, pubsub))
            self._listener_tasks[session_id] = task

            self._logger.debug(
                "redis_listener_started",
                session_id=session_id,
            )
        except Exception as e:
            self._logger.error(
                "redis_subscribe_failed",
                session_id=session_id,
                error=str(e),
            )

    async def _stop_redis_listener(self, session_id: str) -> None:
        """Stop Redis listener for a session.

        Args:
            session_id: Widget session identifier
        """
        # Cancel listener task
        if session_id in self._listener_tasks:
            task = self._listener_tasks.pop(session_id)
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        # Close pubsub
        if session_id in self._pubsub_instances:
            pubsub = self._pubsub_instances.pop(session_id)
            try:
                await pubsub.unsubscribe(f"widget:{session_id}")
                await pubsub.close()
            except Exception:
                pass

        self._logger.debug(
            "redis_listener_stopped",
            session_id=session_id,
        )

    async def _redis_listener(
        self,
        session_id: str,
        pubsub: Any,
    ) -> None:
        """Listen to Redis channel and forward messages to WebSocket.

        Args:
            session_id: Widget session identifier
            pubsub: Redis pubsub instance
        """
        try:
            with open("/tmp/ws_connections.log", "a") as log_file:
                log_file.write(
                    f"{datetime.now(timezone.utc).isoformat()} - redis_listener_started - session_id={session_id}\n"
                )
                log_file.flush()

            async for message in pubsub.listen():
                if message["type"] == "message":
                    try:
                        data = json.loads(message["data"])
                        with open("/tmp/ws_connections.log", "a") as log_file:
                            log_file.write(
                                f"{datetime.now(timezone.utc).isoformat()} - redis_listener_received - session_id={session_id}, message_type={data.get('type')}\n"
                            )
                            log_file.flush()
                        await self._deliver_locally(session_id, data)
                    except json.JSONDecodeError:
                        self._logger.warning(
                            "redis_invalid_message",
                            session_id=session_id,
                        )
        except asyncio.CancelledError:
            raise
        except Exception as e:
            self._logger.error(
                "redis_listener_error",
                session_id=session_id,
                error=str(e),
            )
            with open("/tmp/ws_connections.log", "a") as log_file:
                log_file.write(
                    f"{datetime.now(timezone.utc).isoformat()} - redis_listener_error - session_id={session_id}, error={str(e)}\n"
                )
                log_file.flush()

    def get_connection_count(self, session_id: str) -> int:
        """Get the number of active connections for a session.

        Args:
            session_id: Widget session identifier

        Returns:
            Number of active connections
        """
        count = len(self._connections.get(session_id, set()))
        self._logger.debug(
            "get_connection_count",
            session_id=session_id,
            connection_count=count,
            has_session=session_id in self._connections,
        )
        return count

    def get_all_active_sessions(self) -> Dict[str, int]:
        """Get all active sessions and their connection counts.

        Returns:
            Dict mapping session_id to connection count
        """
        return {
            session_id: len(connections) for session_id, connections in self._connections.items()
        }

    async def shutdown(self) -> None:
        """Gracefully shutdown all connections and listeners."""
        self._logger.info("connection_manager_shutdown")

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


# Global connection manager instance - use a module-level dict to ensure true singleton
_manager_state = {"manager": None}


def get_connection_manager() -> WidgetConnectionManager:
    """Get or create the global connection manager instance."""
    if _manager_state["manager"] is None:
        _manager_state["manager"] = WidgetConnectionManager()
    return _manager_state["manager"]
