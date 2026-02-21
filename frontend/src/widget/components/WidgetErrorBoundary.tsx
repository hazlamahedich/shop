import * as React from 'react';

interface Props {
  children: React.ReactNode;
  fallback?: React.ReactNode;
  onError?: (error: Error, errorInfo: React.ErrorInfo) => void;
  onRetry?: () => void;
  showDetails?: boolean;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: React.ErrorInfo | null;
  retryCount: number;
}

export class WidgetErrorBoundary extends React.Component<Props, State> {
  state: State = { 
    hasError: false, 
    error: null, 
    errorInfo: null,
    retryCount: 0,
  };

  static getDerivedStateFromError(error: Error): Partial<State> {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    this.setState({ errorInfo });
    console.error('Widget Error:', error, errorInfo);
    this.props.onError?.(error, errorInfo);
  }

  handleRetry = () => {
    this.setState((prev) => ({
      hasError: false,
      error: null,
      errorInfo: null,
      retryCount: prev.retryCount + 1,
    }));
    this.props.onRetry?.();
  };

  handleRefresh = () => {
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      const { error, errorInfo, retryCount } = this.state;
      const isChunkError = error?.message?.includes('ChunkLoadError') || 
                          error?.message?.includes('Loading chunk');
      const isNetworkError = error?.message?.includes('Network') ||
                            error?.message?.includes('Failed to fetch');

      return (
        <div
          role="alert"
          aria-live="assertive"
          className="widget-error-boundary"
          style={{
            padding: '24px',
            textAlign: 'center',
            fontFamily: 'system-ui, -apple-system, sans-serif',
            backgroundColor: '#fef2f2',
            borderRadius: '12px',
            border: '1px solid #fecaca',
            maxWidth: '400px',
            margin: '16px auto',
          }}
        >
          <div
            className="widget-error-boundary__icon"
            style={{
              width: '48px',
              height: '48px',
              margin: '0 auto 16px',
              backgroundColor: '#fee2e2',
              borderRadius: '50%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <svg
              width="24"
              height="24"
              viewBox="0 0 24 24"
              fill="none"
              stroke="#dc2626"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <circle cx="12" cy="12" r="10" />
              <line x1="12" y1="8" x2="12" y2="12" />
              <line x1="12" y1="16" x2="12.01" y2="16" />
            </svg>
          </div>

          <h3
            className="widget-error-boundary__title"
            style={{
              margin: '0 0 8px',
              fontSize: '16px',
              fontWeight: 600,
              color: '#1f2937',
            }}
          >
            {isChunkError 
              ? 'Update Available' 
              : isNetworkError 
              ? 'Connection Error'
              : 'Something went wrong'}
          </h3>

          <p
            className="widget-error-boundary__message"
            style={{
              margin: '0 0 20px',
              fontSize: '14px',
              color: '#6b7280',
              lineHeight: 1.5,
            }}
          >
            {isChunkError 
              ? 'A new version is available. Please refresh to get the latest updates.'
              : isNetworkError 
              ? 'Unable to connect to the server. Please check your connection.'
              : 'The chat encountered an unexpected error. Please try again.'}
          </p>

          {this.props.showDetails && error && (
            <details
              className="widget-error-boundary__details"
              style={{
                marginBottom: '16px',
                textAlign: 'left',
                fontSize: '12px',
                color: '#6b7280',
              }}
            >
              <summary
                style={{
                  cursor: 'pointer',
                  marginBottom: '8px',
                }}
              >
                Error Details
              </summary>
              <pre
                style={{
                  backgroundColor: '#f3f4f6',
                  padding: '12px',
                  borderRadius: '6px',
                  overflow: 'auto',
                  maxHeight: '120px',
                  margin: 0,
                }}
              >
                {error.toString()}
                {errorInfo?.componentStack && (
                  <>
                    {'\n\nComponent Stack:'}
                    {errorInfo.componentStack}
                  </>
                )}
              </pre>
            </details>
          )}

          <div
            className="widget-error-boundary__actions"
            style={{
              display: 'flex',
              gap: '12px',
              justifyContent: 'center',
            }}
          >
            <button
              type="button"
              onClick={this.handleRetry}
              className="widget-error-boundary__retry"
              style={{
                padding: '10px 20px',
                fontSize: '14px',
                fontWeight: 500,
                backgroundColor: '#6366f1',
                color: 'white',
                border: 'none',
                borderRadius: '8px',
                cursor: 'pointer',
                transition: 'background-color 0.2s',
              }}
              onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = '#4f46e5')}
              onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = '#6366f1')}
            >
              {isChunkError || isNetworkError ? 'Try Again' : 'Retry'}
            </button>

            {(isChunkError || retryCount >= 2) && (
              <button
                type="button"
                onClick={this.handleRefresh}
                className="widget-error-boundary__refresh"
                style={{
                  padding: '10px 20px',
                  fontSize: '14px',
                  fontWeight: 500,
                  backgroundColor: 'transparent',
                  color: '#6366f1',
                  border: '1px solid #6366f1',
                  borderRadius: '8px',
                  cursor: 'pointer',
                  transition: 'background-color 0.2s',
                }}
                onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = '#eef2ff')}
                onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = 'transparent')}
              >
                Refresh Page
              </button>
            )}
          </div>

          {retryCount > 0 && (
            <p
              className="widget-error-boundary__retry-count"
              style={{
                marginTop: '12px',
                fontSize: '12px',
                color: '#9ca3af',
              }}
            >
              Retry attempts: {retryCount}
            </p>
          )}
        </div>
      );
    }

    return this.props.children;
  }
}

export function withErrorBoundary<P extends object>(
  WrappedComponent: React.ComponentType<P>,
  errorBoundaryProps?: Omit<Props, 'children'>
) {
  const displayName = WrappedComponent.displayName || WrappedComponent.name || 'Component';
  
  const ComponentWithErrorBoundary = (props: P) => (
    <WidgetErrorBoundary {...errorBoundaryProps}>
      <WrappedComponent {...props} />
    </WidgetErrorBoundary>
  );
  
  ComponentWithErrorBoundary.displayName = `withErrorBoundary(${displayName})`;
  
  return ComponentWithErrorBoundary;
}
