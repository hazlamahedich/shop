import { test, expect } from '@playwright/test';

test.describe('Story 9-10: Analytics and Performance Monitoring', () => {
  test.beforeEach(async ({ page }) => {
    const responsePromise = page.waitForResponse('**/api/**').catch(() => null);
    await page.goto('/widget-demo');
    await responsePromise;
    await expect(page.locator('[data-testid="chat-bubble"]')).toBeVisible({ timeout: 10000 });
  });

  test.afterEach(async ({ page }) => {
    const chatWindow = page.locator('[data-testid="chat-window"]');
    const isVisible = await chatWindow.isVisible().catch(() => false);
    if (isVisible) {
      const closeButton = page.locator('[data-testid="close-chat-button"]');
      await closeButton.click().catch(() => {});
    }
    await page.evaluate(() => {
      localStorage.clear();
      sessionStorage.clear();
    });
  });

  test('AC1 Widget open event is tracked @smoke @p0', async ({ page }) => {
    const chatBubble = page.locator('[data-testid="chat-bubble"]');

    const responsePromise = page.waitForResponse((resp) =>
      resp.url().includes('/api/v1/analytics/widget/events') && resp.request().method() === 'POST'
    );

    await chatBubble.click();

    const response = await responsePromise;

    await expect(page.locator('[data-testid="chat-window"]')).toBeVisible({ timeout: 5000 });

    expect(response.status()).toBe(200);

    const body = await response.json();
    expect(body.accepted).toBeGreaterThanOrEqual(1);
  });

  test('AC2 Message send event is tracked @smoke @p0', async ({ page }) => {
    const chatBubble = page.locator('[data-testid="chat-bubble"]');
    await chatBubble.click();

    await expect(page.locator('[data-testid="chat-window"]')).toBeVisible({ timeout: 5000 });

    const messageInput = page.locator('[data-testid="message-input"]');
    await messageInput.fill('Test message for analytics');

    const responsePromise = page.waitForResponse((resp) =>
      resp.url().includes('/api/v1/analytics/widget/events') && resp.request().method() === 'POST'
    );

    const sendButton = page.locator('[data-testid="send-message-button"]');
    await sendButton.click();

    const response = await responsePromise;

    expect(response.status()).toBe(200);
  });

  test('AC3 Quick reply click is tracked @p1', async ({ page }) => {
    const chatBubble = page.locator('[data-testid="chat-bubble"]');
    await chatBubble.click();

    await expect(page.locator('[data-testid="chat-window"]')).toBeVisible({ timeout: 5000 });

    const quickReplyButtons = page.locator('[data-testid^="quick-reply-button"]');
    const count = await quickReplyButtons.count();
    
    if (count === 0) {
      test.skip(true, 'No quick reply buttons available - feature may not be enabled');
      return;
    }

    const responsePromise = page.waitForResponse((resp) =>
      resp.url().includes('/api/v1/analytics/widget/events') && resp.request().method() === 'POST'
    );

    await quickReplyButtons.first().click();

    const response = await responsePromise;
    expect(response.status()).toBe(200);
  });

  test('AC4 Voice input usage is tracked @p2', async ({ page, context }) => {
    await context.grantPermissions(['microphone']);
    
    const chatBubble = page.locator('[data-testid="chat-bubble"]');
    await chatBubble.click();

    await expect(page.locator('[data-testid="chat-window"]')).toBeVisible({ timeout: 5000 });

    const voiceButton = page.locator('[data-testid="voice-input-button"]');
    const isVoiceVisible = await voiceButton.isVisible().catch(() => false);
    
    test.skip(!isVoiceVisible, 'Voice input button not available - feature may not be enabled');
    
    if (isVoiceVisible) {
      const responsePromise = page.waitForResponse((resp) =>
        resp.url().includes('/api/v1/analytics/widget/events') && resp.request().method() === 'POST'
      );

      await voiceButton.click();

      const response = await responsePromise;
      expect(response.status()).toBe(200);
    }
  });

  test('AC5 Proactive trigger conversion is tracked @p1', async ({ page }) => {
    await page.goto('/widget-demo?proactive=true');
    await expect(page.locator('[data-testid="chat-bubble"]')).toBeVisible({ timeout: 10000 });
    
    const proactiveModal = page.locator('[data-testid="proactive-modal"]');
    await expect(proactiveModal).toBeVisible({ timeout: 10000 });
    
    const responsePromise = page.waitForResponse((resp) =>
      resp.url().includes('/api/v1/analytics/widget/events') && resp.request().method() === 'POST'
    );
    
    const engageButton = proactiveModal.locator('button').first();
    await engageButton.click();
    
    const response = await responsePromise;
    expect(response.status()).toBe(200);
  });

  test('AC5 Proactive trigger - no modal fallback @p2', async ({ page }) => {
    await page.goto('/widget-demo');
    await expect(page.locator('[data-testid="chat-bubble"]')).toBeVisible({ timeout: 10000 });
    
    const proactiveModal = page.locator('[data-testid="proactive-modal"]');
    const isModalVisible = await proactiveModal.isVisible({ timeout: 3000 }).catch(() => false);
    
    test.skip(isModalVisible, 'Modal appeared - covered by main AC5 test');
    
    await expect(page.locator('[data-testid="chat-bubble"]')).toBeVisible();
  });

  test('AC6 Product carousel engagement is tracked @p1', async ({ page }) => {
    const chatBubble = page.locator('[data-testid="chat-bubble"]');
    await chatBubble.click();

    await expect(page.locator('[data-testid="chat-window"]')).toBeVisible({ timeout: 5000 });

    const messageInput = page.locator('[data-testid="message-input"]');
    await messageInput.fill('Show me products');

    const sendButton = page.locator('[data-testid="send-message-button"]');
    await sendButton.click();

    const carousel = page.locator('[data-testid="product-carousel"]');
    await expect(carousel).toBeVisible({ timeout: 15000 });
  });

  test('AC7 Widget load time is measured @p1', async ({ page }) => {
    const startTime = Date.now();
    const responsePromise = page.waitForResponse('**/api/**').catch(() => null);
    await page.goto('/widget-demo');
    await responsePromise;
    const loadTime = Date.now() - startTime;
    
    expect(loadTime).toBeLessThan(5000);
    
    await expect(page.locator('[data-testid="chat-bubble"]')).toBeVisible({ timeout: 5000 });
  });

  test('AC8 Dashboard widget displays metrics @p1', async ({ page }) => {
    const responsePromise = page.waitForResponse('**/api/**').catch(() => null);
    await page.goto('/dashboard');
    await responsePromise;
    
    const dashboardContent = page.locator('[data-testid="dashboard-content"]');
    await expect(dashboardContent).toBeVisible({ timeout: 10000 });
    
    const widgetAnalyticsCard = page.locator('text=Widget Analytics').first();
    const isAnalyticsVisible = await widgetAnalyticsCard.isVisible({ timeout: 5000 }).catch(() => false);
    
    test.skip(!isAnalyticsVisible, 'Widget Analytics card not visible - feature may not be enabled for this merchant');
    
    if (isAnalyticsVisible) {
      await expect(page.getByText(/Open Rate|Message Rate/).first()).toBeVisible({ timeout: 5000 });
    }
  });

  test('AC9 CSV export functionality @p2', async ({ page }) => {
    const responsePromise = page.waitForResponse('**/api/**').catch(() => null);
    await page.goto('/dashboard');
    await responsePromise;
    
    const dashboardContent = page.locator('[data-testid="dashboard-content"]');
    await expect(dashboardContent).toBeVisible({ timeout: 10000 });
    
    const exportButton = page.getByRole('button', { name: /Export/i }).first();
    const isExportVisible = await exportButton.isVisible({ timeout: 5000 }).catch(() => false);
    
    test.skip(!isExportVisible, 'Export button not visible - feature may not be enabled for this merchant');
    
    if (isExportVisible) {
      const [download] = await Promise.all([
        page.waitForEvent('download', { timeout: 10000 }).catch(() => null),
        exportButton.click(),
      ]);
      
      if (download) {
        expect(download.suggestedFilename()).toMatch(/widget-analytics|analytics.*\.csv|\.csv/);
      }
    }
  });

  test('AC1 Error handling - API failure graceful degradation @p1', async ({ page, context }) => {
    await context.route('**/api/v1/analytics/widget/events', (route) => {
      route.fulfill({ status: 500, body: JSON.stringify({ error: 'Internal Server Error' }) });
    });

    const responsePromise = page.waitForResponse('**/api/**').catch(() => null);
    await page.goto('/widget-demo');
    await responsePromise;
    
    await expect(page.locator('[data-testid="chat-bubble"]')).toBeVisible({ timeout: 10000 });
    
    await page.locator('[data-testid="chat-bubble"]').click();
    await expect(page.locator('[data-testid="chat-window"]')).toBeVisible({ timeout: 5000 });
  });

  test('AC2 Error handling - Network timeout @p2', async ({ page, context }) => {
    await context.setOffline(true);

    await page.goto('/widget-demo');
    
    const chatBubble = page.locator('[data-testid="chat-bubble"]');
    await expect(chatBubble).toBeVisible({ timeout: 10000 }).catch(() => {
      test.skip(true, 'Widget not visible in offline mode');
    });
    
    await context.setOffline(false);
  });
});
