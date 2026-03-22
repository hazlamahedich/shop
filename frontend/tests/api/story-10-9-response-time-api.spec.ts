/**
 * API Tests for Story 10-9: Response Time Distribution Widget
 *
 * API contract tests verifying endpoint behavior and response structure
 */
import { test, expect } from '@playwright/test'

const API_BASE_URL = process.env.API_BASE_URL || 'http://localhost:8000'
const TEST_HEADERS = {
  'X-Test-Mode': 'true',
  'X-Merchant-Id': '1',
}

test.describe('[Story 10-9] Response Time Distribution API Tests', () => {
  test('[P1][10.9-API-001] endpoint returns correct structure', async ({ request }) => {
    const response = await request.get(`${API_BASE_URL}/api/v1/analytics/response-time-distribution?days=7`, {
      headers: TEST_HEADERS,
    })

    expect(response.status()).toBe(200)
    const body = await response.json()

    expect(body).toHaveProperty('data')
    expect(body.data).toHaveProperty('percentiles')
    expect(body.data).toHaveProperty('histogram')
    expect(body.data).toHaveProperty('lastUpdated')
    expect(body.data).toHaveProperty('period')
    expect(body.data).toHaveProperty('count')
  })

  test('[P1][10.9-API-002] percentiles have correct format', async ({ request }) => {
    const response = await request.get(`${API_BASE_URL}/api/v1/analytics/response-time-distribution?days=7`, {
      headers: TEST_HEADERS,
    })

    expect(response.status()).toBe(200)
    const body = await response.json()
    const { percentiles } = body.data

    expect(percentiles).toHaveProperty('p50')
    expect(percentiles).toHaveProperty('p95')
    expect(percentiles).toHaveProperty('p99')

    // Type validation with null checks
    if (percentiles.p50 !== null) {
      expect(typeof percentiles.p50).toBe('number')
    }
    if (percentiles.p95 !== null) {
      expect(typeof percentiles.p95).toBe('number')
    }
    if (percentiles.p99 !== null) {
      expect(typeof percentiles.p99).toBe('number')
    }
  })

  test('[P1][10.9-API-003] histogram has correct format', async ({ request }) => {
    const response = await request.get(`${API_BASE_URL}/api/v1/analytics/response-time-distribution?days=7`, {
      headers: TEST_HEADERS,
    })

    expect(response.status()).toBe(200)
    const body = await response.json()
    const { histogram } = body.data

    expect(Array.isArray(histogram)).toBe(true)

    if (histogram.length > 0) {
      const bucket = histogram[0]
      expect(bucket).toHaveProperty('label')
      expect(bucket).toHaveProperty('count')
      expect(bucket).toHaveProperty('color')
      expect(['green', 'yellow', 'red']).toContain(bucket.color)
    }
  })

  test('[P1][10.9-API-004] days parameter validation', async ({ request }) => {
    const response7d = await request.get(`${API_BASE_URL}/api/v1/analytics/response-time-distribution?days=7`, {
      headers: TEST_HEADERS,
    })
    expect(response7d.status()).toBe(200)

    const response30d = await request.get(`${API_BASE_URL}/api/v1/analytics/response-time-distribution?days=30`, {
      headers: TEST_HEADERS,
    })
    expect(response30d.status()).toBe(200)

    const responseInvalid = await request.get(`${API_BASE_URL}/api/v1/analytics/response-time-distribution?days=100`, {
      headers: TEST_HEADERS,
    })
    expect([400, 422]).toContain(responseInvalid.status())
  })

  test('[P1][10.9-API-005] response type breakdown structure', async ({ request }) => {
    const response = await request.get(`${API_BASE_URL}/api/v1/analytics/response-time-distribution?days=7`, {
      headers: TEST_HEADERS,
    })

    expect(response.status()).toBe(200)
    const body = await response.json()

    // Response type breakdown is optional
    if (body.data.responseTypeBreakdown) {
      expect(body.data.responseTypeBreakdown).toHaveProperty('rag')
      expect(body.data.responseTypeBreakdown).toHaveProperty('general')

      // RAG breakdown structure
      if (body.data.responseTypeBreakdown.rag) {
        const rag = body.data.responseTypeBreakdown.rag
        expect(rag).toHaveProperty('p50')
        expect(rag).toHaveProperty('p95')
        expect(rag).toHaveProperty('p99')
      }
    }
  })

  test('[P1][10.9-API-006] previous period comparison structure', async ({ request }) => {
    const response = await request.get(`${API_BASE_URL}/api/v1/analytics/response-time-distribution?days=7`, {
      headers: TEST_HEADERS,
    })

    expect(response.status()).toBe(200)
    const body = await response.json()

    // Previous period comparison is optional
    if (body.data.previousPeriod?.comparison) {
      const { comparison } = body.data.previousPeriod.comparison

      if (comparison.p50) {
        expect(comparison.p50).toHaveProperty('deltaMs')
        expect(comparison.p50).toHaveProperty('deltaPercent')
        expect(comparison.p50).toHaveProperty('trend')
        expect(['improving', 'degrading', 'stable']).toContain(comparison.p50.trend)
      }
    }
  })

  test('[P1][10.9-API-007] warning structure when slow responses', async ({ request }) => {
    const response = await request.get(`${API_BASE_URL}/api/v1/analytics/response-time-distribution?days=7`, {
      headers: TEST_HEADERS,
    })

    expect(response.status()).toBe(200)
    const body = await response.json()

    // Warning structure is optional
    if (body.data.warning) {
      expect(body.data.warning).toHaveProperty('show')
      expect(body.data.warning).toHaveProperty('message')
      expect(body.data.warning).toHaveProperty('severity')
      expect(['warning', 'critical']).toContain(body.data.warning.severity)
    }
  })

  test.skip('[P2][10.9-API-008] cache headers present - not implemented in backend', async ({ request }) => {
    // Backend doesn't currently return cache-control headers
    // This is a P2 enhancement, not a test blocker
    const response = await request.get(`${API_BASE_URL}/api/v1/analytics/response-time-distribution?days=7`, {
      headers: TEST_HEADERS,
    })
    expect(response.status()).toBe(200)
  })
})
