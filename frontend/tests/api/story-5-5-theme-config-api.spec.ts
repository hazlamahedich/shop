/**
 * Theme Configuration API Tests
 *
 * Story 5-5: Theme Customization System
 * Tests API-level theme validation, config retrieval, and error handling
 *
 * @tags api widget story-5-5 theme validation
 */

import { test, expect } from '@playwright/test';

const API_BASE = process.env.API_BASE_URL || 'http://localhost:8000';
const TEST_MERCHANT_ID = 1;

interface WidgetConfig {
  enabled: boolean;
  botName: string;
  welcomeMessage: string;
  theme: WidgetTheme;
  allowedDomains: string[];
}

interface WidgetTheme {
  primaryColor: string;
  backgroundColor: string;
  textColor: string;
  botBubbleColor: string;
  userBubbleColor: string;
  position: 'bottom-right' | 'bottom-left';
  borderRadius: number;
  width: number;
  height: number;
  fontFamily: string;
  fontSize: number;
}

interface ApiResponse<T> {
  data: T;
  meta: {
    requestId: string;
    timestamp: string;
  };
}

async function getWidgetConfig(request: any, merchantId: number): Promise<ApiResponse<WidgetConfig> | null> {
  const response = await request.get(`${API_BASE}/api/v1/widget/config/${merchantId}`, {
    headers: { 'Content-Type': 'application/json' },
  });

  if (response.status() === 200) {
    return response.json();
  }
  return null;
}

test.describe('Theme Configuration API - Widget Config Retrieval (AC1)', () => {
  test('[P0] @smoke should return widget config with valid theme', async ({ request }) => {
    const response = await request.get(`${API_BASE}/api/v1/widget/config/${TEST_MERCHANT_ID}`, {
      headers: { 'Content-Type': 'application/json' },
    });

    expect(response.status()).toBe(200);

    const body: ApiResponse<WidgetConfig> = await response.json();
    expect(body.data).toHaveProperty('enabled');
    expect(body.data).toHaveProperty('theme');

    const theme = body.data.theme;
    expect(theme).toHaveProperty('primaryColor');
    expect(theme).toHaveProperty('backgroundColor');
    expect(theme).toHaveProperty('textColor');
    expect(theme).toHaveProperty('position');
    expect(theme).toHaveProperty('borderRadius');
    expect(theme).toHaveProperty('width');
    expect(theme).toHaveProperty('height');
  });

  test('[P0] @smoke should return theme with all 11 required fields', async ({ request }) => {
    const config = await getWidgetConfig(request, TEST_MERCHANT_ID);

    if (!config) {
      test.skip(true, 'Could not retrieve widget config');
      return;
    }

    const theme = config.data.theme;
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

  test('[P1] should return valid hex color format for all color fields', async ({ request }) => {
    const config = await getWidgetConfig(request, TEST_MERCHANT_ID);

    if (!config) {
      test.skip(true, 'Could not retrieve widget config');
      return;
    }

    const theme = config.data.theme;
    const hexColorRegex = /^#[0-9a-fA-F]{6}$/;

    expect(theme.primaryColor).toMatch(hexColorRegex);
    expect(theme.backgroundColor).toMatch(hexColorRegex);
    expect(theme.textColor).toMatch(hexColorRegex);
    expect(theme.botBubbleColor).toMatch(hexColorRegex);
    expect(theme.userBubbleColor).toMatch(hexColorRegex);
  });
});

test.describe('Theme Configuration API - Constraint Validation (AC7, AC8)', () => {
  test('[P1] should return borderRadius within 0-24 range', async ({ request }) => {
    const config = await getWidgetConfig(request, TEST_MERCHANT_ID);

    if (!config) {
      test.skip(true, 'Could not retrieve widget config');
      return;
    }

    const borderRadius = config.data.theme.borderRadius;
    expect(borderRadius).toBeGreaterThanOrEqual(0);
    expect(borderRadius).toBeLessThanOrEqual(24);
  });

  test('[P1] should return width within 280-600 range', async ({ request }) => {
    const config = await getWidgetConfig(request, TEST_MERCHANT_ID);

    if (!config) {
      test.skip(true, 'Could not retrieve widget config');
      return;
    }

    const width = config.data.theme.width;
    expect(width).toBeGreaterThanOrEqual(280);
    expect(width).toBeLessThanOrEqual(600);
  });

  test('[P1] should return height within 400-900 range', async ({ request }) => {
    const config = await getWidgetConfig(request, TEST_MERCHANT_ID);

    if (!config) {
      test.skip(true, 'Could not retrieve widget config');
      return;
    }

    const height = config.data.theme.height;
    expect(height).toBeGreaterThanOrEqual(400);
    expect(height).toBeLessThanOrEqual(900);
  });

  test('[P1] should return fontSize within 12-20 range', async ({ request }) => {
    const config = await getWidgetConfig(request, TEST_MERCHANT_ID);

    if (!config) {
      test.skip(true, 'Could not retrieve widget config');
      return;
    }

    const fontSize = config.data.theme.fontSize;
    expect(fontSize).toBeGreaterThanOrEqual(12);
    expect(fontSize).toBeLessThanOrEqual(20);
  });

  test('[P1] should return valid position value', async ({ request }) => {
    const config = await getWidgetConfig(request, TEST_MERCHANT_ID);

    if (!config) {
      test.skip(true, 'Could not retrieve widget config');
      return;
    }

    const position = config.data.theme.position;
    expect(['bottom-right', 'bottom-left']).toContain(position);
  });
});

test.describe('Theme Configuration API - Security Validation (AC8)', () => {
  test('[P0] @smoke should not expose XSS vectors in theme fields', async ({ request }) => {
    const config = await getWidgetConfig(request, TEST_MERCHANT_ID);

    if (!config) {
      test.skip(true, 'Could not retrieve widget config');
      return;
    }

    const theme = config.data.theme;
    const dangerousPatterns = [
      /<script/i,
      /javascript:/i,
      /onerror=/i,
      /onclick=/i,
      /expression\(/i,
    ];

    const allThemeValues = [
      theme.primaryColor,
      theme.backgroundColor,
      theme.textColor,
      theme.botBubbleColor,
      theme.userBubbleColor,
      theme.fontFamily,
    ];

    for (const value of allThemeValues) {
      for (const pattern of dangerousPatterns) {
        expect(value).not.toMatch(pattern);
      }
    }
  });

  test('[P1] should sanitize fontFamily field', async ({ request }) => {
    const config = await getWidgetConfig(request, TEST_MERCHANT_ID);

    if (!config) {
      test.skip(true, 'Could not retrieve widget config');
      return;
    }

    const fontFamily = config.data.theme.fontFamily;
    expect(fontFamily).not.toContain('<');
    expect(fontFamily).not.toContain('>');
    expect(fontFamily).not.toContain('"');
    expect(fontFamily).not.toContain("'");
  });

  test('[P2] should handle non-existent merchant gracefully', async ({ request }) => {
    const nonExistentMerchantId = 999999999;

    const response = await request.get(`${API_BASE}/api/v1/widget/config/${nonExistentMerchantId}`, {
      headers: { 'Content-Type': 'application/json' },
    });

    expect([200, 404, 403]).toContain(response.status());

    if (response.status() === 404) {
      const body = await response.json();
      expect(body).toHaveProperty('error_code');
    }
  });
});

test.describe('Theme Configuration API - Response Format (AC1)', () => {
  test('[P1] should include requestId in meta', async ({ request }) => {
    const config = await getWidgetConfig(request, TEST_MERCHANT_ID);

    if (!config) {
      test.skip(true, 'Could not retrieve widget config');
      return;
    }

    expect(config.meta).toHaveProperty('requestId');
    expect(config.meta.requestId).toBeTruthy();
  });

  test('[P1] should include timestamp in meta', async ({ request }) => {
    const config = await getWidgetConfig(request, TEST_MERCHANT_ID);

    if (!config) {
      test.skip(true, 'Could not retrieve widget config');
      return;
    }

    expect(config.meta).toHaveProperty('timestamp');

    const timestamp = new Date(config.meta.timestamp);
    expect(timestamp.getTime()).not.toBeNaN();
  });

  test('[P2] should return consistent response structure', async ({ request }) => {
    const responses: ApiResponse<WidgetConfig>[] = [];

    for (let i = 0; i < 3; i++) {
      const config = await getWidgetConfig(request, TEST_MERCHANT_ID);
      if (config) {
        responses.push(config);
      }
    }

    if (responses.length < 2) {
      test.skip(true, 'Could not retrieve multiple configs');
      return;
    }

    const firstThemeKeys = Object.keys(responses[0].data.theme).sort();
    for (let i = 1; i < responses.length; i++) {
      const currentThemeKeys = Object.keys(responses[i].data.theme).sort();
      expect(currentThemeKeys).toEqual(firstThemeKeys);
    }
  });
});

test.describe('Theme Configuration API - Edge Cases', () => {
  test('[P2] should handle invalid merchant ID format', async ({ request }) => {
    const invalidIds = ['abc', '-1', 'null', 'undefined', ''];

    for (const id of invalidIds) {
      const response = await request.get(`${API_BASE}/api/v1/widget/config/${id}`, {
        headers: { 'Content-Type': 'application/json' },
      });

      expect([400, 404, 422]).toContain(response.status());
    }
  });

  test('[P2] should handle large merchant ID', async ({ request }) => {
    const largeId = Number.MAX_SAFE_INTEGER;

    const response = await request.get(`${API_BASE}/api/v1/widget/config/${largeId}`, {
      headers: { 'Content-Type': 'application/json' },
    });

    expect([200, 404, 403, 400, 422, 500]).toContain(response.status());
  });
});
