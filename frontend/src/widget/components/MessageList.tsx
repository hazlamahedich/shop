import * as React from 'react';
import type { WidgetTheme, WidgetMessage, WidgetProduct, QuickReply, MessageGroup, FeedbackRatingValue, ContactOption } from '../types/widget';
import { ProductList } from './ProductCard';
import { ProductCarousel } from './ProductCarousel';
import { CartView } from './CartView';
import { MessageAvatar } from './MessageAvatar';
import { SourceCitation } from './SourceCitation';
import { FeedbackRating } from './FeedbackRating';
import { ContactCard } from './ContactCard';
import { groupMessages, getGroupPosition } from '../utils/messageGrouping';
import { formatRelativeTime, formatAbsoluteTime } from '../utils/timeFormatting';
import { useReducedMotion } from '../hooks/useReducedMotion';

export interface MessageListProps {
  messages: WidgetMessage[];
  botName: string;
  businessName?: string;
  welcomeMessage?: string;
  theme: WidgetTheme;
  isLoading?: boolean;
  onAddToCart?: (product: WidgetProduct) => void;
  onProductClick?: (product: WidgetProduct) => void;
  onRemoveFromCart?: (variantId: string) => void;
  onCheckout?: () => void;
  addingProductId?: string | null;
  removingItemId?: string | null;
  isCheckingOut?: boolean;
  onQuickRepliesAvailable?: (replies: QuickReply[]) => void;
  onSuggestedRepliesAvailable?: (suggestions: string[]) => void;
  sessionId?: string;
  onFeedbackSubmit?: (messageId: string, rating: FeedbackRatingValue, comment?: string) => Promise<void>;
}

export function MessageList({
  messages,
  botName,
  businessName,
  welcomeMessage,
  theme,
  isLoading,
  onAddToCart,
  onProductClick,
  onRemoveFromCart,
  onCheckout,
  addingProductId,
  removingItemId,
  isCheckingOut,
  onQuickRepliesAvailable,
  onSuggestedRepliesAvailable,
  sessionId,
  onFeedbackSubmit,
}: MessageListProps) {
  const messagesEndRef = React.useRef<HTMLDivElement>(null);
  const prevMessageIdsRef = React.useRef<Set<string>>(new Set());
  const reducedMotion = useReducedMotion();

  const groups = React.useMemo(() => groupMessages(messages), [messages]);

  // Track which messages are new
  const getNewMessageIds = React.useCallback(() => {
    const currentIds = new Set(messages.map(m => m.messageId));
    const newIds = new Set<string>();
    
    currentIds.forEach(id => {
      if (!prevMessageIdsRef.current.has(id)) {
        newIds.add(id);
      }
    });
    
    // Update ref for next render
    prevMessageIdsRef.current = currentIds;
    
    return newIds;
  }, [messages]);

  const newMessageIds = getNewMessageIds();

  React.useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  React.useEffect(() => {
    const lastMessage = messages[messages.length - 1];
    if (lastMessage?.sender === 'bot' && lastMessage.quick_replies) {
      onQuickRepliesAvailable?.(lastMessage.quick_replies);
    } else if (lastMessage?.sender === 'user') {
      onQuickRepliesAvailable?.([]);
    }
  }, [messages, onQuickRepliesAvailable]);

  React.useEffect(() => {
    const lastMessage = messages[messages.length - 1];
    if (lastMessage?.sender === 'bot' && lastMessage.suggestedReplies) {
      onSuggestedRepliesAvailable?.(lastMessage.suggestedReplies);
    } else if (lastMessage?.sender === 'user') {
      onSuggestedRepliesAvailable?.([]);
    }
  }, [messages, onSuggestedRepliesAvailable]);

  if (messages.length === 0) {
    return (
      <div
        className="message-list message-list--empty"
        role="log"
        aria-live="polite"
        style={{
          flex: 1,
          minHeight: 0,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          padding: 16,
          textAlign: 'center',
          color: theme.textColor,
          opacity: 0.7,
        }}
      >
        <div>
          <svg
            width="48"
            height="48"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
            aria-hidden="true"
            style={{ margin: '0 auto 12px', opacity: 0.5 }}
          >
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
          </svg>
          <p>{welcomeMessage ?? 'Start a conversation'}</p>
        </div>
      </div>
    );
  }

  return (
    <div
      data-testid="message-list"
      className="message-list"
      role="log"
      aria-live="polite"
      aria-label="Chat messages"
      aria-busy={isLoading ? 'true' : 'false'}
      style={{
        flex: 1,
        minHeight: 0,
        overflowY: 'auto',
        padding: 16,
      }}
    >
      {groups.map((group) => (
        <MessageGroupComponent
          key={group.id}
          group={group}
          botName={botName}
          businessName={businessName}
          theme={theme}
          onAddToCart={onAddToCart}
          onProductClick={onProductClick}
          onRemoveFromCart={onRemoveFromCart}
          onCheckout={onCheckout}
          addingProductId={addingProductId}
          removingItemId={removingItemId}
          isCheckingOut={isCheckingOut}
          newMessageIds={newMessageIds}
          reducedMotion={reducedMotion}
          sessionId={sessionId}
          onFeedbackSubmit={onFeedbackSubmit}
        />
      ))}
      <div ref={messagesEndRef} />
    </div>
  );
}

interface MessageGroupComponentProps {
  group: MessageGroup;
  botName: string;
  businessName?: string;
  theme: WidgetTheme;
  onAddToCart?: (product: WidgetProduct) => void;
  onProductClick?: (product: WidgetProduct) => void;
  onRemoveFromCart?: (variantId: string) => void;
  onCheckout?: () => void;
  addingProductId?: string | null;
  removingItemId?: string | null;
  isCheckingOut?: boolean;
  newMessageIds: Set<string>;
  reducedMotion: boolean;
  sessionId?: string;
  onFeedbackSubmit?: (messageId: string, rating: FeedbackRatingValue, comment?: string) => Promise<void>;
}

function MessageGroupComponent({
  group,
  botName,
  businessName,
  theme,
  onAddToCart,
  onProductClick,
  onRemoveFromCart,
  onCheckout,
  addingProductId,
  removingItemId,
  isCheckingOut,
  newMessageIds,
  reducedMotion,
  sessionId,
  onFeedbackSubmit,
}: MessageGroupComponentProps) {
  const isUser = group.sender === 'user';
  const isSystem = group.sender === 'system';
  const showAvatar = !isUser && !isSystem;

  let displayName = botName;
  if (isUser) {
    displayName = group.messages[0]?.customerName || 'User';
  } else if (group.sender === 'merchant') {
    displayName = businessName || 'Merchant';
  } else if (group.sender === 'bot') {
    displayName = botName;
  }

  if (isSystem) {
    return (
      <div
        data-testid="message-group"
        className="message-group"
        role="listitem"
        style={{ marginBottom: 12 }}
      >
        {group.messages.map((message) => (
          <div
            key={message.messageId}
            data-testid="message-bubble"
            className="message-bubble message-bubble--system"
            style={{
              textAlign: 'center',
              color: theme.textColor,
              opacity: 0.7,
              fontSize: 12,
              padding: '4px 8px',
            }}
          >
            <div style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
              {renderMessageContent(message.content)}
            </div>
          </div>
        ))}
      </div>
    );
  }

  return (
    <div
      data-testid="message-group"
      className="message-group"
      role="listitem"
      style={{ marginBottom: 12 }}
    >
      <div
        className={`message-group__row ${isUser ? 'message-group__row--user' : ''}`}
        style={{
          display: 'flex',
          alignItems: 'flex-end',
          gap: 8,
          flexDirection: isUser ? 'row-reverse' : 'row',
        }}
      >
        {showAvatar && (
          <div className="message-group__avatar" style={{ flexShrink: 0 }}>
            <MessageAvatar
              sender={group.sender as 'bot' | 'merchant'}
              botName={botName}
              theme={theme}
              size={32}
            />
          </div>
        )}
        <div
          className="message-group__content"
          style={{
            display: 'flex',
            flexDirection: 'column',
            gap: 4,
            maxWidth: '75%',
          }}
        >
          {group.messages.map((message, index) => {
            const position = getGroupPosition(group, index);
            const isFirst = position === 'first' || position === 'single';
            const isLast = position === 'last' || position === 'single';

            return (
              <div key={message.messageId}>
                <MessageBubbleInGroup
                  message={message}
                  sender={group.sender}
                  position={position}
                  displayName={isFirst ? displayName : undefined}
                  theme={theme}
                  showRichContent={isLast}
                  onAddToCart={onAddToCart}
                  onProductClick={onProductClick}
                  onRemoveFromCart={onRemoveFromCart}
                  onCheckout={onCheckout}
                  addingProductId={addingProductId}
                  removingItemId={removingItemId}
                  isCheckingOut={isCheckingOut}
                  isNew={newMessageIds.has(message.messageId)}
                  reducedMotion={reducedMotion}
                  sessionId={sessionId}
                  onFeedbackSubmit={onFeedbackSubmit}
                />
                {isLast && (
                  <div
                    data-testid="message-timestamp"
                    className={`message-bubble__timestamp message-bubble__timestamp--${isUser ? 'user' : 'bot'}`}
                    title={formatAbsoluteTime(message.createdAt)}
                    style={{
                      fontSize: 10,
                      color: theme.textColor,
                      opacity: 0.5,
                      marginTop: 2,
                      textAlign: isUser ? 'right' : 'left',
                      marginRight: isUser ? 4 : 0,
                      marginLeft: isUser ? 0 : 4,
                    }}
                  >
                    <span data-testid="relative-time">{formatRelativeTime(message.createdAt)}</span>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

interface MessageBubbleInGroupProps {
  message: WidgetMessage;
  sender: 'user' | 'bot' | 'merchant' | 'system';
  position: 'first' | 'middle' | 'last' | 'single';
  displayName?: string;
  theme: WidgetTheme;
  showRichContent: boolean;
  onAddToCart?: (product: WidgetProduct) => void;
  onProductClick?: (product: WidgetProduct) => void;
  onRemoveFromCart?: (variantId: string) => void;
  onCheckout?: () => void;
  addingProductId?: string | null;
  removingItemId?: string | null;
  isCheckingOut?: boolean;
  isNew?: boolean;
  reducedMotion?: boolean;
  sessionId?: string;
  onFeedbackSubmit?: (messageId: string, rating: FeedbackRatingValue, comment?: string) => Promise<void>;
}

function MessageBubbleInGroup({
  message,
  sender,
  position,
  displayName,
  theme,
  showRichContent,
  onAddToCart,
  onProductClick,
  onRemoveFromCart,
  onCheckout,
  addingProductId,
  removingItemId,
  isCheckingOut,
  isNew = false,
  reducedMotion = false,
  sessionId,
  onFeedbackSubmit,
}: MessageBubbleInGroupProps) {
  const isUser = sender === 'user';

  const getBorderRadius = (): string => {
    if (position === 'single') return '16px';
    if (position === 'first') return isUser ? '16px 16px 4px 16px' : '16px 16px 16px 4px';
    if (position === 'middle') return '4px';
    if (position === 'last') return isUser ? '16px 4px 4px 16px' : '4px 4px 16px 16px';
    return '16px';
  };

  // Only animate new user messages
  const shouldAnimate = isNew && isUser && !reducedMotion;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
      <div
        data-testid="message-bubble"
        className={`message-bubble message-bubble--${position} message-bubble--${isUser ? 'user' : 'bot'}`}
        style={{
          padding: '10px 14px',
          borderRadius: getBorderRadius(),
          backgroundColor: isUser ? theme.userBubbleColor : theme.botBubbleColor,
          color: isUser ? 'white' : theme.textColor,
          wordBreak: 'break-word',
          animationName: shouldAnimate ? 'message-send' : 'none',
          animationDuration: shouldAnimate ? '200ms' : '0ms',
          animationTimingFunction: 'ease-out',
          animationFillMode: 'forwards',
        }}
      >
        {displayName && (
          <div
            className="message-bubble__sender"
            style={{
              fontSize: 11,
              fontWeight: 600,
              marginBottom: 4,
              opacity: 0.8,
            }}
          >
            {displayName}
          </div>
        )}
        <div
          className="message-bubble__content"
          style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}
        >
          {renderMessageContent(message.content)}
        </div>
      </div>

      {showRichContent && !isUser && message.products && message.products.length > 0 && (
        <div
          className="message-bubble__rich-content"
          style={{ maxWidth: '100%', marginTop: 8 }}
        >
          {message.products.length >= 3 ? (
            <ProductCarousel
              products={message.products}
              theme={theme}
              onAddToCart={onAddToCart}
              onProductClick={onProductClick}
              addingProductId={addingProductId}
            />
          ) : (
            <ProductList
              products={message.products}
              theme={theme}
              onAddToCart={onAddToCart}
              onProductClick={onProductClick}
              addingProductId={addingProductId}
            />
          )}
        </div>
      )}

      {showRichContent && !isUser && message.cart && (
        <div
          className="message-bubble__rich-content"
          style={{ maxWidth: '100%', marginTop: 8 }}
        >
          <CartView
            cart={message.cart}
            theme={theme}
            onRemoveItem={onRemoveFromCart}
            onCheckout={onCheckout}
            isCheckingOut={isCheckingOut}
            removingItemId={removingItemId}
          />
        </div>
      )}

      {showRichContent && !isUser && message.checkoutUrl && (
        <div style={{ marginTop: 8 }}>
          <a
            href={message.checkoutUrl}
            target="_blank"
            rel="noopener noreferrer"
            style={{
              display: 'inline-block',
              padding: '8px 16px',
              backgroundColor: theme.primaryColor,
              color: 'white',
              textDecoration: 'none',
              borderRadius: 8,
              fontWeight: 500,
              fontSize: 13,
            }}
          >
            Complete Checkout →
          </a>
        </div>
      )}

      {showRichContent && !isUser && message.sources && message.sources.length > 0 && (
        <div className="message-bubble__sources">
          <SourceCitation sources={message.sources} theme={theme} />
        </div>
      )}

      {showRichContent && !isUser && sender === 'bot' && onFeedbackSubmit && (
        <FeedbackRating
          messageId={message.messageId}
          feedbackEnabled={message.feedbackEnabled}
          userRating={message.userRating}
          theme={theme}
          onSubmit={onFeedbackSubmit}
        />
      )}

      {showRichContent && !isUser && message.contactOptions && message.contactOptions.length > 0 && (
        <ContactCard
          contactOptions={message.contactOptions}
          theme={theme}
          conversationId={sessionId}
          onContactClick={() => {}}
        />
      )}
    </div>
  );
}

function renderMessageContent(content: string) {
  const imageRegex = /(📷\s*Image:\s*)?(https?:\/\/[^\s]+?\.(?:jpg|jpeg|png|gif|webp|svg)(?:\?[^\s]*)?)/gi;

  const result: React.ReactNode[] = [];
  let lastIndex = 0;
  let match;

  while ((match = imageRegex.exec(content)) !== null) {
    if (match.index > lastIndex) {
      result.push(content.slice(lastIndex, match.index));
    }

    const fullMatch = match[0];
    const imageUrl = match[2];

    result.push(
      <div key={match.index} style={{ marginTop: 8, marginBottom: 8 }}>
        <img
          src={imageUrl}
          alt="Product"
          style={{
            maxWidth: '100%',
            borderRadius: 8,
            display: 'block',
          }}
          loading="lazy"
        />
      </div>
    );

    lastIndex = match.index + fullMatch.length;
  }

  if (lastIndex < content.length) {
    result.push(content.slice(lastIndex));
  }

  return result.length > 0 ? result : content;
}
