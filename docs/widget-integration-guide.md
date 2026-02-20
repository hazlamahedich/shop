# Widget Integration Guide

Complete guide for integrating the ShopBot widget into your website.

## Prerequisites

Before integrating the widget, ensure you have:

- **Active merchant account** - Sign up at yourbot.com
- **Widget enabled in settings** - Navigate to Settings > Widget > Enable
- **Merchant ID** - Available in Settings > Widget > Copy Merchant ID

## Basic Integration

### Step 1: Get Your Merchant ID

1. Log into your merchant dashboard
2. Navigate to **Settings** > **Widget**
3. Toggle **Enable Widget** to ON
4. Click **Copy** next to your Merchant ID

### Step 2: Add Widget Script

Add this code before the closing `</body>` tag on your website:

```html
<script>
  window.ShopBotConfig = {
    merchantId: 'YOUR_MERCHANT_ID'
  };
</script>
<script src="https://cdn.yourbot.com/widget/v/1.0.0/widget.umd.js" async></script>
```

### Step 3: Verify Installation

1. Open your website in a browser
2. Look for the chat bubble in the bottom-right corner
3. Click it to open the widget
4. Send a test message

## Advanced Configuration

### Full Configuration Options

```typescript
interface ShopBotConfig {
  merchantId: string;           // Required - Your merchant ID
  theme?: {
    primaryColor?: string;      // Hex color (default: #6366f1)
    backgroundColor?: string;   // Hex color (default: #ffffff)
    textColor?: string;         // Hex color (default: #1f2937)
    position?: 'bottom-right' | 'bottom-left';  // Position (default: bottom-right)
    borderRadius?: number;      // 0-24px (default: 16)
    width?: number;             // 300-500px (default: 380)
    height?: number;            // 400-800px (default: 600)
  };
  callbacks?: {
    onOpen?: () => void;        // Called when widget opens
    onClose?: () => void;       // Called when widget closes
    onMessage?: (message: string) => void;    // Called on user message
    onError?: (error: Error) => void;         // Called on errors
  };
  locale?: string;              // e.g., 'en-US' (default: browser locale)
  debug?: boolean;              // Enable debug logging (default: false)
}
```

### Theme Customization

Match the widget to your brand:

```html
<script>
  window.ShopBotConfig = {
    merchantId: 'YOUR_MERCHANT_ID',
    theme: {
      primaryColor: '#6366f1',
      backgroundColor: '#ffffff',
      textColor: '#1f2937',
      position: 'bottom-right',
      borderRadius: 16,
      width: 380,
      height: 600
    }
  };
</script>
```

### Position Options

The widget can be positioned in either corner:

```html
<!-- Bottom Right (default) -->
<script>
  window.ShopBotConfig = {
    merchantId: 'YOUR_MERCHANT_ID',
    theme: { position: 'bottom-right' }
  };
</script>

<!-- Bottom Left -->
<script>
  window.ShopBotConfig = {
    merchantId: 'YOUR_MERCHANT_ID',
    theme: { position: 'bottom-left' }
  };
</script>
```

### Event Callbacks

Track user interactions:

```html
<script>
  window.ShopBotConfig = {
    merchantId: 'YOUR_MERCHANT_ID',
    callbacks: {
      onOpen: () => {
        console.log('Widget opened');
        // Track in analytics
      },
      onClose: () => {
        console.log('Widget closed');
      },
      onMessage: (message) => {
        console.log('User sent:', message);
      },
      onError: (error) => {
        console.error('Widget error:', error);
      }
    }
  };
</script>
```

### Debug Mode

Enable debug logging for development:

```html
<script>
  window.ShopBotConfig = {
    merchantId: 'YOUR_MERCHANT_ID',
    debug: true  // Logs to browser console
  };
</script>
```

## Common Integration Scenarios

### Basic Embed

Simplest integration with minimal configuration:

```html
<!DOCTYPE html>
<html>
<head>
  <title>My Store</title>
</head>
<body>
  <!-- Your website content -->
  
  <!-- ShopBot Widget -->
  <script>
    window.ShopBotConfig = { merchantId: 'abc123xyz' };
  </script>
  <script src="https://cdn.yourbot.com/widget/v/1.0.0/widget.umd.js" async></script>
</body>
</html>
```

### With Theme Customization

```html
<script>
  window.ShopBotConfig = {
    merchantId: 'abc123xyz',
    theme: {
      primaryColor: '#10b981',     // Green accent
      backgroundColor: '#f9fafb',  // Light gray background
      borderRadius: 24             // Rounded corners
    }
  };
</script>
<script src="https://cdn.yourbot.com/widget/v/1.0.0/widget.umd.js" async></script>
```

### With Event Tracking

```html
<script>
  window.ShopBotConfig = {
    merchantId: 'abc123xyz',
    callbacks: {
      onOpen: () => {
        gtag('event', 'widget_opened');
      },
      onMessage: (message) => {
        gtag('event', 'widget_message', { message_length: message.length });
      }
    }
  };
</script>
<script src="https://cdn.yourbot.com/widget/v/1.0.0/widget.umd.js" async></script>
```

### SPA Integration (React/Vue/Angular)

For Single Page Applications, use the programmatic API:

```tsx
// ShopBotWidget.tsx
import { useEffect, useCallback } from 'react';

interface Props {
  merchantId: string;
  theme?: {
    primaryColor?: string;
    position?: 'bottom-right' | 'bottom-left';
  };
  onMessage?: (message: string) => void;
}

export function ShopBotWidget({ merchantId, theme, onMessage }: Props) {
  useEffect(() => {
    // Configure widget
    window.ShopBotConfig = { 
      merchantId, 
      theme,
      callbacks: {
        onMessage
      }
    };

    // Load script
    const script = document.createElement('script');
    script.src = 'https://cdn.yourbot.com/widget/v/1.0.0/widget.umd.js';
    script.async = true;
    document.body.appendChild(script);

    // Cleanup on unmount
    return () => {
      script.remove();
      if (window.ShopBotWidget?.unmount) {
        window.ShopBotWidget.unmount();
      }
      delete (window as any).ShopBotConfig;
    };
  }, [merchantId, theme, onMessage]);

  return null;
}

// Usage
<ShopBotWidget 
  merchantId="abc123xyz"
  theme={{ primaryColor: '#6366f1' }}
  onMessage={(msg) => console.log('User message:', msg)}
/>
```

### Using data attributes

Alternative configuration via script attributes:

```html
<script 
  data-merchant-id="YOUR_MERCHANT_ID"
  data-theme='{"primaryColor": "#6366f1"}'
  src="https://cdn.yourbot.com/widget/v/1.0.0/widget.umd.js"
  async>
</script>
```

## Programmatic Control

The widget exposes an API on `window.ShopBotWidget`:

```javascript
// Check installed version
console.log(window.ShopBotWidget.version);  // "1.0.0"

// Manually initialize (if auto-init disabled)
window.ShopBotWidget.init();

// Unmount widget
window.ShopBotWidget.unmount();

// Check if mounted
window.ShopBotWidget.isMounted();  // true/false
```

## Version Management

### Checking Current Version

```javascript
// In browser console after widget loads
console.log(window.ShopBotWidget.version);
```

### Upgrading to New Version

1. Update the version in your script URL
2. Test thoroughly in staging
3. Deploy to production

```html
<!-- Old version -->
<script src="https://cdn.yourbot.com/widget/v/1.0.0/widget.umd.js"></script>

<!-- New version -->
<script src="https://cdn.yourbot.com/widget/v/1.1.0/widget.umd.js"></script>
```

## Security Considerations

### Domain Whitelist

Optionally restrict widget to specific domains:

1. Go to Settings > Widget > Security
2. Add allowed domains (e.g., `mystore.com`, `www.mystore.com`)
3. Widget will not load on unauthorized domains

### Content Security Policy

If your site uses CSP, add these directives:

```
script-src: cdn.yourbot.com
connect-src: api.yourbot.com
style-src: cdn.yourbot.com
```

## Related Documentation

- [Widget Quick Start](./widget-quick-start.md) - 5-minute setup guide
- [Widget Troubleshooting](./widget-troubleshooting.md) - Common issues and solutions
- [Widget CDN Setup](./widget-cdn-setup.md) - CDN configuration
- [Widget Cache Headers](./widget-cache-headers.md) - Caching strategy
