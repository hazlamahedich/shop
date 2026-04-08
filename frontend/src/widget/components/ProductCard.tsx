import * as React from 'react';
import type { WidgetProduct, WidgetTheme, ThemeMode } from '../types/widget';

export interface ProductCardProps {
  product: WidgetProduct;
  theme: WidgetTheme;
  themeMode?: ThemeMode;
  onAddToCart?: (product: WidgetProduct) => void;
  onClick?: (product: WidgetProduct) => void;
  isAdding?: boolean;
}

export function ProductCard({ product, theme, themeMode, onAddToCart, onClick, isAdding }: ProductCardProps) {
  const isDark = themeMode === 'dark';

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
        backgroundColor: isDark ? 'rgba(255, 255, 255, 0.08)' : '#ffffff',
        borderRadius: 12,
        border: product.isPinned ? `2px solid ${theme.primaryColor}` : (isDark ? '1px solid rgba(255, 255, 255, 0.1)' : '1px solid #e5e7eb'),
        marginBottom: 8,
        cursor: onClick ? 'pointer' : 'default',
        transition: 'box-shadow 0.2s, border-color 0.2s',
        position: 'relative',
      }}
    >
      {product.isPinned && (
        <div
          className="featured-badge"
          style={{
            position: 'absolute',
            top: -8,
            left: 8,
            background: theme.primaryColor,
            color: 'white',
            padding: '2px 8px',
            borderRadius: 4,
            fontSize: 10,
            fontWeight: 600,
            display: 'flex',
            alignItems: 'center',
            gap: 3,
            boxShadow: '0 1px 3px rgba(0,0,0,0.2)',
            zIndex: 1,
          }}
        >
          ⭐ Featured
        </div>
      )}
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
              color: isDark ? '#94a3b8' : '#6b7280',
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
  themeMode?: ThemeMode;
  onAddToCart?: (product: WidgetProduct) => void;
  onProductClick?: (product: WidgetProduct) => void;
  addingProductId?: string | null;
}

export function ProductList({ products, theme, themeMode, onAddToCart, onProductClick, addingProductId }: ProductListProps) {
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
          themeMode={themeMode}
          onAddToCart={onAddToCart}
          onClick={onProductClick}
          isAdding={addingProductId === product.id}
        />
      ))}
    </div>
  );
}
