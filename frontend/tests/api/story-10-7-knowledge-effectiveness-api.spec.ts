/**
 * API Tests for Story 10-7: Knowledge Effectiveness
 *
 * Tests the /api/v1/analytics/knowledge-effectiveness endpoint
 * for RAG query performance metrics.
 *
 * Test ID Format: 10.7-API-XXX
 */

import { test, expect } from '@playwright/test';

const API_BASE = '/api/v1/analytics/knowledge-effectiveness';

interface KnowledgeEffectivenessResponse {
  totalQueries: number;
  successfulMatches: number;
  noMatchRate: number;
  avgConfidence: number | null;
  trend: number[];
  lastUpdated: string;
}

test.describe('[P1] Story 10-7: Knowledge Effectiveness API', () => {
  test.describe.configure({ mode: 'isolated' });

  test('[10.7-API-001] @p1 should return effectiveness metrics for default 7 days', async ({ request }) => {
    const response = await request.get(API_BASE);
    
    expect(response.status()).toBe(200);
    
    const data = await response.json() as { data: KnowledgeEffectivenessResponse };
    
    expect(data.data).toHaveProperty('totalQueries');
    expect(data.data).toHaveProperty('successfulMatches');
    expect(data.data).toHaveProperty('noMatchRate');
    expect(data.data).toHaveProperty('avgConfidence');
    expect(data.data).toHaveProperty('trend');
    expect(data.data).toHaveProperty('lastUpdated');
    
    expect(typeof data.data.totalQueries).toBe('number');
    expect(typeof data.data.successfulMatches).toBe('number');
    expect(typeof data.data.noMatchRate).toBe('number');
    expect(Array.isArray(data.data.trend)).toBe(true);
  });

  test('[10.7-API-002] @p1 should accept days query parameter', async ({ request }) => {
    const response = await request.get(`${API_BASE}?days=30`);
    
    expect(response.status()).toBe(200);
    
    const data = await response.json() as { data: KnowledgeEffectivenessResponse };
    
    expect(data.data.trend.length).toBeLessThanOrEqual(30);
  });

  test('[10.7-API-003] @p2 should return valid trend data structure', async ({ request }) => {
    const response = await request.get(API_BASE);
    
    expect(response.status()).toBe(200);
    
    const data = await response.json() as { data: KnowledgeEffectivenessResponse };
    
    data.data.trend.forEach((value) => {
      expect(typeof value).toBe('number');
      expect(value).toBeGreaterThanOrEqual(0);
      expect(value).toBeLessThanOrEqual(1);
    });
  });

  test('[10.7-API-004] @p2 should calculate no-match rate correctly', async ({ request }) => {
    const response = await request.get(API_BASE);
    
    expect(response.status()).toBe(200);
    
    const data = await response.json() as { data: KnowledgeEffectivenessResponse };
    
    if (data.data.totalQueries > 0) {
      const expectedNoMatchRate = ((data.data.totalQueries - data.data.successfulMatches) / data.data.totalQueries) * 100;
      expect(data.data.noMatchRate).toBeCloseTo(expectedNoMatchRate, 1);
    }
  });

  test('[10.7-API-005] @p2 should return lastUpdated as ISO timestamp', async ({ request }) => {
    const response = await request.get(API_BASE);
    
    expect(response.status()).toBe(200);
    
    const data = await response.json() as { data: KnowledgeEffectivenessResponse };
    
    const lastUpdated = new Date(data.data.lastUpdated);
    expect(lastUpdated).toBeInstanceOf(Date);
    expect(lastUpdated.getTime()).not.toBeNaN();
  });

  test('[10.7-API-006] @p2 should handle maximum allowed days parameter', async ({ request }) => {
    const response = await request.get(`${API_BASE}?days=30`);
    
    expect(response.status()).toBe(200);
    
    const data = await response.json() as { data: KnowledgeEffectivenessResponse };
    
    expect(data.data).toHaveProperty('totalQueries');
    expect(data.data).toHaveProperty('trend');
  });
});

test.describe('[P2] Story 10-7: API Error Handling', () => {
  test('[10.7-API-007] @p2 should reject invalid days parameter', async ({ request }) => {
    const response = await request.get(`${API_BASE}?days=-1`);
    
    expect(response.status()).toBe(422);
  });

  test('[10.7-API-008] @p2 should reject non-numeric days parameter', async ({ request }) => {
    const response = await request.get(`${API_BASE}?days=invalid`);
    
    expect(response.status()).toBe(422);
  });

  test('[10.7-API-009] @p2 should handle unauthenticated requests', async ({ request }) => {
    const response = await request.get(API_BASE, {
      headers: {
        'Authorization': '',
      },
    });
    
    expect([401, 200]).toContain(response.status());
  });
});
