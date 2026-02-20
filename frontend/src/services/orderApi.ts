/**
 * Order API service for preview chat
 *
 * Fetches order data for order tracking in the preview chat interface.
 */

const API_BASE_URL = '';

export interface OrderDetails {
  found: boolean;
  order_number: string;
  status: string;
  fulfillment_status: string | null;
  tracking_number: string | null;
  tracking_url: string | null;
  customer_email: string | null;
  total: string;
  currency: string;
  created_at: string | null;
  estimated_delivery: string | null;
  formatted_response: string;
  message?: string;
}

export interface OrderSummary {
  order_number: string;
  status: string;
  tracking_number: string | null;
  total: string;
  currency: string;
  created_at: string | null;
}

export interface OrderListResponse {
  orders: OrderSummary[];
  total: number;
}

/**
 * Track an order by order number
 */
export async function trackOrder(
  merchantId: number,
  orderNumber: string
): Promise<OrderDetails> {
  const url = `${API_BASE_URL}/api/v1/preview/orders/${encodeURIComponent(orderNumber)}`;

  const response = await fetch(url, {
    headers: {
      'X-Merchant-Id': String(merchantId),
    },
    credentials: 'include',
  });

  if (!response.ok) {
    throw new Error(`Failed to track order: ${response.statusText}`);
  }

  const data = await response.json();
  return data.data;
}

/**
 * List recent orders, optionally filtered by email
 */
export async function listOrders(
  merchantId: number,
  email?: string,
  limit: number = 5
): Promise<OrderListResponse> {
  const params = new URLSearchParams();
  if (email) params.append('email', email);
  params.append('limit', String(limit));

  const url = `${API_BASE_URL}/api/v1/preview/orders?${params.toString()}`;

  const response = await fetch(url, {
    headers: {
      'X-Merchant-Id': String(merchantId),
    },
    credentials: 'include',
  });

  if (!response.ok) {
    throw new Error(`Failed to list orders: ${response.statusText}`);
  }

  const data = await response.json();
  return data.data;
}

/**
 * Extract order number from user message
 */
export function extractOrderNumber(text: string): string | null {
  const patterns = [
    /order\s*[#:]?\s*(\d{3,6})/i,
    /#\s*(\d{3,6})/,
    /order\s+number\s*[#:]?\s*(\d{3,6})/i,
    /(\d{4,6})/,
  ];

  for (const pattern of patterns) {
    const match = text.match(pattern);
    if (match) {
      return match[1];
    }
  }

  return null;
}

/**
 * Check if message is asking about order status
 */
export function isOrderQuery(text: string): boolean {
  const patterns = [
    /where.*order/i,
    /order.*status/i,
    /track.*order/i,
    /my\s+order/i,
    /order\s+#?\d/i,
    /shipping\s+status/i,
    /delivery\s+status/i,
    /when.*arrive/i,
    /has\s+.*\s+shipped/i,
  ];

  return patterns.some(pattern => pattern.test(text));
}
