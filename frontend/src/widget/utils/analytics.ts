/**
 * Widget Analytics Utility
 *
 * Story 9-10: Analytics & Performance Monitoring
 *
 * Handles event tracking, batching, and flushing for widget analytics.
 * Events are stored in sessionStorage and flushed on visibility change/pagehide.
 */

export type WidgetEventType =
  | 'widget_open'
  | 'message_send'
  | 'quick_reply_click'
  | 'voice_input'
  | 'proactive_trigger'
  | 'carousel_engagement';

export interface WidgetAnalyticsEvent {
  type: WidgetEventType;
  timestamp: string;
  session_id: string;
  metadata?: Record<string, unknown>;
}

export interface WidgetAnalyticsConfig {
  merchantId: number;
  sessionId: string;
  batchSize?: number;
  flushInterval?: number;
}

const STORAGE_KEY = 'widget_analytics_queue';
const DEFAULT_BATCH_SIZE = 10;
const DEFAULT_FLUSH_INTERVAL = 30000; // 30 seconds

class WidgetAnalyticsImpl {
  private merchantId: number | null = null;
  private sessionId: string | null = null;
  private batchSize: number = DEFAULT_BATCH_SIZE;
  private flushInterval: number = DEFAULT_FLUSH_INTERVAL;
  private flushTimer: ReturnType<typeof setTimeout> | null = null;
  private _isInitialized: boolean = false;
  private reducedMotion: boolean = false;

  constructor() {
    this.checkReducedMotion();
  }

  private checkReducedMotion(): void {
    if (typeof window !== 'undefined' && window.matchMedia) {
      const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
      this.reducedMotion = mediaQuery.matches;

      mediaQuery.addEventListener('change', (e) => {
        this.reducedMotion = e.matches;
      });
    }
  }

  get isInitialized(): boolean {
    return this._isInitialized;
  }

  initialize(config: WidgetAnalyticsConfig): void {
    if (this._isInitialized) {
      return;
    }

    this.merchantId = config.merchantId;
    this.sessionId = config.sessionId;
    this.batchSize = config.batchSize ?? DEFAULT_BATCH_SIZE;
    this.flushInterval = config.flushInterval ?? DEFAULT_FLUSH_INTERVAL;
    this._isInitialized = true;

    this.setupFlushListeners();
    this.startFlushTimer();
  }

  private setupFlushListeners(): void {
    if (typeof document === 'undefined') {
      return;
    }

    document.addEventListener('visibilitychange', () => {
      if (document.visibilityState === 'hidden') {
        this.flush();
      }
    });

    window.addEventListener('pagehide', () => {
      this.flush();
    });
  }

  private startFlushTimer(): void {
    if (this.flushTimer) {
      clearTimeout(this.flushTimer);
    }

    this.flushTimer = setTimeout(() => {
      this.flush();
      this.startFlushTimer();
    }, this.flushInterval);
  }

  track(type: WidgetEventType, metadata?: Record<string, unknown>): void {
    if (!this._isInitialized || !this.sessionId) {
      console.warn('[WidgetAnalytics] Not initialized or missing sessionId');
      return;
    }

    const event: WidgetAnalyticsEvent = {
      type,
      timestamp: new Date().toISOString(),
      session_id: this.sessionId,
      metadata: {
        ...metadata,
        reducedMotion: this.reducedMotion,
      },
    };

    const queue = this.getQueue();
    queue.push(event);

    if (queue.length >= this.batchSize) {
      this.flush();
    } else {
      this.saveQueue(queue);
    }
  }

  getQueuedEvents(): WidgetAnalyticsEvent[] {
    return this.getQueue();
  }

  private getQueue(): WidgetAnalyticsEvent[] {
    if (typeof sessionStorage === 'undefined') {
      return [];
    }

    try {
      const stored = sessionStorage.getItem(STORAGE_KEY);
      if (stored) {
        return JSON.parse(stored) as WidgetAnalyticsEvent[];
      }
    } catch {
      // Ignore parse errors
    }

    return [];
  }

  private saveQueue(queue: WidgetAnalyticsEvent[]): void {
    if (typeof sessionStorage === 'undefined') {
      return;
    }

    try {
      sessionStorage.setItem(STORAGE_KEY, JSON.stringify(queue));
    } catch {
      // Storage full or unavailable
    }
  }

  private clearQueue(): void {
    if (typeof sessionStorage === 'undefined') {
      return;
    }

    try {
      sessionStorage.removeItem(STORAGE_KEY);
    } catch {
      // Ignore errors
    }
  }

  async flush(): Promise<number> {
    const queue = this.getQueue();

    if (queue.length === 0) {
      return 0;
    }

    this.clearQueue();

    try {
      const { flushWidgetAnalyticsEvents } = await import('../../services/analyticsService');
      const result = await flushWidgetAnalyticsEvents({
        merchant_id: this.merchantId!,
        events: queue,
      });
      return result.accepted;
    } catch (error) {
      console.error('[WidgetAnalytics] Flush failed:', error);
      this.saveQueue(queue);
      return 0;
    }
  }

  updateSessionId(sessionId: string): void {
    this.sessionId = sessionId;
  }

  destroy(): void {
    if (this.flushTimer) {
      clearTimeout(this.flushTimer);
      this.flushTimer = null;
    }
    this._isInitialized = false;
    this.merchantId = null;
    this.sessionId = null;
    this.clearQueue();
  }

  isReducedMotion(): boolean {
    return this.reducedMotion;
  }
}

export const widgetAnalytics = new WidgetAnalyticsImpl();

export function trackWidgetOpen(): void {
  widgetAnalytics.track('widget_open', {
    url: typeof window !== 'undefined' ? window.location.href : undefined,
  });
}

export function trackMessageSend(messageLength: number): void {
  widgetAnalytics.track('message_send', {
    messageLength,
  });
}

export function trackQuickReplyClick(label: string): void {
  widgetAnalytics.track('quick_reply_click', {
    label,
  });
}

export function trackVoiceInput(durationMs: number, success: boolean): void {
  widgetAnalytics.track('voice_input', {
    durationMs,
    success,
  });
}

export function trackProactiveTrigger(triggerType: string, engaged: boolean): void {
  widgetAnalytics.track('proactive_trigger', {
    triggerType,
    engaged,
  });
}

export function trackCarouselEngagement(
  action: 'swipe' | 'click' | 'add_to_cart',
  productId?: string
): void {
  widgetAnalytics.track('carousel_engagement', {
    action,
    productId,
  });
}

export function logContactInteraction(
  contactType: 'phone' | 'email' | 'custom',
  action?: string
): void {
  widgetAnalytics.track('quick_reply_click', {
    contactType,
    action,
    label: `contact_${contactType}`,
  });
}
