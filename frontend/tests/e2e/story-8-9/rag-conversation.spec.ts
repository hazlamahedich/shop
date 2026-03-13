/**
 * E2E Test: RAG Conversation Flow
 * 
 * Story 8-9: Testing & Quality Assurance
 * 
 * Tests chat functionality with Knowledge Base context (RAG).
 * Uses /bot-preview route which has the PreviewChat component.
 * 
 * @tags e2e knowledge-base story-8-9 rag conversation
 */

import { test, expect } from '@playwright/test';
import { setupKnowledgeBaseMocks, createMockDocument } from '../../helpers/knowledge-base-mocks';

test.describe('Story 8-9: RAG Conversation @knowledge-base @story-8-9', () => {
  
  test.beforeEach(async ({ page }) => {
    // Setup standard KB mocks
    await setupKnowledgeBaseMocks(page, {
      onboardingMode: 'general',
      documents: [
        createMockDocument({ 
          id: 1, 
          filename: 'shipping-policy.pdf', 
          status: 'ready' 
        })
      ]
    });

    // Mock preview chat message API with RAG response
    await page.route('**/api/preview/message', async (route) => {
      const request = route.request();
      if (request.method() === 'POST') {
        const body = JSON.parse(request.postData() || '{}');
        const message = body.message?.toLowerCase() || '';

        let responseMessage = "I'm not sure about that. Let me check.";
        let ragEnabled = false;
        let ragSources = null;

        if (message.includes('shipping')) {
          responseMessage = "Based on our shipping-policy.pdf, shipping takes 3-5 business days.";
          ragEnabled = true;
          ragSources = ["shipping-policy.pdf"];
        }

        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            status: 'success',
            data: {
              message: responseMessage,
              intent: 'general',
              confidence: 0.95,
              metadata: {
                rag_enabled: ragEnabled,
                rag_sources: ragSources
              }
            }
          })
        });
      }
    });
  });

  test('[8.9-E2E-001][P0] should receive RAG-enhanced response with citations @p0 @critical @smoke @rag', async ({ page }) => {
    // 1. Go to Bot Preview page (correct route)
    await page.goto('/bot-preview');
    
    // 2. Wait for preview chat to be visible
    await expect(page.locator('[data-testid="preview-chat"]')).toBeVisible({ timeout: 10000 });

    // 3. Send message about shipping
    const messageInput = page.locator('[data-testid="message-input"]');
    await messageInput.fill('How long does shipping take?');
    await messageInput.press('Enter');

    // 4. Wait for bot response
    await page.waitForSelector('[data-testid="bot-response').last',:contains', 'shipping-policy.pdf', { timeout: 10000 });
    
    // 5. Verify response contains the cited document
    await expect(botResponse).toContainText('shipping-policy.pdf');
    await expect(botResponse).toContainText('3-5 business days');
  });

  test('[8.9-E2E-002][P1] should fallback gracefully when no documents match @p1 @rag @fallback', async ({ page }) => {
    // 1. Go to Bot Preview page
    await page.goto('/bot-preview');

    // 2. Send message about unrelated topic
    const messageInput = page.locator('[data-testid="message-input"]');
    await messageInput.fill('What is the meaning of life?');
    await messageInput.press('Enter');

    // 3. Verify general response without citations
    const botResponse = page.locator('[data-testid="bot-response"]').last();
    await expect(botResponse).not.toContainText('.pdf', { timeout: 10000 });
    await expect(botResponse).toContainText(/not sure|check/i);
  });

  test('[8.9-E2E-003][P2] should handle multiple citations @p2 @rag @citations', async ({ page }) => {
    // Update mock for multiple citations
    await page.route('**/api/preview/message', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          status: 'success',
          data: {
            message: "Our policy (policy.pdf) and FAQ (faq.txt) both confirm this.",
            intent: 'general',
            confidence: 0.9,
            metadata: {
              rag_enabled: true,
              rag_sources: ["policy.pdf", "faq.txt"]
            }
          }
        })
      });
    });

    await page.goto('/bot-preview');
    const messageInput = page.locator('[data-testid="message-input"]');
    await messageInput.fill('Tell me more');
    await messageInput.press('Enter');

    const botResponse = page.locator('[data-testid="bot-response"]').last();
    await expect(botResponse).toContainText('policy.pdf', { timeout: 10000 });
    await expect(botResponse).toContainText('faq.txt');
  });
});

  test('[8.9-E2E-002][P1] should fallback gracefully when no documents match @p1 @rag @fallback', async ({ page }) => {
    // 1. Go to Bot Preview page
    await page.goto('/bot-preview');
    await expect(page.locator('[data-testid="preview-chat"]')).toBeVisible();

    // 2. Send message about unrelated topic
    const messageInput = page.locator('[data-testid="message-input"]');
    await messageInput.fill('What is the meaning of life?');
    await messageInput.press('Enter');

    // 3. Verify general response without citations
    const botResponse = page.locator('[data-testid="bot-response"]').last();
    await expect(botResponse).not.toContainText('.pdf', { timeout: 10000 });
    await expect(botResponse).toContainText(/not sure|check/i);
  });

  test('[8.9-E2E-003][P2] should handle multiple citations @p2 @rag @citations', async ({ page }) => {
    // Update mock for multiple citations
    await page.route('**/api/preview/message', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          status: 'success',
          data: {
            message: "Our policy (policy.pdf) and FAQ (faq.txt) both confirm this.",
            intent: 'general',
            confidence: 0.9,
            metadata: {
              rag_enabled: true,
              rag_sources: ["policy.pdf", "faq.txt"]
            }
          }
        })
      });
    });

    await page.goto('/bot-preview');
    const messageInput = page.locator('[data-testid="message-input"]');
    await messageInput.fill('Tell me more');
    await messageInput.press('Enter');

    const botResponse = page.locator('[data-testid="bot-response"]').last();
    await expect(botResponse).toContainText('policy.pdf', { timeout: 10000 });
    await expect(botResponse).toContainText('faq.txt');
  });
});

    // Mock widget message API with RAG response
    await page.route('**/api/widget/message', async (route) => {
      const request = route.request();
      if (request.method() === 'POST') {
        const body = JSON.parse(request.postData() || '{}');
        const message = body.message?.toLowerCase() || '';

        let responseMessage = "I'm not sure about that. Let me check.";
        let ragEnabled = false;
        let ragSources = null;

        if (message.includes('shipping')) {
          responseMessage = "Based on our shipping-policy.pdf, shipping takes 3-5 business days.";
          ragEnabled = true;
          ragSources = ["shipping-policy.pdf"];
        }

        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            status: 'success',
            data: {
              message: responseMessage,
              intent: 'general',
              confidence: 0.95,
              metadata: {
                rag_enabled: ragEnabled,
                rag_sources: ragSources
              }
            }
          })
        });
      }
    });
  });

  test('[8.9-E2E-001][P0] should receive RAG-enhanced response with citations @p0 @critical @smoke @rag', async ({ page }) => {
    // 1. Go to Bot Preview page (correct route)
    await page.goto('/bot-preview');
    
    // Wait for page to load
    await expect(page.locator('[data-testid="preview-chat"]')).toBeVisible({ timeout: 10000 });

    // 2. Send message about shipping
    const chatInput = page.locator('[data-testid="message-input"]');
    await chatInput.fill('How long does shipping take?');
    await chatInput.press('Enter');

    // 3. Wait for response and verify it contains the cited document
    const botResponse = page.locator('[data-testid="bot-response"]').last();
    await expect(botResponse).toBeVisible({ timeout: 15000 });
    await expect(botResponse).toContainText('shipping-policy.pdf');
    await expect(botResponse).toContainText('3-5 business days');
  });

  test('[8.9-E2E-002][P1] should fallback gracefully when no documents match @p1 @rag @fallback', async ({ page }) => {
    // 1. Go to Bot Preview page
    await page.goto('/bot-preview');
    await expect(page.locator('[data-testid="preview-chat"]')).toBeVisible({ timeout: 10000 });

    // 2. Send message about unrelated topic
    const chatInput = page.locator('[data-testid="message-input"]');
    await chatInput.fill('What is the meaning of life?');
    await chatInput.press('Enter');

    // 3. Verify general response without citations
    const botResponse = page.locator('[data-testid="bot-response"]').last();
    await expect(botResponse).toBeVisible({ timeout: 15000 });
    await expect(botResponse).not.toContainText('.pdf');
    await expect(botResponse).toContainText(/not sure|check/i);
  });

  test('[8.9-E2E-003][P2] should handle multiple citations @p2 @rag @citations', async ({ page }) => {
    // Update mock for multiple citations
    await page.route('**/api/widget/message', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          status: 'success',
          data: {
            message: "Our policy (policy.pdf) and FAQ (faq.txt) both confirm this.",
            intent: 'general',
            confidence: 0.9,
            metadata: {
              rag_enabled: true,
              rag_sources: ["policy.pdf", "faq.txt"]
            }
          }
        })
      });
    });

    await page.goto('/bot-preview');
    await expect(page.locator('[data-testid="preview-chat"]')).toBeVisible({ timeout: 10000 });
    
    const chatInput = page.locator('[data-testid="message-input"]');
    await chatInput.fill('Tell me more');
    await chatInput.press('Enter');

    const botResponse = page.locator('[data-testid="bot-response"]').last();
    await expect(botResponse).toBeVisible({ timeout: 15000 });
    await expect(botResponse).toContainText('policy.pdf');
    await expect(botResponse).toContainText('faq.txt');
  });
});
