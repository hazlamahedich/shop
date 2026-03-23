import type { WidgetPosition, PositioningConfig } from '../types/widget';
import { DEFAULT_POSITIONING_CONFIG } from '../types/widget';

export interface BoundingBox {
  x: number;
  y: number;
  width: number;
  height: number;
}

const CTA_PATTERN = /buy|cart|checkout|order|shop|purchase|add\s*to\s*cart|buy\s*now|get\s*started|sign\s*up|subscribe/i;

export function detectImportantElements(customSelectors?: string[]): Element[] {
  const elements: Element[] = [];
  
  const selectors = customSelectors || ['[data-important="true"]'];
  
  for (const selector of selectors) {
    try {
      const matched = document.querySelectorAll(selector);
      elements.push(...Array.from(matched));
    } catch {
      // Invalid selector, skip
    }
  }
  
  const allElements = document.querySelectorAll('*');
  for (const el of allElements) {
    const style = window.getComputedStyle(el);
    const zIndex = parseInt(style.zIndex, 10);
    if (!isNaN(zIndex) && zIndex > 100) {
      if (!elements.includes(el)) {
        elements.push(el);
      }
    }
  }
  
  const buttons = document.querySelectorAll('button, a[role="button"], input[type="submit"], input[type="button"]');
  for (const btn of buttons) {
    const text = btn.textContent || '';
    const ariaLabel = btn.getAttribute('aria-label') || '';
    if (CTA_PATTERN.test(text) || CTA_PATTERN.test(ariaLabel)) {
      if (!elements.includes(btn)) {
        elements.push(btn);
      }
    }
  }
  
  return elements;
}

export function getElementBounds(element: Element): BoundingBox {
  const rect = element.getBoundingClientRect();
  return {
    x: rect.left,
    y: rect.top,
    width: rect.width,
    height: rect.height,
  };
}

export function checkCollision(rect1: BoundingBox, rect2: BoundingBox, minClearance: number = 0): boolean {
  const expanded1 = {
    x: rect1.x - minClearance,
    y: rect1.y - minClearance,
    width: rect1.width + minClearance * 2,
    height: rect1.height + minClearance * 2,
  };
  
  return !(
    expanded1.x + expanded1.width <= rect2.x ||
    rect2.x + rect2.width <= expanded1.x ||
    expanded1.y + expanded1.height <= rect2.y ||
    rect2.y + rect2.height <= expanded1.y
  );
}

export function findOptimalPosition(
  importantBounds: BoundingBox[],
  widgetSize: { width: number; height: number },
  config: PositioningConfig = DEFAULT_POSITIONING_CONFIG
): WidgetPosition {
  const viewport: BoundingBox = {
    x: 0,
    y: 0,
    width: typeof window !== 'undefined' ? window.innerWidth : 1920,
    height: typeof window !== 'undefined' ? window.innerHeight : 1080,
  };
  
  const { minClearance, viewportPadding } = config;
  
  const positions: Array<{ edge: WidgetPosition['edge']; x: number; y: number }> = [
    {
      edge: 'bottom-right',
      x: viewport.width - widgetSize.width - viewportPadding,
      y: viewport.height - widgetSize.height - viewportPadding,
    },
    {
      edge: 'bottom-left',
      x: viewportPadding,
      y: viewport.height - widgetSize.height - viewportPadding,
    },
    {
      edge: 'top-right',
      x: viewport.width - widgetSize.width - viewportPadding,
      y: viewportPadding,
    },
    {
      edge: 'top-left',
      x: viewportPadding,
      y: viewportPadding,
    },
  ];
  
  for (const pos of positions) {
    const widgetBounds: BoundingBox = {
      x: pos.x,
      y: pos.y,
      width: widgetSize.width,
      height: widgetSize.height,
    };
    
    const hasCollision = importantBounds.some((bound) =>
      checkCollision(widgetBounds, bound, minClearance)
    );
    
    if (!hasCollision) {
      return { x: pos.x, y: pos.y, edge: pos.edge };
    }
  }
  
  return {
    x: Math.max(0, (viewport.width - widgetSize.width) / 2),
    y: Math.max(0, (viewport.height - widgetSize.height) / 2),
  };

}

export function constrainToViewport(
  position: WidgetPosition,
  widgetSize: { width: number; height: number },
  config: PositioningConfig = DEFAULT_POSITIONING_CONFIG
 ): WidgetPosition {
  if (typeof window === 'undefined') return position;
  
  const { viewportPadding } = config;
  const minX = viewportPadding;
  const maxX = Math.max(0, window.innerWidth - widgetSize.width - viewportPadding);
  const minY = viewportPadding;
  const maxY = Math.max(0, window.innerHeight - widgetSize.height - viewportPadding);
  
  return {
    ...position,
    x: Math.max(minX, Math.min(position.x, maxX)),
    y: Math.max(minY, Math.min(position.y, maxY)),
  };
}

export function snapToEdge(
  position: WidgetPosition,
  widgetSize: { width: number; height: number },
  config: PositioningConfig = DEFAULT_POSITIONING_CONFIG
): WidgetPosition {
  if (typeof window === 'undefined') return position;
  
  const { edgeSnapThreshold, viewportPadding } = config;
  let { x, y } = position;
  let edge = position.edge;
  
  if (x < edgeSnapThreshold) {
    x = viewportPadding;
    edge = edge?.includes('right') ? edge.replace('right', 'left') as WidgetPosition['edge'] : 'bottom-left';
  } else if (x > window.innerWidth - widgetSize.width - edgeSnapThreshold) {
    x = window.innerWidth - widgetSize.width - viewportPadding;
    edge = edge?.includes('left') ? edge.replace('left', 'right') as WidgetPosition['edge'] : 'bottom-right';
  }
  
  if (y < edgeSnapThreshold) {
    y = viewportPadding;
    edge = edge?.includes('bottom') ? edge.replace('bottom', 'top') as WidgetPosition['edge'] : 'top-right';
  } else if (y > window.innerHeight - widgetSize.height - edgeSnapThreshold) {
    y = window.innerHeight - widgetSize.height - viewportPadding;
    edge = edge?.includes('top') ? edge.replace('top', 'bottom') as WidgetPosition['edge'] : 'bottom-right';
  }
  
  return { x, y, edge };
}

export function isMobileDevice(): boolean {
  if (typeof window === 'undefined') return false;
  return window.innerWidth < 768 || 'ontouchstart' in window;
}

export function getMobilePosition(): WidgetPosition {
  return {
    x: window.innerWidth * 0.05,
    y: window.innerHeight * 0.15,
    edge: 'center',
  };
}

export function getMobileDimensions(): { width: string; height: string } {
  return {
    width: '90%',
    height: '80%',
  };
}

export function debounce<T extends (...args: unknown[]) => unknown>(
  fn: T,
  delay: number
): (...args: Parameters<T>) => void {
  let timeoutId: ReturnType<typeof setTimeout> | null = null;
  
  return (...args: Parameters<T>) => {
    if (timeoutId) {
      clearTimeout(timeoutId);
    }
    timeoutId = setTimeout(() => {
      fn(...args);
    }, delay);
  };
}
