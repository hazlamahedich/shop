# Widget Quick Replies Not Appearing - Fix Guide

## Problem
The backend sends quick replies correctly, but they don't appear in your embedded widget.

## Root Cause
Your website is likely caching an old version of the widget code that doesn't handle the camelCase field names (`quickReplies` vs `quick_replies`).

## Solutions (try in order)

### Solution 1: Hard Refresh (Most Likely to Work)
Add a cache-busting parameter to your widget embed code:

```html
<!-- BEFORE -->
<script src="http://localhost:5173/src/widget/loader.ts"></script>

<!-- AFTER - Add version parameter -->
<script src="http://localhost:5173/src/widget/loader.ts?v=2"></script>
```

### Solution 2: Clear Browser Cache
1. Open your website in Chrome/Edge
2. Press `Ctrl+Shift+R` (Windows) or `Cmd+Shift+R` (Mac)
3. Or open DevTools (F12) → Right-click refresh button → "Empty Cache and Hard Reload"

### Solution 3: Check Your Embed Code
Make sure you're using the correct embed code format:

```html
<script>
  window.ShopBotConfig = {
    merchantId: '1',
    apiBaseUrl: 'http://localhost:8000'  // or your production URL
  };
</script>
<script src="http://localhost:5173/src/widget/loader.ts" defer></script>
```

### Solution 4: Rebuild Widget for Production
If you're using a production build, rebuild it:

```bash
cd /Users/sherwingorechomante/shop/frontend
npm run build
```

Then update your embed code to use the built version:
```html
<script src="http://localhost:5173/dist/widget.js"></script>
```

## Verification
After applying the fix:
1. Open browser DevTools (F12)
2. Go to Console tab
3. Type: `localStorage.clear()` and press Enter
4. Refresh the page
5. Send a message to the widget
6. Quick reply chips should appear below the bot's response

## About the RAG "Issue"
The RAG system is working correctly! When I tested "where did he graduate", the bot answered:
> "Sherwin Mante graduated from the **University of Santo Tomas**."

If you're seeing different responses, it might be:
- The bot was still in the initial greeting state
- The conversation context was lost
- A temporary connectivity issue

The knowledge base contains your resume and is properly indexed.
