/**
 * ProductGrid component for preview chat
 *
 * Displays a grid of product cards with loading and error states.
 */

import * as React from 'react';
import { ProductCard } from './ProductCard';
import { searchProducts, PreviewProduct } from '../../services/productApi';

export interface ProductGridProps {
  merchantId: number;
  maxPrice?: number;
  category?: string;
  query?: string;
  limit?: number;
  onProductClick?: (productId: string) => void;
}

export function ProductGrid({
  merchantId,
  maxPrice,
  category,
  query,
  limit = 6,
  onProductClick,
}: ProductGridProps) {
  const [products, setProducts] = React.useState<PreviewProduct[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    const fetchProducts = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await searchProducts(merchantId, {
          maxPrice,
          category,
          query,
          limit,
        });
        setProducts(response.products);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load products');
      } finally {
        setLoading(false);
      }
    };

    fetchProducts();
  }, [merchantId, maxPrice, category, query, limit]);

  if (loading) {
    return (
      <div className="product-grid-loading flex items-center justify-center py-4">
        <svg className="animate-spin h-6 w-6 text-gray-400" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
        </svg>
      </div>
    );
  }

  if (error) {
    return (
      <div className="product-grid-error text-center py-4 text-sm text-red-600">
        {error}
      </div>
    );
  }

  if (products.length === 0) {
    return null;
  }

  return (
    <div className="product-grid mt-3" data-testid="product-grid">
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
        {products.map((product) => (
          <ProductCard
            key={product.id}
            id={product.id}
            variantId={product.variant_id}
            title={product.title}
            imageUrl={product.image_url}
            price={product.price}
            available={product.available}
            inventoryQuantity={product.inventory_quantity}
            onClick={onProductClick}
          />
        ))}
      </div>
    </div>
  );
}
