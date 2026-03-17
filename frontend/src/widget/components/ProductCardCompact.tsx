import * as React from 'react';
import type { WidgetProduct, WidgetTheme } from '../types/widget';
import { useRipple } from '../hooks/useRipple';
import { useReducedMotion } from '../hooks/useReducedMotion';

export interface ProductCardCompactProps {
  product: WidgetProduct;
  theme: WidgetTheme;
  onAddToCart?: (product: WidgetProduct) => void;
  onClick?: (product: WidgetProduct) => void;
  isAdding?: boolean;
  cardWidth: number;
}

export function ProductCardCompact({
  product,
  theme,
  onAddToCart,
  onClick,
  isAdding,
  cardWidth,
}: ProductCardCompactProps) {
  const [imageLoaded, setImageLoaded] = React.useState(false);
  const [imageError, setImageError] = React.useState(false);
  const { ripples, createRipple } = useRipple();
  const reducedMotion = useReducedMotion();

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
      createRipple(e as React.MouseEvent<HTMLElement>);
      onAddToCart(product);
    }
  };

  const handleImageLoad = () => {
    setImageLoaded(true);
  };

  const handleImageError = () => {
    setImageError(true);
    setImageLoaded(true);
  };

  return (
    <div
      className="carousel-card"
      data-testid={`carousel-card-${product.id}`}
      onClick={handleCardClick}
      onKeyDown={handleKeyDown}
      tabIndex={onClick ? 0 : undefined}
      role="group"
      aria-label={`${product.title}, $${(product.price ?? 0).toFixed(2)}`}
      style={{
        width: cardWidth,
      }}
    >
      <div className="carousel-card-image" data-testid={`carousel-card-image-${product.id}`}>
        {!imageLoaded && !imageError && <div className="carousel-card-skeleton" data-testid="carousel-card-skeleton" aria-hidden="true" />}
        {product.imageUrl && (
          <img
            src={product.imageUrl}
            alt={product.title}
            className={imageLoaded ? '' : 'loading'}
            onLoad={handleImageLoad}
            onError={handleImageError}
            loading="lazy"
          />
        )}
        {imageError && (
          <div
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              width: '100%',
              height: '100%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              background: 'var(--widget-skeleton-bg, #f1f5f9)',
              color: 'var(--widget-text-muted, #94a3b8)',
              fontSize: 24,
            }}
            aria-hidden="true"
          >
            📦
          </div>
        )}
        {product.isPinned && (
          <div
            style={{
              position: 'absolute',
              top: 4,
              left: 4,
              background: theme.primaryColor,
              color: 'white',
              padding: '2px 6px',
              borderRadius: 4,
              fontSize: 10,
              fontWeight: 600,
              zIndex: 1,
            }}
            aria-label="Featured product"
          >
            ⭐
          </div>
        )}
      </div>
      <div className="carousel-card-content">
        <h4 className="carousel-card-title">{product.title}</h4>
        <p className="carousel-card-price">${(product.price ?? 0).toFixed(2)}</p>
        {onAddToCart && (
          <button
            type="button"
            className="carousel-card-button"
            data-testid={`carousel-card-button-${product.id}`}
            onClick={handleAddToCart}
            disabled={!product.available || isAdding}
            aria-label={isAdding ? 'Adding to cart' : product.available ? `Add ${product.title} to cart` : 'Sold out'}
            style={{
              position: 'relative',
              overflow: 'hidden',
            }}
          >
            {isAdding ? 'Adding...' : product.available ? 'Add to Cart' : 'Sold Out'}
            {/* Ripple effects */}
            {ripples.map((ripple) => (
              <span
                key={ripple.id}
                data-testid="ripple-effect"
                style={{
                  position: 'absolute',
                  left: ripple.x,
                  top: ripple.y,
                  width: 10,
                  height: 10,
                  borderRadius: '50%',
                  backgroundColor: 'rgba(255, 255, 255, 0.3)',
                  transform: 'translate(-50%, -50%)',
                  pointerEvents: 'none',
                  animationName: reducedMotion ? 'none' : 'ripple',
                  animationDuration: reducedMotion ? '0ms' : '600ms',
                  animationTimingFunction: 'ease-out',
                  animationFillMode: 'forwards',
                }}
              />
            ))}
          </button>
        )}
      </div>
    </div>
  );
}
