import { z } from 'zod';

export const WidgetThemeSchema = z.object({
  primaryColor: z.string(),
  backgroundColor: z.string(),
  textColor: z.string(),
  botBubbleColor: z.string(),
  userBubbleColor: z.string(),
  position: z.enum(['bottom-right', 'bottom-left']),
  borderRadius: z.number().min(0).max(24),
  width: z.number().positive(),
  height: z.number().positive(),
  fontFamily: z.string(),
  fontSize: z.number().positive(),
});

export const WidgetConfigSchema = z.object({
  enabled: z.boolean(),
  botName: z.string(),
  bot_name: z.string().optional(),
  welcomeMessage: z.string(),
  welcome_message: z.string().optional(),
  theme: WidgetThemeSchema,
  allowedDomains: z.array(z.string()).optional().default([]),
  shopDomain: z.string().nullable().optional(),
  shop_domain: z.string().nullable().optional(),
  personality: z.enum(['friendly', 'professional', 'enthusiastic']).nullable().optional(),
}).passthrough().transform((data) => ({
  enabled: data.enabled,
  botName: data.botName || data.bot_name || 'Assistant',
  welcomeMessage: data.welcomeMessage || data.welcome_message || '',
  theme: data.theme,
  allowedDomains: data.allowedDomains || [],
  shopDomain: data.shopDomain || data.shop_domain || undefined,
  personality: data.personality || undefined,
}));

export const WidgetSessionSchema = z
  .object({
    session_id: z.string().optional(),
    sessionId: z.string().optional(),
    merchant_id: z.string().optional(),
    expires_at: z.string().optional(),
    expiresAt: z.string().optional(),
    created_at: z.string().optional(),
    last_activity_at: z.string().optional(),
  })
  .passthrough()
  .refine((data) => data.session_id || data.sessionId, {
    message: 'Either session_id or sessionId must be present',
  });

export const WidgetMessageSchema = z.object({
  messageId: z.string().optional(),
  message_id: z.string().optional(),
  content: z.string(),
  sender: z.enum(['user', 'bot', 'merchant']),
  createdAt: z.string().optional(),
  created_at: z.string().optional(),
  products: z.array(z.any()).nullable().optional(),
  cart: z.any().nullable().optional(),
  checkoutUrl: z.string().nullable().optional(),
  checkout_url: z.string().nullable().optional(),
  intent: z.string().nullable().optional(),
  confidence: z.number().nullable().optional(),
});

export const WidgetApiErrorSchema = z.object({
  error_code: z.number(),
  message: z.string(),
});

export const WidgetProductSchema = z.object({
  id: z.string(),
  variant_id: z.string(),
  title: z.string(),
  description: z.string().optional(),
  price: z.number(),
  image_url: z.string().optional(),
  available: z.boolean(),
  product_type: z.string().optional(),
});

export const WidgetCartItemSchema = z.object({
  variant_id: z.string().optional(),
  variantId: z.string().optional(),
  title: z.string(),
  price: z.number(),
  quantity: z.number(),
}).passthrough();

export const WidgetCartSchema = z.object({
  items: z.array(WidgetCartItemSchema),
  item_count: z.number().optional(),
  itemCount: z.number().optional(),
  total: z.number().optional(),
  subtotal: z.number().optional(),
}).passthrough();

export const WidgetSearchResultSchema = z.object({
  products: z.array(WidgetProductSchema),
  total: z.number(),
  query: z.string(),
});

export const WidgetCheckoutResultSchema = z.object({
  checkout_url: z.string().optional(),
  checkoutUrl: z.string().optional(),
  message: z.string().optional(),
  cartTotal: z.number().optional(),
  currency: z.string().optional(),
  itemCount: z.number().optional(),
});

export const WidgetProductDetailSchema = z.object({
  id: z.string(),
  title: z.string(),
  description: z.string().nullable().optional(),
  image_url: z.string().nullable().optional(),
  imageUrl: z.string().nullable().optional(),
  price: z.number(),
  available: z.boolean(),
  inventory_quantity: z.number().nullable().optional(),
  inventoryQuantity: z.number().nullable().optional(),
  product_type: z.string().nullable().optional(),
  productType: z.string().nullable().optional(),
  vendor: z.string().nullable().optional(),
  variant_id: z.string().nullable().optional(),
  variantId: z.string().nullable().optional(),
}).passthrough();
