/**
 * Shopify AJAX Cart Client
 *
 * Syncs widget cart with the main Shopify store cart (the sliding drawer).
 * Uses Shopify's native AJAX Cart API which works on all Shopify themes.
 *
 * Only works when widget is embedded on a Shopify store domain.
 */

export interface ShopifyCartItem {
  id: number;
  variant_id: number;
  title: string;
  price: number;
  quantity: number;
  product_title: string;
  product_id: number;
}

export interface ShopifyCart {
  token: string;
  items: ShopifyCartItem[];
  item_count: number;
  total_price: number;
  currency: string;
}

interface ShopifyWindow extends Window {
  Shopify?: {
    shop?: string;
    theme?: { name: string };
    routes?: { root: string };
    onCartUpdate?: () => void;
  };
  refreshCart?: () => void;
}

/**
 * Check if the widget is running on a Shopify store domain.
 */
export function isOnShopify(): boolean {
  const hostname = window.location.hostname;
  const shopifyWindow = window as ShopifyWindow;
  
  const result = (
    hostname.includes('myshopify.com') ||
    shopifyWindow.Shopify?.routes?.root !== undefined ||
    shopifyWindow.Shopify?.shop !== undefined
  );
  
  console.log('[shopifyCartClient] isOnShopify check:', {
    hostname,
    hasShopify: !!shopifyWindow.Shopify,
    result
  });
  
  if (result) {
    console.log('[shopifyCartClient] ✅ Running on Shopify - will sync cart');
  } else {
    console.warn('[shopifyCartClient] ⚠️ NOT on Shopify domain, hostname:', hostname);
  }
  
  return result;
}

/**
 * Add item(s) to the Shopify cart.
 */
export async function addToCart(
  variantId: number | string,
  quantity: number = 1
): Promise<void> {
  const numericVariantId = typeof variantId === 'string' 
    ? parseInt(variantId, 10) 
    : variantId;

  const response = await fetch('/cart/add.js', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      items: [{ id: numericVariantId, quantity }],
    }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.message || `Failed to add item to cart: ${response.status}`);
  }

  refreshCartUI();
}

/**
 * Remove item from Shopify cart (sets quantity to 0).
 */
export async function removeFromCart(variantId: number | string): Promise<void> {
  const numericVariantId = typeof variantId === 'string' 
    ? parseInt(variantId, 10) 
    : variantId;

  const response = await fetch('/cart/update.js', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      updates: { [numericVariantId]: 0 },
    }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.message || `Failed to remove item from cart: ${response.status}`);
  }

  refreshCartUI();
}

/**
 * Update item quantity in Shopify cart.
 */
export async function updateQuantity(
  variantId: number | string,
  quantity: number
): Promise<void> {
  const numericVariantId = typeof variantId === 'string' 
    ? parseInt(variantId, 10) 
    : variantId;

  const response = await fetch('/cart/update.js', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      updates: { [numericVariantId]: quantity },
    }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.message || `Failed to update cart: ${response.status}`);
  }

  refreshCartUI();
}

/**
 * Clear the entire Shopify cart.
 */
export async function clearCart(): Promise<void> {
  const response = await fetch('/cart/clear.js', {
    method: 'POST',
  });

  if (!response.ok) {
    throw new Error(`Failed to clear cart: ${response.status}`);
  }

  refreshCartUI();
}

/**
 * Get the current Shopify cart state.
 */
export async function getCart(): Promise<ShopifyCart> {
  const response = await fetch('/cart.js');
  
  if (!response.ok) {
    throw new Error(`Failed to get cart: ${response.status}`);
  }
  
  return response.json();
}

/**
 * Trigger cart UI refresh across different Shopify themes.
 * 
 * Different themes use different methods to update the cart drawer.
 * This tries multiple approaches to maximize compatibility.
 */
function refreshCartUI(): void {
  const shopifyWindow = window as ShopifyWindow;

  // Method 1: Standard Shopify events (most themes)
  document.dispatchEvent(new CustomEvent('cart:refresh'));
  document.dispatchEvent(new CustomEvent('ajaxProduct:added'));
  document.dispatchEvent(new CustomEvent('product:added'));

  // Method 2: Dawn/Online Store 2.0 themes
  if (typeof shopifyWindow.Shopify?.onCartUpdate === 'function') {
    try {
      shopifyWindow.Shopify.onCartUpdate();
    } catch {
      // Ignore errors from theme-specific functions
    }
  }

  // Method 3: Common theme refresh functions
  if (typeof shopifyWindow.refreshCart === 'function') {
    try {
      shopifyWindow.refreshCart();
    } catch {
      // Ignore errors
    }
  }

  // Method 4: Fetch cart and dispatch event with data (fallback)
  fetch('/cart.js')
    .then((r) => r.json())
    .then((cart) => {
      document.dispatchEvent(
        new CustomEvent('cart:updated', { detail: cart })
      );
    })
    .catch(() => {
      // Ignore fetch errors
    });
}

export const shopifyCartClient = {
  isOnShopify,
  addToCart,
  removeFromCart,
  updateQuantity,
  clearCart,
  getCart,
  refreshCartUI,
};

// Expose to window for debugging
if (typeof window !== 'undefined') {
  (window as unknown as Record<string, unknown>).shopifyCartClient = shopifyCartClient;
}

export default shopifyCartClient;
