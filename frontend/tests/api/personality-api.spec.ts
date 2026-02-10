import { test, expect } from '../support/merged-fixtures';

test.describe('Bot Personality Configuration API', () => {
  test('[P0] should retrieve current personality config', async ({ apiRequest, authToken }) => {
    const { status, body } = await apiRequest({
      method: 'GET',
      path: '/api/merchant/personality',
      headers: {
        Authorization: `Bearer ${authToken}`,
        'X-Merchant-Id': '1',
      },
      retryConfig: { maxRetries: 0 },
    });

    expect(status).toBe(200);
    // Response is wrapped in MinimalEnvelope with data property
    expect(body).toHaveProperty('data');
    expect(body.data).toHaveProperty('personality');
    expect(body.data).toHaveProperty('custom_greeting');
  });

  test('[P0] should update personality to Friendly', async ({ apiRequest, authToken }) => {
    // Get CSRF Token first
    const csrfResponse = await apiRequest({
      method: 'GET',
      path: '/api/v1/csrf-token',
    });
    const csrfToken = csrfResponse.body.csrf_token;

    const { status, body } = await apiRequest({
      method: 'PATCH',
      path: '/api/merchant/personality',
      headers: {
        Authorization: `Bearer ${authToken}`,
        'X-Merchant-Id': '1',
        'X-CSRF-Token': csrfToken,
      },
      body: {
        personality: 'friendly',
        custom_greeting: 'Hello from friendly bot!',
      },
      retryConfig: { maxRetries: 0 },
    });
    expect(status).toBe(200);
    // Response is wrapped in MinimalEnvelope with data property
    expect(body.data.personality).toBe('friendly');
  });

  test('[P1] should validation invalid personality type', async ({ apiRequest, authToken }) => {
    // Get CSRF Token first
    const csrfResponse = await apiRequest({
      method: 'GET',
      path: '/api/v1/csrf-token',
    });
    const csrfToken = csrfResponse.body.csrf_token;

    const { status, body } = await apiRequest({
      method: 'PATCH',
      path: '/api/merchant/personality',
      headers: {
        Authorization: `Bearer ${authToken}`,
        'X-Merchant-Id': '1',
        'X-CSRF-Token': csrfToken,
      },
      body: {
        personality: 'invalid_type',
      },
      retryConfig: { maxRetries: 0 },
    });
    // Pydantic validation error is 422
    expect(status).toBe(422);
  });

  test('[P1] should enforce character limit on greeting', async ({ apiRequest, authToken }) => {
    // Get CSRF Token first
    const csrfResponse = await apiRequest({
      method: 'GET',
      path: '/api/v1/csrf-token',
    });
    const csrfToken = csrfResponse.body.csrf_token;

    const longGreeting = 'a'.repeat(501);
    const { status, body } = await apiRequest({
      method: 'PATCH',
      path: '/api/merchant/personality',
      headers: {
        Authorization: `Bearer ${authToken}`,
        'X-Merchant-Id': '1',
        'X-CSRF-Token': csrfToken,
      },
      body: {
        personality: 'friendly',
        custom_greeting: longGreeting,
      },
      retryConfig: { maxRetries: 0 },
    });
    expect(status).toBe(422);
  });
});
