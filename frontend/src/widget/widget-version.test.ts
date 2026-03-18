import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';

// Mock the VITE_WIDGET_VERSION constant for tests
vi.stubGlobal('__VITE_WIDGET_VERSION__', '0.1.0');

describe('Widget Version Embedding', () => {
  const originalWindow = global.window;
  const originalDocument = global.document;

  beforeEach(() => {
    vi.resetModules();
    
    const mockElement = {
      id: '',
      appendChild: vi.fn(),
      remove: vi.fn(),
      dataset: {},
    };
    
    const mockBody = {
      appendChild: vi.fn(),
      removeChild: vi.fn(),
    };

    global.document = {
      ...originalDocument,
      readyState: 'complete',
      currentScript: mockElement as any,
      createElement: vi.fn(() => ({ ...mockElement })),
      getElementById: vi.fn(),
      body: mockBody as any,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    } as any;

    global.window = {
      ShopBotConfig: undefined,
      ShopBotWidget: undefined,
    } as any;
  });

  afterEach(() => {
    global.window = originalWindow;
    global.document = originalDocument;
    vi.restoreAllMocks();
  });

  it('should expose version on window.ShopBotWidget', async () => {
    global.window.ShopBotConfig = {
      merchantId: 'test-merchant-123',
    };

    vi.mock('./Widget', () => ({
      Widget: vi.fn(() => null),
    }));

    vi.mock('react-dom/client', () => ({
      createRoot: vi.fn(() => ({
        render: vi.fn(),
        unmount: vi.fn(),
      })),
    }));

    vi.mock('react', () => ({
      createElement: vi.fn(),
    }));

    await import('./loader');

    expect(window.ShopBotWidget).toBeDefined();
    expect(window.ShopBotWidget?.version).toBeDefined();
    expect(typeof window.ShopBotWidget?.version).toBe('string');
    expect(window.ShopBotWidget?.version).toMatch(/^\d+\.\d+\.\d+$/);
  });

  it('should expose init, unmount, and isMounted methods', async () => {
    global.window.ShopBotConfig = {
      merchantId: 'test-merchant-123',
    };

    vi.mock('./Widget', () => ({
      Widget: vi.fn(() => null),
    }));

    vi.mock('react-dom/client', () => ({
      createRoot: vi.fn(() => ({
        render: vi.fn(),
        unmount: vi.fn(),
      })),
    }));

    vi.mock('react', () => ({
      createElement: vi.fn(),
    }));

    await import('./loader');

    expect(typeof window.ShopBotWidget?.init).toBe('function');
    expect(typeof window.ShopBotWidget?.unmount).toBe('function');
    expect(typeof window.ShopBotWidget?.isMounted).toBe('function');
  });

  it('should return correct version matching semantic version format', async () => {
    global.window.ShopBotConfig = {
      merchantId: 'test-merchant-123',
    };

    vi.mock('./Widget', () => ({
      Widget: vi.fn(() => null),
    }));

    vi.mock('react-dom/client', () => ({
      createRoot: vi.fn(() => ({
        render: vi.fn(),
        unmount: vi.fn(),
      })),
    }));

    vi.mock('react', () => ({
      createElement: vi.fn(),
    }));

    await import('./loader');

    // Version should match semantic versioning format (X.Y.Z)
    expect(window.ShopBotWidget?.version).toMatch(/^\d+\.\d+\.\d+$/);
  });
});
