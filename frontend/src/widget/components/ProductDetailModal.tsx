import * as React from 'react';
import type { WidgetProductDetail, WidgetTheme } from '../types/widget';
import { widgetClient, WidgetApiException } from '../api/widgetClient';

export interface ProductDetailModalProps {
  productId: string | null;
  sessionId: string;
  theme: WidgetTheme;
  isOpen: boolean;
  onClose: () => void;
  onAddToCart?: (product: WidgetProductDetail, quantity: number) => void;
}

export function ProductDetailModal({
  productId,
  sessionId,
  theme,
  isOpen,
  onClose,
  onAddToCart,
}: ProductDetailModalProps) {
  const [product, setProduct] = React.useState<WidgetProductDetail | null>(null);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [quantity, setQuantity] = React.useState(1);
  const [added, setAdded] = React.useState(false);

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
        const data = await widgetClient.getProduct(sessionId, productId);
        setProduct(data);
      } catch (err) {
        setError(err instanceof WidgetApiException ? err.message : 'Failed to load product');
      } finally {
        setLoading(false);
      }
    };

    fetchProduct();
  }, [isOpen, productId, sessionId]);

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

  const inStock = product && product.available && (product.inventoryQuantity ?? 0) > 0;
  const maxQuantity = product?.inventoryQuantity ?? 99;

  const handleAddToCartClick = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (!product || !inStock || !onAddToCart) return;
    onAddToCart(product, quantity);
    setAdded(true);
    setTimeout(() => {
      setAdded(false);
      onClose();
    }, 1000);
  };

  const handleCloseClick = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    onClose();
  };

  const handleIncrement = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (quantity < maxQuantity) {
      setQuantity(quantity + 1);
    }
  };

  const handleDecrement = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (quantity > 1) {
      setQuantity(quantity - 1);
    }
  };

  const getStockStatus = () => {
    if (!product) return null;
    if (!product.available) {
      return { text: 'Out of Stock', color: '#dc2626', bg: '#fef2f2' };
    }
    if (product.inventoryQuantity === 0) {
      return { text: 'Out of Stock', color: '#dc2626', bg: '#fef2f2' };
    }
    if (product.inventoryQuantity && product.inventoryQuantity <= 5) {
      return { text: `Only ${product.inventoryQuantity} in stock`, color: '#ea580c', bg: '#fff7ed' };
    }
    if (product.inventoryQuantity && product.inventoryQuantity <= 10) {
      return { text: `${product.inventoryQuantity} in stock`, color: '#ca8a04', bg: '#fefce8' };
    }
    return { text: 'In Stock', color: '#16a34a', bg: '#f0fdf4' };
  };

  const stockStatus = getStockStatus();

  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        zIndex: 2147483647,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '16px',
        backgroundColor: 'rgba(0, 0, 0, 0.5)',
      }}
      onClick={handleBackdropClick}
    >
      <div
        style={{
          backgroundColor: '#ffffff',
          borderRadius: '16px',
          boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
          maxWidth: '400px',
          width: '100%',
          maxHeight: '90vh',
          overflow: 'hidden',
          display: 'flex',
          flexDirection: 'column',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '16px',
            borderBottom: '1px solid #e5e7eb',
          }}
        >
          <h2 style={{ fontSize: '18px', fontWeight: 600, color: '#111827', margin: 0 }}>
            Product Details
          </h2>
          <button
            type="button"
            onClick={handleCloseClick}
            style={{
              padding: '8px',
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              borderRadius: '50%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#9ca3af',
            }}
            aria-label="Close modal"
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M18 6L6 18M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Body */}
        <div style={{ overflowY: 'auto', flex: 1 }}>
          {loading && (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '48px' }}>
              <svg
                style={{ animation: 'spin 1s linear infinite', width: 32, height: 32, color: theme.primaryColor }}
                viewBox="0 0 24 24"
                fill="none"
              >
                <circle style={{ opacity: 0.25 }} cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path style={{ opacity: 0.75 }} fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
            </div>
          )}

          {error && (
            <div style={{ padding: '24px', textAlign: 'center' }}>
              <p style={{ color: '#dc2626', marginBottom: '16px' }}>{error}</p>
              <button
                type="button"
                onClick={handleCloseClick}
                style={{ padding: '8px 16px', fontSize: '14px', color: '#6b7280', background: 'none', border: 'none', cursor: 'pointer' }}
              >
                Close
              </button>
            </div>
          )}

          {product && (
            <div style={{ padding: '16px' }}>
              {/* Image */}
              <div
                style={{
                  position: 'relative',
                  aspectRatio: '1 / 1',
                  backgroundColor: '#f3f4f6',
                  borderRadius: '8px',
                  overflow: 'hidden',
                  marginBottom: '16px',
                }}
              >
                {product.imageUrl ? (
                  <img src={product.imageUrl} alt={product.title} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                ) : (
                  <div style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="#9ca3af" strokeWidth="1.5">
                      <path d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                    </svg>
                  </div>
                )}
              </div>

              {/* Title & Price */}
              <h3 style={{ fontSize: '20px', fontWeight: 600, color: '#111827', marginBottom: '8px' }}>
                {product.title}
              </h3>
              <p style={{ fontSize: '24px', fontWeight: 700, color: theme.primaryColor, marginBottom: '12px' }}>
                ${product.price.toFixed(2)}
              </p>

              {/* Stock Status */}
              {stockStatus && (
                <div
                  style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    padding: '4px 12px',
                    borderRadius: '9999px',
                    fontSize: '12px',
                    fontWeight: 500,
                    backgroundColor: stockStatus.bg,
                    color: stockStatus.color,
                    marginBottom: '12px',
                  }}
                >
                  {stockStatus.text}
                </div>
              )}

              {/* Category/Vendor */}
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '16px', marginBottom: '12px', fontSize: '14px' }}>
                {product.productType && (
                  <div>
                    <span style={{ color: '#6b7280' }}>Category: </span>
                    <span style={{ fontWeight: 500, color: '#111827' }}>{product.productType}</span>
                  </div>
                )}
                {product.vendor && (
                  <div>
                    <span style={{ color: '#6b7280' }}>Vendor: </span>
                    <span style={{ fontWeight: 500, color: '#111827' }}>{product.vendor}</span>
                  </div>
                )}
              </div>

              {/* Description */}
              {product.description && (
                <div style={{ borderTop: '1px solid #e5e7eb', paddingTop: '12px' }}>
                  <h4 style={{ fontSize: '14px', fontWeight: 500, color: '#374151', marginBottom: '8px' }}>Description</h4>
                  <p style={{ fontSize: '14px', color: '#4b5563', lineHeight: 1.6, whiteSpace: 'pre-line' }}>
                    {product.description}
                  </p>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        {product && (
          <div style={{ padding: '16px', borderTop: '1px solid #e5e7eb', backgroundColor: '#f9fafb' }}>
            {inStock && (
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '12px' }}>
                <span style={{ fontSize: '14px', color: '#4b5563' }}>Qty:</span>
                <div style={{ display: 'flex', alignItems: 'center', border: '1px solid #d1d5db', borderRadius: '8px' }}>
                  <button
                    type="button"
                    onClick={handleDecrement}
                    disabled={quantity <= 1}
                    style={{
                      width: '32px',
                      height: '32px',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      background: 'none',
                      border: 'none',
                      borderRight: '1px solid #d1d5db',
                      cursor: quantity <= 1 ? 'not-allowed' : 'pointer',
                      fontSize: '16px',
                      fontWeight: 500,
                      color: '#374151',
                      opacity: quantity <= 1 ? 0.5 : 1,
                    }}
                  >
                    -
                  </button>
                  <span style={{ padding: '0 16px', textAlign: 'center', minWidth: '40px' }}>{quantity}</span>
                  <button
                    type="button"
                    onClick={handleIncrement}
                    disabled={quantity >= maxQuantity}
                    style={{
                      width: '32px',
                      height: '32px',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      background: 'none',
                      border: 'none',
                      borderLeft: '1px solid #d1d5db',
                      cursor: quantity >= maxQuantity ? 'not-allowed' : 'pointer',
                      fontSize: '16px',
                      fontWeight: 500,
                      color: '#374151',
                      opacity: quantity >= maxQuantity ? 0.5 : 1,
                    }}
                  >
                    +
                  </button>
                </div>
              </div>
            )}
            <div style={{ display: 'flex', gap: '8px' }}>
              <button
                type="button"
                onClick={handleAddToCartClick}
                disabled={!inStock || added}
                style={{
                  flex: 1,
                  padding: '10px 16px',
                  borderRadius: '8px',
                  fontWeight: 500,
                  fontSize: '14px',
                  cursor: added || !inStock ? 'not-allowed' : 'pointer',
                  border: 'none',
                  backgroundColor: added ? '#22c55e' : inStock ? theme.primaryColor : '#d1d5db',
                  color: 'white',
                  opacity: added || inStock ? 1 : 0.7,
                }}
              >
                {added ? 'Added to Cart!' : inStock ? 'Add to Cart' : 'Out of Stock'}
              </button>
              <button
                type="button"
                onClick={handleCloseClick}
                style={{
                  padding: '10px 16px',
                  backgroundColor: '#e5e7eb',
                  color: '#374151',
                  borderRadius: '8px',
                  fontWeight: 500,
                  fontSize: '14px',
                  border: 'none',
                  cursor: 'pointer',
                }}
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
