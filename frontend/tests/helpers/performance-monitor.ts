/**
 * Performance Monitor Helper
 *
 * Measures and validates performance metrics for E2E tests.
 * Establishes baseline assertions for page load and interaction timing.
 *
 * Usage:
 * ```ts
 * import { measurePageLoad, measureInteraction } from '../helpers/performance-monitor';
 *
 * const metrics = await measurePageLoad(page);
 * expect(metrics.domContentLoaded).toBeLessThan(2000);
 * ```
 */

import { Page, Locator } from '@playwright/test';

export interface PageLoadMetrics {
  // Navigation timing
  domContentLoaded: number; // DOM ready time
  loadComplete: number; // Full page load time
  firstPaint: number | null;
  firstContentfulPaint: number | null;

  // Resource timing
  totalResources: number;
  largestResource: number;
}

export interface InteractionMetrics {
  interactionTime: number; // Time from action to response
  renderTime: number; // Time to render updated UI
  totalTime: number; // Total interaction latency
}

/**
 * Measure page load performance
 * Captures key navigation timing metrics
 */
export async function measurePageLoad(page: Page): Promise<PageLoadMetrics> {
  const metrics = await page.evaluate(() => {
    const perfData = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;

    return {
      domContentLoaded: perfData.domContentLoadedEventEnd - perfData.domContentLoadedEventStart,
      loadComplete: perfData.loadEventEnd - perfData.loadEventStart,
      firstPaint: null,
      firstContentfulPaint: null,
    };
  });

  // Get paint metrics
  const paintMetrics = await page.evaluate(() => {
    const paints = performance.getEntriesByType('paint');
    const fp = paints.find((p) => p.name === 'first-paint');
    const fcp = paints.find((p) => p.name === 'first-contentful-paint');
    return {
      firstPaint: fp?.startTime ?? null,
      firstContentfulPaint: fcp?.startTime ?? null,
    };
  });

  // Get resource metrics
  const resourceMetrics = await page.evaluate(() => {
    const resources = performance.getEntriesByType('resource');
    const sizes = resources.map((r) => (r as PerformanceResourceTiming).transferSize).filter(Boolean);
    return {
      totalResources: resources.length,
      largestResource: Math.max(0, ...sizes),
    };
  });

  return {
    ...metrics,
    ...paintMetrics,
    ...resourceMetrics,
  };
}

/**
 * Measure interaction performance
 * Times user actions and UI responses
 */
export async function measureInteraction(
  page: Page,
  action: () => Promise<void>,
  responseLocator: Locator
): Promise<InteractionMetrics> {
  const startTime = Date.now();

  // Perform the action
  await action();

  // Wait for response indicator
  const interactionTime = Date.now() - startTime;

  // Wait for UI update/render
  await responseLocator.waitFor({ state: 'attached' });
  const renderTime = Date.now() - startTime - interactionTime;

  return {
    interactionTime,
    renderTime,
    totalTime: interactionTime + renderTime,
  };
}

/**
 * Assert page load meets baseline performance
 * Adjust thresholds based on your application
 */
export async function assertPageLoadBaseline(
  page: Page,
  thresholds: {
    domContentLoaded?: number;
    loadComplete?: number;
  } = {}
): Promise<void> {
  const defaults = {
    domContentLoaded: 2000, // 2 seconds
    loadComplete: 5000, // 5 seconds
  };

  const limits = { ...defaults, ...thresholds };
  const metrics = await measurePageLoad(page);

  const errors: string[] = [];

  if (metrics.domContentLoaded > limits.domContentLoaded) {
    errors.push(
      `DOM Content Loaded ${metrics.domContentLoaded}ms exceeds threshold ${limits.domContentLoaded}ms`
    );
  }

  if (metrics.loadComplete > limits.loadComplete) {
    errors.push(`Page Load ${metrics.loadComplete}ms exceeds threshold ${limits.loadComplete}ms`);
  }

  if (errors.length > 0) {
    throw new Error(`Performance baseline exceeded:\n${errors.join('\n')}`);
  }
}

/**
 * Assert interaction meets baseline performance
 */
export async function assertInteractionBaseline(
  page: Page,
  action: () => Promise<void>,
  responseLocator: Locator,
  threshold: number = 1000 // 1 second default
): Promise<void> {
  const metrics = await measureInteraction(page, action, responseLocator);

  if (metrics.totalTime > threshold) {
    throw new Error(
      `Interaction time ${metrics.totalTime}ms exceeds threshold ${threshold}ms ` +
        `(action: ${metrics.interactionTime}ms, render: ${metrics.renderTime}ms)`
    );
  }
}

/**
 * Create a performance trace
 * Saves detailed trace data for analysis
 */
export async function createPerformanceTrace(page: Page, testName: string): Promise<void> {
  // Start tracing
  await page.context().tracing.start({ screenshots: true, snapshots: true });

  // Collect metrics after a short delay
  await page.waitForTimeout(100);

  // Stop tracing and save
  const tracePath = `test-results/traces/${testName}-trace.zip`;
  await page.context().tracing.stop({ path: tracePath });
}

/**
 * Get Web Vitals metrics
 * LCP, FID, CLS (Core Web Vitals)
 */
export async function getWebVitals(page: Page): Promise<{
  lcp: number | null;
  fid: number | null;
  cls: number | null;
}> {
  return await page.evaluate(() => {
    // LCP (Largest Contentful Paint)
    let lcp = null;
    new PerformanceObserver((list) => {
      const entries = list.getEntries();
      const lastEntry = entries[entries.length - 1] as { startTime: number };
      lcp = lastEntry.startTime;
    }).observe({ entryTypes: ['largest-contentful-paint'] });

    // FID (First Input Delay) - requires user interaction
    let fid = null;
    new PerformanceObserver((list) => {
      const entries = list.getEntries();
      (entries[0] as { processingStart: number; startTime: number })?.processingStart;
      fid = (entries[0] as { processingStart: number; startTime: number }).processingStart -
            (entries[0] as { processingStart: number; startTime: number }).startTime;
    }).observe({ entryTypes: ['first-input'] });

    // CLS (Cumulative Layout Shift)
    let cls = 0;
    let clsValue = 0;
    new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        if (!(entry as { hadRecentInput: boolean }).hadRecentInput) {
          clsValue += (entry as { value: number }).value;
          cls = clsValue;
        }
      }
    }).observe({ entryTypes: ['layout-shift'] });

    return { lcp, fid, cls };
  });
}

/**
 * Performance baseline defaults
 * Adjust these based on your application's requirements
 */
export const PERFORMANCE_BASELINES = {
  // Page load thresholds (milliseconds)
  domContentLoaded: 2000,
  loadComplete: 5000,
  firstPaint: 1000,
  firstContentfulPaint: 1800,

  // Interaction thresholds (milliseconds)
  clickResponse: 100,
  formSubmission: 500,
  pageNavigation: 300,

  // Web Vitals thresholds
  lcp: 2500, // Good: <2.5s
  fid: 100, // Good: <100ms
  cls: 0.1, // Good: <0.1
} as const;
