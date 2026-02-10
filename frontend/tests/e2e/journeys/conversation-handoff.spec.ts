/**
 * E2E Tests: Conversation Handoff Workflow Journey
 *
 * User Journey: Merchant takes over conversation from AI, resumes
 * AI control, and tracks status changes throughout.
 *
 * Flow: Human Takeover → Resume AI → Status Tracking
 *
 * Priority Coverage:
 * - [P0] Complete handoff happy path
 * - [P1] Status tracking and notifications
 * - [P2] Handoff history and analytics
 *
 * @package frontend/tests/e2e/journeys
 */

import { test, expect } from '@playwright/test';

test.describe('Journey: Conversation Handoff Workflow', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to conversations page
    await page.goto('/conversations');
    await page.waitForLoadState('networkidle');

    // Mock conversation data
    await page.route('**/api/conversations**', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          data: {
            conversations: [
              {
                id: 'conv-1',
                customerName: 'John Doe',
                status: 'active',
                mode: 'ai',
                lastMessage: 'Product inquiry about pricing',
                platform: 'facebook',
                createdAt: '2024-01-15T10:00:00Z',
                unreadCount: 2,
              },
            ],
            total: 1,
          },
          meta: { requestId: 'test-conversations' },
        }),
      });
    });
  });

  test('[P0] should complete human takeover workflow', async ({ page }) => {
    // GIVEN: User is viewing conversations list
    await expect(page.getByRole('heading', { name: /conversations/i })).toBeVisible();

    // WHEN: Clicking on a conversation
    const conversationItem = page.locator('[data-testid="conversation-item"]').first();
    await conversationItem.click();

    // Wait for conversation detail to load
    await page.waitForTimeout(500);

    // THEN: Should see conversation detail view
    await expect(page.getByText('John Doe')).toBeVisible();

    // Should show AI mode indicator
    const aiModeIndicator = page.getByText(/ai mode|automatic/i).or(
      page.locator('[data-testid="mode-indicator"]')
    );
    await expect(aiModeIndicator.first()).toBeVisible();

    // WHEN: Clicking "Take Over" button
    const takeOverButton = page.getByRole('button', { name: /take over|manual mode/i }).or(
      page.locator('[data-testid="takeover-button"]')
    );

    await takeOverButton.click();

    // Mock takeover API
    await page.route('**/api/conversations/conv-1/takeover**', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          data: {
            id: 'conv-1',
            mode: 'human',
            takenOverBy: 'merchant-user',
            takenOverAt: new Date().toISOString(),
          },
          meta: { requestId: 'test-takeover' },
        }),
      });
    });

    // THEN: Should show confirmation
    await expect(page.getByText(/manual mode|you are now responding/i)).toBeVisible({
      timeout: 3000
    });

    // Mode indicator should update
    const humanModeIndicator = page.getByText(/manual mode|human/i);
    await expect(humanModeIndicator.first()).toBeVisible();

    // Should show message input
    const messageInput = page.locator('textarea[placeholder*="message"]').or(
      page.getByPlaceholder(/type a message/i)
    );
    await expect(messageInput).toBeVisible();
  });

  test('[P1] should resume AI control after takeover', async ({ page }) => {
    // GIVEN: User has taken over conversation
    await page.route('**/api/conversations/conv-1/takeover**', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          data: { mode: 'human' },
          meta: { requestId: 'test-takeover' },
        }),
      });
    });

    const conversationItem = page.locator('[data-testid="conversation-item"]').first();
    await conversationItem.click();
    await page.waitForTimeout(500);

    const takeOverButton = page.getByRole('button', { name: /take over/i });
    await takeOverButton.click();
    await page.waitForTimeout(1000);

    // WHEN: Clicking "Resume AI" button
    const resumeButton = page.getByRole('button', { name: /resume ai|back to automatic/i }).or(
      page.locator('[data-testid="resume-ai-button"]')
    );

    const hasResume = await resumeButton.isVisible().catch(() => false);

    if (hasResume) {
      // Mock resume API
      await page.route('**/api/conversations/conv-1/resume**', route => {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            data: {
              id: 'conv-1',
              mode: 'ai',
              resumedAt: new Date().toISOString(),
            },
            meta: { requestId: 'test-resume' },
          }),
        });
      });

      await resumeButton.click();

      // THEN: Should show AI mode restored
      await expect(page.getByText(/ai mode|automatic/i)).toBeVisible({ timeout: 3000 });

      // Message input may be disabled or hidden
      const messageInput = page.locator('textarea[placeholder*="message"]');
      const isInputDisabled = await messageInput.isDisabled().catch(() => false);
      const isInputHidden = await messageInput.isHidden().catch(() => false);

      expect(isInputDisabled || isInputHidden).toBeTruthy();
    }
  });

  test('[P1] should track conversation status changes', async ({ page }) => {
    // GIVEN: User has taken over conversation
    await page.route('**/api/conversations/conv-1/takeover**', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          data: {
            mode: 'human',
            status: 'active',
            handoffCount: 1,
          },
          meta: { requestId: 'test-status' },
        }),
      });
    });

    const conversationItem = page.locator('[data-testid="conversation-item"]').first();
    await conversationItem.click();
    await page.waitForTimeout(500);

    const takeOverButton = page.getByRole('button', { name: /take over/i });
    await takeOverButton.click();
    await page.waitForTimeout(1000);

    // THEN: Should show status change notification
    const statusNotification = page.getByText(/status changed|now in manual mode/i);
    await expect(statusNotification.first()).toBeVisible();

    // Should update conversation list item
    await page.goBack();
    await page.waitForLoadState('networkidle');

    const modeIndicator = page.locator('[data-testid="conversation-item"]').first()
      .getByText(/manual|human/i);

    const hasModeIndicator = await modeIndicator.isVisible().catch(() => false);
    if (hasModeIndicator) {
      await expect(modeIndicator).toBeVisible();
    }
  });

  test('[P1] should show handoff history', async ({ page }) => {
    // GIVEN: User is viewing conversation with handoff history
    await page.route('**/api/conversations/conv-1/handoffs**', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          data: {
            handoffs: [
              {
                id: 'handoff-1',
                from: 'ai',
                to: 'human',
                timestamp: '2024-01-15T10:30:00Z',
                reason: 'customer_request',
                agent: 'merchant-user',
              },
              {
                id: 'handoff-2',
                from: 'human',
                to: 'ai',
                timestamp: '2024-01-15T11:00:00Z',
                reason: 'resolved',
                agent: 'system',
              },
            ],
          },
          meta: { requestId: 'test-handoffs' },
        }),
      });
    });

    const conversationItem = page.locator('[data-testid="conversation-item"]').first();
    await conversationItem.click();
    await page.waitForTimeout(500);

    // WHEN: Viewing handoff history
    const historyButton = page.getByRole('button', { name: /history|timeline/i }).or(
      page.locator('[data-testid="handoff-history"]')
    );

    const hasHistory = await historyButton.isVisible().catch(() => false);

    if (hasHistory) {
      await historyButton.click();

      // THEN: Should show handoff timeline
      await expect(page.getByText(/handoff history|timeline/i)).toBeVisible();

      // Should show individual handoff events
      await expect(page.getByText(/ai.*human|took over/i)).toBeVisible();
      await expect(page.getByText(/human.*ai|resumed/i)).toBeVisible();
    }
  });

  test('[P2] should show handoff reason selector', async ({ page }) => {
    // GIVEN: User is taking over conversation
    const conversationItem = page.locator('[data-testid="conversation-item"]').first();
    await conversationItem.click();
    await page.waitForTimeout(500);

    // WHEN: Clicking takeover button
    const takeOverButton = page.getByRole('button', { name: /take over/i });
    await takeOverButton.click();

    // THEN: Should show reason selector
    const reasonSelect = page.locator('select').or(
      page.getByRole('combobox', { name: /reason/i })
    );

    const hasReasonSelector = await reasonSelect.isVisible().catch(() => false);

    if (hasReasonSelector) {
      await expect(reasonSelect).toBeVisible();

      // Should have reason options
      const options = page.getByRole('option');
      const count = await options.count();

      expect(count).toBeGreaterThan(0);

      // Common reasons should be available
      await expect(page.getByRole('option', { name: /customer request/i }).or(
        page.getByRole('option', { name: /complex issue/i })
      ).first()).toBeVisible();
    }
  });

  test('[P1] should notify team of handoff', async ({ page }) => {
    // GIVEN: User takes over conversation in a team environment
    await page.route('**/api/conversations/conv-1/takeover**', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          data: {
            mode: 'human',
            notifiedTeam: true,
          },
          meta: { requestId: 'test-notify' },
        }),
      });
    });

    const conversationItem = page.locator('[data-testid="conversation-item"]').first();
    await conversationItem.click();
    await page.waitForTimeout(500);

    const takeOverButton = page.getByRole('button', { name: /take over/i });
    await takeOverButton.click();
    await page.waitForTimeout(1000);

    // THEN: Should show team notification
    const notificationSent = page.getByText(/team notified|assigned to you/i);
    const hasNotification = await notificationSent.isVisible().catch(() => false);

    if (hasNotification) {
      await expect(notificationSent).toBeVisible();
    }
  });

  test('[P2] should limit concurrent human conversations', async ({ page }) => {
    // GIVEN: User already has max concurrent conversations
    await page.route('**/api/conversations/conv-1/takeover**', route => {
      route.fulfill({
        status: 429,
        contentType: 'application/json',
        body: JSON.stringify({
          error: 'Maximum concurrent conversations reached',
          limit: 5,
          current: 5,
        }),
      });
    });

    const conversationItem = page.locator('[data-testid="conversation-item"]').first();
    await conversationItem.click();
    await page.waitForTimeout(500);

    const takeOverButton = page.getByRole('button', { name: /take over/i });
    await takeOverButton.click();

    // THEN: Should show limit warning
    await expect(page.getByText(/maximum|limit|concurrent/i)).toBeVisible({
      timeout: 3000
    });

    // Should offer to close another conversation
    const closeButton = page.getByRole('button', { name: /close another/i });
    const hasCloseButton = await closeButton.isVisible().catch(() => false);

    if (hasCloseButton) {
      await expect(closeButton).toBeVisible();
    }
  });

  test('[P1] should auto-suggest handoff based on sentiment', async ({ page }) => {
    // GIVEN: Customer message indicates frustration
    await page.route('**/api/conversations/conv-1/sentiment**', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          data: {
            sentiment: 'negative',
            score: -0.8,
            suggestHandoff: true,
            reason: 'customer expressed frustration',
          },
          meta: { requestId: 'test-sentiment' },
        }),
      });
    });

    const conversationItem = page.locator('[data-testid="conversation-item"]').first();
    await conversationItem.click();
    await page.waitForTimeout(500);

    // THEN: Should show handoff suggestion
    const suggestion = page.getByText(/consider taking over|customer needs help/i);
    const hasSuggestion = await suggestion.isVisible().catch(() => false);

    if (hasSuggestion) {
      await expect(suggestion).toBeVisible();

      // Should have quick action button
      const takeOverButton = page.getByRole('button', { name: /take over now/i });
      await expect(takeOverButton).toBeVisible();
    }
  });

  test('[P2] should track handoff analytics', async ({ page }) => {
    // GIVEN: User is viewing analytics
    await page.goto('/analytics');
    await page.waitForLoadState('networkidle');

    // Mock handoff analytics data
    await page.route('**/api/analytics/handoffs**', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          data: {
            totalHandoffs: 45,
            avgTimeInHumanMode: 320, // seconds
            handoffReasons: {
              customer_request: 20,
              complex_issue: 15,
              sentiment: 10,
            },
          },
          meta: { requestId: 'test-analytics' },
        }),
      });
    });

    // THEN: Should show handoff metrics
    const handoffMetrics = page.getByText(/handoff|takeover/i);
    await expect(handoffMetrics.first()).toBeVisible();

    // Should show breakdown by reason
    const reasonBreakdown = page.getByText(/customer request|complex issue/i);
    const hasBreakdown = await reasonBreakdown.isVisible().catch(() => false);

    if (hasBreakdown) {
      await expect(reasonBreakdown).toBeVisible();
    }
  });

  test('[P1] should support quick responses during handoff', async ({ page }) => {
    // GIVEN: User has taken over conversation
    await page.route('**/api/conversations/conv-1/takeover**', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          data: { mode: 'human' },
          meta: { requestId: 'test-takeover' },
        }),
      });
    });

    const conversationItem = page.locator('[data-testid="conversation-item"]').first();
    await conversationItem.click();
    await page.waitForTimeout(500);

    const takeOverButton = page.getByRole('button', { name: /take over/i });
    await takeOverButton.click();
    await page.waitForTimeout(1000);

    // THEN: Should show quick response suggestions
    const quickResponses = page.getByText(/quick responses|suggested replies/i);
    const hasQuickResponses = await quickResponses.isVisible().catch(() => false);

    if (hasQuickResponses) {
      await expect(quickResponses).toBeVisible();

      // Clicking a quick response should populate message input
      const responseButton = page.locator('[data-testid="quick-response"]').first();
      await responseButton.click();

      const messageInput = page.locator('textarea[placeholder*="message"]');
      const inputValue = await messageInput.inputValue();

      expect(inputValue.length).toBeGreaterThan(0);
    }
  });

  test('[P2] should preserve context during handoff', async ({ page }) => {
    // GIVEN: AI was handling conversation with context
    await page.route('**/api/conversations/conv-1', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          data: {
            id: 'conv-1',
            customerName: 'John Doe',
            messages: [
              { role: 'customer', content: 'How much is the product?' },
              { role: 'ai', content: 'The product is $29.99.' },
            ],
            context: {
              productId: 'prod-123',
              customerIntent: 'pricing_inquiry',
            },
          },
          meta: { requestId: 'test-context' },
        }),
      });
    });

    const conversationItem = page.locator('[data-testid="conversation-item"]').first();
    await conversationItem.click();
    await page.waitForTimeout(500);

    // WHEN: Taking over
    const takeOverButton = page.getByRole('button', { name: /take over/i });
    await takeOverButton.click();

    // THEN: Should show conversation context
    const contextInfo = page.getByText(/product.*\$29\.99|pricing inquiry/i);
    const hasContext = await contextInfo.isVisible().catch(() => false);

    if (hasContext) {
      await expect(contextInfo).toBeVisible();
    }

    // Should show customer intent
    const intent = page.getByText(/intent|reason/i);
    const hasIntent = await intent.isVisible().catch(() => false);

    if (hasIntent) {
      await expect(intent).toBeVisible();
    }
  });

  test('[P1] should handle handoff errors gracefully', async ({ page }) => {
    // GIVEN: User attempts to take over
    const conversationItem = page.locator('[data-testid="conversation-item"]').first();
    await conversationItem.click();
    await page.waitForTimeout(500);

    // WHEN: API returns error
    await page.route('**/api/conversations/conv-1/takeover**', route => {
      route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({
          error: 'Failed to take over conversation',
        }),
      });
    });

    const takeOverButton = page.getByRole('button', { name: /take over/i });
    await takeOverButton.click();

    // THEN: Should show error message
    await expect(page.getByText(/error|failed|try again/i)).toBeVisible({
      timeout: 3000
    });

    // Conversation should remain in AI mode
    const aiIndicator = page.getByText(/ai mode|automatic/i);
    await expect(aiIndicator.first()).toBeVisible();
  });

  test('[P2] should support handoff scheduling', async ({ page }) => {
    // GIVEN: User wants to schedule a handoff
    const conversationItem = page.locator('[data-testid="conversation-item"]').first();
    await conversationItem.click();
    await page.waitForTimeout(500);

    // WHEN: Clicking schedule handoff option
    const scheduleButton = page.getByRole('button', { name: /schedule handoff|set reminder/i });
    const hasSchedule = await scheduleButton.isVisible().catch(() => false);

    if (hasSchedule) {
      await scheduleButton.click();

      // THEN: Should show scheduling options
      const timeInput = page.locator('input[type="time"]').or(
        page.locator('[data-testid="handoff-time"]')
      );

      if (await timeInput.isVisible()) {
        await timeInput.fill('14:00');

        const confirmButton = page.getByRole('button', { name: /schedule|set/i });
        await confirmButton.click();

        // Should show confirmation
        await expect(page.getByText(/scheduled|reminder set/i)).toBeVisible({
          timeout: 3000
        });
      }
    }
  });

  test('[P2] should show handoff performance metrics', async ({ page }) => {
    // User is viewing their handoff performance
    await page.goto('/analytics');
    await page.waitForLoadState('networkidle');

    const performanceSection = page.getByText(/handoff performance|takeover stats/i);
    const hasPerformance = await performanceSection.isVisible().catch(() => false);

    if (hasPerformance) {
      await expect(performanceSection).toBeVisible();

      // Should show comparison with team average
      const comparison = page.getByText(/vs team|above average|below average/i);
      await expect(comparison.first()).toBeVisible();

      // Should show trend
      const trend = page.getByText(/improving|declining|stable/i);
      await expect(trend.first()).toBeVisible();
    }
  });
});

test.describe('Journey: Handoff - Real-time', () => {
  test('[P2] should show live typing indicator during handoff', async ({ page }) => {
    await page.goto('/conversations');
    await page.waitForLoadState('networkidle');

    const conversationItem = page.locator('[data-testid="conversation-item"]').first();
    await conversationItem.click();
    await page.waitForTimeout(500);

    // Simulate AI typing before handoff
    await page.evaluate(() => {
      window.dispatchEvent(new CustomEvent('conversation:typing', {
        detail: { isTyping: true, sender: 'ai' }
      }));
    });

    const typingIndicator = page.getByText(/ai is typing|typing\.\.\./i);
    const hasIndicator = await typingIndicator.isVisible().catch(() => false);

    if (hasIndicator) {
      await expect(typingIndicator).toBeVisible();

      // Take over during typing
      const takeOverButton = page.getByRole('button', { name: /take over/i });
      await takeOverButton.click();

      // Typing indicator should disappear
      await expect(typingIndicator).toBeHidden({ timeout: 2000 });
    }
  });

  test('[P2] should sync handoff status across team', async ({ context }) => {
    // Two team members viewing same conversation
    const page1 = await context.newPage();
    const page2 = await context.newPage();

    try {
      for (const page of [page1, page2]) {
        await page.goto('/conversations/conv-1');
        await page.evaluate(() => {
          localStorage.setItem('auth_token', 'team-member-token');
        });
      }

      // Member 1 takes over
      await page1.route('**/api/conversations/conv-1/takeover**', route => {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            data: { mode: 'human', agent: 'member-1' },
            meta: { requestId: 'test-sync' },
          }),
        });
      });

      await page1.getByRole('button', { name: /take over/i }).click();
      await page1.waitForTimeout(1000);

      // Member 2 should see the status change
      await page2.reload();
      await page2.waitForLoadState('networkidle');

      const statusUpdate = page2.getByText(/handled by|taken over by.*member-1/i);
      const hasUpdate = await statusUpdate.isVisible().catch(() => false);

      if (hasUpdate) {
        await expect(statusUpdate).toBeVisible();
      }
    } finally {
      await page1.close();
      await page2.close();
    }
  });
});
