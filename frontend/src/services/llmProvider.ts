/** LLM Provider API service.
 *
 * Story 3.4: LLM Provider Switching
 *
 * Provides API client functions for provider switching operations.
 */

/** Provider pricing information */
interface ProviderPricing {
  inputCost: number;
  outputCost: number;
  currency: string;
}

/** LLM Provider information */
interface Provider {
  id: string;
  name: string;
  description: string;
  pricing: ProviderPricing;
  models: string[];
  features: string[];
  isActive?: boolean;
  estimatedMonthlyCost?: number;
}

/** Current provider information */
interface CurrentProvider {
  id: string;
  name: string;
  description: string;
  model: string;
  status: string;
  configuredAt: string;
  totalTokensUsed: number;
  totalCostUsd: number;
}

/** API response envelope */
interface ApiEnvelope<T> {
  data: T;
  meta: {
    requestId: string;
    timestamp: string;
  };
}

/** Providers list response */
export interface ProvidersResponse {
  currentProvider: CurrentProvider;
  providers: Provider[];
}

/** Switch provider configuration */
export interface SwitchProviderConfig {
  providerId: string;
  apiKey?: string;
  serverUrl?: string;
  model?: string;
}

/** Switch provider response */
export interface SwitchProviderResponse {
  success: boolean;
  provider: {
    id: string;
    name: string;
    model: string;
  };
  switchedAt: string;
  previousProvider?: string;
}

/** Validation configuration */
export interface ValidateProviderConfig {
  providerId: string;
  apiKey?: string;
  serverUrl?: string;
  model?: string;
}

/** Validation response */
export interface ValidateProviderResponse {
  valid: boolean;
  provider: {
    id: string;
    name: string;
    testResponse: string;
    latencyMs?: number;
  };
  validatedAt: string;
}

/** Get JWT token from localStorage */
function getAuthToken(): string | null {
  return localStorage.getItem('auth_token');
}

/** Make API request with authentication */
async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<ApiEnvelope<T>> {
  const token = getAuthToken();

  const response = await fetch(endpoint, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(token && { Authorization: `Bearer ${token}` }),
      ...options.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({
      message: 'Unknown error occurred',
    }));

    // Handle structured error responses from backend
    if (error.error_code || error.details) {
      throw new Error(
        error.details?.message || error.message || 'API request failed'
      );
    }

    throw new Error(error.message || `HTTP ${response.status}`);
  }

  return response.json();
}

/** Get list of available providers with current provider indicator */
export async function getProviders(): Promise<ApiEnvelope<ProvidersResponse>> {
  return apiRequest<ProvidersResponse>('/api/llm/providers-list');
}

/** Switch to a new provider */
export async function switchProvider(
  config: SwitchProviderConfig
): Promise<ApiEnvelope<SwitchProviderResponse>> {
  return apiRequest<SwitchProviderResponse>('/api/llm/switch-provider', {
    method: 'POST',
    body: JSON.stringify({
      providerId: config.providerId,
      apiKey: config.apiKey,
      serverUrl: config.serverUrl,
      model: config.model,
    }),
  });
}

/** Validate provider configuration without switching */
export async function validateProviderConfig(
  config: ValidateProviderConfig
): Promise<ApiEnvelope<ValidateProviderResponse>> {
  return apiRequest<ValidateProviderResponse>('/api/llm/validate-provider', {
    method: 'POST',
    body: JSON.stringify({
      providerId: config.providerId,
      apiKey: config.apiKey,
      serverUrl: config.serverUrl,
      model: config.model,
    }),
  });
}
