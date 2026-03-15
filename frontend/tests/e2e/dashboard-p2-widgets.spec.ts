import { test, expect } from '@playwright/test';

test.describe('Dashboard P2 Widgets', () => {
  test('should display Benchmark Comparison widget', async ({ page }) => {
    await page.goto('/dashboard');
    
    const benchmarkWidget = page.getByTestId('benchmark-comparison-widget');
    await expect(benchmarkWidget).toBeVisible();
    
    const heading = benchmarkWidget.getByRole('heading');
    await expect(heading.first()).toContain('vs Industry');
    
    const percentile = benchmarkWidget.getByTestId('percentile-badge');
    await expect(percentile).toBeVisible();
  });

  test('should display Customer Sentiment widget', async ({ page }) => {
    await page.goto('/dashboard');
    
    const sentimentWidget = page.getByTestId('customer-sentiment-widget');
    await expect(sentimentWidget).toBeVisible();
    
    const trendIcon = sentimentWidget.locator('.trend-icon');
    await expect(trendIcon).toBeVisible();
    
    const positiveCount = sentimentWidget.getByTestId('positive-count');
    const negativeCount = sentimentWidget.getByTestId('negative-count');
    await expect(positiveCount).toBeVisible();
    await expect(negativeCount).toBeVisible();
  });

  test('should display 7-day sentiment breakdown', async ({ page }) => {
    await page.goto('/dashboard');
    
    const dailyBars = page.getByTestId('sentiment-daily-breakdown');
    await expect(dailyBars).toBeVisible();
    
    const bars = dailyBars.locator('div');
    await expect(bars).toHaveCount(7);
  });

  test('should show alert in declining sentiment', async ({ page }) => {
    await page.goto('/dashboard');
    
    const alert = page.getByTestId('sentiment-alert');
  });
});
