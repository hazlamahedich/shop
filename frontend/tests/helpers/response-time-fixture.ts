import { Page } from '@playwright/test';

export interface ResponseTimePercentiles {
  p50: number | null;
  p95: number | null;
  p99: number | null;
}

export interface ResponseTimeHistogramBucket {
  label: string;
  count: number;
  color: 'green' | 'yellow' | 'red';
}

export interface ResponseTimeData {
  percentiles: ResponseTimePercentiles;
  histogram: ResponseTimeHistogramBucket[];
  previousPeriod?: {
    percentiles: ResponseTimePercentiles;
    comparison?: {
      p50?: { deltaMs: number; deltaPercent: number; trend: 'improving' | 'degrading' | 'stable' } | null;
      p95?: { deltaMs: number; deltaPercent: number; trend: 'improving' | 'degrading' | 'stable' } | null;
      p99?: { deltaMs: number; deltaPercent: number; trend: 'improving' | 'degrading' | 'stable' } | null;
    } | null;
  };
  responseTypeBreakdown?: {
    rag: ResponseTimePercentiles | null;
    general: ResponseTimePercentiles | null;
  } | null;
  warning?: {
    show: boolean;
    message: string;
    severity: 'warning' | 'critical';
  } | null;
  lastUpdated: string;
  period: string;
  count: number;
}

export interface MockResponseTimeData {
  percentiles?: ResponseTimePercentiles;
  histogram?: ResponseTimeHistogramBucket[];
  previousPeriod?: ResponseTimeData['previousPeriod'];
  responseTypeBreakdown?: ResponseTimeData['responseTypeBreakdown'];
  warning?: ResponseTimeData['warning'];
  count?: number;
}

const DEFAULT_RESPONSE_TIME_DATA: ResponseTimeData = {
  percentiles: { p50: 850, p95: 2100, p99: 4500 },
  histogram: [
    { label: '0-1s', count: 150, color: 'green' },
    { label: '1-2s', count: 80, color: 'green' },
    { label: '2-3s', count: 45, color: 'green' },
    { label: '3-5s', count: 20, color: 'yellow' },
    { label: '5s+', count: 5, color: 'red' },
  ],
  previousPeriod: {
    percentiles: { p50: 800, p95: 1800, p99: 4200 },
    comparison: {
      p50: { deltaMs: 50, deltaPercent: 6.3, trend: 'degrading' },
      p95: { deltaMs: 300, deltaPercent: 16.7, trend: 'degrading' },
      p99: { deltaMs: 300, deltaPercent: 7.1, trend: 'degrading' },
    },
  },
  warning: null,
  lastUpdated: new Date().toISOString(),
  period: '7d',
  count: 300,
};

/**
 * Mock the Response Time Distribution API response
 * @param page - Playwright Page object
 * @param overrides - Partial data to override defaults
 */
export async function mockResponseTimeApi(
  page: Page,
  overrides?: MockResponseTimeData
): Promise<void> {
  const data: ResponseTimeData = {
    ...DEFAULT_RESPONSE_TIME_DATA,
    ...overrides,
  };

  await page.route('**/api/v1/analytics/response-time-distribution**', (route) => {
    return route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        data: data,
        meta: {
          request_id: 'test-request-id',
          timestamp: new Date().toISOString(),
        },
      }),
    });
  });
}
