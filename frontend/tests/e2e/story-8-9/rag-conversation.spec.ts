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

    await page.route('**/api/preview/message', async (route) => {
      const request = route.request();
      if (request.method() === 'POST') {
        const body = JSON.parse(request.postData() || '{}');
        const message = body.message?.toLowerCase() || '';

        let responseMessage = "I'm not sure about that. Let me check.";
        let ragEnabled = false;
        let ragSources: string[] = [];

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
    await page.goto('/bot-preview');
    
    await expect(page.locator('[data-testid="preview-chat"]')).toBeVisible({ timeout: 10000 });
    
    const messageInput = page.locator('[data-testid="message-input"]');
    await messageInput.fill('How long does shipping take?');
    await messageInput.press('Enter');

    const botResponse = page.locator('[data-testid="bot-response"]').last();
    await botResponse.waitFor({ state: 'visible', timeout: 10000 });
    
    await expect(botResponse).toContainText('shipping-policy.pdf');
    await expect(botResponse).toContainText('3-5 business days');
  });

  test('[8.9-E2E-002][P1] should fallback gracefully when no documents match @p1 @rag @fallback', async ({ page }) => {
    await page.goto('/bot-preview');

    const messageInput = page.locator('[data-testid="message-input"]');
    await messageInput.fill('What is the meaning of life?');
    await messageInput.press('Enter');

    const botResponse = page.locator('[data-testid="bot-response"]').last();
    await botResponse.waitFor({ state: 'visible', timeout: 10000 });

    await expect(botResponse).not.toContainText('.pdf');
    await expect(botResponse).toContainText(/not sure|check/i);
  });

  test('[8.9-E2E-003][P2] should handle multiple citations @p2 @rag @citations', async ({ page }) => {
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
    await expect(page.locator('[data-testid="preview-chat"]')).toBeVisible({ timeout: 10000 });
    
    const messageInput = page.locator('[data-testid="message-input"]');
    await messageInput.fill('Tell me more');
    await messageInput.press('Enter');

    const botResponse = page.locator('[data-testid="bot-response"]').last();
    await botResponse.waitFor({ state: 'visible', timeout: 15000 });
    await expect(botResponse).toContainText('policy.pdf');
    await expect(botResponse).toContainText('faq.txt');
  });
});
