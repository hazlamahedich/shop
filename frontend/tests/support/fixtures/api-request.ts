import { test as base } from '@playwright/test';

type ApiRequestOptions = {
  method: string;
  path: string;
  body?: any;
  headers?: Record<string, string>;
  retryConfig?: { maxRetries: number };
  baseURL?: string;
};

export const test = base.extend<{
  apiRequest: (options: ApiRequestOptions) => Promise<{ status: number; body: any }>;
}>({
  apiRequest: async ({ request, baseURL: configBaseURL }, use) => {
    const makeRequest = async (options: ApiRequestOptions) => {
      const baseURL = options.baseURL || configBaseURL || '';
      const url = options.path.startsWith('http') ? options.path : `${baseURL}${options.path}`;

      const response = await request.fetch(url, {
        method: options.method,
        data: options.body,
        headers: options.headers,
      });

      let body;
      try {
        body = await response.json();
      } catch {
        body = await response.text();
      }

      return {
        status: response.status(),
        body,
      };
    };

    await use(makeRequest);
  },
});
