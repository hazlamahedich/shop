/**
 * Cart Store for Preview Mode
 *
 * Zustand store for managing shopping cart state in preview mode.
 * This is a MOCK cart - it does not create real Shopify orders.
 *
 * State:
 * - items: Array of cart items with product and quantity
 * - isOpen: Whether the mini cart sidebar is visible
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export interface CartItem {
  id: string;
  productId: string;
  variantId: string | null;
  title: string;
  price: string;
  imageUrl: string | null;
  quantity: number;
  maxQuantity: number;
}

interface CartState {
  items: CartItem[];
  isOpen: boolean;

  addItem: (product: {
    id: string;
    variantId?: string | null;
    title: string;
    price: string;
    imageUrl: string | null;
    inventoryQuantity?: number;
  }) => void;
  removeItem: (productId: string) => void;
  updateQuantity: (productId: string, quantity: number) => void;
  clearCart: () => void;
  openCart: () => void;
  closeCart: () => void;
  toggleCart: () => void;

  getItemCount: () => number;
  getTotal: () => number;
}

export const useCartStore = create<CartState>()(
  persist(
    (set, get) => ({
      items: [],
      isOpen: false,

      addItem: (product) => {
        const { items } = get();
        const existingItem = items.find((item) => item.productId === product.id);

        if (existingItem) {
          const maxQty = product.inventoryQuantity ?? 99;
          const newQty = Math.min(existingItem.quantity + 1, maxQty);

          if (newQty === existingItem.quantity) {
            return;
          }

          set({
            items: items.map((item) =>
              item.productId === product.id
                ? { ...item, quantity: newQty }
                : item
            ),
          });
        } else {
          const newItem: CartItem = {
            id: `cart-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`,
            productId: product.id,
            variantId: product.variantId ?? null,
            title: product.title,
            price: product.price,
            imageUrl: product.imageUrl,
            quantity: 1,
            maxQuantity: product.inventoryQuantity ?? 99,
          };

          set({ items: [...items, newItem] });
        }

        set({ isOpen: true });
      },

      removeItem: (productId) => {
        set({
          items: get().items.filter((item) => item.productId !== productId),
        });
      },

      updateQuantity: (productId, quantity) => {
        const { items } = get();
        const item = items.find((i) => i.productId === productId);

        if (!item) return;

        if (quantity <= 0) {
          set({
            items: items.filter((i) => i.productId !== productId),
          });
          return;
        }

        const newQty = Math.min(quantity, item.maxQuantity);
        set({
          items: items.map((i) =>
            i.productId === productId ? { ...i, quantity: newQty } : i
          ),
        });
      },

      clearCart: () => {
        set({ items: [] });
      },

      openCart: () => {
        set({ isOpen: true });
      },

      closeCart: () => {
        set({ isOpen: false });
      },

      toggleCart: () => {
        set({ isOpen: !get().isOpen });
      },

      getItemCount: () => {
        return get().items.reduce((total, item) => total + item.quantity, 0);
      },

      getTotal: () => {
        return get().items.reduce((total, item) => {
          const price = parseFloat(item.price) || 0;
          return total + price * item.quantity;
        }, 0);
      },
    }),
    {
      name: 'preview-cart-storage',
      partialize: (state) => ({ items: state.items }),
    }
  )
);
