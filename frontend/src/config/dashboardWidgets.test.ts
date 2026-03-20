import { describe, it, expect } from 'vitest';
import { WIDGET_CONFIG, isWidgetVisible } from './dashboardWidgets';

describe('dashboardWidgets', () => {
  describe('isWidgetVisible', () => {
    describe('E-commerce mode', () => {
      it('shows e-commerce widgets', () => {
        expect(isWidgetVisible('revenue', 'ecommerce')).toBe(true);
        expect(isWidgetVisible('top-products', 'ecommerce')).toBe(true);
        expect(isWidgetVisible('pending-orders', 'ecommerce')).toBe(true);
        expect(isWidgetVisible('geographic', 'ecommerce')).toBe(true);
        expect(isWidgetVisible('conversion-funnel', 'ecommerce')).toBe(true);
      });

      it('hides General-only widgets', () => {
        expect(isWidgetVisible('knowledge-base', 'ecommerce')).toBe(false);
        expect(isWidgetVisible('feedback-analytics', 'ecommerce')).toBe(false);
      });

      it('shows shared widgets', () => {
        expect(isWidgetVisible('conversation-overview', 'ecommerce')).toBe(true);
        expect(isWidgetVisible('handoff-queue', 'ecommerce')).toBe(true);
        expect(isWidgetVisible('ai-cost', 'ecommerce')).toBe(true);
        expect(isWidgetVisible('bot-quality', 'ecommerce')).toBe(true);
        expect(isWidgetVisible('alerts', 'ecommerce')).toBe(true);
        expect(isWidgetVisible('peak-hours', 'ecommerce')).toBe(true);
        expect(isWidgetVisible('benchmark-comparison', 'ecommerce')).toBe(true);
        expect(isWidgetVisible('customer-sentiment', 'ecommerce')).toBe(true);
        expect(isWidgetVisible('knowledge-gap', 'ecommerce')).toBe(true);
      });
    });

    describe('General mode', () => {
      it('hides e-commerce widgets', () => {
        expect(isWidgetVisible('revenue', 'general')).toBe(false);
        expect(isWidgetVisible('top-products', 'general')).toBe(false);
        expect(isWidgetVisible('pending-orders', 'general')).toBe(false);
        expect(isWidgetVisible('geographic', 'general')).toBe(false);
        expect(isWidgetVisible('conversion-funnel', 'general')).toBe(false);
      });

      it('shows General-only widgets', () => {
        expect(isWidgetVisible('knowledge-base', 'general')).toBe(true);
        expect(isWidgetVisible('feedback-analytics', 'general')).toBe(true);
      });

      it('shows shared widgets', () => {
        expect(isWidgetVisible('conversation-overview', 'general')).toBe(true);
        expect(isWidgetVisible('handoff-queue', 'general')).toBe(true);
        expect(isWidgetVisible('ai-cost', 'general')).toBe(true);
        expect(isWidgetVisible('bot-quality', 'general')).toBe(true);
        expect(isWidgetVisible('alerts', 'general')).toBe(true);
        expect(isWidgetVisible('peak-hours', 'general')).toBe(true);
        expect(isWidgetVisible('benchmark-comparison', 'general')).toBe(true);
        expect(isWidgetVisible('customer-sentiment', 'general')).toBe(true);
        expect(isWidgetVisible('knowledge-gap', 'general')).toBe(true);
      });
    });

    describe('Graceful degradation', () => {
      it('shows all widgets when mode is undefined', () => {
        expect(isWidgetVisible('revenue', undefined)).toBe(true);
        expect(isWidgetVisible('knowledge-base', undefined)).toBe(true);
        expect(isWidgetVisible('conversation-overview', undefined)).toBe(true);
      });

      it('shows all widgets when mode is null', () => {
        expect(isWidgetVisible('revenue', null)).toBe(true);
        expect(isWidgetVisible('knowledge-base', null)).toBe(true);
        expect(isWidgetVisible('conversation-overview', null)).toBe(true);
      });
    });

    describe('Edge cases', () => {
      it('returns false for invalid widget ID', () => {
        expect(isWidgetVisible('invalid-widget', 'ecommerce')).toBe(false);
        expect(isWidgetVisible('invalid-widget', 'general')).toBe(false);
      });
    });
  });

  describe('Dashboard performance', () => {
    it('should render widgets quickly', () => {
      const start = Date.now();
      
      const modes = ['general', 'ecommerce'] as const;
      modes.forEach(mode => {
        const allWidgets = Object.keys(WIDGET_CONFIG);
        allWidgets.forEach(widgetId => {
          isWidgetVisible(widgetId, mode);
        });
      });
      
      const duration = Date.now() - start;
      expect(duration).toBeLessThan(100);
    });
  });
});
