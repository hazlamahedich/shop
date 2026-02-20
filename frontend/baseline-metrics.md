# Widget Performance Baseline Metrics

**Date:** 2026-02-19
**Story:** 5-8 Performance Optimization
**Status:** Pre-optimization baseline

## Bundle Sizes (Raw)

| File | Size | Notes |
|------|------|-------|
| widget.es.js | 104.5 KB | ES module format |
| widget.umd.js | 114.1 KB | UMD format |
| widgetClient-CDIxDl9t.js | 132.1 KB | Vite internal chunk |
| widget.es.js.map | 206.3 KB | Source map |
| widget.umd.js.map | 571.7 KB | Source map |
| widgetClient-CDIxDl9t.js.map | 371.2 KB | Source map |

## Bundle Sizes (Gzipped)

| File | Gzipped | Target | Status |
|------|---------|--------|--------|
| widget.es.js | 25.1 KB | < 100 KB | ✅ PASS |
| widget.umd.js | 32.7 KB | < 100 KB | ✅ PASS |
| widgetClient-CDIxDl9t.js | 24.3 KB | N/A (internal) | - |

**Total widget gzipped:** ~82 KB (ES + widgetClient = end user download)

## Current Build Configuration

- **Sourcemaps:** Enabled (sourcemap: true)
- **Minification:** Terser
- **Console:** All console methods retained
- **React/ReactDOM:** Externalized ✓
- **Code Splitting:** Not configured (ChatWindow eager loaded)

## Optimization Targets

1. **Sourcemaps:** 1,149 KB total → Remove from production CDN
2. **Console statements:** Remove log/debug/info (keep error/warn)
3. **Lazy Loading:** ChatWindow → lazy load on demand
4. **Tree Shaking:** Verify all imports are tree-shakeable

## Expected Post-Optimization

- Sourcemaps: 0 KB (separate upload to error tracking)
- Console removal: ~2 KB savings
- Lazy loading: Faster Time to Interactive
- Target gzipped: < 80 KB
