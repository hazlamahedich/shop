import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright Multi-Project Test Configuration
 *
 * Enhanced configuration supporting:
 * - Multi-level testing: E2E, API, Component
 * - Multi-browser testing (Chromium, Firefox, WebKit)
 * - Mobile viewport testing
 * - CI/CD integration with parallel sharding
 * - Enhanced reporting (HTML, JSON, JUnit)
 * - Performance monitoring
 *
 * Test Strategy: Test pyramid - E2E (10%), API (30%), Component (60%)
 */
export default defineConfig({
  /* Default test directory (can be overridden per project) */
  testDir: './tests/e2e',

  /* Run tests in files in parallel */
  fullyParallel: true,

  /* Fail the build on CI if you accidentally left test.only in the source code */
  forbidOnly: !!process.env.CI,

  /* Retry on CI only */
  retries: process.env.CI ? 2 : 0,

  /* Opt out of parallel tests on CI - use 2 workers for CI */
  workers: process.env.CI ? 2 : undefined,

  /* Reporter to use - multiple reporters for different needs */
  reporter: [
    ['html', { outputFolder: 'playwright-report' }],
    ['list', { printSteps: true }],
    ['json', { outputFile: 'test-results/results.json' }],
    ['junit', { outputFile: 'test-results/results.xml' }],
  ],

  /* Shared settings for all tests */
  use: {
    /* Base URL to use in actions like `await page.goto('/')` */
    baseURL: 'http://localhost:5173',

    /* Collect trace when retrying the failed test */
    trace: 'on-first-retry',

    /* Screenshot on failure */
    screenshot: 'only-on-failure',

    /* Video on failure */
    video: 'retain-on-failure',

    /* Action timeout for slower development environments */
    actionTimeout: 10000,

    /* Navigation timeout */
    navigationTimeout: 30000,
  },

  /* Configure projects for different test levels and browsers */
  projects: [
    // ===== E2E TESTS =====
    // Critical user journeys with full browser
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },

    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },

    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },

    /* Mobile viewport tests */
    {
      name: 'Mobile Chrome',
      use: { ...devices['Pixel 5'] },
    },

    {
      name: 'Mobile Safari',
      use: { ...devices['iPhone 12'] },
    },

    /* Smoke tests - run on Chromium only, E2E tests only */
    {
      name: 'smoke-tests',
      testDir: './tests/e2e',
      testMatch: /.*\.spec\.ts/,
      testIgnore: /.*\/api\/.*/, // Ignore API tests in smoke-tests project
      use: { ...devices['Desktop Chrome'] },
    },

    // ===== API TESTS =====
    // Direct API testing - no browser needed, faster execution
    {
      name: 'api',
      testDir: './tests/api',
      testMatch: /.*\.spec\.ts/,
      use: {
        // API tests use { request } fixture, no browser context needed
      },
      // API tests don't need webServer - they make direct HTTP requests
      fullyParallel: true,
    },

    // ===== COMPONENT TESTS =====
    // Isolated component testing with browser
    {
      name: 'component',
      testDir: './tests/component',
      testMatch: /.*\.spec\.ts/,
      use: {
        ...devices['Desktop Chrome'],
        // Component tests run in isolation
      },
    },
  ],

  /* Start local dev server before running E2E tests */
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:5173',
    reuseExistingServer: !process.env.CI,
    timeout: 120000,
  },

  /* Test timeout */
  timeout: 60000,
});
