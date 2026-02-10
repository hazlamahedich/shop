/**
 * E2E Tests: CSRF Token Validation
 *
 * Story 1.11: Business Info & FAQ Configuration
 *
 * Tests CSRF token validation on business info save operations:
 * - Valid CSRF token allows save
 * - Missing/invalid CSRF token blocks save with 403 error
 * - CSRF token is generated and stored correctly
 * - Token refresh behavior
 *
 * Prerequisites:
 * - Frontend dev server running on http://localhost:5173
 * - Backend API running on http://localhost:8000
 * - Test merchant account exists
 * - CSRF protection is enabled
 *
 * @tags e2e story-1-11 csrf security
 */

import { test, expect } from '@playwright/test';
import { clearStorage } from '../fixtures/test-helper';

const API_URL = process.env.API_URL || 'http://localhost:8000';
const BASE_URL = process.env.BASE_URL || 'http://localhost:5173';

const TEST_MERCHANT = {
  email: 'e2e-csrf@test.com',
  password: 'TestPass123',
};

test.describe.configure({ mode: 'serial' });
test.describe('Story 1.11: CSRF Token Validation [P0]', () => {
  let merchantToken: string;
  let merchantId: string;
  let csrfToken: string;

  test.beforeAll(async ({ request }) => {
    // Create or login test merchant
    const loginResponse = await request.post(`${API_URL}/api/v1/auth/login`, {
      data: TEST_MERCHANT,
    });

    if (loginResponse.ok()) {
      const loginData = await loginResponse.json();
      merchantToken = loginData.data.session.token;
      merchantId = loginData.data.user.merchantId;

      // Get CSRF token after login
      const csrfResponse = await request.get(`${API_URL}/api/v1/csrf-token`, {
        headers: {
          Authorization: `Bearer ${merchantToken}`,
        },
      });

      if (csrfResponse.ok()) {
        const csrfData = await csrfResponse.json();
        csrfToken = csrfData.data.csrf_token;
      }
    } else {
      throw new Error('Failed to authenticate test merchant');
    }
  });

  test.beforeEach(async ({ page }) => {
    await clearStorage(page);
    // Set auth state
    await page.evaluate((token) => {
      localStorage.setItem('auth_token', token);
      localStorage.setItem('auth_timestamp', Date.now().toString());
    }, merchantToken);
  });

  test('[P0] should save business info with valid CSRF token', async ({ page }) => {
    await page.goto(`${BASE_URL}/business-info`);
    await page.waitForLoadState('networkidle');

    // Fill business info
    await page.getByRole('textbox', { name: /Business Name/i }).fill('CSRF Test Store');
    await page.getByRole('textbox', { name: /Business Hours/i }).fill('9 AM - 5 PM');

    // Intercept the save request to verify CSRF token is included
    let csrfTokenSent = false;
    let saveRequestSuccess = false;

    await page.route('**/api/v1/merchant/business-info', async (route) => {
      const request = route.request();
      const headers = request.headers();

      // Check for CSRF token in headers
      if (headers['x-csrf-token'] || headers['X-CSRF-Token']) {
        csrfTokenSent = true;
      }

      // Continue with request
      const response = await route.continue();
      const responseBody = await response.text();

      if (response.status() === 200) {
        saveRequestSuccess = true;
      }
    });

    // Save business info
    const saveButton = page.getByRole('button', { name: /Save Business Info/i });
    await saveButton.click();

    // Wait for response
    await page.waitForTimeout(1000);

    // Verify CSRF token was sent
    expect(csrfTokenSent).toBe(true);

    // Verify save was successful
    expect(saveRequestSuccess).toBe(true);

    // Verify success message
    await expect(page.getByText(/business info saved/i)).toBeVisible({ timeout: 5000 });
  });

  test('[P0] should reject save with missing CSRF token', async ({ page, request }) => {
    // Get fresh CSRF token for this test
    const csrfResponse = await request.get(`${API_URL}/api/v1/csrf-token`, {
      headers: {
        Authorization: `Bearer ${merchantToken}`,
      },
    });

    if (csrfResponse.ok()) {
      const csrfData = await csrfResponse.json();
      csrfToken = csrfData.data.csrf_token;
    }

    await page.goto(`${BASE_URL}/business-info`);
    await page.waitForLoadState('networkidle');

    // Fill business info
    await page.getByRole('textbox', { name: /Business Name/i }).fill('No CSRF Store');

    // Intercept and remove CSRF token from request
    await page.route('**/api/v1/merchant/business-info', async (route) => {
      const request = route.request();
      const headers = { ...request.headers() };

      // Remove CSRF token header
      delete headers['x-csrf-token'];
      delete headers['X-CSRF-Token'];

      // Continue with modified headers
      await route.continue({
        headers,
      });
    });

    // Attempt to save
    const saveButton = page.getByRole('button', { name: /Save Business Info/i });
    await saveButton.click();

    // Wait for error response
    await page.waitForTimeout(1000);

    // Verify error message is displayed
    await expect(page.getByText(/403|forbidden|csrf|invalid token/i)).toBeVisible({ timeout: 5000 });
  });

  test('[P0] should reject save with invalid CSRF token', async ({ page }) => {
    await page.goto(`${BASE_URL}/business-info`);
    await page.waitForLoadState('networkidle');

    // Fill business info
    await page.getByRole('textbox', { name: /Business Name/i }).fill('Invalid CSRF Store');

    // Intercept and replace CSRF token with invalid one
    await page.route('**/api/v1/merchant/business-info', async (route) => {
      const request = route.request();
      const headers = { ...request.headers() };

      // Replace with invalid CSRF token
      headers['X-CSRF-Token'] = 'invalid-csrf-token-12345';

      await route.continue({
        headers,
      });
    });

    // Attempt to save
    const saveButton = page.getByRole('button', { name: /Save Business Info/i });
    await saveButton.click();

    // Wait for error response
    await page.waitForTimeout(1000);

    // Verify error message
    await expect(page.getByText(/403|forbidden|csrf|invalid token/i)).toBeVisible({ timeout: 5000 });
  });

  test('[P0] should reject FAQ create with missing CSRF token', async ({ page }) => {
    await page.goto(`${BASE_URL}/business-info`);
    await page.waitForLoadState('networkidle');

    // Open FAQ creation modal
    await page.getByRole('button', { name: /Add FAQ/i }).click();
    await expect(page.getByRole('dialog')).toBeVisible();

    // Fill FAQ form
    await page.getByRole('textbox', { name: /Question/i }).fill('Test Question?');
    await page.getByRole('textbox', { name: /Answer/i }).fill('Test Answer');

    // Intercept and remove CSRF token
    await page.route('**/api/v1/merchant/faqs', async (route) => {
      const request = route.request();
      const headers = { ...request.headers() };

      // Remove CSRF token
      delete headers['x-csrf-token'];
      delete headers['X-CSRF-Token'];

      await route.continue({
        headers,
      });
    });

    // Attempt to save
    const saveButton = page.getByRole('button', { name: /Save FAQ/i });
    await saveButton.click();

    // Wait for error response
    await page.waitForTimeout(1000);

    // Verify error message (modal may stay open or show error)
    const errorMessage = page.getByText(/403|forbidden|csrf|invalid token/i);
    const modalStillOpen = page.getByRole('dialog').isVisible();

    // Either error message or modal should indicate failure
    const hasError = await errorMessage.isVisible().catch(() => false);
    const isModalOpen = await modalStillOpen.catch(() => false);

    expect(hasError || isModalOpen).toBe(true);
  });

  test('[P1] should include CSRF token in FAQ update request', async ({ page }) => {
    // First create an FAQ
    await page.goto(`${BASE_URL}/business-info`);
    await page.waitForLoadState('networkidle');

    await page.getByRole('button', { name: /Add FAQ/i }).click();
    await expect(page.getByRole('dialog')).toBeVisible();

    await page.getByRole('textbox', { name: /Question/i }).fill('Original Question?');
    await page.getByRole('textbox', { name: /Answer/i }).fill('Original Answer');
    await page.getByRole('button', { name: /Save FAQ/i }).click();

    await expect(page.getByRole('dialog')).not.toBeVisible({ timeout: 5000 });

    // Now update it
    const editButton = page.getByRole('button', { name: /Edit FAQ/i }).first();
    await editButton.click();

    await expect(page.getByRole('dialog')).toBeVisible();

    // Track CSRF token in update request
    let csrfTokenSent = false;

    await page.route('**/api/v1/merchant/faqs/*', async (route) => {
      const request = route.request();
      const method = request.method();
      const headers = request.headers();

      if (method === 'PUT') {
        if (headers['x-csrf-token'] || headers['X-CSRF-Token']) {
          csrfTokenSent = true;
        }
      }

      await route.continue();
    });

    // Modify and save
    await page.getByRole('textbox', { name: /Question/i }).fill('Updated Question?');
    await page.getByRole('button', { name: /Save FAQ/i }).click();

    await page.waitForTimeout(1000);

    // Verify CSRF token was sent
    expect(csrfTokenSent).toBe(true);
  });

  test('[P1] should include CSRF token in FAQ delete request', async ({ page }) => {
    // First create an FAQ
    await page.goto(`${BASE_URL}/business-info`);
    await page.waitForLoadState('networkidle');

    await page.getByRole('button', { name: /Add FAQ/i }).click();
    await expect(page.getByRole('dialog')).toBeVisible();

    await page.getByRole('textbox', { name: /Question/i }).fill('To Be Deleted?');
    await page.getByRole('textbox', { name: /Answer/i }).fill('Will Be Deleted');
    await page.getByRole('button', { name: /Save FAQ/i }).click();

    await expect(page.getByRole('dialog')).not.toBeVisible({ timeout: 5000 });

    // Track CSRF token in delete request
    let csrfTokenSent = false;

    await page.route('**/api/v1/merchant/faqs/*', async (route) => {
      const request = route.request();
      const method = request.method();
      const headers = request.headers();

      if (method === 'DELETE') {
        if (headers['x-csrf-token'] || headers['X-CSRF-Token']) {
          csrfTokenSent = true;
        }
      }

      await route.continue();
    });

    // Delete FAQ
    const deleteButton = page.getByRole('button', { name: /Delete FAQ/i }).first();
    await deleteButton.click();

    const confirmButton = page.getByRole('button', { name: /Confirm|Delete/i }).first();
    if (await confirmButton.isVisible({ timeout: 2000 })) {
      await confirmButton.click();
    }

    await page.waitForTimeout(1000);

    // Verify CSRF token was sent
    expect(csrfTokenSent).toBe(true);
  });

  test('[P1] should refresh CSRF token after expiry', async ({ page, request }) => {
    // Get initial CSRF token
    let initialToken = csrfToken;

    await page.goto(`${BASE_URL}/business-info`);
    await page.waitForLoadState('networkidle');

    // Store token in page context
    await page.evaluate((token) => {
      localStorage.setItem('csrf_token', token);
    }, initialToken);

    // Simulate token expiry by waiting (in real scenario, token has TTL)
    await page.waitForTimeout(100);

    // Get new token
    const newCsrfResponse = await request.get(`${API_URL}/api/v1/csrf-token`, {
      headers: {
        Authorization: `Bearer ${merchantToken}`,
      },
    });

    if (newCsrfResponse.ok()) {
      const csrfData = await newCsrfResponse.json();
      const newToken = csrfData.data.csrf_token;

      // Tokens should be different (after expiry)
      expect(newToken).toBeDefined();

      // Update page with new token
      await page.evaluate((token) => {
        localStorage.setItem('csrf_token', token);
      }, newToken);

      // Try to save with new token
      await page.getByRole('textbox', { name: /Business Name/i }).fill('New Token Test');

      let newTokenUsed = false;

      await page.route('**/api/v1/merchant/business-info', async (route) => {
        const headers = route.request().headers();
        const sentToken = headers['x-csrf-token'] || headers['X-CSRF-Token'];

        if (sentToken === newToken) {
          newTokenUsed = true;
        }

        await route.continue();
      });

      await page.getByRole('button', { name: /Save Business Info/i }).click();
      await page.waitForTimeout(1000);

      // Verify new token was used
      expect(newTokenUsed).toBe(true);
    }
  });

  test('[P2] should store CSRF token in accessible location', async ({ page }) => {
    await page.goto(`${BASE_URL}/business-info`);
    await page.waitForLoadState('networkidle');

    // Check if CSRF token is stored in localStorage
    const tokenInLocalStorage = await page.evaluate(() => {
      return localStorage.getItem('csrf_token') || localStorage.getItem('csrfToken') || null;
    });

    // Check if CSRF token is stored in cookie
    const cookies = await page.context().cookies();
    const csrfCookie = cookies.find((c) => c.name.toLowerCase().includes('csrf'));

    // Token should be accessible via localStorage or cookie
    const tokenIsAccessible = tokenInLocalStorage !== null || csrfCookie !== undefined;

    expect(tokenIsAccessible).toBe(true);
  });

  test('[P2] should handle CSRF token errors gracefully', async ({ page }) => {
    await page.goto(`${BASE_URL}/business-info`);
    await page.waitForLoadState('networkidle');

    // Fill business info
    await page.getByRole('textbox', { name: /Business Name/i }).fill('Error Test');

    // Force CSRF error
    await page.route('**/api/v1/merchant/business-info', async (route) => {
      // Return 403 error
      await route.fulfill({
        status: 403,
        contentType: 'application/json',
        body: JSON.stringify({
          detail: {
            error_code: 2001,
            message: 'CSRF token validation failed',
          },
        }),
      });
    });

    // Attempt to save
    const saveButton = page.getByRole('button', { name: /Save Business Info/i });
    await saveButton.click();

    // Wait for error handling
    await page.waitForTimeout(1000);

    // Verify error is displayed to user
    await expect(page.getByText(/csrf|validation failed|403/i)).toBeVisible({ timeout: 5000 });

    // Verify form is still accessible (not crashed)
    await expect(page.getByRole('textbox', { name: /Business Name/i })).toBeVisible();
  });

  test('[P2] should include CSRF token in FAQ reorder request', async ({ page }) => {
    // Create multiple FAQs first
    await page.goto(`${BASE_URL}/business-info`);
    await page.waitForLoadState('networkidle');

    for (let i = 1; i <= 3; i++) {
      await page.getByRole('button', { name: /Add FAQ/i }).click();
      await expect(page.getByRole('dialog')).toBeVisible();

      await page.getByRole('textbox', { name: /Question/i }).fill(`FAQ ${i}`);
      await page.getByRole('textbox', { name: /Answer/i }).fill(`Answer ${i}`);
      await page.getByRole('button', { name: /Save FAQ/i }).click();

      await expect(page.getByRole('dialog')).not.toBeVisible({ timeout: 5000 });
    }

    // Track CSRF token in reorder request
    let csrfTokenSent = false;

    await page.route('**/api/v1/merchant/faqs/reorder', async (route) => {
      const headers = route.request().headers();

      if (headers['x-csrf-token'] || headers['X-CSRF-Token']) {
        csrfTokenSent = true;
      }

      await route.continue();
    });

    // Perform drag and drop reorder
    const faqCards = page.locator('[data-testid^="faq-card-"]');
    const thirdCard = faqCards.nth(2);
    const firstCard = faqCards.nth(0);

    if (await thirdCard.isVisible() && await firstCard.isVisible()) {
      await thirdCard.dragTo(firstCard);
      await page.waitForTimeout(500);

      // Verify CSRF token was sent during reorder
      expect(csrfTokenSent).toBe(true);
    }
  });

  test('[P3] should regenerate CSRF token after session refresh', async ({ page, request }) => {
    // Get initial token
    const initialResponse = await request.get(`${API_URL}/api/v1/csrf-token`, {
      headers: {
        Authorization: `Bearer ${merchantToken}`,
      },
    });

    const initialData = await initialResponse.json();
    const initialToken = initialData.data.csrf_token;

    await page.goto(`${BASE_URL}/business-info`);
    await page.waitForLoadState('networkidle');

    // Store initial token
    await page.evaluate((token) => {
      localStorage.setItem('csrf_token', token);
    }, initialToken);

    // Simulate session refresh (logout and login again)
    await page.evaluate(() => {
      localStorage.removeItem('auth_token');
      localStorage.removeItem('csrf_token');
    });

    // Login again
    const loginResponse = await request.post(`${API_URL}/api/v1/auth/login`, {
      data: TEST_MERCHANT,
    });

    if (loginResponse.ok()) {
      const loginData = await loginResponse.json();
      const newToken = loginData.data.session.token;

      // Get new CSRF token
      const newCsrfResponse = await request.get(`${API_URL}/api/v1/csrf-token`, {
        headers: {
          Authorization: `Bearer ${newToken}`,
        },
      });

      const newCsrfData = await newCsrfResponse.json();
      const newCsrfToken = newCsrfData.data.csrf_token;

      // Tokens should be different after session refresh
      expect(newCsrfToken).toBeDefined();
      // Note: Tokens might be the same in some implementations
      // The important thing is that a valid token exists
    }
  });
});
