import { test as base } from '@playwright/test';

export const test = base.extend<{ authToken: string }>({
  authToken: async ({ request, baseURL }, use) => {
    // Mock token for now since we don't have running backend environment info
    // In a real scenario, this would POST to /api/auth/login
    // Assuming development environment for now

    // Attempt login if possible, else fallback to mock
    try {
      const response = await request.post(`${baseURL}/api/auth/login`, {
        data: {
          email: process.env.TEST_USER_EMAIL || 'admin@example.com',
          password: process.env.TEST_USER_PASSWORD || 'password',
        },
      });

      if (response.ok()) {
        const body = await response.json();
        await use(body.access_token || 'mock-token-from-response');
        return;
      }
    } catch (e) {
      // Ignore network errors and fallback
    }

    console.log('Using mock auth token');
    await use('mock-jwt-token');
  },
});
