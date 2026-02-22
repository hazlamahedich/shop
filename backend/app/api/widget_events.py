"""Widget Events API - SSE (Server-Sent Events) endpoint.

Provides real-time communication for widget clients to receive
merchant messages and other events.

Story: Merchant Reply Feature
"""

from __future__ import annotations

import asyncio
import json
from asyncio import Queue
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4

import structlog
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

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
        # Map of session_id -> list of queues (one per connection)
        self._connections: dict[str, list[Queue]] = {}
        self._lock = asyncio.Lock()
        self.logger = structlog.get_logger(__name__)

    async def connect(self, session_id: str) -> Queue:
        """Register a new SSE connection for a session.

        Args:
            session_id: Widget session identifier

        Returns:
            Queue for receiving messages
        """
        queue: Queue = Queue()

        async with self._lock:
            if session_id not in self._connections:
                self._connections[session_id] = []
            self._connections[session_id].append(queue)

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
                except ValueError:
                    pass

                # Clean up empty session entries
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
sse_manager: Optional[SSEConnectionManager] = None


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
    last_keepalive = datetime.now(timezone.utc)

    try:
        # Send initial connection confirmation
        yield _format_sse_event(
            "connected",
            {
                "sessionId": session_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
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
                yield _format_sse_event(event_type, message)

            except asyncio.TimeoutError:
                # Send keepalive comment
                now = datetime.now(timezone.utc)
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

    # Register this connection
    queue = await manager.connect(session_id)

    logger.info(
        "sse_connection_established",
        session_id=session_id,
        client_host=request.client.host if request.client else "unknown",
    )

    return StreamingResponse(
        _event_generator(session_id, queue, manager),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
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
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
