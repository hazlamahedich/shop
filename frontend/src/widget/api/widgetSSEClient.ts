/**
 * Widget SSE (Server-Sent Events) Client
 *
 * Provides real-time connection to receive merchant messages
 * and other events in the widget.
 */

import { getWidgetApiBase } from './widgetClient';

export interface SSEMerchantMessage {
  id: number;
  content: string;
  sender: 'merchant';
  createdAt: string;
}

export interface SSEMessageEvent {
  type: 'merchant_message' | 'connected';
  data: SSEMerchantMessage | { sessionId: string; timestamp: string };
}

export type SSEEventHandler = (event: SSEMessageEvent) => void;
export type SSEErrorHandler = (error: Event) => void;

export interface SSEConnectionOptions {
  onMessage?: SSEEventHandler;
  onError?: SSEErrorHandler;
  onOpen?: () => void;
  onClose?: () => void;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
}

/**
 * Connect to the widget SSE endpoint
 *
 * @param sessionId - Widget session ID
 * @param options - Connection options including event handlers
 * @returns Cleanup function to close the connection
 */
export function connectToWidgetSSE(
  sessionId: string,
  options: SSEConnectionOptions = {}
): () => void {
  const {
    onMessage,
    onError,
    onOpen,
    onClose,
    reconnectInterval = 3000,
    maxReconnectAttempts = 5,
  } = options;

  let eventSource: EventSource | null = null;
  let reconnectAttempts = 0;
  let isClosed = false;

  const connect = () => {
    if (isClosed) return;

    // Use same origin detection as widgetClient to work on Shopify/cross-origin
    const url = `${getWidgetApiBase()}/${sessionId}/events`;
    console.warn('[SSE] Connecting to:', url);
    eventSource = new EventSource(url);

    eventSource.onopen = () => {
      console.warn('[SSE] Connection opened');
      reconnectAttempts = 0;
      onOpen?.();
    };

    eventSource.onerror = (error) => {
      console.warn('[SSE] Connection error:', error);
      onError?.(error);

      // Attempt to reconnect
      if (eventSource) {
        eventSource.close();
        eventSource = null;
      }

      if (reconnectAttempts < maxReconnectAttempts && !isClosed) {
        reconnectAttempts++;
        setTimeout(connect, reconnectInterval);
      } else {
        onClose?.();
      }
    };

    // Handle 'connected' event
    eventSource.addEventListener('connected', (event) => {
      try {
        const data = JSON.parse((event as MessageEvent).data);
        onMessage?.({ type: 'connected', data });
      } catch {
        // Ignore parse errors
      }
    });

    // Handle 'merchant_message' event
    eventSource.addEventListener('merchant_message', (event) => {
      console.warn('[SSE] merchant_message event FIRED:', event);
      try {
        const raw = (event as MessageEvent).data;
        console.warn('[SSE] Raw event data:', raw);
        const parsed = JSON.parse(raw);
        console.warn('[SSE] Parsed data:', parsed);
        // Unwrap the nested structure: {"type":"merchant_message","data":{...}}
        // WidgetContext expects event.data to be the inner data object
        const innerData = parsed.data || parsed;
        console.warn('[SSE] Inner data to pass:', innerData);
        onMessage?.({ type: 'merchant_message', data: innerData });
        console.warn('[SSE] onMessage callback called');
      } catch (e) {
        console.warn('[SSE] Parse error:', e);
      }
    });

    // Handle generic messages
    eventSource.onmessage = (event) => {
      try {
        const parsed = JSON.parse(event.data);
        // Unwrap nested structure if present
        const innerData = parsed.data || parsed;
        onMessage?.({ type: 'merchant_message', data: innerData });
      } catch {
        // Ignore parse errors
      }
    };
  };

  connect();

  // Return cleanup function
  return () => {
    isClosed = true;
    if (eventSource) {
      eventSource.close();
      eventSource = null;
    }
    onClose?.();
  };
}

/**
 * Check if SSE is supported in the current environment
 */
export function isSSESupported(): boolean {
  return typeof EventSource !== 'undefined';
}
