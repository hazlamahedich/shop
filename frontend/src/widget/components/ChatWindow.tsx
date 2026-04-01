import * as React from 'react';
import FocusTrap from 'focus-trap-react';
import type { WidgetTheme, WidgetConfig, WidgetMessage, WidgetProduct, WidgetProductDetail, ConnectionStatus, ConsentState, WidgetPosition, ThemeMode, QuickReply, FAQQuickButton, FeedbackRatingValue } from '../types/widget';
import type { WidgetError } from '../types/errors';
import { MessageList } from './MessageList';
import { MessageInput } from './MessageInput';
import { TypingIndicator } from './TypingIndicator';
import { ErrorToast } from './ErrorToast';
import { ProductDetailModal } from './ProductDetailModal';
import { ConnectionStatusIndicator } from './ConnectionStatus';
import { ConsentPrompt } from './ConsentPrompt';
import { ThemeToggle } from './ThemeToggle';
import { QuickReplyButtons } from './QuickReplyButtons';
import { FAQQuickButtons } from './FAQQuickButtons';
import { SuggestedReplies } from './SuggestedReplies';
import { StreamingIndicator, StreamErrorIndicator } from './StreamingIndicator';

export interface ChatWindowProps {
  isOpen: boolean;
  onClose: () => void;
  theme: WidgetTheme;
  config: WidgetConfig | null;
  messages: WidgetMessage[];
  isTyping: boolean;
  onSendMessage: (content: string) => Promise<void>;
  error: string | null;
  errors?: WidgetError[];
  onDismissError?: (errorId: string) => void;
  onRetryError?: (errorId: string) => void;
  onAddToCart?: (product: WidgetProduct) => void;
  onRemoveFromCart?: (variantId: string) => void;
  onCheckout?: () => void;
  addingProductId?: string | null;
  removingItemId?: string | null;
  isCheckingOut?: boolean;
  sessionId?: string;
  connectionStatus?: ConnectionStatus;
  consentState?: ConsentState;
  onRecordConsent?: (consented: boolean) => Promise<void>;
  onClearHistory?: () => Promise<void>;
  position?: WidgetPosition | null;
  isDragging?: boolean;
  isMinimized?: boolean;
  onDragStart?: (e: React.MouseEvent | React.TouchEvent) => void;
  onMinimize?: () => void;
  themeMode?: ThemeMode;
  onThemeToggle?: () => void;
  faqQuickButtons?: FAQQuickButton[];
  onFaqButtonClick?: (button: FAQQuickButton) => void;
  onFeedbackSubmit?: (messageId: string, rating: FeedbackRatingValue, comment?: string) => Promise<void>;
  isStreaming?: boolean;
  streamingError?: string | null;
}

function ChatWindow({
  isOpen,
  onClose,
  theme,
  config,
  messages,
  isTyping,
  onSendMessage,
  error,
  errors = [],
  onDismissError,
  onRetryError,
  onAddToCart,
  onRemoveFromCart,
  onCheckout,
  addingProductId,
  removingItemId,
  isCheckingOut,
  sessionId,
  connectionStatus = 'disconnected',
  consentState,
  onRecordConsent,
  onClearHistory,
  position = { x: 0, y: 0 },
  isDragging = false,
  isMinimized: _isMinimized = false,
  onDragStart,
  onMinimize,
  themeMode = 'auto',
  onThemeToggle,
  faqQuickButtons,
  onFaqButtonClick,
  onFeedbackSubmit,
  isStreaming = false,
  streamingError = null,
}: ChatWindowProps) {
  const [inputValue, setInputValue] = React.useState('');
  const [selectedProductId, setSelectedProductId] = React.useState<string | null>(null);
  const [isProductModalOpen, setIsProductModalOpen] = React.useState(false);
  const [showMenu, setShowMenu] = React.useState(false);
  const [activeQuickReplies, setActiveQuickReplies] = React.useState<QuickReply[] | null>(null);
  const [showFaqButtons, setShowFaqButtons] = React.useState(true);
  const [activeSuggestions, setActiveSuggestions] = React.useState<string[] | null>(null);
  const inputRef = React.useRef<HTMLInputElement>(null);
  const menuRef = React.useRef<HTMLDivElement>(null);

  // Story 10-3: Hide suggestions when user starts typing
  const handleInputChange = (value: string) => {
    setInputValue(value);
    if (value.length > 0 && activeSuggestions) {
      setActiveSuggestions(null);
    }
  };

  const handleProductClick = (product: WidgetProduct) => {
    setSelectedProductId(product.id);
    setIsProductModalOpen(true);
  };

  const handleProductModalClose = () => {
    setIsProductModalOpen(false);
    setSelectedProductId(null);
  };

  const handleProductAddToCart = (product: WidgetProductDetail, _quantity: number) => {
    if (onAddToCart && product.variantId) {
      onAddToCart({
        id: product.id,
        variantId: product.variantId,
        title: product.title,
        description: product.description ?? undefined,
        price: product.price,
        imageUrl: product.imageUrl ?? undefined,
        available: product.available,
        productType: product.productType ?? undefined,
      });
    }
  };

  React.useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isOpen]);

  React.useEffect(() => {
    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [isOpen, onClose]);

  React.useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setShowMenu(false);
      }
    };
    if (showMenu) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [showMenu]);

  const handleClearHistory = async () => {
    if (onClearHistory) {
      setShowMenu(false);
      await onClearHistory();
    }
  };

  const handleSend = async () => {
    if (!inputValue.trim()) return;
    const message = inputValue.trim();
    setInputValue('');
    setActiveSuggestions(null);
    await onSendMessage(message);
  };

  const handleQuickReply = async (reply: QuickReply) => {
    setActiveQuickReplies(null);
    await onSendMessage(reply.payload ?? reply.text);
  };

  const handleQuickRepliesAvailable = (replies: QuickReply[]) => {
    if (replies && replies.length > 0) {
      setActiveQuickReplies(replies);
    } else {
      setActiveQuickReplies(null);
    }
  };

  const handleSuggestedRepliesAvailable = (suggestions: string[]) => {
    if (suggestions && suggestions.length > 0) {
      setActiveSuggestions(suggestions);
    } else {
      setActiveSuggestions(null);
    }
  };

  const handleFaqButtonClick = async (button: FAQQuickButton) => {
    if (onFaqButtonClick) {
      onFaqButtonClick(button);
    } else {
      setShowFaqButtons(false);
      await onSendMessage(button.question);
    }
  };

  const handleSuggestionSelect = async (suggestion: string) => {
    setActiveSuggestions(null);
    await onSendMessage(suggestion);
  };

  // Hide FAQ buttons after first USER message (Story 10-2 AC4)
  // Note: Welcome message from bot doesn't count as first message
  React.useEffect(() => {
    const userMessages = messages.filter((m) => m.sender === 'user');
    if (userMessages.length > 0 && showFaqButtons) {
      setShowFaqButtons(false);
    }
  }, [messages, showFaqButtons]);

  if (!isOpen) return null;


  const isMobile = typeof window !== 'undefined' && window.innerWidth < 768;
  
  // A position is considered "default" if it's null OR exactly 0,0 (which usually means it hasn't been moved)
  const isDefaultPosition = isMobile || !position || (position.x === 0 && position.y === 0);
  const windowPosition = position || { x: 0, y: 0 };

  const windowStyle: React.CSSProperties = {
    position: 'fixed',
    bottom: isMobile ? 0 : (isDefaultPosition ? (theme.position?.startsWith('top') ? 'auto' : 90) : 'auto'),
    right: isMobile ? 0 : (isDefaultPosition ? (theme.position?.endsWith('left') ? 'auto' : 20) : 'auto'),
    top: isMobile ? 'auto' : (isDefaultPosition ? (theme.position?.startsWith('top') ? 20 : 'auto') : 0),
    left: isMobile ? 'auto' : (isDefaultPosition ? (theme.position?.endsWith('left') ? 20 : 'auto') : 0),
    transform: isDefaultPosition ? 'none' : `translate(${windowPosition.x}px, ${windowPosition.y}px)`,
    width: isMobile ? '100%' : theme.width,
    height: isMobile ? '100%' : theme.height,
    maxWidth: isMobile ? '100%' : 'calc(100vw - 40px)',
    maxHeight: isMobile ? '100%' : 'calc(100vh - 40px)',
    backgroundColor: theme.backgroundColor,
    borderRadius: theme.borderRadius,
    boxShadow: '0 8px 32px rgba(0, 0, 0, 0.15)',
    display: 'flex',
    flexDirection: 'column',
    overflow: 'hidden',
    zIndex: 2147483646,
    fontFamily: theme.fontFamily,
    fontSize: theme.fontSize,
    color: theme.textColor,
    transition: isDragging ? 'none' : 'transform 0.2s ease-out',
    userSelect: isDragging ? 'none' : 'auto',
  };

  console.log('[ChatWindow] Rendering with state:', {
    isOpen,
    isMobile,
    isDefaultPosition,
    position,
    windowPosition,
    themeWidth: theme.width,
    viewportWidth: window.innerWidth
  });
  console.log('[ChatWindow] Calculated Style:', {
    bottom: windowStyle.bottom,
    right: windowStyle.right,
    left: windowStyle.left,
    top: windowStyle.top,
    transform: windowStyle.transform,
    width: windowStyle.width
  });

  const handleHeaderMouseDown = (e: React.MouseEvent) => {
    if ((e.target as HTMLElement).closest('button')) return;
    onDragStart?.(e);
  };

  const handleHeaderTouchStart = (e: React.TouchEvent) => {
    if ((e.target as HTMLElement).closest('button')) return;
    onDragStart?.(e);
  };

  return (
    <>
    <FocusTrap active={isOpen && !isProductModalOpen}>
      <div
        role="dialog"
        aria-modal="true"
        aria-label="Chat window"
        data-testid="chat-window"
        className={`shopbot-chat-window draggable-chat-window ${isDragging ? 'dragging' : ''} ${isDefaultPosition ? 'is-default-position' : ''}`}
        style={windowStyle}
      >
        <div
          className="chat-header chat-header-drag-handle"
          onMouseDown={handleHeaderMouseDown}
          onTouchStart={handleHeaderTouchStart}
          style={{
            padding: '12px 16px',
            backgroundColor: theme.primaryColor,
            color: 'white',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            borderRadius: `${theme.borderRadius}px ${theme.borderRadius}px 0 0`,
            cursor: isDragging ? 'grabbing' : 'grab',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span className="chat-header-title" style={{ fontWeight: 600, pointerEvents: 'none' }}>
              {config?.botName ?? 'Mantisbot'}
            </span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            {onClearHistory && messages.length > 0 && (
              <div style={{ position: 'relative' }} ref={menuRef}>
                <button
                  type="button"
                  onClick={() => setShowMenu(!showMenu)}
                  aria-label="Chat options"
                  aria-haspopup="true"
                  aria-expanded={showMenu}
                  style={{
                    background: 'rgba(255, 255, 255, 0.2)',
                    border: 'none',
                    cursor: 'pointer',
                    padding: '8px',
                    color: 'white',
                    borderRadius: '4px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}
                >
                  <svg
                    width="18"
                    height="18"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    aria-hidden="true"
                  >
                    <circle cx="12" cy="12" r="1" />
                    <circle cx="12" cy="5" r="1" />
                    <circle cx="12" cy="19" r="1" />
                  </svg>
                </button>
                {showMenu && (
                  <div
                    role="menu"
                    style={{
                      position: 'absolute',
                      top: '100%',
                      right: 0,
                      marginTop: '4px',
                      backgroundColor: 'white',
                      borderRadius: '8px',
                      boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
                      minWidth: '150px',
                      zIndex: 10,
                      overflow: 'hidden',
                    }}
                  >
                    <button
                      type="button"
                      role="menuitem"
                      onClick={handleClearHistory}
                      style={{
                        width: '100%',
                        padding: '10px 14px',
                        textAlign: 'left',
                        background: 'none',
                        border: 'none',
                        cursor: 'pointer',
                        fontSize: '14px',
                        color: theme.textColor,
                        display: 'flex',
                        alignItems: 'center',
                        gap: '8px',
                      }}
                      onMouseEnter={(e) => {
                        (e.target as HTMLElement).style.backgroundColor = '#f3f4f6';
                      }}
                      onMouseLeave={(e) => {
                        (e.target as HTMLElement).style.backgroundColor = 'transparent';
                      }}
                    >
                      <svg
                        width="16"
                        height="16"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="2"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        aria-hidden="true"
                      >
                        <polyline points="3 6 5 6 21 6" />
                        <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
                      </svg>
                      Clear History
                    </button>
                  </div>
                )}
              </div>
            )}
            {onThemeToggle && (
              <ThemeToggle
                themeMode={themeMode}
                onToggle={onThemeToggle}
              />
            )}
            {onMinimize && (
              <button
                type="button"
                onClick={onMinimize}
                aria-label="Minimize chat window"
                title="Minimize"
                style={{
                  background: 'rgba(255, 255, 255, 0.2)',
                  border: 'none',
                  cursor: 'pointer',
                  padding: '8px',
                  color: 'white',
                  borderRadius: '4px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  transition: 'background 0.15s ease',
                }}
                onMouseEnter={(e) => (e.currentTarget.style.background = 'rgba(255, 255, 255, 0.3)')}
                onMouseLeave={(e) => (e.currentTarget.style.background = 'rgba(255, 255, 255, 0.2)')}
              >
                <svg
                  width="18"
                  height="18"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  aria-hidden="true"
                >
                  <line x1="5" y1="12" x2="19" y2="12" />
                </svg>
              </button>
            )}
            <button
              type="button"
              onClick={onClose}
              aria-label="Close chat window"
              title="Close"
              style={{
                background: 'rgba(255, 255, 255, 0.2)',
                border: 'none',
                cursor: 'pointer',
                padding: '8px',
                color: 'white',
                borderRadius: '4px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                transition: 'background 0.15s ease',
              }}
              onMouseEnter={(e) => (e.currentTarget.style.background = 'rgba(255, 255, 255, 0.3)')}
              onMouseLeave={(e) => (e.currentTarget.style.background = 'rgba(255, 255, 255, 0.2)')}
            >
              <svg
                width="18"
                height="18"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2.5"
                strokeLinecap="round"
                strokeLinejoin="round"
                aria-hidden="true"
              >
                <line x1="18" y1="6" x2="6" y2="18" />
                <line x1="6" y1="6" x2="18" y2="18" />
              </svg>
            </button>
          </div>
        </div>

        {/* Connection Status Indicator */}
        {connectionStatus !== 'connected' && (
          <div style={{ padding: '8px 12px', flexShrink: 0 }}>
            <ConnectionStatusIndicator status={connectionStatus} />
          </div>
        )}

        <MessageList
          messages={messages}
          botName={config?.botName ?? 'Mantisbot'}
          businessName={config?.businessName}
          welcomeMessage={config?.welcomeMessage}
          theme={theme}
          isLoading={isTyping}
          onAddToCart={onAddToCart}
          onProductClick={handleProductClick}
          onRemoveFromCart={onRemoveFromCart}
          onCheckout={onCheckout}
          addingProductId={addingProductId}
          removingItemId={removingItemId}
          isCheckingOut={isCheckingOut}
          onQuickRepliesAvailable={handleQuickRepliesAvailable}
          onSuggestedRepliesAvailable={handleSuggestedRepliesAvailable}
          sessionId={sessionId}
          onFeedbackSubmit={onFeedbackSubmit}
        />

        {/* Story 10-3: Suggested Reply Chips */}
        {activeSuggestions && activeSuggestions.length > 0 && (
          <div style={{ flexShrink: 0, padding: '0 12px 8px' }}>
            <SuggestedReplies
              suggestions={activeSuggestions}
              onSelect={handleSuggestionSelect}
              theme={theme}
              disabled={isTyping}
            />
          </div>
        )}

        {/* Quick Reply Buttons - Story 9-4 */}
        {activeQuickReplies && activeQuickReplies.length > 0 && (
          <div style={{ flexShrink: 0, padding: '0 12px 8px' }}>
            <QuickReplyButtons
              quickReplies={activeQuickReplies}
              onReply={handleQuickReply}
              theme={theme}
              dismissOnSelect={true}
            />
          </div>
        )}

        {/* FAQ Quick Buttons - Story 10-2 */}
        {showFaqButtons && faqQuickButtons && faqQuickButtons.length > 0 && config?.onboardingMode === 'general' && (
          <div style={{ flexShrink: 0, padding: '0 12px 8px' }}>
            <FAQQuickButtons
              buttons={faqQuickButtons}
              onButtonClick={handleFaqButtonClick}
              theme={theme}
              disabled={isTyping}
            />
          </div>
        )}

        {consentState && onRecordConsent && (
          <div style={{ padding: '8px 12px', flexShrink: 0 }}>
            <ConsentPrompt
              isOpen={isOpen}
              isLoading={false}
              isTyping={isTyping}
              promptShown={consentState.promptShown}
              consentGranted={
                consentState.status === 'opted_in'
                  ? true
                  : consentState.status === 'opted_out'
                    ? false
                    : null
              }
              theme={theme}
              botName={config?.botName ?? 'Mantisbot'}
              personality={config?.personality}
              onConfirmConsent={onRecordConsent}
            />
          </div>
        )}

        {isTyping && (
          <div style={{ flexShrink: 0 }}>
            <TypingIndicator
              isVisible={isTyping}
              botName={config?.botName ?? 'Mantisbot'}
              theme={theme}
            />
          </div>
        )}

        <StreamingIndicator isVisible={isStreaming} theme={theme} />
        <StreamErrorIndicator error={streamingError} />

        {(errors.length > 0 || error) && (
          <div
            className="chat-errors"
            style={{
              padding: '8px',
              maxHeight: '150px',
              overflowY: 'auto',
              flexShrink: 0,
            }}
          >
            {errors.filter((e) => !e.dismissed).map((widgetError) => (
              <ErrorToast
                key={widgetError.id}
                error={widgetError}
                onDismiss={onDismissError || (() => {})}
                onRetry={onRetryError}
                autoDismiss={true}
                autoDismissDelay={10000}
                showProgress={true}
              />
            ))}
            {error && errors.filter((e) => !e.dismissed).length === 0 && (
              <div
                className="chat-error"
                role="alert"
                style={{
                  padding: '12px 16px',
                  backgroundColor: '#fee2e2',
                  color: '#dc2626',
                  fontSize: '13px',
                  borderRadius: '8px',
                  borderLeft: '4px solid #dc2626',
                  display: 'flex',
                  alignItems: 'flex-start',
                  gap: '12px',
                }}
              >
                <span aria-hidden="true">❌</span>
                <span>{error}</span>
              </div>
            )}
          </div>
        )}

        <MessageInput
          value={inputValue}
          onChange={handleInputChange}
          onSend={handleSend}
          disabled={isTyping}
          placeholder="Type a message..."
          inputRef={inputRef as React.Ref<HTMLInputElement>}
          theme={theme}
          themeMode={themeMode}
        />
      </div>
    </FocusTrap>

    {sessionId && (
      <ProductDetailModal
        productId={selectedProductId}
        sessionId={sessionId}
        theme={theme}
        isOpen={isProductModalOpen}
        onClose={handleProductModalClose}
        onAddToCart={handleProductAddToCart}
      />
    )}
  </>
  );
}

export default ChatWindow;
