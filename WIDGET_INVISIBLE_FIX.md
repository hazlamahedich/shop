# 🔧 Widget Not Visible - Diagnosis & Solutions

## Issue: Widget embedded but not visible on https://portfolio-website-phi-brown.vercel.app

**Good News**: No console errors means scripts are loading correctly!

---

## 🎯 Most Likely Causes & Solutions

### Issue 1: CSS Hiding the Widget (Most Common)

**Problem**: Portfolio site CSS might be hiding the widget

**Solutions**:

#### Option A: Add CSS Override (Quick Fix)
Add this to your portfolio site CSS:
```css
/* Ensure widget is visible */
.shopbot-chat-bubble,
.shopbot-chat-window,
[class*="shopbot"] {
    display: block !important;
    visibility: visible !important;
    opacity: 1 !important;
    position: fixed !important;
    z-index: 2147483647 !important;
}
```

#### Option B: Add Widget Wrapper
```html
<div id="shopbot-widget-container" style="position: fixed; bottom: 20px; right: 20px; z-index: 2147483647;">
  <!-- Your widget scripts here -->
</div>
```

---

### Issue 2: Widget Container Has Zero Size

**Problem**: Widget container might be collapsed

**Solution**: Add minimum size
```css
#shopbot-widget-container {
    min-width: 300px;
    min-height: 400px;
}
```

---

### Issue 3: Z-Index Conflict

**Problem**: Site has elements with very high z-index

**Solution**: Increase widget z-index
```html
<script>
  window.ShopBotConfig = {
    merchantId: '1',
    theme: {
      primaryColor: '#6366f1'
    },
    // Add this to boost widget priority
    zIndex: 2147483647
  };
</script>
```

---

### Issue 4: Widget Loading Before DOM Ready

**Problem**: Scripts running too early

**Solution**: Add delay
```html
<script>
  // Wait for DOM to be ready
  document.addEventListener('DOMContentLoaded', function() {
    // ShopBotConfig and widget scripts here
  });
</script>
```

---

## ✅ Working Embed Code for Your Portfolio Site

```html
<!-- Add this before closing </body> tag -->
<div id="shopbot-widget-wrapper" style="position: fixed; bottom: 20px; right: 20px; z-index: 2147483647; pointer-events: auto;">
</div>

<script>
  document.addEventListener('DOMContentLoaded', function() {
    // Configure widget
    window.ShopBotConfig = {
      merchantId: '1',
      theme: {
        primaryColor: '#6366f1',
        position: 'bottom-right',
        borderRadius: 12,
        width: 400,
        height: 600
      },
      apiBaseUrl: 'https://shopdevsherwingor.share.zrok.io/api/v1/widget'
    };

    // Load React dependencies
    const reactScript = document.createElement('script');
    reactScript.src = 'https://unpkg.com/react@18/umd/react.production.min.js';
    reactScript.crossOrigin = 'anonymous';
    document.getElementById('shopbot-widget-wrapper').appendChild(reactScript);

    const reactDOMScript = document.createElement('script');
    reactDOMScript.src = 'https://unpkg.com/react-dom@18/umd/react-dom.production.min.js';
    reactDOMScript.crossOrigin = 'anonymous';
    document.getElementById('shopbot-widget-wrapper').appendChild(reactDOMScript);

    // Load widget
    const widgetScript = document.createElement('script');
    widgetScript.src = 'https://shopdevsherwingor.share.zrok.io/static/widget/widget.umd.js';
    widgetScript.onload = function() {
      console.log('✅ Widget loaded successfully!');
    };
    widgetScript.onerror = function() {
      console.error('❌ Widget failed to load');
    };
    document.getElementById('shopbot-widget-wrapper').appendChild(widgetScript);
  });
</script>

<style>
  /* Ensure widget is visible */
  #shopbot-widget-wrapper,
  #shopbot-widget-wrapper * {
    visibility: visible !important;
    opacity: 1 !important;
    display: block !important;
  }

  /* Widget bubble styles */
  [class*="shopbot-chat-bubble"] {
    display: block !important;
    position: fixed !important;
    z-index: 2147483647 !important;
  }

  /* Widget window styles */
  [class*="shopbot-chat-window"] {
    display: block !important;
    z-index: 2147483647 !important;
  }
</style>
```

---

## 🧪 Test Widget on Your Portfolio Site

### Quick Test Page:

1. **Create a test page** on your portfolio:
   - Create `/test-widget.html`
   - Paste the working embed code above
   - Access: `https://portfolio-website-phi-brown.vercel.app/test-widget.html`

2. **Check if widget appears** on test page

3. **If it works on test page**, add the same code to your main page

---

## 🔍 Debug Steps

### Step 1: Add Debug Code
```html
<script>
  window.ShopBotConfig = {
    merchantId: '1',
    apiBaseUrl: 'https://shopdevsherwingor.share.zrok.io/api/v1/widget',
    theme: { primaryColor: '#6366f1' },
    debug: true  // Enable debug mode
  };
</script>
```

### Step 2: Check Console After Page Load
```javascript
// Run in browser console
console.log('ShopBotConfig:', window.ShopBotConfig);
console.log('ShopBotWidget:', window.ShopBotWidget);

// Check for widget elements
document.querySelectorAll('[class*="shopbot"]').forEach((el, i) => {
  console.log(`Widget element ${i}:`, el);
  console.log('  Visible:', el.offsetParent !== null);
  console.log('  Z-index:', getComputedStyle(el).zIndex);
  console.log('  Display:', getComputedStyle(el).display);
});
```

### Step 3: Force Widget Visibility
```javascript
// Run in browser console to unhide widget
document.querySelectorAll('[class*="shopbot"]').forEach(el => {
  el.style.setProperty('display', 'block', 'important');
  el.style.setProperty('visibility', 'visible', 'important');
  el.style.setProperty('opacity', '1', 'important');
  el.style.setProperty('z-index', '2147483647', 'important');
});
```

---

## 🎯 Quick Fix Template

Copy and paste this into your portfolio site HTML (before `</body>`):

```html
<link rel="stylesheet" href="/widget-widget-override.css">
<div id="widget-container"></div>
<script src="/widget-loader.js"></script>
```

Then create these files:

**widget-widget-override.css**:
```css
#widget-container {
  position: fixed;
  bottom: 20px;
  right: 20px;
  z-index: 2147483647;
  min-width: 300px;
  min-height: 400px;
}

[class*="shopbot"] {
  visibility: visible !important;
  opacity: 1 !important;
  display: block !important;
}
```

---

## 📋 What I Need From You

1. **Try the debug steps above** and share console output
2. **Or** try the test page approach and let me know results
3. **Or** share the HTML code where you embedded the widget

This will help me pinpoint the exact issue! 🔧
