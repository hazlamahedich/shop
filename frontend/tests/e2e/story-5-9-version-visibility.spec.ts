import { test, expect } from '@playwright/test';

const WIDGET_LOAD_TIMEOUT = 15000;
const VERSION_REGEX = /^\d+\.\d+\.\d+$/;

test.describe('[P1] Widget Version Visibility - Story 5-9', () => {
  test('[P1] should expose version on window.ShopBotWidget after load', async ({ page }) => {
    await page.goto('/widget-bundle-test.html');

    await expect(page.getByRole('button', { name: 'Open chat' })).toBeVisible({ timeout: WIDGET_LOAD_TIMEOUT });

    const version = await page.evaluate(
      () => (window as any).ShopBotWidget?.version
    );

    expect(version).toBeDefined();
    expect(version).toMatch(VERSION_REGEX);
  });

  test('[P0] should call init, unmount, and isMounted methods correctly', async ({ page }) => {
    await page.goto('/widget-bundle-test.html');

    await expect(page.getByRole('button', { name: 'Open chat' })).toBeVisible({ timeout: WIDGET_LOAD_TIMEOUT });

    const beforeInit = await page.evaluate(
      () => (window as any).ShopBotWidget.isMounted()
    );
    expect(beforeInit).toBe(true);

    await page.evaluate(
      () => (window as any).ShopBotWidget.unmount()
    );

    const afterUnmount = await page.evaluate(
      () => (window as any).ShopBotWidget.isMounted()
    );
    expect(afterUnmount).toBe(false);

    await page.evaluate(() => {
      (window as any).ShopBotConfig = { merchantId: 'test-merchant-456' };
      (window as any).ShopBotWidget.init();
    });

    const afterReinit = await page.evaluate(
      () => (window as any).ShopBotWidget.isMounted()
    );
    expect(afterReinit).toBe(true);
  });

  test('[P0] should handle widget script load failure', async ({ page }) => {
    await page.route('**/widget*.{js,ts}', (route) => route.abort('failed'));

    await page.goto('/widget-bundle-test.html');

    await expect
      .poll(
        async () => {
          return await page.evaluate(
            () => typeof (window as any).ShopBotWidget !== 'undefined'
          );
        },
        { timeout: WIDGET_LOAD_TIMEOUT }
      )
      .toBe(false);
  });

  test('[P2] should expose init, unmount, and isMounted methods', async ({ page }) => {
    await page.goto('/widget-bundle-test.html');

    await expect(page.getByRole('button', { name: 'Open chat' })).toBeVisible({ timeout: WIDGET_LOAD_TIMEOUT });

    const api = await page.evaluate(() => ({
      init: typeof (window as any).ShopBotWidget?.init,
      unmount: typeof (window as any).ShopBotWidget?.unmount,
      isMounted: typeof (window as any).ShopBotWidget?.isMounted,
    }));

    expect(api.init).toBe('function');
    expect(api.unmount).toBe('function');
    expect(api.isMounted).toBe('function');
  });
});
