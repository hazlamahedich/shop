"""Widget WebSocket API endpoint.

Provides real-time bidirectional communication for widget clients
using WebSocket protocol. Works through Cloudflare tunnels (unlike SSE).

Story: Merchant Reply Feature - WebSocket Implementation
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from typing import Any

import structlog
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.validators import is_valid_session_id
from app.services.widget.connection_manager import get_connection_manager

logger = structlog.get_logger(__name__)

router = APIRouter()

# Heartbeat settings
HEARTBEAT_INTERVAL = 30  # seconds
HEARTBEAT_TIMEOUT = 45  # seconds


@router.websocket("/ws/widget/{session_id}")
async def widget_websocket(
    websocket: WebSocket,
    session_id: str,
) -> None:
    """WebSocket endpoint for real-time widget communication.

    Provides bidirectional communication for:
    - Merchant messages (server -> client)
    - Heartbeat/ping-pong (both directions)
    - Connection status updates

    Args:
        websocket: WebSocket connection from FastAPI
        session_id: Widget session identifier

    Protocol:
        Client -> Server:
            - "ping" - Heartbeat request
            - JSON message with "type" field

        Server -> Client:
            - "pong" - Heartbeat response
            - {"type": "connected", "data": {...}} - Connection confirmation
            - {"type": "merchant_message", "data": {...}} - Merchant reply
            - {"type": "error", "data": {...}} - Error notification
    """
    # Validate session ID format
    if not is_valid_session_id(session_id):
        await websocket.close(code=4000, reason="Invalid session ID format")
        return

    manager = get_connection_manager()

    try:
        # Accept and register connection
        await manager.connect(session_id, websocket)

        # Start heartbeat task
        heartbeat_task = asyncio.create_task(_heartbeat_loop(websocket, session_id))

        try:
            # Main message loop
            while True:
                try:
                    # Wait for message with timeout for heartbeat
                    message = await asyncio.wait_for(
                        websocket.receive_text(),
                        timeout=HEARTBEAT_TIMEOUT,
                    )

                    # Handle message
                    await _handle_message(websocket, session_id, message, manager)

                except asyncio.TimeoutError:
                    # No message received within timeout - client may be dead
                    logger.warning(
                        "websocket_timeout",
                        session_id=session_id,
                    )
                    break

        except WebSocketDisconnect:
            logger.info(
                "websocket_disconnect",
                session_id=session_id,
            )
        except Exception as e:
            logger.error(
                "websocket_error",
                session_id=session_id,
                error=str(e),
            )
        finally:
            # Cancel heartbeat task
            heartbeat_task.cancel()
            try:
                await heartbeat_task
            except asyncio.CancelledError:
                pass

    finally:
        # Unregister connection
        await manager.disconnect(session_id, websocket)


async def _handle_message(
    websocket: WebSocket,
    session_id: str,
    message: str,
    manager: Any,
) -> None:
    """Handle incoming WebSocket message.

    Args:
        websocket: WebSocket connection
        session_id: Widget session identifier
        message: Raw message string
        manager: Connection manager instance
    """
    # Handle plain text ping
    if message.strip().lower() == "ping":
        await websocket.send_text("pong")
        logger.debug(
            "websocket_pong",
            session_id=session_id,
        )
        return

    # Try to parse as JSON
    try:
        data = json.loads(message)
    except json.JSONDecodeError:
        # Send error response
        await websocket.send_text(
            json.dumps(
                {
                    "type": "error",
                    "data": {
                        "code": "invalid_json",
                        "message": "Message must be valid JSON or 'ping'",
                    },
                }
            )
        )
        return

    # Handle typed messages
    msg_type = data.get("type")

    if msg_type == "ping":
        # JSON ping
        await websocket.send_text(
            json.dumps(
                {
                    "type": "pong",
                    "data": {"timestamp": datetime.now(timezone.utc).isoformat()},
                }
            )
        )
    elif msg_type == "pong":
        # Response to our ping - ignore
        pass
    else:
        # Unknown message type
        logger.debug(
            "websocket_unknown_message",
            session_id=session_id,
            message_type=msg_type,
        )


async def _heartbeat_loop(websocket: WebSocket, session_id: str) -> None:
    """Send periodic heartbeat pings to keep connection alive.

    Args:
        websocket: WebSocket connection
        session_id: Widget session identifier
    """
    try:
        while True:
            await asyncio.sleep(HEARTBEAT_INTERVAL)

            try:
                await websocket.send_text(
                    json.dumps(
                        {
                            "type": "ping",
                            "data": {"timestamp": datetime.now(timezone.utc).isoformat()},
                        }
                    )
                )
                logger.debug(
                    "websocket_heartbeat_sent",
                    session_id=session_id,
                )
            except Exception as e:
                logger.warning(
                    "websocket_heartbeat_failed",
                    session_id=session_id,
                    error=str(e),
                )
                break

    except asyncio.CancelledError:
        pass


@router.get(
    "/ws/widget/{session_id}/status",
    summary="WebSocket Connection Status",
    description="Get the number of active WebSocket connections for a session",
)
async def websocket_status(session_id: str) -> dict[str, Any]:
    """Get WebSocket connection status for a session.

    Args:
        session_id: Widget session identifier

    Returns:
        Dict with connection count
    """
    manager = get_connection_manager()

    return {
        "sessionId": session_id,
        "activeConnections": manager.get_connection_count(session_id),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
