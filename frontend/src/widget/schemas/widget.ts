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
  welcomeMessage: z.string(),
  theme: WidgetThemeSchema,
  allowedDomains: z.array(z.string()),
});

export const WidgetSessionSchema = z.object({
  session_id: z.string().uuid(),
  merchant_id: z.string(),
  expires_at: z.string(),
  created_at: z.string(),
  last_activity_at: z.string(),
});

export const WidgetMessageSchema = z.object({
  message_id: z.string().uuid(),
  content: z.string(),
  sender: z.enum(['user', 'bot']),
  created_at: z.string(),
  products: z.array(z.any()).optional(),
  cart: z.any().optional(),
  checkout_url: z.string().optional(),
  intent: z.string().optional(),
  confidence: z.number().optional(),
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
  variant_id: z.string(),
  title: z.string(),
  price: z.number(),
  quantity: z.number(),
});

export const WidgetCartSchema = z.object({
  items: z.array(WidgetCartItemSchema),
  item_count: z.number(),
  total: z.number(),
});

export const WidgetSearchResultSchema = z.object({
  products: z.array(WidgetProductSchema),
  total: z.number(),
  query: z.string(),
});

export const WidgetCheckoutResultSchema = z.object({
  checkout_url: z.string(),
  message: z.string(),
});
