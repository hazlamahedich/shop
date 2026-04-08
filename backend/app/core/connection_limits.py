"""Connection limits for WebSocket and SSE endpoints.

Centralized configuration for maximum connections to prevent
resource exhaustion attacks (DDoS mitigation).
"""

from __future__ import annotations

MAX_CONNECTIONS_PER_WIDGET_SESSION = 5
MAX_CONNECTIONS_PER_DASHBOARD_MERCHANT = 10
MAX_SSE_CONNECTIONS_PER_SESSION = 5
MAX_TOTAL_WIDGET_CONNECTIONS = 5000
MAX_TOTAL_DASHBOARD_CONNECTIONS = 1000
MAX_TOTAL_SSE_CONNECTIONS = 5000

WS_MESSAGE_RATE_LIMIT = 60
WS_MESSAGE_RATE_PERIOD = 60
