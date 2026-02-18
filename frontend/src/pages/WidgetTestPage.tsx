import * as React from 'react';
import { Widget } from '../widget/Widget';

const defaultTheme = {
  primaryColor: '#6366f1',
  backgroundColor: '#ffffff',
  textColor: '#1f2937',
  botBubbleColor: '#f3f4f6',
  userBubbleColor: '#6366f1',
  position: 'bottom-right' as const,
  borderRadius: 16,
  width: 380,
  height: 600,
  fontFamily: 'Inter, sans-serif',
  fontSize: 14,
};

function parseThemeFromUrl() {
  const params = new URLSearchParams(window.location.search);
  const theme: Record<string, unknown> = {};

  for (const [key, value] of params) {
    if (key.startsWith('theme[')) {
      const themeKey = key.match(/theme\[(.+)\]/)?.[1];
      if (themeKey) {
        if (value.startsWith('%23') || value.startsWith('#')) {
          theme[themeKey] = decodeURIComponent(value);
        } else if (!isNaN(Number(value))) {
          theme[themeKey] = parseInt(value, 10);
        } else {
          theme[themeKey] = value;
        }
      }
    }
  }

  return Object.keys(theme).length > 0 ? theme : {};
}

function getMerchantId() {
  const params = new URLSearchParams(window.location.search);
  return params.get('merchantId') || '1';
}

export default function WidgetTestPage() {
  const theme = { ...defaultTheme, ...parseThemeFromUrl() };
  const merchantId = getMerchantId();

  return (
    <div style={{ padding: 40, fontFamily: 'system-ui, sans-serif' }}>
      <div style={{
        maxWidth: 800,
        margin: '0 auto',
        background: 'white',
        padding: 40,
        borderRadius: 8,
        boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
      }}>
        <h1 style={{ margin: '0 0 20px 0', color: '#1f2937' }}>
          Widget Test Page
        </h1>
        <p style={{ color: '#6b7280', lineHeight: 1.6 }}>
          This page is used for E2E testing of the chat widget.
          The widget should appear in the bottom-right corner.
        </p>
        <p style={{ color: '#6b7280', marginTop: 16 }}>
          URL parameters for testing:
        </p>
        <ul style={{ color: '#6b7280', marginTop: 8 }}>
          <li><code>?theme[primaryColor]=%23ff0000</code> - Custom primary color</li>
          <li><code>?theme[position]=bottom-left</code> - Position on bottom-left</li>
          <li><code>?theme[borderRadius]=24</code> - Custom border radius</li>
          <li><code>?merchantId=2</code> - Different merchant ID</li>
        </ul>
      </div>
      <Widget merchantId={merchantId} theme={theme} />
    </div>
  );
}
