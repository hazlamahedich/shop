# 🚀 Deploy Widget Visibility Fix to Vercel

## Overview

The `widget-visibility-fix.css` file has been added to `frontend/public/` and committed to the repository. This guide shows how to deploy it and use it on your portfolio site.

---

## Step 1: Deploy Shop Frontend to Vercel

### Option A: Automatic Deployment (Recommended)

If your shop repository is already linked to Vercel, pushing to `main` branch should trigger an automatic deployment.

1. Check deployment status: https://vercel.com/dashboard
2. Look for the "shop" project
3. Wait for deployment to complete (usually takes 1-2 minutes)

### Option B: Manual Deployment

If automatic deployment is not set up:

```bash
cd /Users/sherwingorechomante/shop/frontend

# Install Vercel CLI (if not installed)
npm i -g vercel

# Login to Vercel
vercel login

# Deploy to production
vercel --prod
```

---

## Step 2: Get CSS File URL

After deployment, the CSS file will be available at:

```
https://[your-shop-frontend-url].vercel.app/widget-visibility-fix.css
```

Example:
```
https://shop-frontend.vercel.app/widget-visibility-fix.css
```

Test the URL in your browser to verify it's accessible.

---

## Step 3: Add CSS to Portfolio Site

### For Portfolio Site in This Repository

If the portfolio site code is in this repository, add this to your portfolio site's HTML (in `<head>`):

```html
<!-- Add before closing </head> tag -->
<link rel="stylesheet" href="https://[your-shop-frontend-url].vercel.app/widget-visibility-fix.css">
```

### For External Portfolio Site

If your portfolio site at `https://portfolio-website-phi-brown.vercel.app` is in a different repository:

1. Open the portfolio site repository
2. Find the HTML file (usually `index.html`)
3. Add the CSS link before the closing `</head>` tag:

```html
<link rel="stylesheet" href="https://[your-shop-frontend-url].vercel.app/widget-visibility-fix.css">
```

---

## Step 4: Verify Widget Visibility

1. Visit your portfolio site: `https://portfolio-website-phi-brown.vercel.app`
2. Open DevTools (F12 or Cmd+Option+I)
3. Check the Network tab - you should see `widget-visibility-fix.css` loaded
4. Check the bottom-right corner - the widget bubble should be visible
5. Click the bubble to open the chat window

---

## Troubleshooting

### Widget Still Not Visible?

1. **Clear browser cache**: Hard refresh (Ctrl+Shift+R or Cmd+Shift+R)
2. **Check CSS is loading**: Open DevTools Network tab and verify CSS file loads
3. **Run diagnostic**: Open browser console and run:
   ```javascript
   // Check for widget elements
   document.querySelectorAll('[class*="shopbot"]').forEach((el, i) => {
     console.log(`Element ${i}:`, {
       tag: el.tagName,
       class: el.className,
       visible: el.offsetParent !== null,
       zIndex: getComputedStyle(el).zIndex
     });
   });
   ```

### CSS File Not Loading?

1. Verify Vercel deployment completed successfully
2. Check the CSS URL in browser - should return CSS content
3. Check for CORS errors in console
4. Try accessing CSS file directly in browser

---

## Alternative: Inline CSS

If linking external CSS doesn't work, you can add the CSS directly to your portfolio site's HTML:

```html
<style>
  /* Add this before closing </head> tag */
  [class*="shopbot"] {
      display: block !important;
      visibility: visible !important;
      opacity: 1 !important;
  }

  .shopbot-chat-bubble,
  [class*="shopbot-bubble"] {
      display: block !important;
      visibility: visible !important;
      opacity: 1 !important;
      position: fixed !important;
      z-index: 2147483647 !important;
      cursor: pointer !important;
      pointer-events: auto !important;
  }

  .shopbot-chat-window,
  [class*="shopbot-window"] {
      display: block !important;
      visibility: visible !important;
      opacity: 1 !important;
      z-index: 2147483647 !important;
  }
</style>
```

---

## Next Steps

After widget is visible:

1. **Test FAQ clicks**: Click FAQ buttons and verify they're tracked
2. **Check FAQ Usage Widget**: Log into admin panel and view FAQ Usage Widget
3. **Verify analytics**: Check that FAQ clicks appear in analytics dashboard

---

## Files Changed

- ✅ `frontend/public/widget-visibility-fix.css` - CSS fix file (now in Vercel)
- ✅ `WIDGET_INVISIBLE_FIX.md` - Comprehensive troubleshooting guide
- ✅ `widget-diagnostic-page.html` - Diagnostic tool
- ✅ `widget-diagnostic.js` - Console diagnostic script

All committed and pushed to `main` branch! 🎉
