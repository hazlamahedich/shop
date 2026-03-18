/**
 * Component tests for useWidgetTheme hook
 *
 * Story 5-5: Theme Customization System
 * Tests theme retrieval, CSS variable generation, and default handling
 *
 * @tags component widget story-5-5 theme hook
 */

import { describe, it, expect } from 'vitest';
import { renderHook } from '@testing-library/react';
import { useWidgetTheme } from '@/widget/hooks/useWidgetTheme';
import type { WidgetTheme } from '@/widget/types/widget';

const DEFAULT_THEME: WidgetTheme = {
  primaryColor: '#6366f1',
  backgroundColor: '#ffffff',
  textColor: '#1f2937',
  botBubbleColor: '#f3f4f6',
  userBubbleColor: '#6366f1',
  position: 'bottom-right',
  borderRadius: 16,
  width: 380,
  height: 600,
  fontFamily: 'Inter, sans-serif',
  fontSize: 14,
};

const CUSTOM_THEME: WidgetTheme = {
  primaryColor: '#ff0000',
  backgroundColor: '#000000',
  textColor: '#ffffff',
  botBubbleColor: '#111111',
  userBubbleColor: '#ff0000',
  position: 'bottom-left',
  borderRadius: 24,
  width: 500,
  height: 700,
  fontFamily: 'Georgia, serif',
  fontSize: 18,
};

describe('useWidgetTheme Hook', () => {
  describe('getTheme', () => {
    it('should return default theme when no initial theme provided', () => {
      const { result } = renderHook(() => useWidgetTheme());

      const theme = result.current.getTheme();

      expect(theme).toEqual(DEFAULT_THEME);
    });

    it('should return provided initial theme', () => {
      const { result } = renderHook(() => useWidgetTheme(CUSTOM_THEME));

      const theme = result.current.getTheme();

      expect(theme).toEqual(CUSTOM_THEME);
    });

    it('should return theme with all 11 required fields', () => {
      const { result } = renderHook(() => useWidgetTheme());

      const theme = result.current.getTheme();
      const requiredFields = [
        'primaryColor',
        'backgroundColor',
        'textColor',
        'botBubbleColor',
        'userBubbleColor',
        'position',
        'borderRadius',
        'width',
        'height',
        'fontFamily',
        'fontSize',
      ];

      for (const field of requiredFields) {
        expect(theme).toHaveProperty(field);
      }
    });
  });

  describe('applyTheme', () => {
    it('should generate CSS custom properties from theme', () => {
      const { result } = renderHook(() => useWidgetTheme(CUSTOM_THEME));

      const styles = result.current.applyTheme(CUSTOM_THEME);

      expect(styles['--widget-primary']).toBe('#ff0000');
      expect(styles['--widget-bg']).toBe('#000000');
      expect(styles['--widget-text']).toBe('#ffffff');
    });

    it('should convert borderRadius to px', () => {
      const { result } = renderHook(() => useWidgetTheme());

      const styles = result.current.applyTheme(DEFAULT_THEME);

      expect(styles['--widget-radius']).toBe('16px');
    });

    it('should convert width to px', () => {
      const { result } = renderHook(() => useWidgetTheme());

      const styles = result.current.applyTheme(DEFAULT_THEME);

      expect(styles['--widget-width']).toBe('380px');
    });

    it('should convert height to px', () => {
      const { result } = renderHook(() => useWidgetTheme());

      const styles = result.current.applyTheme(DEFAULT_THEME);

      expect(styles['--widget-height']).toBe('600px');
    });

    it('should convert fontSize to px', () => {
      const { result } = renderHook(() => useWidgetTheme());

      const styles = result.current.applyTheme(DEFAULT_THEME);

      expect(styles['--widget-font-size']).toBe('14px');
    });

    it('should not convert fontFamily to px', () => {
      const { result } = renderHook(() => useWidgetTheme());

      const styles = result.current.applyTheme(DEFAULT_THEME);

      expect(styles['--widget-font']).toBe('Inter, sans-serif');
      expect(styles['--widget-font']).not.toContain('px');
    });

    it('should generate all 10 CSS custom properties', () => {
      const { result } = renderHook(() => useWidgetTheme());

      const styles = result.current.applyTheme(DEFAULT_THEME);
      const cssVars = [
        '--widget-primary',
        '--widget-bg',
        '--widget-text',
        '--widget-bot-bubble',
        '--widget-user-bubble',
        '--widget-radius',
        '--widget-font',
        '--widget-font-size',
        '--widget-width',
        '--widget-height',
      ];

      for (const varName of cssVars) {
        expect(styles).toHaveProperty(varName);
      }
    });

    it('should handle custom borderRadius value', () => {
      const theme: WidgetTheme = { ...DEFAULT_THEME, borderRadius: 24 };
      const { result } = renderHook(() => useWidgetTheme());

      const styles = result.current.applyTheme(theme);

      expect(styles['--widget-radius']).toBe('24px');
    });

    it('should handle zero borderRadius', () => {
      const theme: WidgetTheme = { ...DEFAULT_THEME, borderRadius: 0 };
      const { result } = renderHook(() => useWidgetTheme());

      const styles = result.current.applyTheme(theme);

      expect(styles['--widget-radius']).toBe('0px');
    });

    it('should handle custom fontFamily', () => {
      const theme: WidgetTheme = { ...DEFAULT_THEME, fontFamily: 'Arial, sans-serif' };
      const { result } = renderHook(() => useWidgetTheme());

      const styles = result.current.applyTheme(theme);

      expect(styles['--widget-font']).toBe('Arial, sans-serif');
    });
  });

  describe('defaultTheme', () => {
    it('should expose default theme', () => {
      const { result } = renderHook(() => useWidgetTheme());

      expect(result.current.defaultTheme).toEqual(DEFAULT_THEME);
    });

    it('should return same default theme regardless of initial theme', () => {
      const { result: result1 } = renderHook(() => useWidgetTheme());
      const { result: result2 } = renderHook(() => useWidgetTheme(CUSTOM_THEME));

      expect(result1.current.defaultTheme).toEqual(DEFAULT_THEME);
      expect(result2.current.defaultTheme).toEqual(DEFAULT_THEME);
    });

    it('should have immutable default theme', () => {
      const { result } = renderHook(() => useWidgetTheme());
      const theme1 = result.current.defaultTheme;
      const theme2 = result.current.defaultTheme;

      expect(theme1).toEqual(theme2);
    });
  });

  describe('Edge Cases', () => {
    it('should handle minimum valid theme values', () => {
      const minTheme: WidgetTheme = {
        primaryColor: '#000000',
        backgroundColor: '#ffffff',
        textColor: '#000000',
        botBubbleColor: '#ffffff',
        userBubbleColor: '#000000',
        position: 'bottom-right',
        borderRadius: 0,
        width: 280,
        height: 400,
        fontFamily: 'sans-serif',
        fontSize: 12,
      };

      const { result } = renderHook(() => useWidgetTheme(minTheme));

      const theme = result.current.getTheme();
      expect(theme.borderRadius).toBe(0);
      expect(theme.width).toBe(280);
      expect(theme.height).toBe(400);
      expect(theme.fontSize).toBe(12);
    });

    it('should handle maximum valid theme values', () => {
      const maxTheme: WidgetTheme = {
        primaryColor: '#ffffff',
        backgroundColor: '#000000',
        textColor: '#ffffff',
        botBubbleColor: '#111111',
        userBubbleColor: '#ffffff',
        position: 'bottom-left',
        borderRadius: 24,
        width: 600,
        height: 900,
        fontFamily: 'Georgia, Times, serif',
        fontSize: 20,
      };

      const { result } = renderHook(() => useWidgetTheme(maxTheme));

      const theme = result.current.getTheme();
      expect(theme.borderRadius).toBe(24);
      expect(theme.width).toBe(600);
      expect(theme.height).toBe(900);
      expect(theme.fontSize).toBe(20);
    });

    it('should generate consistent CSS properties for same theme', () => {
      const { result } = renderHook(() => useWidgetTheme(CUSTOM_THEME));

      const styles1 = result.current.applyTheme(CUSTOM_THEME);
      const styles2 = result.current.applyTheme(CUSTOM_THEME);

      expect(styles1).toEqual(styles2);
    });
  });
});
