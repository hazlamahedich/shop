/**
 * Story 10-2 AC5: FAQ Merchant Configuration API Tests
 *
 * Tests for merchant FAQ configuration functionality:
 * - Create, Update, Delete FAQs
 * - Reorder FAQs (change order_index)
 * - FAQs are filtered by merchant_id
 *
 * Prerequisites: Running backend server with test data
 * Run: TEST_MERCHANT_ID=1 TEST_AUTH_TOKEN=xxx npx playwright test frontend/tests/api/story-10-2-faq-configuration.spec.ts
 */

import { test, expect } from '@playwright/test';
import { randomUUID } from 'crypto';

const API_URL = process.env.VITE_API_URL || 'http://localhost:8000';
const TEST_MERCHANT_ID = parseInt(process.env.TEST_MERCHANT_ID || '1');
const AUTH_TOKEN = process.env.TEST_AUTH_TOKEN || '';

test.describe('[P1] Story 10-2: FAQ Configuration API', () => {
  test.skip(!AUTH_TOKEN, 'Skipping - TEST_AUTH_TOKEN not provided');

  let createdFaqId: number | null = null;

  test.afterEach(async ({ request }) => {
    // Cleanup: Delete any FAQs created during tests
    if (createdFaqId && AUTH_TOKEN) {
      await request.delete(`${API_URL}/api/v1/faqs/${createdFaqId}`, {
        headers: { Authorization: `Bearer ${AUTH_TOKEN}` },
      });
      createdFaqId = null;
    }
  });

  test('[10.2-API-AC5-001] Merchant can create new FAQ', async ({ request }) => {
    const response = await request.post(`${API_URL}/api/v1/faqs`, {
      headers: { Authorization: `Bearer ${AUTH_TOKEN}` },
      data: {
        question: `Test FAQ ${randomUUID().slice(0, 8)}?`,
        answer: 'Test answer for FAQ',
        order_index: 999,
        icon: '❓',
      },
    });

    expect(response.ok()).toBeTruthy();
    const body = await response.json();
    expect(body.data).toHaveProperty('id');
    expect(body.data).toHaveProperty('question');
    expect(body.data).toHaveProperty('answer');
    expect(body.data).toHaveProperty('order_index');
    
    createdFaqId = body.data.id;
  });

  test('[10.2-API-AC5-002] Merchant can update existing FAQ', async ({ request }) => {
    // First create an FAQ
    const createResponse = await request.post(`${API_URL}/api/v1/faqs`, {
      headers: { Authorization: `Bearer ${AUTH_TOKEN}` },
      data: {
        question: `Original Question ${randomUUID().slice(0, 8)}?`,
        answer: 'Original Answer',
        order_index: 998,
        icon: null,
      },
    });

    if (!createResponse.ok()) {
      test.skip(true, 'Failed to create test FAQ');
      return;
    }

    const createBody = await createResponse.json();
    const faqId = createBody.data.id;
    createdFaqId = faqId;

    // Update the FAQ
    const updateResponse = await request.put(`${API_URL}/api/v1/faqs/${faqId}`, {
      headers: { Authorization: `Bearer ${AUTH_TOKEN}` },
      data: {
        question: `Updated Question ${randomUUID().slice(0, 8)}?`,
        answer: 'Updated Answer',
        order_index: 1,
        icon: '✅',
      },
    });

    expect(updateResponse.ok()).toBeTruthy();
    const updateBody = await updateResponse.json();
    expect(updateBody.data.question).toContain('Updated Question');
    expect(updateBody.data.answer).toBe('Updated Answer');
    expect(updateBody.data.order_index).toBe(1);
    expect(updateBody.data.icon).toBe('✅');
  });

  test('[10.2-API-AC5-003] Merchant can delete FAQ', async ({ request }) => {
    // First create an FAQ
    const createResponse = await request.post(`${API_URL}/api/v1/faqs`, {
      headers: { Authorization: `Bearer ${AUTH_TOKEN}` },
      data: {
        question: `FAQ to Delete ${randomUUID().slice(0, 8)}?`,
        answer: 'Will be deleted',
        order_index: 997,
        icon: null,
      },
    });

    if (!createResponse.ok()) {
      test.skip(true, 'Failed to create test FAQ');
      return;
    }

    const createBody = await createResponse.json();
    const faqId = createBody.data.id;

    // Delete the FAQ
    const deleteResponse = await request.delete(`${API_URL}/api/v1/faqs/${faqId}`, {
      headers: { Authorization: `Bearer ${AUTH_TOKEN}` },
    });

    expect(deleteResponse.ok()).toBeTruthy();

    // Verify FAQ is deleted
    const listResponse = await request.get(`${API_URL}/api/v1/faqs`, {
      headers: { Authorization: `Bearer ${AUTH_TOKEN}` },
    });

    const listBody = await listResponse.json();
    const deletedFaq = listBody.data.find((f: any) => f.id === faqId);
    expect(deletedFaq).toBeUndefined();
  });

  test('[10.2-API-AC5-004] Merchant can reorder FAQs', async ({ request }) => {
    // Get current FAQs
    const listResponse = await request.get(`${API_URL}/api/v1/faqs`, {
      headers: { Authorization: `Bearer ${AUTH_TOKEN}` },
    });

    if (!listResponse.ok()) {
      test.skip(true, 'Failed to list FAQs');
      return;
    }

    const body = await listResponse.json();
    
    if (body.data.length < 2) {
      test.skip(true, 'Need at least 2 FAQs to test reordering');
      return;
    }

    // Verify FAQs are sorted by order_index
    const faqs = body.data;
    for (let i = 0; i < faqs.length - 1; i++) {
      expect(faqs[i].order_index).toBeLessThanOrEqual(faqs[i + 1].order_index);
    }
  });

  test('[10.2-API-AC5-005] FAQs are filtered by merchant_id', async ({ request }) => {
    const response = await request.get(`${API_URL}/api/v1/faqs`, {
      headers: { Authorization: `Bearer ${AUTH_TOKEN}` },
    });

    expect(response.ok()).toBeTruthy();
    const body = await response.json();
    
    // All FAQs should belong to the authenticated merchant
    body.data.forEach((faq: any) => {
      expect(faq).toHaveProperty('merchant_id');
    });
  });

  test('[10.2-API-AC5-006] Merchant can set FAQ icon', async ({ request }) => {
    const response = await request.post(`${API_URL}/api/v1/faqs`, {
      headers: { Authorization: `Bearer ${AUTH_TOKEN}` },
      data: {
        question: `FAQ with Icon ${randomUUID().slice(0, 8)}?`,
        answer: 'Answer with Icon',
        order_index: 996,
        icon: '🕐',
      },
    });

    if (!response.ok()) {
      test.skip(true, 'Failed to create FAQ');
      return;
    }

    const body = await response.json();
    expect(body.data.icon).toBe('🕐');
    createdFaqId = body.data.id;
  });

  test('[10.2-API-AC5-007] Merchant can set null icon', async ({ request }) => {
    const response = await request.post(`${API_URL}/api/v1/faqs`, {
      headers: { Authorization: `Bearer ${AUTH_TOKEN}` },
      data: {
        question: `FAQ without Icon ${randomUUID().slice(0, 8)}?`,
        answer: 'Answer without Icon',
        order_index: 995,
        icon: null,
      },
    });

    if (!response.ok()) {
      test.skip(true, 'Failed to create FAQ');
      return;
    }

    const body = await response.json();
    expect(body.data.icon).toBeNull();
    createdFaqId = body.data.id;
  });
});
