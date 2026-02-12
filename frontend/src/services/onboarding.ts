/** Onboarding API service for prerequisite state management.

Story 1.2: Handles localStorage to PostgreSQL migration with sync endpoints.

Provides functions to:
- Get prerequisite state from backend
- Save/update prerequisite state to backend
- Sync localStorage state with backend
- Delete prerequisite state

All functions use localStorage as fallback for offline scenarios.
*/

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "";

/** Prerequisite state matching backend PrerequisiteStateResponse schema. */
export interface PrerequisiteStateResponse {
  id: number;
  merchantId: number;
  hasCloudAccount: boolean;
  hasFacebookAccount: boolean;
  hasShopifyAccess: boolean;
  hasLlmProviderChoice: boolean;
  isComplete: boolean;
  completedAt: string | null;
  createdAt: string;
  updatedAt: string;
}

/** Request payload for creating/updating prerequisite state. */
export interface PrerequisiteStateCreate {
  hasCloudAccount: boolean;
  hasFacebookAccount: boolean;
  hasShopifyAccess: boolean;
  hasLlmProviderChoice: boolean;
}

/** Sync request payload matching localStorage state. */
export interface PrerequisiteSyncRequest {
  cloudAccount: boolean;
  facebookAccount: boolean;
  shopifyAccess: boolean;
  llmProviderChoice: boolean;
  updatedAt?: string;
}

/** API response envelope structure. */
interface ApiEnvelope<T> {
  data: T;
  meta: {
    requestId: string;
    timestamp: string;
  };
}

/** API error response structure. */
interface ApiError {
  error_code: number;
  message: string;
  details?: {
    missing?: string[];
  };
}

/**
 * Get prerequisite state from backend for a merchant.
 *
 * @param merchantId - Merchant ID (defaults to 1 until auth is implemented)
 * @returns Prerequisite state or null if not found
 */
export async function getPrerequisiteState(
  merchantId: number = 1,
): Promise<PrerequisiteStateResponse | null> {
  try {
    const response = await fetch(
      `${API_BASE_URL}/api/onboarding/prerequisites?merchant_id=${merchantId}`,
      {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
      },
    );

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    const envelope: ApiEnvelope<PrerequisiteStateResponse | null> = await response.json();
    return envelope.data;
  } catch (error) {
    console.warn("Failed to fetch prerequisite state from backend:", error);
    return null;
  }
}

/**
 * Save or update prerequisite state to backend.
 *
 * @param state - Prerequisite state to save
 * @param merchantId - Merchant ID (defaults to 1 until auth is implemented)
 * @returns Saved prerequisite state or null on error
 */
export async function savePrerequisiteState(
  state: PrerequisiteStateCreate,
  merchantId: number = 1,
): Promise<PrerequisiteStateResponse | null> {
  try {
    const response = await fetch(
      `${API_BASE_URL}/api/onboarding/prerequisites?merchant_id=${merchantId}`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(state),
      },
    );

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    const envelope: ApiEnvelope<PrerequisiteStateResponse> = await response.json();
    return envelope.data;
  } catch (error) {
    console.warn("Failed to save prerequisite state to backend:", error);
    return null;
  }
}

/**
 * Sync localStorage state to backend (Story 1.2 migration endpoint).
 *
 * @param state - LocalStorage state to sync
 * @param merchantId - Merchant ID (defaults to 1 until auth is implemented)
 * @returns Synced prerequisite state or null on error
 */
export async function syncPrerequisiteState(
  state: PrerequisiteSyncRequest,
  merchantId: number = 1,
): Promise<PrerequisiteStateResponse | null> {
  try {
    const response = await fetch(
      `${API_BASE_URL}/api/onboarding/prerequisites/sync?merchant_id=${merchantId}`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(state),
      },
    );

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    const envelope: ApiEnvelope<PrerequisiteStateResponse> = await response.json();
    return envelope.data;
  } catch (error) {
    console.warn("Failed to sync prerequisite state to backend:", error);
    return null;
  }
}

/**
 * Delete prerequisite state from backend.
 *
 * @param merchantId - Merchant ID (defaults to 1 until auth is implemented)
 * @returns True if deleted, false on error
 */
export async function deletePrerequisiteState(
  merchantId: number = 1,
): Promise<boolean> {
  try {
    const response = await fetch(
      `${API_BASE_URL}/api/onboarding/prerequisites?merchant_id=${merchantId}`,
      {
        method: "DELETE",
        headers: {
          "Content-Type": "application/json",
        },
      },
    );

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    const envelope: ApiEnvelope<{ deleted: boolean }> = await response.json();
    return envelope.data.deleted;
  } catch (error) {
    console.warn("Failed to delete prerequisite state from backend:", error);
    return false;
  }
}

/**
 * Convert frontend PrerequisiteState to backend PrerequisiteStateCreate format.
 *
 * @param state - Frontend prerequisite state
 * @returns Backend-compatible state object
 */
export function toBackendFormat(state: {
  cloudAccount: boolean;
  facebookAccount: boolean;
  shopifyAccess: boolean;
  llmProviderChoice: boolean;
}): PrerequisiteStateCreate {
  return {
    hasCloudAccount: state.cloudAccount,
    hasFacebookAccount: state.facebookAccount,
    hasShopifyAccess: state.shopifyAccess,
    hasLlmProviderChoice: state.llmProviderChoice,
  };
}

/**
 * Convert backend PrerequisiteStateResponse to frontend PrerequisiteState format.
 *
 * @param state - Backend prerequisite state
 * @returns Frontend-compatible state object
 */
export function fromBackendFormat(state: PrerequisiteStateResponse): {
  cloudAccount: boolean;
  facebookAccount: boolean;
  shopifyAccess: boolean;
  llmProviderChoice: boolean;
  updatedAt: string;
} {
  return {
    cloudAccount: state.hasCloudAccount,
    facebookAccount: state.hasFacebookAccount,
    shopifyAccess: state.hasShopifyAccess,
    llmProviderChoice: state.hasLlmProviderChoice,
    updatedAt: state.updatedAt,
  };
}
