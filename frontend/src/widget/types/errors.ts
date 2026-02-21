export enum ErrorSeverity {
  INFO = 'info',
  WARNING = 'warning',
  ERROR = 'error',
  CRITICAL = 'critical',
}

export enum ErrorType {
  NETWORK = 'network',
  TIMEOUT = 'timeout',
  RATE_LIMIT = 'rate_limit',
  SERVER = 'server',
  AUTH = 'auth',
  NOT_FOUND = 'not_found',
  VALIDATION = 'validation',
  CART = 'cart',
  CHECKOUT = 'checkout',
  SESSION = 'session',
  CONFIG = 'config',
  UNKNOWN = 'unknown',
}

export enum ErrorCode {
  NETWORK_ERROR = 10001,
  TIMEOUT = 10002,
  MALFORMED_RESPONSE = 10003,
  
  RATE_LIMITED = 14029,
  UNAUTHORIZED = 14001,
  FORBIDDEN = 14003,
  NOT_FOUND = 14004,
  
  SERVER_ERROR = 15000,
  BAD_GATEWAY = 15002,
  SERVICE_UNAVAILABLE = 15003,
  GATEWAY_TIMEOUT = 15004,
  
  CART_EMPTY = 12020,
  CART_ITEM_NOT_FOUND = 12021,
  CART_QUANTITY_INVALID = 12022,
  
  CHECKOUT_FAILED = 8009,
  CHECKOUT_NO_SHOPIFY = 8010,
  
  SESSION_EXPIRED = 8011,
  SESSION_INVALID = 8012,
  
  CONFIG_LOAD_FAILED = 8020,
}

export interface WidgetError {
  id: string;
  type: ErrorType;
  code: ErrorCode | number;
  severity: ErrorSeverity;
  message: string;
  detail?: string;
  retryable: boolean;
  retryAfter?: number;
  retryAction?: string;
  fallbackUrl?: string;
  timestamp: number;
  dismissed: boolean;
}

export interface ErrorAction {
  label: string;
  handler: () => void;
  primary?: boolean;
}

export const ERROR_MESSAGES: Record<ErrorType, { title: string; defaultAction: string }> = {
  [ErrorType.NETWORK]: {
    title: 'Connection Error',
    defaultAction: 'Please check your internet connection and try again.',
  },
  [ErrorType.TIMEOUT]: {
    title: 'Request Timed Out',
    defaultAction: 'The request took too long. Please try again.',
  },
  [ErrorType.RATE_LIMIT]: {
    title: 'Too Many Requests',
    defaultAction: 'Please wait a moment and try again.',
  },
  [ErrorType.SERVER]: {
    title: 'Server Error',
    defaultAction: 'Something went wrong on our end. Please try again.',
  },
  [ErrorType.AUTH]: {
    title: 'Authentication Required',
    defaultAction: 'Your session has expired. Please refresh the page.',
  },
  [ErrorType.NOT_FOUND]: {
    title: 'Not Found',
    defaultAction: 'The requested resource was not found.',
  },
  [ErrorType.VALIDATION]: {
    title: 'Invalid Request',
    defaultAction: 'Please check your input and try again.',
  },
  [ErrorType.CART]: {
    title: 'Cart Error',
    defaultAction: 'Unable to update your cart. Please try again.',
  },
  [ErrorType.CHECKOUT]: {
    title: 'Checkout Error',
    defaultAction: 'Unable to process checkout. Please try again.',
  },
  [ErrorType.SESSION]: {
    title: 'Session Error',
    defaultAction: 'Your session has expired. Please refresh the page.',
  },
  [ErrorType.CONFIG]: {
    title: 'Configuration Error',
    defaultAction: 'Unable to load chat configuration. Please refresh.',
  },
  [ErrorType.UNKNOWN]: {
    title: 'Unexpected Error',
    defaultAction: 'Something went wrong. Please try again.',
  },
};

export function classifyError(status: number, errorCode?: number): ErrorType {
  if (errorCode) {
    if (errorCode >= 12020 && errorCode <= 12029) return ErrorType.CART;
    if (errorCode >= 8009 && errorCode <= 8019) return ErrorType.CHECKOUT;
    if (errorCode >= 8011 && errorCode <= 8012) return ErrorType.SESSION;
    if (errorCode === 8020) return ErrorType.CONFIG;
  }
  
  if (status === 0) return ErrorType.NETWORK;
  if (status === 401) return ErrorType.AUTH;
  if (status === 403) return ErrorType.AUTH;
  if (status === 404) return ErrorType.NOT_FOUND;
  if (status === 429) return ErrorType.RATE_LIMIT;
  if (status === 504 || status === 524) return ErrorType.TIMEOUT;
  if (status === 502 || status === 503) return ErrorType.SERVER;
  if (status >= 500) return ErrorType.SERVER;
  if (status >= 400) return ErrorType.VALIDATION;
  
  return ErrorType.UNKNOWN;
}

export function getErrorSeverity(type: ErrorType): ErrorSeverity {
  switch (type) {
    case ErrorType.NETWORK:
    case ErrorType.TIMEOUT:
    case ErrorType.RATE_LIMIT:
      return ErrorSeverity.WARNING;
    case ErrorType.AUTH:
    case ErrorType.SESSION:
      return ErrorSeverity.ERROR;
    case ErrorType.SERVER:
      return ErrorSeverity.CRITICAL;
    default:
      return ErrorSeverity.ERROR;
  }
}

export function isRetryable(type: ErrorType): boolean {
  return [
    ErrorType.NETWORK,
    ErrorType.TIMEOUT,
    ErrorType.RATE_LIMIT,
    ErrorType.SERVER,
  ].includes(type);
}

export function createWidgetError(
  error: unknown,
  context?: { action?: string; fallbackUrl?: string }
): WidgetError {
  const id = `error-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  
  let status = 0;
  let errorCode: number | undefined;
  let message = 'An unexpected error occurred';
  let detail: string | undefined;
  let retryAfter: number | undefined;
  
  if (error && typeof error === 'object') {
    const err = error as Record<string, unknown>;
    status = (err.status as number) || (err.statusCode as number) || 0;
    errorCode = err.error_code as number | undefined;
    message = (err.message as string) || message;
    detail = err.detail as string | undefined;
    retryAfter = err.retry_after as number | undefined;
    
    if (err.response && typeof err.response === 'object') {
      const response = err.response as Record<string, unknown>;
      status = (response.status as number) || status;
      const data = response.data as Record<string, unknown> | undefined;
      if (data) {
        errorCode = data.error_code as number | undefined;
        message = (data.message as string) || message;
        detail = data.detail as string | undefined;
      }
    }
  }
  
  const type = classifyError(status, errorCode);
  const severity = getErrorSeverity(type);
  const retryable = isRetryable(type);
  
  return {
    id,
    type,
    code: errorCode || status || 0,
    severity,
    message: ERROR_MESSAGES[type].title,
    detail: detail || message || ERROR_MESSAGES[type].defaultAction,
    retryable,
    retryAfter,
    retryAction: context?.action,
    fallbackUrl: context?.fallbackUrl,
    timestamp: Date.now(),
    dismissed: false,
  };
}

export function formatRetryTime(seconds: number): string {
  if (seconds < 60) {
    return `${seconds}s`;
  }
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = seconds % 60;
  if (remainingSeconds === 0) {
    return `${minutes}m`;
  }
  return `${minutes}m ${remainingSeconds}s`;
}
