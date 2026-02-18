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
});

export const WidgetApiErrorSchema = z.object({
  error_code: z.number(),
  message: z.string(),
});
