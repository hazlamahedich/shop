/**
 * MiniCart sidebar component for preview chat
 *
 * Displays cart items with quantity controls, totals, and checkout button.
 * Slides in from the right when opened.
 * Checkout redirects to Shopify cart permalink.
 */

import * as React from 'react';
import { useCartStore, CartItem } from '../../stores/cartStore';
import { getShopDomain, buildCheckoutUrl } from '../../services/productApi';

export interface MiniCartProps {
  merchantId?: number;
}

export function MiniCart({ merchantId }: MiniCartProps) {
  const items = useCartStore((state) => state.items);
  const isOpen = useCartStore((state) => state.isOpen);
  const closeCart = useCartStore((state) => state.closeCart);
  const removeItem = useCartStore((state) => state.removeItem);
  const updateQuantity = useCartStore((state) => state.updateQuantity);
  const clearCart = useCartStore((state) => state.clearCart);
  const getTotal = useCartStore((state) => state.getTotal);

  const total = getTotal();
  const [checkoutLoading, setCheckoutLoading] = React.useState(false);
  const [checkoutError, setCheckoutError] = React.useState<string | null>(null);

  React.useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        closeCart();
      }
    };

    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [isOpen, closeCart]);

  React.useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => {
      document.body.style.overflow = '';
    };
  }, [isOpen]);

  const handleCheckout = async () => {
    if (!merchantId) {
      setCheckoutError('Unable to checkout - please refresh the page');
      return;
    }

    const itemsWithVariant = items.filter(item => item.variantId);
    if (itemsWithVariant.length === 0) {
      setCheckoutError('No items with valid variant IDs. Please remove and re-add items to your cart.');
      return;
    }

    if (itemsWithVariant.length < items.length) {
      setCheckoutError(`${items.length - itemsWithVariant.length} item(s) missing variant info. Try removing and re-adding them.`);
      return;
    }

    setCheckoutLoading(true);
    setCheckoutError(null);

    try {
      const shopDomain = await getShopDomain(merchantId);
      const checkoutItems = itemsWithVariant.map(item => ({
        variantId: item.variantId!,
        quantity: item.quantity,
      }));

      const checkoutUrl = buildCheckoutUrl(shopDomain, checkoutItems);
      
      if (checkoutUrl) {
        clearCart();
        closeCart();
        window.open(checkoutUrl, '_blank');
      } else {
        setCheckoutError('Unable to build checkout URL. Please try again.');
      }
    } catch (err) {
      setCheckoutError(err instanceof Error ? err.message : 'Failed to start checkout');
    } finally {
      setCheckoutLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <>
      <div
        className="fixed inset-0 bg-black bg-opacity-50 z-40"
        onClick={closeCart}
        aria-hidden="true"
      />

      <div
        className="fixed right-0 top-0 h-full w-full max-w-md bg-white shadow-2xl z-50 flex flex-col"
        role="dialog"
        aria-modal="true"
        aria-labelledby="mini-cart-title"
        data-testid="mini-cart"
      >
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
          <h2 id="mini-cart-title" className="text-lg font-semibold text-gray-900">
            Your Cart ({items.length} {items.length === 1 ? 'item' : 'items'})
          </h2>
          <button
            onClick={closeCart}
            className="p-2 text-gray-400 hover:text-gray-600 rounded-full hover:bg-gray-100 transition-colors"
            aria-label="Close cart"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {items.length === 0 ? (
          <div className="flex-1 flex flex-col items-center justify-center p-6">
            <svg className="w-16 h-16 text-gray-300 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z" />
            </svg>
            <p className="text-gray-500 text-center">Your cart is empty</p>
            <p className="text-gray-400 text-sm text-center mt-1">Add some products to get started!</p>
          </div>
        ) : (
          <>
            <div className="flex-1 overflow-y-auto p-4">
              <div className="space-y-4">
                {items.map((item) => (
                  <CartItemRow
                    key={item.id}
                    item={item}
                    onRemove={() => removeItem(item.productId)}
                    onUpdateQuantity={(qty) => updateQuantity(item.productId, qty)}
                  />
                ))}
              </div>
            </div>

            <div className="border-t border-gray-200 p-4 bg-gray-50">
              <div className="flex justify-between items-center mb-4">
                <span className="text-gray-600">Subtotal</span>
                <span className="text-xl font-bold text-gray-900">${total.toFixed(2)}</span>
              </div>

              {checkoutError && (
                <div className="mb-3 p-2 bg-red-50 border border-red-200 rounded text-sm text-red-600">
                  {checkoutError}
                </div>
              )}

              <div className="space-y-2">
                <button
                  onClick={handleCheckout}
                  disabled={checkoutLoading || !merchantId}
                  className="w-full px-4 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                >
                  {checkoutLoading ? (
                    <>
                      <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                      </svg>
                      Processing...
                    </>
                  ) : (
                    'Proceed to Checkout'
                  )}
                </button>
                <button
                  onClick={clearCart}
                  className="w-full px-4 py-2 text-sm text-gray-600 hover:text-gray-800"
                >
                  Clear Cart
                </button>
              </div>

              <p className="text-xs text-gray-500 text-center mt-3">
                You'll be redirected to Shopify to complete your order
              </p>
            </div>
          </>
        )}
      </div>
    </>
  );
}

interface CartItemRowProps {
  item: CartItem;
  onRemove: () => void;
  onUpdateQuantity: (quantity: number) => void;
}

function CartItemRow({ item, onRemove, onUpdateQuantity }: CartItemRowProps) {
  return (
    <div className="flex gap-3 p-3 bg-gray-50 rounded-lg">
      <div className="w-16 h-16 bg-gray-200 rounded-md overflow-hidden flex-shrink-0">
        {item.imageUrl ? (
          <img
            src={item.imageUrl}
            alt={item.title}
            className="w-full h-full object-cover"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center">
            <svg className="w-6 h-6 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
          </div>
        )}
      </div>

      <div className="flex-1 min-w-0">
        <h4 className="text-sm font-medium text-gray-900 truncate" title={item.title}>
          {item.title}
        </h4>
        <p className="text-sm text-blue-600 font-medium">${item.price}</p>

        <div className="flex items-center gap-2 mt-2">
          <div className="flex items-center border border-gray-300 rounded">
            <button
              onClick={() => onUpdateQuantity(item.quantity - 1)}
              className="px-2 py-1 text-gray-600 hover:bg-gray-100"
              aria-label="Decrease quantity"
            >
              -
            </button>
            <span className="px-2 py-1 text-sm min-w-[28px] text-center">{item.quantity}</span>
            <button
              onClick={() => onUpdateQuantity(item.quantity + 1)}
              disabled={item.quantity >= item.maxQuantity}
              className="px-2 py-1 text-gray-600 hover:bg-gray-100 disabled:opacity-50"
              aria-label="Increase quantity"
            >
              +
            </button>
          </div>

          <button
            onClick={onRemove}
            className="text-xs text-red-500 hover:text-red-700"
          >
            Remove
          </button>
        </div>
      </div>

      <div className="text-right">
        <p className="text-sm font-medium text-gray-900">
          ${(parseFloat(item.price) * item.quantity).toFixed(2)}
        </p>
      </div>
    </div>
  );
}
