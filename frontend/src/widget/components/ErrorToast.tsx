import * as React from 'react';
import type { WidgetError, ErrorAction } from '../types/errors';
import { ErrorSeverity, formatRetryTime } from '../types/errors';

export interface ErrorToastProps {
  error: WidgetError;
  onDismiss: (id: string) => void;
  onRetry?: (id: string) => void;
  actions?: ErrorAction[];
  autoDismiss?: boolean;
  autoDismissDelay?: number;
  showProgress?: boolean;
}

const severityStyles: Record<ErrorSeverity, { bg: string; border: string; icon: string }> = {
  [ErrorSeverity.INFO]: {
    bg: '#eff6ff',
    border: '#3b82f6',
    icon: 'ℹ️',
  },
  [ErrorSeverity.WARNING]: {
    bg: '#fffbeb',
    border: '#f59e0b',
    icon: '⚠️',
  },
  [ErrorSeverity.ERROR]: {
    bg: '#fef2f2',
    border: '#ef4444',
    icon: '❌',
  },
  [ErrorSeverity.CRITICAL]: {
    bg: '#fef2f2',
    border: '#dc2626',
    icon: '🚨',
  },
};

export function ErrorToast({
  error,
  onDismiss,
  onRetry,
  actions,
  autoDismiss = true,
  autoDismissDelay = 8000,
  showProgress = true,
}: ErrorToastProps) {
  const [isVisible, setIsVisible] = React.useState(false);
  const [isExiting, setIsExiting] = React.useState(false);
  const [timeLeft, setTimeLeft] = React.useState(autoDismissDelay);
  const [isPaused, setIsPaused] = React.useState(false);
  const timerRef = React.useRef<ReturnType<typeof setInterval> | null>(null);

  React.useEffect(() => {
    requestAnimationFrame(() => {
      setIsVisible(true);
    });
  }, []);

  React.useEffect(() => {
    if (!autoDismiss || error.dismissed || isPaused) return;

    timerRef.current = setInterval(() => {
      setTimeLeft((prev) => {
        if (prev <= 100) {
          handleDismiss();
          return 0;
        }
        return prev - 100;
      });
    }, 100);

    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    };
  }, [autoDismiss, error.dismissed, isPaused]);

  const handleDismiss = React.useCallback(() => {
    setIsExiting(true);
    setTimeout(() => {
      onDismiss(error.id);
    }, 300);
  }, [error.id, onDismiss]);

  const handleRetry = React.useCallback(() => {
    if (onRetry) {
      onRetry(error.id);
      handleDismiss();
    }
  }, [error.id, onRetry, handleDismiss]);

  const handleMouseEnter = () => setIsPaused(true);
  const handleMouseLeave = () => setIsPaused(false);

  const styles = severityStyles[error.severity];
  const progress = (timeLeft / autoDismissDelay) * 100;

  return (
    <div
      role="alert"
      aria-live="assertive"
      aria-atomic="true"
      className={`error-toast ${isVisible && !isExiting ? 'error-toast--visible' : ''} ${isExiting ? 'error-toast--exiting' : ''}`}
      style={{
        backgroundColor: styles.bg,
        borderLeft: `4px solid ${styles.border}`,
        borderRadius: '8px',
        padding: '12px 16px',
        marginBottom: '8px',
        boxShadow: '0 4px 12px rgba(0, 0, 0, 0.1)',
        transform: isVisible && !isExiting ? 'translateX(0)' : 'translateX(100%)',
        opacity: isExiting ? 0 : 1,
        transition: 'transform 0.3s ease, opacity 0.3s ease',
        position: 'relative',
        overflow: 'hidden',
      }}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
    >
      {showProgress && autoDismiss && (
        <div
          className="error-toast__progress"
          style={{
            position: 'absolute',
            bottom: 0,
            left: 0,
            height: '3px',
            backgroundColor: styles.border,
            width: `${progress}%`,
            transition: 'width 0.1s linear',
          }}
        />
      )}

      <div
        className="error-toast__content"
        style={{
          display: 'flex',
          alignItems: 'flex-start',
          gap: '12px',
        }}
      >
        <span
          className="error-toast__icon"
          style={{
            fontSize: '18px',
            lineHeight: 1,
            flexShrink: 0,
          }}
          aria-hidden="true"
        >
          {styles.icon}
        </span>

        <div
          className="error-toast__body"
          style={{
            flex: 1,
            minWidth: 0,
          }}
        >
          <div
            className="error-toast__title"
            style={{
              fontWeight: 600,
              fontSize: '14px',
              color: '#1f2937',
              marginBottom: '4px',
            }}
          >
            {error.message}
          </div>

          {error.detail && (
            <div
              className="error-toast__detail"
              style={{
                fontSize: '13px',
                color: '#4b5563',
                marginBottom: error.retryable || actions?.length ? '12px' : 0,
              }}
            >
              {error.detail}
            </div>
          )}

          {(error.retryable || actions?.length) && (
            <div
              className="error-toast__actions"
              style={{
                display: 'flex',
                gap: '8px',
                flexWrap: 'wrap',
              }}
            >
              {error.retryable && onRetry && (
                <button
                  type="button"
                  onClick={handleRetry}
                  className="error-toast__retry"
                  style={{
                    padding: '6px 12px',
                    fontSize: '13px',
                    fontWeight: 500,
                    backgroundColor: styles.border,
                    color: 'white',
                    border: 'none',
                    borderRadius: '6px',
                    cursor: 'pointer',
                    transition: 'opacity 0.2s',
                  }}
                  onMouseEnter={(e) => (e.currentTarget.style.opacity = '0.8')}
                  onMouseLeave={(e) => (e.currentTarget.style.opacity = '1')}
                >
                  {error.retryAction || 'Try Again'}
                </button>
              )}

              {error.fallbackUrl && (
                <a
                  href={error.fallbackUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="error-toast__fallback"
                  style={{
                    padding: '6px 12px',
                    fontSize: '13px',
                    fontWeight: 500,
                    backgroundColor: 'transparent',
                    color: styles.border,
                    border: `1px solid ${styles.border}`,
                    borderRadius: '6px',
                    textDecoration: 'none',
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '4px',
                  }}
                >
                  Visit Store
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
                    <polyline points="15 3 21 3 21 9" />
                    <line x1="10" y1="14" x2="21" y2="3" />
                  </svg>
                </a>
              )}

              {actions?.map((action, index) => (
                <button
                  key={index}
                  type="button"
                  onClick={action.handler}
                  className={`error-toast__action ${action.primary ? 'error-toast__action--primary' : ''}`}
                  style={{
                    padding: '6px 12px',
                    fontSize: '13px',
                    fontWeight: 500,
                    backgroundColor: action.primary ? styles.border : 'transparent',
                    color: action.primary ? 'white' : '#4b5563',
                    border: `1px solid ${action.primary ? styles.border : '#d1d5db'}`,
                    borderRadius: '6px',
                    cursor: 'pointer',
                    transition: 'opacity 0.2s',
                  }}
                  onMouseEnter={(e) => (e.currentTarget.style.opacity = '0.8')}
                  onMouseLeave={(e) => (e.currentTarget.style.opacity = '1')}
                >
                  {action.label}
                </button>
              ))}

              {error.retryAfter && (
                <span
                  className="error-toast__retry-after"
                  style={{
                    fontSize: '12px',
                    color: '#6b7280',
                    display: 'flex',
                    alignItems: 'center',
                  }}
                >
                  Retry in {formatRetryTime(error.retryAfter)}
                </span>
              )}
            </div>
          )}
        </div>

        <button
          type="button"
          onClick={handleDismiss}
          className="error-toast__dismiss"
          aria-label="Dismiss error"
          style={{
            background: 'none',
            border: 'none',
            padding: '4px',
            cursor: 'pointer',
            color: '#9ca3af',
            flexShrink: 0,
            transition: 'color 0.2s',
          }}
          onMouseEnter={(e) => (e.currentTarget.style.color = '#4b5563')}
          onMouseLeave={(e) => (e.currentTarget.style.color = '#9ca3af')}
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="18" y1="6" x2="6" y2="18" />
            <line x1="6" y1="6" x2="18" y2="18" />
          </svg>
        </button>
      </div>
    </div>
  );
}

export interface ErrorToastContainerProps {
  errors: WidgetError[];
  onDismiss: (id: string) => void;
  onRetry?: (id: string) => void;
  maxVisible?: number;
  position?: 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left';
}

export function ErrorToastContainer({
  errors,
  onDismiss,
  onRetry,
  maxVisible = 3,
  position = 'top-right',
}: ErrorToastContainerProps) {
  const visibleErrors = errors.filter((e) => !e.dismissed).slice(0, maxVisible);

  if (visibleErrors.length === 0) return null;

  const positionStyles: Record<string, React.CSSProperties> = {
    'top-right': { top: '16px', right: '16px' },
    'top-left': { top: '16px', left: '16px' },
    'bottom-right': { bottom: '16px', right: '16px' },
    'bottom-left': { bottom: '16px', left: '16px' },
  };

  return (
    <div
      className="error-toast-container"
      aria-label="Error notifications"
      style={{
        position: 'fixed',
        ...positionStyles[position],
        zIndex: 10000,
        maxWidth: '400px',
        width: 'calc(100% - 32px)',
        display: 'flex',
        flexDirection: 'column',
        gap: '8px',
      }}
    >
      {visibleErrors.map((error) => (
        <ErrorToast
          key={error.id}
          error={error}
          onDismiss={onDismiss}
          onRetry={onRetry}
        />
      ))}
      
      {errors.filter((e) => !e.dismissed).length > maxVisible && (
        <div
          className="error-toast__more"
          style={{
            fontSize: '12px',
            color: '#6b7280',
            textAlign: 'center',
            padding: '8px',
          }}
        >
          +{errors.filter((e) => !e.dismissed).length - maxVisible} more errors
        </div>
      )}
    </div>
  );
}
