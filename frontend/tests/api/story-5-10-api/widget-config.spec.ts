/**
 * Widget Configuration API Tests
 *
 * Story 5-10: Widget Full App Integration
 * Tests widget config endpoints and theme validation.
 *
 * @tags api widget story-5-10 config
 */

import { test, expect } from '@playwright/test';

const API_BASE = process.env.API_BASE_URL || 'http://localhost:8000';
const TEST_MERCHANT_ID = 1;

interface WidgetConfigResponse {
  data: {
    enabled: boolean;
    botName: string;
    welcomeMessage: string;
    theme: {
      primaryColor: string;
      backgroundColor: string;
      textColor: string;
      botBubbleColor: string;
      userBubbleColor: string;
      position: string;
      borderRadius: number;
      width: number;
      height: number;
      fontFamily: string;
      fontSize: number;
    };
  };
}

function getWidgetHeaders(testMode = true): Record<string, string> {
  return {
    'Content-Type': 'application/json',
    'X-Test-Mode': testMode ? 'true' : 'false',
  };
}

test.describe('Story 5-10: Widget Configuration [P0]', () => {
  test('[P0] GET /api/v1/widget/config should return valid widget config', async ({ request }) => {
    const configUrl = `${API_BASE}/api/v1/widget/config/${TEST_MERCHANT_ID}`;

    const response = await request.get(configUrl, {
      headers: getWidgetHeaders(),
    });

    expect(response.status()).toBe(200);

    const body: WidgetConfigResponse = await response.json();
    expect(body).toHaveProperty('data');
    expect(body.data).toHaveProperty('enabled');
    expect(body.data).toHaveProperty('botName');
    expect(body.data).toHaveProperty('welcomeMessage');
    expect(body.data).toHaveProperty('theme');

    expect(typeof body.data.enabled).toBe('boolean');
    expect(typeof body.data.botName).toBe('string');
    expect(typeof body.data.welcomeMessage).toBe('string');
  });

  test('[P0] GET /api/v1/widget/config should return valid theme', async ({ request }) => {
    const configUrl = `${API_BASE}/api/v1/widget/config/${TEST_MERCHANT_ID}`;

    const response = await request.get(configUrl, {
      headers: getWidgetHeaders(),
    });

    expect(response.status()).toBe(200);

    const body: WidgetConfigResponse = await response.json();
    const theme = body.data.theme;

    expect(theme).toHaveProperty('primaryColor');
    expect(theme).toHaveProperty('backgroundColor');
    expect(theme).toHaveProperty('textColor');
    expect(theme.primaryColor).toMatch(/^#[0-9a-fA-F]{6}$/);
  });

  test('[P1] GET /api/v1/widget/config should handle invalid merchant', async ({ request }) => {
    const configUrl = `${API_BASE}/api/v1/widget/config/99999`;

    const response = await request.get(configUrl, {
      headers: getWidgetHeaders(),
    });

    expect([404, 400]).toContain(response.status());
  });

  test('[P2] GET /api/v1/widget/config should validate theme dimensions bounds', async ({ request }) => {
    const configUrl = `${API_BASE}/api/v1/widget/config/${TEST_MERCHANT_ID}`;

    const response = await request.get(configUrl, {
      headers: getWidgetHeaders(),
    });

    if (response.status() === 200) {
      const body: WidgetConfigResponse = await response.json();
      const theme = body.data.theme;

      expect(theme.width).toBeGreaterThanOrEqual(280);
      expect(theme.width).toBeLessThanOrEqual(500);
      expect(theme.height).toBeGreaterThanOrEqual(400);
      expect(theme.height).toBeLessThanOrEqual(800);
      expect(theme.borderRadius).toBeGreaterThanOrEqual(0);
      expect(theme.borderRadius).toBeLessThanOrEqual(30);
      expect(theme.fontSize).toBeGreaterThanOrEqual(12);
      expect(theme.fontSize).toBeLessThanOrEqual(20);
    }
  });
});
