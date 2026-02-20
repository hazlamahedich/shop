/**
 * ProductCard component for preview chat
 *
 * Displays a product with image, title, price, and Add to Cart button.
 * Clicking the card opens the product detail modal.
 */

import * as React from 'react';
import { useCartStore } from '../../stores/cartStore';

export interface ProductCardProps {
  id: string;
  variantId?: string | null;
  title: string;
  imageUrl: string | null;
  price: string;
  available?: boolean;
  inventoryQuantity?: number;
  onClick?: (productId: string) => void;
}

export function ProductCard({
  id,
  variantId,
  title,
  imageUrl,
  price,
  available = true,
  inventoryQuantity = 0,
  onClick,
}: ProductCardProps) {
  const addItem = useCartStore((state) => state.addItem);
  const [added, setAdded] = React.useState(false);

  const inStock = available !== false && inventoryQuantity > 0;

  const handleCardClick = () => {
    if (onClick) {
      onClick(id);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      handleCardClick();
    }
  };

  const handleAddToCart = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (!inStock) return;

    addItem({
      id,
      variantId,
      title,
      price,
      imageUrl,
      inventoryQuantity,
    });

    setAdded(true);
    setTimeout(() => setAdded(false), 1500);
  };

  return (
    <div
      className="product-card bg-white border border-gray-200 rounded-lg overflow-hidden hover:shadow-md hover:border-blue-300 transition-all duration-200"
      onClick={handleCardClick}
      onKeyDown={handleKeyDown}
      tabIndex={0}
      role="button"
      aria-label={`View details for ${title}`}
      data-testid={`product-card-${id}`}
    >
      <div className="relative aspect-square bg-gray-100 cursor-pointer">
        {imageUrl ? (
          <img
            src={imageUrl}
            alt={title}
            className="w-full h-full object-cover"
            loading="lazy"
            onError={(e) => {
              const target = e.target as HTMLImageElement;
              target.style.display = 'none';
              target.nextElementSibling?.classList.remove('hidden');
            }}
          />
        ) : null}
        <div
          className={`absolute inset-0 flex items-center justify-center ${
            imageUrl ? 'hidden' : ''
          }`}
        >
          <svg
            className="w-12 h-12 text-gray-300"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
            />
          </svg>
        </div>

        {!inStock && (
          <div className="absolute top-2 right-2 px-2 py-1 bg-red-500 text-white text-xs font-medium rounded">
            Out of Stock
          </div>
        )}

        {inStock && inventoryQuantity <= 5 && (
          <div className="absolute top-2 right-2 px-2 py-1 bg-orange-500 text-white text-xs font-medium rounded">
            Only {inventoryQuantity} left
          </div>
        )}
      </div>

      <div className="p-3">
        <h4 className="text-sm font-medium text-gray-900 line-clamp-2 mb-1 cursor-pointer" title={title}>
          {title}
        </h4>
        <div className="flex items-center justify-between gap-2">
          <p className="text-lg font-semibold text-blue-600">${price}</p>
          <button
            onClick={handleAddToCart}
            disabled={!inStock}
            className={`px-3 py-1.5 text-xs font-medium rounded transition-colors ${
              added
                ? 'bg-green-500 text-white'
                : inStock
                ? 'bg-blue-600 text-white hover:bg-blue-700'
                : 'bg-gray-300 text-gray-500 cursor-not-allowed'
            }`}
            aria-label={inStock ? `Add ${title} to cart` : 'Out of stock'}
          >
            {added ? 'Added!' : inStock ? 'Add to Cart' : 'Out of Stock'}
          </button>
        </div>
      </div>
    </div>
  );
}
