/**
 * Unit tests for Widget Analytics Utility
 *
 * Story 9-10: Analytics & Performance Monitoring
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';

const mockFlushWidgetAnalyticsEvents = vi.fn();
vi.mock('../../../services/analyticsService', () => ({
  flushWidgetAnalyticsEvents: mockFlushWidgetAnalyticsEvents,
}));

const mockSessionStorage = (() => {
  let store: Record<string, string> = {};
  return {
    getItem: vi.fn((key: string) => store[key] || null),
    setItem: vi.fn((key: string, value: string) => {
      store[key] = value;
    }),
    removeItem: vi.fn((key: string) => {
      delete store[key];
    }),
    clear: vi.fn(() => {
      store = {};
    }),
  };
})();

Object.defineProperty(global, 'sessionStorage', {
  value: mockSessionStorage,
});

const mockMatchMedia = vi.fn();
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: mockMatchMedia,
});

import {
  widgetAnalytics,
  trackWidgetOpen,
  trackMessageSend,
  trackQuickReplyClick,
  trackVoiceInput,
  trackProactiveTrigger,
  trackCarouselEngagement,
} from './analytics';

describe('Widget Analytics Utility', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockSessionStorage.clear();
    mockFlushWidgetAnalyticsEvents.mockResolvedValue({ accepted: 1 });

    mockMatchMedia.mockReturnValue({
      matches: false,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    });

    widgetAnalytics.destroy();
    widgetAnalytics.initialize({
      merchantId: 1,
      sessionId: 'test-session-123',
      batchSize: 3,
      flushInterval: 30000,
    });
  });

  afterEach(() => {
    widgetAnalytics.destroy();
  });

  describe('Initialization', () => {
    it('should initialize with config', () => {
      expect(widgetAnalytics.isInitialized).toBe(true);
    });

    it('should not reinitialize if already initialized', () => {
      widgetAnalytics.initialize({
        merchantId: 2,
        sessionId: 'different-session',
      });
      expect(widgetAnalytics.isInitialized).toBe(true);
    });
  });

  describe('Event Tracking', () => {
    it('should track widget_open event', () => {
      trackWidgetOpen();
      const events = widgetAnalytics.getQueuedEvents();
      expect(events).toHaveLength(1);
      expect(events[0].type).toBe('widget_open');
      expect(events[0].sessionId).toBe('test-session-123');
    });

    it('should track message_send event with metadata', () => {
      trackMessageSend(50);
      const events = widgetAnalytics.getQueuedEvents();
      expect(events).toHaveLength(1);
      expect(events[0].type).toBe('message_send');
      expect(events[0].metadata?.messageLength).toBe(50);
    });

    it('should track quick_reply_click event', () => {
      trackQuickReplyClick('Track Order');
      const events = widgetAnalytics.getQueuedEvents();
      expect(events).toHaveLength(1);
      expect(events[0].type).toBe('quick_reply_click');
      expect(events[0].metadata?.label).toBe('Track Order');
    });

    it('should track voice_input event', () => {
      trackVoiceInput(2500, true);
      const events = widgetAnalytics.getQueuedEvents();
      expect(events).toHaveLength(1);
      expect(events[0].type).toBe('voice_input');
      expect(events[0].metadata?.durationMs).toBe(2500);
      expect(events[0].metadata?.success).toBe(true);
    });

    it('should track proactive_trigger event', () => {
      trackProactiveTrigger('exit_intent', true);
      const events = widgetAnalytics.getQueuedEvents();
      expect(events).toHaveLength(1);
      expect(events[0].type).toBe('proactive_trigger');
      expect(events[0].metadata?.triggerType).toBe('exit_intent');
      expect(events[0].metadata?.engaged).toBe(true);
    });

    it('should track carousel_engagement event', () => {
      trackCarouselEngagement('swipe', 'prod-123');
      const events = widgetAnalytics.getQueuedEvents();
      expect(events).toHaveLength(1);
      expect(events[0].type).toBe('carousel_engagement');
      expect(events[0].metadata?.action).toBe('swipe');
      expect(events[0].metadata?.productId).toBe('prod-123');
    });
  });

  describe('Event Batching', () => {
    it('should batch events until batch size is reached', async () => {
      trackWidgetOpen();
      await new Promise((resolve) => setTimeout(resolve, 0));
      expect(mockFlushWidgetAnalyticsEvents).not.toHaveBeenCalled();

      trackMessageSend(10);
      await new Promise((resolve) => setTimeout(resolve, 0));
      expect(mockFlushWidgetAnalyticsEvents).not.toHaveBeenCalled();

      trackQuickReplyClick('Help');
      await new Promise((resolve) => setTimeout(resolve, 0));
      expect(mockFlushWidgetAnalyticsEvents).toHaveBeenCalledTimes(1);
    });

    it('should include all batched events in flush', async () => {
      trackWidgetOpen();
      trackMessageSend(10);
      trackQuickReplyClick('Help');

      await new Promise((resolve) => setTimeout(resolve, 50));

      expect(mockFlushWidgetAnalyticsEvents).toHaveBeenCalledTimes(1);
      const callArgs = mockFlushWidgetAnalyticsEvents.mock.calls[0][0];
      expect(callArgs.merchantId).toBe(1);
      expect(callArgs.events.length).toBeGreaterThanOrEqual(2);
      expect(callArgs.events.map((e: any) => e.type)).toContain('widget_open');
      expect(callArgs.events.map((e: any) => e.type)).toContain('message_send');
    });
  });

  describe('Queue Persistence', () => {
    it('should persist events to sessionStorage', () => {
      trackWidgetOpen();
      expect(mockSessionStorage.setItem).toHaveBeenCalled();
    });

    it('should clear queue after flush', async () => {
      trackWidgetOpen();
      trackMessageSend(10);
      trackQuickReplyClick('Help');

      await new Promise((resolve) => setTimeout(resolve, 10));

      expect(widgetAnalytics.getQueuedEvents()).toHaveLength(0);
    });
  });

  describe('Reduced Motion', () => {
    it('should include reducedMotion in metadata', () => {
      trackWidgetOpen();
      const events = widgetAnalytics.getQueuedEvents();
      expect(events[0].metadata?.reducedMotion).toBeDefined();
    });
  });

  describe('Session Management', () => {
    it('should update session ID', () => {
      widgetAnalytics.updateSessionId('new-session-456');
      trackWidgetOpen();
      const events = widgetAnalytics.getQueuedEvents();
      expect(events[0].sessionId).toBe('new-session-456');
    });
  });

  describe('Destroy', () => {
    it('should clear all state on destroy', () => {
      trackWidgetOpen();
      widgetAnalytics.destroy();

      expect(widgetAnalytics.isInitialized).toBe(false);
      expect(widgetAnalytics.getQueuedEvents()).toHaveLength(0);
    });
  });

  describe('Error Handling', () => {
    it('should not track if not initialized', () => {
      const consoleSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
      widgetAnalytics.destroy();

      trackWidgetOpen();

      expect(consoleSpy).toHaveBeenCalledWith(
        '[WidgetAnalytics] Not initialized or missing sessionId'
      );
      consoleSpy.mockRestore();
    });

    it('should restore queue on flush failure', async () => {
      mockFlushWidgetAnalyticsEvents.mockRejectedValue(new Error('Network error'));

      trackWidgetOpen();
      trackMessageSend(10);
      trackQuickReplyClick('Help');

      await new Promise((resolve) => setTimeout(resolve, 50));

      const events = widgetAnalytics.getQueuedEvents();
      expect(events.length).toBeGreaterThanOrEqual(1);
      expect(events.map((e: { type: string }) => e.type)).toContain('widget_open');
    });
  });
});

describe('Track Functions', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    widgetAnalytics.destroy();
    widgetAnalytics.initialize({
      merchantId: 1,
      sessionId: 'test-session',
    });
  });

  afterEach(() => {
    widgetAnalytics.destroy();
  });

  it('trackWidgetOpen should include URL metadata', () => {
    trackWidgetOpen();
    const events = widgetAnalytics.getQueuedEvents();
    expect(events[0].metadata?.url).toBeDefined();
  });

  it('trackCarouselEngagement should handle all action types', () => {
    const actions: Array<'swipe' | 'click' | 'add_to_cart'> = [
      'swipe',
      'click',
      'add_to_cart',
    ];

    actions.forEach((action) => {
      trackCarouselEngagement(action, 'prod-1');
    });

    const events = widgetAnalytics.getQueuedEvents();
    expect(events).toHaveLength(3);
    expect(events.map((e: any) => e.metadata?.action)).toEqual(actions);
  });
});
