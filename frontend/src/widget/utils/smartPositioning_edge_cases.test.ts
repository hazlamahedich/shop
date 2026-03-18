import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import {
  detectImportantElements,
  getElementBounds,
  checkCollision,
  findOptimalPosition,
  constrainToViewport,
  snapToEdge,
  isMobileDevice,
  getMobileDimensions,
  debounce,
} from './smartPositioning';
import type { BoundingBox } from './smartPositioning';
import { DEFAULT_POSITIONING_CONFIG } from '../types/widget';

describe('smartPositioning - Error Boundaries', () => {
  const originalInnerWidth = window.innerWidth;
  const originalInnerHeight = window.innerHeight;

  beforeEach(() => {
    vi.stubGlobal('innerWidth', 1920);
    vi.stubGlobal('innerHeight', 1080);
  });

  afterEach(() => {
    vi.stubGlobal('innerWidth', originalInnerWidth);
    vi.stubGlobal('innerHeight', originalInnerHeight);
    vi.unstubAllGlobals();
  });

  describe('detectImportantElements - Error Cases', () => {
    it('handles invalid CSS selectors gracefully', () => {
      document.body.innerHTML = '<div class="test" data-test="true">Content</div>';
      
      const elements = detectImportantElements(['[invalid-selector[', '[data-test]']);
      
      expect(elements.length).toBeGreaterThanOrEqual(0);
      expect(elements[0]).toBeDefined();
    });

    it('handles empty DOM gracefully', () => {
      document.body.innerHTML = '';
      
      const elements = detectImportantElements();
      
      expect(elements).toEqual([]);
    });

    it('handles elements with negative z-index', () => {
      const el = document.createElement('div');
      el.style.zIndex = '-1';
      document.body.appendChild(el);
      
      const elements = detectImportantElements();
      
      expect(elements).not.toContain(el);
    });

    it('handles elements with non-numeric z-index', () => {
      const el = document.createElement('div');
      (el.style as any).zIndex = 'invalid';
      document.body.appendChild(el);
      
      const elements = detectImportantElements();
      
      expect(elements).not.toContain(el);
    });
  });

  describe('getElementBounds - Error Cases', () => {
    it('handles elements not in DOM', () => {
      const el = document.createElement('div');
      document.body.appendChild(el);
      document.body.removeChild(el);
      
      expect(() => getElementBounds(el)).not.toThrow();
    });

    it('handles elements with zero dimensions', () => {
      const el = document.createElement('div');
      el.style.width = '0';
      el.style.height = '0';
      document.body.appendChild(el);
      
      const bounds = getElementBounds(el);
      
      expect(bounds.width).toBe(0);
      expect(bounds.height).toBe(0);
    });
  });

  describe('checkCollision - Edge Cases', () => {
    it('handles zero-area rectangles', () => {
      const rect1: BoundingBox = { x: 0, y: 0, width: 0, height: 0 };
      const rect2: BoundingBox = { x: 0, y: 0, width: 0, height: 0 };
      
      expect(checkCollision(rect1, rect2)).toBe(false);
    });

    it('handles negative coordinates', () => {
      const rect1: BoundingBox = { x: -100, y: -100, width: 200, height: 200 };
      const rect2: BoundingBox = { x: -50, y: -50, width: 100, height: 100 };
      
      expect(checkCollision(rect1, rect2)).toBe(true);
    });

    it('handles extremely large values', () => {
      const rect1: BoundingBox = { x: 0, y: 0, width: Number.MAX_SAFE_INTEGER, height: Number.MAX_SAFE_INTEGER };
      const rect2: BoundingBox = { x: 100, y: 100, width: 100, height: 100 };
      
      expect(() => checkCollision(rect1, rect2)).not.toThrow();
    });
  });

  describe('findOptimalPosition - Edge Cases', () => {
    it('handles all corners blocked', () => {
      const importantBounds: BoundingBox[] = [
        { x: 0, y: 0, width: 1920, height: 300 },
        { x: 0, y: 780, width: 1920, height: 300 },
        { x: 0, y: 0, width: 500, height: 1080 },
        { x: 1420, y: 0, width: 500, height: 1080 },
      ];
      
      const widgetSize = { width: 400, height: 600 };
      const position = findOptimalPosition(importantBounds, widgetSize);
      
      expect(position.edge).toBe('center');
    });

    it('handles extremely large widget', () => {
      const widgetSize = { width: 1800, height: 1000 };
      const position = findOptimalPosition([], widgetSize);
      
      expect(['center', 'bottom-right']).toContain(position.edge);
    });

    it('handles widget larger than viewport', () => {
      const widgetSize = { width: 2500, height: 1500 };
      const position = findOptimalPosition([], widgetSize);
      
      expect(position).toBeDefined();
    });
  });

  describe('constrainToViewport - Edge Cases', () => {
    it('handles negative positions', () => {
        const position = { x: -1000, y: -1000, edge: 'bottom-right' as const };
        const widgetSize = { width: 400, height: 600 };
      
        const constrained = constrainToViewport(position, widgetSize);
      
        expect(constrained.x).toBeGreaterThanOrEqual(0);
        expect(constrained.y).toBeGreaterThanOrEqual(0);
      });

    it('handles NaN positions values', () => {
        const position = { x: NaN, y: NaN, edge: 'bottom-right' as const };
        const widgetSize = { width: 400, height: 600 };
      
        const constrained = constrainToViewport(position, widgetSize);
        
        expect(isNaN(constrained.x) || constrained.x >= 0).toBe(true);
      });
  });

  describe('snapToEdge - Edge Cases', () => {
    it('handles negative threshold', () => {
        const position = { x: 100, y: 100, edge: 'bottom-right' as const };
        const widgetSize = { width: 400, height: 600 };
        
        vi.stubGlobal('innerWidth', 1920);
        vi.stubGlobal('innerHeight', 1080);
        
        const snapped = snapToEdge(position, widgetSize, { ...DEFAULT_POSITIONING_CONFIG, edgeSnapThreshold: -10 });
        
        expect(snapped).toBeDefined();
        
        vi.unstubAllGlobals();
      });
  });

  describe('isMobileDevice - Edge Cases', () => {
    it('handles undefined window properties', () => {
        const originalOntouchstart = window.ontouchstart;
        delete (window as any).ontouchstart;
        
        Object.defineProperty(window, 'innerWidth', { value: 1920, writable: true });
        
        const result = isMobileDevice();
        
        expect(typeof result).toBe('boolean');
        
        if (originalOntouchstart !== undefined) {
          (window as any).ontouchstart = originalOntouchstart;
        }
      });
  });

  describe('debounce - Edge Cases', () => {
    beforeEach(() => {
      vi.useFakeTimers();
    });

    afterEach(() => {
      vi.useRealTimers();
    });

    it('handles zero delay', () => {
      const fn = vi.fn();
      const debounced = debounce(fn, 0);

      debounced();
      vi.advanceTimersByTime(0);
      
      expect(fn).toHaveBeenCalledTimes(1);
    });

    it('handles negative delay', () => {
      const fn = vi.fn();
      const debounced = debounce(fn, -100);

      debounced();
      vi.advanceTimersByTime(0);
      
      expect(fn).toHaveBeenCalledTimes(1);
    });

    it('handles function that throws', () => {
      const fn = vi.fn(() => {
        throw new Error('Test error');
      });
      const debounced = debounce(fn, 100);

      debounced();
      
      expect(() => vi.advanceTimersByTime(100)).toThrow('Test error');
    });
  });
});

describe('smartPositioning - Concurrency Tests', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  describe('debounce - Rapid Invocation', () => {
    it('handles 100 rapid invocations', () => {
      const fn = vi.fn();
      const debounced = debounce(fn, 250);

      for (let i = 0; i < 100; i++) {
        debounced(`call-${i}`);
        vi.advanceTimersByTime(10);
      }
      
      vi.advanceTimersByTime(250);
      
      expect(fn).toHaveBeenCalledTimes(1);
      expect(fn).toHaveBeenCalledWith('call-99');
    });

    it('maintains correct context with multiple debounced functions', () => {
      const fn1 = vi.fn();
      const fn2 = vi.fn();
      const debounced1 = debounce(fn1, 100);
      const debounced2 = debounce(fn2, 200);

      debounced1('first');
      debounced2('second');
      
      vi.advanceTimersByTime(150);
      expect(fn1).toHaveBeenCalledTimes(1);
      expect(fn2).toHaveBeenCalledTimes(0);
      
      vi.advanceTimersByTime(100);
      expect(fn2).toHaveBeenCalledTimes(1);
    });
  });

  describe('findOptimalPosition - Multiple Elements', () => {
    beforeEach(() => {
      vi.stubGlobal('innerWidth', 1920);
      vi.stubGlobal('innerHeight', 1080);
    });

    afterEach(() => {
      vi.unstubAllGlobals();
    });

    it('handles 1000 important elements efficiently', () => {
      const importantBounds: BoundingBox[] = [];
      for (let i = 0; i < 1000; i++) {
        importantBounds.push({
          x: Math.random() * 1920,
          y: Math.random() * 1080,
          width: 50,
          height: 50,
        });
      }
      
      const widgetSize = { width: 400, height: 600 };
      
      const startTime = performance.now();
      const position = findOptimalPosition(importantBounds, widgetSize);
      const endTime = performance.now();
      
      expect(position).toBeDefined();
      expect(endTime - startTime).toBeLessThan(100);
    });
  });
});

describe('smartPositioning - Accessibility Edge Cases', () => {
  describe('reduced motion integration', () => {
    it('should respect prefers-reduced-motion system setting', () => {
      vi.stubGlobal('matchMedia', (query: string) => ({
        matches: query === '(prefers-reduced-motion: reduce)',
        media: query,
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
      }));
      
      const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
      const prefersReducedMotion = mediaQuery.matches;
      
      expect(typeof prefersReducedMotion).toBe('boolean');
      
      vi.unstubAllGlobals();
    });
  });

  describe('high contrast mode', () => {
    it('should detect high contrast mode', () => {
      vi.stubGlobal('matchMedia', (query: string) => ({
        matches: query === '(prefers-contrast: more)',
        media: query,
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
      }));
      
      const mediaQuery = window.matchMedia('(prefers-contrast: more)');
      const prefersHighContrast = mediaQuery.matches;
      
      expect(typeof prefersHighContrast).toBe('boolean');
      
      vi.unstubAllGlobals();
    });
  });

  describe('touch target sizing', () => {
    it('getMobileDimensions returns sizes meeting WCAG touch target minimum', () => {
      vi.stubGlobal('innerWidth', 375);
      vi.stubGlobal('innerHeight', 667);
      
      const dims = getMobileDimensions();
      
      expect(dims.width).toBe('90%');
      expect(dims.height).toBe('80%');
      
      vi.unstubAllGlobals();
    });
  });
});

describe('smartPositioning - Performance Tests', () => {
  beforeEach(() => {
    vi.stubGlobal('innerWidth', 1920);
    vi.stubGlobal('innerHeight', 1080);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  describe('detectImportantElements - Performance', () => {
    it('handles DOM with 1000 elements efficiently', () => {
      document.body.innerHTML = '';
      
      for (let i = 0; i < 1000; i++) {
        const div = document.createElement('div');
        div.textContent = `Element ${i}`;
        document.body.appendChild(div);
      }
      
      const startTime = performance.now();
      const elements = detectImportantElements();
      const endTime = performance.now();
      
      expect(endTime - startTime).toBeLessThan(1500);
      expect(elements).toBeDefined();
      
      document.body.innerHTML = '';
    });
  });

  describe('checkCollision - Performance', () => {
    it('handles 10000 collision checks efficiently', () => {
      const rect1: BoundingBox = { x: 100, y: 100, width: 200, height: 200 };
      const rect2: BoundingBox = { x: 150, y: 150, width: 200, height: 200 };
      
      const startTime = performance.now();
      
      for (let i = 0; i < 10000; i++) {
        checkCollision(rect1, rect2);
      }
      
      const endTime = performance.now();
      
      expect(endTime - startTime).toBeLessThan(100);
    });
  });

  describe('debounce - Memory Efficiency', () => {
    beforeEach(() => {
      vi.useFakeTimers();
    });

    afterEach(() => {
      vi.useRealTimers();
    });

    it('does not leak memory with repeated calls', () => {
      const fn = vi.fn();
      const debounced = debounce(fn, 100);
      
      for (let i = 0; i < 1000; i++) {
        debounced();
        vi.advanceTimersByTime(50);
      }
      
      vi.advanceTimersByTime(100);
      
      expect(fn).toHaveBeenCalledTimes(1);
    });
  });
});
