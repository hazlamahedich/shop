/**
 * MessageBubble component.
 *
 * Story 1.13: Bot Preview Mode
 *
 * Displays a single message in the preview chat.
 * Different styles for user and bot messages.
 * Supports product card rendering for bot responses.
 */

import * as React from 'react';
import { ConfidenceIndicator } from './ConfidenceIndicator';
import { ProductGrid } from './ProductGrid';
import { extractPriceFromText } from '../../services/productApi';
import type { PreviewMessage } from '../../stores/previewStore';

export interface MessageBubbleProps {
  message: PreviewMessage;
  botName: string;
  merchantId?: number;
  onProductClick?: (productId: string) => void;
  availableCategories?: string[];
  className?: string;
}

function formatTimestamp(date: Date): string {
  return new Intl.DateTimeFormat('en-US', {
    hour: 'numeric',
    minute: '2-digit',
  }).format(date);
}

function isProductQuery(messageContent: string): boolean {
  const productPatterns = [
    /products?\s+(under|below|less|cheaper)/i,
    /what.*products?/i,
    /show\s+me/i,
    /do\s+you\s+have/i,
    /available/i,
    /for\s+sale/i,
    /buy/i,
    /shop/i,
    /\$?\d+\s*(or\s+less|dollars?)/i,
    /price\s*range/i,
    /how\s+much/i,
    /cost/i,
    /popular/i,
    /featured/i,
    /recommend/i,
    /best/i,
  ];

  return productPatterns.some(pattern => pattern.test(messageContent));
}

function shouldShowProducts(messageContent: string): boolean {
  const showPatterns = [
    /here('s| are) .* products/i,
    /we have/i,
    /available.*are/i,
    /options.*include/i,
    /check out/i,
    /take a look/i,
    /\$[\d.]+/i,
    /under\s+\$?\d+/i,
    /products/i,
    /snowboard/i,
    /collection/i,
  ];

  return showPatterns.some(pattern => pattern.test(messageContent));
}

function extractProductNamesFromBotResponse(content: string): string[] {
  const productNames: string[] = [];

  const boldWithPrice = /\*\*([^*]+)\*\*\s*\(\$?[\d.,]+\)/g;
  let match;
  while ((match = boldWithPrice.exec(content)) !== null) {
    const name = match[1].trim();
    if (name && name.length > 2) {
      productNames.push(name);
    }
  }

  const bulletPlainWithPrice = /[*-]\s+(.+?)\s*\(\$?[\d.,]+\)/g;
  while ((match = bulletPlainWithPrice.exec(content)) !== null) {
    const name = match[1].trim();
    if (name && name.length > 2 && !productNames.includes(name) && !name.includes('http')) {
      productNames.push(name);
    }
  }

  return [...new Set(productNames)];
}

function extractPriceContext(content: string): number | null {
  const underPattern = /under\s+\$?(\d+)/i;
  const match = content.match(underPattern);
  if (match) {
    return parseFloat(match[1]);
  }
  return null;
}

export function MessageBubble({
  message,
  botName,
  merchantId,
  onProductClick,
  availableCategories = [],
  className = '',
}: MessageBubbleProps) {
  const isUser = message.role === 'user';
  const isBot = message.role === 'bot';

  const showProducts = isBot && merchantId && shouldShowProducts(message.content);

  const productNames = isBot ? extractProductNamesFromBotResponse(message.content) : [];
  const botPriceContext = isBot ? extractPriceContext(message.content) : null;

  const [trackedMaxPrice, setTrackedMaxPrice] = React.useState<number | null>(null);

  React.useEffect(() => {
    if (isUser && isProductQuery(message.content)) {
      const price = extractPriceFromText(message.content);
      if (price) {
        setTrackedMaxPrice(price);
      } else {
        setTrackedMaxPrice(null);
      }
    }
  }, [isUser, message.content]);

  const effectiveMaxPrice = botPriceContext ?? trackedMaxPrice ?? undefined;

  return (
    <div
      className={`message-bubble flex flex-col ${isUser ? 'items-end' : 'items-start'} mb-4 ${className}`}
      role="listitem"
      data-testid={isBot ? "bot-response" : "user-message"}
    >
      <div
        className={`max-w-[85%] rounded-lg px-4 py-2 ${
          isUser
            ? 'bg-blue-500 text-white rounded-br-sm'
            : 'bg-gray-100 text-gray-800 rounded-bl-sm'
        }`}
      >
        {isBot && (
          <div className="text-xs font-semibold text-gray-600 mb-1">
            {botName}
          </div>
        )}

        <p className="text-sm whitespace-pre-wrap break-words">
          {message.content}
        </p>

        <div className={`text-xs mt-1 ${isUser ? 'text-blue-100' : 'text-gray-500'}`}>
          {formatTimestamp(message.timestamp)}
        </div>

        {isBot && message.confidence !== undefined && (
          <div className="mt-2">
            <ConfidenceIndicator
              confidence={message.confidence}
              confidenceLevel={message.confidenceLevel || 'medium'}
              metadata={message.metadata}
            />
          </div>
        )}
      </div>

      {showProducts && merchantId && (
        <div className="max-w-[85%] w-full mt-1">
          {productNames.length > 0 ? (
            <div className="space-y-3">
              {productNames.slice(0, 3).map((name, index) => (
                <ProductGrid
                  key={`product-${name}-${index}`}
                  merchantId={merchantId}
                  maxPrice={effectiveMaxPrice}
                  query={name}
                  limit={3}
                  onProductClick={onProductClick}
                />
              ))}
            </div>
          ) : (
            <ProductGrid
              merchantId={merchantId}
              maxPrice={effectiveMaxPrice}
              limit={6}
              onProductClick={onProductClick}
            />
          )}
        </div>
      )}
    </div>
  );
}
