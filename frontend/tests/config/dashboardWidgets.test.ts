import { describe, it, expect } from 'vitest';
import { isWidgetVisible, WIDGET_CONFIG, type WidgetId, type OnboardingMode } from '../../src/config/dashboardWidgets';

describe('dashboardWidgets configuration', () => {
  describe('WIDGET_CONFIG', () => {
    it('should define all required widgets', () => {
      expect(WIDGET_CONFIG['revenue']).toBeDefined();
      expect(WIDGET_CONFIG['top-products']).toBeDefined();
      expect(WIDGET_CONFIG['pending-orders']).toBeDefined();
      expect(WIDGET_CONFIG['geographic']).toBeDefined();
      expect(WIDGET_CONFIG['knowledge-base']).toBeDefined();
      expect(WIDGET_CONFIG['conversation-overview']).toBeDefined();
      expect(WIDGET_CONFIG['handoff-queue']).toBeDefined();
      expect(WIDGET_CONFIG['ai-cost']).toBeDefined();
    });

    it('should mark e-commerce widgets as ecommerce-only', () => {
      expect(WIDGET_CONFIG['revenue'].modes).toEqual(['ecommerce']);
      expect(WIDGET_CONFIG['top-products'].modes).toEqual(['ecommerce']);
      expect(WIDGET_CONFIG['pending-orders'].modes).toEqual(['ecommerce']);
      expect(WIDGET_CONFIG['geographic'].modes).toEqual(['ecommerce']);
    });

    it('should mark knowledge-base as general-only', () => {
      expect(WIDGET_CONFIG['knowledge-base'].modes).toEqual(['general']);
    });

    it('should mark shared widgets as both modes', () => {
      expect(WIDGET_CONFIG['conversation-overview'].modes).toEqual(['general', 'ecommerce']);
      expect(WIDGET_CONFIG['handoff-queue'].modes).toEqual(['general', 'ecommerce']);
      expect(WIDGET_CONFIG['ai-cost'].modes).toEqual(['general', 'ecommerce']);
    });
  });

  describe('isWidgetVisible', () => {
    it('should return true for e-commerce widgets in ecommerce mode', () => {
      expect(isWidgetVisible('revenue', 'ecommerce')).toBe(true);
      expect(isWidgetVisible('top-products', 'ecommerce')).toBe(true);
      expect(isWidgetVisible('pending-orders', 'ecommerce')).toBe(true);
      expect(isWidgetVisible('geographic', 'ecommerce')).toBe(true);
    });

    it('should return false for e-commerce widgets in general mode', () => {
      expect(isWidgetVisible('revenue', 'general')).toBe(false);
      expect(isWidgetVisible('top-products', 'general')).toBe(false);
      expect(isWidgetVisible('pending-orders', 'general')).toBe(false);
      expect(isWidgetVisible('geographic', 'general')).toBe(false);
    });

    it('should return true for knowledge-base widget in general mode', () => {
      expect(isWidgetVisible('knowledge-base', 'general')).toBe(true);
    });

    it('should return false for knowledge-base widget in ecommerce mode', () => {
      expect(isWidgetVisible('knowledge-base', 'ecommerce')).toBe(false);
    });

    it('should return true for shared widgets in both modes', () => {
      // General mode
      expect(isWidgetVisible('conversation-overview', 'general')).toBe(true);
      expect(isWidgetVisible('handoff-queue', 'general')).toBe(true);
      expect(isWidgetVisible('ai-cost', 'general')).toBe(true);
      
      // E-commerce mode
      expect(isWidgetVisible('conversation-overview', 'ecommerce')).toBe(true);
      expect(isWidgetVisible('handoff-queue', 'ecommerce')).toBe(true);
      expect(isWidgetVisible('ai-cost', 'ecommerce')).toBe(true);
    });

    it('should return true for all widgets when mode is undefined (graceful degradation)', () => {
      expect(isWidgetVisible('revenue', undefined)).toBe(true);
      expect(isWidgetVisible('knowledge-base', undefined)).toBe(true);
      expect(isWidgetVisible('conversation-overview', undefined)).toBe(true);
    });

    it('should handle invalid widget IDs gracefully', () => {
      // TypeScript would prevent this at compile time, but runtime safety
      const invalidId = 'invalid-widget' as WidgetId;
      expect(isWidgetVisible(invalidId, 'general')).toBe(false);
    });
  });
});
