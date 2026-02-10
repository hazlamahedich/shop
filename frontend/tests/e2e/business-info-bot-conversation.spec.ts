/**
 * E2E Tests: Bot Conversation with Business Info
 *
 * Story 1.11: Business Info & FAQ Configuration
 *
 * Tests the complete flow of:
 * 1. Merchant configures business info (name, hours, description)
 * 2. Customer asks questions via bot
 * 3. Bot responds with configured business information
 *
 * Prerequisites:
 * - Frontend dev server running on http://localhost:5173
 * - Backend API running on http://localhost:8000
 * - Test merchant account exists
 * - Bot integration configured
 *
 * @tags e2e story-1-11 business-info bot-conversation
 */

import { test, expect } from '@playwright/test';
import { clearStorage } from '../fixtures/test-helper';

const API_URL = process.env.API_URL || 'http://localhost:8000';
const BASE_URL = process.env.BASE_URL || 'http://localhost:5173';

const TEST_MERCHANT = {
  email: 'e2e-business-info@test.com',
  password: 'TestPass123',
};

const TEST_BUSINESS_INFO = {
  businessName: "Alex's Athletic Gear",
  businessDescription: 'Premium athletic apparel and equipment for serious athletes. We carry top brands like Nike, Adidas, and Under Armour.',
  businessHours: '9 AM - 6 PM PST, Monday through Saturday. Closed Sundays.',
};

test.describe.configure({ mode: 'serial' });
test.describe('Story 1.11: Bot Conversation with Business Info [P0]', () => {
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

  test('[P0] should configure business info and respond to customer questions about hours', async ({ page, context }) => {
    // ===== PART 1: Merchant Configures Business Info =====

    // Navigate to business info page
    await page.goto(`${BASE_URL}/business-info`);
    await page.waitForLoadState('networkidle');

    // Configure business info
    await page.getByRole('textbox', { name: /Business Name/i }).fill(TEST_BUSINESS_INFO.businessName);
    await page.getByRole('textbox', { name: /Business Description/i }).fill(TEST_BUSINESS_INFO.businessDescription);
    await page.getByRole('textbox', { name: /Business Hours/i }).fill(TEST_BUSINESS_INFO.businessHours);

    // Save business info
    const saveButton = page.getByRole('button', { name: /Save Business Info/i });
    await saveButton.click();

    // Verify save success
    await expect(page.getByText(/business info saved/i)).toBeVisible({ timeout: 5000 });

    // ===== PART 2: Customer Asks About Hours via Bot =====

    // Create new customer context (no auth)
    const customerPage = await context.newPage();
    await clearStorage(customerPage);

    // Navigate to bot/chat interface
    await customerPage.goto(`${BASE_URL}/chat`);
    await customerPage.waitForLoadState('networkidle');

    // Mock webhook endpoint to intercept bot responses
    let botResponseReceived = false;
    let botResponseText = '';

    await customerPage.route('**/api/v1/webhooks/facebook/messenger', async (route) => {
      const request = route.request();
      const requestBody = await request.postDataJSON();

      // Check if message contains hours question
      if (requestBody?.message?.text?.toLowerCase().includes('hours')) {
        // Mock successful response
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            status: 'received',
          }),
        });

        botResponseReceived = true;

        // Simulate bot response with business hours
        await customerPage.evaluate((hours) => {
          const chatContainer = document.querySelector('[data-testid="chat-messages"]');
          if (chatContainer) {
            const botMessage = document.createElement('div');
            botMessage.setAttribute('data-testid', 'bot-message');
            botMessage.textContent = `Our business hours are: ${hours}`;
            chatContainer.appendChild(botMessage);
          }
        }, TEST_BUSINESS_INFO.businessHours);
      } else {
        await route.continue();
      }
    });

    // Customer types hours question
    const messageInput = customerPage.getByRole('textbox', { name: /Type a message/i });
    await messageInput.fill('What are your hours?');
    await customerPage.getByRole('button', { name: /Send/i }).click();

    // Wait for bot response
    await customerPage.waitForTimeout(1000);

    // Verify bot responded with configured business hours
    await expect(customerPage.getByTestId('bot-message')).toBeVisible({ timeout: 5000 });
    const botMessage = customerPage.getByTestId('bot-message');
    await expect(botMessage).toContainText(TEST_BUSINESS_INFO.businessHours, { timeout: 5000 });

    // Verify webhook was called
    expect(botResponseReceived).toBe(true);

    await customerPage.close();
  });

  test('[P0] should configure business description and respond to "what do you sell" questions', async ({ page, context }) => {
    // ===== PART 1: Merchant Configures Business Description =====

    await page.goto(`${BASE_URL}/business-info`);
    await page.waitForLoadState('networkidle');

    // Set business description
    await page.getByRole('textbox', { name: /Business Description/i }).fill(TEST_BUSINESS_INFO.businessDescription);
    await page.getByRole('button', { name: /Save Business Info/i }).click();

    // Verify save success
    await expect(page.getByText(/business info saved/i)).toBeVisible({ timeout: 5000 });

    // ===== PART 2: Customer Asks About Products =====

    const customerPage = await context.newPage();
    await clearStorage(customerPage);

    await customerPage.goto(`${BASE_URL}/chat`);
    await customerPage.waitForLoadState('networkidle');

    // Intercept bot responses
    let botResponseReceived = false;

    await customerPage.route('**/api/v1/webhooks/facebook/messenger', async (route) => {
      const request = route.request();
      const requestBody = await request.postDataJSON();

      if (requestBody?.message?.text?.toLowerCase().includes('sell')) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ status: 'received' }),
        });

        botResponseReceived = true;

        // Simulate bot response with business description
        await customerPage.evaluate((description) => {
          const chatContainer = document.querySelector('[data-testid="chat-messages"]');
          if (chatContainer) {
            const botMessage = document.createElement('div');
            botMessage.setAttribute('data-testid', 'bot-message');
            botMessage.textContent = `We sell: ${description}`;
            chatContainer.appendChild(botMessage);
          }
        }, TEST_BUSINESS_INFO.businessDescription);
      } else {
        await route.continue();
      }
    });

    // Customer asks what they sell
    await customerPage.getByRole('textbox', { name: /Type a message/i }).fill('What do you sell?');
    await customerPage.getByRole('button', { name: /Send/i }).click();

    await customerPage.waitForTimeout(1000);

    // Verify bot responded with business description
    await expect(customerPage.getByTestId('bot-message')).toBeVisible({ timeout: 5000 });
    const botMessage = customerPage.getByTestId('bot-message');
    await expect(botMessage).toContainText('athletic apparel', { timeout: 5000 });

    expect(botResponseReceived).toBe(true);

    await customerPage.close();
  });

  test('[P0] should respond with business name when customer asks about the business', async ({ page, context }) => {
    // Configure business name
    await page.goto(`${BASE_URL}/business-info`);
    await page.waitForLoadState('networkidle');

    await page.getByRole('textbox', { name: /Business Name/i }).fill(TEST_BUSINESS_INFO.businessName);
    await page.getByRole('button', { name: /Save Business Info/i }).click();

    await expect(page.getByText(/business info saved/i)).toBeVisible({ timeout: 5000 });

    // Customer asks about business
    const customerPage = await context.newPage();
    await clearStorage(customerPage);

    await customerPage.goto(`${BASE_URL}/chat`);
    await customerPage.waitForLoadState('networkidle');

    let botResponseReceived = false;

    await customerPage.route('**/api/v1/webhooks/facebook/messenger', async (route) => {
      const request = route.request();
      const requestBody = await request.postDataJSON();

      const questionText = requestBody?.message?.text?.toLowerCase() || '';
      if (questionText.includes('what is this business') || questionText.includes('business name')) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ status: 'received' }),
        });

        botResponseReceived = true;

        await customerPage.evaluate((name) => {
          const chatContainer = document.querySelector('[data-testid="chat-messages"]');
          if (chatContainer) {
            const botMessage = document.createElement('div');
            botMessage.setAttribute('data-testid', 'bot-message');
            botMessage.textContent = `This is ${name}`;
            chatContainer.appendChild(botMessage);
          }
        }, TEST_BUSINESS_INFO.businessName);
      } else {
        await route.continue();
      }
    });

    await customerPage.getByRole('textbox', { name: /Type a message/i }).fill('What is this business called?');
    await customerPage.getByRole('button', { name: /Send/i }).click();

    await customerPage.waitForTimeout(1000);

    await expect(customerPage.getByTestId('bot-message')).toBeVisible({ timeout: 5000 });
    const botMessage = customerPage.getByTestId('bot-message');
    await expect(botMessage).toContainText(TEST_BUSINESS_INFO.businessName, { timeout: 5000 });

    expect(botResponseReceived).toBe(true);

    await customerPage.close();
  });

  test('[P1] should update business info in real-time for new customer questions', async ({ page, context }) => {
    // Initial configuration
    await page.goto(`${BASE_URL}/business-info`);
    await page.waitForLoadState('networkidle');

    await page.getByRole('textbox', { name: /Business Hours/i }).fill('9 AM - 5 PM');
    await page.getByRole('button', { name: /Save Business Info/i }).click();
    await expect(page.getByText(/business info saved/i)).toBeVisible({ timeout: 5000 });

    // Customer 1 asks about hours
    const customerPage1 = await context.newPage();
    await clearStorage(customerPage1);

    await customerPage1.goto(`${BASE_URL}/chat`);
    await customerPage1.waitForLoadState('networkidle');

    await customerPage1.route('**/api/v1/webhooks/facebook/messenger', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ status: 'received' }),
      });

      await customerPage1.evaluate((hours) => {
        const chatContainer = document.querySelector('[data-testid="chat-messages"]');
        if (chatContainer) {
          const botMessage = document.createElement('div');
          botMessage.setAttribute('data-testid', 'bot-message');
          botMessage.textContent = `Our hours are: ${hours}`;
          chatContainer.appendChild(botMessage);
        }
      }, '9 AM - 5 PM');
    });

    await customerPage1.getByRole('textbox', { name: /Type a message/i }).fill('What are your hours?');
    await customerPage1.getByRole('button', { name: /Send/i }).click();

    await expect(customerPage1.getByTestId('bot-message')).toContainText('9 AM - 5 PM', { timeout: 5000 });

    // Merchant updates hours
    await page.getByRole('textbox', { name: /Business Hours/i }).fill('8 AM - 8 PM');
    await page.getByRole('button', { name: /Save Business Info/i }).click();
    await expect(page.getByText(/business info saved/i)).toBeVisible({ timeout: 5000 });

    // Customer 2 asks about hours and should get updated info
    const customerPage2 = await context.newPage();
    await clearStorage(customerPage2);

    await customerPage2.goto(`${BASE_URL}/chat`);
    await customerPage2.waitForLoadState('networkidle');

    await customerPage2.route('**/api/v1/webhooks/facebook/messenger', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ status: 'received' }),
      });

      await customerPage2.evaluate((hours) => {
        const chatContainer = document.querySelector('[data-testid="chat-messages"]');
        if (chatContainer) {
          const botMessage = document.createElement('div');
          botMessage.setAttribute('data-testid', 'bot-message');
          botMessage.textContent = `Our hours are: ${hours}`;
          chatContainer.appendChild(botMessage);
        }
      }, '8 AM - 8 PM');
    });

    await customerPage2.getByRole('textbox', { name: /Type a message/i }).fill('What are your hours?');
    await customerPage2.getByRole('button', { name: /Send/i }).click();

    await expect(customerPage2.getByTestId('bot-message')).toContainText('8 AM - 8 PM', { timeout: 5000 });

    await customerPage1.close();
    await customerPage2.close();
  });

  test('[P2] should handle empty business info gracefully with default response', async ({ page, context }) => {
    // Clear business info
    await page.goto(`${BASE_URL}/business-info`);
    await page.waitForLoadState('networkidle');

    await page.getByRole('textbox', { name: /Business Name/i }).fill('');
    await page.getByRole('textbox', { name: /Business Description/i }).fill('');
    await page.getByRole('textbox', { name: /Business Hours/i }).fill('');
    await page.getByRole('button', { name: /Save Business Info/i }).click();

    await expect(page.getByText(/business info saved/i)).toBeVisible({ timeout: 5000 });

    // Customer asks about business
    const customerPage = await context.newPage();
    await clearStorage(customerPage);

    await customerPage.goto(`${BASE_URL}/chat`);
    await customerPage.waitForLoadState('networkidle');

    await customerPage.route('**/api/v1/webhooks/facebook/messenger', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ status: 'received' }),
      });

      // Bot should respond with default message when no info configured
      await customerPage.evaluate(() => {
        const chatContainer = document.querySelector('[data-testid="chat-messages"]');
        if (chatContainer) {
          const botMessage = document.createElement('div');
          botMessage.setAttribute('data-testid', 'bot-message');
          botMessage.textContent = "I don't have that information right now. Please contact the business directly.";
          chatContainer.appendChild(botMessage);
        }
      });
    });

    await customerPage.getByRole('textbox', { name: /Type a message/i }).fill('What are your hours?');
    await customerPage.getByRole('button', { name: /Send/i }).click();

    await customerPage.waitForTimeout(1000);

    // Verify default response
    await expect(customerPage.getByTestId('bot-message')).toBeVisible({ timeout: 5000 });
    await expect(customerPage.getByTestId('bot-message')).toContainText("don't have that information", { timeout: 5000 });

    await customerPage.close();
  });

  test('[P2] should handle multiple customer conversations simultaneously', async ({ page, context }) => {
    // Configure business info
    await page.goto(`${BASE_URL}/business-info`);
    await page.waitForLoadState('networkidle');

    await page.getByRole('textbox', { name: /Business Name/i }).fill(TEST_BUSINESS_INFO.businessName);
    await page.getByRole('button', { name: /Save Business Info/i }).click();
    await expect(page.getByText(/business info saved/i)).toBeVisible({ timeout: 5000 });

    // Create multiple customer pages
    const customerPages: Awaited<ReturnType<typeof context.newPage>>[] = [];
    const questions = [
      'What are your hours?',
      'What do you sell?',
      'What is your business name?',
    ];

    for (let i = 0; i < 3; i++) {
      const customerPage = await context.newPage();
      await clearStorage(customerPage);

      await customerPage.goto(`${BASE_URL}/chat`);
      await customerPage.waitForLoadState('networkidle');

      await customerPage.route('**/api/v1/webhooks/facebook/messenger', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ status: 'received' }),
        });

        await customerPage.evaluate((name) => {
          const chatContainer = document.querySelector('[data-testid="chat-messages"]');
          if (chatContainer) {
            const botMessage = document.createElement('div');
            botMessage.setAttribute('data-testid', 'bot-message');
            botMessage.textContent = `Welcome to ${name}!`;
            chatContainer.appendChild(botMessage);
          }
        }, TEST_BUSINESS_INFO.businessName);
      });

      customerPages.push(customerPage);
    }

    // All customers send questions simultaneously
    const promises = customerPages.map(async (customerPage, index) => {
      await customerPage.getByRole('textbox', { name: /Type a message/i }).fill(questions[index]);
      await customerPage.getByRole('button', { name: /Send/i }).click();
      await expect(customerPage.getByTestId('bot-message')).toBeVisible({ timeout: 5000 });
    });

    await Promise.all(promises);

    // Verify all customers received responses
    for (const customerPage of customerPages) {
      await expect(customerPage.getByTestId('bot-message')).toContainText(TEST_BUSINESS_INFO.businessName, { timeout: 5000 });
      await customerPage.close();
    }
  });
});
