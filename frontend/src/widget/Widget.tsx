import * as React from 'react';
import { WidgetProvider, useWidgetContext } from './context/WidgetContext';
import { ChatBubble } from './components/ChatBubble';
import { WidgetErrorBoundary } from './components/WidgetErrorBoundary';
import { LoadingSpinner } from './components/LoadingSpinner';
import type { WidgetTheme } from './types/widget';
import { mergeThemes } from './utils/themeMerge';

const ChatWindow = React.lazy(() => import('./components/ChatWindow'));

interface WidgetInnerProps {
  theme?: Partial<WidgetTheme>;
}

function WidgetInner({ theme }: WidgetInnerProps) {
  const {
    state,
    toggleChat,
    initWidget,
    sendMessage,
    merchantId,
    addToCart,
    removeFromCart,
    checkout,
    addingProductId,
    removingItemId,
    isCheckingOut,
    dismissError,
    retryLastAction,
    recordConsent,
  } = useWidgetContext();
  const merchantTheme = state.config?.theme;
  const mergedTheme = React.useMemo(
    () => mergeThemes(merchantTheme, theme),
    [merchantTheme, theme]
  );

  const prefetchChatWindow = React.useCallback(() => {
    import('./components/ChatWindow');
  }, []);

  React.useEffect(() => {
    initWidget(merchantId);
  }, [initWidget, merchantId]);

  return (
    <>
      <style>{`
        .shopbot-widget-root * {
          box-sizing: border-box;
        }
        .shopbot-chat-bubble:hover {
          transform: scale(1.05);
          box-shadow: 0 6px 16px rgba(0, 0, 0, 0.2) !important;
        }
        .shopbot-chat-bubble:active {
          transform: scale(0.95);
        }
        .shopbot-chat-window {
          animation: shopbot-slideUp 0.2s ease-out;
        }
        @keyframes shopbot-slideUp {
          from { opacity: 0; transform: translateY(10px); }
          to { opacity: 1; transform: translateY(0); }
        }
      `}</style>
      {state.isLoading ? (
        <div style={{
          position: 'fixed',
          bottom: 20,
          right: mergedTheme.position === 'bottom-left' ? undefined : 20,
          left: mergedTheme.position === 'bottom-left' ? 20 : undefined,
          width: 60,
          height: 60,
          borderRadius: '50%',
          backgroundColor: mergedTheme.primaryColor,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 2147483647,
        }}>
          <LoadingSpinner />
        </div>
      ) : (
        <>
          <ChatBubble
            isOpen={state.isOpen}
            onClick={toggleChat}
            theme={mergedTheme}
            onPrefetch={prefetchChatWindow}
          />
          {state.isOpen && (
            <WidgetErrorBoundary fallback={<div style={{position:'fixed',bottom:100,right:20,zIndex:2147483647}}>Failed to load chat.</div>}>
              <React.Suspense fallback={<LoadingSpinner />}>
                <ChatWindow
                  isOpen={state.isOpen}
                  onClose={toggleChat}
                  theme={mergedTheme}
                  config={state.config}
                  messages={state.messages}
                  isTyping={state.isTyping}
                  onSendMessage={sendMessage}
                  error={state.error}
                  errors={state.errors}
                  onDismissError={dismissError}
                  onRetryError={retryLastAction}
                  onAddToCart={addToCart}
                  onRemoveFromCart={removeFromCart}
                  onCheckout={checkout}
                  addingProductId={addingProductId}
                  removingItemId={removingItemId}
                  isCheckingOut={isCheckingOut}
                  sessionId={state.session?.sessionId}
                  connectionStatus={state.connectionStatus}
                  consentState={state.consentState}
                  onRecordConsent={recordConsent}
                />
              </React.Suspense>
            </WidgetErrorBoundary>
          )}
        </>
      )}
    </>
  );
}

interface WidgetProps {
  merchantId: string;
  theme?: Partial<WidgetTheme>;
}

export function Widget({ merchantId, theme }: WidgetProps) {
  return (
    <WidgetErrorBoundary>
      <WidgetProvider merchantId={merchantId}>
        <WidgetInner theme={theme} />
      </WidgetProvider>
    </WidgetErrorBoundary>
  );
}
