import type { WidgetApiError, WidgetConfig, WidgetMessage, WidgetSession } from '../types/widget';
import {
  WidgetConfigSchema,
  WidgetMessageSchema,
  WidgetSessionSchema,
} from '../schemas/widget';

const WIDGET_API_BASE = '/api/v1/widget';

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

  private async request<T>(
    endpoint: string,
    options: RequestInit = {},
    retries = 2
  ): Promise<T> {
    try {
      const response = await fetch(`${WIDGET_API_BASE}${endpoint}`, {
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
    const data = await this.request<{ session: unknown }>('/session', {
      method: 'POST',
      body: JSON.stringify({ merchant_id: merchantId }),
    });
    const parsed = WidgetSessionSchema.safeParse(data.session);
    if (!parsed.success) {
      throw new WidgetApiException(0, 'Invalid session response');
    }
    return {
      sessionId: parsed.data.session_id,
      merchantId: parsed.data.merchant_id,
      expiresAt: parsed.data.expires_at,
      createdAt: parsed.data.created_at,
      lastActivityAt: parsed.data.last_activity_at,
    };
  }

  async getSession(sessionId: string): Promise<WidgetSession | null> {
    try {
      const data = await this.request<{ session: unknown }>(`/session/${sessionId}`);
      const parsed = WidgetSessionSchema.safeParse(data.session);
      if (!parsed.success) {
        return null;
      }
      return {
        sessionId: parsed.data.session_id,
        merchantId: parsed.data.merchant_id,
        expiresAt: parsed.data.expires_at,
        createdAt: parsed.data.created_at,
        lastActivityAt: parsed.data.last_activity_at,
      };
    } catch {
      return null;
    }
  }

  async endSession(sessionId: string): Promise<void> {
    await this.request(`/session/${sessionId}`, { method: 'DELETE' });
  }

  async sendMessage(sessionId: string, message: string): Promise<WidgetMessage> {
    const data = await this.request<{ message: unknown }>('/message', {
      method: 'POST',
      body: JSON.stringify({ session_id: sessionId, content: message }),
    });
    const parsed = WidgetMessageSchema.safeParse(data.message);
    if (!parsed.success) {
      throw new WidgetApiException(0, 'Invalid message response');
    }
    return {
      messageId: parsed.data.message_id,
      content: parsed.data.content,
      sender: parsed.data.sender,
      createdAt: parsed.data.created_at,
    };
  }

  async getConfig(merchantId: string): Promise<WidgetConfig> {
    const data = await this.request<{ config: unknown }>(`/config/${merchantId}`);
    const parsed = WidgetConfigSchema.safeParse(data.config);
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
}

export const widgetClient = new WidgetApiClient();
