import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';

// Mock the Widget import to avoid rendering issues
vi.mock('./Widget', () => ({
  Widget: vi.fn(() => null),
}));

// Mock react-dom/client
vi.mock('react-dom/client', () => ({
  createRoot: vi.fn(() => ({
    render: vi.fn(),
    unmount: vi.fn(),
  })),
}));

describe('loader', () => {
  let originalShopBotConfig: unknown;

  beforeEach(() => {
    vi.clearAllMocks();
    originalShopBotConfig = window.ShopBotConfig;
    delete (window as Record<string, unknown>).ShopBotConfig;

    // Reset document.currentScript
    Object.defineProperty(document, 'currentScript', {
      value: null,
      writable: true,
      configurable: true,
    });

    // Clean up any existing widget container
    const existingContainer = document.getElementById('shopbot-widget-root');
    if (existingContainer) {
      existingContainer.remove();
    }
  });

  afterEach(() => {
    window.ShopBotConfig = originalShopBotConfig as (typeof window.ShopBotConfig);
    vi.resetModules();
  });

  describe('getConfig', () => {
    it('should return config from window.ShopBotConfig', async () => {
      window.ShopBotConfig = {
        merchantId: 'test-merchant-123',
        theme: { primaryColor: '#10b981' },
      };

      const { getConfig } = await import('./loader');
      const config = getConfig();

      expect(config).toEqual({
        merchantId: 'test-merchant-123',
        theme: { primaryColor: '#10b981' },
      });
    });

    it('should return config from data-merchant-id attribute', async () => {
      const mockScript = document.createElement('script');
      mockScript.dataset.merchantId = 'data-merchant-456';
      mockScript.dataset.theme = JSON.stringify({ primaryColor: '#6366f1' });

      Object.defineProperty(document, 'currentScript', {
        value: mockScript,
        writable: true,
        configurable: true,
      });

      const { getConfig } = await import('./loader');
      const config = getConfig();

      expect(config).toEqual({
        merchantId: 'data-merchant-456',
        theme: { primaryColor: '#6366f1' },
      });
    });

    it('should return null when no config available', async () => {
      const { getConfig } = await import('./loader');
      const config = getConfig();

      expect(config).toBeNull();
    });

    it('should return null when window.ShopBotConfig has no merchantId', async () => {
      window.ShopBotConfig = { merchantId: '' };

      const { getConfig } = await import('./loader');
      const config = getConfig();

      expect(config).toBeNull();
    });

    it('should handle invalid theme JSON gracefully', async () => {
      const mockScript = document.createElement('script');
      mockScript.dataset.merchantId = 'test-merchant-123';
      mockScript.dataset.theme = 'invalid-json{';

      Object.defineProperty(document, 'currentScript', {
        value: mockScript,
        writable: true,
        configurable: true,
      });

      const consoleWarnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});

      const { getConfig } = await import('./loader');
      const config = getConfig();

      expect(config).toEqual({
        merchantId: 'test-merchant-123',
        theme: undefined,
      });
      expect(consoleWarnSpy).toHaveBeenCalledWith(
        '[ShopBot Widget] Invalid theme JSON in data-theme attribute'
      );

      consoleWarnSpy.mockRestore();
    });

    it('should prefer window.ShopBotConfig over data attributes', async () => {
      window.ShopBotConfig = {
        merchantId: 'window-config',
      };

      const mockScript = document.createElement('script');
      mockScript.dataset.merchantId = 'data-config';

      Object.defineProperty(document, 'currentScript', {
        value: mockScript,
        writable: true,
        configurable: true,
      });

      const { getConfig } = await import('./loader');
      const config = getConfig();

      expect(config?.merchantId).toBe('window-config');
    });
  });

  describe('merchantId validation', () => {
    it('should reject merchantId that is too short', async () => {
      window.ShopBotConfig = { merchantId: 'short' };

      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      await import('./loader');

      expect(consoleErrorSpy).toHaveBeenCalledWith(
        expect.stringContaining('Invalid merchantId format')
      );

      consoleErrorSpy.mockRestore();
    });

    it('should reject merchantId with special characters', async () => {
      window.ShopBotConfig = { merchantId: 'test@merchant#123' };

      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      await import('./loader');

      expect(consoleErrorSpy).toHaveBeenCalledWith(
        expect.stringContaining('Invalid merchantId format')
      );

      consoleErrorSpy.mockRestore();
    });

    it('should accept valid merchantId with alphanumeric, hyphens, underscores', async () => {
      window.ShopBotConfig = { merchantId: 'test_merchant-12345' };

      const { getConfig } = await import('./loader');
      const config = getConfig();

      expect(config?.merchantId).toBe('test_merchant-12345');
    });
  });

  describe('initWidget', () => {
    it('should log error and not render when merchantId is missing', async () => {
      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      await import('./loader');

      document.dispatchEvent(new Event('DOMContentLoaded'));

      expect(consoleErrorSpy).toHaveBeenCalledWith(
        expect.stringContaining('[ShopBot Widget] Missing merchantId')
      );

      consoleErrorSpy.mockRestore();
    });

    it('should create container element when valid config exists', async () => {
      const mockCreateRoot = vi.fn(() => ({ render: vi.fn() }));
      vi.doMock('react-dom/client', () => ({
        createRoot: mockCreateRoot,
      }));

      window.ShopBotConfig = {
        merchantId: 'test-merchant-123',
      };

      await vi.importMock('./loader');

      const container = document.getElementById('shopbot-widget-root');
      expect(container).toBeTruthy();
    });

    it('should warn if widget already initialized', async () => {
      window.ShopBotConfig = {
        merchantId: 'test-merchant-123',
      };

      const consoleWarnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});

      const { initWidget } = await import('./loader');

      initWidget();
      initWidget();

      expect(consoleWarnSpy).toHaveBeenCalledWith(
        '[ShopBot Widget] Widget already initialized. Call unmountWidget() first to reinitialize.'
      );

      consoleWarnSpy.mockRestore();
    });
  });

  describe('unmountWidget', () => {
    it('should export unmountWidget function', async () => {
      const { unmountWidget } = await import('./loader');
      expect(typeof unmountWidget).toBe('function');
    });

    it('should handle unmount when widget not mounted', async () => {
      const { unmountWidget, isWidgetMounted } = await import('./loader');

      expect(isWidgetMounted()).toBe(false);

      unmountWidget();

      expect(isWidgetMounted()).toBe(false);
    });
  });

  describe('isWidgetMounted', () => {
    it('should export isWidgetMounted function', async () => {
      const { isWidgetMounted } = await import('./loader');
      expect(typeof isWidgetMounted).toBe('function');
    });

    it('should return false when widget not mounted', async () => {
      const { isWidgetMounted } = await import('./loader');
      expect(isWidgetMounted()).toBe(false);
    });
  });

  describe('exports', () => {
    it('should export Widget component', async () => {
      const { Widget } = await import('./loader');
      expect(Widget).toBeDefined();
    });

    it('should export initWidget function', async () => {
      const { initWidget } = await import('./loader');
      expect(typeof initWidget).toBe('function');
    });

    it('should export ShopBotConfig type', async () => {
      const loader = await import('./loader');
      expect(loader).toHaveProperty('Widget');
      expect(loader).toHaveProperty('initWidget');
    });
  });
});
