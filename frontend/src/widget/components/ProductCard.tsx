import * as React from 'react';
import type { WidgetProduct, WidgetTheme } from '../types/widget';

export interface ProductCardProps {
  product: WidgetProduct;
  theme: WidgetTheme;
  onAddToCart?: (product: WidgetProduct) => void;
  isAdding?: boolean;
}

export function ProductCard({ product, theme, onAddToCart, isAdding }: ProductCardProps) {
  const handleAddToCart = () => {
    if (onAddToCart && product.available) {
      onAddToCart(product);
    }
  };

  return (
    <div
      className="product-card"
      style={{
        display: 'flex',
        gap: 12,
        padding: 12,
        backgroundColor: '#ffffff',
        borderRadius: 12,
        border: '1px solid #e5e7eb',
        marginBottom: 8,
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
          <div style={{ fontWeight: 600, fontSize: 14 }}>${product.price.toFixed(2)}</div>
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
  addingProductId?: string | null;
}

export function ProductList({ products, theme, onAddToCart, addingProductId }: ProductListProps) {
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
          isAdding={addingProductId === product.id}
        />
      ))}
    </div>
  );
}
