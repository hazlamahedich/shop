/**
 * Tests for Widget Analytics Utility
 *
 * Story 9-10: Analytics & Performance Monitoring
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import {
  widgetAnalytics,
} from './analytics';

vi.mock('../../services/analyticsService', () => ({
  flushWidgetAnalyticsEvents: vi.fn().mockResolvedValue({ accepted: 1 }),
}));

describe('WidgetAnalytics', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    sessionStorage.clear();
    widgetAnalytics.destroy();
  });

  afterEach(() => {
    widgetAnalytics.destroy();
    vi.useRealTimers();
    vi.clearAllMocks();
  });

  describe('initialize', () => {
    it('should initialize with config', () => {
      widgetAnalytics.initialize({
        merchantId: 123,
        sessionId: 'test-session-id',
      });

      expect(widgetAnalytics.isInitialized).toBe(true);
    });

    it('should not initialize twice', () => {
      widgetAnalytics.initialize({
        merchantId: 123,
        sessionId: 'test-session-id',
      });

      widgetAnalytics.initialize({
        merchantId: 456,
        sessionId: 'other-session-id',
      });

      expect(widgetAnalytics.isInitialized).toBe(true);
    });
  });

  describe('track', () => {
    beforeEach(() => {
      widgetAnalytics.initialize({
        merchantId: 123,
        sessionId: 'test-session-id',
      });
    });

    it('should track widget_open event', () => {
      widgetAnalytics.track('widget_open', { url: 'https://example.com' });

      const events = widgetAnalytics.getQueuedEvents();
      expect(events).toHaveLength(1);
      expect(events[0].type).toBe('widget_open');
    });

    it('should track message_send event with metadata', () => {
      widgetAnalytics.track('message_send', { messageLength: 50 });

      const events = widgetAnalytics.getQueuedEvents();
      expect(events).toHaveLength(1);
      expect(events[0].type).toBe('message_send');
      expect(events[0].metadata?.messageLength).toBe(50);
    });

    it('should include ISO timestamp', () => {
      widgetAnalytics.track('widget_open');

      const events = widgetAnalytics.getQueuedEvents();
      expect(events[0].timestamp).toMatch(/^\d{4}-\d{2}-\d{2}T/);
    });

    it('should include session ID in event', () => {
      widgetAnalytics.track('widget_open');

      const events = widgetAnalytics.getQueuedEvents();
      expect(events[0].sessionId).toBe('test-session-id');
    });

    it('should not track if not initialized', () => {
      widgetAnalytics.destroy();

      widgetAnalytics.track('widget_open');

      const events = widgetAnalytics.getQueuedEvents();
      expect(events).toHaveLength(0);
    });
  });

  describe('persistence', () => {
    it('should persist events to sessionStorage', () => {
      widgetAnalytics.initialize({
        merchantId: 123,
        sessionId: 'test-session-id',
      });

      widgetAnalytics.track('widget_open');

      const stored = sessionStorage.getItem('widget_analytics_queue');
      expect(stored).not.toBeNull();
      const parsed = JSON.parse(stored!);
      expect(parsed).toHaveLength(1);
    });
  });

  describe('flush', () => {
    it('should clear queue after successful flush', async () => {
      widgetAnalytics.initialize({ merchantId: 123, sessionId: 'test-session-id' });

      widgetAnalytics.track('widget_open');
      await widgetAnalytics.flush();

      expect(widgetAnalytics.getQueuedEvents()).toHaveLength(0);
    });

    it('should handle flush errors gracefully', async () => {
      const { flushWidgetAnalyticsEvents } = await import('../../services/analyticsService');
      vi.mocked(flushWidgetAnalyticsEvents).mockRejectedValueOnce(new Error('Network error'));

      widgetAnalytics.initialize({ merchantId: 123, sessionId: 'test-session-id' });

      widgetAnalytics.track('widget_open');
      await widgetAnalytics.flush();

      expect(widgetAnalytics.getQueuedEvents()).toHaveLength(1);
    });

    it('should flush manually on demand', async () => {
      widgetAnalytics.initialize({ merchantId: 123, sessionId: 'test-session-id' });

      widgetAnalytics.track('widget_open');
      widgetAnalytics.track('message_send', { messageLength: 10 });

      expect(widgetAnalytics.getQueuedEvents()).toHaveLength(2);
      await widgetAnalytics.flush();
      expect(widgetAnalytics.getQueuedEvents()).toHaveLength(0);
    });

    it('should return 0 when flushing empty queue', async () => {
      widgetAnalytics.initialize({ merchantId: 123, sessionId: 'test-session-id' });

      const result = await widgetAnalytics.flush();
      expect(result).toBe(0);
    });
  });

  describe('lifecycle', () => {
    it('should cleanup on destroy', () => {
      widgetAnalytics.initialize({
        merchantId: 123,
        sessionId: 'test-session-id',
      });

      widgetAnalytics.track('widget_open');
      widgetAnalytics.destroy();

      expect(widgetAnalytics.isInitialized).toBe(false);
      expect(widgetAnalytics.getQueuedEvents()).toHaveLength(0);
    });

    it('should update session ID', () => {
      widgetAnalytics.initialize({
        merchantId: 123,
        sessionId: 'old-session-id',
      });

      widgetAnalytics.updateSessionId('new-session-id');

      widgetAnalytics.track('widget_open');

      const events = widgetAnalytics.getQueuedEvents();
      expect(events[0].sessionId).toBe('new-session-id');
    });
  });
});
