import * as React from 'react';
import * as ReactDOM from 'react-dom/client';
import { Widget } from './Widget';
import type { WidgetTheme } from './types/widget';

declare const __VITE_WIDGET_VERSION__: string;

interface ShopBotConfig {
  merchantId: string;
  theme?: Partial<WidgetTheme>;
  apiBaseUrl?: string;
}

declare global {
  interface Window {
    ShopBotConfig?: ShopBotConfig;
    ShopBotWidget?: {
      version: string;
      init: () => void;
      unmount: () => void;
      isMounted: () => boolean;
    };
  }
}

const capturedScript = document.currentScript as HTMLScriptElement | null;

let widgetRoot: ReactDOM.Root | null = null;
let widgetContainer: HTMLDivElement | null = null;

const MERCHANT_ID_PATTERN = /^[a-zA-Z0-9_-]{1,64}$/;

function isValidMerchantId(id: string): boolean {
  if (!id || typeof id !== 'string') return false;
  return MERCHANT_ID_PATTERN.test(id);
}

function getConfig(): ShopBotConfig | null {
  if (window.ShopBotConfig?.merchantId) {
    return window.ShopBotConfig;
  }

  if (capturedScript?.dataset?.merchantId) {
    let theme: Partial<WidgetTheme> | undefined;
    if (capturedScript.dataset.theme) {
      try {
        theme = JSON.parse(capturedScript.dataset.theme);
      } catch {
        console.warn('[ShopBot Widget] Invalid theme JSON in data-theme attribute');
      }
    }
    return {
      merchantId: capturedScript.dataset.merchantId,
      theme,
    };
  }

  return null;
}

function initWidget(): void {
  if (widgetContainer && widgetRoot) {
    console.warn('[ShopBot Widget] Widget already initialized. Call unmountWidget() first to reinitialize.');
    return;
  }

  const config = getConfig();

  if (!config?.merchantId) {
    console.error(
      '[ShopBot Widget] Missing merchantId. Provide it via:\n' +
        '  window.ShopBotConfig = { merchantId: "YOUR_ID" }\n' +
        '  OR <script data-merchant-id="YOUR_ID" ...>'
    );
    return;
  }

  if (!isValidMerchantId(config.merchantId)) {
    console.error(
      '[ShopBot Widget] Invalid merchantId format. Expected 1-64 alphanumeric characters, hyphens, or underscores.'
    );
    return;
  }

  widgetContainer = document.createElement('div');
  widgetContainer.id = 'shopbot-widget-root';
  document.body.appendChild(widgetContainer);

  widgetRoot = ReactDOM.createRoot(widgetContainer);
  widgetRoot.render(
    React.createElement(Widget, {
      merchantId: config.merchantId,
      theme: config.theme,
    })
  );
}

function unmountWidget(): void {
  if (widgetRoot) {
    widgetRoot.unmount();
    widgetRoot = null;
  }
  if (widgetContainer) {
    widgetContainer.remove();
    widgetContainer = null;
  }
}

function isWidgetMounted(): boolean {
  return widgetContainer !== null && widgetRoot !== null;
}

// Handle async script loading
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initWidget);
} else {
  initWidget();
}

// Expose version and API on window.ShopBotWidget
if (typeof window !== 'undefined') {
  window.ShopBotWidget = {
    version: __VITE_WIDGET_VERSION__,
    init: initWidget,
    unmount: unmountWidget,
    isMounted: isWidgetMounted,
  };
}

// Export for programmatic use
export { Widget, initWidget, unmountWidget, isWidgetMounted, getConfig };
export type { ShopBotConfig, WidgetTheme };
