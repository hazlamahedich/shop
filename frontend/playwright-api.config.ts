import { defineConfig } from '@playwright/test';

/**
 * Playwright API Test Configuration
 * 
 * Minimal config for API tests only (no browser, no Vitest conflicts)
 */
export default defineConfig({
  testDir: './tests/api',
  testMatch: /.*\.spec\.ts/,
  fullyParallel: false, // Serial execution for API tests
  workers: 1,
  timeout: 60000,
  
  reporter: [
    ['list'],
    ['html', { outputFolder: 'playwright-report-api' }],
  ],
  
  use: {
    baseURL: 'http://localhost:8000',
    extraHTTPHeaders: {
      'X-Test-Mode': 'true',
    },
  },
  
  projects: [
    {
      name: 'api',
      use: {
        // API tests use { request } fixture, no browser needed
      },
    },
  ],
});
