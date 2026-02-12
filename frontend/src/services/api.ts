/**
 * Centralized API Client
 *
 * Handles:
 * - Base URL configuration
 * - Authentication (JWT)
 * - CSRF protection (fetching and attaching tokens)
 * - Standard error handling
 */

const API_BASE_URL = ''; // Relative path for proxy

interface ApiEnvelope<T> {
  data: T;
  meta: any;
}

class ApiClient {
  private csrfToken: string | null = null;
  private tokenFetchPromise: Promise<string> | null = null;

  private async fetchCsrfToken(): Promise<string> {
    if (this.tokenFetchPromise) {
      return this.tokenFetchPromise;
    }

    this.tokenFetchPromise = (async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/v1/csrf-token`);
        if (!response.ok) {
          throw new Error(`Failed to fetch CSRF token: ${response.status}`);
        }
        const data = await response.json();
        this.csrfToken = data.csrf_token;
        return data.csrf_token;
      } catch (error) {
        console.error('Error fetching CSRF token:', error);
        throw error;
      } finally {
        this.tokenFetchPromise = null;
      }
    })();

    return this.tokenFetchPromise;
  }

  async request<T>(endpoint: string, options: RequestInit = {}): Promise<ApiEnvelope<T>> {
    const url = `${API_BASE_URL}${endpoint}`;
    const headers = new Headers(options.headers || {});

    // Disable caching by default for API requests
    if (!options.cache) {
      options.cache = 'no-store';
    }

    if (!headers.has('Content-Type') && !(options.body instanceof FormData)) {
      headers.set('Content-Type', 'application/json');
    }

    // Add CSRF Token for state-changing methods
    const method = (options.method || 'GET').toUpperCase();
    if (['POST', 'PUT', 'PATCH', 'DELETE'].includes(method)) {
      if (!this.csrfToken) {
        try {
          await this.fetchCsrfToken();
        } catch (e) {
          console.warn('Proceeding without CSRF token due to fetch error', e);
        }
      }
      if (this.csrfToken) {
        headers.set('X-CSRF-Token', this.csrfToken);
      }
    }

    const config: RequestInit = {
      credentials: 'include', // Ensure cookies are sent (Story 1.8)
      ...options,
      headers,
    };

    let response = await fetch(url, config);

    // Handle 403 CSRF Retry
    if (response.status === 403) {
      // Clone response to read body
      const errorBody = await response
        .clone()
        .json()
        .catch(() => ({}));

      // Check if it's a CSRF error (assuming error_code 2000 based on previous logs)
      if (errorBody.error_code === 2000) {
        console.log('CSRF token invalid, refreshing...');
        this.csrfToken = null;
        try {
          const newToken = await this.fetchCsrfToken();
          headers.set('X-CSRF-Token', newToken);
          config.headers = headers;
          response = await fetch(url, config);
        } catch (e) {
          console.error('Failed to refresh CSRF token, throwing original error');
        }
      }
    }

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      // Construct Error object
      const message =
        errorData.message || errorData.detail?.message || `API Error ${response.status}`;
      const error = new Error(message);
      (error as any).status = response.status;
      (error as any).code = errorData.error_code;
      (error as any).details = errorData.details;
      throw error;
    }

    // Response.json() returns a Promise - await it to get the actual data
    const jsonResult = await response.json();
    return jsonResult;
  }

  async get<T>(endpoint: string, options: RequestInit = {}) {
    return this.request<T>(endpoint, { ...options, method: 'GET' });
  }

  async post<T>(endpoint: string, body: any, options: RequestInit = {}) {
    return this.request<T>(endpoint, {
      ...options,
      method: 'POST',
      body: JSON.stringify(body),
    });
  }

  async put<T>(endpoint: string, body: any, options: RequestInit = {}) {
    return this.request<T>(endpoint, {
      ...options,
      method: 'PUT',
      body: JSON.stringify(body),
    });
  }

  async patch<T>(endpoint: string, body: any, options: RequestInit = {}) {
    return this.request<T>(endpoint, {
      ...options,
      method: 'PATCH',
      body: JSON.stringify(body),
    });
  }

  async delete<T>(endpoint: string, options: RequestInit = {}) {
    return this.request<T>(endpoint, { ...options, method: 'DELETE' });
  }
}

export const apiClient = new ApiClient();
