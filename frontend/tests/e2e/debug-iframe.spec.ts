import { test } from '@playwright/test';

test('debug iframe structure', async ({ page }) => {
  await page.goto('/widget-test?merchantId=4&sessionId=test-id');
  await page.waitForTimeout(2000);
  
  const pageInfo = await page.evaluate(() => {
    const iframes = document.querySelectorAll('iframe');
    const scripts = document.querySelectorAll('script[src*="widget"]');
    const chatBubbles = document.querySelectorAll('.shopbot-chat-bubble');
    
    return {
      iframeCount: iframes.length,
      iframeSrcdocs: Array.from(iframes).map(f => ({
        hasSrcdoc: !!f.srcdoc,
        srcdocLength: f.srcdoc?.length || 0,
        srcdocPreview: f.srcdoc?.substring(0, 500) || null
      })),
      scriptCount: scripts.length,
      scriptSrcs: Array.from(scripts).map(s => s.src),
      chatBubbleCount: chatBubbles.length,
      url: window.location.href,
      searchParams: window.location.search
    };
  });
  
  console.log('Page info:', JSON.stringify(pageInfo, null, 2));
});
