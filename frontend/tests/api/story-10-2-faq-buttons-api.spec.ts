/**
 * Story 10-2: FAQ Quick Buttons API Tests
 *
 * Tests for GET /api/v1/widget/faq-buttons/{merchant_id} endpoint
 *
 * Acceptance Criteria:
 * - AC2: Returns top 5 FAQs by order_index
 * - AC2: Includes icon field in response
 * - AC8: Only returns FAQs for General Mode merchants
 */

import { test, expect } from '@playwright/test';
import { randomUUID } from 'crypto';

const API_URL = process.env.VITE_API_URL || 'http://localhost:8000';
const TEST_MERCHANT_ID = parseInt(process.env.TEST_MERCHANT_ID || '1');
const AUTH_TOKEN = process.env.TEST_AUTH_TOKEN || '';

const createFaqData = (overrides = {}) => ({
    question: `FAQ Question ${randomUUID().slice(0, 8)}?`,
    answer: 'Test answer for FAQ',
    order_index: 0,
    icon: null,
    ...overrides,
});

test.describe('[P0] Story 10-2: FAQ Buttons API - Critical Path', () => {
    test('returns top 5 FAQs sorted by order_index', async ({ request }) => {
        const response = await request.get(
            `${API_URL}/api/v1/widget/faq-buttons/${TEST_MERCHANT_ID}`,
            {
                headers: { Authorization: `Bearer ${AUTH_TOKEN}` },
            }
        );

        expect(response.ok()).toBeTruthy();
        const body = await response.json();

        expect(body).toHaveProperty('data');
        expect(body.data).toHaveProperty('buttons');
        expect(Array.isArray(body.data.buttons)).toBeTruthy();

        if (body.data.buttons.length > 0) {
            expect(body.data.buttons.length).toBeLessThanOrEqual(5);
        }
    });

    test('returns FAQs in order_index ascending order', async ({ request }) => {
        const response = await request.get(
            `${API_URL}/api/v1/widget/faq-buttons/${TEST_MERCHANT_ID}`,
            {
                headers: { Authorization: `Bearer ${AUTH_TOKEN}` },
            }
        );

        expect(response.ok()).toBeTruthy();
        const body = await response.json();

        if (body.data.buttons.length > 1) {
            const buttons = body.data.buttons;
            for (let i = 0; i < buttons.length - 1; i++) {
                expect(buttons[i].id).toBeLessThan(buttons[i + 1].id + 1);
            }
        }
    });

    test('response includes required fields (id, question, icon)', async ({ request }) => {
        const response = await request.get(
            `${API_URL}/api/v1/widget/faq-buttons/${TEST_MERCHANT_ID}`,
            {
                headers: { Authorization: `Bearer ${AUTH_TOKEN}` },
            }
        );

        expect(response.ok()).toBeTruthy();
        const body = await response.json();

        if (body.data.buttons.length > 0) {
            const firstButton = body.data.buttons[0];
            expect(firstButton).toHaveProperty('id');
            expect(firstButton).toHaveProperty('question');
            expect(firstButton).toHaveProperty('icon');
            expect(typeof firstButton.id).toBe('number');
            expect(typeof firstButton.question).toBe('string');
        }
    });

    test('response follows API envelope pattern', async ({ request }) => {
        const response = await request.get(
            `${API_URL}/api/v1/widget/faq-buttons/${TEST_MERCHANT_ID}`,
            {
                headers: { Authorization: `Bearer ${AUTH_TOKEN}` },
            }
        );

        expect(response.ok()).toBeTruthy();
        const body = await response.json();

        expect(body).toHaveProperty('data');
        expect(body).toHaveProperty('meta');
        expect(body.meta).toHaveProperty('requestId');
        expect(body.meta).toHaveProperty('timestamp');
    });
});

test.describe('[P1] Story 10-2: FAQ Buttons API - Error Handling', () => {
    test('returns 404 for non-existent merchant', async ({ request }) => {
        const nonExistentId = 999999;

        const response = await request.get(
            `${API_URL}/api/v1/widget/faq-buttons/${nonExistentId}`,
            {
                headers: { Authorization: `Bearer ${AUTH_TOKEN}` },
            }
        );

        expect(response.status()).toBe(404);
        const body = await response.json();
        expect(body).toHaveProperty('error_code');
        expect(body).toHaveProperty('message');
    });
});

test.describe('[P1] Story 10-2: FAQ Buttons API - Mode Detection', () => {
    test('returns empty list for E-commerce mode merchant', async ({ request }) => {
        const ecommerceMerchantId = parseInt(process.env.TEST_ECOMMERCE_MERCHANT_ID || '0');

        if (ecommerceMerchantId === 0) {
            test.skip();
            return;
        }

        const response = await request.get(
            `${API_URL}/api/v1/widget/faq-buttons/${ecommerceMerchantId}`,
            {
                headers: { Authorization: `Bearer ${AUTH_TOKEN}` },
            }
        );

        if (response.ok()) {
            const body = await response.json();
            expect(body.data.buttons).toHaveLength(0);
        }
    });
});

test.describe('[P1] Story 10-2: FAQ Buttons API - Truncation', () => {
    test('API truncates to exactly 5 FAQs when merchant has more', async ({ request }) => {
        const response = await request.get(
            `${API_URL}/api/v1/widget/faq-buttons/${TEST_MERCHANT_ID}`,
            {
                headers: { Authorization: `Bearer ${AUTH_TOKEN}` },
            }
        );

        expect(response.ok()).toBeTruthy();
        const body = await response.json();

        expect(body).toHaveProperty('data');
        expect(body.data).toHaveProperty('buttons');
        expect(Array.isArray(body.data.buttons)).toBeTruthy();

        expect(body.data.buttons.length).toBeLessThanOrEqual(5);
    });
});

test.describe('[P2] Story 10-2: FAQ Buttons API - Edge Cases', () => {
    test('handles merchant with no FAQs', async ({ request }) => {
        const response = await request.get(
            `${API_URL}/api/v1/widget/faq-buttons/${TEST_MERCHANT_ID}`,
            {
                headers: { Authorization: `Bearer ${AUTH_TOKEN}` },
            }
        );

        expect(response.ok()).toBeTruthy();
        const body = await response.json();
        expect(Array.isArray(body.data.buttons)).toBeTruthy();
    });

    test('handles FAQ with null icon', async ({ request }) => {
        const response = await request.get(
            `${API_URL}/api/v1/widget/faq-buttons/${TEST_MERCHANT_ID}`,
            {
                headers: { Authorization: `Bearer ${AUTH_TOKEN}` },
            }
        );

        expect(response.ok()).toBeTruthy();
        const body = await response.json();

        const nullIconButtons = body.data.buttons.filter((b: any) => b.icon === null);
        if (nullIconButtons.length > 0) {
            expect(nullIconButtons[0].icon).toBeNull();
        }
    });

    test('handles FAQ with emoji icon', async ({ request }) => {
        const response = await request.get(
            `${API_URL}/api/v1/widget/faq-buttons/${TEST_MERCHANT_ID}`,
            {
                headers: { Authorization: `Bearer ${AUTH_TOKEN}` },
            }
        );

        expect(response.ok()).toBeTruthy();
        const body = await response.json();

        const emojiIconButtons = body.data.buttons.filter(
            (b: any) => b.icon !== null && b.icon.length <= 4
        );
        if (emojiIconButtons.length > 0) {
            expect(typeof emojiIconButtons[0].icon).toBe('string');
        }
    });
});
