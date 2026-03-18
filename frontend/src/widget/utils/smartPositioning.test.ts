import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import {
  detectImportantElements,
  getElementBounds,
  checkCollision,
  findOptimalPosition,
  constrainToViewport,
  snapToEdge,
  isMobileDevice,
  getMobilePosition,
  getMobileDimensions,
  debounce,
  type BoundingBox,
} from './smartPositioning';

describe('smartPositioning', () => {
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

  describe('detectImportantElements', () => {
    it('finds elements with [data-important="true"] attribute', () => {
      const importantDiv = document.createElement('div');
      importantDiv.setAttribute('data-important', 'true');
      document.body.appendChild(importantDiv);

      const elements = detectImportantElements();
      expect(elements).toContain(importantDiv);

      document.body.removeChild(importantDiv);
    });

    it('finds elements with high z-index (>100)', () => {
      const highZDiv = document.createElement('div');
      highZDiv.style.zIndex = '200';
      document.body.appendChild(highZDiv);

      const elements = detectImportantElements();
      expect(elements).toContain(highZDiv);

      document.body.removeChild(highZDiv);
    });

    it('finds buttons with CTA text patterns', () => {
      const buyButton = document.createElement('button');
      buyButton.textContent = 'Buy Now';
      document.body.appendChild(buyButton);

      const cartButton = document.createElement('button');
      cartButton.textContent = 'Add to Cart';
      document.body.appendChild(cartButton);

      const elements = detectImportantElements();
      expect(elements).toContain(buyButton);
      expect(elements).toContain(cartButton);

      document.body.removeChild(buyButton);
      document.body.removeChild(cartButton);
    });

    it('finds checkout buttons', () => {
      const checkoutBtn = document.createElement('button');
      checkoutBtn.textContent = 'Proceed to Checkout';
      document.body.appendChild(checkoutBtn);

      const elements = detectImportantElements();
      expect(elements).toContain(checkoutBtn);

      document.body.removeChild(checkoutBtn);
    });

    it('finds anchor buttons with CTA text', () => {
      const linkBtn = document.createElement('a');
      linkBtn.setAttribute('role', 'button');
      linkBtn.textContent = 'Shop Now';
      document.body.appendChild(linkBtn);

      const elements = detectImportantElements();
      expect(elements).toContain(linkBtn);

      document.body.removeChild(linkBtn);
    });

    it('ignores buttons without CTA text', () => {
      const normalButton = document.createElement('button');
      normalButton.textContent = 'Learn More';
      document.body.appendChild(normalButton);

      const elements = detectImportantElements();
      expect(elements).not.toContain(normalButton);

      document.body.removeChild(normalButton);
    });

    it('ignores elements with low z-index', () => {
      const lowZDiv = document.createElement('div');
      lowZDiv.style.zIndex = '50';
      document.body.appendChild(lowZDiv);

      const elements = detectImportantElements();
      expect(elements).not.toContain(lowZDiv);

      document.body.removeChild(lowZDiv);
    });
  });

  describe('getElementBounds', () => {
    it('returns bounding box for element', () => {
      const div = document.createElement('div');
      div.getBoundingClientRect = vi.fn().mockReturnValue({
        left: 100,
        top: 200,
        width: 300,
        height: 150,
        right: 400,
        bottom: 350,
        x: 100,
        y: 200,
        toJSON: () => ({}),
      });

      const bounds = getElementBounds(div);
      expect(bounds.x).toBe(100);
      expect(bounds.y).toBe(200);
      expect(bounds.width).toBe(300);
      expect(bounds.height).toBe(150);
    });
  });

  describe('checkCollision', () => {
    it('returns true when rectangles overlap', () => {
      const rect1: BoundingBox = { x: 0, y: 0, width: 100, height: 100 };
      const rect2: BoundingBox = { x: 50, y: 50, width: 100, height: 100 };

      expect(checkCollision(rect1, rect2)).toBe(true);
    });

    it('returns false when rectangles do not overlap', () => {
      const rect1: BoundingBox = { x: 0, y: 0, width: 100, height: 100 };
      const rect2: BoundingBox = { x: 200, y: 200, width: 100, height: 100 };

      expect(checkCollision(rect1, rect2)).toBe(false);
    });

    it('returns false for edge-adjacent rectangles', () => {
      const rect1: BoundingBox = { x: 0, y: 0, width: 100, height: 100 };
      const rect2: BoundingBox = { x: 100, y: 0, width: 100, height: 100 };

      expect(checkCollision(rect1, rect2)).toBe(false);
    });

    it('respects minClearance parameter', () => {
      const rect1: BoundingBox = { x: 0, y: 0, width: 100, height: 100 };
      const rect2: BoundingBox = { x: 110, y: 0, width: 100, height: 100 };

      expect(checkCollision(rect1, rect2, 0)).toBe(false);
      expect(checkCollision(rect1, rect2, 15)).toBe(true);
    });
  });

  describe('findOptimalPosition', () => {
    it('prefers bottom-right when unobstructed', () => {
      const widgetSize = { width: 400, height: 600 };
      const importantBounds: BoundingBox[] = [];

      const position = findOptimalPosition(importantBounds, widgetSize);

      expect(position.edge).toBe('bottom-right');
      expect(position.x).toBe(1920 - 400 - 10);
      expect(position.y).toBe(1080 - 600 - 10);
    });

    it('avoids important elements', () => {
      const widgetSize = { width: 400, height: 600 };
      const importantBounds: BoundingBox[] = [
        { x: 1500, y: 460, width: 200, height: 200 },
      ];

      const position = findOptimalPosition(importantBounds, widgetSize);

      expect(position.edge).not.toBe('bottom-right');
    });

    it('falls back to center when all corners blocked', () => {
      const widgetSize = { width: 400, height: 600 };
      const importantBounds: BoundingBox[] = [
        { x: 0, y: 460, width: 400, height: 200 },
        { x: 1520, y: 460, width: 400, height: 200 },
        { x: 0, y: 0, width: 400, height: 200 },
        { x: 1520, y: 0, width: 400, height: 200 },
      ];

      const position = findOptimalPosition(importantBounds, widgetSize);

      expect(position.edge).toBe('center');
    });
  });

  describe('constrainToViewport', () => {
    it('keeps position within viewport bounds', () => {
      const position = { x: -100, y: -100 };
      const widgetSize = { width: 400, height: 600 };

      const constrained = constrainToViewport(position, widgetSize);

      expect(constrained.x).toBeGreaterThanOrEqual(10);
      expect(constrained.y).toBeGreaterThanOrEqual(10);
    });

    it('keeps widget from going off right/bottom edge', () => {
      const position = { x: 2000, y: 1500 };
      const widgetSize = { width: 400, height: 600 };

      const constrained = constrainToViewport(position, widgetSize);

      expect(constrained.x).toBeLessThanOrEqual(1920 - 400 - 10);
      expect(constrained.y).toBeLessThanOrEqual(1080 - 600 - 10);
    });

    it('returns original position if already valid', () => {
      const position = { x: 500, y: 300 };
      const widgetSize = { width: 400, height: 600 };

      const constrained = constrainToViewport(position, widgetSize);

      expect(constrained.x).toBe(500);
      expect(constrained.y).toBe(300);
    });
  });

  describe('snapToEdge', () => {
    it('snaps to left edge when within threshold', () => {
      const position = { x: 15, y: 400 };
      const widgetSize = { width: 400, height: 600 };

      const snapped = snapToEdge(position, widgetSize);

      expect(snapped.x).toBe(10);
    });

    it('snaps to right edge when within threshold', () => {
      const position = { x: 1495, y: 400 };
      const widgetSize = { width: 400, height: 600 };

      const snapped = snapToEdge(position, widgetSize);

      expect(snapped.x).toBe(1920 - 400 - 10);
    });

    it('snaps to top edge when within threshold', () => {
      const position = { x: 500, y: 15 };
      const widgetSize = { width: 400, height: 600 };

      const snapped = snapToEdge(position, widgetSize);

      expect(snapped.y).toBe(10);
    });

    it('snaps to bottom edge when within threshold', () => {
      const position = { x: 500, y: 455 };
      const widgetSize = { width: 400, height: 600 };

      const snapped = snapToEdge(position, widgetSize);

      expect(snapped.y).toBe(1080 - 600 - 10);
    });

    it('does not snap when outside threshold', () => {
      const position = { x: 500, y: 400 };
      const widgetSize = { width: 400, height: 600 };

      const snapped = snapToEdge(position, widgetSize);

      expect(snapped.x).toBe(500);
      expect(snapped.y).toBe(400);
    });
  });

  describe('isMobileDevice', () => {
    it('returns true for narrow viewport', () => {
      Object.defineProperty(window, 'innerWidth', { value: 600, writable: true });
      Object.defineProperty(window, 'ontouchstart', { value: undefined, writable: true, configurable: true });
      expect(isMobileDevice()).toBe(true);
    });

    it('returns true when touch events supported', () => {
      Object.defineProperty(window, 'innerWidth', { value: 1024, writable: true });
      Object.defineProperty(window, 'ontouchstart', { value: {}, writable: true, configurable: true });
      expect(isMobileDevice()).toBe(true);
    });

    it('returns false for desktop', () => {
      Object.defineProperty(window, 'innerWidth', { value: 1920, writable: true });
      Object.defineProperty(window, 'ontouchstart', { value: undefined, writable: true, configurable: true });
      // @ts-expect-error - Testing environment cleanup
      delete (window as any).ontouchstart;
      expect(isMobileDevice()).toBe(false);
    });
  });

  describe('getMobilePosition', () => {
    it('returns centered position for mobile', () => {
      vi.stubGlobal('innerWidth', 375);
      vi.stubGlobal('innerHeight', 667);

      const position = getMobilePosition();

      expect(position.x).toBe(375 * 0.05);
      expect(position.y).toBe(667 * 0.15);
      expect(position.edge).toBe('center');
    });
  });

  describe('getMobileDimensions', () => {
    it('returns 90% width and 80% height', () => {
      const dims = getMobileDimensions();

      expect(dims.width).toBe('90%');
      expect(dims.height).toBe('80%');
    });
  });

  describe('debounce', () => {
    beforeEach(() => {
      vi.useFakeTimers();
    });

    afterEach(() => {
      vi.useRealTimers();
    });

    it('delays function execution', () => {
      const fn = vi.fn();
      const debounced = debounce(fn, 250);

      debounced();
      expect(fn).not.toHaveBeenCalled();

      vi.advanceTimersByTime(250);
      expect(fn).toHaveBeenCalledTimes(1);
    });

    it('cancels previous call on rapid invocation', () => {
      const fn = vi.fn();
      const debounced = debounce(fn, 250);

      debounced();
      vi.advanceTimersByTime(100);
      debounced();
      vi.advanceTimersByTime(100);
      debounced();
      vi.advanceTimersByTime(250);

      expect(fn).toHaveBeenCalledTimes(1);
    });
  });
});
