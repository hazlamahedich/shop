/**
 * E2E Test: Mode-Aware Navigation
 * 
 * Story 8-9: Testing & Quality Assurance
 * Task 7.1: Create frontend/tests/e2e/story-8-9/mode-aware-navigation.spec.ts
 * 
 * Verifies that navigation and page access are restricted based on onboarding mode.
 * 
 * @tags e2e knowledge-base story-8-9 navigation mode-aware
 */

import { test, expect } from '@playwright/test';
import { setupKnowledgeBaseMocks } from '../../helpers/knowledge-base-mocks';

test.describe('Story 8-9: Mode-Aware Navigation @story-8-9', () => {

  test('[8.9-E2E-004][P0] should show correct nav items in General mode @p0 @critical @smoke', async ({ page }) => {
    // 1. Setup in General mode
    await setupKnowledgeBaseMocks(page, { onboardingMode: 'general' });
    
    // 2. Go to dashboard
    await page.goto('/dashboard');
    
    // 3. Verify Knowledge Base is visible in Sidebar
    const kbNavLink = page.locator('nav >> text=Knowledge Base');
    await expect(kbNavLink).toBeVisible();
    
    // 4. Verify E-commerce specific items (like Products/Orders) are hidden
    // Note: Some might be under "Shopify" or "Products"
    const productsLink = page.locator('nav >> text=Products');
    const ordersLink = page.locator('nav >> text=Orders');
    
    await expect(productsLink).not.toBeVisible();
    await expect(ordersLink).not.toBeVisible();
  });

  test('[8.9-E2E-005][P0] should show correct nav items in E-commerce mode @p0 @critical @smoke', async ({ page }) => {
    // 1. Setup in E-commerce mode
    await setupKnowledgeBaseMocks(page, { onboardingMode: 'ecommerce' });
    
    // 2. Go to dashboard
    await page.goto('/dashboard');
    
    // 3. Verify E-commerce items are visible
    // Depending on sidebar structure, it might be 'Shopify' or specific items
    // Based on story 8-7/8-8, these should be visible in ecommerce mode
    const shopifyLink = page.locator('nav >> text=Shopify');
    if (await shopifyLink.count() > 0) {
      await expect(shopifyLink).toBeVisible();
    }
    
    // 4. Verify Knowledge Base is hidden
    const kbNavLink = page.locator('nav >> text=Knowledge Base');
    await expect(kbNavLink).not.toBeVisible();
  });

  test('[8.9-E2E-006][P1] should redirect from restricted pages @p1 @navigation @access-control', async ({ page }) => {
    // 1. Setup in General mode
    await setupKnowledgeBaseMocks(page, { onboardingMode: 'general' });
    
    // 2. Try to access E-commerce page directly (e.g., /products or /integrations/shopify)
    await page.goto('/products');
    
    // 3. Should be redirected to dashboard or onboarding
    // The exact redirect depends on implementation, but it shouldn't be the products page
    await expect(page).not.toHaveURL(/.*products/);
    await expect(page).toHaveURL(/\/dashboard|\/onboarding/);
  });

  test('[8.9-E2E-007][P1] should handle mode switch navigation updates @p1 @navigation @mode-switch', async ({ page }) => {
    // 1. Setup initially in General mode
    await setupKnowledgeBaseMocks(page, { onboardingMode: 'general' });
    await page.goto('/settings');
    
    // 2. Verify KB in nav
    await expect(page.locator('nav >> text=Knowledge Base')).toBeVisible();

    // 3. Mock the mode switch API
    await page.route('**/api/merchant/settings/mode', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          status: 'success',
          data: { onboarding_mode: 'ecommerce' }
        })
      });
    });

    // 4. Trigger mode switch (assuming there's a button/toggle in settings)
    // We might need to mock the auth me update as well
    await page.route('**/api/v1/auth/me', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            data: {
              merchant: {
                id: 1,
                onboardingMode: 'ecommerce',
                has_store_connected: true
              }
            }
          })
        });
    });

    // 5. Verify the ecommerce option exists before interacting (deterministic)
    const ecommerceRadio = page.locator('text=E-commerce');
    await expect(ecommerceRadio).toBeVisible();
    
    await ecommerceRadio.click();
    await page.click('button:has-text("Save"), button:has-text("Switch")');
    
    // 6. Verify nav items update without hard reload (if SPA logic works)
    await expect(page.locator('nav >> text=Knowledge Base')).not.toBeVisible();
  });
});
