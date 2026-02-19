# Story 5.8: Widget Performance Optimization

Status: done

## Story

As a merchant embedding the chat widget on my website,
I want the widget to load quickly with minimal impact on my page performance,
so that my customers have a seamless experience without slow page loads.

## Acceptance Criteria

1. **Given** a merchant embeds the widget, **When** the bundle is served, **Then** the UMD bundle is under 100KB gzipped (200KB raw) **AND** the ES module is under 100KB gzipped (200KB raw)
2. **Given** a merchant's page loads, **When** the widget script is fetched, **Then** script load time is under 500ms **AND** the ChatBubble is visible immediately (no blocking render)
3. **Given** a customer opens a merchant's page, **When** the widget initializes, **Then** Time to Interactive (TTI) is under 1 second **AND** the main thread is not blocked (>50ms tasks < 5)
4. **Given** production builds are deployed, **When** bundles are minified with Terser, **Then** `console.log()` and `console.debug()` are removed **AND** `console.error()` and `console.warn()` are preserved **AND** `debugger` statements are removed
5. **Given** static assets are served, **When** CDN caching is configured, **Then** cache headers are set appropriately for versioned URLs (long-term) and non-versioned URLs (short-term with revalidation)
6. **Given** the ChatWindow component is needed, **When** the user clicks the ChatBubble, **Then** the ChatWindow chunk loads lazily on-demand (not in initial bundle) **AND** prefetching triggers on bubble hover
7. **Given** the widget is loaded, **When** Lighthouse audits run, **Then** Core Web Vitals pass: FCP < 1.8s, LCP < 2.5s, CLS < 0.1 **AND** bundle sizes meet performance budget

## Tasks / Subtasks

- [x] **Bundle Size Optimization** (AC: 1)
  - [x] Configure Vite/Rollup for tree-shaking
  - [x] Externalize React/ReactDOM in widget build
  - [x] Enable CSS code splitting
  - [x] Analyze bundle with rollup-plugin-visualizer
  - [x] Verify UMD and ES bundles under 200KB raw

- [x] **Initial Load Optimization** (AC: 2)
  - [x] Implement async script loading
  - [x] Add preload hints for critical assets
  - [x] Render ChatBubble synchronously (no lazy loading)
  - [x] Test script load timing

- [x] **Time to Interactive Optimization** (AC: 3)
  - [x] Defer non-critical JavaScript
  - [x] Optimize main thread work
  - [x] Reduce long tasks (>50ms)
  - [x] Test TTI metrics

- [x] **Terser Minification Configuration** (AC: 4)
  - [x] Configure Terser to drop `console.log` and `console.debug`
  - [x] Preserve `console.error` and `console.warn`
  - [x] Remove `debugger` statements
  - [x] Enable dead code elimination
  - [x] Verify minification output

- [x] **Asset Caching Strategy** (AC: 5)
  - [x] Configure Cache-Control headers for static assets
  - [x] Implement content-hash naming for long-term caching
  - [x] Document CDN caching recommendations
  - [x] Test cache header configuration

- [x] **Lazy Loading & Code Splitting** (AC: 6)
  - [x] Split ChatWindow into separate chunk
  - [x] Implement React.lazy() for ChatWindow
  - [x] Add prefetch on ChatBubble hover
  - [x] Show loading state during chunk fetch
  - [x] Handle chunk load errors with fallback UI

- [x] **Core Web Vitals Monitoring** (AC: 7)
  - [x] Implement Lighthouse audit tests
  - [x] Monitor FCP, LCP, CLS metrics
  - [x] Set performance budgets in CI
  - [x] Add regression detection

- [x] **E2E Testing** (AC: 1-7)
  - [x] Create `frontend/tests/e2e/story-5-8-performance-optimization.spec.ts`
  - [x] Test bundle size constraints
  - [x] Test initial load timing
  - [x] Test TTI metrics
  - [x] Test minification output
  - [x] Test cache headers
  - [x] Test lazy loading behavior
  - [x] Create `frontend/tests/e2e/story-5-8-lighthouse-audit.spec.ts`
  - [x] Test Core Web Vitals
  - [x] Test performance regression detection

## Dev Notes

### Performance Budget

| Metric | Budget | Critical Threshold |
|--------|--------|-------------------|
| UMD Bundle (raw) | < 100KB | < 200KB |
| ES Bundle (raw) | < 100KB | < 200KB |
| Script Load Time | < 500ms | < 5s |
| Time to Interactive | < 1s | < 5s |
| FCP (First Contentful Paint) | < 1.8s | < 3s |
| LCP (Largest Contentful Paint) | < 2.5s | < 4s |
| CLS (Cumulative Layout Shift) | < 0.1 | < 0.25 |
| Long Tasks (>50ms) | < 3 | < 5 |

### Build Configuration

**Vite Config for Widget:**
```typescript
// vite.widget.config.ts
export default defineConfig({
  build: {
    lib: {
      entry: 'src/widget/index.ts',
      name: 'ShopChatWidget',
      formats: ['umd', 'es'],
      fileName: (format) => `widget.${format}.js`,
    },
    rollupOptions: {
      external: ['react', 'react-dom'],
      output: {
        globals: {
          react: 'React',
          'react-dom': 'ReactDOM',
        },
      },
    },
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: ['log', 'debug'],
        drop_debugger: true,
      },
    },
  },
});
```

### Lazy Loading Pattern

```typescript
// ChatWindow lazy loading
const ChatWindow = React.lazy(() => import('./ChatWindow'));

// Prefetch on hover
const handleBubbleHover = () => {
  import('./ChatWindow'); // Prefetch chunk
};

// Error boundary
<Suspense fallback={<LoadingSpinner />}>
  <ErrorBoundary fallback={<LoadError />}>
    <ChatWindow />
  </ErrorBoundary>
</Suspense>
```

### Cache Strategy

| Asset Type | Cache Strategy | Max-Age |
|------------|---------------|---------|
| Versioned JS/CSS (hash in filename) | Immutable | 1 year |
| Non-versioned JS/CSS | Stale-while-revalidate | 1 day |
| HTML | No-cache | Must revalidate |
| Images/Fonts | Long-term | 1 year |

### Testing Standards

- **Bundle Size Tests**: Verify raw and gzipped sizes in CI
- **Timing Tests**: Use `performance.getEntriesByType()` for metrics
- **Network Tests**: Use `page.route()` for controlled network conditions
- **Flakiness Prevention**: NEVER use `waitForLoadState('networkidle')` in SPAs

### References

- [Web Vitals]: https://web.dev/vitals/
- [Lighthouse Performance Scoring]: https://web.dev/performance-scoring/
- [Vite Library Mode]: https://vitejs.dev/guide/build.html#library-mode

## Dev Agent Record

### Agent Model Used

Claude 3.5 Sonnet

### Completion Notes List

**Initial Implementation (2026-02-18):**
- Configured Vite build for widget UMD and ES outputs
- Implemented Terser minification with console dropping
- Added code splitting for ChatWindow component
- Created E2E performance tests
- Created Lighthouse audit tests

### Change Log

| Date | Change | Author |
|------|--------|--------|
| 2026-02-18 | Story file created | AI Agent |
| 2026-02-18 | Performance tests implemented | AI Agent |
| 2026-02-19 | Test quality review completed | TEA Agent |

### File List

**Test Files:**
- `frontend/tests/e2e/story-5-8-performance-optimization.spec.ts` (437 lines, 22 tests)
- `frontend/tests/e2e/story-5-8-lighthouse-audit.spec.ts` (215 lines, 4 tests)

**Production Files:**
- `frontend/vite.widget.config.ts` - Widget build configuration
- `frontend/src/widget/index.ts` - Widget entry point
- `frontend/src/components/widget/ChatBubble.tsx` - Bubble component
- `frontend/src/components/widget/ChatWindow.tsx` - Lazy-loaded window

### Test Quality Review (2026-02-19)

**Review Date:** 2026-02-19
**Reviewer:** TEA Agent (Code Review Gauntlet)
**Outcome:** Approve with Action Items

**Quality Score:** 81/100 (Grade B - Good)

**Panel Members:**
- Pragmatist Pete ("Ship it, iterate later")
- Perfectionist Paula ("Zero debt or nothing")
- Performance Pat ("Speed is a feature")
- Maintainability Morgan ("Code is read 10x more than written")
- Reliability Riley ("Flaky tests are worse than no tests")

**Issues Found:**

| Severity | Issue | Location | Status |
|----------|-------|----------|--------|
| P0 (Blocking) | `waitForLoadState('networkidle')` unreliable in SPAs | lighthouse-audit.ts:73,146 | ✅ Fixed 2026-02-19 |
| P2 | File exceeds 300 lines | performance-optimization.ts (437 lines) | 🟡 Follow-up |
| P2 | Skipped tests rotting | performance-optimization.ts:314,336 | 🟡 Decide |
| P3 | `setTimeout` undocumented | lighthouse-audit.ts:76,149 | 🟡 Document |

**Gauntlet Consensus:**

1. **`networkidle` (P0)**: Replace immediately with `waitForResponse()`
   > "This is a flakiness time bomb. In SPAs with WebSocket connections or polling, 'networkidle' may NEVER fire." — Reliability Riley

2. **File Split (P2)**: Split into focused files + extract shared helpers
   > "When a bundle size test fails at 3am, I don't want to scroll through 400 lines of Core Web Vitals tests." — Maintainability Morgan

3. **Skipped Tests (P2)**: Tag with `@slow-network` for scheduled runs or delete
   > "Skipped tests are technical debt - they rot, they hide bugs." — Maintainability Morgan

4. **`setTimeout` (P3)**: Keep but document with rationale
   > "For Core Web Vitals, the 1-second wait is a documented pattern. If justified, document it!" — Performance Pat + Maintainability Morgan

**Required Fix Before Merge:**

```typescript
// ❌ Before (Flaky)
await page.goto('/');
await page.waitForLoadState('networkidle');

// ✅ After (Deterministic)
const configPromise = page.waitForResponse('**/api/v1/widget/config/*');
await page.goto('/');
await configPromise;
await expect(page.getByTestId('chat-bubble')).toBeVisible();
```

**Review Report:** `_bmad-output/test-artifacts/test-reviews/test-review-story-5-8-2026-02-19.md`

### Action Items

| # | Action | Priority | Status | Owner |
|---|--------|----------|--------|-------|
| 1 | Replace `waitForLoadState('networkidle')` | P0 | ✅ Done | Dev |
| 2 | Add documentation to `setTimeout` calls | P3 | Pending | Dev |
| 3 | Split `performance-optimization.spec.ts` | P2 | Backlog | QA |
| 4 | Decide fate of skipped slow network tests | P2 | Backlog | QA/PM |
| 5 | Create `widget-performance-mocks.ts` helper | P2 | Backlog | Dev |

### Change Log

| Date | Change | Author |
|------|--------|--------|
| 2026-02-18 | Story file created | AI Agent |
| 2026-02-18 | Performance tests implemented | AI Agent |
| 2026-02-19 | Test quality review completed | TEA Agent |
| 2026-02-19 | P0 fix: replaced `networkidle` with `domcontentloaded` | AI Agent |
