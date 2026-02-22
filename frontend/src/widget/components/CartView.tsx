import * as React from 'react';
import type { WidgetCart, WidgetCartItem, WidgetTheme } from '../types/widget';

export interface CartViewProps {
  cart: WidgetCart;
  theme: WidgetTheme;
  onRemoveItem?: (variantId: string) => void;
  onCheckout?: () => void;
  isCheckingOut?: boolean;
  removingItemId?: string | null;
}

export function CartView({
  cart,
  theme,
  onRemoveItem,
  onCheckout,
  isCheckingOut,
  removingItemId,
}: CartViewProps) {
  if (cart.items.length === 0) {
    return (
      <div
        className="cart-view cart-view--empty"
        style={{
          padding: 16,
          textAlign: 'center',
          color: '#6b7280',
          fontSize: 13,
        }}
      >
        Your cart is empty
      </div>
    );
  }

  return (
    <div
      className="cart-view"
      style={{
        backgroundColor: '#f9fafb',
        borderRadius: 12,
        padding: 12,
        marginTop: 8,
      }}
    >
      <div
        style={{
          fontSize: 13,
          fontWeight: 600,
          marginBottom: 12,
          display: 'flex',
          alignItems: 'center',
          gap: 8,
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
        >
          <circle cx="9" cy="21" r="1" />
          <circle cx="20" cy="21" r="1" />
          <path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6" />
        </svg>
        Your Cart ({cart.itemCount} {cart.itemCount === 1 ? 'item' : 'items'})
      </div>

      {cart.items.map((item) => (
        <CartItemView
          key={item.variantId}
          item={item}
          onRemove={onRemoveItem}
          isRemoving={removingItemId === item.variantId}
        />
      ))}

      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginTop: 12,
          paddingTop: 12,
          borderTop: '1px solid #e5e7eb',
        }}
      >
        <div style={{ fontWeight: 600 }}>Total: ${(cart.total ?? 0).toFixed(2)}</div>
        <div style={{ display: 'flex', gap: 8 }}>
          {cart.shopifyCartUrl && (
            <a
              href={cart.shopifyCartUrl}
              target="_blank"
              rel="noopener noreferrer"
              style={{
                padding: '8px 16px',
                fontSize: 13,
                fontWeight: 500,
                backgroundColor: 'transparent',
                color: theme.primaryColor,
                border: `1px solid ${theme.primaryColor}`,
                borderRadius: 8,
                textDecoration: 'none',
                display: 'flex',
                alignItems: 'center',
                gap: 4,
              }}
            >
              <svg
                width="14"
                height="14"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
                <polyline points="15 3 21 3 21 9" />
                <line x1="10" y1="14" x2="21" y2="3" />
              </svg>
              View on Store
            </a>
          )}
          {onCheckout && (
            <button
              type="button"
              onClick={onCheckout}
              disabled={isCheckingOut}
              style={{
                padding: '8px 16px',
                fontSize: 13,
                fontWeight: 500,
                backgroundColor: theme.primaryColor,
                color: 'white',
                border: 'none',
                borderRadius: 8,
                cursor: 'pointer',
                opacity: isCheckingOut ? 0.7 : 1,
              }}
            >
              {isCheckingOut ? 'Processing...' : 'Checkout'}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

interface CartItemViewProps {
  item: WidgetCartItem;
  onRemove?: (variantId: string) => void;
  isRemoving?: boolean;
}

function CartItemView({ item, onRemove, isRemoving }: CartItemViewProps) {
  return (
    <div
      className="cart-item"
      style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        padding: '8px 0',
        borderBottom: '1px solid #e5e7eb',
      }}
    >
      <div style={{ flex: 1, minWidth: 0 }}>
        <div
          style={{
            fontSize: 13,
            fontWeight: 500,
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap',
          }}
        >
          {item.title}
        </div>
        <div style={{ fontSize: 12, color: '#6b7280' }}>
          Qty: {item.quantity} × ${(item.price ?? 0).toFixed(2)}
        </div>
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        <div style={{ fontWeight: 500, fontSize: 13 }}>
          ${((item.price ?? 0) * item.quantity).toFixed(2)}
        </div>
        {onRemove && (
          <button
            type="button"
            onClick={() => onRemove(item.variantId)}
            disabled={isRemoving}
            style={{
              padding: 4,
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              opacity: isRemoving ? 0.5 : 1,
            }}
            aria-label={`Remove ${item.title}`}
          >
            <svg
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="#ef4444"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <polyline points="3 6 5 6 21 6" />
              <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
            </svg>
          </button>
        )}
      </div>
    </div>
  );
}
