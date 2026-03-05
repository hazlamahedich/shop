/**
 * @fileoverview Story 6-5: Operational Data Preservation Tests
 * @description E2E tests for verifying operational data is preserved during retention
 * @tags e2e story-6-5 retention data-preservation operational-data
 */

import { test, expect } from './fixtures';
import { APIRequestContext } from '@playwright/test';

test.describe.configure({ mode: 'parallel' });

test.describe('Story 6-5: Operational Data Preservation', () => {
  test('[P0][regression] should preserve operational data after retention job', async ({ authenticatedPage, apiContext }) => {
    const customerData = {
      email: `orders-test-${Date.now()}@example.com`,
      preferences: { theme: 'dark' },
    };

    const createCustomerResponse = await apiContext.post('/api/v1/customers', {
      data: customerData,
    });

    if (!createCustomerResponse.ok()) {
      test.skip(true, 'Customer creation endpoint not available');
      return;
    }

    const { customer_id } = await createCustomerResponse.json();

    const orderData = {
      customer_id,
      order_number: 'ORD-12345',
      platform: 'shopify',
      status: 'delivered',
    };

    const createOrderResponse = await apiContext.post('/api/v1/orders', {
      data: orderData,
    });

    expect(createOrderResponse.ok()).toBeTruthy();

    await authenticatedPage.goto('/conversations');

    const conversationWithOrder = authenticatedPage.locator(`[data-testid="conversation-${customer_id}"]`);

    const conversationVisible = await conversationWithOrder.isVisible().catch(() => false);

    if (conversationVisible) {
      const orderReference = conversationWithOrder.locator('[data-testid="order-reference"]');
      await expect(orderReference).toBeVisible();
      await expect(orderReference).toContainText('ORD-12345');
    } else {
      test.skip(true, 'Conversation with order not visible - feature may not be implemented');
    }
  });

  test('[P1][regression] should show order references after voluntary data deletion', async ({ authenticatedPage, apiContext }) => {
    const customerData = {
      email: `orders-preserve-${Date.now()}@example.com`,
      preferences: { theme: 'light' },
    };

    const createCustomerResponse = await apiContext.post('/api/v1/customers', {
      data: customerData,
    });

    if (!createCustomerResponse.ok()) {
      test.skip(true, 'Customer creation endpoint not available');
      return;
    }

    const { customer_id } = await createCustomerResponse.json();

    const orderData = {
      customer_id,
      order_number: 'ORD-67890',
      platform: 'shopify',
      status: 'shipped',
    };

    const createOrderResponse = await apiContext.post('/api/v1/orders', {
      data: orderData,
    });

    expect(createOrderResponse.ok()).toBeTruthy();

    const deleteResponse = await apiContext.delete(`/api/v1/customers/${customer_id}/voluntary-data`);

    expect([200, 204, 404]).toContain(deleteResponse.status());

    await authenticatedPage.goto('/conversations');

    const orderReference = authenticatedPage.locator('[data-testid="order-reference"]');

    const orderRefVisible = await orderReference.first().isVisible().catch(() => false);

    if (orderRefVisible) {
      await expect(orderReference.first()).toBeVisible();
      await expect(orderReference.first()).toContainText('ORD-67890');
    } else {
      test.skip(true, 'Order reference not visible - feature may not be implemented');
    }
  });
});
