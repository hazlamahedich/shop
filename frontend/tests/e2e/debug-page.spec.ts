import { test } from '@playwright/test';

test('debug widget-test.html page structure', async ({ page }) => {
  // Capture console logs
  page.on('console', msg => {
    console.log(`BROWSER [${msg.type()}]:`, msg.text());
  });
  
  // Capture page errors
  page.on('pageerror', error => {
    console.log('PAGE ERROR:', error.message);
  });
  
  await page.goto('/widget-test?merchantId=4&sessionId=test-id');
  
  // Wait a bit for any async operations
  await page.waitForTimeout(2000);
  
  // Debug page structure
  const debug = await page.evaluate(() => {
    return {
      iframeCount: document.querySelectorAll('iframe').length,
      iframes: Array.from(document.querySelectorAll('iframe')).map(f => ({
        srcdoc: f.srcdoc?.substring(0, 200),
        src: f.src
      })),
      widgetContainer: document.getElementById('widget-container')?.innerHTML?.substring(0, 500),
      bodyHTML: document.body.innerHTML?.substring(0, 1000)
    };
  });
  
  console.log('DEBUG page structure:', JSON.stringify(debug, null, 2));
});
