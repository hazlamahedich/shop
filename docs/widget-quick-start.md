# Quick Start: 5-Minute Widget Setup

Get the ShopBot AI shopping assistant running on your website in just 5 minutes.

## Prerequisites

- Active merchant account at yourbot.com
- Access to edit your website HTML

---

## Step 1: Enable Widget (30 seconds)

1. Log into your [merchant dashboard](https://dashboard.yourbot.com)
2. Navigate to **Settings** → **Widget**
3. Toggle **Enable Widget** to **ON**
4. Click **Copy** next to your **Merchant ID**

> 💡 **Tip:** Keep this Merchant ID handy - you'll need it in Step 2.

---

## Step 2: Add to Your Website (2 minutes)

Paste this code before the closing `</body>` tag on every page where you want the widget:

```html
<script>
  window.ShopBotConfig = {
    merchantId: 'PASTE_YOUR_MERCHANT_ID_HERE'
  };
</script>
<script src="https://cdn.yourbot.com/widget/v/1.0.0/widget.umd.js" async></script>
```

### Where to add it:

**For most websites:**
```html
<!DOCTYPE html>
<html>
<head>
  <title>Your Website</title>
</head>
<body>
  <!-- Your website content here -->
  
  <!-- Add ShopBot Widget here -->
  <script>
    window.ShopBotConfig = {
      merchantId: 'YOUR_MERCHANT_ID'
    };
  </script>
  <script src="https://cdn.yourbot.com/widget/v/1.0.0/widget.umd.js" async></script>
</body>
</html>
```

**For Shopify:**
1. Go to Online Store → Themes → Edit code
2. Open `theme.liquid`
3. Paste code before `</body>`
4. Save

**For WordPress:**
1. Install "Insert Headers and Footers" plugin
2. Go to Settings → Insert Headers and Footers
3. Paste code in "Scripts in Footer"
4. Save

---

## Step 3: Customize (2 minutes) - Optional

Match the widget to your brand colors:

```html
<script>
  window.ShopBotConfig = {
    merchantId: 'YOUR_MERCHANT_ID',
    theme: {
      primaryColor: '#6366f1',      // Your brand color
      position: 'bottom-right'       // or 'bottom-left'
    }
  };
</script>
<script src="https://cdn.yourbot.com/widget/v/1.0.0/widget.umd.js" async></script>
```

### Available Theme Options:

| Option | Default | Options |
|--------|---------|---------|
| `primaryColor` | `#6366f1` | Any hex color |
| `position` | `bottom-right` | `bottom-right`, `bottom-left` |
| `borderRadius` | `16` | `0` to `24` (pixels) |
| `width` | `380` | `300` to `500` (pixels) |
| `height` | `600` | `400` to `800` (pixels) |

---

## Step 4: Test (30 seconds)

1. Open your website in a browser
2. Look for the chat bubble in the bottom-right corner
3. Click it to open the widget
4. Type a message like "Hello" or "Show me products"
5. Verify the bot responds

> ✅ **Success!** You should see the AI shopping assistant responding to your messages.

---

## ✅ Done!

Your AI shopping assistant is now live on your website. It will:
- Greet visitors automatically
- Answer product questions
- Help customers find items
- Assist with orders

---

## Next Steps

### Recommended

1. **Customize appearance** - [Theme customization guide](./widget-integration-guide.md#theme-customization)
2. **Set up welcome message** - Configure in Settings > Widget > Greeting
3. **Track conversations** - View in [Conversations dashboard](https://dashboard.yourbot.com/conversations)

### Advanced

- **Add event tracking** - [Track widget interactions](./widget-integration-guide.md#event-callbacks)
- **React/Vue integration** - [SPA integration guide](./widget-integration-guide.md#spa-integration)
- **Troubleshooting** - [Common issues and solutions](./widget-troubleshooting.md)

---

## Need Help?

| Issue | Solution |
|-------|----------|
| Widget not appearing | [Troubleshooting guide](./widget-troubleshooting.md#widget-not-appearing) |
| Messages not sending | [Troubleshooting guide](./widget-troubleshooting.md#messages-not-sending) |
| Customization questions | [Integration guide](./widget-integration-guide.md) |
| Other issues | support@yourbot.com |

---

## Copy-Paste Examples

### Minimal (Default styling)

```html
<script>window.ShopBotConfig={merchantId:'YOUR_ID'};</script>
<script src="https://cdn.yourbot.com/widget/v/1.0.0/widget.umd.js" async></script>
```

### With Brand Colors

```html
<script>
window.ShopBotConfig={
  merchantId:'YOUR_ID',
  theme:{primaryColor:'#6366f1',position:'bottom-right'}
};
</script>
<script src="https://cdn.yourbot.com/widget/v/1.0.0/widget.umd.js" async></script>
```

### Left Position

```html
<script>
window.ShopBotConfig={
  merchantId:'YOUR_ID',
  theme:{position:'bottom-left'}
};
</script>
<script src="https://cdn.yourbot.com/widget/v/1.0.0/widget.umd.js" async></script>
```

---

## Related Documentation

- [Full Integration Guide](./widget-integration-guide.md)
- [Troubleshooting Guide](./widget-troubleshooting.md)
- [CDN Setup](./widget-cdn-setup.md)
- [Release Process](./widget-release-process.md)
