import { test, expect } from "@playwright/test";

const BASE_URL = process.env.BASE_URL || "http://localhost:5173";
const TEST_MERCHANT = {
  email: 'e2e-product-pins@test.com',
  password: 'TestPass123',
};

test("debug login flow - detailed", async ({ page }) => {
  // Set up console and network monitoring
  const consoleLogs: string[] = [];
  page.on("console", msg => consoleLogs.push(msg.text()));
  
  const apiRequests: string[] = [];
  page.on("request", request => {
    if (request.url().includes("/api/v1/auth/login")) {
      apiRequests.push(request.url());
      console.log("Login API called:", request.url());
    }
  });
  
  console.log("Step 1: Navigating to login page...");
  await page.goto(`${BASE_URL}/login`);
  await page.waitForLoadState("networkidle");
  
  // Fill form
  console.log("Step 2: Filling form...");
  await page.fill('input[name="email"]', TEST_MERCHANT.email);
  await page.fill('input[name="password"]', TEST_MERCHANT.password);
  
  // Check form exists
  const form = page.locator("form");
  const formExists = await form.isVisible();
  console.log("Form visible:", formExists);
  
  // Submit form
  console.log("Step 3: Clicking submit button...");
  const submitButton = page.locator('button[type="submit"]');
  await submitButton.click();
  
  // Wait for any navigation
  console.log("Step 4: Waiting for navigation...");
  await page.waitForTimeout(5000);
  
  const currentUrl = page.url();
  console.log("Current URL:", currentUrl);
  console.log("Console logs:", consoleLogs.slice(-10));
  console.log("API requests made:", apiRequests);
  
  // Check for any error messages
  const errorSelector = page.locator('[role="alert"]');
  const hasError = await errorSelector.isVisible().catch(() => false);
  console.log("Has error:", hasError);
  
  // Try waiting longer for dashboard
  try {
    await page.waitForURL(`${BASE_URL}/bot-config`, { timeout: 10000 });
    console.log("SUCCESS: Navigated to bot-config!");
  } catch (e) {
    console.log("FAIL: Did not navigate to bot-config");
    await page.screenshot({ path: "test-results/debug-failed-state.png" });
  }
  
  // Final check
  const finalUrl = page.url();
  console.log("Final URL:", finalUrl);
});
