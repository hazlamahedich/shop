# 🔍 Widget Troubleshooting Guide

## Issue: Widget Not Appearing on Page

### ✅ What's Running
- **Backend**: Running on port 8000 ✅
- **Database**: Docker PostgreSQL on port 5433 ✅
- **Zrok Tunnel**: Active ✅
- **Merchant ID**: 1 exists with config ✅

---

## 🧪 Step 1: Test with Simple HTML Page

I've created a test page for you:

**URL**: `file:///Users/sherwingorechomante/shop/test-widget-page.html`

Or if frontend is running: `http://localhost:5173/test-widget-page.html`

### What to Check:
1. **Open the page in your browser**
2. **Open DevTools Console** (F12 or Cmd+Option+I)
3. **Look for errors** in red
4. **Check if widget bubble appears** in bottom-right corner

---

## 🔧 Common Widget Issues & Solutions

### Issue 1: Wrong API Base URL
**Symptom**: Console shows `Network error` or `CORS error`

**Solution**: Update your embed code with correct zrok URL:
```html
<script>
  window.ShopBotConfig = {
    merchantId: '1',
    theme: { primaryColor: '#6366f1' },
    apiBaseUrl: 'https://your-zrok-url.share.zrok.io/api/v1/widget'  // ← Your zrok URL
  };
</script>
```

### Issue 2: Missing React Dependencies
**Symptom**: Console shows `React is not defined`

**Solution**: Make sure these are loaded BEFORE the widget:
```html
<script src="https://unpkg.com/react@18/umd/react.production.min.js"></script>
<script src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js"></script>
```

### Issue 3: Widget Script Not Loading
**Symptom**: Console shows 404 for widget.umd.js

**Solution**: Check the script URL:
```html
<!-- For local development -->
<script src="http://localhost:8000/static/widget/widget.umd.js"></script>

<!-- For production via zrok -->
<script src="https://your-zrok-url.share.zrok.io/static/widget/widget.umd.js"></script>
```

### Issue 4: Merchant ID Not Found
**Symptom**: Console shows "Merchant X not found"

**Solution**: Use correct merchant ID:
- Your merchant ID is: **1** (hazlamahedich@gmail.com)

---

## 📋 Current Merchant Configuration

```
Merchant ID: 1
Email: hazlamahedich@gmail.com
Business: Sherwin Mante Personal Portfolio Page
FAQs Available: 4
Contact: hazlamahedich@gmail.com
```

---

## 🎯 Complete Working Embed Code

### Option 1: Local Development
```html
<script>
  window.ShopBotConfig = {
    merchantId: '1',
    theme: {
      primaryColor: '#6366f1',
      position: 'bottom-right'
    },
    apiBaseUrl: 'http://localhost:8000/api/v1/widget'
  };
</script>
<script src="https://unpkg.com/react@18/umd/react.production.min.js"></script>
<script src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js"></script>
<script src="http://localhost:8000/static/widget/widget.umd.js"></script>
```

### Option 2: Via Zrok Tunnel
```html
<script>
  window.ShopBotConfig = {
    merchantId: '1',
    theme: {
      primaryColor: '#6366f1',
      position: 'bottom-right'
    },
    apiBaseUrl: 'https://your-zrok-url.share.zrok.io/api/v1/widget'
  };
</script>
<script src="https://unpkg.com/react@18/umd/react.production.min.js"></script>
<script src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js"></script>
<script src="https://your-zrok-url.share.zrok.io/static/widget/widget.umd.js"></script>
```

---

## 🧪 Testing Checklist

Use the test page and verify:

- [ ] Console shows "✅ ShopBotConfig set"
- [ ] No red errors in console
- [ ] Widget bubble appears in bottom-right
- [ ] Can click the bubble to open chat
- [ ] FAQ buttons are visible

---

## 🐛 Next Steps

1. **Open the test page** and check console
2. **Tell me what errors** you see (if any)
3. **Share the URL** where you're trying to embed the widget
4. **Share your current embed code** (if different from above)

I'll help you fix it! 🔧
