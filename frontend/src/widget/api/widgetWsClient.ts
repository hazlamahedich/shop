/**
 * Widget WebSocket Client
 *
 * Provides real-time bidirectional communication with the backend
 * using WebSocket protocol. Works through Cloudflare tunnels (unlike SSE).
 *
 * Features:
 * - Auto-reconnect on disconnect
 * - Heartbeat to detect dead connections
 * - Connection status tracking
 */

import { getWidgetApiBase } from './widgetClient';

export type ConnectionStatus = 'connecting' | 'connected' | 'disconnected' | 'error';

export interface WSMerchantMessage {
  id: number;
  content: string;
  sender: 'merchant' | 'bot';
  createdAt: string;
}

export interface WSMessageEvent {
  type: 'merchant_message' | 'handoff_resolved' | 'connected' | 'ping' | 'pong' | 'error';
  data: WSMerchantMessage | Record<string, unknown> | string;
}

export type WSMessageHandler = (event: WSMessageEvent) => void;
export type WSStatusHandler = (status: ConnectionStatus) => void;
export type WSErrorHandler = (error: Event) => void;

export interface WSConnectionOptions {
  onMessage?: WSMessageHandler;
  onStatusChange?: WSStatusHandler;
  onError?: WSErrorHandler;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
}

/**
 * Get WebSocket base URL from HTTP API base URL
 */
function getWsBaseUrl(): string {
  const apiBase = getWidgetApiBase();
  // API base is like "https://xxx/api/v1/widget"
  // WebSocket base should be just the origin: "wss://xxx"
  // Because the WebSocket endpoint is at /ws/widget/{sessionId}
  try {
    const url = new URL(apiBase);
    return url.origin.replace(/^http/, 'ws');
  } catch {
    // Fallback - replace http with ws and remove /api/v1/widget path
    return apiBase.replace(/^http/, 'ws').replace(/\/api\/v1\/widget$/, '');
  }
}

/**
 * Connect to the widget WebSocket endpoint
 *
 * @param sessionId - Widget session ID
 * @param options - Connection options including event handlers
 * @returns Cleanup function to close the connection
 */
export function connectWidgetWebSocket(
  sessionId: string,
  options: WSConnectionOptions = {}
): () => void {
  const {
    onMessage,
    onStatusChange,
    onError,
    reconnectInterval = 3000,
    maxReconnectAttempts = 10,
  } = options;

  let ws: WebSocket | null = null;
  let reconnectAttempts = 0;
  let isClosed = false;
  let heartbeatTimer: ReturnType<typeof setInterval> | null = null;
  let reconnectTimer: ReturnType<typeof setTimeout> | null = null;

  const updateStatus = (status: ConnectionStatus) => {
    console.warn('[WS] Status:', status);
    onStatusChange?.(status);
  };

  const clearTimers = () => {
    if (heartbeatTimer) {
      clearInterval(heartbeatTimer);
      heartbeatTimer = null;
    }
    if (reconnectTimer) {
      clearTimeout(reconnectTimer);
      reconnectTimer = null;
    }
  };

  const startHeartbeat = () => {
    // Send ping every 25 seconds (server expects activity within 45 seconds)
    heartbeatTimer = setInterval(() => {
      if (ws?.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'ping' }));
        console.warn('[WS] Heartbeat ping sent');
      }
    }, 25000);
  };

  const connect = () => {
    if (isClosed) return;

    console.warn('[WS] ========== WIDGET WS CLIENT v20260308-12-00 ==========');
    
    const wsBaseUrl = getWsBaseUrl();
    const url = `${wsBaseUrl}/ws/widget/${sessionId}`;

    console.warn('[WS] Connecting to:', url);
    updateStatus('connecting');

    try {
      ws = new WebSocket(url);
    } catch (error) {
      console.warn('[WS] Failed to create WebSocket:', error);
      updateStatus('error');
      scheduleReconnect();
      return;
    }

    ws.onopen = () => {
      console.warn('[WS] Connection opened');
      reconnectAttempts = 0;
      updateStatus('connected');
      startHeartbeat();
    };

    ws.onmessage = (event) => {
      console.warn('[WS] onmessage triggered, data type:', typeof event.data);
      try {
        // Handle plain text pong
        if (event.data === 'pong') {
          console.warn('[WS] Heartbeat pong received');
          return;
        }

        console.warn('[WS] Parsing JSON...');
        const parsed = JSON.parse(event.data);
        console.warn('[WS] Message received:', parsed);
        console.warn('[WS] Message type:', parsed.type);

        // Handle different message types
        if (parsed.type === 'ping') {
          console.warn('[WS] Handling ping, responding with pong');
          // Respond to server ping
          if (ws?.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: 'pong' }));
          }
          return;
        }

        if (parsed.type === 'pong') {
          console.warn('[WS] Handling pong, ignoring');
          // Response to our ping - ignore
          return;
        }

        console.warn('[WS] Not ping/pong, checking onMessage callback...');
        console.warn('[WS] onMessage exists:', !!onMessage);
        console.warn('[WS] onMessage type:', typeof onMessage);
        
        // Pass to message handler
        if (onMessage) {
          console.warn('[WS] Calling onMessage with:', parsed);
          try {
            onMessage(parsed);
            console.warn('[WS] onMessage call completed successfully');
          } catch (callbackError) {
            console.error('[WS] Error in onMessage callback:', callbackError);
          }
        } else {
          console.warn('[WS] ⚠️ onMessage callback is undefined!');
          console.warn('[WS] Available callbacks:', {
            onMessage: typeof onMessage,
            onStatusChange: typeof onStatusChange,
            onError: typeof onError
          });
        }
      } catch (e) {
        console.error('[WS] Failed to process message:', e);
        console.error('[WS] Error stack:', (e as Error).stack);
      }
    };

    ws.onerror = (error) => {
      console.warn('[WS] Error:', error);
      updateStatus('error');
      onError?.(error);
    };

    ws.onclose = (event) => {
      console.warn('[WS] Closed:', event.code, event.reason);
      clearTimers();
      
      if (!isClosed) {
        updateStatus('disconnected');
        scheduleReconnect();
      }
    };
  };

  const scheduleReconnect = () => {
    if (isClosed) return;

    if (reconnectAttempts < maxReconnectAttempts) {
      reconnectAttempts++;
      console.warn(`[WS] Reconnecting in ${reconnectInterval}ms (attempt ${reconnectAttempts}/${maxReconnectAttempts})`);
      
      reconnectTimer = setTimeout(() => {
        connect();
      }, reconnectInterval);
    } else {
      console.warn('[WS] Max reconnect attempts reached');
      updateStatus('error');
    }
  };

  // Start connection
  connect();

  // Return cleanup function
  return () => {
    console.warn('[WS] Cleanup - closing connection');
    isClosed = true;
    clearTimers();
    
    if (ws) {
      ws.close(1000, 'Client disconnect');
      ws = null;
    }
    
    updateStatus('disconnected');
  };
}

/**
 * Check if WebSocket is supported in the current environment
 */
export function isWebSocketSupported(): boolean {
  return typeof WebSocket !== 'undefined';
}
