"""Dashboard WebSocket API endpoint.

Provides real-time analytics updates for dashboard connections.
Updates are pushed when underlying data changes (RAG queries, metrics, etc).

Story 10.7: Knowledge Effectiveness Widget - Real-time Updates
"""

from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime
from typing import Any

import structlog
from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect

from app.api.analytics import _get_merchant_id_from_request
from app.services.analytics.dashboard_websocket_manager import (
    get_dashboard_connection_manager,
)

logger = structlog.get_logger(__name__)

router = APIRouter()

# Heartbeat settings
HEARTBEAT_INTERVAL = 30  # seconds
HEARTBEAT_TIMEOUT = 45  # seconds


@router.websocket("/ws/dashboard/analytics")
async def dashboard_analytics_websocket(
    websocket: WebSocket,
) -> None:
    """WebSocket endpoint for real-time dashboard analytics updates.

    Provides real-time updates for:
    - Knowledge effectiveness metrics (Story 10.7)
    - Bot quality metrics
    - Response time distribution
    - FAQ usage
    - Top topics

    Protocol:
        Client -> Server:
            - "ping" - Heartbeat request
            - JSON message with "type" field

        Server -> Client:
            - "pong" - Heartbeat response
            - {"type": "connected", "data": {...}} - Connection confirmation
            - {"type": "analytics_update", "data": {...}} - Analytics update
            - {"type": "error", "data": {...}} - Error notification

    Message Types:
        - knowledge_effectiveness: Knowledge base effectiveness metrics
        - bot_quality: Bot quality metrics (CSAT, response time, etc.)
        - response_time: Response time distribution metrics
        - faq_usage: FAQ usage statistics
        - top_topics: Top queried topics
    """
    # Extract merchant_id from query params or headers
    merchant_id = None

    # Try query param first
    if hasattr(websocket, "query_params"):
        merchant_id_str = websocket.query_params.get("merchant_id")
        if merchant_id_str:
            try:
                merchant_id = int(merchant_id_str)
            except ValueError:
                pass

    # Fallback to headers
    if merchant_id is None:
        headers = dict(websocket.headers)
        merchant_id_str = headers.get("X-Merchant-Id") or headers.get("x-merchant-id")
        if merchant_id_str:
            try:
                merchant_id = int(merchant_id_str)
            except ValueError:
                pass

    # Default to merchant 1 in development
    if merchant_id is None:
        merchant_id = 1
        logger.warning(
            "dashboard_ws_no_merchant_id_using_default",
            default_merchant_id=merchant_id,
        )

    manager = get_dashboard_connection_manager()

    logger.info(
        "dashboard_ws_connection_attempt",
        merchant_id=merchant_id,
    )

    try:
        # Accept and register connection
        await manager.connect(merchant_id, websocket)

        logger.info(
            "dashboard_ws_connection_accepted",
            merchant_id=merchant_id,
            connection_count=manager.get_connection_count(merchant_id),
        )

        # Start heartbeat task
        heartbeat_task = asyncio.create_task(_heartbeat_loop(websocket, merchant_id))

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
                    await _handle_message(websocket, merchant_id, message)

                except TimeoutError:
                    # No message received within timeout - client may be dead
                    logger.warning(
                        "dashboard_ws_timeout",
                        merchant_id=merchant_id,
                    )
                    break

        except WebSocketDisconnect:
            logger.info(
                "dashboard_ws_disconnect",
                merchant_id=merchant_id,
            )
        except Exception as e:
            logger.error(
                "dashboard_ws_error",
                merchant_id=merchant_id,
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
        await manager.disconnect(merchant_id, websocket)


async def _handle_message(
    websocket: WebSocket,
    merchant_id: int,
    message: str,
) -> None:
    """Handle incoming WebSocket message.

    Args:
        websocket: WebSocket connection
        merchant_id: Merchant identifier
        message: Raw message string
    """
    # Handle plain text ping
    if message.strip().lower() == "ping":
        await websocket.send_text("pong")
        logger.debug(
            "dashboard_ws_pong",
            merchant_id=merchant_id,
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
                    "data": {"timestamp": datetime.now(UTC).isoformat()},
                }
            )
        )
    elif msg_type == "subscribe":
        # Subscribe to specific analytics types
        # For now, we subscribe to all by default
        await websocket.send_text(
            json.dumps(
                {
                    "type": "subscribed",
                    "data": {
                        "merchantId": merchant_id,
                        "types": ["all"],  # Subscribe to all analytics updates
                        "timestamp": datetime.now(UTC).isoformat(),
                    },
                }
            )
        )
    elif msg_type == "pong":
        # Response to our ping - ignore
        pass
    else:
        # Unknown message type
        logger.debug(
            "dashboard_ws_unknown_message",
            merchant_id=merchant_id,
            message_type=msg_type,
        )


async def _heartbeat_loop(websocket: WebSocket, merchant_id: int) -> None:
    """Send periodic heartbeat pings to keep connection alive.

    Args:
        websocket: WebSocket connection
        merchant_id: Merchant identifier
    """
    try:
        while True:
            await asyncio.sleep(HEARTBEAT_INTERVAL)

            try:
                await websocket.send_text(
                    json.dumps(
                        {
                            "type": "ping",
                            "data": {"timestamp": datetime.now(UTC).isoformat()},
                        }
                    )
                )
                logger.debug(
                    "dashboard_ws_heartbeat_sent",
                    merchant_id=merchant_id,
                )
            except Exception as e:
                logger.warning(
                    "dashboard_ws_heartbeat_failed",
                    merchant_id=merchant_id,
                    error=str(e),
                )
                break

    except asyncio.CancelledError:
        pass


@router.get(
    "/ws/dashboard/analytics/status",
    summary="Dashboard WebSocket Connection Status",
    description="Get the number of active WebSocket connections for a merchant",
    response_model=None,
)
async def dashboard_websocket_status(
    merchant_id: int,
    request: Request,
) -> dict[str, Any]:
    """Get dashboard WebSocket connection status for a merchant.

    Args:
        merchant_id: Merchant identifier
        request: FastAPI request

    Returns:
        Dict with connection count
    """
    from app.core.config import settings

    config = settings()
    is_test_mode = request.headers.get("X-Test-Mode", "").lower() == "true"
    is_debug = config.get("DEBUG", False)

    if not (is_debug or is_test_mode):
        pass

    manager = get_dashboard_connection_manager()

    return {
        "merchantId": merchant_id,
        "activeConnections": manager.get_connection_count(merchant_id),
        "timestamp": datetime.now(UTC).isoformat(),
    }


async def broadcast_knowledge_effectiveness_update(
    merchant_id: int,
    data: dict[str, Any],
) -> int:
    """Broadcast knowledge effectiveness update to connected dashboards.

    Helper function to be called after RAG query logs are updated.

    Args:
        merchant_id: Merchant identifier
        data: Knowledge effectiveness metrics

    Returns:
        Number of connections the update was sent to
    """
    manager = get_dashboard_connection_manager()

    message = {
        "type": "knowledge_effectiveness",
        "data": data,
    }

    return await manager.broadcast_to_merchant(merchant_id, message)
