import * as React from 'react';
import { WidgetProvider, useWidgetContext } from './context/WidgetContext';
import { ChatBubble } from './components/ChatBubble';
import { WidgetErrorBoundary } from './components/WidgetErrorBoundary';
import { LoadingSpinner } from './components/LoadingSpinner';
import type { WidgetTheme } from './types/widget';
import { mergeThemes } from './utils/themeMerge';
import { useThemeDetection } from './hooks/useThemeDetection';
import { GlassmorphismChatWindow } from './components/GlassmorphismChatWindow';
import { getNextThemeMode } from './components/ThemeToggle';

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
    setThemeMode,
  } = useWidgetContext();
  const { systemTheme } = useThemeDetection();
  const merchantTheme = state.config?.theme;
  const mergedTheme = React.useMemo(
    () => mergeThemes(merchantTheme, theme),
    [merchantTheme, theme]
  );

  const handleThemeToggle = React.useCallback(() => {
    const nextMode = getNextThemeMode(state.themeMode);
    setThemeMode(nextMode);
  }, [state.themeMode, setThemeMode]);

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
        
        /* Glassmorphism Styles */
        .glassmorphism-wrapper.dark-mode .shopbot-chat-window {
          background: rgba(15, 23, 42, 0.8) !important;
          -webkit-backdrop-filter: blur(16px);
          backdrop-filter: blur(16px);
          border: 1px solid rgba(255, 255, 255, 0.1);
          color: #f8fafc !important;
        }
        .glassmorphism-wrapper.dark-mode .chat-header {
          background: rgba(15, 23, 42, 0.6) !important;
          -webkit-backdrop-filter: blur(8px);
          backdrop-filter: blur(8px);
        }
        .glassmorphism-wrapper.dark-mode .message-timestamp {
          color: #94a3b8 !important;
        }
        .glassmorphism-wrapper.light-mode .shopbot-chat-window {
          background: rgba(255, 255, 255, 0.7) !important;
          -webkit-backdrop-filter: blur(16px);
          backdrop-filter: blur(16px);
          border: 1px solid rgba(0, 0, 0, 0.05);
          color: #1e293b !important;
        }
        .glassmorphism-wrapper.light-mode .chat-header {
          background: rgba(255, 255, 255, 0.5) !important;
          -webkit-backdrop-filter: blur(8px);
          backdrop-filter: blur(8px);
        }
        .glassmorphism-wrapper.light-mode .message-timestamp {
          color: #64748b !important;
        }
        .glassmorphism-wrapper .shopbot-chat-window,
        .glassmorphism-wrapper .shopbot-chat-window * {
          transition: background 300ms ease, color 300ms ease, border-color 300ms ease, box-shadow 300ms ease;
        }
        @media (prefers-reduced-motion: reduce) {
          .glassmorphism-wrapper .shopbot-chat-window,
          .glassmorphism-wrapper .shopbot-chat-window * {
            transition: none !important;
            animation: none !important;
          }
        }
        @supports not (backdrop-filter: blur(1px)) {
          .glassmorphism-wrapper.dark-mode .shopbot-chat-window {
            background: rgba(15, 23, 42, 0.95);
          }
          .glassmorphism-wrapper.light-mode .shopbot-chat-window {
            background: rgba(255, 255, 255, 0.95);
          }
        }
        .shopbot-theme-toggle {
          display: flex;
          align-items: center;
          justify-content: center;
          width: 32px;
          height: 32px;
          background: rgba(255, 255, 255, 0.2);
          border: none;
          border-radius: 4px;
          cursor: pointer;
          color: white;
          transition: background 0.15s ease;
          padding: 0;
        }
        .shopbot-theme-toggle:hover {
          background: rgba(255, 255, 255, 0.3);
        }
        .shopbot-theme-toggle:focus-visible {
          outline: 2px solid rgba(255, 255, 255, 0.5);
          outline-offset: 2px;
        }
        .shopbot-theme-toggle svg {
          width: 18px;
          height: 18px;
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
                <GlassmorphismChatWindow
                  themeMode={state.themeMode}
                  systemTheme={systemTheme}
                >
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
                    themeMode={state.themeMode}
                    onThemeToggle={handleThemeToggle}
                  />
                </GlassmorphismChatWindow>
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
