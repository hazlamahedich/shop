import * as React from 'react';
import type { WidgetTheme, WidgetMessage, WidgetProduct } from '../types/widget';
import { ProductList } from './ProductCard';
import { CartView } from './CartView';

export interface MessageListProps {
  messages: WidgetMessage[];
  botName: string;
  welcomeMessage?: string;
  theme: WidgetTheme;
  isLoading?: boolean;
  onAddToCart?: (product: WidgetProduct) => void;
  onRemoveFromCart?: (variantId: string) => void;
  onCheckout?: () => void;
  addingProductId?: string | null;
  removingItemId?: string | null;
  isCheckingOut?: boolean;
}

export function MessageList({
  messages,
  botName,
  welcomeMessage,
  theme,
  isLoading,
  onAddToCart,
  onRemoveFromCart,
  onCheckout,
  addingProductId,
  removingItemId,
  isCheckingOut,
}: MessageListProps) {
  const messagesEndRef = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  if (messages.length === 0) {
    return (
      <div
        className="message-list message-list--empty"
        role="log"
        aria-live="polite"
        style={{
          flex: 1,
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
      className="message-list"
      role="log"
      aria-live="polite"
      aria-label="Chat messages"
      aria-busy={isLoading ? 'true' : 'false'}
      style={{
        flex: 1,
        overflowY: 'auto',
        padding: 16,
      }}
    >
      {messages.map((message) => (
        <MessageBubble
          key={message.messageId}
          message={message}
          botName={botName}
          theme={theme}
          onAddToCart={onAddToCart}
          onRemoveFromCart={onRemoveFromCart}
          onCheckout={onCheckout}
          addingProductId={addingProductId}
          removingItemId={removingItemId}
          isCheckingOut={isCheckingOut}
        />
      ))}
      <div ref={messagesEndRef} />
    </div>
  );
}

interface MessageBubbleProps {
  message: WidgetMessage;
  botName: string;
  theme: WidgetTheme;
  onAddToCart?: (product: WidgetProduct) => void;
  onRemoveFromCart?: (variantId: string) => void;
  onCheckout?: () => void;
  addingProductId?: string | null;
  removingItemId?: string | null;
  isCheckingOut?: boolean;
}

function MessageBubble({
  message,
  botName,
  theme,
  onAddToCart,
  onRemoveFromCart,
  onCheckout,
  addingProductId,
  removingItemId,
  isCheckingOut,
}: MessageBubbleProps) {
  const isUser = message.sender === 'user';

  return (
    <div
      className={`message-bubble message-bubble--${message.sender}`}
      role="listitem"
      style={{
        marginBottom: 12,
      }}
    >
      <div
        style={{
          display: 'flex',
          justifyContent: isUser ? 'flex-end' : 'flex-start',
        }}
      >
        <div
          style={{
            maxWidth: '75%',
            padding: '10px 14px',
            borderRadius: 16,
            backgroundColor: isUser ? theme.userBubbleColor : theme.botBubbleColor,
            color: isUser ? 'white' : theme.textColor,
            borderBottomRightRadius: isUser ? 4 : 16,
            borderBottomLeftRadius: isUser ? 16 : 4,
          }}
        >
          {!isUser && (
            <div
              style={{
                fontSize: 11,
                fontWeight: 600,
                marginBottom: 4,
                opacity: 0.8,
              }}
            >
              {botName}
            </div>
          )}
          <div style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
            {message.content}
          </div>
        </div>
      </div>

      {!isUser && message.products && message.products.length > 0 && (
        <div style={{ maxWidth: '100%', marginTop: 8 }}>
          <ProductList
            products={message.products}
            theme={theme}
            onAddToCart={onAddToCart}
            addingProductId={addingProductId}
          />
        </div>
      )}

      {!isUser && message.cart && (
        <div style={{ maxWidth: '100%', marginTop: 8 }}>
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

      {!isUser && message.checkoutUrl && (
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
    </div>
  );
}
