"""Widget Events API - SSE (Server-Sent Events) endpoint.

Provides real-time communication for widget clients to receive
merchant messages and other events.

Story: Merchant Reply Feature
"""

from __future__ import annotations

import asyncio
import json
from asyncio import Queue
from datetime import UTC, datetime
from typing import Any

import structlog
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from app.core.connection_limits import MAX_SSE_CONNECTIONS_PER_SESSION, MAX_TOTAL_SSE_CONNECTIONS
from app.core.errors import APIError, ErrorCode
from app.core.validators import is_valid_session_id

logger = structlog.get_logger(__name__)

router = APIRouter()


class SSEConnectionManager:
    """Manages SSE connections for widget sessions.

    Allows broadcasting messages to all connections for a specific session.
    Uses in-memory storage with asyncio Queues for message delivery.
    """

    def __init__(self) -> None:
        """Initialize the SSE connection manager."""
        self._connections: dict[str, list[Queue]] = {}
        self._lock = asyncio.Lock()
        self.logger = structlog.get_logger(__name__)
        self._total_connections = 0

    async def connect(self, session_id: str) -> Queue | None:
        """Register a new SSE connection for a session.

        Args:
            session_id: Widget session identifier

        Returns:
            Queue for receiving messages, or None if connection limit exceeded
        """
        async with self._lock:
            if self._total_connections >= MAX_TOTAL_SSE_CONNECTIONS:
                self.logger.warning(
                    "sse_rejected_total_limit",
                    session_id=session_id,
                    total_connections=self._total_connections,
                    limit=MAX_TOTAL_SSE_CONNECTIONS,
                )
                return None

            session_conns = len(self._connections.get(session_id, []))
            if session_conns >= MAX_SSE_CONNECTIONS_PER_SESSION:
                self.logger.warning(
                    "sse_rejected_session_limit",
                    session_id=session_id,
                    session_connections=session_conns,
                    limit=MAX_SSE_CONNECTIONS_PER_SESSION,
                )
                return None

            queue: Queue = Queue()
            if session_id not in self._connections:
                self._connections[session_id] = []
            self._connections[session_id].append(queue)
            self._total_connections += 1

        self.logger.info(
            "sse_client_connected",
            session_id=session_id,
            connection_count=len(self._connections.get(session_id, [])),
        )

        return queue

    async def disconnect(self, session_id: str, queue: Queue) -> None:
        """Remove an SSE connection.

        Args:
            session_id: Widget session identifier
            queue: The queue to remove
        """
        async with self._lock:
            if session_id in self._connections:
                try:
                    self._connections[session_id].remove(queue)
                    self._total_connections = max(0, self._total_connections - 1)
                except ValueError:
                    pass

                if not self._connections[session_id]:
                    del self._connections[session_id]

        self.logger.info(
            "sse_client_disconnected",
            session_id=session_id,
        )

    async def broadcast_message(
        self,
        session_id: str,
        message: dict[str, Any],
    ) -> int:
        """Broadcast a message to all connections for a session.

        Args:
            session_id: Widget session identifier
            message: Message payload to broadcast

        Returns:
            Number of connections the message was sent to
        """
        async with self._lock:
            queues = self._connections.get(session_id, []).copy()

        if not queues:
            self.logger.debug(
                "sse_no_connections",
                session_id=session_id,
            )
            return 0

        sent_count = 0
        for queue in queues:
            try:
                await queue.put(message)
                sent_count += 1
            except Exception as e:
                self.logger.warning(
                    "sse_queue_put_failed",
                    session_id=session_id,
                    error=str(e),
                )

        self.logger.info(
            "sse_message_broadcast",
            session_id=session_id,
            message_type=message.get("type"),
            connections=sent_count,
        )

        return sent_count

    def get_connection_count(self, session_id: str) -> int:
        """Get the number of active connections for a session.

        Args:
            session_id: Widget session identifier

        Returns:
            Number of active connections
        """
        return len(self._connections.get(session_id, []))


# Global SSE manager instance
sse_manager: SSEConnectionManager | None = None


def get_sse_manager() -> SSEConnectionManager:
    """Get or create the global SSE manager instance."""
    global sse_manager
    if sse_manager is None:
        sse_manager = SSEConnectionManager()
    return sse_manager


# Initialize on module load
sse_manager = get_sse_manager()


def _format_sse_event(event: str, data: dict[str, Any]) -> str:
    """Format data as SSE event.

    Args:
        event: Event type/name
        data: Event data payload

    Returns:
        Formatted SSE string
    """
    data_json = json.dumps(data)
    return f"event: {event}\ndata: {data_json}\n\n"


async def _event_generator(
    session_id: str,
    queue: Queue,
    manager: SSEConnectionManager,
) -> Any:
    """Generate SSE events for a connection.

    Args:
        session_id: Widget session identifier
        queue: Message queue for this connection
        manager: SSE connection manager

    Yields:
        SSE formatted event strings
    """
    keepalive_interval = 15  # seconds
    last_keepalive = datetime.now(UTC)

    try:
        # Send initial connection confirmation
        logger.info(
            "sse_sending_connected_event",
            session_id=session_id,
        )
        yield _format_sse_event(
            "connected",
            {
                "sessionId": session_id,
                "timestamp": datetime.now(UTC).isoformat(),
            },
        )

        while True:
            try:
                # Check for messages with timeout for keepalive
                message = await asyncio.wait_for(
                    queue.get(),
                    timeout=keepalive_interval,
                )

                # Send the message
                event_type = message.get("type", "message")
                formatted_event = _format_sse_event(event_type, message)
                logger.info(
                    "sse_event_yielded",
                    session_id=session_id,
                    event_type=event_type,
                    message_preview=str(message)[:100],
                )
                yield formatted_event

            except TimeoutError:
                # Send keepalive comment
                now = datetime.now(UTC)
                yield f": keepalive {now.isoformat()}\n\n"
                last_keepalive = now

    except asyncio.CancelledError:
        logger.info(
            "sse_stream_cancelled",
            session_id=session_id,
        )
        raise
    except Exception as e:
        logger.error(
            "sse_stream_error",
            session_id=session_id,
            error=str(e),
        )
        raise
    finally:
        await manager.disconnect(session_id, queue)


@router.get(
    "/widget/{session_id}/events",
    summary="Widget SSE Events",
    description="Server-Sent Events endpoint for real-time widget updates",
)
async def widget_events(
    request: Request,
    session_id: str,
) -> StreamingResponse:
    """SSE endpoint for widget to receive real-time events.

    Provides a persistent connection for receiving:
    - Merchant messages
    - Cart updates
    - System notifications

    Args:
        request: FastAPI request
        session_id: Widget session identifier

    Returns:
        StreamingResponse with SSE events

    Raises:
        APIError: If session ID format is invalid
    """
    # Validate session ID format
    if not is_valid_session_id(session_id):
        raise APIError(
            ErrorCode.VALIDATION_ERROR,
            "Invalid session ID format",
        )

    manager = get_sse_manager()

    queue = await manager.connect(session_id)

    if queue is None:
        raise APIError(
            ErrorCode.WIDGET_RATE_LIMITED,
            "Too many connections for this session",
            details={"retry_after": 60},
        )

    logger.info(
        "sse_connection_established",
        session_id=session_id,
        client_host=request.client.host if request.client else "unknown",
    )

    return StreamingResponse(
        _event_generator(session_id, queue, manager),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-store, no-transform, must-revalidate, max-age=0",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "X-Content-Type-Options": "nosniff",
            "Pragma": "no-cache",
            "Expires": "0",
        },
    )


@router.get(
    "/widget/{session_id}/events/status",
    summary="SSE Connection Status",
    description="Get the number of active SSE connections for a session",
)
async def sse_status(
    request: Request,
    session_id: str,
) -> dict[str, Any]:
    """Get SSE connection status for a session.

    Args:
        request: FastAPI request
        session_id: Widget session identifier

    Returns:
        Dict with connection count
    """
    manager = get_sse_manager()

    return {
        "sessionId": session_id,
        "activeConnections": manager.get_connection_count(session_id),
        "timestamp": datetime.now(UTC).isoformat(),
    }
