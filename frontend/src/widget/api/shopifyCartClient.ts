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

let configuredShopDomain: string | null = null;

/**
 * Register the merchant's shop domain from the widget config.
 * Call this once after getConfig() returns so isOnShopify() can also
 * match stores that use a custom domain and don't expose window.Shopify.
 */
export function setShopDomain(domain: string | null | undefined): void {
  configuredShopDomain = domain ?? null;
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

  // Match when the current hostname equals the merchant's configured shop domain.
  // This covers custom-domain stores where window.Shopify is not defined.
  if (configuredShopDomain) {
    const domain = configuredShopDomain.toLowerCase().replace(/^https?:\/\//, '');
    if (hostname === domain || hostname.endsWith('.' + domain)) {
      return true;
    }
  }

  return (
    hostname.includes('myshopify.com') ||
    shopifyWindow.Shopify?.routes?.root !== undefined ||
    shopifyWindow.Shopify?.shop !== undefined
  );
}

function parseVariantId(variantId: number | string): number {
  if (!variantId) {
    throw new Error('Variant ID is required');
  }

  const numericId = typeof variantId === 'string' 
    ? parseInt(variantId.replace(/\D/g, ''), 10) 
    : variantId;

  if (isNaN(numericId)) {
    throw new Error(`Invalid variant ID format: ${variantId}`);
  }

  return numericId;
}

/**
 * Add item(s) to the Shopify cart.
 */
export async function addToCart(
  variantId: number | string,
  quantity: number = 1
): Promise<void> {
  const numericVariantId = parseVariantId(variantId);

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
  const numericVariantId = parseVariantId(variantId);

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
  const numericVariantId = parseVariantId(variantId);

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
 * Shopify Section Rendering API - Re-render cart sections without page reload.
 * Only fetches sections that commonly exist across themes to avoid 404 errors.
 */
async function refreshCartSections(): Promise<void> {
  const cartSections = [
    'cart-icon-bubble',
    'cart-drawer',
  ];

  const sectionSelectors: Record<string, string[]> = {
    'cart-icon-bubble': ['#cart-icon-bubble', '.cart-count-bubble', '[data-cart-count]'],
    'cart-drawer': ['#cart-drawer', '.cart-drawer', '[data-cart-drawer]'],
  };

  const promises = cartSections.map(async (sectionId) => {
    try {
      const response = await fetch(`/?section_id=${sectionId}`, {
        method: 'GET',
        credentials: 'same-origin',
      });

      // Silently skip sections that don't exist (404) or other errors
      if (!response.ok) return;

      const html = await response.text();
      const selectors = sectionSelectors[sectionId] || [`#${sectionId}`];

      for (const selector of selectors) {
        const elements = document.querySelectorAll(selector);
        elements.forEach((element) => {
          if (element && html) {
            element.innerHTML = html;
          }
        });
      }
    } catch {
      // Section fetch failed, continue with other refresh methods
    }
  });

  await Promise.allSettled(promises);
}

let cartChannel: BroadcastChannel | null = null;

function getCartChannel(): BroadcastChannel {
  if (!cartChannel) {
    cartChannel = new BroadcastChannel('shopify-cart-sync');
  }
  return cartChannel;
}

/**
 * Trigger cart UI refresh across different Shopify themes.
 * 
 * Tries multiple approaches in order of reliability:
 * 1. Section Rendering API (most reliable for modern themes)
 * 2. Standard Shopify events
 * 3. Theme-specific refresh functions
 * 4. BroadcastChannel for multi-tab sync
 */
function refreshCartUI(): void {
  const shopifyWindow = window as ShopifyWindow;

  refreshCartSections().catch(() => {});

  document.dispatchEvent(new CustomEvent('cart:refresh'));
  document.dispatchEvent(new CustomEvent('ajaxProduct:added'));
  document.dispatchEvent(new CustomEvent('product:added'));

  if (typeof shopifyWindow.Shopify?.onCartUpdate === 'function') {
    try {
      shopifyWindow.Shopify.onCartUpdate();
    } catch {
      // Ignore errors from theme-specific functions
    }
  }

  if (typeof shopifyWindow.refreshCart === 'function') {
    try {
      shopifyWindow.refreshCart();
    } catch {
      // Ignore errors
    }
  }

  fetch('/cart.js')
    .then((r) => r.json())
    .then((cart) => {
      document.dispatchEvent(
        new CustomEvent('cart:updated', { detail: cart })
      );

      try {
        getCartChannel().postMessage({ type: 'CART_UPDATED', cart });
      } catch {
        // BroadcastChannel not supported
      }
    })
    .catch(() => {
      // Ignore fetch errors
    });
}

export function subscribeToCartUpdates(callback: (cart: ShopifyCart) => void): () => void {
  try {
    const channel = getCartChannel();
    const handler = (event: MessageEvent) => {
      if (event.data?.type === 'CART_UPDATED' && event.data?.cart) {
        callback(event.data.cart);
      }
    };
    channel.addEventListener('message', handler);
    return () => channel.removeEventListener('message', handler);
  } catch {
    return () => {};
  }
}

export function subscribeToCartEvents(callback: (cart: ShopifyCart) => void): () => void {
  const handler = (event: Event) => {
    const customEvent = event as CustomEvent<ShopifyCart>;
    if (customEvent.detail) {
      callback(customEvent.detail);
    }
  };
  document.addEventListener('cart:updated', handler);
  return () => document.removeEventListener('cart:updated', handler);
}

export const shopifyCartClient = {
  isOnShopify,
  setShopDomain,
  addToCart,
  removeFromCart,
  updateQuantity,
  clearCart,
  getCart,
  refreshCartUI,
  subscribeToCartUpdates,
  subscribeToCartEvents,
};

export default shopifyCartClient;
