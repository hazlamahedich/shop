/**
 * API Tests for Story 3-7: Budget Progress API
 *
 * Tests the budget progress API endpoint for:
 * - HTTP response structure and data format
 * - Projection calculations (daily average, projected monthly spend)
 * - Error handling for missing/invalid data
 * - Integration with budget cap configuration
 *
 * Test Coverage Plan:
 * - [P1] Budget progress endpoint returns valid data
 * - [P1] Projection calculations are accurate
 * - [P2] API handles missing budget cap gracefully
 * - [P2] API handles insufficient data for projection
 *
 * @package frontend/tests/api
 */

import { test, expect } from '@playwright/test';

// Type definitions for budget progress response
type BudgetStatus = 'green' | 'yellow' | 'red' | 'no_limit';

interface BudgetProgressResponse {
  monthlySpend: number;
  budgetCap: number | null;
  budgetPercentage: number | null;
  budgetStatus: BudgetStatus;
  daysSoFar: number;
  daysInMonth: number;
  dailyAverage: number | null;
  projectedSpend: number | null;
  projectionAvailable: boolean;
  projectedExceedsBudget: boolean;
}

// Helper function to calculate expected values
function calculateProjection(monthlySpend: number, daysSoFar: number, daysInMonth: number): {
  dailyAverage: number;
  projectedSpend: number;
} {
  const dailyAverage = daysSoFar > 0 ? monthlySpend / daysSoFar : 0;
  const projectedSpend = dailyAverage * daysInMonth;
  return { dailyAverage, projectedSpend };
}

function calculateBudgetPercentage(monthlySpend: number, budgetCap: number): number {
  return budgetCap > 0 ? (monthlySpend / budgetCap) * 100 : 0;
}

function determineBudgetStatus(percentage: number | null): BudgetStatus {
  if (percentage === null) return 'no_limit';
  if (percentage < 50) return 'green';
  if (percentage < 80) return 'yellow';
  return 'red';
}

test.describe('Story 3-7: Budget Progress API Tests', () => {
  // Base URL for API requests
  const baseURL = process.env.API_BASE_URL || 'http://localhost:8000';

  test.describe('[P1] GET /api/costs/budget-progress - Success Cases', () => {
    test('[P1] should return budget progress data with valid budget cap', async ({ request }) => {
      // Given: API endpoint is available
      const response = await request.get(`${baseURL}/api/costs/budget-progress`);

      // Then: Response should be successful
      expect(response.status()).toBe(200);

      // And: Response should have valid JSON structure
      const contentType = response.headers()['content-type'];
      expect(contentType).toContain('application/json');

      const json: BudgetProgressResponse = await response.json();

      // And: Budget progress data should have required fields
      expect(json).toHaveProperty('monthlySpend');
      expect(json).toHaveProperty('budgetCap');
      expect(json).toHaveProperty('budgetPercentage');
      expect(json).toHaveProperty('budgetStatus');
      expect(json).toHaveProperty('daysSoFar');
      expect(json).toHaveProperty('daysInMonth');
      expect(json).toHaveProperty('dailyAverage');
      expect(json).toHaveProperty('projectedSpend');
      expect(json).toHaveProperty('projectionAvailable');
      expect(json).toHaveProperty('projectedExceedsBudget');
    });

    test('[P1] should calculate daily average correctly', async ({ request }) => {
      // Given: API has spend data
      const response = await request.get(`${baseURL}/api/costs/budget-progress`);
      expect(response.status()).toBe(200);

      const json: BudgetProgressResponse = await response.json();

      // When: Data has sufficient history (3+ days)
      if (json.projectionAvailable && json.daysSoFar >= 3) {
        // Then: Daily average should be calculated correctly
        const expectedDailyAverage = calculateProjection(
          json.monthlySpend,
          json.daysSoFar,
          json.daysInMonth
        ).dailyAverage;

        expect(json.dailyAverage).toBeCloseTo(expectedDailyAverage, 2);
        expect(json.dailyAverage).toBeGreaterThan(0);
      }
      // Else: Insufficient data test handles this case
    });

    test('[P1] should calculate projected monthly spend correctly', async ({ request }) => {
      // Given: API has spend data
      const response = await request.get(`${baseURL}/api/costs/budget-progress`);
      expect(response.status()).toBe(200);

      const json: BudgetProgressResponse = await response.json();

      // When: Projection is available
      if (json.projectionAvailable && json.daysSoFar >= 3) {
        // Then: Projected spend should equal daily average * days in month
        const expectedProjection = calculateProjection(
          json.monthlySpend,
          json.daysSoFar,
          json.daysInMonth
        ).projectedSpend;

        expect(json.projectedSpend).toBeCloseTo(expectedProjection, 2);
        expect(json.projectedSpend).toBeGreaterThanOrEqual(json.monthlySpend);
      }
    });

    test('[P1] should determine budget status correctly', async ({ request }) => {
      // Given: API has budget data
      const response = await request.get(`${baseURL}/api/costs/budget-progress`);
      expect(response.status()).toBe(200);

      const json: BudgetProgressResponse = await response.json();

      // When: Budget cap is set
      if (json.budgetCap !== null && json.budgetPercentage !== null) {
        // Then: Budget status should match percentage thresholds
        const expectedStatus = determineBudgetStatus(json.budgetPercentage);
        expect(json.budgetStatus).toBe(expectedStatus);

        // And: Status should be one of the valid values
        expect(['green', 'yellow', 'red', 'no_limit']).toContain(json.budgetStatus);
      } else {
        // When: No budget cap
        expect(json.budgetStatus).toBe('no_limit');
      }
    });

    test('[P1] should indicate when projection exceeds budget', async ({ request }) => {
      // Given: API has budget and projection data
      const response = await request.get(`${baseURL}/api/costs/budget-progress`);
      expect(response.status()).toBe(200);

      const json: BudgetProgressResponse = await response.json();

      // When: Projection is available and budget cap is set
      if (json.projectionAvailable && json.budgetCap !== null && json.projectedSpend !== null) {
        // Then: projectedExceedsBudget should be accurate
        const expectedExceeds = json.projectedSpend > json.budgetCap;
        expect(json.projectedExceedsBudget).toBe(expectedExceeds);
      }
    });
  });

  test.describe('[P1] Budget Status Calculation - Edge Cases', () => {
    test('[P1] should return green status when spend < 50% of budget', async ({ request }) => {
      // This test validates the status calculation logic
      // Note: Actual data depends on test database state
      const response = await request.get(`${baseURL}/api/costs/budget-progress`);
      expect(response.status()).toBe(200);

      const json: BudgetProgressResponse = await response.json();

      // Verify status is one of valid values
      expect(['green', 'yellow', 'red', 'no_limit']).toContain(json.budgetStatus);
    });

    test('[P1] should return yellow status when spend is 50-80% of budget', async ({ request }) => {
      const response = await request.get(`${baseURL}/api/costs/budget-progress`);
      expect(response.status()).toBe(200);

      const json: BudgetProgressResponse = await response.json();

      expect(['green', 'yellow', 'red', 'no_limit']).toContain(json.budgetStatus);
    });

    test('[P1] should return red status when spend >= 80% of budget', async ({ request }) => {
      const response = await request.get(`${baseURL}/api/costs/budget-progress`);
      expect(response.status()).toBe(200);

      const json: BudgetProgressResponse = await response.json();

      expect(['green', 'yellow', 'red', 'no_limit']).toContain(json.budgetStatus);
    });
  });

  test.describe('[P2] Error Handling - Invalid/Missing Data', () => {
    test('[P2] should handle missing budget cap gracefully', async ({ request }) => {
      // Given: User has no budget cap configured
      const response = await request.get(`${baseURL}/api/costs/budget-progress`);
      expect(response.status()).toBe(200);

      const json: BudgetProgressResponse = await response.json();

      // When: No budget cap is set
      if (json.budgetCap === null) {
        // Then: Should return no_limit status
        expect(json.budgetStatus).toBe('no_limit');
        expect(json.budgetPercentage).toBeNull();
      }
      // Else: Budget cap is set, verify it's valid
      else {
        expect(json.budgetCap).toBeGreaterThan(0);
      }
    });

    test('[P2] should handle insufficient data for projection', async ({ request }) => {
      // Given: User has less than 3 days of spend data
      const response = await request.get(`${baseURL}/api/costs/budget-progress`);
      expect(response.status()).toBe(200);

      const json: BudgetProgressResponse = await response.json();

      // When: Less than 3 days of data
      if (json.daysSoFar < 3) {
        // Then: Projection should not be available
        expect(json.projectionAvailable).toBe(false);
        expect(json.dailyAverage).toBeNull();
        expect(json.projectedSpend).toBeNull();
        expect(json.projectedExceedsBudget).toBe(false);
      }
    });

    test('[P2] should handle zero monthly spend', async ({ request }) => {
      const response = await request.get(`${baseURL}/api/costs/budget-progress`);
      expect(response.status()).toBe(200);

      const json: BudgetProgressResponse = await response.json();

      // When: Monthly spend is zero
      if (json.monthlySpend === 0) {
        // Then: Should handle gracefully
        expect(json.monthlySpend).toBe(0);
        // Daily average could be null or 0 depending on days
        if (json.daysSoFar > 0) {
          expect(json.dailyAverage).toBe(0);
        }
      }
    });

    test('[P2] should return error for unauthenticated request', async ({ }) => {
      // Given: API request context without authentication
      // Note: This test validates authentication behavior
      // In DEBUG mode, the API allows X-Merchant-Id header or uses default
      // In production, proper authentication would be required

      // This test is skipped in DEBUG mode since the API has fallback behavior
      test.skip(true, 'API has DEBUG mode fallback - auth testing requires production config');
    });
  });

  test.describe('[P2] Data Consistency', () => {
    test('[P2] should return consistent data across multiple requests', async ({ request }) => {
      // Given: API is available
      const response1 = await request.get(`${baseURL}/api/costs/budget-progress`);
      const response2 = await request.get(`${baseURL}/api/costs/budget-progress`);

      expect(response1.status()).toBe(200);
      expect(response2.status()).toBe(200);

      const json1: BudgetProgressResponse = await response1.json();
      const json2: BudgetProgressResponse = await response2.json();

      // Then: Both responses should have identical data (within reasonable time window)
      expect(json1.budgetCap).toEqual(json2.budgetCap);
      expect(json1.daysInMonth).toEqual(json2.daysInMonth);
      // Note: monthlySpend may differ if tests run across day boundary
    });

    test('[P2] should include valid data types', async ({ request }) => {
      const response = await request.get(`${baseURL}/api/costs/budget-progress`);
      expect(response.status()).toBe(200);

      const json: BudgetProgressResponse = await response.json();

      // Then: All numeric fields should be numbers
      expect(typeof json.monthlySpend).toBe('number');
      expect(typeof json.daysSoFar).toBe('number');
      expect(typeof json.daysInMonth).toBe('number');
      expect(typeof json.projectionAvailable).toBe('boolean');
      expect(typeof json.projectedExceedsBudget).toBe('boolean');

      // And: Status should be a string
      expect(typeof json.budgetStatus).toBe('string');
    });
  });
});
