# Widget CDN Caching Configuration

This document describes the caching strategy for serving the ShopBot widget from a CDN.

## URL Patterns and Cache Headers

### Versioned URLs (Recommended for Production)

```
URL: /widget/v/1.0.0/widget.umd.js
Cache-Control: public, max-age=31536000, immutable
```

Versioned URLs enable aggressive caching since the URL changes with each release. This provides:
- Maximum cache efficiency
- No validation requests needed
- Instant updates when new version is deployed

### Latest URL (Development/Testing)

```
URL: /widget/latest/widget.umd.js
Cache-Control: public, max-age=3600, must-revalidate
```

The "latest" URL is useful for development and testing but should not be used in production as it requires revalidation requests.

### Config API

```
URL: /api/v1/widget/config/{merchant_id}
Cache-Control: public, max-age=300
```

The config API has a short cache lifetime since it may change (theme updates, settings changes, etc.).

## Cache-Busting Strategy

### Filename Versioning

Include the version in the filename for long-term caching:

```
widget.v1.0.0.umd.js
widget.v1.0.0.es.js
```

### Loader Script Updates

The loader script includes the current version and is updated on each release:

```html
<script>
  (function() {
    var version = '1.0.0';
    var script = document.createElement('script');
    script.src = 'https://cdn.example.com/widget/v/' + version + '/widget.umd.js';
    document.head.appendChild(script);
  })();
</script>
```

## CDN Configuration Examples

### CloudFront (AWS)

```json
{
  "DistributionConfig": {
    "DefaultCacheBehavior": {
      "ViewerProtocolPolicy": "redirect-to-https",
      "AllowedMethods": ["GET", "HEAD"],
      "CachedMethods": ["GET", "HEAD"],
      "CachePolicyId": "658327ea-f89d-4fab-a63d-7e88639e58f6",
      "Compress": true
    },
    "CacheBehaviors": [
      {
        "PathPattern": "/widget/v/*",
        "CachePolicyId": "static-asset-cache-policy"
      },
      {
        "PathPattern": "/widget/latest/*",
        "CachePolicyId": "short-cache-policy"
      }
    ]
  }
}
```

### nginx Configuration

```nginx
# Versioned widget files - 1 year cache
location ~ ^/widget/v/[0-9]+\.[0-9]+\.[0-9]+/.*\.(js|css)$ {
    add_header Cache-Control "public, max-age=31536000, immutable";
    add_header Content-Type $content_type;
    gzip_static on;
}

# Latest widget files - 1 hour cache with revalidation
location ~ ^/widget/latest/.*\.(js|css)$ {
    add_header Cache-Control "public, max-age=3600, must-revalidate";
    add_header Content-Type $content_type;
    gzip_static on;
}

# Widget config API - 5 minute cache
location ~ ^/api/v1/widget/config/ {
    add_header Cache-Control "public, max-age=300";
    proxy_pass http://backend;
}
```

### Cloudflare Page Rules

| Pattern | Cache Level | Edge Cache TTL | Browser Cache TTL |
|---------|-------------|----------------|-------------------|
| `*example.com/widget/v/*` | Cache Everything | 1 year | 1 year |
| `*example.com/widget/latest/*` | Cache Everything | 1 hour | 1 hour |
| `*example.com/api/v1/widget/*` | Standard | 5 minutes | 5 minutes |

## Performance Benefits

| Metric | Without CDN | With CDN |
|--------|-------------|----------|
| First Load (cold) | 500-800ms | 200-400ms |
| Repeat Load (warm) | 200-400ms | 20-50ms |
| Geographic Latency | Variable | < 50ms globally |
| Server Load | High | Minimal |

## Implementation Checklist

- [ ] Configure CDN with versioned URL paths
- [ ] Set appropriate Cache-Control headers
- [ ] Enable gzip/Brotli compression
- [ ] Configure CORS headers if needed
- [ ] Set up CDN invalidation for emergency updates
- [ ] Monitor cache hit ratios
- [ ] Document version update process

## Related Files

- `frontend/vite.widget.config.ts` - Widget build configuration
- `frontend/dist/widget/` - Built widget files
- Story 5-9 - Full CDN setup and deployment

## Notes

- Actual CDN setup is handled in **Story 5-9: CDN Setup Documentation**
- This story (5-8) focuses on build optimization and caching documentation
- The widget bundle is designed to be < 100KB gzipped for optimal loading
