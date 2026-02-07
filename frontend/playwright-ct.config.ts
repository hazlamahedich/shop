import { defineConfig, devices } from '@playwright/experimental-ct-react';

/**
 * Playwright Component Testing Configuration
 *
 * Configuration for isolated React component testing
 */
export default defineConfig({
  testDir: './tests/component',
  testMatch: /.*\.spec\.tsx/,

  /* The base directory for component files */
  // This tells CT where to find the components relative to the test files
  // The @/ alias is configured in tsconfig.json and vite.config.ts

  /* Run tests in files in parallel */
  fullyParallel: true,

  /* Fail the build on CI if you accidentally left test.only in the source code */
  forbidOnly: !!process.env.CI,

  /* Retry on CI only */
  retries: process.env.CI ? 2 : 0,

  /* Opt out of parallel tests on CI */
  workers: process.env.CI ? 2 : undefined,

  /* Reporter to use */
  reporter: [
    ['html', { outputFolder: 'playwright-report' }],
    ['list', { printSteps: true }],
    ['json', { outputFile: 'test-results/results.json' }],
    ['junit', { outputFile: 'test-results/results.xml' }],
  ],

  /* Shared settings for all tests */
  use: {
    /* Base URL for CT framework - localhost dev server */
    baseURL: 'http://localhost:5173',

    /* Collect trace when retrying the failed test */
    trace: 'on-first-retry',

    /* Screenshot on failure */
    screenshot: 'only-on-failure',

    /* Video on failure */
    video: 'retain-on-failure',

    /* Action timeout */
    actionTimeout: 10000,
  },

  /* Configure projects for different browsers */
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],

  /* Start local dev server before running tests */
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:5173',
    reuseExistingServer: !process.env.CI,
    timeout: 120000,
  },

  /* Test timeout */
  timeout: 60000,
});
