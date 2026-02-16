/**
 * E2E Tests for Story 1.14: Smart Greeting Templates
 * Tests greeting configuration UI and interactions within BotConfig page
 *
 * Prerequisites:
 * - Frontend dev server running on http://localhost:5173
 * - Backend API running on http://localhost:8000
 * - Test merchant account exists and is logged in
 *
 *
 * Test Fix: 2026-02-12 - Updated selectors to match actual BotConfig page structure
 */

import { test, expect } from '@playwright/test';
import { clearStorage } from '../fixtures/test-helper';

const API_URL = process.env.API_URL || 'http://localhost:8000';

test.describe.configure({ mode: 'serial' }); // Run tests serially to avoid state conflicts
test.describe('Story 1.14: Smart Greeting Templates - Greeting Configuration [P0]', () => {
  test.beforeEach(async ({ page }) => {
    await clearStorage(page);

    // Setup test merchant authentication
    await page.goto(`${API_URL}/api/v1/auth/login`);
    await page.evaluate(() => {
      window.localStorage.setItem('test_token', 'test-token-123');
    });
  });

  test('[P0] should display greeting configuration section on Bot Config page', async ({ page }) => {
    // Navigate to bot config page
    await page.goto('http://localhost:5173/bot-config');
    await page.waitForLoadState('networkidle');

    // Verify greeting section is visible (using data-testid for reliability)
    await expect(page.getByTestId('greeting-section')).toBeVisible();

    // Verify personality indicator is visible
    const personalitySection = page.getByTestId('personality-section');
    await expect(personalitySection).toBeVisible();

    // Verify greeting configuration section is visible
    await expect(page.getByTestId('greeting-config-section')).toBeVisible();

    // Verify default template display exists
    await expect(page.getByTestId('default-template-display')).toBeVisible();

    // Verify custom greeting textarea exists
    await expect(page.getByTestId('custom-greeting-textarea')).toBeVisible();

    // Verify use custom greeting checkbox exists
    await expect(page.getByTestId('use-custom-greeting-checkbox')).toBeVisible();

    // Verify reset button exists
    await expect(page.getByTestId('reset-greeting-button')).toBeVisible();

    // Verify live preview exists
    await expect(page.getByTestId('greeting-preview-display')).toBeVisible();

    // Verify help section exists
    await expect(page.getByTestId('greeting-help-section')).toBeVisible();
  });

  test('[P0] should display personality-based default greeting template', async ({ page }) => {
    // Navigate to bot config page
    await page.goto('http://localhost:5173/bot-config');
    await page.waitForLoadState('networkidle');

    // Get bot config store state to determine expected defaults
    const botConfigStore = await page.evaluate(async () => {
      // @ts-ignore
      return (window as any).botConfigStore?.getState?.() || {};
    });

    const personality = botConfigStore?.personality || 'friendly';

    // Expected default templates by personality
    const expectedDefaults: Record<string, string> = {
      friendly: "Hey there! 👋 I'm {bot_name} from {business_name}. How can I help you today?",
      professional: "Good day. I am {bot_name} from {business_name}. How may I assist you today?",
      enthusiastic: "Hello! 🎉 I'm {bot_name} from {business_name} and I'm SO excited to help you find exactly what you need!!! ✨ What can I help you with today?",
    };

    const expectedDefault = expectedDefaults[personality] || expectedDefaults.friendly;

    // Verify default template is displayed correctly
    const defaultTemplate = page.getByTestId('default-template-display');
    await expect(defaultTemplate).toBeVisible();
    await expect(defaultTemplate).toHaveText(expectedDefault);
  });

  test('[P0] should enable custom greeting and see live preview update', async ({ page }) => {
    // Navigate to bot config page
    await page.goto('http://localhost:5173/bot-config');
    await page.waitForLoadState('networkidle');

    // Click use custom greeting checkbox
    await page.getByTestId('use-custom-greeting-checkbox').click();

    // Verify custom greeting textarea appears
    const customTextarea = page.getByTestId('custom-greeting-textarea');
    await expect(customTextarea).toBeVisible();

    // Type custom greeting message
    const customGreeting = "Welcome to our valued customers! We're excited to help you find what you need.";
    await customTextarea.fill(customGreeting);

    // Verify live preview updates with custom message
    const preview = page.getByTestId('greeting-preview-display');
    await expect(preview).toContainText(customGreeting);
  });

  test('[P0] should validate greeting input - empty greeting', async ({ page }) => {
    // Navigate to bot config page
    await page.goto('http://localhost:5173/bot-config');
    await page.waitForLoadState('networkidle');

    // Click use custom greeting checkbox to enable custom input
    await page.getByTestId('use-custom-greeting-checkbox').click();

    // Clear the textarea
    const customTextarea = page.getByTestId('custom-greeting-textarea');
    await customTextarea.fill('');

    // Try to save (should trigger validation)
    const saveButton = page.getByTestId('save-bot-name-button'); // BotConfig save button

    // Click save button (triggers validation)
    await saveButton.click();

    // Verify error message appears
    await expect(page.getByText(/greeting cannot be empty/i)).toBeVisible();
  });

  test('[P0] should validate greeting input - exceeds 500 characters', async ({ page }) => {
    // Navigate to bot config page
    await page.goto('http://localhost:5173/bot-config');
    await page.waitForLoadState('networkidle');

    // Click use custom greeting checkbox
    await page.getByTestId('use-custom-greeting-checkbox').click();

    // Fill with too long greeting (>500 chars)
    const customTextarea = page.getByTestId('custom-greeting-textarea');
    await customTextarea.fill('a'.repeat(501));

    // Click save button
    const saveButton = page.getByTestId('save-bot-name-button');
    await saveButton.click();

    // Verify error message for too long
    await expect(page.getByText(/must be less than 500 characters/i)).toBeVisible();
  });

  test('[P0] should reset greeting to default personality template', async ({ page }) => {
    // Navigate to bot config page
    await page.goto('http://localhost:5173/bot-config');
    await page.waitForLoadState('networkidle');

    // Click reset button
    await page.getByTestId('reset-greeting-button').click();

    // Verify custom greeting checkbox is unchecked after reset
    const checkbox = page.getByTestId('use-custom-greeting-checkbox');
    await expect(checkbox).not.toBeChecked();

    // Verify default template is shown (personality-based)
    const defaultTemplate = page.getByTestId('default-template-display');
    await expect(defaultTemplate).toBeVisible();

    // Verify the template contains personality-based greeting
    await expect(defaultTemplate).toMatch(/Hey there|Good day|Hello/i);
  });

  test('[P0] should show help section with variable explanations', async ({ page }) => {
    // Navigate to bot config page
    await page.goto('http://localhost:5173/bot-config');
    await page.waitForLoadState('networkidle');

    // Verify help section exists
    await expect(page.getByTestId('greeting-help-section')).toBeVisible();

    // Verify variable badges are shown
    await expect(page.getByText('{bot_name}')).toBeVisible();
    await expect(page.getByText('{business_name}')).toBeVisible();
    await expect(page.getByText('{business_hours}')).toBeVisible();

    // Verify help text for variables
    await expect(page.getByText(/from Bot Configuration/i)).toBeVisible();
    await expect(page.getByText(/from Business Info/i)).toBeVisible();
  });

  test('[P0] should display configured greeting when custom is enabled', async ({ page }) => {
    // Navigate to bot config page
    await page.goto('http://localhost:5173/bot-config');
    await page.waitForLoadState('networkidle');

    // Click use custom greeting checkbox
    await page.getByTestId('use-custom-greeting-checkbox').click();

    // Type custom greeting
    const customGreeting = "Custom greeting from {business_name}!";
    await page.getByTestId('custom-greeting-textarea').fill(customGreeting);

    // Verify configured greeting is displayed
    await expect(page.getByTestId('custom-greeting-display')).toBeVisible();
    await expect(page.getByTestId('custom-greeting-display')).toContainText(customGreeting);
  });

  test('[P0] should support all three personality types', async ({ page }) => {
    const personalities = ['friendly', 'professional', 'enthusiastic'] as const;

    for (const personality of personalities) {
      // Navigate to bot config page fresh for each test
      await page.goto('http://localhost:5173/personality');
      await page.waitForLoadState('networkidle');

      // Select this personality
      await page.getByRole('radio', { name: new RegExp(personality, 'i') }).click();

      // Wait for navigation
      await page.waitForLoadState('networkidle');

      // Go to bot config page
      await page.goto('http://localhost:5173/bot-config');
      await page.waitForLoadState('networkidle');

      // Verify the correct default template is shown
      const defaultTemplate = page.getByTestId('default-template-display');

      if (personality === 'friendly') {
        await expect(defaultTemplate).toContainText('Hey there! 👋');
      } else if (personality === 'professional') {
        await expect(defaultTemplate).toContainText('Good day');
      } else if (personality === 'enthusiastic') {
        await expect(defaultTemplate).toContainText('Hello! 🎉');
      }
    }
  });

  test('[P1] should maintain greeting state across page navigation', async ({ page }) => {
    // Navigate to bot config page
    await page.goto('http://localhost:5173/bot-config');
    await page.waitForLoadState('networkidle');

    // Click use custom greeting checkbox
    await page.getByTestId('use-custom-greeting-checkbox').click();
    await page.getByTestId('custom-greeting-textarea').fill('Test greeting');

    // Navigate to personality page and back (tests state persistence)
    await page.goto('http://localhost:5173/personality');
    await page.waitForLoadState('networkidle');

    // Return to bot config page
    await page.goto('http://localhost:5173/bot-config');
    await page.waitForLoadState('networkidle');

    // Verify custom greeting is still filled (state persisted)
    const customTextarea = page.getByTestId('custom-greeting-textarea');
    await expect(customTextarea).toHaveValue('Test greeting');
  });

  test('[P0] should display personality indicator with correct styling', async ({ page }) => {
    // Navigate to bot config page
    await page.goto('http://localhost:5173/bot-config');
    await page.waitForLoadState('networkidle');

    // Verify personality section is visible
    const personalitySection = page.getByTestId('personality-section');
    await expect(personalitySection).toBeVisible();

    // Verify personality badge exists
    const personalityBadge = page.getByTestId('personality-badge');
    await expect(personalityBadge).toBeVisible();

    // Verify badge has correct text based on personality
    const botConfigStore = await page.evaluate(async () => {
      // @ts-ignore
      return (window as any).botConfigStore?.getState?.() || {};
    });

    const personality = botConfigStore?.personality || 'friendly';
    const expectedColors: Record<string, { bg: string; text: string }> = {
      friendly: { bg: 'bg-green-50', text: 'text-green-700' },
      professional: { bg: 'bg-indigo-50', text: 'text-indigo-700' },
      enthusiastic: { bg: 'bg-amber-50', text: 'text-amber-700' },
    };

    const expected = expectedColors[personality] || expectedColors.friendly;

    await expect(personalityBadge).toHaveCSS('background-color', expected.bg);
    await expect(personalityBadge).toHaveCSS('color', expected.text);
  });

  test('[P1] should display available variables list', async ({ page }) => {
    // Navigate to bot config page
    await page.goto('http://localhost:5173/bot-config');
    await page.waitForLoadState('networkidle');

    // Verify help section with variables is visible
    await expect(page.getByTestId('greeting-help-section')).toBeVisible();

    // Check for all three variable badges
    await expect(page.getByText('{bot_name}')).toBeVisible();
    await expect(page.getByText('{business_name}')).toBeVisible();
    await expect(page.getByText('{business_hours}')).toBeVisible();
  });
});
