# Widget CDN Setup Guide

This document describes the CDN URL patterns, versioning strategy, and provider configuration for distributing the ShopBot widget.

## Production URLs

### Versioned URL (Recommended for Production)

```
https://cdn.yourbot.com/widget/v/{version}/widget.umd.js
```

Example: `https://cdn.yourbot.com/widget/v/1.0.0/widget.umd.js`

### Latest URL (Development/Testing Only)

```
https://cdn.yourbot.com/widget/latest/widget.umd.js
```

> **Note:** Use versioned URLs in production for maximum cache efficiency and stability. The "latest" URL is for development/testing only.

## Environment-Specific URLs

| Environment | Base URL | Use Case |
|-------------|----------|----------|
| Production | `cdn.yourbot.com` | Live merchant websites |
| Staging | `cdn-staging.yourbot.com` | Pre-release testing |
| Development | Local serve | Development builds |

### Local Development

For local development, serve the widget from the build output:

```bash
cd frontend
npm run build:widget
npx serve dist/widget -p 3001
# Widget available at http://localhost:3001/widget.umd.js
```

## Version Format

The widget uses **Semantic Versioning (SemVer)**: `MAJOR.MINOR.PATCH`

| Component | When to Increment | Example |
|-----------|-------------------|---------|
| MAJOR | Breaking changes | 1.0.0 → 2.0.0 |
| MINOR | New features, backward compatible | 1.0.0 → 1.1.0 |
| PATCH | Bug fixes, backward compatible | 1.0.0 → 1.0.1 |

### Version Embedding

The widget version is embedded at build time and accessible at runtime:

```javascript
// Check installed version in browser console
console.log(window.ShopBotWidget.version); // "1.0.0"
```

## CDN Provider Selection

| Provider | Pros | Cons | Recommendation |
|----------|------|------|----------------|
| CloudFront | AWS integration, global reach | Complex configuration | If using AWS infrastructure |
| Cloudflare | Easy setup, generous free tier | Limited edge rules | **Recommended for MVP** |
| Fastly | VCL flexibility, real-time purging | Higher cost | If custom caching logic needed |

### For This Project

**Start with Cloudflare** (free tier, easy setup):
1. Create Cloudflare account
2. Add `cdn.yourbot.com` as custom hostname
3. Configure Page Rules for caching (see [widget-cdn-caching.md](./widget-cdn-caching.md))
4. Set up SSL/TLS certificate

## Custom Domain Configuration

To use a custom CDN domain:

1. **DNS Configuration**: Add CNAME record pointing to CDN provider
   ```
   cdn.yourbot.com → [cdn-provider-endpoint]
   ```

2. **SSL Certificate**: Configure SSL/TLS at CDN level
   - Use Let's Encrypt (free) or provider-managed certificates
   - Enable HTTP/2 for better performance

3. **CORS Headers**: Ensure CDN passes CORS headers from origin
   ```
   Access-Control-Allow-Origin: *
   Access-Control-Allow-Methods: GET, HEAD, OPTIONS
   ```

## URL Pattern Examples

### Basic Integration (Versioned)

```html
<script>
  window.ShopBotConfig = {
    merchantId: 'YOUR_MERCHANT_ID'
  };
</script>
<script src="https://cdn.yourbot.com/widget/v/1.0.0/widget.umd.js" async></script>
```

### ES Module Import (Versioned)

```html
<script type="module">
  import { initWidget } from 'https://cdn.yourbot.com/widget/v/1.0.0/widget.es.js';
  initWidget({ merchantId: 'YOUR_MERCHANT_ID' });
</script>
```

### Latest Version (Development Only)

```html
<script src="https://cdn.yourbot.com/widget/latest/widget.umd.js" async></script>
```

## Related Documentation

- [Widget CDN Caching](./widget-cdn-caching.md) - Cache header configuration
- [Widget Release Process](./widget-release-process.md) - Release checklist and CI/CD
- [Widget Integration Guide](./widget-integration-guide.md) - Full integration docs
- [Widget Quick Start](./widget-quick-start.md) - 5-minute setup guide

## Implementation Checklist

- [ ] Configure CDN provider (Cloudflare recommended)
- [ ] Set up custom domain with SSL
- [ ] Configure cache headers (see widget-cdn-caching.md)
- [ ] Test versioned URL access
- [ ] Set up CI/CD for automated deployments
- [ ] Monitor CDN performance and cache hit ratios
