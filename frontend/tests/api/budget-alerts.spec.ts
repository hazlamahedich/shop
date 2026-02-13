/**
 * API Tests for Story 3-8: Budget Alert Notifications
 *
 * Tests the budget alerts and bot status API endpoints for:
 * - Budget alert creation and retrieval
 * - Bot pause/resume status management
 * - Alert deduplication logic
 * - Error handling for invalid requests
 *
 * Test Coverage Plan:
 * - [P0] Bot status endpoint returns correct pause state
 * - [P0] Bot resume endpoint clears pause state
 * - [P0] Budget alerts endpoint returns alerts
 * - [P1] Alert deduplication prevents duplicates
 * - [P1] Mark alert as read works
 * - [P2] Error handling for invalid requests
 *
 * @package frontend/tests/api
 */

import { test, expect } from '@playwright/test';

type ThresholdLevel = 80 | 100;

interface BudgetAlert {
  id: number;
  merchant_id: number;
  threshold: ThresholdLevel;
  message: string;
  created_at: string;
  is_read: boolean;
}

interface BotStatus {
  isPaused: boolean;
  pauseReason: string | null;
  budgetCap: number | null;
  monthlySpend: number;
  budgetPercentage: number | null;
}

const baseURL = process.env.API_BASE_URL || 'http://localhost:8000';

test.describe('Story 3-8: Budget Alerts API Tests', () => {
  test.describe('[P0] GET /api/merchant/bot-status', () => {
    test('[P0] should return bot status with required fields', async ({ request }) => {
      const response = await request.get(`${baseURL}/api/merchant/bot-status`);

      expect(response.status()).toBe(200);

      const json: BotStatus = await response.json();

      expect(json).toHaveProperty('isPaused');
      expect(json).toHaveProperty('pauseReason');
      expect(json).toHaveProperty('budgetCap');
      expect(json).toHaveProperty('monthlySpend');
      expect(json).toHaveProperty('budgetPercentage');
      expect(typeof json.isPaused).toBe('boolean');
    });

    test('[P0] should return isPaused=true when budget exceeded', async ({ request }) => {
      const response = await request.get(`${baseURL}/api/merchant/bot-status`);
      expect(response.status()).toBe(200);

      const json: BotStatus = await response.json();

      if (json.budgetCap !== null && json.budgetPercentage !== null && json.budgetPercentage >= 100) {
        expect(json.isPaused).toBe(true);
        expect(json.pauseReason).toBeTruthy();
      }
    });

    test('[P0] should return isPaused=false when under budget', async ({ request }) => {
      const response = await request.get(`${baseURL}/api/merchant/bot-status`);
      expect(response.status()).toBe(200);

      const json: BotStatus = await response.json();

      if (json.budgetCap === null || (json.budgetPercentage !== null && json.budgetPercentage < 100)) {
        expect(json.isPaused).toBe(false);
      }
    });

    test('[P0] should return isPaused=true when budget_cap is $0', async ({ request }) => {
      const response = await request.get(`${baseURL}/api/merchant/bot-status`);
      expect(response.status()).toBe(200);

      const json: BotStatus = await response.json();

      if (json.budgetCap === 0) {
        expect(json.isPaused).toBe(true);
        expect(json.pauseReason).toContain('$0');
      }
    });
  });

  test.describe('[P0] POST /api/merchant/bot/resume', () => {
    test('[P0] should resume bot when budget allows', async ({ request }) => {
      const botStatusResponse = await request.get(`${baseURL}/api/merchant/bot-status`);
      const status: BotStatus = await botStatusResponse.json();

      if (status.isPaused && status.budgetCap !== null && status.budgetPercentage !== null && status.budgetPercentage < 100) {
        const response = await request.post(`${baseURL}/api/merchant/bot/resume`);

        expect(response.status()).toBe(200);

        const json = await response.json();
        expect(json.success).toBe(true);
        expect(json.message).toContain('resumed');
      }
    });

    test('[P1] should fail to resume when budget still exceeded', async ({ request }) => {
      const botStatusResponse = await request.get(`${baseURL}/api/merchant/bot-status`);
      const status: BotStatus = await botStatusResponse.json();

      if (status.isPaused && status.budgetPercentage !== null && status.budgetPercentage >= 100) {
        const response = await request.post(`${baseURL}/api/merchant/bot/resume`);

        expect(response.status()).toBe(400);

        const json = await response.json();
        expect(json.error || json.message).toBeTruthy();
      }
    });
  });

  test.describe('[P0] GET /api/merchant/budget-alerts', () => {
    test('[P0] should return list of budget alerts', async ({ request }) => {
      const response = await request.get(`${baseURL}/api/merchant/budget-alerts`);

      expect(response.status()).toBe(200);

      const json = await response.json();
      expect(Array.isArray(json)).toBe(true);
    });

    test('[P0] should return alerts with required fields', async ({ request }) => {
      const response = await request.get(`${baseURL}/api/merchant/budget-alerts`);
      expect(response.status()).toBe(200);

      const alerts: BudgetAlert[] = await response.json();

      if (alerts.length > 0) {
        const alert = alerts[0];
        expect(alert).toHaveProperty('id');
        expect(alert).toHaveProperty('threshold');
        expect(alert).toHaveProperty('message');
        expect(alert).toHaveProperty('is_read');
        expect([80, 100]).toContain(alert.threshold);
      }
    });

    test('[P1] should only return unread alerts by default', async ({ request }) => {
      const response = await request.get(`${baseURL}/api/merchant/budget-alerts`);
      expect(response.status()).toBe(200);

      const alerts: BudgetAlert[] = await response.json();

      const allUnread = alerts.every((alert) => alert.is_read === false);
      expect(allUnread).toBe(true);
    });
  });

  test.describe('[P1] POST /api/merchant/budget-alerts/{id}/read', () => {
    test('[P1] should mark alert as read', async ({ request }) => {
      const listResponse = await request.get(`${baseURL}/api/merchant/budget-alerts`);
      const alerts: BudgetAlert[] = await listResponse.json();

      if (alerts.length > 0) {
        const alertId = alerts[0].id;
        const response = await request.post(`${baseURL}/api/merchant/budget-alerts/${alertId}/read`);

        expect(response.status()).toBe(200);

        const json = await response.json();
        expect(json.success).toBe(true);
      }
    });

    test('[P2] should return 404 for non-existent alert', async ({ request }) => {
      const response = await request.post(`${baseURL}/api/merchant/budget-alerts/999999/read`);

      expect(response.status()).toBe(404);
    });
  });

  test.describe('[P1] Alert Deduplication', () => {
    test('[P1] should not create duplicate alerts for same threshold', async ({ request }) => {
      const response = await request.get(`${baseURL}/api/merchant/budget-alerts`);
      const alerts: BudgetAlert[] = await response.json();

      const thresholdCounts = alerts.reduce(
        (acc, alert) => {
          acc[alert.threshold] = (acc[alert.threshold] || 0) + 1;
          return acc;
        },
        {} as Record<number, number>,
      );

      Object.values(thresholdCounts).forEach((count) => {
        expect(count).toBeLessThanOrEqual(1);
      });
    });
  });

  test.describe('[P2] Error Handling', () => {
    test('[P2] should handle invalid alert ID format', async ({ request }) => {
      const response = await request.post(`${baseURL}/api/merchant/budget-alerts/invalid/read`);

      expect([400, 404, 422]).toContain(response.status());
    });

    test('[P2] should return empty array when no alerts exist', async ({ request }) => {
      const response = await request.get(`${baseURL}/api/merchant/budget-alerts`);

      expect(response.status()).toBe(200);

      const alerts: BudgetAlert[] = await response.json();
      expect(Array.isArray(alerts)).toBe(true);
    });
  });
});
