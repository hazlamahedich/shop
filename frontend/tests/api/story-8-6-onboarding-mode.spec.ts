import { test, expect } from '@playwright/test';

const TEST_MERCHANT_ID = '1';

test.describe.serial('Onboarding Mode API @api', () => {
  
  test('[P0] should get current onboarding mode', async ({ request }) => {
    const response = await request.get('/api/merchant/mode', {
      headers: {
        'X-Test-Mode': 'true',
        'X-Merchant-Id': TEST_MERCHANT_ID,
      },
    });
    
    expect(response.status()).toBe(200);
    
    const body = await response.json();
    expect(body).toHaveProperty('data');
    expect(body.data).toHaveProperty('onboardingMode');
    expect(['general', 'ecommerce']).toContain(body.data.onboardingMode);
  });

  test('[P0] should update mode to general', async ({ request }) => {
    const response = await request.patch('/api/merchant/mode', {
      headers: {
        'X-Test-Mode': 'true',
        'X-Merchant-Id': TEST_MERCHANT_ID,
      },
      data: {
        mode: 'general'
      }
    });
    
    expect(response.status()).toBe(200);
    
    const body = await response.json();
    expect(body).toHaveProperty('data');
    expect(body.data.onboardingMode).toBe('general');
  });

  test('[P0] should update mode to ecommerce', async ({ request }) => {
    const response = await request.patch('/api/merchant/mode', {
      headers: {
        'X-Test-Mode': 'true',
        'X-Merchant-Id': TEST_MERCHANT_ID,
      },
      data: {
        mode: 'ecommerce'
      }
    });
    
    expect(response.status()).toBe(200);
    
    const body = await response.json();
    expect(body).toHaveProperty('data');
    expect(body.data.onboardingMode).toBe('ecommerce');
  });

  test('[P1] should reject invalid mode values', async ({ request }) => {
    const response = await request.patch('/api/merchant/mode', {
      headers: {
        'X-Test-Mode': 'true',
        'X-Merchant-Id': TEST_MERCHANT_ID,
      },
      data: {
        mode: 'invalid_mode'
      }
    });
    
    expect(response.status()).toBe(422);
    
    const body = await response.json();
    expect(body).toHaveProperty('detail');
  });

  test('[P1] should persist mode across requests', async ({ request }) => {
    const headers = {
      'X-Test-Mode': 'true',
      'X-Merchant-Id': TEST_MERCHANT_ID,
    };

    await request.patch('/api/merchant/mode', {
      headers,
      data: {
        mode: 'ecommerce'
      }
    });
    
    const response = await request.get('/api/merchant/mode', { headers });
    
    expect(response.status()).toBe(200);
    
    const body = await response.json();
    expect(body.data.onboardingMode).toBe('ecommerce');
    
    await request.patch('/api/merchant/mode', {
      headers,
      data: {
        mode: 'general'
      }
    });
    
    const response2 = await request.get('/api/merchant/mode', { headers });
    
    expect(response2.status()).toBe(200);
    
    const body2 = await response2.json();
    expect(body2.data.onboardingMode).toBe('general');
  });

  test('[P2] should validate mode value format', async ({ request }) => {
    const response = await request.patch('/api/merchant/mode', {
      headers: {
        'X-Test-Mode': 'true',
        'X-Merchant-Id': TEST_MERCHANT_ID,
      },
      data: {
        mode: 'INVALID_UPPERCASE'
      }
    });
    
    expect([400, 422]).toContain(response.status());
  });
});
