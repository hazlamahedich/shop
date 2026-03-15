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
import { positioningStyles } from './utils/styles';

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

  const prefetchChatWindow = React.useCallback(() => {
    import('./components/ChatWindow');
  }, []);

  React.useEffect(() => {
    initWidget(merchantId);
  }, [initWidget, merchantId]);

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
        
        /* Smart Positioning Styles */
        ${positioningStyles}
        
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
        
        /* Product Carousel Styles */
        .product-carousel {
          display: flex;
          overflow-x: auto;
          scroll-snap-type: x mandatory;
          scroll-behavior: smooth;
          -webkit-overflow-scrolling: touch;
          scrollbar-width: none;
          gap: 12px;
          padding: 4px 0;
          margin: 0 -4px;
        }
        .product-carousel::-webkit-scrollbar {
          display: none;
        }
        .carousel-card {
          scroll-snap-align: start;
          flex-shrink: 0;
          width: 140px;
          border-radius: 8px;
          background: #ffffff;
          border: 1px solid rgba(0, 0, 0, 0.1);
          overflow: hidden;
          transition: transform 200ms ease, box-shadow 200ms ease;
          cursor: pointer;
        }
        .carousel-card:hover {
          transform: translateY(-4px);
          box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
        }
        .carousel-card:focus-visible {
          outline: 2px solid var(--widget-primary, #6366f1);
          outline-offset: 2px;
        }
        .carousel-card-image {
          position: relative;
          width: 100%;
          padding-bottom: 100%;
          background: #f1f5f9;
          overflow: hidden;
        }
        .carousel-card-image img {
          position: absolute;
          top: 0;
          left: 0;
          width: 100%;
          height: 100%;
          object-fit: cover;
          transition: opacity 200ms ease;
        }
        .carousel-card-image img.loading {
          opacity: 0;
        }
        .carousel-card-skeleton {
          position: absolute;
          top: 0;
          left: 0;
          width: 100%;
          height: 100%;
          background: linear-gradient(90deg, #f1f5f9 25%, #e2e8f0 50%, #f1f5f9 75%);
          background-size: 200% 100%;
          animation: skeleton-shimmer 1.5s infinite;
        }
        @keyframes skeleton-shimmer {
          0% { background-position: 200% 0; }
          100% { background-position: -200% 0; }
        }
        .carousel-card-content {
          padding: 8px;
          display: flex;
          flex-direction: column;
          gap: 4px;
        }
        .carousel-card-title {
          font-size: 13px;
          font-weight: 500;
          line-height: 1.3;
          color: #1e293b;
          display: -webkit-box;
          -webkit-line-clamp: 2;
          -webkit-box-orient: vertical;
          overflow: hidden;
          text-overflow: ellipsis;
          margin: 0;
          min-height: 34px;
        }
        .carousel-card-price {
          font-size: 14px;
          font-weight: 600;
          color: #6366f1;
          margin: 0;
        }
        .carousel-card-button {
          display: flex;
          align-items: center;
          justify-content: center;
          width: 100%;
          padding: 6px 8px;
          margin-top: 4px;
          font-size: 12px;
          font-weight: 500;
          color: white;
          background: #6366f1;
          border: none;
          border-radius: 4px;
          cursor: pointer;
          transition: background 150ms ease, opacity 150ms ease;
        }
        .carousel-card-button:hover {
          background: #4f46e5;
        }
        .carousel-card-button:disabled {
          opacity: 0.7;
          cursor: not-allowed;
        }
        .carousel-card-button:focus-visible {
          outline: 2px solid #6366f1;
          outline-offset: 2px;
        }
        .carousel-arrows {
          position: absolute;
          top: 50%;
          left: 0;
          right: 0;
          transform: translateY(-50%);
          display: flex;
          justify-content: space-between;
          pointer-events: none;
          padding: 0 4px;
          opacity: 0;
          transition: opacity 200ms ease;
        }
        .product-carousel-wrapper:hover .carousel-arrows {
          opacity: 1;
        }
        .carousel-arrow {
          display: flex;
          align-items: center;
          justify-content: center;
          width: 32px;
          height: 32px;
          background: #ffffff;
          border: 1px solid rgba(0, 0, 0, 0.1);
          border-radius: 50%;
          cursor: pointer;
          pointer-events: auto;
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
          transition: background 150ms ease, box-shadow 150ms ease;
          color: #1e293b;
        }
        .carousel-arrow:hover {
          background: #f8fafc;
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        }
        .carousel-arrow:disabled {
          opacity: 0.3;
          cursor: not-allowed;
        }
        .carousel-arrow:focus-visible {
          outline: 2px solid #6366f1;
          outline-offset: 2px;
        }
        .carousel-dots {
          display: flex;
          justify-content: center;
          gap: 6px;
          padding: 8px 0 4px;
        }
        .carousel-dot {
          width: 8px;
          height: 8px;
          border-radius: 50%;
          background: rgba(0, 0, 0, 0.2);
          border: none;
          padding: 0;
          cursor: pointer;
          transition: background 150ms ease, transform 150ms ease;
        }
        .carousel-dot:hover {
          background: rgba(0, 0, 0, 0.4);
        }
        .carousel-dot.active {
          width: 10px;
          height: 10px;
          background: #6366f1;
        }
        .carousel-dot:focus-visible {
          outline: 2px solid #6366f1;
          outline-offset: 2px;
        }
        .product-carousel-wrapper {
          position: relative;
          width: 100%;
        }
        @media (prefers-reduced-motion: reduce) {
          .carousel-card:hover {
            transform: none;
          }
          .product-carousel {
            scroll-behavior: auto;
          }
          .carousel-card-skeleton {
            animation: none;
          }
          .carousel-card,
          .carousel-arrow,
          .carousel-dot,
          .carousel-card-image img,
          .carousel-arrows {
            transition: none;
          }
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
                    isDragging={state.isDragging}
                    isMinimized={state.isMinimized}
                    onDragStart={() => {}}
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
