import { getWidgetApiBase } from "./widgetClient-DgavxOUn.js";
function connectToWidgetSSE(sessionId, options = {}) {
  const {
    onMessage,
    onError,
    onOpen,
    onClose,
    reconnectInterval = 3e3,
    maxReconnectAttempts = 5
  } = options;
  let eventSource = null;
  let reconnectAttempts = 0;
  let isClosed = false;
  const connect = () => {
    if (isClosed) return;
    const url = `${getWidgetApiBase()}/${sessionId}/events`;
    console.warn("[SSE] Connecting to:", url);
    eventSource = new EventSource(url);
    eventSource.onopen = () => {
      console.warn("[SSE] Connection opened");
      reconnectAttempts = 0;
      onOpen == null ? void 0 : onOpen();
    };
    eventSource.onerror = (error) => {
      console.warn("[SSE] Connection error:", error);
      onError == null ? void 0 : onError(error);
      if (eventSource) {
        eventSource.close();
        eventSource = null;
      }
      if (reconnectAttempts < maxReconnectAttempts && !isClosed) {
        reconnectAttempts++;
        setTimeout(connect, reconnectInterval);
      } else {
        onClose == null ? void 0 : onClose();
      }
    };
    eventSource.addEventListener("connected", (event) => {
      try {
        const data = JSON.parse(event.data);
        onMessage == null ? void 0 : onMessage({ type: "connected", data });
      } catch {
      }
    });
    eventSource.addEventListener("merchant_message", (event) => {
      console.warn("[SSE] merchant_message event received:", event);
      try {
        const parsed = JSON.parse(event.data);
        console.warn("[SSE] Parsed data:", parsed);
        const innerData = parsed.data || parsed;
        console.warn("[SSE] Inner data:", innerData);
        onMessage == null ? void 0 : onMessage({ type: "merchant_message", data: innerData });
      } catch (e) {
        console.warn("[SSE] Parse error:", e);
      }
    });
    eventSource.onmessage = (event) => {
      try {
        const parsed = JSON.parse(event.data);
        const innerData = parsed.data || parsed;
        onMessage == null ? void 0 : onMessage({ type: "merchant_message", data: innerData });
      } catch {
      }
    };
  };
  connect();
  return () => {
    isClosed = true;
    if (eventSource) {
      eventSource.close();
      eventSource = null;
    }
    onClose == null ? void 0 : onClose();
  };
}
function isSSESupported() {
  return typeof EventSource !== "undefined";
}
export {
  connectToWidgetSSE,
  isSSESupported
};
