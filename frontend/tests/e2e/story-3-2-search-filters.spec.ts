/**
 * Conversations Search and Filter E2E Tests
 *
 * Story 3-2: Search and Filter Conversations
 * Tests the complete user journey for searching and filtering conversations
 *
 * @tags e2e conversations story-3-2 search-filters
 */

import { test, expect } from '@playwright/test';

/**
 * Data factory for creating test conversations with faker-like patterns
 * Uses timestamp-based uniqueness for parallel-safe test execution
 */
const createTestConversation = (overrides: {
  id?: number;
  platformSenderId?: string;
  platformSenderIdMasked?: string;
  lastMessage?: string;
  status?: 'active' | 'handoff' | 'closed';
  sentiment?: 'positive' | 'neutral' | 'negative';
  messageCount?: number;
  updatedAt?: string;
  createdAt?: string;
  hasHandoff?: boolean;
} = {}) => {
  const platformSenderId = overrides.platformSenderId ?? `customer_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  return {
    id: overrides.id ?? 1,
    platformSenderId,
    platformSenderIdMasked: overrides.platformSenderIdMasked ?? `${platformSenderId.substring(0, 4)}****`,
    lastMessage: overrides.lastMessage ?? 'Test message',
    status: overrides.status ?? 'active',
    sentiment: overrides.sentiment ?? 'neutral',
    messageCount: overrides.messageCount ?? 1,
    updatedAt: overrides.updatedAt ?? new Date().toISOString(),
    createdAt: overrides.createdAt ?? new Date().toISOString(),
    hasHandoff: overrides.hasHandoff ?? false,
  };
};

/**
 * Helper to wait for debounce timeout (300ms)
 */
const waitForDebounce = () => new Promise((resolve) => setTimeout(resolve, 350));

test.describe('Conversations Search and Filter E2E Journey', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to conversations page
    await page.goto('http://localhost:5173/conversations');
  });

  /**
   * [P0] Search by customer ID
   * Given the user is on the conversations page
   * When the user types a customer ID in the search input
   * Then the API should be called with the search parameter
   * And matching conversations should be displayed
   */
  test('[P0] @smoke should search by customer ID', async ({ page }) => {
    const testCustomerId = `customer_search_${Date.now()}`;
    const mockConversations = [
      createTestConversation({
        id: 1,
        platformSenderId: testCustomerId,
        lastMessage: 'Where is my order?',
        status: 'active',
      }),
      createTestConversation({
        id: 2,
        platformSenderId: 'other_customer',
        lastMessage: 'Different message',
        status: 'closed',
      }),
    ];

    // Mock API response - network-first pattern
    await page.route('**/api/conversations**', async (route) => {
      const url = new URL(route.request().url());
      const searchParam = url.searchParams.get('search');

      if (searchParam === testCustomerId) {
        // Return filtered results when searching
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            data: [mockConversations[0]],
            meta: {
              pagination: {
                total: 1,
                page: 1,
                perPage: 20,
                totalPages: 1,
              },
            },
          }),
        });
      } else {
        // Return all results without search
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            data: mockConversations,
            meta: {
              pagination: {
                total: 2,
                page: 1,
                perPage: 20,
                totalPages: 1,
              },
            },
          }),
        });
      }
    });

    await page.goto('http://localhost:5173/conversations');

    // Wait for initial load
    await expect(page.getByText('Different message')).toBeVisible();

    // Type customer ID in search input - use getByLabel for resilient selector
    const searchInput = page.getByLabel('Search conversations');
    await searchInput.fill(testCustomerId);

    // Wait for debounce to complete
    await waitForDebounce();

    // Assert filtered results - only matching conversation should be visible
    await expect(page.getByText('Where is my order?')).toBeVisible();
    await expect(page.getByText('Different message')).not.toBeVisible();

    // Assert search input has value
    await expect(searchInput).toHaveValue(testCustomerId);

    // Assert clear button is visible
    const clearButton = page.getByLabel('Clear search');
    await expect(clearButton).toBeVisible();
  });

  /**
   * [P0] Search by message content
   * Given the user is on the conversations page
   * When the user types a message content in the search input
   * Then the API should be called with the search parameter
   * And conversations containing that message should be displayed
   */
  test('[P0] @smoke should search by message content', async ({ page }) => {
    const searchContent = `refund request ${Date.now()}`;
    const mockConversations = [
      createTestConversation({
        id: 1,
        platformSenderId: 'customer_1',
        lastMessage: `I want a ${searchContent} please`,
        status: 'active',
      }),
      createTestConversation({
        id: 2,
        platformSenderId: 'customer_2',
        lastMessage: 'Hello, how are you?',
        status: 'active',
      }),
    ];

    await page.route('**/api/conversations**', async (route) => {
      const url = new URL(route.request().url());
      const searchParam = url.searchParams.get('search');

      if (searchParam?.includes('refund')) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            data: [mockConversations[0]],
            meta: {
              pagination: {
                total: 1,
                page: 1,
                perPage: 20,
                totalPages: 1,
              },
            },
          }),
        });
      } else {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            data: mockConversations,
            meta: {
              pagination: {
                total: 2,
                page: 1,
                perPage: 20,
                totalPages: 1,
              },
            },
          }),
        });
      }
    });

    await page.goto('http://localhost:5173/conversations');

    // Type search query
    const searchInput = page.getByLabel('Search conversations');
    await searchInput.fill(searchContent);

    // Wait for debounce
    await waitForDebounce();

    // Assert filtered results
    await expect(page.getByText(`I want a ${searchContent} please`)).toBeVisible();
    await expect(page.getByText('Hello, how are you?')).not.toBeVisible();
  });

  /**
   * [P0] Case-insensitive search
   * Given the user is on the conversations page
   * When the user types a search query in different cases
   * Then the search should be case-insensitive
   * And matching results should be displayed regardless of case
   */
  test('[P0] should perform case-insensitive search', async ({ page }) => {
    const mockConversations = [
      createTestConversation({
        id: 1,
        platformSenderId: 'ORDER_123',
        lastMessage: 'Where is my ORDER?',
        status: 'active',
      }),
    ];

    await page.route('**/api/conversations**', async (route) => {
      const url = new URL(route.request().url());
      const searchParam = url.searchParams.get('search');

      // Mock backend returns results for any case variation
      if (searchParam?.toLowerCase().includes('order')) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            data: mockConversations,
            meta: {
              pagination: {
                total: 1,
                page: 1,
                perPage: 20,
                totalPages: 1,
              },
            },
          }),
        });
      } else {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            data: mockConversations,
            meta: {
              pagination: {
                total: 1,
                page: 1,
                perPage: 20,
                totalPages: 1,
              },
            },
          }),
        });
      }
    });

    await page.goto('http://localhost:5173/conversations');

    const searchInput = page.getByLabel('Search conversations');

    // Test lowercase search
    await searchInput.fill('order');
    await waitForDebounce();
    await expect(page.getByText('Where is my ORDER?')).toBeVisible();

    // Test uppercase search
    await searchInput.fill('ORDER');
    await waitForDebounce();
    await expect(page.getByText('Where is my ORDER?')).toBeVisible();

    // Test mixed case search
    await searchInput.fill('OrDeR');
    await waitForDebounce();
    await expect(page.getByText('Where is my ORDER?')).toBeVisible();
  });

  /**
   * [P0] Date range filtering
   * Given the user is on the conversations page
   * When the user sets a date range filter
   * Then the API should be called with date_from and date_to parameters
   * And conversations within that date range should be displayed
   */
  test('[P0] @smoke should filter by date range', async ({ page }) => {
    const today = new Date();
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);
    const twoDaysAgo = new Date(today);
    twoDaysAgo.setDate(twoDaysAgo.getDate() - 2);

    const formatDate = (date: Date) => date.toISOString().split('T')[0];

    const mockConversations = [
      createTestConversation({
        id: 1,
        platformSenderId: 'customer_1',
        lastMessage: 'Message from today',
        createdAt: today.toISOString(),
        updatedAt: today.toISOString(),
      }),
      createTestConversation({
        id: 2,
        platformSenderId: 'customer_2',
        lastMessage: 'Message from yesterday',
        createdAt: yesterday.toISOString(),
        updatedAt: yesterday.toISOString(),
      }),
      createTestConversation({
        id: 3,
        platformSenderId: 'customer_3',
        lastMessage: 'Message from 2 days ago',
        createdAt: twoDaysAgo.toISOString(),
        updatedAt: twoDaysAgo.toISOString(),
      }),
    ];

    await page.route('**/api/conversations**', async (route) => {
      const url = new URL(route.request().url());
      const dateFrom = url.searchParams.get('date_from');
      const dateTo = url.searchParams.get('date_to');

      // If date range is set, return filtered results
      if (dateFrom && dateTo) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            data: [mockConversations[0], mockConversations[1]], // Today and yesterday
            meta: {
              pagination: {
                total: 2,
                page: 1,
                perPage: 20,
                totalPages: 1,
              },
            },
          }),
        });
      } else {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            data: mockConversations,
            meta: {
              pagination: {
                total: 3,
                page: 1,
                perPage: 20,
                totalPages: 1,
              },
            },
          }),
        });
      }
    });

    await page.goto('http://localhost:5173/conversations');

    // Click filter panel toggle to open (not "Saved Filters")
    const filterToggle = page.getByRole('button', { name: 'Filters', exact: true });
    await filterToggle.click();

    // Set date range
    const dateFromInput = page.getByLabel('From');
    const dateToInput = page.getByLabel('To');

    await dateFromInput.fill(formatDate(twoDaysAgo));
    await dateToInput.fill(formatDate(today));

    // Wait for debounce and API call
    await waitForDebounce();

    // Assert filtered results - should see today and yesterday messages
    await expect(page.getByText('Message from today')).toBeVisible();
    await expect(page.getByText('Message from yesterday')).toBeVisible();

    // Assert active filters chip is visible
    await expect(page.getByText(/Date:/)).toBeVisible();
  });

  /**
   * [P1] Status multi-select filter
   * Given the user is on the conversations page
   * When the user selects multiple status filters
   * Then the API should be called with multiple status parameters
   * And conversations with any of those statuses should be displayed
   */
  test('[P1] should filter by multiple statuses', async ({ page }) => {
    const mockConversations = [
      createTestConversation({
        id: 1,
        platformSenderId: 'customer_1',
        lastMessage: 'Active conversation',
        status: 'active',
      }),
      createTestConversation({
        id: 2,
        platformSenderId: 'customer_2',
        lastMessage: 'Handoff conversation',
        status: 'handoff',
      }),
      createTestConversation({
        id: 3,
        platformSenderId: 'customer_3',
        lastMessage: 'Closed conversation',
        status: 'closed',
      }),
    ];

    await page.route('**/api/conversations**', async (route) => {
      const url = new URL(route.request().url());
      const statusParams = url.searchParams.getAll('status');

      if (statusParams.length > 0) {
        const filteredData = mockConversations.filter((conv) =>
          statusParams.includes(conv.status)
        );
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            data: filteredData,
            meta: {
              pagination: {
                total: filteredData.length,
                page: 1,
                perPage: 20,
                totalPages: 1,
              },
            },
          }),
        });
      } else {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            data: mockConversations,
            meta: {
              pagination: {
                total: 3,
                page: 1,
                perPage: 20,
                totalPages: 1,
              },
            },
          }),
        });
      }
    });

    await page.goto('http://localhost:5173/conversations');

    // Open filter panel
    const filterToggle = page.getByRole('button', { name: 'Filters', exact: true });
    await filterToggle.click();

    // Select Active and Handoff statuses
    await page.getByRole('button', { name: 'Active' }).first().click();
    await page.getByRole('button', { name: 'Handoff' }).first().click();

    // Wait for API call
    await waitForDebounce();

    // Assert filtered results
    await expect(page.getByText('Active conversation')).toBeVisible();
    await expect(page.getByText('Handoff conversation')).toBeVisible();
    await expect(page.getByText('Closed conversation')).not.toBeVisible();

    // Assert active filters chips
    await expect(page.getByRole('button', { name: 'Active' }).nth(1)).toBeVisible();
    await expect(page.getByRole('button', { name: 'Handoff' }).nth(1)).toBeVisible();
  });

  /**
   * [P1] Sentiment multi-select filter
   * Given the user is on the conversations page
   * When the user selects multiple sentiment filters
   * Then the API should be called with multiple sentiment parameters
   * And conversations with any of those sentiments should be displayed
   */
  test('[P1] should filter by multiple sentiments', async ({ page }) => {
    const mockConversations = [
      createTestConversation({
        id: 1,
        platformSenderId: 'customer_1',
        lastMessage: 'Great service!',
        sentiment: 'positive',
      }),
      createTestConversation({
        id: 2,
        platformSenderId: 'customer_2',
        lastMessage: 'Okay thanks',
        sentiment: 'neutral',
      }),
      createTestConversation({
        id: 3,
        platformSenderId: 'customer_3',
        lastMessage: 'Very disappointed',
        sentiment: 'negative',
      }),
    ];

    await page.route('**/api/conversations**', async (route) => {
      const url = new URL(route.request().url());
      const sentimentParams = url.searchParams.getAll('sentiment');

      if (sentimentParams.length > 0) {
        const filteredData = mockConversations.filter((conv) =>
          sentimentParams.includes(conv.sentiment!)
        );
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            data: filteredData,
            meta: {
              pagination: {
                total: filteredData.length,
                page: 1,
                perPage: 20,
                totalPages: 1,
              },
            },
          }),
        });
      } else {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            data: mockConversations,
            meta: {
              pagination: {
                total: 3,
                page: 1,
                perPage: 20,
                totalPages: 1,
              },
            },
          }),
        });
      }
    });

    await page.goto('http://localhost:5173/conversations');

    // Open filter panel
    const filterToggle = page.getByRole('button', { name: 'Filters', exact: true });
    await filterToggle.click();

    // Select Positive and Negative sentiments
    await page.getByRole('button', { name: /😊.*Positive/ }).click();
    await page.getByRole('button', { name: /😞.*Negative/ }).click();

    // Wait for API call
    await waitForDebounce();

    // Assert filtered results
    await expect(page.getByText('Great service!')).toBeVisible();
    await expect(page.getByText('Very disappointed')).toBeVisible();
    await expect(page.getByText('Okay thanks')).not.toBeVisible();

    // Assert active filters chips (in active filters area, use button role to avoid strict mode)
    await expect(page.getByRole('button', { name: /😊.*Positive/ }).nth(1)).toBeVisible();
    await expect(page.getByRole('button', { name: /😞.*Negative/ }).nth(1)).toBeVisible();
  });

  /**
   * [P1] Combined filters (search + date + status)
   * Given the user is on the conversations page
   * When the user applies multiple filters simultaneously
   * Then the API should be called with all filter parameters
   * And only conversations matching all filters should be displayed
   */
  test('[P1] should apply combined filters', async ({ page }) => {
    const testCustomerId = `customer_${Date.now()}`;
    const today = new Date();
    const formatDate = (date: Date) => date.toISOString().split('T')[0];

    const mockConversations = [
      createTestConversation({
        id: 1,
        platformSenderId: testCustomerId,
        lastMessage: 'Active issue',
        status: 'active',
        createdAt: today.toISOString(),
        updatedAt: today.toISOString(),
      }),
      createTestConversation({
        id: 2,
        platformSenderId: testCustomerId,
        lastMessage: 'Closed issue',
        status: 'closed',
        createdAt: today.toISOString(),
        updatedAt: today.toISOString(),
      }),
      createTestConversation({
        id: 3,
        platformSenderId: 'other_customer',
        lastMessage: 'Different customer',
        status: 'active',
        createdAt: today.toISOString(),
        updatedAt: today.toISOString(),
      }),
    ];

    await page.route('**/api/conversations**', async (route) => {
      const url = new URL(route.request().url());
      const searchParam = url.searchParams.get('search');
      const statusParams = url.searchParams.getAll('status');
      const hasDateFrom = url.searchParams.has('date_from');
      const hasDateTo = url.searchParams.has('date_to');

      // Check if all filters are applied
      if (searchParam === testCustomerId && statusParams.includes('active') && hasDateFrom && hasDateTo) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            data: [mockConversations[0]], // Only active + matching customer + date
            meta: {
              pagination: {
                total: 1,
                page: 1,
                perPage: 20,
                totalPages: 1,
              },
            },
          }),
        });
      } else {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            data: mockConversations,
            meta: {
              pagination: {
                total: 3,
                page: 1,
                perPage: 20,
                totalPages: 1,
              },
            },
          }),
        });
      }
    });

    await page.goto('http://localhost:5173/conversations');

    // Apply search filter
    const searchInput = page.getByLabel('Search conversations');
    await searchInput.fill(testCustomerId);
    await waitForDebounce();

    // Open filter panel
    const filterToggle = page.getByRole('button', { name: 'Filters', exact: true });
    await filterToggle.click();

    // Apply date range
    await page.getByLabel('From').fill(formatDate(today));
    await page.getByLabel('To').fill(formatDate(today));

    // Apply status filter
    await page.getByRole('button', { name: 'Active' }).first().click();

    // Wait for all API calls
    await waitForDebounce();

    // Assert only matching conversation is visible
    await expect(page.getByText('Active issue')).toBeVisible();
    await expect(page.getByText('Closed issue')).not.toBeVisible();
    await expect(page.getByText('Different customer')).not.toBeVisible();

    // Assert all active filters chips are visible
    await expect(page.getByText(/Search:/)).toBeVisible();
    await expect(page.getByText(/Date:/)).toBeVisible();
    await expect(page.getByRole('button', { name: 'Active' }).nth(1)).toBeVisible();
  });

  /**
   * [P1] Save and apply saved filter
   * Given the user has applied filters
   * When the user saves the filter combination
   * And then applies the saved filter
   * Then the same filters should be restored
   * And matching conversations should be displayed
   */
  test('[P1] should save and apply saved filter', async ({ page }) => {
    const filterName = `Test Filter ${Date.now()}`;
    const mockConversations = [
      createTestConversation({
        id: 1,
        platformSenderId: 'customer_1',
        lastMessage: 'Active conversation',
        status: 'active',
      }),
      createTestConversation({
        id: 2,
        platformSenderId: 'customer_2',
        lastMessage: 'Closed conversation',
        status: 'closed',
      }),
    ];

    await page.route('**/api/conversations**', async (route) => {
      const url = new URL(route.request().url());
      const statusParams = url.searchParams.getAll('status');

      if (statusParams.includes('active')) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            data: [mockConversations[0]],
            meta: {
              pagination: {
                total: 1,
                page: 1,
                perPage: 20,
                totalPages: 1,
              },
            },
          }),
        });
      } else {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            data: mockConversations,
            meta: {
              pagination: {
                total: 2,
                page: 1,
                perPage: 20,
                totalPages: 1,
              },
            },
          }),
        });
      }
    });

    await page.goto('http://localhost:5173/conversations');

    // Open filter panel and apply status filter
    const filterToggle = page.getByRole('button', { name: 'Filters', exact: true });
    await filterToggle.click();
    await page.getByRole('button', { name: 'Active' }).first().click();
    await waitForDebounce();

    // Assert filter is applied
    await expect(page.getByText('Active conversation')).toBeVisible();
    await expect(page.getByText('Closed conversation')).not.toBeVisible();

    // Open saved filters dropdown
    const savedFiltersButton = page.getByRole('button', { name: /Saved Filters/ });
    await savedFiltersButton.click();

    // Wait for "Save Current Filters" button to be enabled (has active filters)
    await expect(page.getByRole('button', { name: 'Save Current Filters' })).toBeEnabled();

    // Save current filters
    await page.getByRole('button', { name: 'Save Current Filters' }).click();
    await page.getByPlaceholder('Filter name...').fill(filterName);
    // Wait for Save button to be enabled
    await expect(page.getByRole('button', { name: 'Save' }).first()).toBeEnabled();
    // Press Enter to save (more reliable than click)
    await page.getByPlaceholder('Filter name...').press('Enter');

    // Close the saved filters dropdown before clearing all filters
    // The dropdown stays open after saving a filter, so we need to explicitly close it
    await savedFiltersButton.click();
    // Wait for the dropdown to close
    await expect(page.getByRole('heading', { name: 'Saved Filters', level: 3 })).not.toBeVisible();

    // Now clear all filters - no force needed since dropdown is closed
    await page.getByRole('button', { name: /Clear all/ }).click();
    await waitForDebounce();

    // Assert both conversations are visible again
    await expect(page.getByText('Active conversation')).toBeVisible();
    await expect(page.getByText('Closed conversation')).toBeVisible();

    // Open saved filters and apply saved filter
    await savedFiltersButton.click();
    // Wait for the saved filter to appear in the list
    await page.waitForSelector(`text="${filterName}"`, { timeout: 5000 });
    // Click the saved filter by clicking on the text itself
    await page.getByText(filterName).click();
    // Wait for dropdown to close and filter to be applied
    await page.waitForTimeout(200);
    await waitForDebounce();

    // Assert saved filter is applied
    await expect(page.getByText('Active conversation')).toBeVisible();
    await expect(page.getByText('Closed conversation')).not.toBeVisible();

    // Wait for saved filters dropdown to close before clicking Clear all
    // On mobile, the dropdown can take longer to close, so wait for it to be hidden
    await expect(page.getByRole('heading', { name: 'Saved Filters', level: 3 })).not.toBeVisible();
  });

  /**
   * [P2] URL query param sync
   * Given the user has applied filters
   * When the URL query parameters contain filter values
   * Then the filters should be synced from URL on page load
   * And matching conversations should be displayed
   */
  test('[P2] should sync filters from URL query params', async ({ page }) => {
    const mockConversations = [
      createTestConversation({
        id: 1,
        platformSenderId: 'customer_1',
        lastMessage: 'Active conversation',
        status: 'active',
      }),
    ];

    await page.route('**/api/conversations**', async (route) => {
      const url = new URL(route.request().url());
      const statusParams = url.searchParams.getAll('status');

      if (statusParams.includes('active')) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            data: [mockConversations[0]],
            meta: {
              pagination: {
                total: 1,
                page: 1,
                perPage: 20,
                totalPages: 1,
              },
            },
          }),
        });
      } else {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            data: mockConversations,
            meta: {
              pagination: {
                total: 1,
                page: 1,
                perPage: 20,
                totalPages: 1,
              },
            },
          }),
        });
      }
    });

    // Navigate with URL query parameters
    await page.goto('http://localhost:5173/conversations?status=active&search=test');

    // Wait for page to sync filters from URL
    await waitForDebounce();

    // Assert filters are applied from URL
    await expect(page.getByText('Active conversation')).toBeVisible();

    // Assert search input has value from URL
    const searchInput = page.getByLabel('Search conversations');
    await expect(searchInput).toHaveValue('test');
  });

  /**
   * [P2] Clear all filters
   * Given the user has applied multiple filters
   * When the user clicks "Clear all filters"
   * Then all filters should be removed
   * And all conversations should be displayed
   */
  test('[P2] should clear all filters', async ({ page }) => {
    const testCustomerId = `customer_${Date.now()}`;
    const mockConversations = [
      createTestConversation({
        id: 1,
        platformSenderId: testCustomerId,
        lastMessage: 'Active conversation',
        status: 'active',
      }),
      createTestConversation({
        id: 2,
        platformSenderId: 'other_customer',
        lastMessage: 'Closed conversation',
        status: 'closed',
      }),
    ];

    let callCount = 0;
    await page.route('**/api/conversations**', async (route) => {
      callCount++;
      const url = new URL(route.request().url());
      const searchParam = url.searchParams.get('search');
      const hasSearch = searchParam !== null;
      const hasStatus = url.searchParams.has('status');

      // Filter by search query if present
      if (hasSearch) {
        const filteredConversations = mockConversations.filter(
          (conv) => conv.platformSenderId.includes(searchParam!)
        );
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            data: filteredConversations,
            meta: {
              pagination: {
                total: filteredConversations.length,
                page: 1,
                perPage: 20,
                totalPages: 1,
              },
            },
          }),
        });
      } else {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            data: mockConversations,
            meta: {
              pagination: {
                total: 2,
                page: 1,
                perPage: 20,
                totalPages: 1,
              },
            },
          }),
        });
      }
    });

    await page.goto('http://localhost:5173/conversations');

    // Apply search filter
    const searchInput = page.getByLabel('Search conversations');
    await searchInput.fill(testCustomerId);
    await waitForDebounce();

    // Assert filtered results
    await expect(page.getByText('Active conversation')).toBeVisible();
    await expect(page.getByText('Closed conversation')).not.toBeVisible();

    // Clear all filters using the Clear all button in active filters
    const clearAllButton = page.getByRole('button', { name: /Clear all/ }).first();
    await clearAllButton.click();

    // Wait for API call after clearing
    await waitForDebounce();

    // Assert all conversations are visible
    await expect(page.getByText('Active conversation')).toBeVisible();
    await expect(page.getByText('Closed conversation')).toBeVisible();

    // Assert search input is cleared
    await expect(searchInput).toHaveValue('');
  });
});

test.describe('Conversations Search and Filter - Edge Cases', () => {
  /**
   * [P2] Empty search results
   * Given the user has searched for a term
   * When no conversations match the search
   * Then an empty state should be displayed
   */
  test('[P2] should show empty state for no search results', async ({ page }) => {
    await page.route('**/api/conversations**', async (route) => {
      const url = new URL(route.request().url());
      const searchParam = url.searchParams.get('search');

      if (searchParam) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            data: [],
            meta: {
              pagination: {
                total: 0,
                page: 1,
                perPage: 20,
                totalPages: 0,
              },
            },
          }),
        });
      } else {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            data: [],
            meta: {
              pagination: {
                total: 0,
                page: 1,
                perPage: 20,
                totalPages: 0,
              },
            },
          }),
        });
      }
    });

    await page.goto('http://localhost:5173/conversations');

    // Search for non-existent conversation
    const searchInput = page.getByLabel('Search conversations');
    await searchInput.fill('nonexistent_search_term_xyz');
    await waitForDebounce();

    // Assert empty state is shown
    await expect(page.getByText('No conversations yet')).toBeVisible();
  });

  /**
   * [P2] Filter panel toggle
   * Given the user is on the conversations page
   * When the user toggles the filter panel
   * Then the filter panel should show/hide accordingly
   */
  test('[P2] should toggle filter panel visibility', async ({ page }) => {
    await page.route('**/api/conversations**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          data: [createTestConversation()],
          meta: {
            pagination: {
              total: 1,
              page: 1,
              perPage: 20,
              totalPages: 1,
            },
          },
        }),
      });
    });

    await page.goto('http://localhost:5173/conversations');

    // Filter panel should be closed by default
    const dateInput = page.getByLabel('From');
    await expect(dateInput).not.toBeVisible();

    // Toggle filter panel open
    const filterToggle = page.getByRole('button', { name: 'Filters', exact: true });
    await filterToggle.click();

    // Filter panel content should be visible
    await expect(dateInput).toBeVisible();

    // Toggle filter panel closed
    await filterToggle.click();

    // Filter panel content should be hidden
    await expect(dateInput).not.toBeVisible();
  });
});
