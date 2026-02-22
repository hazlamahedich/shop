import * as React from 'react';
import type { WidgetProduct, WidgetTheme } from '../types/widget';

export interface ProductCardProps {
  product: WidgetProduct;
  theme: WidgetTheme;
  onAddToCart?: (product: WidgetProduct) => void;
  onClick?: (product: WidgetProduct) => void;
  isAdding?: boolean;
}

export function ProductCard({ product, theme, onAddToCart, onClick, isAdding }: ProductCardProps) {
  const handleCardClick = () => {
    if (onClick && product.available) {
      onClick(product);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if ((e.key === 'Enter' || e.key === ' ') && onClick && product.available) {
      e.preventDefault();
      onClick(product);
    }
  };

  const handleAddToCart = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (onAddToCart && product.available) {
      onAddToCart(product);
    }
  };

  return (
    <div
      className="product-card"
      onClick={handleCardClick}
      onKeyDown={handleKeyDown}
      tabIndex={onClick ? 0 : undefined}
      role={onClick ? 'button' : undefined}
      aria-label={onClick ? `View details for ${product.title}` : undefined}
      style={{
        display: 'flex',
        gap: 12,
        padding: 12,
        backgroundColor: '#ffffff',
        borderRadius: 12,
        border: '1px solid #e5e7eb',
        marginBottom: 8,
        cursor: onClick ? 'pointer' : 'default',
        transition: 'box-shadow 0.2s, border-color 0.2s',
      }}
    >
      {product.imageUrl && (
        <img
          src={product.imageUrl}
          alt={product.title}
          style={{
            width: 64,
            height: 64,
            objectFit: 'cover',
            borderRadius: 8,
            flexShrink: 0,
          }}
        />
      )}
      <div style={{ flex: 1, minWidth: 0 }}>
        <div
          style={{
            fontWeight: 500,
            fontSize: 13,
            marginBottom: 4,
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap',
          }}
        >
          {product.title}
        </div>
        {product.productType && (
          <div
            style={{
              fontSize: 11,
              color: '#6b7280',
              marginBottom: 4,
            }}
          >
            {product.productType}
          </div>
        )}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: 8,
          }}
        >
          <div style={{ fontWeight: 600, fontSize: 14 }}>${(product.price ?? 0).toFixed(2)}</div>
          {onAddToCart && (
            <button
              type="button"
              onClick={handleAddToCart}
              disabled={!product.available || isAdding}
              style={{
                padding: '6px 12px',
                fontSize: 12,
                fontWeight: 500,
                backgroundColor: product.available ? theme.primaryColor : '#9ca3af',
                color: 'white',
                border: 'none',
                borderRadius: 8,
                cursor: product.available ? 'pointer' : 'not-allowed',
                opacity: isAdding ? 0.7 : 1,
              }}
            >
              {isAdding ? 'Adding...' : product.available ? 'Add to Cart' : 'Sold Out'}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

export interface ProductListProps {
  products: WidgetProduct[];
  theme: WidgetTheme;
  onAddToCart?: (product: WidgetProduct) => void;
  onProductClick?: (product: WidgetProduct) => void;
  addingProductId?: string | null;
}

export function ProductList({ products, theme, onAddToCart, onProductClick, addingProductId }: ProductListProps) {
  if (products.length === 0) {
    return null;
  }

  return (
    <div className="product-list" style={{ marginTop: 8 }}>
      {products.map((product) => (
        <ProductCard
          key={product.id}
          product={product}
          theme={theme}
          onAddToCart={onAddToCart}
          onClick={onProductClick}
          isAdding={addingProductId === product.id}
        />
      ))}
    </div>
  );
}
