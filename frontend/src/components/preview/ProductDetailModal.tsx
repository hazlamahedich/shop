/**
 * ProductDetailModal component for preview chat
 *
 * Displays full product information including image, description,
 * price, and inventory when a user clicks on a product card.
 * Includes Add to Cart functionality.
 */

import * as React from 'react';
import { PreviewProduct, getProduct } from '../../services/productApi';
import { useCartStore } from '../../stores/cartStore';

export interface ProductDetailModalProps {
  productId: string | null;
  merchantId: number;
  isOpen: boolean;
  onClose: () => void;
}

export function ProductDetailModal({
  productId,
  merchantId,
  isOpen,
  onClose,
}: ProductDetailModalProps) {
  const [product, setProduct] = React.useState<PreviewProduct | null>(null);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [quantity, setQuantity] = React.useState(1);
  const [added, setAdded] = React.useState(false);

  const addItem = useCartStore((state) => state.addItem);

  React.useEffect(() => {
    if (!isOpen || !productId) {
      setProduct(null);
      setError(null);
      setQuantity(1);
      setAdded(false);
      return;
    }

    const fetchProduct = async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await getProduct(merchantId, productId);
        setProduct(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load product');
      } finally {
        setLoading(false);
      }
    };

    fetchProduct();
  }, [isOpen, productId, merchantId]);

  React.useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };

    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [isOpen, onClose]);

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

  if (!isOpen) return null;

  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  const inStock = product && product.available && (product.inventory_quantity ?? 0) > 0;
  const maxQuantity = product?.inventory_quantity ?? 99;

  const handleAddToCart = () => {
    if (!product || !inStock) return;

    addItem({
      id: product.id,
      variantId: product.variant_id,
      title: product.title,
      price: product.price,
      imageUrl: product.image_url,
      inventoryQuantity: product.inventory_quantity,
    });

    setAdded(true);
    setTimeout(() => {
      setAdded(false);
      onClose();
    }, 1000);
  };

  const incrementQuantity = () => {
    if (quantity < maxQuantity) {
      setQuantity(quantity + 1);
    }
  };

  const decrementQuantity = () => {
    if (quantity > 1) {
      setQuantity(quantity - 1);
    }
  };

  const getStockStatus = () => {
    if (!product) return null;
    
    if (!product.available) {
      return { text: 'Out of Stock', color: 'text-red-600', bg: 'bg-red-100' };
    }
    
    if (product.inventory_quantity === 0) {
      return { text: 'Out of Stock', color: 'text-red-600', bg: 'bg-red-100' };
    }
    
    if (product.inventory_quantity <= 5) {
      return { text: `Only ${product.inventory_quantity} in stock`, color: 'text-orange-600', bg: 'bg-orange-100' };
    }
    
    if (product.inventory_quantity <= 10) {
      return { text: `${product.inventory_quantity} in stock`, color: 'text-yellow-600', bg: 'bg-yellow-100' };
    }
    
    return { text: 'In Stock', color: 'text-green-600', bg: 'bg-green-100' };
  };

  const stockStatus = getStockStatus();

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black bg-opacity-50"
      onClick={handleBackdropClick}
      role="dialog"
      aria-modal="true"
      aria-labelledby="product-modal-title"
      data-testid="product-detail-modal"
    >
      <div className="bg-white rounded-xl shadow-2xl max-w-lg w-full max-h-[90vh] overflow-hidden flex flex-col">
        <div className="flex items-center justify-between p-4 border-b border-gray-200 flex-shrink-0">
          <h2 id="product-modal-title" className="text-lg font-semibold text-gray-900">
            Product Details
          </h2>
          <button
            onClick={onClose}
            className="p-2 text-gray-400 hover:text-gray-600 rounded-full hover:bg-gray-100 transition-colors"
            aria-label="Close modal"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="overflow-y-auto flex-1">
          {loading && (
            <div className="flex items-center justify-center p-12">
              <svg className="animate-spin h-8 w-8 text-blue-500" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
            </div>
          )}

          {error && (
            <div className="p-6 text-center">
              <p className="text-red-600">{error}</p>
              <button
                onClick={onClose}
                className="mt-4 px-4 py-2 text-sm text-gray-600 hover:text-gray-800"
              >
                Close
              </button>
            </div>
          )}

          {product && (
            <div className="p-6">
              {/* Product Image */}
              <div className="relative aspect-square bg-gray-100 rounded-lg overflow-hidden mb-6">
                {product.image_url ? (
                  <img
                    src={product.image_url}
                    alt={product.title}
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <div className="absolute inset-0 flex items-center justify-center">
                    <svg className="w-16 h-16 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                    </svg>
                  </div>
                )}
              </div>

              {/* Product Title */}
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                {product.title}
              </h3>

              {/* Price */}
              <p className="text-2xl font-bold text-blue-600 mb-4">
                ${product.price}
              </p>

              {/* Stock Status */}
              {stockStatus && (
                <div className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${stockStatus.bg} ${stockStatus.color} mb-4`}>
                  {stockStatus.text}
                </div>
              )}

              {/* Product Type & Vendor */}
              <div className="flex flex-wrap gap-4 mb-4 text-sm">
                {product.product_type && (
                  <div>
                    <span className="text-gray-500">Category:</span>{' '}
                    <span className="font-medium text-gray-900">{product.product_type}</span>
                  </div>
                )}
                {product.vendor && (
                  <div>
                    <span className="text-gray-500">Vendor:</span>{' '}
                    <span className="font-medium text-gray-900">{product.vendor}</span>
                  </div>
                )}
              </div>

              {/* Description */}
              {product.description && (
                <div className="border-t border-gray-200 pt-4">
                  <h4 className="text-sm font-medium text-gray-700 mb-2">Description</h4>
                  <p className="text-sm text-gray-600 leading-relaxed whitespace-pre-line">
                    {product.description}
                  </p>
                </div>
              )}
            </div>
          )}
        </div>

        {product && (
          <div className="p-4 border-t border-gray-200 bg-gray-50 flex-shrink-0">
            {inStock && (
              <div className="flex items-center gap-4 mb-3">
                <span className="text-sm text-gray-600">Qty:</span>
                <div className="flex items-center border border-gray-300 rounded-lg">
                  <button
                    onClick={decrementQuantity}
                    disabled={quantity <= 1}
                    className="px-3 py-1 text-gray-600 hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
                    aria-label="Decrease quantity"
                  >
                    -
                  </button>
                  <span className="px-4 py-1 text-center min-w-[40px]">{quantity}</span>
                  <button
                    onClick={incrementQuantity}
                    disabled={quantity >= maxQuantity}
                    className="px-3 py-1 text-gray-600 hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
                    aria-label="Increase quantity"
                  >
                    +
                  </button>
                </div>
              </div>
            )}
            <div className="flex gap-2">
              <button
                onClick={handleAddToCart}
                disabled={!inStock || added}
                className={`flex-1 px-4 py-2 rounded-lg font-medium transition-colors ${
                  added
                    ? 'bg-green-500 text-white'
                    : inStock
                    ? 'bg-blue-600 text-white hover:bg-blue-700'
                    : 'bg-gray-300 text-gray-500 cursor-not-allowed'
                }`}
              >
                {added ? 'Added to Cart!' : inStock ? 'Add to Cart' : 'Out of Stock'}
              </button>
              <button
                onClick={onClose}
                className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors font-medium"
              >
                Close
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
