# Widget Cache Header Configuration

This document describes the cache-busting strategy for the ShopBot widget. For CDN provider configurations (CloudFront, nginx, Cloudflare), see the related documentation.

## Cache Headers Summary

| URL Pattern | Cache-Control | Purpose |
|-------------|---------------|---------|
| `/widget/v/{version}/*` | `public, max-age=31536000, immutable` | Production (versioned) |
| `/widget/latest/*` | `public, max-age=3600, must-revalidate` | Development/testing |
| `/api/v1/widget/config/{id}` | `public, max-age=300` | Widget configuration |

## Cache-Busting Strategy

### For Versioned URLs

Versioned URLs use aggressive caching since the URL changes with each release:

```
URL: /widget/v/1.0.0/widget.umd.js
Cache-Control: public, max-age=31536000, immutable
```

**Benefits:**
- Maximum cache efficiency (1 year)
- No validation requests needed
- Instant updates when new version deployed (new URL)
- `immutable` flag prevents unnecessary revalidation

**Usage:**
```html
<script src="https://cdn.yourbot.com/widget/v/1.0.0/widget.umd.js"></script>
```

### For Latest URL

The latest URL has short cache with revalidation:

```
URL: /widget/latest/widget.umd.js
Cache-Control: public, max-age=3600, must-revalidate
```

**Benefits:**
- Always get the most recent version
- Reduced load on origin (1-hour cache)
- `must-revalidate` ensures fresh content

**Usage (Development Only):**
```html
<script src="https://cdn.yourbot.com/widget/latest/widget.umd.js"></script>
```

> **Warning:** Do not use `latest` in production. Use versioned URLs for stability and predictability.

### For Widget Config API

Configuration endpoint has short cache for flexibility:

```
URL: /api/v1/widget/config/{merchant_id}
Cache-Control: public, max-age=300
```

**Rationale:**
- Theme settings may change
- Rate limits may be updated
- Feature flags may toggle
- 5-minute cache balances freshness with performance

## CDN Provider Configuration

For detailed CDN provider configurations, see the [Widget CDN Caching](./widget-cdn-caching.md) document which includes:

- **CloudFront**: Cache policies and behaviors
- **nginx**: Location blocks and header configuration  
- **Cloudflare**: Page rules for caching

## Breaking Changes and Cache

When releasing breaking changes:

1. **Increment MAJOR version**
   ```bash
   npm version major  # 1.0.0 → 2.0.0
   ```

2. **Create migration guide**
   - Document deprecated APIs
   - Provide upgrade instructions

3. **Keep old version available**
   - Do not delete old versioned files
   - 90-day minimum overlap period

4. **Update documentation**
   - Link to migration guide
   - Announce deprecation timeline

## Cache Invalidation

For emergency fixes requiring immediate propagation:

### CloudFront
```bash
aws cloudfront create-invalidation \
  --distribution-id $DISTRIBUTION_ID \
  --paths "/widget/latest/*"
```

### Cloudflare
```bash
curl -X POST "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/purge_cache" \
  -H "Authorization: Bearer $API_TOKEN" \
  -d '{"files":["https://cdn.yourbot.com/widget/latest/widget.umd.js"]}'
```

### Best Practices
- Only invalidate `latest` URL (versioned URLs should never change)
- Use sparingly - invalidation costs money
- Plan releases to avoid emergency invalidations

## Performance Metrics

| Metric | Without CDN | With CDN |
|--------|-------------|----------|
| First Load (cold) | 500-800ms | 200-400ms |
| Repeat Load (warm) | 200-400ms | 20-50ms |
| Geographic Latency | Variable | < 50ms globally |
| Server Load | High | Minimal |

## Related Documentation

- [Widget CDN Setup](./widget-cdn-setup.md) - URL patterns and provider selection
- [Widget Release Process](./widget-release-process.md) - Deployment workflow
- [Widget CDN Caching](./widget-cdn-caching.md) - Detailed provider configs
