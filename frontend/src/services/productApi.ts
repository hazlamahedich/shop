/**
 * Product API service for preview chat
 *
 * Fetches product data from Shopify for displaying product cards
 * in the preview chat interface.
 */

const API_BASE_URL = ''; // Relative path for proxy

export interface PreviewProduct {
  id: string;
  title: string;
  description: string;
  image_url: string | null;
  price: string;
  available: boolean;
  inventory_quantity: number;
  product_type: string | null;
  vendor: string | null;
  variant_id: string | null;
  shop_domain?: string | null;
}

export interface ProductSearchResponse {
  products: PreviewProduct[];
  total: number;
  query: string;
  filters: {
    max_price: number | null;
    category: string | null;
  };
  shop_domain: string | null;
}

export interface ShopDomainResponse {
  shop_domain: string;
}

/**
 * Search products with optional filters
 */
export async function searchProducts(
  merchantId: number,
  options: {
    query?: string;
    maxPrice?: number;
    category?: string;
    limit?: number;
  } = {}
): Promise<ProductSearchResponse> {
  const params = new URLSearchParams();
  
  if (options.query) params.append('query', options.query);
  if (options.maxPrice !== undefined) params.append('max_price', String(options.maxPrice));
  if (options.category) params.append('category', options.category);
  if (options.limit) params.append('limit', String(options.limit));

  const queryString = params.toString();
  const url = `${API_BASE_URL}/api/v1/preview/products${queryString ? `?${queryString}` : ''}`;

  const response = await fetch(url, {
    headers: {
      'X-Merchant-Id': String(merchantId),
    },
    credentials: 'include',
  });

  if (!response.ok) {
    throw new Error(`Failed to search products: ${response.statusText}`);
  }

  const data = await response.json();
  return data.data;
}

/**
 * Get single product by ID
 */
export async function getProduct(
  merchantId: number,
  productId: string
): Promise<PreviewProduct> {
  const url = `${API_BASE_URL}/api/v1/preview/products/${productId}`;

  const response = await fetch(url, {
    headers: {
      'X-Merchant-Id': String(merchantId),
    },
    credentials: 'include',
  });

  if (!response.ok) {
    throw new Error(`Failed to get product: ${response.statusText}`);
  }

  const data = await response.json();
  return data.data;
}

/**
 * Detect price references in text and find matching products
 */
export function extractPriceFromText(text: string): number | null {
  const patterns = [
    /under\s+\$?(\d+)/i,
    /below\s+\$?(\d+)/i,
    /less\s+than\s+\$?(\d+)/i,
    /cheaper\s+than\s+\$?(\d+)/i,
    /\$?(\d+)\s+or\s+less/i,
    /<\s*\$?(\d+)/i,
  ];

  for (const pattern of patterns) {
    const match = text.match(pattern);
    if (match) {
      return parseFloat(match[1]);
    }
  }

  return null;
}

/**
 * Detect product category mentions in text
 */
export function extractCategoryFromText(
  text: string,
  availableCategories: string[]
): string | null {
  const lowerText = text.toLowerCase();
  
  for (const category of availableCategories) {
    if (lowerText.includes(category.toLowerCase())) {
      return category;
    }
  }

  return null;
}

/**
 * Get the Shopify shop domain for checkout
 */
export async function getShopDomain(merchantId: number): Promise<string> {
  const url = `${API_BASE_URL}/api/v1/preview/shop-domain`;

  const response = await fetch(url, {
    headers: {
      'X-Merchant-Id': String(merchantId),
    },
    credentials: 'include',
  });

  if (!response.ok) {
    throw new Error('No Shopify store connected');
  }

  const data = await response.json();
  return data.data.shop_domain;
}

/**
 * Build a Shopify cart permalink URL for checkout
 * 
 * Format: https://{shop}.myshopify.com/cart/{variant_id}:{quantity},{variant_id}:{quantity}
 */
export function buildCheckoutUrl(
  shopDomain: string,
  items: Array<{ variantId: string; quantity: number }>
): string {
  if (!shopDomain || items.length === 0) {
    console.warn('buildCheckoutUrl: Missing shopDomain or items', { shopDomain, items });
    return '';
  }

  const validItems = items.filter(item => item.variantId && item.quantity > 0);
  
  if (validItems.length === 0) {
    console.warn('buildCheckoutUrl: No valid items with variantId', { items });
    return '';
  }

  const cartItems = validItems
    .map(item => `${item.variantId}:${item.quantity}`)
    .join(',');

  const url = `https://${shopDomain}/cart/${cartItems}`;
  console.log('buildCheckoutUrl:', { shopDomain, validItems, cartItems, url });
  
  return url;
}
