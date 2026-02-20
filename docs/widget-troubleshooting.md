# Widget Troubleshooting Guide

This guide helps you diagnose and resolve common issues with the ShopBot widget.

## Quick Diagnostics

Run these checks first when troubleshooting:

1. **Open Browser Console** (F12 → Console tab)
2. **Check for errors** - Red error messages indicate issues
3. **Enable debug mode** - Add `debug: true` to your config
4. **Check version** - Run `window.ShopBotWidget.version`

## Common Issues

### Widget Not Appearing

**Symptoms:** Chat bubble doesn't appear on page

**Solutions:**

1. **Check merchant ID is correct**
   ```html
   <!-- Verify this matches your dashboard -->
   window.ShopBotConfig = { merchantId: 'YOUR_MERCHANT_ID' };
   ```

2. **Verify widget is enabled**
   - Go to Settings > Widget
   - Ensure "Enable Widget" toggle is ON

3. **Check browser console for errors**
   - Open DevTools (F12)
   - Look for red error messages
   - Common errors:
     - `Missing merchantId` - Config not set correctly
     - `Invalid merchantId format` - ID should be 8-64 alphanumeric chars

4. **Verify domain is whitelisted**
   - If you configured domain whitelist, ensure current domain is included
   - Go to Settings > Widget > Security > Allowed Domains

5. **Check script loading**
   ```javascript
   // In console, verify script loaded
   typeof window.ShopBotWidget  // Should be 'object', not 'undefined'
   ```

6. **Clear browser cache**
   - Hard refresh: Ctrl+Shift+R (Windows) or Cmd+Shift+R (Mac)

### Messages Not Sending

**Symptoms:** Messages appear stuck or show error

**Solutions:**

1. **Check network connectivity**
   - Open Network tab in DevTools
   - Look for failed requests to `api.yourbot.com`

2. **Verify rate limits not exceeded**
   - Widget has rate limiting (60 messages/minute)
   - Wait 1 minute and try again

3. **Check session hasn't expired**
   - Sessions expire after 1 hour of inactivity
   - Refresh the page to create a new session

4. **Check for CORS errors**
   - Look for CORS errors in console
   - Ensure your domain is configured in widget settings

### Styling Conflicts

**Symptoms:** Widget looks broken or elements overlap

**Solutions:**

1. **Widget uses Shadow DOM**
   - Widget styles are isolated from page styles
   - Page CSS should not affect widget appearance

2. **Check z-index for visibility issues**
   - Widget uses z-index: 9999 by default
   - If you have higher z-index elements, they may overlap

3. **Verify container has sufficient space**
   - Widget needs space in bottom corner
   - Check for fixed elements that might overlap

4. **Theme configuration issues**
   ```javascript
   // Ensure colors are valid hex
   theme: {
     primaryColor: '#6366f1',  // Valid
     // primaryColor: 'blue',  // Invalid - use hex
   }
   ```

### Widget Loading Slowly

**Symptoms:** Long delay before widget appears

**Solutions:**

1. **Use versioned URLs**
   ```html
   <!-- Better: cached for 1 year -->
   <script src="https://cdn.yourbot.com/widget/v/1.0.0/widget.umd.js"></script>
   
   <!-- Worse: must revalidate every hour -->
   <script src="https://cdn.yourbot.com/widget/latest/widget.umd.js"></script>
   ```

2. **Check CDN availability**
   - Widget is served from CDN
   - Check status.yourbot.com for outages

3. **Enable script async loading**
   ```html
   <!-- Ensure async is present -->
   <script src="..." async></script>
   ```

### Session Errors

**Symptoms:** "Session not found" or similar errors

**Solutions:**

1. **Session expired**
   - Refresh the page
   - New session will be created automatically

2. **Invalid session state**
   - Clear localStorage: `localStorage.clear()`
   - Refresh the page

3. **Multiple tabs open**
   - Each tab maintains its own session
   - This is expected behavior

## Debug Mode

Enable debug mode for detailed logging:

```html
<script>
  window.ShopBotConfig = {
    merchantId: 'YOUR_MERCHANT_ID',
    debug: true  // Enable debug logging
  };
</script>
```

Debug mode provides:
- Detailed initialization logs
- API request/response logging
- State change notifications
- Error stack traces

**Remember to disable debug mode in production!**

## Error Codes Reference

| Code | Name | Description | Solution |
|------|------|-------------|----------|
| 8001 | SESSION_NOT_FOUND | Widget session expired or invalid | Refresh page to create new session |
| 8002 | RATE_LIMITED | Too many messages in short time | Wait 1 minute before retrying |
| 8003 | DOMAIN_NOT_ALLOWED | Current domain not in whitelist | Contact support to whitelist domain |
| 8004 | MERCHANT_DISABLED | Widget disabled in merchant settings | Enable widget in Settings > Widget |
| 8005 | INVALID_CONFIG | Configuration validation failed | Check ShopBotConfig format |

## Browser Compatibility

| Browser | Version | Status | Notes |
|---------|---------|--------|-------|
| Chrome | 90+ | ✅ Full support | Recommended |
| Firefox | 88+ | ✅ Full support | |
| Safari | 14+ | ✅ Full support | |
| Edge | 90+ | ✅ Full support | Chromium-based |
| IE 11 | - | ❌ Not supported | Use modern browser |

### Mobile Support

| Platform | Version | Status |
|----------|---------|--------|
| iOS Safari | 14+ | ✅ Supported |
| Android Chrome | 90+ | ✅ Supported |
| Android Firefox | 88+ | ✅ Supported |

## Support Escalation

If you can't resolve an issue:

### Step 1: Collect Information

Gather these details before contacting support:

1. **Merchant ID** - From Settings > Widget
2. **Browser and version** - e.g., Chrome 120.0.6099
3. **Operating system** - e.g., Windows 11, macOS 14
4. **Error messages** - Copy from browser console
5. **Network requests** - Screenshots from Network tab
6. **Steps to reproduce** - Detailed steps

### Step 2: Enable Debug Mode

```javascript
window.ShopBotConfig = {
  merchantId: 'YOUR_MERCHANT_ID',
  debug: true
};
```

Capture console output during the issue.

### Step 3: Contact Support

- **Email:** support@yourbot.com
- **Subject:** [Widget Issue] Brief description
- **Include:** All collected information from Step 1

### For Urgent Issues

Mark your support request as **"Widget Down"** for priority handling if:
- Widget not loading for all users
- Messages not being delivered
- Critical business impact

## Related Documentation

- [Widget Integration Guide](./widget-integration-guide.md) - Full integration docs
- [Widget Quick Start](./widget-quick-start.md) - 5-minute setup
- [Widget CDN Setup](./widget-cdn-setup.md) - CDN configuration
