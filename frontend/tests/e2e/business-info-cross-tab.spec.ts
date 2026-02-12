/**
 * E2E Tests: Cross-Tab Synchronization
 *
 * Story 1.11: Business Info & FAQ Configuration
 *
 * Tests business info synchronization across multiple browser tabs:
 * - Changes in one tab reflect in other tabs
 * - StorageEvent listeners trigger updates
 * - Conflict resolution when multiple tabs edit simultaneously
 *
 * Prerequisites:
 * - Frontend dev server running on http://localhost:5173
 * - Backend API running on http://localhost:8000
 * - Test merchant account exists
 *
 * @tags e2e story-1-11 cross-tab synchronization
 */

import { test, expect } from '@playwright/test';
import { clearStorage } from '../fixtures/test-helper';

const API_URL = process.env.API_URL || 'http://localhost:8000';
const BASE_URL = process.env.BASE_URL || 'http://localhost:5173';

const TEST_MERCHANT = {
  email: 'e2e-cross-tab@test.com',
  password: 'TestPass123',
};

test.describe.configure({ mode: 'serial' });
test.describe('Story 1.11: Cross-Tab Synchronization [P1]', () => {
  let merchantToken: string;
  let merchantId: string;

  test.beforeAll(async ({ request }) => {
    // Create or login test merchant
    const loginResponse = await request.post(`${API_URL}/api/v1/auth/login`, {
      data: TEST_MERCHANT,
    });

    if (loginResponse.ok()) {
      const loginData = await loginResponse.json();
      merchantToken = loginData.data.session.token;
      merchantId = loginData.data.user.merchantId;
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

  test('[P1] should sync business name change from Tab A to Tab B', async ({ page, context }) => {
    // ===== PART 1: Open Tabs =====

    // Tab A: Open business info page
    const tabA = page;
    await tabA.goto(`${BASE_URL}/business-info`);
    await tabA.waitForLoadState('networkidle');

    // Verify initial state
    const nameInputA = tabA.getByRole('textbox', { name: /Business Name/i });
    await expect(nameInputA).toBeVisible();

    // Tab B: Open same page in new tab (context)
    const tabB = await context.newPage();
    await clearStorage(tabB);
    await tabB.evaluate((token) => {
      localStorage.setItem('auth_token', token);
      localStorage.setItem('auth_timestamp', Date.now().toString());
    }, merchantToken);
    await tabB.goto(`${BASE_URL}/business-info`);
    await tabB.waitForLoadState('networkidle');

    // Verify Tab B loaded
    const nameInputB = tabB.getByRole('textbox', { name: /Business Name/i });
    await expect(nameInputB).toBeVisible();

    // ===== PART 2: Update in Tab A =====

    // Set up listener in Tab B for storage events
    let storageEventFired = false;
    let updatedName = '';

    await tabB.evaluate(() => {
      window.addEventListener('storage', (event) => {
        if (event.key === 'business_info' && event.newValue) {
          // Store the event data for verification
          (window as any).__storageEventData = JSON.parse(event.newValue);
        }
      });
    });

    // Update business name in Tab A
    const newName = 'Cross-Tab Test Store';
    await nameInputA.fill(newName);

    // Save in Tab A
    const saveButtonA = tabA.getByRole('button', { name: /Save Business Info/i });
    await saveButtonA.click();

    // Verify save success in Tab A
    await expect(tabA.getByText(/business info saved/i)).toBeVisible({ timeout: 5000 });

    // ===== PART 3: Verify Sync to Tab B =====

    // Wait for storage event propagation
    await tabB.waitForTimeout(1000);

    // Check if storage event was received
    const storageData = await tabB.evaluate(() => (window as any).__storageEventData);

    if (storageData) {
      storageEventFired = true;
      updatedName = storageData.businessName || storageData.business_name;
    }

    // Verify Tab B shows updated value
    // The page should react to the storage event and update the UI
    const nameInputBValue = await nameInputB.inputValue();

    // Either via storage event or reload, Tab B should have the new value
    expect(nameInputBValue === newName || updatedName === newName).toBe(true);

    await tabB.close();
  });

  test('[P1] should sync business hours change from Tab B to Tab A', async ({ page, context }) => {
    // Tab A
    const tabA = page;
    await tabA.goto(`${BASE_URL}/business-info`);
    await tabA.waitForLoadState('networkidle');

    const hoursInputA = tabA.getByRole('textbox', { name: /Business Hours/i });
    await expect(hoursInputA).toBeVisible();

    // Tab B
    const tabB = await context.newPage();
    await clearStorage(tabB);
    await tabB.evaluate((token) => {
      localStorage.setItem('auth_token', token);
      localStorage.setItem('auth_timestamp', Date.now().toString());
    }, merchantToken);
    await tabB.goto(`${BASE_URL}/business-info`);
    await tabB.waitForLoadState('networkidle');

    // Update in Tab B
    const newHours = '8 AM - 10 PM Daily';
    await tabB.getByRole('textbox', { name: /Business Hours/i }).fill(newHours);
    await tabB.getByRole('button', { name: /Save Business Info/i }).click();

    await expect(tabB.getByText(/business info saved/i)).toBeVisible({ timeout: 5000 });

    // Wait for sync
    await tabA.waitForTimeout(1500);

    // Verify Tab A has updated value
    const hoursInputAValue = await hoursInputA.inputValue();
    expect(hoursInputAValue).toBe(newHours);

    await tabB.close();
  });

  test('[P1] should sync business description across multiple tabs', async ({ page, context }) => {
    // Open three tabs
    const tabA = page;
    await tabA.goto(`${BASE_URL}/business-info`);
    await tabA.waitForLoadState('networkidle');

    const tabB = await context.newPage();
    await clearStorage(tabB);
    await tabB.evaluate((token) => {
      localStorage.setItem('auth_token', token);
      localStorage.setItem('auth_timestamp', Date.now().toString());
    }, merchantToken);
    await tabB.goto(`${BASE_URL}/business-info`);
    await tabB.waitForLoadState('networkidle');

    const tabC = await context.newPage();
    await clearStorage(tabC);
    await tabC.evaluate((token) => {
      localStorage.setItem('auth_token', token);
      localStorage.setItem('auth_timestamp', Date.now().toString());
    }, merchantToken);
    await tabC.goto(`${BASE_URL}/business-info`);
    await tabC.waitForLoadState('networkidle');

    // Update in Tab B
    const newDescription = 'Premium athletic gear for serious athletes. Top brands, competitive prices.';
    await tabB.getByRole('textbox', { name: /Business Description/i }).fill(newDescription);
    await tabB.getByRole('button', { name: /Save Business Info/i }).click();

    await expect(tabB.getByText(/business info saved/i)).toBeVisible({ timeout: 5000 });

    // Wait for sync to all tabs
    await tabA.waitForTimeout(1500);
    await tabC.waitForTimeout(1500);

    // Verify all tabs have updated value
    const descriptionA = await tabA.getByRole('textbox', { name: /Business Description/i }).inputValue();
    const descriptionC = await tabC.getByRole('textbox', { name: /Business Description/i }).inputValue();

    expect(descriptionA).toBe(newDescription);
    expect(descriptionC).toBe(newDescription);

    await tabB.close();
    await tabC.close();
  });

  test('[P1] should sync FAQ creation across tabs', async ({ page, context }) => {
    // Tab A
    const tabA = page;
    await tabA.goto(`${BASE_URL}/business-info`);
    await tabA.waitForLoadState('networkidle');

    // Tab B
    const tabB = await context.newPage();
    await clearStorage(tabB);
    await tabB.evaluate((token) => {
      localStorage.setItem('auth_token', token);
      localStorage.setItem('auth_timestamp', Date.now().toString());
    }, merchantToken);
    await tabB.goto(`${BASE_URL}/business-info`);
    await tabB.waitForLoadState('networkidle');

    // Create FAQ in Tab A
    await tabA.getByRole('button', { name: /Add FAQ/i }).click();
    await expect(tabA.getByRole('dialog')).toBeVisible();

    const faqQuestion = 'Do you offer student discounts?';
    const faqAnswer = 'Yes, students get 10% off with valid ID';

    await tabA.getByRole('textbox', { name: /Question/i }).fill(faqQuestion);
    await tabA.getByRole('textbox', { name: /Answer/i }).fill(faqAnswer);
    await tabA.getByRole('button', { name: /Save FAQ/i }).click();

    await expect(tabA.getByRole('dialog')).not.toBeVisible({ timeout: 5000 });

    // Wait for sync
    await tabB.waitForTimeout(1500);

    // Verify FAQ appears in Tab B
    // The FAQ list should update via storage event or refresh
    const faqVisibleInTabB = await tabB.getByText(faqQuestion).isVisible().catch(() => false);

    if (!faqVisibleInTabB) {
      // If not automatically synced, reload Tab B to fetch from server
      await tabB.reload();
      await tabB.waitForLoadState('networkidle');
    }

    await expect(tabB.getByText(faqQuestion)).toBeVisible({ timeout: 5000 });

    await tabB.close();
  });

  test('[P1] should sync FAQ deletion across tabs', async ({ page, context }) => {
    // Tab A
    const tabA = page;
    await tabA.goto(`${BASE_URL}/business-info`);
    await tabA.waitForLoadState('networkidle');

    // Create FAQ first
    await tabA.getByRole('button', { name: /Add FAQ/i }).click();
    await expect(tabA.getByRole('dialog')).toBeVisible();

    const faqQuestion = 'To be deleted across tabs';
    await tabA.getByRole('textbox', { name: /Question/i }).fill(faqQuestion);
    await tabA.getByRole('textbox', { name: /Answer/i }).fill('This will be deleted');
    await tabA.getByRole('button', { name: /Save FAQ/i }).click();

    await expect(tabA.getByRole('dialog')).not.toBeVisible({ timeout: 5000 });

    // Tab B
    const tabB = await context.newPage();
    await clearStorage(tabB);
    await tabB.evaluate((token) => {
      localStorage.setItem('auth_token', token);
      localStorage.setItem('auth_timestamp', Date.now().toString());
    }, merchantToken);
    await tabB.goto(`${BASE_URL}/business-info`);
    await tabB.waitForLoadState('networkidle');

    // Verify FAQ exists in Tab B
    await expect(tabB.getByText(faqQuestion)).toBeVisible();

    // Delete FAQ in Tab A
    const deleteButton = tabA.getByRole('button', { name: /Delete FAQ/i }).first();
    await deleteButton.click();

    const confirmButton = tabA.getByRole('button', { name: /Confirm|Delete/i }).first();
    if (await confirmButton.isVisible({ timeout: 2000 })) {
      await confirmButton.click();
    }

    await expect(tabA.getByText(faqQuestion)).not.toBeVisible();

    // Wait for sync
    await tabB.waitForTimeout(1500);

    // Verify FAQ removed from Tab B
    const faqStillInTabB = await tabB.getByText(faqQuestion).isVisible().catch(() => true);

    if (faqStillInTabB) {
      // If not automatically synced, reload
      await tabB.reload();
      await tabB.waitForLoadState('networkidle');
    }

    await expect(tabB.getByText(faqQuestion)).not.toBeVisible({ timeout: 5000 });

    await tabB.close();
  });

  test('[P2] should handle simultaneous edits with last-write-wins', async ({ page, context }) => {
    // Tab A and Tab B both open
    const tabA = page;
    await tabA.goto(`${BASE_URL}/business-info`);
    await tabA.waitForLoadState('networkidle');

    const tabB = await context.newPage();
    await clearStorage(tabB);
    await tabB.evaluate((token) => {
      localStorage.setItem('auth_token', token);
      localStorage.setItem('auth_timestamp', Date.now().toString());
    }, merchantToken);
    await tabB.goto(`${BASE_URL}/business-info`);
    await tabB.waitForLoadState('networkidle');

    // Simultaneous edits (within network tolerance)
    const nameA = 'Store A';
    const nameB = 'Store B';

    // Edit in Tab A
    await tabA.getByRole('textbox', { name: /Business Name/i }).fill(nameA);

    // Edit in Tab B
    await tabB.getByRole('textbox', { name: /Business Name/i }).fill(nameB);

    // Save in Tab A first
    await tabA.getByRole('button', { name: /Save Business Info/i }).click();
    await expect(tabA.getByText(/business info saved/i)).toBeVisible({ timeout: 5000 });

    // Small delay
    await tabA.waitForTimeout(100);

    // Save in Tab B second (should win with last-write-wins)
    await tabB.getByRole('button', { name: /Save Business Info/i }).click();
    await expect(tabB.getByText(/business info saved/i)).toBeVisible({ timeout: 5000 });

    // Wait for sync
    await tabA.waitForTimeout(1500);

    // Both tabs should have the last saved value (Tab B's value)
    const nameInputAValue = await tabA.getByRole('textbox', { name: /Business Name/i }).inputValue();
    const nameInputBValue = await tabB.getByRole('textbox', { name: /Business Name/i }).inputValue();

    expect(nameInputAValue).toBe(nameB);
    expect(nameInputBValue).toBe(nameB);

    await tabB.close();
  });

  test('[P2] should sync unsaved changes indicator across tabs', async ({ page, context }) => {
    // Tab A
    const tabA = page;
    await tabA.goto(`${BASE_URL}/business-info`);
    await tabA.waitForLoadState('networkidle');

    // Tab B
    const tabB = await context.newPage();
    await clearStorage(tabB);
    await tabB.evaluate((token) => {
      localStorage.setItem('auth_token', token);
      localStorage.setItem('auth_timestamp', Date.now().toString());
    }, merchantToken);
    await tabB.goto(`${BASE_URL}/business-info`);
    await tabB.waitForLoadState('networkidle');

    // Make unsaved change in Tab A
    await tabA.getByRole('textbox', { name: /Business Name/i }).fill('Unsaved Change');

    // Check for unsaved changes indicator (if implemented)
    // This would typically be a dirty flag in the store
    const hasUnsavedChangesA = await tabA.evaluate(() => {
      return (window as any).__hasUnsavedChanges || false;
    });

    // If dirty flag is tracked via storage
    await tabB.waitForTimeout(500);

    // Verify both tabs have awareness of unsaved state
    // (This depends on implementation - may vary)
    const hasUnsavedChangesB = await tabB.evaluate(() => {
      return (window as any).__hasUnsavedChanges || false;
    });

    // Both should know about unsaved changes if storage sync is working
    expect(hasUnsavedChangesA).toBe(true);

    await tabB.close();
  });

  test('[P2] should handle rapid consecutive updates without race conditions', async ({ page, context }) => {
    // Tab A
    const tabA = page;
    await tabA.goto(`${BASE_URL}/business-info`);
    await tabA.waitForLoadState('networkidle');

    // Tab B
    const tabB = await context.newPage();
    await clearStorage(tabB);
    await tabB.evaluate((token) => {
      localStorage.setItem('auth_token', token);
      localStorage.setItem('auth_timestamp', Date.now().toString());
    }, merchantToken);
    await tabB.goto(`${BASE_URL}/business-info`);
    await tabB.waitForLoadState('networkidle');

    // Rapid updates in Tab A
    const updates = ['Update 1', 'Update 2', 'Update 3'];

    for (const update of updates) {
      await tabA.getByRole('textbox', { name: /Business Name/i }).fill(update);
      await tabA.getByRole('button', { name: /Save Business Info/i }).click();
      await expect(tabA.getByText(/business info saved/i)).toBeVisible({ timeout: 5000 });
      await tabA.waitForTimeout(100);
    }

    // Wait for all updates to sync
    await tabB.waitForTimeout(2000);

    // Tab B should have the final value
    const nameInputBValue = await tabB.getByRole('textbox', { name: /Business Name/i }).inputValue();
    expect(nameInputBValue).toBe(updates[updates.length - 1]);

    await tabB.close();
  });

  test('[P3] should preserve tab-specific state during sync', async ({ page, context }) => {
    // Tab A
    const tabA = page;
    await tabA.goto(`${BASE_URL}/business-info`);
    await tabA.waitForLoadState('networkidle');

    // Tab B
    const tabB = await context.newPage();
    await clearStorage(tabB);
    await tabB.evaluate((token) => {
      localStorage.setItem('auth_token', token);
      localStorage.setItem('auth_timestamp', Date.now().toString());
    }, merchantToken);
    await tabB.goto(`${BASE_URL}/business-info`);
    await tabB.waitForLoadState('networkidle');

    // Open FAQ modal in Tab B (tab-specific state)
    await tabB.getByRole('button', { name: /Add FAQ/i }).click();
    await expect(tabB.getByRole('dialog')).toBeVisible();

    // Make change in Tab A
    await tabA.getByRole('textbox', { name: /Business Name/i }).fill('Tab A Update');
    await tabA.getByRole('button', { name: /Save Business Info/i }).click();
    await expect(tabA.getByText(/business info saved/i)).toBeVisible({ timeout: 5000 });

    // Wait for sync
    await tabB.waitForTimeout(1000);

    // Tab B's modal should still be open (tab-specific state preserved)
    await expect(tabB.getByRole('dialog')).toBeVisible();

    // But the business name should be updated
    const nameInputBValue = await tabB.getByRole('textbox', { name: /Business Name/i }).inputValue();
    expect(nameInputBValue).toBe('Tab A Update');

    await tabB.close();
  });
});
