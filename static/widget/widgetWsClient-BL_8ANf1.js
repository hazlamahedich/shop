import { g as getWidgetApiBase } from "./loader-DqT2y91v.js";
function getWsBaseUrl() {
  const apiBase = getWidgetApiBase();
  try {
    const url = new URL(apiBase);
    return url.origin.replace(/^http/, "ws");
  } catch {
    return apiBase.replace(/^http/, "ws").replace(/\/api\/v1\/widget$/, "");
  }
}
function connectWidgetWebSocket(sessionId, options = {}) {
  const {
    onMessage,
    onStatusChange,
    onError,
    reconnectInterval = 3e3,
    maxReconnectAttempts = 10
  } = options;
  let ws = null;
  let reconnectAttempts = 0;
  let isClosed = false;
  let heartbeatTimer = null;
  let reconnectTimer = null;
  const updateStatus = (status) => {
    console.warn("[WS] Status:", status);
    onStatusChange == null ? void 0 : onStatusChange(status);
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
    heartbeatTimer = setInterval(() => {
      if ((ws == null ? void 0 : ws.readyState) === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: "ping" }));
        console.warn("[WS] Heartbeat ping sent");
      }
    }, 25e3);
  };
  const connect = () => {
    if (isClosed) return;
    console.warn("[WS] ========== WIDGET WS CLIENT v20260308-12-00 ==========");
    const wsBaseUrl = getWsBaseUrl();
    const url = `${wsBaseUrl}/ws/widget/${sessionId}`;
    console.warn("[WS] Connecting to:", url);
    updateStatus("connecting");
    try {
      ws = new WebSocket(url);
    } catch (error) {
      console.warn("[WS] Failed to create WebSocket:", error);
      updateStatus("error");
      scheduleReconnect();
      return;
    }
    ws.onopen = () => {
      console.warn("[WS] Connection opened");
      reconnectAttempts = 0;
      updateStatus("connected");
      startHeartbeat();
    };
    ws.onmessage = (event) => {
      console.warn("[WS] onmessage triggered, data type:", typeof event.data);
      try {
        if (event.data === "pong") {
          console.warn("[WS] Heartbeat pong received");
          return;
        }
        console.warn("[WS] Parsing JSON...");
        const parsed = JSON.parse(event.data);
        console.warn("[WS] Message received:", parsed);
        console.warn("[WS] Message type:", parsed.type);
        if (parsed.type === "ping") {
          console.warn("[WS] Handling ping, responding with pong");
          if ((ws == null ? void 0 : ws.readyState) === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: "pong" }));
          }
          return;
        }
        if (parsed.type === "pong") {
          console.warn("[WS] Handling pong, ignoring");
          return;
        }
        console.warn("[WS] Not ping/pong, checking onMessage callback...");
        console.warn("[WS] onMessage exists:", !!onMessage);
        console.warn("[WS] onMessage type:", typeof onMessage);
        if (onMessage) {
          console.warn("[WS] Calling onMessage with:", parsed);
          try {
            onMessage(parsed);
            console.warn("[WS] onMessage call completed successfully");
          } catch (callbackError) {
            console.error("[WS] Error in onMessage callback:", callbackError);
          }
        } else {
          console.warn("[WS] ⚠️ onMessage callback is undefined!");
          console.warn("[WS] Available callbacks:", {
            onMessage: typeof onMessage,
            onStatusChange: typeof onStatusChange,
            onError: typeof onError
          });
        }
      } catch (e) {
        console.error("[WS] Failed to process message:", e);
        console.error("[WS] Error stack:", e.stack);
      }
    };
    ws.onerror = (error) => {
      console.warn("[WS] Error:", error);
      updateStatus("error");
      onError == null ? void 0 : onError(error);
    };
    ws.onclose = (event) => {
      console.warn("[WS] Closed:", event.code, event.reason);
      clearTimers();
      if (!isClosed) {
        updateStatus("disconnected");
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
      console.warn("[WS] Max reconnect attempts reached");
      updateStatus("error");
    }
  };
  connect();
  return () => {
    console.warn("[WS] Cleanup - closing connection");
    isClosed = true;
    clearTimers();
    if (ws) {
      ws.close(1e3, "Client disconnect");
      ws = null;
    }
    updateStatus("disconnected");
  };
}
function isWebSocketSupported() {
  return typeof WebSocket !== "undefined";
}
export {
  connectWidgetWebSocket,
  isWebSocketSupported
};
