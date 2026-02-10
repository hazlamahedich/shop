import { test as base } from '@playwright/test';

type InterceptOptions = {
  url: string;
  method?: string;
  fulfillResponse?: { status: number; body: any };
};

export const test = base.extend<{
  interceptNetworkCall: (
    options: InterceptOptions
  ) => Promise<{ status: number; requestJson: any; responseJson: any }>;
}>({
  interceptNetworkCall: async ({ page }, use) => {
    // Add X-Test-Mode header to bypass CSRF validation for all API requests
    await page.route('**/api/**', async (route) => {
      const headers = route.request().headers();
      // Add test mode header to bypass CSRF validation
      headers['X-Test-Mode'] = 'true';
      await route.continue({ headers });
    });

    const intercept = async (options: InterceptOptions) => {
      const { url, method, fulfillResponse } = options;

      // Simple glob to regex conversion (very basic)
      // Playwright route accepts glob strings directly, so we use those.
      const routeUrl = url;

      if (fulfillResponse) {
        await page.route(routeUrl, async (route) => {
          if (!method || route.request().method() === method) {
            await route.fulfill({
              status: fulfillResponse.status,
              contentType: 'application/json',
              body: JSON.stringify(fulfillResponse.body),
            });
          } else {
            await route.continue();
          }
        });
      }

      // Wait for response
      // Note: page.waitForResponse predicate
      const responsePromise = page.waitForResponse((resp) => {
        // Basic match check
        const respUrl = resp.url();
        // If url is glob like **/api/users, check inclusion
        // This is a naive implementation compared to picomatch
        const matchUrl = url.replace('**', '');
        return respUrl.includes(matchUrl) && (!method || resp.request().method() === method);
      });

      return responsePromise.then(async (resp) => {
        let requestJson, responseJson;
        try {
          requestJson = await resp.request().postDataJSON();
        } catch {}
        try {
          responseJson = await resp.json();
        } catch {}

        return {
          status: resp.status(),
          requestJson,
          responseJson,
        };
      });
    };

    await use(intercept);
  },
});
