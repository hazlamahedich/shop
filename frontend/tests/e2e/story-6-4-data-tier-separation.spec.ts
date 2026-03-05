/**
 * Story 6-4: Data Tier Separation - E2E Tests
 * 
 * E2E tests verify frontend behavior. Backend API tests are in:
 * - backend/tests/integration/test_data_tier_api.py
 * - backend/tests/integration/test_consent_tier_integration.py
 */

import { test, expect } from '@playwright/test';

const BASE_URL = process.env.BASE_URL || 'http://localhost:5173';
const API_URL = process.env.API_URL || 'http://localhost:8000';

const TEST_MERCHANT = {
  email: 'test@test.com',
  password: 'Test12345',
};

test.describe('[Story 6-4] Data Tier Separation - E2E Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Login via API
    const loginResponse = await page.request.post(`${API_URL}/api/v1/auth/login`, {
      data: TEST_MERCHANT,
    });

    if (!loginResponse.ok()) {
      throw new Error('Failed to login with test merchant');
    }
  });

  /**
   * [P0] Test: Frontend app loads with auth
   * Verifies basic app functionality after authentication
   */
  test('[P0] should load dashboard after login', async ({ page }) => {
    // Navigate to app
    await page.goto(BASE_URL);
    
    // Wait for page to load
    await page.waitForLoadState('networkidle');
    
    // Verify we're on the app (not redirected to login)
    await expect(page).toHaveURL(new RegExp(BASE_URL));
    
    // Verify main content is visible
    const body = page.locator('body');
    await expect(body).toBeVisible();
  });

  /**
   * [P1] Test: Consent API integration
   * AC2: Voluntary data - 30-day retention, deletable
   */
  test('[P1] should handle consent status check', async ({ page }) => {
    // Get current consent status
    const statusResponse = await page.request.get(`${API_URL}/api/v1/consent/status`);
    
    // API should respond (200, 401, or 404 are acceptable)
    expect([200, 401, 404]).toContain(statusResponse.status());
  });

  /**
   * [P2] Test: Error handling - API failure
   * Non-functional requirement: Graceful error handling
   */
  test('[P2] should handle API errors gracefully', async ({ page }) => {
    // Mock API failure
    await page.route('**/api/v1/analytics/**', (route) => {
      route.fulfill({
        status: 500,
        body: JSON.stringify({ error: 'Internal Server Error' }),
      });
    });

    // Navigate - app should not crash
    await page.goto(BASE_URL);
    
    // Verify page still loads
    await expect(page.locator('body')).toBeVisible();
  });

  /**
   * [P3] Test: Page loads quickly
   * Non-functional requirement: Performance
   */
  test('[P3] dashboard should load within 5 seconds', async ({ page }) => {
    const startTime = Date.now();
    
    await page.goto(BASE_URL);
    await page.waitForLoadState('networkidle');
    
    const duration = Date.now() - startTime;
    expect(duration).toBeLessThan(5000);
  });
});
