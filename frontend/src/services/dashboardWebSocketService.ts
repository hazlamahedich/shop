/**
 * Dashboard WebSocket Service
 *
 * Provides real-time analytics updates for dashboard widgets.
 * Subscribes to analytics updates and pushes data to React Query cache.
 *
 * Story 10.7: Knowledge Effectiveness Widget - Real-time Updates
 */

import { getApiBase } from './api';
import { QueryClient } from '@tanstack/react-query';

export type DashboardMessageType =
  | 'connected'
  | 'knowledge_effectiveness'
  | 'bot_quality'
  | 'response_time'
  | 'faq_usage'
  | 'top_topics'
  | 'error'
  | 'ping'
  | 'pong'
  | 'subscribed';

export interface DashboardMessage<T = unknown> {
  type: DashboardMessageType;
  data: T;
}

export interface ConnectedData {
  merchantId: number;
  timestamp: string;
}

export interface KnowledgeEffectivenessData {
  totalQueries: number;
  successfulMatches: number;
  noMatchRate: number;
  avgConfidence: number | null;
  trend: number[];
  lastUpdated: string;
}

export class DashboardWebSocketService {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000; // Start with 1 second
  private maxReconnectDelay = 30000; // Max 30 seconds
  private merchantId: number;
  private queryClient: QueryClient | null = null;
  private reconnectTimeout: ReturnType<typeof setTimeout> | null = null;
  private heartbeatInterval: ReturnType<typeof setInterval> | null = null;

  constructor(merchantId: number) {
    this.merchantId = merchantId;
  }

  connect(queryClient: QueryClient): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      console.log('[DashboardWS] Already connected');
      return;
    }

    this.queryClient = queryClient;

    const apiBase = getApiBase();
    const wsProtocol = apiBase.includes('https') ? 'wss:' : 'ws:';
    const wsHost = apiBase ? apiBase.replace(/^https?:/, wsProtocol) : `${wsProtocol}//${window.location.host}`;

    const wsUrl = `${wsHost}/api/v1/ws/dashboard/analytics?merchant_id=${this.merchantId}`;

    console.log('[DashboardWS] Connecting to:', wsUrl);

    try {
      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = () => {
        console.log('[DashboardWS] Connected');
        this.reconnectAttempts = 0;
        this.reconnectDelay = 1000;

        // Start heartbeat
        this.startHeartbeat();

        // Update connection status in cache
        this.updateConnectionStatus(true);
      };

      this.ws.onmessage = (event) => {
        this.handleMessage(event.data);
      };

      this.ws.onclose = (event) => {
        console.log('[DashboardWS] Disconnected:', event.code, event.reason);
        this.updateConnectionStatus(false);
        this.stopHeartbeat();

        // Attempt to reconnect
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
          this.scheduleReconnect();
        }
      };

      this.ws.onerror = (error) => {
        console.error('[DashboardWS] Error:', error);
      };
    } catch (error) {
      console.error('[DashboardWS] Failed to connect:', error);
      this.scheduleReconnect();
    }
  }

  disconnect(): void {
    console.log('[DashboardWS] Disconnecting');

    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }

    this.stopHeartbeat();

    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }

    this.updateConnectionStatus(false);
  }

  private scheduleReconnect(): void {
    if (this.reconnectTimeout) {
      return; // Already scheduled
    }

    this.reconnectAttempts++;
    const delay = Math.min(
      this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1),
      this.maxReconnectDelay
    );

    console.log(
      `[DashboardWS] Scheduling reconnect in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`
    );

    this.reconnectTimeout = setTimeout(() => {
      this.reconnectTimeout = null;
      this.connect(this.queryClient!);
    }, delay);
  }

  private startHeartbeat(): void {
    // Send ping every 30 seconds to keep connection alive
    this.heartbeatInterval = setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({ type: 'ping' }));
      }
    }, 30000);
  }

  private stopHeartbeat(): void {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }

  private handleMessage(data: string): void {
    try {
      const message = JSON.parse(data) as DashboardMessage;

      switch (message.type) {
        case 'connected':
          console.log('[DashboardWS] Connection confirmed:', message.data);
          break;

        case 'knowledge_effectiveness':
          console.log('[DashboardWS] Knowledge effectiveness update:', message.data);
          this.updateKnowledgeEffectiveness(message.data as KnowledgeEffectivenessData);
          break;

        case 'pong':
          // Heartbeat response - ignore
          break;

        case 'error':
          console.error('[DashboardWS] Server error:', message.data);
          break;

        default:
          console.log('[DashboardWS] Unknown message type:', message.type);
      }
    } catch (error) {
      console.error('[DashboardWS] Failed to parse message:', error, data);
    }
  }

  private updateKnowledgeEffectiveness(data: KnowledgeEffectivenessData): void {
    if (!this.queryClient) return;

    // Update React Query cache with fresh data
    this.queryClient.setQueryData(
      ['analytics', 'knowledge-effectiveness'],
      { data }
    );

    console.log('[DashboardWS] Updated knowledge effectiveness cache:', data);
  }

  private updateConnectionStatus(connected: boolean): void {
    if (!this.queryClient) return;

    // Store connection status in a special query key
    this.queryClient.setQueryData(
      ['dashboard', 'websocket', 'status'],
      {
        connected,
        merchantId: this.merchantId,
        timestamp: new Date().toISOString(),
      }
    );
  }

  getConnectionStatus(): { connected: boolean; timestamp: string | null } {
    if (!this.queryClient) {
      return { connected: false, timestamp: null };
    }

    const status = this.queryClient.getQueryData([
      'dashboard',
      'websocket',
      'status',
    ]) as { connected: boolean; timestamp: string } | undefined;

    return {
      connected: status?.connected ?? false,
      timestamp: status?.timestamp ?? null,
    };
  }
}

// Singleton instance
let wsService: DashboardWebSocketService | null = null;

export function getDashboardWebSocketService(merchantId: number): DashboardWebSocketService {
  if (!wsService || wsService['merchantId'] !== merchantId) {
    wsService = new DashboardWebSocketService(merchantId);
  }
  return wsService;
}

export function closeDashboardWebSocket(): void {
  if (wsService) {
    wsService.disconnect();
    wsService = null;
  }
}
