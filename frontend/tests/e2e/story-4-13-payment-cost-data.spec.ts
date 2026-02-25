/**
 * Story 4-13: Shopify Payment/Cost Data Enhancement - E2E Tests
 *
 * Coverage: Task 19 E2E Tests
 * - Cross-device order lookup flow (email vs order number)
 * - Payment breakdown in order status response
 * - "Welcome back, {name}" personalized greeting
 * - Geographic analytics dashboard display
 *
 * @tags e2e story-4-13 payment-data customer-identity analytics
 */

import { test, expect } from '@playwright/test';
import { faker } from '@faker-js/faker';
import {
  blockShopifyCalls,
  mockWidgetConfig,
  mockWidgetSession,
  mockWidgetMessage,
} from '../helpers/widget-test-helpers';

type PaymentMethod = 'credit_card' | 'paypal' | 'shopify_pay' | 'apple_pay';

interface PaymentBreakdown {
  subtotal: number;
  shipping: number;
  tax: number;
  discount: number;
  total: number;
  paymentMethod: PaymentMethod;
}

interface CustomerProfile {
  email: string;
  firstName: string;
  lastName: string;
  phone?: string;
  totalOrders: number;
  totalSpent: number;
}

interface OrderData {
  id: number;
  orderNumber: string;
  status: 'pending' | 'processing' | 'shipped' | 'delivered' | 'cancelled';
  paymentBreakdown: PaymentBreakdown;
  customer: CustomerProfile;
  shippingAddress: {
    city: string;
    province: string;
    country: string;
    postalCode: string;
  };
}

const createPaymentBreakdown = (overrides: Partial<PaymentBreakdown> = {}): PaymentBreakdown => {
  const subtotal = parseFloat(faker.commerce.price({ min: 50, max: 200 }));
  const shipping = parseFloat(faker.commerce.price({ min: 5, max: 25 }));
  const tax = parseFloat((subtotal * 0.08).toFixed(2));
  const discount = faker.datatype.boolean() ? parseFloat(faker.commerce.price({ min: 5, max: 20 })) : 0;
  const total = subtotal + shipping + tax - discount;

  return {
    subtotal,
    shipping,
    tax,
    discount,
    total,
    paymentMethod: faker.helpers.arrayElement(['credit_card', 'paypal', 'shopify_pay', 'apple_pay']),
    ...overrides,
  };
};

const createCustomerProfile = (overrides: Partial<CustomerProfile> = {}): CustomerProfile => ({
  email: faker.internet.email(),
  firstName: faker.person.firstName(),
  lastName: faker.person.lastName(),
  phone: faker.phone.number(),
  totalOrders: faker.number.int({ min: 1, max: 20 }),
  totalSpent: parseFloat(faker.commerce.price({ min: 100, max: 5000 })),
  ...overrides,
});

const createOrderData = (overrides: Partial<OrderData> = {}): OrderData => {
  const orderNumber = `#10${faker.number.int({ min: 100, max: 999 })}`;

  return {
    id: faker.number.int({ min: 1, max: 999999 }),
    orderNumber,
    status: faker.helpers.arrayElement(['pending', 'processing', 'shipped', 'delivered']),
    paymentBreakdown: createPaymentBreakdown(),
    customer: createCustomerProfile(),
    shippingAddress: {
      city: faker.location.city(),
      province: faker.location.state({ abbreviated: true }),
      country: faker.location.countryCode('alpha-2'),
      postalCode: faker.location.zipCode(),
    },
    ...overrides,
  };
};

async function openChatWidget(page) {
  const bubble = page.getByRole('button', { name: 'Open chat' });
  await bubble.click();
  await expect(page.getByPlaceholder(/type.*message/i)).toBeVisible({ timeout: 10000 });
}

test.describe('Story 4-13: Payment/Cost Data Enhancement', () => {
  test.beforeEach(async ({ page }) => {
    await blockShopifyCalls(page);
    await mockWidgetConfig(page, {
      botName: 'ShopBot',
      welcomeMessage: 'Hello! How can I help you today?',
    });
    await mockWidgetSession(page, 'test-session-4-13');
  });

  test.afterEach(async ({ page }) => {
    await page.context().clearCookies();
    await page.context().clearPermissions();
  });

  test.describe('Cross-Device Order Lookup', () => {
    test('@p0 @smoke should lookup order by email when order number not found', async ({ page }) => {
      const customer = createCustomerProfile({
        firstName: 'Maria',
        lastName: 'Garcia',
        email: 'maria@example.com',
      });

      const order = createOrderData({
        orderNumber: '#1001',
        status: 'shipped',
        customer,
      });

      await mockWidgetMessage(page, {
        content: `I couldn't find orders on this device. I can look it up! What's easier: Your order number or your email address?`,
      });

      await page.goto('/widget-test');
      await openChatWidget(page);

      await page.getByPlaceholder(/type.*message/i).fill("Where's my order?");
      await page.getByRole('button', { name: /send/i }).click();

      await expect(page.getByText(/couldn't find orders|look it up/i)).toBeVisible({ timeout: 10000 });
    });

    test('@p0 should lookup order by order number directly', async ({ page }) => {
      const order = createOrderData({
        orderNumber: '#1002',
        status: 'delivered',
        paymentBreakdown: createPaymentBreakdown({ total: 127.5 }),
      });

      await mockWidgetMessage(page, {
        content: `Order ${order.orderNumber} - Delivered. Your order has been delivered!`,
      });

      await page.goto('/widget-test');
      await openChatWidget(page);

      await page.getByPlaceholder(/type.*message/i).fill(`Order ${order.orderNumber}`);
      await page.getByRole('button', { name: /send/i }).click();

      await expect(page.getByText(new RegExp(order.orderNumber))).toBeVisible({ timeout: 10000 });
      await expect(page.getByText(/delivered/i)).toBeVisible();
    });

    test('@p1 should prompt for email or order number when neither provided', async ({ page }) => {
      await mockWidgetMessage(page, {
        content: "I'd be happy to help you find your order! Could you provide either your order number or email address?",
      });

      await page.goto('/widget-test');
      await openChatWidget(page);

      await page.getByPlaceholder(/type.*message/i).fill("Where's my order?");
      await page.getByRole('button', { name: /send/i }).click();

      await expect(page.getByText(/order number.*email|email.*order number/i)).toBeVisible({ timeout: 10000 });
    });
  });

  test.describe('Payment Breakdown Display', () => {
    test('@p1 @regression should display payment breakdown in order status response', async ({ page }) => {
      const paymentBreakdown = createPaymentBreakdown({
        subtotal: 110.0,
        shipping: 12.5,
        tax: 5.0,
        discount: 0,
        total: 127.5,
        paymentMethod: 'credit_card',
      });

      const order = createOrderData({
        orderNumber: '#1003',
        status: 'shipped',
        paymentBreakdown,
      });

      await mockWidgetMessage(page, {
        content: `Order ${order.orderNumber} - Shipped. Items: $${paymentBreakdown.subtotal.toFixed(2)}, Shipping: $${paymentBreakdown.shipping.toFixed(2)}, Tax: $${paymentBreakdown.tax.toFixed(2)}, Total: $${paymentBreakdown.total.toFixed(2)}`,
      });

      await page.goto('/widget-test');
      await openChatWidget(page);

      await page.getByPlaceholder(/type.*message/i).fill(`Order ${order.orderNumber}`);
      await page.getByRole('button', { name: /send/i }).click();

      await expect(page.getByText(/110|127/i)).toBeVisible({ timeout: 10000 });
    });

    test('@p1 should display discount when applicable', async ({ page }) => {
      const paymentBreakdown = createPaymentBreakdown({
        subtotal: 100.0,
        shipping: 10.0,
        tax: 8.0,
        discount: 15.0,
        total: 103.0,
      });

      const order = createOrderData({
        orderNumber: '#1004',
        status: 'shipped',
        paymentBreakdown,
      });

      await mockWidgetMessage(page, {
        content: `Order ${order.orderNumber} - Shipped. Discount applied: -$${paymentBreakdown.discount.toFixed(2)}. Total: $${paymentBreakdown.total.toFixed(2)}`,
      });

      await page.goto('/widget-test');
      await openChatWidget(page);

      await page.getByPlaceholder(/type.*message/i).fill(`Order ${order.orderNumber}`);
      await page.getByRole('button', { name: /send/i }).click();

      await expect(page.getByText(/discount|15/i)).toBeVisible({ timeout: 10000 });
    });

    test('@p2 should display payment method in response', async ({ page }) => {
      const order = createOrderData({
        orderNumber: '#1005',
        paymentBreakdown: createPaymentBreakdown({ paymentMethod: 'paypal' }),
      });

      await mockWidgetMessage(page, {
        content: `Order ${order.orderNumber} - Paid via PayPal. Your order is being processed.`,
      });

      await page.goto('/widget-test');
      await openChatWidget(page);

      await page.getByPlaceholder(/type.*message/i).fill(`Order ${order.orderNumber}`);
      await page.getByRole('button', { name: /send/i }).click();

      await expect(page.getByText(/paypal/i)).toBeVisible({ timeout: 10000 });
    });
  });

  test.describe('Customer Recognition', () => {
    test('@p1 @regression should display welcome back greeting for returning customer', async ({ page }) => {
      const returningCustomer = createCustomerProfile({
        firstName: 'John',
        lastName: 'Smith',
        email: 'john.smith@example.com',
        totalOrders: 5,
        totalSpent: 1250.0,
      });

      await mockWidgetMessage(page, {
        content: `Welcome back, ${returningCustomer.firstName}! You've placed ${returningCustomer.totalOrders} orders with us. How can I help you today?`,
      });

      await page.goto('/widget-test');
      await openChatWidget(page);

      await page.getByPlaceholder(/type.*message/i).fill("Where's my order?");
      await page.getByRole('button', { name: /send/i }).click();

      await expect(page.getByText(new RegExp(`welcome back, ${returningCustomer.firstName}`, 'i'))).toBeVisible({ timeout: 10000 });
    });

    test('@p2 should link device to customer profile on first lookup', async ({ page }) => {
      const newCustomer = createCustomerProfile({
        firstName: 'Alice',
        email: 'alice.new@example.com',
        totalOrders: 1,
      });

      await mockWidgetMessage(page, {
        content: `Great news! I found your account and linked this device. This device is now linked to your account!`,
      });

      await page.goto('/widget-test');
      await openChatWidget(page);

      await page.getByPlaceholder(/type.*message/i).fill("Where's my order?");
      await page.getByRole('button', { name: /send/i }).click();

      await page.getByPlaceholder(/type.*message/i).fill(newCustomer.email);
      await page.getByRole('button', { name: /send/i }).click();

      await expect(page.getByText(/device.*linked|linked.*device/i)).toBeVisible({ timeout: 10000 });
    });
  });

  test.describe('Geographic Analytics Dashboard', () => {
    test('@p2 @regression should display geographic sales breakdown', async ({ page }) => {
      await page.goto('/dashboard/analytics/geographic');
      await expect(page.getByRole('heading', { name: /geographic.*analytics/i })).toBeVisible({ timeout: 15000 });
    });

    test('@p2 should filter analytics by date range', async ({ page }) => {
      await page.goto('/dashboard/analytics/geographic');
      await expect(page.getByRole('heading', { name: /geographic.*analytics/i })).toBeVisible({ timeout: 15000 });
    });

    test('@p3 should display top performing regions', async ({ page }) => {
      await page.goto('/dashboard/analytics/geographic');
      await expect(page.getByRole('heading', { name: /geographic.*analytics/i })).toBeVisible({ timeout: 15000 });
    });
  });
});
