/**
 * Tests for Route Guard Components
 *
 * Sprint Change 2026-02-13: Tests for StoreRequiredGuard
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, cleanup } from '@testing-library/react';
import { MemoryRouter, Routes, Route, useLocation } from 'react-router-dom';

// Mock the auth store
const mockUseHasStoreConnected = vi.fn();
vi.mock('../stores/authStore', () => ({
  useHasStoreConnected: () => mockUseHasStoreConnected(),
}));

import { StoreRequiredGuard } from './RouteGuards';

// Test component to show current location
function LocationDisplay() {
  const location = useLocation();
  return (
    <div data-testid="location">
      {location.pathname}
      {location.state && (
        <span data-testid="location-state">
          {JSON.stringify(location.state)}
        </span>
      )}
    </div>
  );
}

// Test page components
function ProductsPage() {
  return <div data-testid="protected-content">Products Page</div>;
}

function BotConfigPage() {
  return (
    <>
      <LocationDisplay />
      <div data-testid="bot-config">Bot Config Page</div>
    </>
  );
}

function SettingsStorePage() {
  return (
    <>
      <LocationDisplay />
      <div data-testid="settings-store">Settings Store Page</div>
    </>
  );
}

describe('StoreRequiredGuard', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    cleanup();
  });

  it('should render children when store is connected', () => {
    mockUseHasStoreConnected.mockReturnValue(true);

    render(
      <MemoryRouter initialEntries={['/products']}>
        <Routes>
          <Route
            path="/products"
            element={
              <StoreRequiredGuard>
                <ProductsPage />
              </StoreRequiredGuard>
            }
          />
        </Routes>
      </MemoryRouter>
    );

    expect(screen.getByTestId('protected-content')).toBeInTheDocument();
    expect(screen.getByText('Products Page')).toBeInTheDocument();
  });

  it('should redirect to /bot-config when no store is connected', () => {
    mockUseHasStoreConnected.mockReturnValue(false);

    render(
      <MemoryRouter initialEntries={['/products']}>
        <Routes>
          <Route
            path="/products"
            element={
              <StoreRequiredGuard>
                <ProductsPage />
              </StoreRequiredGuard>
            }
          />
          <Route path="/bot-config" element={<BotConfigPage />} />
        </Routes>
      </MemoryRouter>
    );

    // Should be redirected to /bot-config
    expect(screen.getByTestId('location')).toHaveTextContent('/bot-config');
  });

  it('should pass location state when redirecting', () => {
    mockUseHasStoreConnected.mockReturnValue(false);

    render(
      <MemoryRouter initialEntries={['/products']}>
        <Routes>
          <Route
            path="/products"
            element={
              <StoreRequiredGuard>
                <ProductsPage />
              </StoreRequiredGuard>
            }
          />
          <Route path="/bot-config" element={<BotConfigPage />} />
        </Routes>
      </MemoryRouter>
    );

    // Should include state with from path and requiresStore flag
    const locationState = screen.getByTestId('location-state');
    const state = JSON.parse(locationState.textContent || '{}');
    expect(state.from).toBe('/products');
    expect(state.requiresStore).toBe(true);
  });

  it('should redirect to custom path when specified', () => {
    mockUseHasStoreConnected.mockReturnValue(false);

    render(
      <MemoryRouter initialEntries={['/orders']}>
        <Routes>
          <Route
            path="/orders"
            element={
              <StoreRequiredGuard redirectTo="/settings/store">
                <div data-testid="protected-content">Orders Page</div>
              </StoreRequiredGuard>
            }
          />
          <Route path="/settings/store" element={<SettingsStorePage />} />
        </Routes>
      </MemoryRouter>
    );

    // Should be redirected to custom path
    expect(screen.getByTestId('location')).toHaveTextContent('/settings/store');
  });
});
