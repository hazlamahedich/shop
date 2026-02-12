const { chromium } = require('@playwright/test');

(async () => {
  const browser = await chromium.launch();
  const context = await browser.newContext();
  const page = await context.newPage();

  // Enable console logging
  page.on('console', msg => console.log('PAGE CONSOLE:', msg.text()));
  
  // Enable request logging
  page.on('request', request => {
    if (request.url().includes('/auth/login')) {
      console.log('LOGIN REQUEST:', request.url());
    }
  });
  
  page.on('response', async response => {
    if (response.url().includes('/auth/login')) {
      console.log('LOGIN RESPONSE:', response.status());
      try {
        const body = await response.text();
        console.log('LOGIN BODY:', body);
      } catch (e) {
        console.log('LOGIN BODY ERROR:', e.message);
      }
    }
  });

  try {
    await page.goto('http://localhost:5173/login');
    await page.fill('input[name="email"]', 'e2e-test@example.com');
    await page.fill('input[name="password"]', 'TestPass123');
    await page.click('button[type="submit"]');
    
    // Wait up to 10 seconds for navigation
    await page.waitForURL(/.*\/dashboard/, { timeout: 10000 });
    console.log('SUCCESS: Navigated to dashboard');
  } catch (error) {
    console.log('ERROR:', error.message);
  }

  await browser.close();
})();
