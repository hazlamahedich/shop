/**
 * API Tests for Story 1.11: Concurrent FAQ Operations
 *
 * Tests concurrent/parallel FAQ operations to ensure data integrity.
 * Verifies no race conditions or data corruption occur.
 *
 * @tags api integration faq story-1-11 concurrent
 */

import { test, expect } from '@playwright/test';

const API_URL = process.env.API_URL || 'http://localhost:8000';

const TEST_MERCHANT = {
  email: 'e2e-test@example.com',
  password: 'TestPass123',
};

test.describe.configure({ mode: 'serial' });
test.describe('Story 1.11: FAQ Concurrent Operations [P1]', () => {
  let authToken: string;
  let merchantId: number;

  test.beforeAll(async ({ request }) => {
    // Login to get auth token
    const loginResponse = await request.post(`${API_URL}/api/v1/auth/login`, {
      data: TEST_MERCHANT,
    });

    if (loginResponse.ok()) {
      const loginData = await loginResponse.json();
      authToken = loginData.data.session.token;
      merchantId = loginData.data.merchant.id;

      // Clean up any existing FAQs
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
    }
  });

  test('[P1] should handle simultaneous FAQ create operations', async ({ request }) => {
    // Given: No FAQs exist
    const beforeResponse = await request.get(`${API_URL}/api/v1/merchant/faqs`, {
      headers: { Authorization: `Bearer ${authToken}` },
    });
    const beforeData = await beforeResponse.json();
    const initialCount = beforeData.data.length;

    // When: Create multiple FAQs simultaneously
    const createPromises = [
      request.post(`${API_URL}/api/v1/merchant/faqs`, {
        headers: {
          Authorization: `Bearer ${authToken}`,
          'Content-Type': 'application/json',
        },
        data: { question: 'Concurrent FAQ 1?', answer: 'Answer 1', keywords: 'c1' },
      }),
      request.post(`${API_URL}/api/v1/merchant/faqs`, {
        headers: {
          Authorization: `Bearer ${authToken}`,
          'Content-Type': 'application/json',
        },
        data: { question: 'Concurrent FAQ 2?', answer: 'Answer 2', keywords: 'c2' },
      }),
      request.post(`${API_URL}/api/v1/merchant/faqs`, {
        headers: {
          Authorization: `Bearer ${authToken}`,
          'Content-Type': 'application/json',
        },
        data: { question: 'Concurrent FAQ 3?', answer: 'Answer 3', keywords: 'c3' },
      }),
    ];

    const responses = await Promise.all(createPromises);

    // Then: All operations should succeed
    for (const response of responses) {
      expect(response.status()).toBe(201);
    }

    // And: All FAQs should be created
    const afterResponse = await request.get(`${API_URL}/api/v1/merchant/faqs`, {
      headers: { Authorization: `Bearer ${authToken}` },
    });
    const afterData = await afterResponse.json();

    expect(afterData.data.length).toBe(initialCount + 3);

    // And: Each FAQ should have unique order_index
    const orderIndices = afterData.data.map((f: any) => f.order_index);
    const uniqueIndices = new Set(orderIndices);
    expect(uniqueIndices.size).toBe(orderIndices.length);
  });

  test('[P1] should handle simultaneous FAQ update operations', async ({ request }) => {
    // Given: Multiple FAQs exist
    const createdIds: number[] = [];
    for (let i = 0; i < 3; i++) {
      const response = await request.post(`${API_URL}/api/v1/merchant/faqs`, {
        headers: {
          Authorization: `Bearer ${authToken}`,
          'Content-Type': 'application/json',
        },
        data: { question: `Update Test ${i}?`, answer: `Original ${i}`, keywords: `u${i}` },
      });
      if (response.ok()) {
        const data = await response.json();
        createdIds.push(data.data.id);
      }
    }

    // When: Update all FAQs simultaneously
    const updatePromises = createdIds.map((id, index) =>
      request.put(`${API_URL}/api/v1/merchant/faqs/${id}`, {
        headers: {
          Authorization: `Bearer ${authToken}`,
          'Content-Type': 'application/json',
        },
        data: { answer: `Updated answer ${index}` },
      })
    );

    const responses = await Promise.all(updatePromises);

    // Then: All operations should succeed
    for (const response of responses) {
      expect(response.status()).toBe(200);
    }

    // And: All FAQs should be updated correctly
    const getResponse = await request.get(`${API_URL}/api/v1/merchant/faqs`, {
      headers: { Authorization: `Bearer ${authToken}` },
    });
    const getData = await getResponse.json();

    for (const id of createdIds) {
      const faq = getData.data.find((f: any) => f.id === id);
      expect(faq).toBeDefined();
      expect(faq.answer).toMatch(/Updated answer \d/);
    }
  });

  test('[P1] should handle simultaneous FAQ delete operations', async ({ request }) => {
    // Given: Multiple FAQs exist
    const createdIds: number[] = [];
    for (let i = 0; i < 5; i++) {
      const response = await request.post(`${API_URL}/api/v1/merchant/faqs`, {
        headers: {
          Authorization: `Bearer ${authToken}`,
          'Content-Type': 'application/json',
        },
        data: { question: `Delete Test ${i}?`, answer: `To delete ${i}`, keywords: `d${i}` },
      });
      if (response.ok()) {
        const data = await response.json();
        createdIds.push(data.data.id);
      }
    }

    const beforeCount = (await request.get(`${API_URL}/api/v1/merchant/faqs`, {
      headers: { Authorization: `Bearer ${authToken}` },
    })).ok() ? (await (await request.get(`${API_URL}/api/v1/merchant/faqs`, {
      headers: { Authorization: `Bearer ${authToken}` },
    })).json()).data.length : 0;

    // When: Delete multiple FAQs simultaneously
    const deletePromises = createdIds.slice(0, 3).map((id) =>
      request.delete(`${API_URL}/api/v1/merchant/faqs/${id}`, {
        headers: { Authorization: `Bearer ${authToken}` },
      })
    );

    const responses = await Promise.all(deletePromises);

    // Then: All operations should succeed
    for (const response of responses) {
      expect([200, 204]).toContain(response.status());
    }

    // And: FAQs should be deleted
    const afterResponse = await request.get(`${API_URL}/api/v1/merchant/faqs`, {
      headers: { Authorization: `Bearer ${authToken}` },
    });
    const afterData = await afterResponse.json();

    expect(afterData.data.length).toBeLessThan(beforeCount);

    // And: Remaining FAQs should have valid order_index sequence
    const orderIndices = afterData.data.map((f: any) => f.order_index).sort((a: number, b: number) => a - b);
    for (let i = 0; i < orderIndices.length; i++) {
      expect(orderIndices[i]).toBe(i);
    }
  });

  test('[P1] should handle mixed concurrent operations (create, update, delete)', async ({ request }) => {
    // Given: Some FAQs exist
    const existingIds: number[] = [];
    for (let i = 0; i < 3; i++) {
      const response = await request.post(`${API_URL}/api/v1/merchant/faqs`, {
        headers: {
          Authorization: `Bearer ${authToken}`,
          'Content-Type': 'application/json',
        },
        data: { question: `Mixed Test ${i}?`, answer: `Original ${i}`, keywords: `m${i}` },
      });
      if (response.ok()) {
        const data = await response.json();
        existingIds.push(data.data.id);
      }
    }

    // When: Perform mixed operations simultaneously
    const operations = [
      // Create new FAQ
      request.post(`${API_URL}/api/v1/merchant/faqs`, {
        headers: {
          Authorization: `Bearer ${authToken}`,
          'Content-Type': 'application/json',
        },
        data: { question: 'New FAQ?', answer: 'New answer', keywords: 'new' },
      }),
      // Update first FAQ
      request.put(`${API_URL}/api/v1/merchant/faqs/${existingIds[0]}`, {
        headers: {
          Authorization: `Bearer ${authToken}`,
          'Content-Type': 'application/json',
        },
        data: { answer: 'Updated in mixed operation' },
      }),
      // Delete second FAQ
      request.delete(`${API_URL}/api/v1/merchant/faqs/${existingIds[1]}`, {
        headers: { Authorization: `Bearer ${authToken}` },
      }),
    ];

    const responses = await Promise.all(operations);

    // Then: All operations should succeed
    expect(responses[0].status()).toBe(201); // Create
    expect(responses[1].status()).toBe(200); // Update
    expect([200, 204]).toContain(responses[2].status()); // Delete

    // And: Data integrity should be maintained
    const finalResponse = await request.get(`${API_URL}/api/v1/merchant/faqs`, {
      headers: { Authorization: `Bearer ${authToken}` },
    });
    const finalData = await finalResponse.json();

    // Verify created FAQ exists
    const newFaq = finalData.data.find((f: any) => f.question === 'New FAQ?');
    expect(newFaq).toBeDefined();

    // Verify updated FAQ
    const updatedFaq = finalData.data.find((f: any) => f.id === existingIds[0]);
    expect(updatedFaq.answer).toBe('Updated in mixed operation');

    // Verify deleted FAQ is gone
    const deletedFaq = finalData.data.find((f: any) => f.id === existingIds[1]);
    expect(deletedFaq).toBeUndefined();

    // Verify order_index sequence is valid
    const orderIndices = finalData.data.map((f: any) => f.order_index).sort((a: number, b: number) => a - b);
    for (let i = 0; i < orderIndices.length; i++) {
      expect(orderIndices[i]).toBe(i);
    }
  });

  test('[P1] should prevent data corruption during concurrent reorders', async ({ request }) => {
    // Given: Multiple FAQs exist
    const createdIds: number[] = [];
    for (let i = 0; i < 4; i++) {
      const response = await request.post(`${API_URL}/api/v1/merchant/faqs`, {
        headers: {
          Authorization: `Bearer ${authToken}`,
          'Content-Type': 'application/json',
        },
        data: { question: `Reorder Test ${i}?`, answer: `Answer ${i}`, keywords: `r${i}` },
      });
      if (response.ok()) {
        const data = await response.json();
        createdIds.push(data.data.id);
      }
    }

    // When: Perform multiple simultaneous reorders
    const reorderPromises = [
      request.put(`${API_URL}/api/v1/merchant/faqs/reorder`, {
        headers: {
          Authorization: `Bearer ${authToken}`,
          'Content-Type': 'application/json',
        },
        data: { faq_ids: [createdIds[3], createdIds[2], createdIds[1], createdIds[0]] },
      }),
      request.put(`${API_URL}/api/v1/merchant/faqs/reorder`, {
        headers: {
          Authorization: `Bearer ${authToken}`,
          'Content-Type': 'application/json',
        },
        data: { faq_ids: [createdIds[0], createdIds[1], createdIds[2], createdIds[3]] },
      }),
    ];

    const responses = await Promise.all(reorderPromises);

    // Then: At least one should succeed
    const successCount = responses.filter(r => r.status() === 200).length;
    expect(successCount).toBeGreaterThan(0);

    // And: Final state should be consistent
    const finalResponse = await request.get(`${API_URL}/api/v1/merchant/faqs`, {
      headers: { Authorization: `Bearer ${authToken}` },
    });
    const finalData = await finalResponse.json();

    // All FAQs should still exist
    expect(finalData.data).toHaveLength(4);

    // Each FAQ should have a unique order_index
    const orderIndices = finalData.data.map((f: any) => f.order_index);
    const uniqueIndices = new Set(orderIndices);
    expect(uniqueIndices.size).toBe(4);
  });

  test('[P1] should maintain FAQ count after concurrent operations', async ({ request }) => {
    // Given: Initial FAQ count
    const beforeResponse = await request.get(`${API_URL}/api/v1/merchant/faqs`, {
      headers: { Authorization: `Bearer ${authToken}` },
    });
    const beforeData = await beforeResponse.json();
    const initialCount = beforeData.data.length;

    // When: Create 3 and delete 2 simultaneously
    const createPromises = [
      request.post(`${API_URL}/api/v1/merchant/faqs`, {
        headers: {
          Authorization: `Bearer ${authToken}`,
          'Content-Type': 'application/json',
        },
        data: { question: 'Count Test 1?', answer: 'A1', keywords: 'ct1' },
      }),
      request.post(`${API_URL}/api/v1/merchant/faqs`, {
        headers: {
          Authorization: `Bearer ${authToken}`,
          'Content-Type': 'application/json',
        },
        data: { question: 'Count Test 2?', answer: 'A2', keywords: 'ct2' },
      }),
      request.post(`${API_URL}/api/v1/merchant/faqs`, {
        headers: {
          Authorization: `Bearer ${authToken}`,
          'Content-Type': 'application/json',
        },
        data: { question: 'Count Test 3?', answer: 'A3', keywords: 'ct3' },
      }),
    ];

    // Get some existing FAQs to delete
    const toDelete = beforeData.data.slice(0, 2);
    const deletePromises = toDelete.map((faq: any) =>
      request.delete(`${API_URL}/api/v1/merchant/faqs/${faq.id}`, {
        headers: { Authorization: `Bearer ${authToken}` },
      })
    );

    const allResponses = await Promise.all([...createPromises, ...deletePromises]);

    // Then: Count should be initial + 3 - 2
    const afterResponse = await request.get(`${API_URL}/api/v1/merchant/faqs`, {
      headers: { Authorization: `Bearer ${authToken}` },
    });
    const afterData = await afterResponse.json();

    expect(afterData.data.length).toBe(initialCount + 1);
  });

  test('[P2] should handle concurrent reads during writes', async ({ request }) => {
    // Given: Some FAQs exist
    for (let i = 0; i < 3; i++) {
      await request.post(`${API_URL}/api/v1/merchant/faqs`, {
        headers: {
          Authorization: `Bearer ${authToken}`,
          'Content-Type': 'application/json',
        },
        data: { question: `Read Test ${i}?`, answer: `Answer ${i}`, keywords: `rt${i}` },
      });
    }

    // When: Perform writes while reading
    const operations = [
      request.get(`${API_URL}/api/v1/merchant/faqs`, {
        headers: { Authorization: `Bearer ${authToken}` },
      }),
      request.post(`${API_URL}/api/v1/merchant/faqs`, {
        headers: {
          Authorization: `Bearer ${authToken}`,
          'Content-Type': 'application/json',
        },
        data: { question: 'New during read?', answer: 'New answer', keywords: 'nr' },
      }),
      request.get(`${API_URL}/api/v1/merchant/faqs`, {
        headers: { Authorization: `Bearer ${authToken}` },
      }),
    ];

    const responses = await Promise.all(operations);

    // Then: All reads should succeed
    expect(responses[0].status()).toBe(200);
    expect(responses[2].status()).toBe(200);

    // Create should also succeed
    expect(responses[1].status()).toBe(201);
  });
});
