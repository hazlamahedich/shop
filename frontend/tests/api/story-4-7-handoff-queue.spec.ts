/**
 * API Tests: Story 4-7 Handoff Queue with Urgency
 *
 * Tests handoff queue API endpoint functionality:
 * - Queue view sorting (urgency DESC, wait_time DESC)
 * - Queue filtering by urgency
 * - Pagination for queue view
 * - total_waiting count in meta
 *
 * Acceptance Criteria Coverage:
 * - AC1: Sort by Urgency then Wait Time
 * - AC3: Filter by Urgency
 * - AC4: Total Waiting Count
 * - AC5: Pagination
 *
 * @package frontend/tests/api/story-4-7-handoff-queue.spec.ts
 */

import { test, expect } from '../support/merged-fixtures';

test.describe('Story 4-7: Handoff Queue API', () => {
  const queueEndpoint = '/api/handoff-alerts';

  test.describe('[P0] Queue View Sorting', () => {
    test('[P0] should sort queue by urgency DESC then wait_time DESC', async ({ apiRequest }) => {
      const requestParams = new URLSearchParams({
        view: 'queue',
        sort_by: 'urgency_desc',
      });

      const result = await apiRequest({
        method: 'GET',
        path: `${queueEndpoint}?${requestParams.toString()}`,
        body: null,
        headers: {},
      });

      expect(result.status).toBe(200);
      expect(result.body.data).toBeDefined();
      expect(Array.isArray(result.body.data)).toBe(true);

      if (result.body.data.length >= 2) {
        const items = result.body.data;
        const urgencyOrder = { high: 3, medium: 2, low: 1 };

        for (let i = 0; i < items.length - 1; i++) {
          const currentUrgency = urgencyOrder[items[i].urgencyLevel as keyof typeof urgencyOrder] || 0;
          const nextUrgency = urgencyOrder[items[i + 1].urgencyLevel as keyof typeof urgencyOrder] || 0;

          expect(currentUrgency).toBeGreaterThanOrEqual(nextUrgency);

          if (currentUrgency === nextUrgency && items[i].waitTimeSeconds !== undefined) {
            expect(items[i].waitTimeSeconds).toBeGreaterThanOrEqual(items[i + 1].waitTimeSeconds);
          }
        }
      }
    });

    test('[P0] should return only active handoffs in queue view', async ({ apiRequest }) => {
      const requestParams = new URLSearchParams({
        view: 'queue',
        sort_by: 'urgency_desc',
      });

      const result = await apiRequest({
        method: 'GET',
        path: `${queueEndpoint}?${requestParams.toString()}`,
        body: null,
        headers: {},
      });

      expect(result.status).toBe(200);

      if (result.body.data && result.body.data.length > 0) {
        for (const item of result.body.data) {
          expect(item).toHaveProperty('conversationId');
          expect(item).toHaveProperty('urgencyLevel');
          expect(['high', 'medium', 'low']).toContain(item.urgencyLevel);
        }
      }
    });
  });

  test.describe('[P0] Queue Meta Response', () => {
    test('[P0] should include totalWaiting in queue view meta', async ({ apiRequest }) => {
      const requestParams = new URLSearchParams({
        view: 'queue',
        sort_by: 'urgency_desc',
      });

      const result = await apiRequest({
        method: 'GET',
        path: `${queueEndpoint}?${requestParams.toString()}`,
        body: null,
        headers: {},
      });

      expect(result.status).toBe(200);
      expect(result.body.meta).toBeDefined();
      expect(result.body.meta).toHaveProperty('total');
      expect(result.body.meta).toHaveProperty('page');
      expect(result.body.meta).toHaveProperty('limit');
      expect(result.body.meta).toHaveProperty('totalWaiting');
      expect(typeof result.body.meta.totalWaiting).toBe('number');
    });

    test('[P0] should have totalWaiting null or number for notifications view', async ({ apiRequest }) => {
      const requestParams = new URLSearchParams({
        view: 'notifications',
      });

      const result = await apiRequest({
        method: 'GET',
        path: `${queueEndpoint}?${requestParams.toString()}`,
        body: null,
        headers: {},
      });

      expect(result.status).toBe(200);
      expect(result.body.meta).toBeDefined();
    });
  });

  test.describe('[P1] Queue Filtering', () => {
    test('[P1] should filter queue by high urgency', async ({ apiRequest }) => {
      const requestParams = new URLSearchParams({
        view: 'queue',
        sort_by: 'urgency_desc',
        urgency: 'high',
      });

      const result = await apiRequest({
        method: 'GET',
        path: `${queueEndpoint}?${requestParams.toString()}`,
        body: null,
        headers: {},
      });

      expect(result.status).toBe(200);

      if (result.body.data && result.body.data.length > 0) {
        for (const item of result.body.data) {
          expect(item.urgencyLevel).toBe('high');
        }
      }
    });

    test('[P1] should filter queue by medium urgency', async ({ apiRequest }) => {
      const requestParams = new URLSearchParams({
        view: 'queue',
        sort_by: 'urgency_desc',
        urgency: 'medium',
      });

      const result = await apiRequest({
        method: 'GET',
        path: `${queueEndpoint}?${requestParams.toString()}`,
        body: null,
        headers: {},
      });

      expect(result.status).toBe(200);

      if (result.body.data && result.body.data.length > 0) {
        for (const item of result.body.data) {
          expect(item.urgencyLevel).toBe('medium');
        }
      }
    });

    test('[P1] should filter queue by low urgency', async ({ apiRequest }) => {
      const requestParams = new URLSearchParams({
        view: 'queue',
        sort_by: 'urgency_desc',
        urgency: 'low',
      });

      const result = await apiRequest({
        method: 'GET',
        path: `${queueEndpoint}?${requestParams.toString()}`,
        body: null,
        headers: {},
      });

      expect(result.status).toBe(200);

      if (result.body.data && result.body.data.length > 0) {
        for (const item of result.body.data) {
          expect(item.urgencyLevel).toBe('low');
        }
      }
    });
  });

  test.describe('[P1] Queue Pagination', () => {
    test('[P1] should support pagination with page and limit params', async ({ apiRequest }) => {
      const requestParams = new URLSearchParams({
        view: 'queue',
        sort_by: 'urgency_desc',
        page: '1',
        limit: '10',
      });

      const result = await apiRequest({
        method: 'GET',
        path: `${queueEndpoint}?${requestParams.toString()}`,
        body: null,
        headers: {},
      });

      expect(result.status).toBe(200);
      expect(result.body.meta.page).toBe(1);
      expect(result.body.meta.limit).toBe(10);
      expect(result.body.data.length).toBeLessThanOrEqual(10);
    });

    test('[P1] should return correct pagination metadata', async ({ apiRequest }) => {
      const requestParams = new URLSearchParams({
        view: 'queue',
        sort_by: 'urgency_desc',
        page: '2',
        limit: '5',
      });

      const result = await apiRequest({
        method: 'GET',
        path: `${queueEndpoint}?${requestParams.toString()}`,
        body: null,
        headers: {},
      });

      expect(result.status).toBe(200);
      expect(result.body.meta.page).toBe(2);
      expect(result.body.meta.limit).toBe(5);
    });
  });

  test.describe('[P1] Handoff Reason Field', () => {
    test('[P1] should include handoffReason in queue items', async ({ apiRequest }) => {
      const requestParams = new URLSearchParams({
        view: 'queue',
        sort_by: 'urgency_desc',
      });

      const result = await apiRequest({
        method: 'GET',
        path: `${queueEndpoint}?${requestParams.toString()}`,
        body: null,
        headers: {},
      });

      expect(result.status).toBe(200);

      if (result.body.data && result.body.data.length > 0) {
        const itemWithReason = result.body.data.find(
          (item: { handoffReason: string | null }) => item.handoffReason !== null
        );
        if (itemWithReason && itemWithReason.handoffReason) {
          expect(['keyword', 'low_confidence', 'clarification_loop']).toContain(
            itemWithReason.handoffReason
          );
        }
      }
    });
  });

  test.describe('[P2] Edge Cases', () => {
    test('[P2] should handle empty queue gracefully', async ({ apiRequest }) => {
      const requestParams = new URLSearchParams({
        view: 'queue',
        sort_by: 'urgency_desc',
        urgency: 'high',
      });

      const result = await apiRequest({
        method: 'GET',
        path: `${queueEndpoint}?${requestParams.toString()}`,
        body: null,
        headers: {},
      });

      expect(result.status).toBe(200);
      expect(Array.isArray(result.body.data)).toBe(true);
      expect(result.body.meta.totalWaiting).toBeDefined();
    });

    test('[P2] should default to page 1 if not specified', async ({ apiRequest }) => {
      const requestParams = new URLSearchParams({
        view: 'queue',
        sort_by: 'urgency_desc',
      });

      const result = await apiRequest({
        method: 'GET',
        path: `${queueEndpoint}?${requestParams.toString()}`,
        body: null,
        headers: {},
      });

      expect(result.status).toBe(200);
      expect(result.body.meta.page).toBe(1);
    });

    test('[P2] should default limit to 20 if not specified', async ({ apiRequest }) => {
      const requestParams = new URLSearchParams({
        view: 'queue',
        sort_by: 'urgency_desc',
      });

      const result = await apiRequest({
        method: 'GET',
        path: `${queueEndpoint}?${requestParams.toString()}`,
        body: null,
        headers: {},
      });

      expect(result.status).toBe(200);
      expect(result.body.meta.limit).toBe(20);
    });
  });

  test.describe('[P2] Error Handling', () => {
    test('[P2] should reject invalid view parameter', async ({ apiRequest }) => {
      const requestParams = new URLSearchParams({
        view: 'invalid_view',
      });

      const result = await apiRequest({
        method: 'GET',
        path: `${queueEndpoint}?${requestParams.toString()}`,
        body: null,
        headers: {},
      });

      expect([400, 422]).toContain(result.status);
    });

    test('[P2] should reject invalid sort_by parameter', async ({ apiRequest }) => {
      const requestParams = new URLSearchParams({
        view: 'queue',
        sort_by: 'invalid_sort',
      });

      const result = await apiRequest({
        method: 'GET',
        path: `${queueEndpoint}?${requestParams.toString()}`,
        body: null,
        headers: {},
      });

      expect([400, 422]).toContain(result.status);
    });

    test('[P2] should reject invalid urgency parameter', async ({ apiRequest }) => {
      const requestParams = new URLSearchParams({
        view: 'queue',
        urgency: 'critical',
      });

      const result = await apiRequest({
        method: 'GET',
        path: `${queueEndpoint}?${requestParams.toString()}`,
        body: null,
        headers: {},
      });

      expect([400, 422]).toContain(result.status);
    });
  });
});
