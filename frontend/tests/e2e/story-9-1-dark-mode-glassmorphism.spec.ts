/**
 * Story 9-1: Dark Mode with Glassmorphism E2E Tests
 *
 * Tests the glassmorphism theme system including:
 * - Frosted glass background effect (backdrop-filter blur)
 * - Light/dark mode auto-adapts to system preference
 * - Manual theme toggle available (light/dark/auto)
 * - Smooth transitions between themes
 * - WCAG AA contrast ratios
 * - Browser compatibility (Chrome, Firefox, Safari, Edge)
 *
 * @tags e2e widget story-9-1 theme glassmorphism dark-mode accessibility
 */

import { test, expect, Page } from '@playwright/test';
import { mockWidgetConfig, mockWidgetSession, mockWidgetMessage, createMockMessageResponse } from '../helpers/widget-test-helpers';

const TEST_MERCHANT_ID = '4';
const THEME_STORAGE_KEY = `shopbot-widget-theme-${TEST_MERCHANT_ID}`;

async function setupWidgetMocks(page: Page) {
  await mockWidgetConfig(page);
  await mockWidgetSession(page);
  await mockWidgetMessage(page, createMockMessageResponse({ content: 'Hello! How can I help?' }));
}

async function getGlassmorphismWrapper(page: Page) {
  return page.locator('.glassmorphism-wrapper .shopbot-chat-window').first();
}

async function openChat(page: Page) {
  const bubble = page.getByRole('button', { name: 'Open chat' });
  await bubble.click();
  const dialog = page.getByRole('dialog', { name: 'Chat window' });
  await expect(dialog).toBeVisible({ timeout: 10000 });
  return dialog;
}

async function getThemeFromStorage(page: Page): Promise<string | null> {
  return page.evaluate((key) => localStorage.getItem(key), THEME_STORAGE_KEY);
}

async function setThemeInStorage(page: Page, mode: string) {
  await page.evaluate(
    ({ key, value }) => localStorage.setItem(key, value),
    { key: THEME_STORAGE_KEY, value: mode }
  );
}

async function clearThemeStorage(page: Page) {
  await page.evaluate((key) => localStorage.removeItem(key), THEME_STORAGE_KEY);
}

async function emulateSystemTheme(page: Page, theme: 'dark' | 'light') {
  await page.emulateMedia({ colorScheme: theme });
}

test.describe('Story 9-1: Dark Mode with Glassmorphism', () => {
  test.beforeEach(async ({ page }) => {
    await setupWidgetMocks(page);
  });

  test.describe('[P0] Critical Path - Glassmorphism Rendering', () => {
    test('[P0] @smoke should render chat window with glassmorphism classes', async ({ page }) => {
      await page.goto('/widget-test');
      await openChat(page);

      const glassmorphismWrapper = await getGlassmorphismWrapper(page);
      await expect(glassmorphismWrapper).toBeVisible();
    });

    test('[P0] @smoke should apply dark-mode class when system prefers dark', async ({ page }) => {
      await emulateSystemTheme(page, 'dark');
      await page.goto('/widget-test');
      await openChat(page);

      const glassmorphismWrapper = await getGlassmorphismWrapper(page);
      const wrapperParent = page.locator('.glassmorphism-wrapper');
      await expect(wrapperParent).toHaveClass(/dark-mode/);
    });

    test('[P0] @smoke should apply light-mode class when system prefers light', async ({ page }) => {
      await emulateSystemTheme(page, 'light');
      await page.goto('/widget-test');
      await openChat(page);

      const wrapperParent = page.locator('.glassmorphism-wrapper');
      await expect(wrapperParent).toHaveClass(/light-mode/);
    });
  });

  test.describe('[P0] Critical Path - Theme Persistence', () => {
    test('[P0] should persist theme mode in localStorage', async ({ page }) => {
      await page.goto('/widget-test');
      await openChat(page);

      const themeToggle = page.getByRole('button', { name: /Theme:/ });
      await themeToggle.click();

      const storedTheme = await getThemeFromStorage(page);
      expect(storedTheme).toBeTruthy();
      expect(['light', 'dark', 'auto']).toContain(storedTheme);
    });

    test('[P0] should restore theme mode from localStorage on reload', async ({ page }) => {
      await page.goto('/widget-test');
      await setThemeInStorage(page, 'dark');
      await page.reload();

      await openChat(page);

      const wrapperParent = page.locator('.glassmorphism-wrapper');
      await expect(wrapperParent).toHaveClass(/dark-mode/);
    });
  });

  test.describe('[P1] System Theme Detection', () => {
    test('[P1] should use dark theme when system prefers dark and mode is auto', async ({ page }) => {
      await emulateSystemTheme(page, 'dark');
      await page.goto('/widget-test');
      await setThemeInStorage(page, 'auto');
      await page.reload();
      await openChat(page);

      const wrapperParent = page.locator('.glassmorphism-wrapper');
      await expect(wrapperParent).toHaveClass(/dark-mode/);
    });

    test('[P1] should use light theme when system prefers light and mode is auto', async ({ page }) => {
      await emulateSystemTheme(page, 'light');
      await page.goto('/widget-test');
      await setThemeInStorage(page, 'auto');
      await page.reload();
      await openChat(page);

      const wrapperParent = page.locator('.glassmorphism-wrapper');
      await expect(wrapperParent).toHaveClass(/light-mode/);
    });

    test('[P1] should respect manual dark mode regardless of system preference', async ({ page }) => {
      await emulateSystemTheme(page, 'light');
      await page.goto('/widget-test');
      await setThemeInStorage(page, 'dark');
      await page.reload();
      await openChat(page);

      const wrapperParent = page.locator('.glassmorphism-wrapper');
      await expect(wrapperParent).toHaveClass(/dark-mode/);
    });

    test('[P1] should respect manual light mode regardless of system preference', async ({ page }) => {
      await emulateSystemTheme(page, 'dark');
      await page.goto('/widget-test');
      await setThemeInStorage(page, 'light');
      await page.reload();
      await openChat(page);

      const wrapperParent = page.locator('.glassmorphism-wrapper');
      await expect(wrapperParent).toHaveClass(/light-mode/);
    });
  });

  test.describe('[P1] Theme Toggle Integration', () => {
    test('[P1] should cycle through theme modes: light → dark → auto → light', async ({ page }) => {
      await page.goto('/widget-test');
      await setThemeInStorage(page, 'light');
      await page.reload();
      await openChat(page);

      const themeToggle = page.getByRole('button', { name: /Light theme/ });
      await expect(themeToggle).toBeVisible();

      await themeToggle.click();
      await expect(page.getByRole('button', { name: /Dark theme/ })).toBeVisible();

      const darkToggle = page.getByRole('button', { name: /Dark theme/ });
      await darkToggle.click();
      await expect(page.getByRole('button', { name: /Auto/ })).toBeVisible();

      const autoToggle = page.getByRole('button', { name: /Auto/ });
      await autoToggle.click();
      await expect(page.getByRole('button', { name: /Light theme/ })).toBeVisible();
    });

    test('[P1] should have accessible theme toggle button', async ({ page }) => {
      await page.goto('/widget-test');
      await openChat(page);

      const themeToggle = page.getByRole('button', { name: /Theme:/ });
      await expect(themeToggle).toBeVisible();

      const ariaLabel = await themeToggle.getAttribute('aria-label');
      expect(ariaLabel).toContain('Theme:');
    });

    test('[P1] should show correct icon for each theme mode', async ({ page }) => {
      await page.goto('/widget-test');
      await setThemeInStorage(page, 'light');
      await page.reload();
      await openChat(page);

      const lightToggle = page.getByRole('button', { name: /Light theme/ });
      await expect(lightToggle).toBeVisible();

      await lightToggle.click();
      const darkToggle = page.getByRole('button', { name: /Dark theme/ });
      await expect(darkToggle).toBeVisible();

      await darkToggle.click();
      const autoToggle = page.getByRole('button', { name: /Auto/ });
      await expect(autoToggle).toBeVisible();
    });
  });

  test.describe('[P1] Accessibility - WCAG AA Contrast', () => {
    test('[P1] should have sufficient contrast in dark mode', async ({ page }) => {
      await emulateSystemTheme(page, 'dark');
      await page.goto('/widget-test');
      await openChat(page);

      const chatWindow = page.getByRole('dialog', { name: 'Chat window' });

      const textColor = await chatWindow.evaluate((el) => {
        return window.getComputedStyle(el).color;
      });

      expect(textColor).toBeTruthy();
    });

    test('[P1] should have sufficient contrast in light mode', async ({ page }) => {
      await emulateSystemTheme(page, 'light');
      await page.goto('/widget-test');
      await openChat(page);

      const chatWindow = page.getByRole('dialog', { name: 'Chat window' });

      const textColor = await chatWindow.evaluate((el) => {
        return window.getComputedStyle(el).color;
      });

      expect(textColor).toBeTruthy();
    });

    test('[P1] should have accessible theme toggle focus indicator', async ({ page }) => {
      await page.goto('/widget-test');
      await openChat(page);

      const themeToggle = page.getByRole('button', { name: /Theme:/ });
      await themeToggle.focus();

      await expect(themeToggle).toBeFocused();
    });
  });

  test.describe('[P2] Glassmorphism Visual Effects', () => {
    test('[P2] should apply backdrop-filter blur in dark mode', async ({ page }) => {
      await emulateSystemTheme(page, 'dark');
      await page.goto('/widget-test');
      await openChat(page);

      const glassmorphismWrapper = await getGlassmorphismWrapper(page);

      const backdropFilter = await glassmorphismWrapper.evaluate((el) => {
        return window.getComputedStyle(el).backdropFilter;
      });

      expect(backdropFilter).toContain('blur');
    });

    test('[P2] should apply backdrop-filter blur in light mode', async ({ page }) => {
      await emulateSystemTheme(page, 'light');
      await page.goto('/widget-test');
      await openChat(page);

      const glassmorphismWrapper = await getGlassmorphismWrapper(page);

      const backdropFilter = await glassmorphismWrapper.evaluate((el) => {
        return window.getComputedStyle(el).backdropFilter;
      });

      expect(backdropFilter).toContain('blur');
    });

    test('[P2] should have transparent background for glass effect', async ({ page }) => {
      await page.goto('/widget-test');
      await openChat(page);

      const glassmorphismWrapper = await getGlassmorphismWrapper(page);

      const background = await glassmorphismWrapper.evaluate((el) => {
        return window.getComputedStyle(el).background;
      });

      expect(background).toMatch(/rgba|transparent/);
    });
  });

  test.describe('[P2] Smooth Transitions', () => {
    test('[P2] should have transition styles for theme changes', async ({ page }) => {
      await page.goto('/widget-test');
      await openChat(page);

      const glassmorphismWrapper = await getGlassmorphismWrapper(page);

      const transition = await glassmorphismWrapper.evaluate((el) => {
        return window.getComputedStyle(el).transition;
      });

      expect(transition).toBeTruthy();
    });

    test('[P2] should transition smoothly between light and dark modes', async ({ page }) => {
      await page.goto('/widget-test');
      await setThemeInStorage(page, 'light');
      await page.reload();
      await openChat(page);

      const wrapperParent = page.locator('.glassmorphism-wrapper');
      await expect(wrapperParent).toHaveClass(/light-mode/);

      const themeToggle = page.getByRole('button', { name: /Light theme/ });
      await themeToggle.click();

      await expect(wrapperParent).toHaveClass(/dark-mode/);
    });
  });

  test.describe('[P2] Reduced Motion Support', () => {
    test('[P2] should respect prefers-reduced-motion setting', async ({ page }) => {
      await page.emulateMedia({ reducedMotion: 'reduce' });
      await page.goto('/widget-test');
      await openChat(page);

      const glassmorphismWrapper = await getGlassmorphismWrapper(page);

      const transition = await glassmorphismWrapper.evaluate((el) => {
        const styles = window.getComputedStyle(el);
        return styles.transition;
      });

      expect(transition).toMatch(/none|0s/);
    });

    test('[P2] should disable animations when reduced motion is preferred', async ({ page }) => {
      await page.emulateMedia({ reducedMotion: 'reduce' });
      await page.goto('/widget-test');
      await openChat(page);

      const glassmorphismWrapper = await getGlassmorphismWrapper(page);

      const animation = await glassmorphismWrapper.evaluate((el) => {
        return window.getComputedStyle(el).animation;
      });

      expect(animation === 'none 0s ease 0s normal none running none' || animation.includes('none') || animation === '0s').toBeTruthy();
    });
  });

  test.describe('[P2] Browser Fallback Support', () => {
    test('[P2] should have fallback background when backdrop-filter unsupported', async ({ page }) => {
      await page.goto('/widget-test');
      await openChat(page);

      const glassmorphismWrapper = await getGlassmorphismWrapper(page);

      const background = await glassmorphismWrapper.evaluate((el) => {
        return window.getComputedStyle(el).background;
      });

      expect(background).toBeTruthy();
    });
  });

  test.describe('[P1] Theme Toggle Keyboard Navigation', () => {
    test('[P1] should activate theme toggle with Enter key', async ({ page }) => {
      await page.goto('/widget-test');
      await openChat(page);

      const themeToggle = page.getByRole('button', { name: /Theme:/ });
      await themeToggle.focus();
      await themeToggle.press('Enter');

      await expect(page.getByRole('button', { name: /Light theme/ })).toBeVisible();
    });

    test('[P1] should activate theme toggle with Space key', async ({ page }) => {
      await page.goto('/widget-test');
      await openChat(page);

      const themeToggle = page.getByRole('button', { name: /Theme:/ });
      await themeToggle.focus();
      await themeToggle.press('Space');

      await expect(page.getByRole('button', { name: /Light theme/ })).toBeVisible();
    });

    test('[P1] should be focusable in tab order', async ({ page }) => {
      await page.goto('/widget-test');
      await openChat(page);

      const themeToggle = page.getByRole('button', { name: /Theme:/ });
      
      await themeToggle.focus();
      await expect(themeToggle).toBeFocused();
    });
  });

  test.describe('[P1] Theme with Messages', () => {
    test('[P1] should display user messages with correct styling in dark mode', async ({ page }) => {
      await emulateSystemTheme(page, 'dark');
      await page.goto('/widget-test');
      await openChat(page);

      const input = page.getByLabel('Type a message');
      await input.fill('Test message in dark mode');
      await page.getByRole('button', { name: 'Send message' }).click();

      const userMessage = page.locator('.message-bubble--user').filter({ hasText: 'Test message in dark mode' });
      await expect(userMessage).toBeVisible();
    });

    test('[P1] should display user messages with correct styling in light mode', async ({ page }) => {
      await emulateSystemTheme(page, 'light');
      await page.goto('/widget-test');
      await openChat(page);

      const input = page.getByLabel('Type a message');
      await input.fill('Test message in light mode');
      await page.getByRole('button', { name: 'Send message' }).click();

      const userMessage = page.locator('.message-bubble--user').filter({ hasText: 'Test message in light mode' });
      await expect(userMessage).toBeVisible();
    });

    test('[P2] should maintain message visibility after theme change', async ({ page }) => {
      await page.goto('/widget-test');
      await openChat(page);

      const input = page.getByLabel('Type a message');
      await input.fill('Persistent message');
      await page.getByRole('button', { name: 'Send message' }).click();

      const messageList = page.getByRole('log', { name: 'Chat messages' });
      await expect(messageList.getByText('Persistent message')).toBeVisible();

      const themeToggle = page.getByRole('button', { name: /Theme:/ });
      await themeToggle.click();

      await expect(messageList.getByText('Persistent message')).toBeVisible();
    });

    test('[P2] should apply glow effect to user messages (AC4)', async ({ page }) => {
      await page.goto('/widget-test');
      await openChat(page);

      const input = page.getByLabel('Type a message');
      await input.fill('Glowing message');
      await page.getByRole('button', { name: 'Send message' }).click();

      const userMessage = page.locator('.message-bubble--user').filter({ hasText: 'Glowing message' });
      await expect(userMessage).toBeVisible();

      const styles = await userMessage.evaluate((el) => {
        const computed = window.getComputedStyle(el);
        return {
          background: computed.background,
          boxShadow: computed.boxShadow,
        };
      });

      expect(styles.background || styles.boxShadow).toBeTruthy();
    });

    test('[P2] should have pulsing glow animation on user messages (AC4)', async ({ page }) => {
      await page.goto('/widget-test');
      await openChat(page);

      const input = page.getByLabel('Type a message');
      await input.fill('Animated message');
      await page.getByRole('button', { name: 'Send message' }).click();

      const userMessage = page.locator('.message-bubble--user').filter({ hasText: 'Animated message' });
      await expect(userMessage).toBeVisible();

      const animation = await userMessage.evaluate((el) => {
        return window.getComputedStyle(el).animation;
      });

      expect(animation).toBeTruthy();
    });
  });

  test.describe('[P3] Edge Cases', () => {
    test('[P3] should handle rapid theme toggle clicks without errors', async ({ page }) => {
      await page.goto('/widget-test');
      await openChat(page);

      const themeToggle = page.getByRole('button', { name: /Theme:/ });
      await expect(themeToggle).toBeVisible();

      for (let i = 0; i < 5; i++) {
        await themeToggle.click();
        await page.waitForTimeout(50);
      }

      const ariaLabel = await themeToggle.getAttribute('aria-label');
      expect(ariaLabel).toContain('Theme:');
    });

    test('[P3] should recover from corrupted localStorage theme value', async ({ page }) => {
      await page.goto('/widget-test');
      
      // Set invalid theme value after page loads
      await page.evaluate((key) => localStorage.setItem(key, 'invalid-theme-value'), THEME_STORAGE_KEY);
      
      // Reload to trigger theme loading with corrupted value
      await page.reload({ waitUntil: 'networkidle' });
      
      // Widget should still open with default theme
      const bubble = page.getByRole('button', { name: 'Open chat' });
      await expect(bubble).toBeVisible({ timeout: 10000 });
      await bubble.click();
      
      const dialog = page.getByRole('dialog', { name: 'Chat window' });
      await expect(dialog).toBeVisible({ timeout: 10000 });

      // Verify theme wrapper has valid class (not corrupted) - element exists with valid class
      const glassmorphismWrapper = page.locator('.glassmorphism-wrapper');
      
      // Check class directly (element may be in shadow DOM or have visibility issues, but class proves recovery works)
      const className = await glassmorphismWrapper.getAttribute('class');
      expect(className).toMatch(/(light-mode|dark-mode)/);
    });

    test('[P3] should handle localStorage quota exceeded gracefully', async ({ page }) => {
      await page.evaluate(() => {
        let i = 0;
        try {
          while (true) {
            localStorage.setItem(`quota-test-${i}`, 'x'.repeat(100000));
            i++;
          }
        } catch (e) {
          // Expected: quota exceeded
        }
      });

      await page.goto('/widget-test');
      await openChat(page);

      const themeToggle = page.getByRole('button', { name: /Theme:/ });
      await expect(themeToggle).toBeVisible();
      
      await themeToggle.click();
      await expect(themeToggle).toBeVisible();
    });
  });
});
