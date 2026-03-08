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
    clearHistory,
    updatePosition,
    toggleMinimized,
  } = useWidgetContext();
  const merchantTheme = state.config?.theme;
  const mergedTheme = React.useMemo(
    () => mergeThemes(merchantTheme, theme),
    [merchantTheme, theme]
  );

  const dragStartRef = React.useRef({ x: 0, y: 0, windowX: 0, windowY: 0 });
  const [isDraggingLocal, setIsDraggingLocal] = React.useState(false);

  const prefetchChatWindow = React.useCallback(() => {
    import('./components/ChatWindow');
  }, []);

  React.useEffect(() => {
    initWidget(merchantId);
  }, [initWidget, merchantId]);

  const handleDragStart = React.useCallback((e: React.MouseEvent | React.TouchEvent) => {
    e.preventDefault();
    setIsDraggingLocal(true);

    const clientX = 'touches' in e ? e.touches[0].clientX : e.clientX;
    const clientY = 'touches' in e ? e.touches[0].clientY : e.clientY;

    dragStartRef.current = {
      x: clientX,
      y: clientY,
      windowX: state.position.x,
      windowY: state.position.y,
    };
  }, [state.position]);

  React.useEffect(() => {
    if (!isDraggingLocal) return;

    const handleMouseMove = (e: MouseEvent) => {
      const deltaX = e.clientX - dragStartRef.current.x;
      const deltaY = e.clientY - dragStartRef.current.y;

      const newX = dragStartRef.current.windowX + deltaX;
      const newY = dragStartRef.current.windowY + deltaY;

      const boundedX = Math.max(-window.innerWidth + 200, Math.min(newX, window.innerWidth - 200));
      const boundedY = Math.max(-window.innerHeight + 200, Math.min(newY, window.innerHeight - 200));

      updatePosition({ x: boundedX, y: boundedY });
    };

    const handleTouchMove = (e: TouchEvent) => {
      e.preventDefault();
      const touch = e.touches[0];
      const deltaX = touch.clientX - dragStartRef.current.x;
      const deltaY = touch.clientY - dragStartRef.current.y;

      const newX = dragStartRef.current.windowX + deltaX;
      const newY = dragStartRef.current.windowY + deltaY;

      const boundedX = Math.max(-window.innerWidth + 200, Math.min(newX, window.innerWidth - 200));
      const boundedY = Math.max(-window.innerHeight + 200, Math.min(newY, window.innerHeight - 200));

      updatePosition({ x: boundedX, y: boundedY });
    };

    const handleEnd = () => {
      setIsDraggingLocal(false);
    };

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleEnd);
    document.addEventListener('touchmove', handleTouchMove, { passive: false });
    document.addEventListener('touchend', handleEnd);

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleEnd);
      document.removeEventListener('touchmove', handleTouchMove);
      document.removeEventListener('touchend', handleEnd);
    };
  }, [isDraggingLocal, updatePosition]);

  const handleBubbleClick = React.useCallback(() => {
    if (state.isMinimized) {
      toggleMinimized();
    } else {
      toggleChat();
    }
  }, [state.isMinimized, toggleMinimized, toggleChat]);

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
        .shopbot-chat-window.dragging {
          animation: none;
        }
        @keyframes shopbot-slideUp {
          from { opacity: 0; transform: translateY(10px); }
          to { opacity: 1; transform: translateY(0); }
        }
        @keyframes shopbot-pulse {
          0%, 100% { transform: scale(1); }
          50% { transform: scale(1.1); }
        }
        .shopbot-chat-bubble.has-unread {
          animation: shopbot-pulse 2s ease-in-out infinite;
        }
        .chat-header-drag-handle {
          cursor: grab;
        }
        .chat-header-drag-handle:active {
          cursor: grabbing;
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
            isOpen={state.isOpen && !state.isMinimized}
            onClick={handleBubbleClick}
            theme={mergedTheme}
            onPrefetch={prefetchChatWindow}
            unreadCount={state.unreadCount}
          />
          {state.isOpen && !state.isMinimized && (
            <WidgetErrorBoundary fallback={<div style={{position:'fixed',bottom:100,right:20,zIndex:2147483647}}>Failed to load chat.</div>}>
              <React.Suspense fallback={<LoadingSpinner />}>
                <ChatWindow
                  isOpen={state.isOpen && !state.isMinimized}
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
                  onClearHistory={clearHistory}
                  position={state.position}
                  isDragging={isDraggingLocal}
                  isMinimized={state.isMinimized}
                  onDragStart={handleDragStart}
                  onMinimize={toggleMinimized}
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
