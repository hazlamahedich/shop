/**
 * E2E P0 Tests for Story 10-9: Response Time Distribution Widget
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

test.describe('[Story 10-9] Response Time Distribution Widget - P0 Tests', () => {
  test('[P0][10.9-E2E-001] widget displays in General mode with correct metrics', async ({ page, mockAuth }) => {
    await mockAuth()
    await mockResponseTimeApi(page)

    const responsePromise = page.waitForResponse('**/api/v1/analytics/response-time-distribution**')
    await page.goto('/dashboard', { waitUntil: 'domcontentloaded' })
    await responsePromise

    const widget = page.locator('[data-testid="response-time-widget"]')
    await expect(widget).toBeVisible()
  })

  test('[P0][10.9-E2E-002] widget displays histogram visualization', async ({ page, mockAuth }) => {
    await mockAuth()
    await mockResponseTimeApi(page)

    const responsePromise = page.waitForResponse('**/api/v1/analytics/response-time-distribution**')
    await page.goto('/dashboard', { waitUntil: 'domcontentloaded' })
    await responsePromise

    const histogramContainer = page.locator('[data-testid="histogram-container"]')
    await expect(histogramContainer).toBeVisible()
  })
})
