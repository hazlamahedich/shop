import { getWidgetApiBase } from "./widgetClient-DgavxOUn.js";
function getWsBaseUrl() {
  const apiBase = getWidgetApiBase();
  return apiBase.replace(/^http/, "ws");
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
      try {
        if (event.data === "pong") {
          console.warn("[WS] Heartbeat pong received");
          return;
        }
        const parsed = JSON.parse(event.data);
        console.warn("[WS] Message received:", parsed);
        if (parsed.type === "ping") {
          if ((ws == null ? void 0 : ws.readyState) === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: "pong" }));
          }
          return;
        }
        if (parsed.type === "pong") {
          return;
        }
        onMessage == null ? void 0 : onMessage(parsed);
      } catch (e) {
        console.warn("[WS] Failed to parse message:", e);
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
