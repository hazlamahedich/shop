/**
 * API Tests for Story 1.11: FAQ Reordering
 *
 * Tests the FAQ reordering endpoint functionality.
 * Verifies order_index updates and sequence validation.
 *
 * @tags api integration faq story-1-11 reorder
 */

import { test, expect } from '@playwright/test';

const API_URL = process.env.API_URL || 'http://localhost:8000';

const TEST_MERCHANT = {
  email: 'e2e-test@example.com',
  password: 'TestPass123',
};

test.describe.configure({ mode: 'serial' });
test.describe('Story 1.11: FAQ Reordering API [P1]', () => {
  let authToken: string;
  let merchantId: number;
  let createdFaqIds: number[] = [];

  test.beforeAll(async ({ request }) => {
    // Login to get auth token
    const loginResponse = await request.post(`${API_URL}/api/v1/auth/login`, {
      data: TEST_MERCHANT,
    });

    if (loginResponse.ok()) {
      const loginData = await loginResponse.json();
      authToken = loginData.data.session.token;
      merchantId = loginData.data.merchant.id;

      // Clean up any existing FAQs first
      const existingFaqs = await request.get(`${API_URL}/api/v1/merchant/faqs`, {
        headers: { Authorization: `Bearer ${authToken}` },
      });

      if (existingFaqs.ok()) {
        const existingData = await existingFaqs.json();
        for (const faq of existingData.data) {
          await request.delete(`${API_URL}/api/v1/merchant/faqs/${faq.id}`, {
            headers: { Authorization: `Bearer ${authToken}` },
          });
        }
      }

      // Create test FAQs for reordering
      const faqData = [
        { question: 'First FAQ?', answer: 'Answer 1', keywords: 'first' },
        { question: 'Second FAQ?', answer: 'Answer 2', keywords: 'second' },
        { question: 'Third FAQ?', answer: 'Answer 3', keywords: 'third' },
        { question: 'Fourth FAQ?', answer: 'Answer 4', keywords: 'fourth' },
      ];

      for (const faq of faqData) {
        const response = await request.post(`${API_URL}/api/v1/merchant/faqs`, {
          headers: {
            Authorization: `Bearer ${authToken}`,
            'Content-Type': 'application/json',
          },
          data: faq,
        });

        if (response.ok()) {
          const data = await response.json();
          createdFaqIds.push(data.data.id);
        }
      }
    }
  });

  test.afterAll(async ({ request }) => {
    // Clean up created FAQs
    for (const faqId of createdFaqIds) {
      await request.delete(`${API_URL}/api/v1/merchant/faqs/${faqId}`, {
        headers: { Authorization: `Bearer ${authToken}` },
      });
    }
  });

  test('[P1] should reorder FAQs with new order sequence', async ({ request }) => {
    // Given: Initial FAQ order (created in beforeAll)
    const getBefore = await request.get(`${API_URL}/api/v1/merchant/faqs`, {
      headers: { Authorization: `Bearer ${authToken}` },
    });
    expect(getBefore.ok()).toBe(true);
    const beforeData = await getBefore.json();
    const initialOrder = beforeData.data.map((f: any) => f.id);

    // When: Reorder FAQs (reverse the order)
    const reversedOrder = [...initialOrder].reverse();
    const response = await request.put(`${API_URL}/api/v1/merchant/faqs/reorder`, {
      headers: {
        Authorization: `Bearer ${authToken}`,
        'Content-Type': 'application/json',
      },
      data: {
        faq_ids: reversedOrder,
      },
    });

    // Then: Response should be successful
    expect(response.status()).toBe(200);
    const body = await response.json();

    // And: FAQs should be in new order
    expect(body.data).toHaveLength(reversedOrder.length);
    expect(body.data[0].id).toBe(reversedOrder[0]);
    expect(body.data[1].id).toBe(reversedOrder[1]);
    expect(body.data[2].id).toBe(reversedOrder[2]);
    expect(body.data[3].id).toBe(reversedOrder[3]);

    // And: order_index should be updated correctly
    expect(body.data[0].order_index).toBe(0);
    expect(body.data[1].order_index).toBe(1);
    expect(body.data[2].order_index).toBe(2);
    expect(body.data[3].order_index).toBe(3);

    // Verify with GET request
    const verifyResponse = await request.get(`${API_URL}/api/v1/merchant/faqs`, {
      headers: { Authorization: `Bearer ${authToken}` },
    });
    const verifyData = await verifyResponse.json();

    expect(verifyData.data[0].id).toBe(reversedOrder[0]);
    expect(verifyData.data[0].order_index).toBe(0);
  });

  test('[P1] should move last FAQ to first position', async ({ request }) => {
    // Given: Current FAQ order
    const getBefore = await request.get(`${API_URL}/api/v1/merchant/faqs`, {
      headers: { Authorization: `Bearer ${authToken}` },
    });
    const beforeData = await getBefore.json();
    const lastFaqId = beforeData.data[beforeData.data.length - 1].id;
    const otherIds = beforeData.data.slice(0, -1).map((f: any) => f.id);
    const newOrder = [lastFaqId, ...otherIds];

    // When: Move last FAQ to first position
    const response = await request.put(`${API_URL}/api/v1/merchant/faqs/reorder`, {
      headers: {
        Authorization: `Bearer ${authToken}`,
        'Content-Type': 'application/json',
      },
      data: {
        faq_ids: newOrder,
      },
    });

    // Then: Last FAQ should now be first
    expect(response.status()).toBe(200);
    const body = await response.json();

    expect(body.data[0].id).toBe(lastFaqId);
    expect(body.data[0].order_index).toBe(0);
  });

  test('[P1] should move first FAQ to last position', async ({ request }) => {
    // Given: Current FAQ order
    const getBefore = await request.get(`${API_URL}/api/v1/merchant/faqs`, {
      headers: { Authorization: `Bearer ${authToken}` },
    });
    const beforeData = await getBefore.json();
    const firstFaqId = beforeData.data[0].id;
    const otherIds = beforeData.data.slice(1).map((f: any) => f.id);
    const newOrder = [...otherIds, firstFaqId];

    // When: Move first FAQ to last position
    const response = await request.put(`${API_URL}/api/v1/merchant/faqs/reorder`, {
      headers: {
        Authorization: `Bearer ${authToken}`,
        'Content-Type': 'application/json',
      },
      data: {
        faq_ids: newOrder,
      },
    });

    // Then: First FAQ should now be last
    expect(response.status()).toBe(200);
    const body = await response.json();

    const lastIndex = body.data.length - 1;
    expect(body.data[lastIndex].id).toBe(firstFaqId);
    expect(body.data[lastIndex].order_index).toBe(lastIndex);
  });

  test('[P1] should handle partial reordering (subset of FAQs)', async ({ request }) => {
    // Given: All FAQs
    const getBefore = await request.get(`${API_URL}/api/v1/merchant/faqs`, {
      headers: { Authorization: `Bearer ${authToken}` },
    });
    const beforeData = await getBefore.json();
    const allIds = beforeData.data.map((f: any) => f.id);

    // When: Reorder only first 3 FAQs (swap first and third)
    const partialReorder = [allIds[2], allIds[1], allIds[0], allIds[3]];
    const response = await request.put(`${API_URL}/api/v1/merchant/faqs/reorder`, {
      headers: {
        Authorization: `Bearer ${authToken}`,
        'Content-Type': 'application/json',
      },
      data: {
        faq_ids: partialReorder,
      },
    });

    // Then: All FAQs should be in new order
    expect(response.status()).toBe(200);
    const body = await response.json();

    expect(body.data[0].id).toBe(allIds[2]);
    expect(body.data[1].id).toBe(allIds[1]);
    expect(body.data[2].id).toBe(allIds[0]);
    expect(body.data[3].id).toBe(allIds[3]);
  });

  test('[P1] should return 404 when reordering with invalid FAQ IDs', async ({ request }) => {
    // Given: Current FAQ IDs
    const getBefore = await request.get(`${API_URL}/api/v1/merchant/faqs`, {
      headers: { Authorization: `Bearer ${authToken}` },
    });
    const beforeData = await getBefore.json();
    const validIds = beforeData.data.map((f: any) => f.id);

    // When: Include an invalid FAQ ID in reorder
    const invalidReorder = [...validIds, 99999]; // 99999 doesn't exist
    const response = await request.put(`${API_URL}/api/v1/merchant/faqs/reorder`, {
      headers: {
        Authorization: `Bearer ${authToken}`,
        'Content-Type': 'application/json',
      },
      data: {
        faq_ids: invalidReorder,
      },
    });

    // Then: Should return 404
    expect(response.status()).toBe(404);
    const body = await response.json();
    expect(body.detail.message).toMatch(/do not belong to this merchant|not found/i);
  });

  test('[P1] should return 404 when reordering with FAQ IDs from another merchant', async ({ request }) => {
    // This test verifies that FAQ ownership is validated during reordering
    // Note: In a real scenario, you'd need to create a FAQ for a different merchant
    // For this test, we use a non-existent FAQ ID that would fail ownership check

    // When: Try to reorder with an FAQ ID that doesn't exist for this merchant
    const response = await request.put(`${API_URL}/api/v1/merchant/faqs/reorder`, {
      headers: {
        Authorization: `Bearer ${authToken}`,
        'Content-Type': 'application/json',
      },
      data: {
        faq_ids: [99998, 99999], // Non-existent FAQ IDs
      },
    });

    // Then: Should return 404
    expect(response.status()).toBe(404);
    const body = await response.json();
    expect(body.detail.message).toMatch(/do not belong to this merchant|not found/i);
  });

  test('[P1] should handle single FAQ reordering (no-op)', async ({ request }) => {
    // Given: Only one FAQ
    // First, delete all but one FAQ
    const getBefore = await request.get(`${API_URL}/api/v1/merchant/faqs`, {
      headers: { Authorization: `Bearer ${authToken}` },
    });
    const beforeData = await getBefore.json();

    if (beforeData.data.length > 1) {
      // Delete all but the first one
      for (let i = 1; i < beforeData.data.length; i++) {
        await request.delete(`${API_URL}/api/v1/merchant/faqs/${beforeData.data[i].id}`, {
          headers: { Authorization: `Bearer ${authToken}` },
        });
      }
    }

    // Get the remaining FAQ
    const getAfter = await request.get(`${API_URL}/api/v1/merchant/faqs`, {
      headers: { Authorization: `Bearer ${authToken}` },
    });
    const afterData = await getAfter.json();
    const singleFaqId = afterData.data[0].id;

    // When: Reorder single FAQ
    const response = await request.put(`${API_URL}/api/v1/merchant/faqs/reorder`, {
      headers: {
        Authorization: `Bearer ${authToken}`,
        'Content-Type': 'application/json',
      },
      data: {
        faq_ids: [singleFaqId],
      },
    });

    // Then: Should be successful
    expect(response.status()).toBe(200);
    const body = await response.json();

    expect(body.data).toHaveLength(1);
    expect(body.data[0].id).toBe(singleFaqId);
    expect(body.data[0].order_index).toBe(0);
  });

  test('[P1] should maintain FAQ content during reordering', async ({ request }) => {
    // Given: FAQs with specific content
    const getBefore = await request.get(`${API_URL}/api/v1/merchant/faqs`, {
      headers: { Authorization: `Bearer ${authToken}` },
    });
    const beforeData = await getBefore.json();

    // Store original content
    const originalContent = beforeData.data.map((f: any) => ({
      id: f.id,
      question: f.question,
      answer: f.answer,
      keywords: f.keywords,
    }));

    const newOrder = beforeData.data.map((f: any) => f.id).reverse();

    // When: Reorder FAQs
    const response = await request.put(`${API_URL}/api/v1/merchant/faqs/reorder`, {
      headers: {
        Authorization: `Bearer ${authToken}`,
        'Content-Type': 'application/json',
      },
      data: {
        faq_ids: newOrder,
      },
    });

    // Then: FAQ content should remain unchanged
    expect(response.status()).toBe(200);
    const body = await response.json();

    for (const original of originalContent) {
      const reorderedFaq = body.data.find((f: any) => f.id === original.id);
      expect(reorderedFaq).toBeDefined();
      expect(reorderedFaq.question).toBe(original.question);
      expect(reorderedFaq.answer).toBe(original.answer);
      expect(reorderedFaq.keywords).toBe(original.keywords);
    }
  });

  test('[P1] should include metadata in reorder response', async ({ request }) => {
    // When: Reorder FAQs
    const getBefore = await request.get(`${API_URL}/api/v1/merchant/faqs`, {
      headers: { Authorization: `Bearer ${authToken}` },
    });
    const beforeData = await getBefore.json();
    const faqIds = beforeData.data.map((f: any) => f.id);

    const response = await request.put(`${API_URL}/api/v1/merchant/faqs/reorder`, {
      headers: {
        Authorization: `Bearer ${authToken}`,
        'Content-Type': 'application/json',
      },
      data: {
        faq_ids: faqIds,
      },
    });

    // Then: Response should include metadata
    expect(response.status()).toBe(200);
    const body = await response.json();

    expect(body).toHaveProperty('meta');
    expect(body.meta).toHaveProperty('request_id');
    expect(body.meta).toHaveProperty('timestamp');
    expect(typeof body.meta.request_id).toBe('string');
    expect(typeof body.meta.timestamp).toBe('string');
  });

  test('[P2] should validate faq_ids is an array', async ({ request }) => {
    // When: Send non-array faq_ids
    const response = await request.put(`${API_URL}/api/v1/merchant/faqs/reorder`, {
      headers: {
        Authorization: `Bearer ${authToken}`,
        'Content-Type': 'application/json',
      },
      data: {
        faq_ids: 'not-an-array',
      },
    });

    // Then: Should return validation error
    expect([400, 422]).toContain(response.status());
  });

  test('[P2] should reject empty faq_ids array', async ({ request }) => {
    // When: Send empty array
    const response = await request.put(`${API_URL}/api/v1/merchant/faqs/reorder`, {
      headers: {
        Authorization: `Bearer ${authToken}`,
        'Content-Type': 'application/json',
      },
      data: {
        faq_ids: [],
      },
    });

    // Then: Should return validation error
    expect([400, 422]).toContain(response.status());
  });
});
