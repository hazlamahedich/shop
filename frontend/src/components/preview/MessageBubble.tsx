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

function shouldShowProducts(message: PreviewMessage): boolean {
  // If message has products from backend, always show them
  if (message.products && message.products.length > 0) {
    return true;
  }
  
  // Otherwise, check message content for product-related patterns
  const content = message.content;
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

  return showPatterns.some(pattern => pattern.test(content));
}

function extractProductNamesFromBotResponse(content: string): string[] {
  const productNames: string[] = [];

  // Match **Bold Name** ($price) or **Bold Name** for $price
  const boldWithPrice = /\*\*([^*]+)\*\*\s*(?:\(|for\s+)\$?[\d.,]+/g;
  let match;
  while ((match = boldWithPrice.exec(content)) !== null) {
    const name = match[1].trim();
    if (name && name.length > 2) {
      productNames.push(name);
    }
  }

  // Match bullet points with prices: * Name ($price) or - Name ($price)
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
  const patterns = [
    /under\s+\$?(\d+)/i,
    /below\s+\$?(\d+)/i,
    /less\s+than\s+\$?(\d+)/i,
    /budget\s+(?:of\s+)?\$?(\d+)/i,
    /\$?(\d+)\s+(?:dollars?|or\s+less)/i,
  ];
  
  for (const pattern of patterns) {
    const match = content.match(pattern);
    if (match) {
      return parseFloat(match[1]);
    }
  }
  return null;
}

const PRICE_CONTEXT_KEY = 'preview_price_context';

function getPriceContext(): number | null {
  try {
    const stored = sessionStorage.getItem(PRICE_CONTEXT_KEY);
    if (stored) {
      const { price, timestamp } = JSON.parse(stored);
      if (Date.now() - timestamp < 5 * 60 * 1000) {
        return price;
      }
    }
  } catch {}
  return null;
}

function setPriceContext(price: number): void {
  try {
    sessionStorage.setItem(PRICE_CONTEXT_KEY, JSON.stringify({ price, timestamp: Date.now() }));
  } catch {}
}

function clearPriceContext(): void {
  try {
    sessionStorage.removeItem(PRICE_CONTEXT_KEY);
  } catch {}
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

  // Check if we have products from backend (preferred) or need to fetch
  const hasProductsFromBackend = isBot && message.products && message.products.length > 0;
  const showProducts = isBot && merchantId && (hasProductsFromBackend || shouldShowProducts(message));

  const productNames = isBot && !hasProductsFromBackend ? extractProductNamesFromBotResponse(message.content) : [];
  const botPriceContext = isBot ? extractPriceContext(message.content) : null;

  // Track price from user messages and persist across messages
  React.useEffect(() => {
    if (isUser && isProductQuery(message.content)) {
      const price = extractPriceFromText(message.content);
      if (price) {
        setPriceContext(price);
      } else {
        clearPriceContext();
      }
    } else if (isUser) {
      clearPriceContext();
    }
  }, [isUser, message.content]);

  const effectiveMaxPrice = botPriceContext ?? getPriceContext() ?? undefined;

  // Render products directly from backend response
  const renderProductsFromBackend = () => {
    if (!message.products || message.products.length === 0) return null;
    
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {message.products.slice(0, 5).map((product) => (
          <div
            key={product.product_id}
            className="border rounded-lg p-3 bg-white shadow-sm hover:shadow-md transition-shadow cursor-pointer"
            onClick={() => onProductClick?.(product.product_id)}
          >
            {product.image_url && (
              <img
                src={product.image_url}
                alt={product.title}
                className="w-full h-32 object-contain rounded mb-2 bg-gray-50"
              />
            )}
            <h4 className="font-medium text-sm text-gray-900 line-clamp-2">
              {product.title}
            </h4>
            {product.price !== null && (
              <p className="text-sm font-semibold text-gray-700 mt-1">
                ${product.price.toFixed(2)}
              </p>
            )}
            <button
              className="mt-2 w-full text-xs bg-blue-500 text-white py-1.5 px-3 rounded hover:bg-blue-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              disabled={!product.available}
            >
              {product.available ? 'Add to Cart' : 'Out of Stock'}
            </button>
          </div>
        ))}
      </div>
    );
  };

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

      {showProducts && (
        <div className="max-w-[85%] w-full mt-1">
          {hasProductsFromBackend ? (
            renderProductsFromBackend()
          ) : productNames.length > 0 ? (
            <div className="space-y-3">
              {productNames.slice(0, 3).map((name, index) => (
                <ProductGrid
                  key={`product-${name}-${index}`}
                  merchantId={merchantId!}
                  maxPrice={effectiveMaxPrice}
                  query={name}
                  limit={3}
                  onProductClick={onProductClick}
                />
              ))}
            </div>
          ) : (
            <ProductGrid
              merchantId={merchantId!}
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
