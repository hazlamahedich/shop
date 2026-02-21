import type {
  WidgetApiError,
  WidgetCart,
  WidgetCheckoutResult,
  WidgetConfig,
  WidgetMessage,
  WidgetSearchResult,
  WidgetSession,
  WidgetProduct,
} from '../types/widget';
import {
  WidgetCartSchema,
  WidgetCheckoutResultSchema,
  WidgetConfigSchema,
  WidgetMessageSchema,
  WidgetSearchResultSchema,
  WidgetSessionSchema,
} from '../schemas/widget';

let cachedApiBase: string | null = null;

function getApiBaseUrl(): string {
  if (cachedApiBase) return cachedApiBase;

  // Try to find the widget script by src
  const scripts = document.querySelectorAll('script[src*="widget.umd.js"]');
  for (const script of scripts) {
    if (script instanceof HTMLScriptElement && script.src) {
      try {
        const scriptUrl = new URL(script.src);
        cachedApiBase = `${scriptUrl.origin}/api/v1/widget`;
        return cachedApiBase;
      } catch {
        // Continue to next
      }
    }
  }

  // Fallback to relative path
  cachedApiBase = '/api/v1/widget';
  return cachedApiBase;
}

// Don't call at module load time - call lazily
const getWidgetApiBase = () => getApiBaseUrl();

export class WidgetApiException extends Error {
  constructor(
    public code: number,
    message: string
  ) {
    super(message);
    this.name = 'WidgetApiException';
  }
}

function parseApiError(data: unknown): WidgetApiError {
  if (typeof data === 'object' && data !== null && 'error_code' in data && 'message' in data) {
    return data as WidgetApiError;
  }
  return { error_code: 0, message: 'Unknown error' };
}

export class WidgetApiClient {
  private async delay(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  private isRetryableError(error: unknown): boolean {
    return error instanceof TypeError;
  }

  private async request<T>(endpoint: string, options: RequestInit = {}, retries = 2): Promise<T> {
    try {
      const response = await fetch(`${getWidgetApiBase()}${endpoint}`, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
      });

      if (!response.ok) {
        const data = await response.json().catch(() => null);
        const error = parseApiError(data);
        throw new WidgetApiException(error.error_code, error.message);
      }

      return response.json();
    } catch (error) {
      if (retries > 0 && this.isRetryableError(error)) {
        await this.delay(1000 * (3 - retries));
        return this.request<T>(endpoint, options, retries - 1);
      }
      throw error;
    }
  }

  async createSession(merchantId: string): Promise<WidgetSession> {
    // Backend returns { data: { sessionId, expiresAt } } at the top level
    const data = await this.request<{ data?: unknown; session?: unknown }>('/session', {
      method: 'POST',
      body: JSON.stringify({ merchant_id: merchantId }),
    });
    const raw = data.data ?? data.session ?? data;
    const parsed = WidgetSessionSchema.safeParse(raw);
    if (!parsed.success) {
      throw new WidgetApiException(0, 'Invalid session response');
    }
    return {
      sessionId: parsed.data.sessionId ?? parsed.data.session_id ?? '',
      merchantId: parsed.data.merchant_id ?? merchantId,
      expiresAt: parsed.data.expiresAt ?? parsed.data.expires_at ?? '',
      createdAt: parsed.data.created_at ?? new Date().toISOString(),
      lastActivityAt: parsed.data.last_activity_at ?? new Date().toISOString(),
    };
  }

  async getSession(sessionId: string): Promise<WidgetSession | null> {
    try {
      const data = await this.request<{ data?: unknown; session?: unknown }>(
        `/session/${sessionId}`
      );
      const raw = data.data ?? data.session ?? data;
      const parsed = WidgetSessionSchema.safeParse(raw);
      if (!parsed.success) {
        return null;
      }
      return {
        sessionId: parsed.data.sessionId ?? parsed.data.session_id ?? sessionId,
        merchantId:
          parsed.data.merchant_id ??
          String((parsed.data as Record<string, unknown>).merchantId ?? ''),
        expiresAt: parsed.data.expiresAt ?? parsed.data.expires_at ?? '',
        createdAt:
          ((parsed.data as Record<string, unknown>).createdAt as string) ??
          parsed.data.created_at ??
          new Date().toISOString(),
        lastActivityAt:
          ((parsed.data as Record<string, unknown>).lastActivityAt as string) ??
          parsed.data.last_activity_at ??
          new Date().toISOString(),
      };
    } catch {
      return null;
    }
  }

  async endSession(sessionId: string): Promise<void> {
    await this.request(`/session/${sessionId}`, { method: 'DELETE' });
  }

  async sendMessage(sessionId: string, message: string): Promise<WidgetMessage> {
    const data = await this.request<{ data: unknown }>('/message', {
      method: 'POST',
      body: JSON.stringify({ session_id: sessionId, message: message }),
    });
    const parsed = WidgetMessageSchema.safeParse(data.data);
    if (!parsed.success) {
      throw new WidgetApiException(0, 'Invalid message response');
    }
    return {
      messageId: (parsed.data.messageId || parsed.data.message_id) ?? '',
      content: parsed.data.content,
      sender: parsed.data.sender,
      createdAt: (parsed.data.createdAt || parsed.data.created_at) ?? '',
      products: parsed.data.products?.map((p: Record<string, unknown>) => ({
        id: (p.id || p.product_id) as string,
        variantId: (p.variantId || p.variant_id) as string,
        title: p.title as string,
        description: p.description as string | undefined,
        price: p.price as number,
        imageUrl: (p.imageUrl || p.image_url) as string | undefined,
        available: p.available as boolean,
        productType: (p.productType || p.product_type) as string | undefined,
      })),
      cart: parsed.data.cart
        ? {
            items: (
              (parsed.data.cart as Record<string, unknown>).items as Record<string, unknown>[]
            ).map((item: Record<string, unknown>) => ({
              variantId: item.variant_id as string,
              title: item.title as string,
              price: item.price as number,
              quantity: item.quantity as number,
            })),
            itemCount: (parsed.data.cart as Record<string, unknown>).item_count as number,
            total: (parsed.data.cart as Record<string, unknown>).total as number,
          }
        : undefined,
      checkoutUrl: (parsed.data.checkoutUrl || parsed.data.checkout_url) ?? undefined,
      intent: parsed.data.intent ?? undefined,
      confidence: parsed.data.confidence ?? undefined,
    };
  }

  async getConfig(merchantId: string): Promise<WidgetConfig> {
    const data = await this.request<{ data: unknown }>(`/config/${merchantId}`);
    const parsed = WidgetConfigSchema.safeParse(data.data);
    if (!parsed.success) {
      throw new WidgetApiException(0, 'Invalid config response');
    }
    return {
      enabled: parsed.data.enabled,
      botName: parsed.data.botName,
      welcomeMessage: parsed.data.welcomeMessage,
      theme: parsed.data.theme,
      allowedDomains: parsed.data.allowedDomains,
    };
  }

  async searchProducts(sessionId: string, query: string): Promise<WidgetSearchResult> {
    const data = await this.request<{ data: unknown }>('/search', {
      method: 'POST',
      body: JSON.stringify({ session_id: sessionId, query }),
    });
    const parsed = WidgetSearchResultSchema.safeParse(data.data);
    if (!parsed.success) {
      throw new WidgetApiException(0, 'Invalid search response');
    }
    return {
      products: parsed.data.products.map((p) => ({
        id: p.id,
        variantId: p.variant_id,
        title: p.title,
        description: p.description,
        price: p.price,
        imageUrl: p.image_url,
        available: p.available,
        productType: p.product_type,
      })),
      total: parsed.data.total,
      query: parsed.data.query,
    };
  }

  async getCart(sessionId: string): Promise<WidgetCart> {
    const data = await this.request<{ data: unknown }>(`/cart?session_id=${sessionId}`);
    const parsed = WidgetCartSchema.safeParse(data.data);
    if (!parsed.success) {
      throw new WidgetApiException(0, 'Invalid cart response');
    }
    return {
      items: parsed.data.items.map((item) => ({
        variantId: item.variant_id,
        title: item.title,
        price: item.price,
        quantity: item.quantity,
      })),
      itemCount: parsed.data.item_count,
      total: parsed.data.total,
    };
  }

  async addToCart(
    sessionId: string,
    product: WidgetProduct,
    quantity: number = 1
  ): Promise<WidgetCart> {
    const data = await this.request<{ data: unknown }>('/cart', {
      method: 'POST',
      body: JSON.stringify({
        session_id: sessionId,
        variant_id: product.variantId,
        quantity,
        title: product.title,
        price: product.price,
        image_url: product.imageUrl,
      }),
    });
    const parsed = WidgetCartSchema.safeParse(data.data);
    if (!parsed.success) {
      throw new WidgetApiException(0, 'Invalid cart response');
    }
    return {
      items: parsed.data.items.map((item) => ({
        variantId: item.variant_id,
        title: item.title,
        price: item.price,
        quantity: item.quantity,
      })),
      itemCount: parsed.data.item_count,
      total: parsed.data.total,
    };
  }

  async removeFromCart(sessionId: string, variantId: string): Promise<WidgetCart> {
    const data = await this.request<{ data: unknown }>(
      `/cart/${variantId}?session_id=${sessionId}`,
      {
        method: 'DELETE',
      }
    );
    const parsed = WidgetCartSchema.safeParse(data.data);
    if (!parsed.success) {
      throw new WidgetApiException(0, 'Invalid cart response');
    }
    return {
      items: parsed.data.items.map((item) => ({
        variantId: item.variant_id,
        title: item.title,
        price: item.price,
        quantity: item.quantity,
      })),
      itemCount: parsed.data.item_count,
      total: parsed.data.total,
    };
  }

  async updateQuantity(
    sessionId: string,
    variantId: string,
    quantity: number
  ): Promise<WidgetCart> {
    const data = await this.request<{ data: unknown }>(`/cart/${variantId}`, {
      method: 'PATCH',
      body: JSON.stringify({ session_id: sessionId, quantity }),
    });
    const parsed = WidgetCartSchema.safeParse(data.data);
    if (!parsed.success) {
      throw new WidgetApiException(0, 'Invalid cart response');
    }
    return {
      items: parsed.data.items.map((item) => ({
        variantId: item.variant_id,
        title: item.title,
        price: item.price,
        quantity: item.quantity,
      })),
      itemCount: parsed.data.item_count,
      total: parsed.data.total,
    };
  }

  async checkout(sessionId: string): Promise<WidgetCheckoutResult> {
    const data = await this.request<{ data: unknown }>('/checkout', {
      method: 'POST',
      body: JSON.stringify({ session_id: sessionId }),
    });
    const parsed = WidgetCheckoutResultSchema.safeParse(data.data);
    if (!parsed.success) {
      throw new WidgetApiException(0, 'Invalid checkout response');
    }
    return {
      checkoutUrl: parsed.data.checkout_url,
      message: parsed.data.message,
    };
  }
}

export const widgetClient = new WidgetApiClient();
