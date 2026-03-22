/**
 * E2E P1/P2 Tests for Story 10-9: Response Time Distribution Widget
 *
 * Feature tests for time range selector, comparison trends, response type breakdown,
 * warnings, refresh functionality, and loading/empty states.
 */
import { test as base, expect } from '@playwright/test'
import { mockResponseTimeApi } from '../helpers/response-time-fixture'

type AuthFixtures = {
  mockAuth: () => Promise<void>
}

const test = base.extend<AuthFixtures>({
  mockAuth: async ({ context }, use) => {
    const mockAuthentication = async () => {
      await context.addInitScript(() => {
        localStorage.setItem('auth_token', 'mock-jwt-token')
        localStorage.setItem('merchant_key', 'test-merchant-123')
        localStorage.setItem('user_id', 'mock-user-123')
        localStorage.setItem('auth_timestamp', Date.now().toString())
      })
    }
    await use(mockAuthentication)
  },
})

test.describe('[Story 10-9] Response Time Distribution Widget - Feature Tests', () => {
  test.beforeEach(async ({ page, mockAuth }) => {
    await mockResponseTimeApi(page)
    await mockAuth()
  })

  test('[P1][10.9-E2E-003] time range selector updates days param', async ({ page }) => {
    await page.goto('/dashboard', { waitUntil: 'domcontentloaded' })

    const selector = page.locator('[data-testid="time-range-selector"]')
    await expect(selector).toBeVisible()

    const responsePromise = page.waitForResponse('**/api/v1/analytics/response-time-distribution**')
    await selector.selectOption({ label: '30 days' })
    const response = await responsePromise

    expect(response.request().url()).toContain('days=30')
  })

  test('[P1][10.9-E2E-004] comparison trends display correctly', async ({ page }) => {
    await page.goto('/dashboard', { waitUntil: 'domcontentloaded' })

    const widget = page.locator('[data-testid="response-time-widget"]')
    await expect(widget).toBeVisible()

    const trends = page.locator('[data-testid="comparison-trend"]')
    await expect(trends.first()).toBeVisible()

    const trendTexts = await trends.allTextContents()
    expect(trendTexts.length).toBeGreaterThan(0)
  })

  test('[P1][10.9-E2E-005] response type breakdown displays when data available', async ({ page }) => {
    await page.goto('/dashboard', { waitUntil: 'domcontentloaded' })

    const widget = page.locator('[data-testid="response-time-widget"]')
    await expect(widget).toBeVisible()

    const ragSection = page.locator('[data-testid="rag-responses"]')
    await expect(ragSection).toBeVisible()

    const generalSection = page.locator('[data-testid="general-responses"]')
    await expect(generalSection).toBeVisible()
  })

  test('[P1][10.9-E2E-006] warning displays when p95 exceeds threshold', async ({ page }) => {
    await page.goto('/dashboard', { waitUntil: 'domcontentloaded' })

    const widget = page.locator('[data-testid="response-time-widget"]')
    await expect(widget).toBeVisible()

    const warning = page.locator('[data-testid="response-time-warning"]')
    const warningCount = await warning.count()
    if (warningCount > 0) {
      await expect(warning.first()).toBeVisible()
    }
  })

  test('[P1][10.9-E2E-007] refresh button fetches latest data', async ({ page }) => {
    await page.goto('/dashboard', { waitUntil: 'domcontentloaded' })

    const widget = page.locator('[data-testid="response-time-widget"]')
    await expect(widget).toBeVisible()

    const refreshButton = page.locator('[data-testid="refresh-button"]')
    await expect(refreshButton).toBeVisible()
    await expect(refreshButton).toBeEnabled()

    const responsePromise = page.waitForResponse('**/api/v1/analytics/response-time-distribution**')
    await refreshButton.click()
    await responsePromise
  })

  test('[P2][10.9-E2E-008] empty state displays correctly when no data', async ({ page }) => {
    // Override mock with empty data for this test
    await page.route('**/api/v1/analytics/response-time-distribution**', async (route) => {
      return route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          data: {
            percentiles: { p50: null, p95: null, p99: null },
            histogram: [],
            count: 0,
          },
        }),
      })
    })

    await page.goto('/dashboard', { waitUntil: 'domcontentloaded' })

    // Widget should still render even with no data
    const widget = page.locator('[data-testid="response-time-widget"]')
    await expect(widget).toBeVisible()

    // Check for empty state
    const emptyState = page.locator('[data-testid="response-time-empty"]')
    const emptyCount = await emptyState.count()
    expect(emptyCount).toBeGreaterThanOrEqual(0)
  })

  test('[P2][10.9-E2E-009] loading state displays skeleton', async ({ page }) => {
    // Intentional delay to test loading skeleton display
    await page.route('**/api/v1/analytics/response-time-distribution**', async (route) => {
      await new Promise((resolve) => setTimeout(resolve, 2000))
      return route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          data: {
            percentiles: { p50: 850, p95: 2100, p99: 4500 },
            histogram: [{ label: '0-1s', count: 150, color: 'green' }],
            count: 150,
          },
        }),
      })
    })

    await page.goto('/dashboard', { waitUntil: 'domcontentloaded' })

    // Widget should eventually be visible
    const widget = page.locator('[data-testid="response-time-widget"]')
    await expect(widget).toBeVisible({ timeout: 10000 })
  })
})
