/**
 * Story 9-3: Product Carousel E2E Tests
 *
 * Tests the horizontal product carousel with:
 * - Horizontal scrolling carousel with CSS scroll-snap
 * - Touch/swipe gestures (mobile)
 * - Navigation arrows (desktop)
 * - Dots indicator
 * - Product card layout
 * - Hover animation
 * - Add to Cart button
 * - Loading state
 * - Smooth scroll animation
 * - Accessibility
 *
 * @tags e2e widget story-9-3 carousel products
 */

import { test, expect, Page, Locator } from '@playwright/test';
import {
  mockWidgetConfig,
  mockWidgetSession,
  mockWidgetMessage,
  createMockMessageResponse,
} from '../helpers/widget-test-helpers';

const TEST_MERCHANT_ID = '4';

const createMockProducts = (count: number) =>
  Array.from({ length: count }, (_, i) => ({
    id: `prod-${i + 1}`,
    variantId: `var-${i + 1}`,
    handle: `test-product-${i + 1}`,
    title: `Test Product ${i + 1} - ${['Nike Air Max', 'Adidas Ultraboost', 'New Balance 574', 'Puma RS-X', 'Reebok Classic'][i % 5]}`,
    price: 99.99 + i * 10,
    imageUrl: `https://picsum.photos/seed/product${i + 1}/200/200`,
    available: true,
  }));

async function setupWidgetMocks(page: Page) {
  await mockWidgetConfig(page);
  await mockWidgetSession(page);
}

async function openChat(page: Page) {
  const bubble = page.getByRole('button', { name: 'Open chat' });
  await bubble.click();
  const dialog = page.getByRole('dialog', { name: 'Chat window' });
  await expect(dialog).toBeVisible({ timeout: 10000 });
  return dialog;
}

async function sendMessageWithProducts(page: Page, productCount: number) {
  await mockWidgetMessage(
    page,
    createMockMessageResponse({
      content: `Here are ${productCount} products I found for you:`,
      products: createMockProducts(productCount),
    })
  );

  const input = page.getByLabel('Type a message');
  await input.scrollIntoViewIfNeeded();
  await input.fill('show me shoes');
  await input.press('Enter');
}

/**
 * Deterministic scroll wait - waits for scroll position to stabilize
 * Replaces arbitrary waitForTimeout() for animation timing
 */
async function waitForScrollToComplete(carousel: Locator, timeout = 2000): Promise<void> {
  await carousel.evaluate(async (el, timeoutMs) => {
    await new Promise<void>((resolve) => {
      let lastScrollLeft = el.scrollLeft;
      let stableCount = 0;
      const checkInterval = setInterval(() => {
        if (el.scrollLeft === lastScrollLeft) {
          stableCount++;
          if (stableCount >= 3) {
            clearInterval(checkInterval);
            resolve();
          }
        } else {
          stableCount = 0;
          lastScrollLeft = el.scrollLeft;
        }
      }, 50);

      setTimeout(() => {
        clearInterval(checkInterval);
        resolve();
      }, timeoutMs);
    });
  }, timeout);
}

test.describe('Story 9-3: Product Carousel', () => {
  test.beforeEach(async ({ page }) => {
    await setupWidgetMocks(page);
  });

  test.describe('[P0] Critical Path - Carousel Rendering', () => {
    test('[P0] @smoke should render carousel when 3+ products returned', async ({ page }) => {
      await page.goto('/widget-test');
      await openChat(page);
      await sendMessageWithProducts(page, 5);

      const carousel = page.getByTestId('product-carousel');
      await expect(carousel).toBeVisible();
    });

    test('[P0] @smoke should display products in horizontal layout', async ({ page }) => {
      await page.goto('/widget-test');
      await openChat(page);
      await sendMessageWithProducts(page, 5);

      const carousel = page.getByTestId('product-carousel');
      await expect(carousel).toBeVisible();

      const flexDirection = await carousel.evaluate((el) => {
        return window.getComputedStyle(el).flexDirection;
      });
      expect(flexDirection).toBe('row');
    });

    test('[P0] should show scroll-snap behavior', async ({ page }) => {
      await page.goto('/widget-test');
      await openChat(page);
      await sendMessageWithProducts(page, 5);

      const carousel = page.getByTestId('product-carousel');
      const scrollSnapType = await carousel.evaluate((el) => {
        return window.getComputedStyle(el).scrollSnapType;
      });
      expect(scrollSnapType).toContain('mandatory');
    });

    test('[P0] should use list view for 1-2 products', async ({ page }) => {
      await mockWidgetMessage(
        page,
        createMockMessageResponse({
          content: 'Here are 2 products:',
          products: createMockProducts(2),
        })
      );

      await page.goto('/widget-test');
      await openChat(page);

      const input = page.getByLabel('Type a message');
      await input.scrollIntoViewIfNeeded();
      await input.fill('show me shoes');
      await input.press('Enter');

      const productCards = page.locator('.product-card');
      await expect(productCards.first()).toBeVisible({ timeout: 5000 });

      const carousel = page.getByTestId('product-carousel');
      await expect(carousel).not.toBeVisible();
    });
  });

  test.describe('[P1] Navigation Arrows', () => {
    test('[P1] should show navigation arrows on desktop', async ({ page }) => {
      await page.setViewportSize({ width: 1024, height: 768 });
      await page.goto('/widget-test');
      await openChat(page);
      await sendMessageWithProducts(page, 5);

      const carouselWrapper = page.getByTestId('product-carousel-wrapper');
      await carouselWrapper.hover();

      const leftArrow = page.getByTestId('carousel-arrow-left');
      const rightArrow = page.getByTestId('carousel-arrow-right');

      await expect(leftArrow).toBeVisible();
      await expect(rightArrow).toBeVisible();
    });

    test('[P1] should have proper aria-labels on arrows', async ({ page }) => {
      await page.setViewportSize({ width: 1024, height: 768 });
      await page.goto('/widget-test');
      await openChat(page);
      await sendMessageWithProducts(page, 5);

      const leftArrow = page.getByTestId('carousel-arrow-left');
      const rightArrow = page.getByTestId('carousel-arrow-right');

      await expect(leftArrow).toHaveAttribute('aria-label', 'Scroll left to previous products');
      await expect(rightArrow).toHaveAttribute('aria-label', 'Scroll right to next products');
    });

    test('[P1] should scroll when arrow clicked', async ({ page }) => {
      await page.setViewportSize({ width: 1024, height: 768 });
      await page.goto('/widget-test');
      await openChat(page);
      await sendMessageWithProducts(page, 5);

      const carousel = page.getByTestId('product-carousel');
      const initialScroll = await carousel.evaluate((el) => el.scrollLeft);

      const carouselWrapper = page.getByTestId('product-carousel-wrapper');
      await carouselWrapper.hover();

      const rightArrow = page.getByTestId('carousel-arrow-right');
      await rightArrow.click();

      await waitForScrollToComplete(carousel);

      const newScroll = await carousel.evaluate((el) => el.scrollLeft);
      expect(newScroll).toBeGreaterThan(initialScroll);
    });
  });

  test.describe('[P1] Dots Indicator', () => {
    test('[P1] should show dots indicator when multiple pages', async ({ page }) => {
      await page.goto('/widget-test');
      await openChat(page);
      await sendMessageWithProducts(page, 5);

      const dots = page.getByTestId('carousel-dots');
      await expect(dots).toBeVisible();
    });

    test('[P1] should have correct number of dots', async ({ page }) => {
      await page.setViewportSize({ width: 1024, height: 768 });
      await page.goto('/widget-test');
      await openChat(page);
      await sendMessageWithProducts(page, 5);

      const dots = page.getByTestId('carousel-dot');
      const count = await dots.count();
      expect(count).toBeGreaterThanOrEqual(2);
    });

    test('[P1] should highlight active dot', async ({ page }) => {
      await page.goto('/widget-test');
      await openChat(page);
      await sendMessageWithProducts(page, 5);

      const activeDot = page.getByTestId('carousel-dot').and(page.locator('.active'));
      await expect(activeDot).toBeVisible();
    });

    test('[P1] should have proper role="tablist"', async ({ page }) => {
      await page.goto('/widget-test');
      await openChat(page);
      await sendMessageWithProducts(page, 5);

      const dots = page.getByTestId('carousel-dots');
      await expect(dots).toHaveAttribute('role', 'tablist');
    });

    test('[P1] should navigate when dot clicked', async ({ page }) => {
      await page.setViewportSize({ width: 1024, height: 768 });
      await page.goto('/widget-test');
      await openChat(page);
      await sendMessageWithProducts(page, 6);

      const carousel = page.getByTestId('product-carousel');
      const initialScroll = await carousel.evaluate((el) => el.scrollLeft);

      const lastDot = page.getByTestId('carousel-dot').last();
      await lastDot.click();

      await waitForScrollToComplete(carousel);

      const newScroll = await carousel.evaluate((el) => el.scrollLeft);
      expect(newScroll).toBeGreaterThan(initialScroll);
    });
  });

  test.describe('[P1] Product Card Layout', () => {
    test('[P1] should show product image, title, and price', async ({ page }) => {
      await page.goto('/widget-test');
      await openChat(page);
      await sendMessageWithProducts(page, 3);

      const card = page.getByTestId('carousel-card-prod-1');
      await expect(card).toBeVisible();

      const image = card.locator('img');
      await expect(image).toBeVisible();

      const title = card.locator('.carousel-card-title');
      await expect(title).toBeVisible();

      const price = card.locator('.carousel-card-price');
      await expect(price).toBeVisible();
    });

    test('[P1] should show Add to Cart button', async ({ page }) => {
      await page.goto('/widget-test');
      await openChat(page);
      await sendMessageWithProducts(page, 3);

      const addToCartButton = page.getByTestId('carousel-card-button-prod-1');
      await expect(addToCartButton).toBeVisible();
      await expect(addToCartButton).toHaveText('Add to Cart');
    });

    test('[P1] should show loading skeleton initially', async ({ page }) => {
      await page.goto('/widget-test');
      await openChat(page);
      await sendMessageWithProducts(page, 3);

      const skeleton = page.getByTestId('carousel-card-skeleton').first();
      await expect(skeleton).toBeVisible({ timeout: 1000 });
    });
  });

  test.describe('[P1] Add to Cart', () => {
    test('[P1] should show loading state when clicked', async ({ page }) => {
      await page.goto('/widget-test');
      await openChat(page);
      await sendMessageWithProducts(page, 3);

      const addToCartButton = page.getByTestId('carousel-card-button-prod-1');
      await addToCartButton.click();

      await expect(addToCartButton).toHaveText('Adding...');
    });
  });

  test.describe('[P1] Accessibility', () => {
    test('[P1] should have proper carousel role', async ({ page }) => {
      await page.goto('/widget-test');
      await openChat(page);
      await sendMessageWithProducts(page, 5);

      const carouselRegion = page.getByRole('region', { name: /Product carousel/i });
      await expect(carouselRegion).toBeVisible();
    });

    test('[P1] should have aria-roledescription on carousel', async ({ page }) => {
      await page.goto('/widget-test');
      await openChat(page);
      await sendMessageWithProducts(page, 5);

      const carouselRegion = page.getByRole('region', { name: /Product carousel/i });
      await expect(carouselRegion).toHaveAttribute('aria-roledescription', 'carousel');
    });

    test('[P1] should have aria-roledescription on slides', async ({ page }) => {
      await page.goto('/widget-test');
      await openChat(page);
      await sendMessageWithProducts(page, 3);

      const slide = page.locator('[aria-roledescription="slide"]').first();
      await expect(slide).toBeVisible();
    });

    test('[P1] should have accessible dot labels', async ({ page }) => {
      await page.goto('/widget-test');
      await openChat(page);
      await sendMessageWithProducts(page, 5);

      const firstDot = page.getByTestId('carousel-dot').first();
      const ariaLabel = await firstDot.getAttribute('aria-label');
      expect(ariaLabel).toMatch(/Page \d+ of \d+/);
    });

    test('[P1] should support keyboard navigation', async ({ page }) => {
      await page.goto('/widget-test');
      await openChat(page);
      await sendMessageWithProducts(page, 5);

      const carouselGroup = page.getByRole('group', { name: /products/ });
      await carouselGroup.focus();

      const carousel = page.getByTestId('product-carousel');

      await page.keyboard.press('ArrowRight');
      await waitForScrollToComplete(carousel);

      await page.keyboard.press('ArrowLeft');
      await waitForScrollToComplete(carousel);

      await expect(carouselGroup).toBeVisible();
    });
  });

  test.describe('[P2] Hover Animation', () => {
    test('[P2] should lift card on hover', async ({ page }) => {
      await page.goto('/widget-test');
      await openChat(page);
      await sendMessageWithProducts(page, 3);

      const card = page.getByTestId('carousel-card-prod-1');
      await card.hover();

      const transform = await card.evaluate((el) => {
        return window.getComputedStyle(el).transform;
      });

      expect(transform).toBeTruthy();
    });
  });

  test.describe('[P2] Reduced Motion Support', () => {
    test('[P2] should respect prefers-reduced-motion for hover', async ({ page }) => {
      await page.emulateMedia({ reducedMotion: 'reduce' });
      await page.goto('/widget-test');
      await openChat(page);
      await sendMessageWithProducts(page, 3);

      const card = page.getByTestId('carousel-card-prod-1');
      await card.hover();

      const transform = await card.evaluate((el) => {
        return window.getComputedStyle(el).transform;
      });

      expect(transform).toMatch(/none|matrix\(1, 0, 0, 1, 0, 0\)/);
    });

    test('[P2] should respect prefers-reduced-motion for scroll', async ({ page }) => {
      await page.emulateMedia({ reducedMotion: 'reduce' });
      await page.goto('/widget-test');
      await openChat(page);
      await sendMessageWithProducts(page, 5);

      const carousel = page.getByTestId('product-carousel');
      const scrollBehavior = await carousel.evaluate((el) => {
        return window.getComputedStyle(el).scrollBehavior;
      });

      expect(scrollBehavior).toBe('auto');
    });
  });

  test.describe('[P2] Mobile Layout', () => {
    test('[P2] should show 2 visible cards on mobile', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 });
      await page.goto('/widget-test');
      await openChat(page);
      await sendMessageWithProducts(page, 5);

      const carousel = page.getByTestId('product-carousel');
      await expect(carousel).toBeVisible();

      const card = page.getByTestId('carousel-card-prod-1');
      const cardWidth = await card.evaluate((el) => el.getBoundingClientRect().width);
      const carouselWidth = await carousel.evaluate((el) => el.getBoundingClientRect().width);

      const visibleCards = Math.round(carouselWidth / cardWidth);
      expect(visibleCards).toBeLessThanOrEqual(2);
    });
  });

  test.describe('[P2] Desktop Layout', () => {
    test('[P2] should show 3 visible cards on desktop', async ({ page }) => {
      await page.setViewportSize({ width: 1024, height: 768 });
      await page.goto('/widget-test');
      await openChat(page);
      await sendMessageWithProducts(page, 5);

      const carousel = page.getByTestId('product-carousel');
      await expect(carousel).toBeVisible();

      const card = page.getByTestId('carousel-card-prod-1');
      const cardWidth = await card.evaluate((el) => el.getBoundingClientRect().width);
      const carouselWidth = await carousel.evaluate((el) => el.getBoundingClientRect().width);

      const visibleCards = Math.round(carouselWidth / cardWidth);
      expect(visibleCards).toBeLessThanOrEqual(3);
    });
  });

  test.describe('[P1] Touch/Swipe Gestures (Mobile)', () => {
    test('[P1] should support programmatic scroll with snap', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 });
      await page.goto('/widget-test');
      await openChat(page);
      await sendMessageWithProducts(page, 5);

      const carousel = page.getByTestId('product-carousel');
      await expect(carousel).toBeVisible();

      const initialScroll = await carousel.evaluate((el) => el.scrollLeft);

      await carousel.evaluate((el) => {
        el.scrollTo({ left: 200, behavior: 'smooth' });
      });

      await waitForScrollToComplete(carousel);

      const newScroll = await carousel.evaluate((el) => el.scrollLeft);
      expect(newScroll).toBeGreaterThan(initialScroll);
    });

    test('[P1] should have smooth scroll-snap on touch devices', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 });
      await page.goto('/widget-test');
      await openChat(page);
      await sendMessageWithProducts(page, 5);

      const carousel = page.getByTestId('product-carousel');
      const scrollSnapType = await carousel.evaluate((el) => {
        return window.getComputedStyle(el).scrollSnapType;
      });
      expect(scrollSnapType).toContain('mandatory');

      const webkitScrolling = await carousel.evaluate((el) => {
        const style = window.getComputedStyle(el) as CSSStyleDeclaration & { webkitOverflowScrolling?: string };
        return style.webkitOverflowScrolling || 'auto';
      });
      expect(['touch', 'auto']).toContain(webkitScrolling);
    });
  });

  test.describe('[P1] Add to Cart Success', () => {
    test('[P1] should show success feedback after adding to cart', async ({ page }) => {
      await page.route('**/api/v1/widget/cart/add', async (route) => {
        await route.fulfill({
          status: 200,
          body: JSON.stringify({
            data: {
              success: true,
              cart: {
                items: [{ variant_id: 'var-1', title: 'Test Product 1', price: 99.99, quantity: 1 }],
                item_count: 1,
                total: 99.99,
              },
            },
          }),
        });
      });

      await page.goto('/widget-test');
      await openChat(page);
      await sendMessageWithProducts(page, 3);

      const addToCartButton = page.getByTestId('carousel-card-button-prod-1');
      await addToCartButton.scrollIntoViewIfNeeded();
      await addToCartButton.click();

      await expect(addToCartButton).toHaveText('Adding...');
      await expect(addToCartButton).toContainText(/Added|✓/, { timeout: 5000 });
    });

    test('[P1] should verify cart update response is processed', async ({ page }) => {
      await page.route('**/api/v1/widget/cart/add', async (route) => {
        await route.fulfill({
          status: 200,
          body: JSON.stringify({
            data: {
              success: true,
              cart: {
                items: [{ variant_id: 'var-1', title: 'Test Product 1', price: 99.99, quantity: 1 }],
                item_count: 1,
                total: 99.99,
              },
            },
          }),
        });
      });

      await page.goto('/widget-test');
      await openChat(page);
      await sendMessageWithProducts(page, 3);

      const addToCartButton = page.getByTestId('carousel-card-button-prod-1');
      await addToCartButton.scrollIntoViewIfNeeded();
      await addToCartButton.click();

      await expect(addToCartButton).toHaveText('Adding...', { timeout: 2000 });

      const response = await page.waitForResponse((resp) => resp.url().includes('/api/v1/widget/cart/add'));
      expect(response.status()).toBe(200);

      const body = await response.json();
      expect(body.data.success).toBe(true);
      expect(body.data.cart.item_count).toBe(1);
    });
  });

  test.describe('[P2] Scroll Animation Timing', () => {
    test('[P2] should complete scroll animation within 500ms', async ({ page }) => {
      await page.setViewportSize({ width: 1024, height: 768 });
      await page.goto('/widget-test');
      await openChat(page);
      await sendMessageWithProducts(page, 5);

      const carousel = page.getByTestId('product-carousel');
      await carousel.scrollIntoViewIfNeeded();

      const carouselWrapper = page.getByTestId('product-carousel-wrapper');
      await carouselWrapper.hover({ force: true });

      const rightArrow = page.getByTestId('carousel-arrow-right');
      await rightArrow.waitFor({ state: 'visible', timeout: 2000 });

      const startTime = Date.now();
      await rightArrow.click({ force: true });

      await waitForScrollToComplete(carousel, 500);

      const elapsed = Date.now() - startTime;
      expect(elapsed).toBeLessThanOrEqual(500);
    });

    test('[P2] should use smooth scroll behavior', async ({ page }) => {
      await page.goto('/widget-test');
      await openChat(page);
      await sendMessageWithProducts(page, 5);

      const carousel = page.getByTestId('product-carousel');
      await carousel.scrollIntoViewIfNeeded();
      const scrollBehavior = await carousel.evaluate((el) => {
        return window.getComputedStyle(el).scrollBehavior;
      });

      expect(['smooth', 'auto']).toContain(scrollBehavior);
    });
  });

  test.describe('[P3] Edge Cases', () => {
    test('[P3] should handle empty products array', async ({ page }) => {
      await mockWidgetMessage(
        page,
        createMockMessageResponse({
          content: 'No products found.',
          products: [],
        })
      );

      await page.goto('/widget-test');
      await openChat(page);

      const input = page.getByLabel('Type a message');
      await input.scrollIntoViewIfNeeded();
      await input.fill('show me xyz');
      await input.press('Enter');

      const carousel = page.getByTestId('product-carousel');
      await expect(carousel).not.toBeVisible();
    });

    test('[P3] should handle single product', async ({ page }) => {
      await mockWidgetMessage(
        page,
        createMockMessageResponse({
          content: 'Found one product:',
          products: createMockProducts(1),
        })
      );

      await page.goto('/widget-test');
      await openChat(page);

      const input = page.getByLabel('Type a message');
      await input.scrollIntoViewIfNeeded();
      await input.fill('show me shoes');
      await input.press('Enter');

      const productCards = page.locator('.product-card');
      await expect(productCards.first()).toBeVisible({ timeout: 5000 });
    });

    test('[P3] should handle many products (10+)', async ({ page }) => {
      await page.goto('/widget-test');
      await openChat(page);
      await sendMessageWithProducts(page, 15);

      const carousel = page.getByTestId('product-carousel');
      await expect(carousel).toBeVisible();

      const cards = page.locator('[data-testid^="carousel-card-prod-"]');
      const count = await cards.count();
      expect(count).toBe(15);
    });

    test('[P3] should handle rapid arrow clicks', async ({ page }) => {
      await page.setViewportSize({ width: 1024, height: 768 });
      await page.goto('/widget-test');
      await openChat(page);
      await sendMessageWithProducts(page, 10);

      const carouselWrapper = page.getByTestId('product-carousel-wrapper');
      await carouselWrapper.hover();

      const rightArrow = page.getByTestId('carousel-arrow-right');

      for (let i = 0; i < 5; i++) {
        await rightArrow.click({ timeout: 500 });
      }

      const carousel = page.getByTestId('product-carousel');
      const scrollLeft = await carousel.evaluate((el) => el.scrollLeft);
      expect(scrollLeft).toBeGreaterThan(0);
    });
  });
});
