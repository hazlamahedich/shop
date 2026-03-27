import * as React from 'react';
import * as ReactDOM from 'react-dom/client';
import { Widget } from './Widget';
import type { WidgetTheme } from './types/widget';

declare const __VITE_WIDGET_VERSION__: string;

interface ShopBotConfig {
  merchantId: string;
  theme?: Partial<WidgetTheme>;
  apiBaseUrl?: string;
  /** Optional session ID for testing purposes - allows pre-seeding session state */
  sessionId?: string;
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

let capturedScript: HTMLScriptElement | null = null;
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
        // Invalid theme JSON - use defaults
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
    return;
  }

  const config = getConfig();

  if (!config?.merchantId) {
    return;
  }

  if (!isValidMerchantId(config.merchantId)) {
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
      initialSessionId: config.sessionId,
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

// Capture the script element that loads the widget
if (document.currentScript instanceof HTMLScriptElement) {
  capturedScript = document.currentScript;
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
