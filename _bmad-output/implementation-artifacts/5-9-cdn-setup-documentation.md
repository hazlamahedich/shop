# Story 5.9: CDN Setup & Documentation

Status: done

**Test Automation**: ✅ Verified (2026-02-20) - 12/12 tests passing (8 unit + 4 E2E), Quality Score: ~95/100
**Code Review**: ✅ Complete (2026-02-20) - 3 MEDIUM issues fixed, all ACs implemented

## Story

As a **merchant**,
I want **CDN-hosted widget with integration documentation**,
so that **I can reliably embed the widget and get help if needed**.

## Acceptance Criteria

1. **AC1: CDN URL Configuration** - Given the widget is ready for distribution, When merchant accesses the widget, Then CDN URL is configured (cdn.yourbot.com pattern documented), And the configuration supports custom domains

2. **AC2: Versioned Releases** - Given a new widget version is released, When merchants reference the widget, Then versioned URLs are supported (e.g., `/v/1.0.0/widget.umd.js`), And semantic versioning is documented

3. **AC3: Cache Headers** - Given widgets are served from CDN, When requests are made, Then versioned assets have 1-year cache with immutable flag, And latest URL has 1-hour cache with must-revalidate, And cache-busting strategy is documented

4. **AC4: Integration Documentation** - Given a merchant wants to embed the widget, When they read the documentation, Then step-by-step integration guide exists, And code examples for common scenarios are provided, And configuration options are fully documented

5. **AC5: Troubleshooting Guide** - Given a merchant encounters issues, When they check documentation, Then common errors are documented with solutions, And debug mode instructions are provided, And support escalation path is defined

6. **AC6: Quick Start Guide** - Given a new merchant, When they want to get started quickly, Then a 5-minute quick start exists, And minimal configuration example is shown, And "copy-paste" ready embed code is provided

## Tasks / Subtasks

| Task | Priority | AC Coverage | Description |
|------|----------|-------------|-------------|
| Task 1 | 🔴 BLOCKING | AC1, AC2 | Document CDN URL patterns and versioning strategy |
| Task 2 | AC3 | Document cache header configuration |
| Task 3 | AC4 | Create integration documentation |
| Task 4 | AC5 | Create troubleshooting guide |
| Task 5 | AC6 | Create quick start guide |

> **Note:** Full CDN E2E testing removed from scope - this is a documentation-only story. Version 
> visibility E2E test added for runtime behavior validation. Actual CDN deployment and testing 
> requires infrastructure setup and belongs in a deployment story.

- [x] **Task 1: Document CDN URL Patterns and Versioning** (AC: 1, 2) 🔴 BLOCKING

  - [x] **CREATE** `docs/widget-cdn-setup.md` with URL structure:
    ```markdown
    # CDN URL Patterns
    
    ## Production URLs
    - Versioned: https://cdn.yourbot.com/widget/v/{version}/widget.umd.js
    - Latest: https://cdn.yourbot.com/widget/latest/widget.umd.js
    
    ## Version Format
    - Semantic versioning: MAJOR.MINOR.PATCH (e.g., 1.0.0, 1.1.0)
    - Breaking changes: Increment MAJOR
    - New features: Increment MINOR
    - Bug fixes: Increment PATCH
    ```

  - [x] **DOCUMENT** environment-specific URLs:
    - Production: `cdn.yourbot.com`
    - Staging: `cdn-staging.yourbot.com`
    - Development: Local serve instructions

  - [x] **ADD** version embedding to build:
    
    **Step 1:** Update `frontend/vite.widget.config.ts`:
    ```typescript
    import { readFileSync } from 'fs';
    const pkg = JSON.parse(readFileSync('./package.json', 'utf-8'));
    
    export default defineConfig({
      // ... existing config ...
      define: {
        'process.env.NODE_ENV': JSON.stringify('production'),
        __VITE_WIDGET_VERSION__: JSON.stringify(pkg.version),
      },
    });
    ```
    
    **Step 2:** Update `frontend/src/widget/loader.ts` to expose version:
    ```typescript
    // Add after window.ShopBotWidget initialization
    if (typeof window !== 'undefined') {
      window.ShopBotWidget = {
        version: __VITE_WIDGET_VERSION__,
        init: initWidget,
        unmount: unmountWidget,
        isMounted: isWidgetMounted,
      };
    }
    ```
    
    **Step 3:** Add TypeScript declaration in `frontend/src/widget/vite-env.d.ts`:
    ```typescript
    declare const __VITE_WIDGET_VERSION__: string;
    ```
    
    - Document how to check installed version: `console.log(window.ShopBotWidget.version)`

  - [x] **CREATE** release checklist in `docs/widget-release-process.md`:
    1. Update version in `package.json`
    2. Run full test suite
    3. Build widget: `npm run build:widget`
    4. Verify bundle size: `npm run build:widget:size`
    5. Upload to CDN under versioned path
    6. Update `latest` symlink
    7. Tag git release
    
    **Add Breaking Change Migration Section:**
    ```markdown
    ## Breaking Change Migration
    
    When releasing v2.0.0:
    1. Create `docs/widget-migration-v1-to-v2.md`
    2. Document deprecated APIs and replacements
    3. Keep v1.x available for 90 days
    4. Add deprecation warnings to v1.x console
    ```
    
  - [x] **ADD** CDN Provider Selection to `docs/widget-cdn-setup.md`:
    ```markdown
    ## CDN Provider Selection
    
    | Provider | Pros | Cons | Recommendation |
    |----------|------|------|----------------|
    | CloudFront | AWS integration, global | Complex config | If using AWS |
    | Cloudflare | Easy setup, free tier | Limited edge rules | **Recommended for MVP** |
    | Fastly | VCL flexibility | Higher cost | If custom caching needed |
    
    **For this project:** Start with Cloudflare (free tier, easy setup).
    ```
    
  - [x] **ADD** CI/CD Integration section to `docs/widget-release-process.md`:
    ```yaml
    ## CI/CD Integration
    
    # .github/workflows/widget-release.yml
    name: Widget Release
    on:
      push:
        tags: ['widget-v*']
    
    jobs:
      deploy:
        runs-on: ubuntu-latest
        steps:
          - uses: actions/checkout@v4
          - uses: actions/setup-node@v4
            with:
              node-version: '20'
              cache: 'npm'
              cache-dependency-path: frontend/package-lock.json
          
          - name: Install dependencies
            run: cd frontend && npm ci
          
          - name: Build widget
            run: cd frontend && npm run build:widget
          
          - name: Verify bundle size
            run: cd frontend && npm run build:widget:size
          
          - name: Deploy to CDN
            run: |
              VERSION=${GITHUB_REF#refs/tags/widget-v}
              aws s3 sync frontend/dist/widget/ s3://cdn-bucket/widget/v/$VERSION/
              # Update latest symlink
              aws s3 sync frontend/dist/widget/ s3://cdn-bucket/widget/latest/ --delete
    ```

- [x] **Task 2: Document Cache Header Configuration** (AC: 3)

  - [x] **REFERENCE** existing CDN provider configs in `docs/widget-cdn-caching.md` (created in Story 5-8):
    - CloudFront, nginx, and Cloudflare configs already documented
    - **NO NEED TO DUPLICATE** - just link to existing doc

  - [x] **DOCUMENT** cache-busting strategy:
    ```markdown
    ## Cache-Busting Strategy
    
    ### For Versioned URLs
    URL: /widget/v/1.0.0/widget.umd.js
    Cache-Control: public, max-age=31536000, immutable
    
    ### For Latest URL
    URL: /widget/latest/widget.umd.js
    Cache-Control: public, max-age=3600, must-revalidate
    
    ### Breaking Changes
    When releasing breaking changes:
    1. Increment MAJOR version
    2. Document migration guide
    3. Keep old version available for 90 days
    ```

- [x] **Task 3: Create Integration Documentation** (AC: 4)

  - [x] **CREATE** `docs/widget-integration-guide.md`:
    ```markdown
    # Widget Integration Guide
    
    ## Prerequisites
    - Active merchant account
    - Widget enabled in settings
    - Merchant ID available
    
    ## Basic Integration
    ### Step 1: Get Your Merchant ID
    Navigate to Settings > Widget > Copy Merchant ID
    
    ### Step 2: Add Widget Script
    <script>
      window.ShopBotConfig = {
        merchantId: 'YOUR_MERCHANT_ID'
      };
    </script>
    <script src="https://cdn.yourbot.com/widget/latest/widget.umd.js" async></script>
    
    ## Advanced Configuration
    ### Theme Customization
    ### Position Options
    ### Event Callbacks
    ```

  - [x] **ADD** code examples for common scenarios:
    | Scenario | Code Example |
    |----------|--------------|
    | Basic embed | `<script>` tag only |
    | With theme | Config with `theme: {}` |
    | Custom position | `position: 'bottom-left'` |
    | Event tracking | `onMessage`, `onOpen` callbacks |
    | SPA integration | React/Vue component wrapper |

  - [x] **DOCUMENT** all configuration options:
    ```typescript
    interface ShopBotConfig {
      merchantId: string;           // Required
      theme?: {
        primaryColor?: string;      // Hex color
        backgroundColor?: string;
        textColor?: string;
        position?: 'bottom-right' | 'bottom-left';
        borderRadius?: number;      // 0-24
        width?: number;             // px
        height?: number;            // px
      };
      callbacks?: {
        onOpen?: () => void;
        onClose?: () => void;
        onMessage?: (message: string) => void;
        onError?: (error: Error) => void;
      };
      locale?: string;              // e.g., 'en-US'
      debug?: boolean;              // Enable debug logging
    }
    ```

  - [x] **CREATE** React component wrapper example:
    ```tsx
    // ShopBotWidget.tsx - For React SPAs
    import { useEffect } from 'react';
    
    interface Props {
      merchantId: string;
      theme?: Partial<ShopBotTheme>;
    }
    
    export function ShopBotWidget({ merchantId, theme }: Props) {
      useEffect(() => {
        window.ShopBotConfig = { merchantId, theme };
        const script = document.createElement('script');
        script.src = 'https://cdn.yourbot.com/widget/latest/widget.umd.js';
        script.async = true;
        document.body.appendChild(script);
        
        return () => {
          script.remove();
          delete (window as any).ShopBotConfig;  // Cleanup global
        };
      }, [merchantId, theme]);
      return null;
    }
    ```

- [x] **Task 4: Create Troubleshooting Guide** (AC: 5)

  - [x] **CREATE** `docs/widget-troubleshooting.md`:
    ```markdown
    # Widget Troubleshooting Guide
    
    ## Common Issues
    
    ### Widget Not Appearing
    1. Check merchant ID is correct
    2. Verify widget is enabled in settings
    3. Check browser console for errors
    4. Verify domain is whitelisted (if configured)
    
    ### Messages Not Sending
    1. Check network connectivity
    2. Verify rate limits not exceeded
    3. Check session hasn't expired (1-hour idle)
    
    ### Styling Conflicts
    1. Widget uses Shadow DOM for isolation
    2. Check z-index for visibility issues
    3. Verify container has sufficient space
    
    ## Debug Mode
    Enable debug logging:
    window.ShopBotConfig = {
      merchantId: 'xxx',
      debug: true
    };
    
    ## Error Codes Reference
    | Code | Name | Solution |
    |------|------|----------|
    | 8001 | SESSION_NOT_FOUND | Refresh page to create new session |
    | 8002 | RATE_LIMITED | Wait 1 minute before retrying |
    | 8003 | DOMAIN_NOT_ALLOWED | Contact support to whitelist domain |
    | 8004 | MERCHANT_DISABLED | Enable widget in settings |
    ```

  - [x] **ADD** browser compatibility table:
    | Browser | Version | Status |
    |---------|---------|--------|
    | Chrome | 90+ | ✅ Full support |
    | Firefox | 88+ | ✅ Full support |
    | Safari | 14+ | ✅ Full support |
    | Edge | 90+ | ✅ Full support |
    | IE 11 | - | ❌ Not supported |

  - [x] **DOCUMENT** support escalation:
    1. Check troubleshooting guide
    2. Enable debug mode and collect logs
    3. Contact support with: Merchant ID, browser/version, error messages
    4. For urgent issues: Mark as "Widget Down"

- [x] **Task 5: Create Quick Start Guide** (AC: 6)

  - [x] **CREATE** `docs/widget-quick-start.md`:
    ```markdown
    # Quick Start: 5-Minute Widget Setup
    
    ## Step 1: Enable Widget (30 seconds)
    1. Log into your merchant dashboard
    2. Go to **Settings > Widget**
    3. Toggle **Enable Widget** to ON
    4. Copy your **Merchant ID**
    
    ## Step 2: Add to Your Website (2 minutes)
    Paste this code before `</body>`:
    
    ```html
    <script>
      window.ShopBotConfig = {
        merchantId: 'PASTE_YOUR_MERCHANT_ID_HERE'
      };
    </script>
    <script src="https://cdn.yourbot.com/widget/latest/widget.umd.js" async></script>
    ```
    
    ## Step 3: Customize (2 minutes)
    Optional: Match your brand colors
    
    ```html
    <script>
      window.ShopBotConfig = {
        merchantId: 'YOUR_MERCHANT_ID',
        theme: {
          primaryColor: '#6366f1',
          position: 'bottom-right'
        }
      };
    </script>
    ```
    
    ## Step 4: Test (30 seconds)
    1. Open your website
    2. Click the chat bubble
    3. Send a test message
    4. Verify bot responds
    
    ## ✅ Done!
    Your AI shopping assistant is now live.
    
    ## Next Steps
    - [Customize appearance](./widget-integration-guide.md#theme)
    - [Set up welcome message](./widget-integration-guide.md#welcome)
    - [Track conversations](./merchant-dashboard-guide.md)
    ```

  - [x] **ADD** embed code generator section:
    ```markdown
    ## Embed Code Generator
    
    Copy and customize:
    
    | Setting | Default | Options |
    |---------|---------|---------|
    | Position | bottom-right | bottom-left |
    | Primary Color | #6366f1 | Any hex |
    | Width | 380px | 300-500px |
    | Height | 600px | 400-800px |
    ```
    
> **Note:** This is primarily a documentation-only story. Version visibility E2E test added for 
> runtime behavior. Full CDN E2E tests require a deployed CDN and belong in a separate 
> deployment/integration story.

## Dev Notes

### Context from Previous Stories

| Story | Component | Status | Relevance |
|-------|-----------|--------|-----------|
| 5-1 | Backend Widget API | ✅ Done | API endpoints documented |
| 5-2 | Widget Session Management | ✅ Done | Session lifecycle docs |
| 5-3 | Widget Frontend Components | ✅ Done | Component usage examples |
| 5-4 | Build System & Loader Script | ✅ Done | Build process reference |
| 5-5 | Theme Customization System | ✅ Done | Theme config documentation |
| 5-6 | Merchant Widget Settings UI | ✅ Done | Settings page reference |
| 5-7 | Security & Rate Limiting | ✅ Done | Error codes, security docs |
| 5-8 | Performance Optimization | ✅ Done | CDN caching docs started |

### Existing Documentation (To Extend)

| File | Created In | Extension Needed |
|------|------------|------------------|
| `docs/widget-cdn-caching.md` | Story 5-8 | Add CDN provider configs |
| `frontend/vite.widget.config.ts` | Story 5-4 | Add version embedding |

### Widget Error Codes (8000-8999)

Documented in Story 5-7, include in troubleshooting guide:
- 8001: WIDGET_SESSION_NOT_FOUND
- 8002: WIDGET_RATE_LIMITED
- 8003: WIDGET_DOMAIN_NOT_ALLOWED
- 8004: WIDGET_MERCHANT_DISABLED
- 8005: WIDGET_INVALID_CONFIG

### CDN Architecture (Reference)

```
┌─────────────────────────────────────────────────────────────────┐
│                    CDN Distribution Flow                         │
│                                                                   │
│  Build (CI/CD)                                                   │
│  └── npm run build:widget                                        │
│      └── dist/widget/                                            │
│          ├── widget.umd.js                                       │
│          ├── widget.es.js                                        │
│          └── chunks/                                             │
│              │                                                    │
│              ▼ Upload to CDN                                     │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  cdn.yourbot.com/                                           │ │
│  │  ├── widget/                                                │ │
│  │  │   ├── v/                                                 │ │
│  │  │   │   ├── 1.0.0/   (immutable, 1-year cache)            │ │
│  │  │   │   ├── 1.1.0/   (immutable, 1-year cache)            │ │
│  │  │   │   └── ...                                            │ │
│  │  │   └── latest/    (1-hour cache, must-revalidate)        │ │
│  └────────────────────────────────────────────────────────────┘ │
│              │                                                    │
│              ▼ Merchant Website                                  │
│  <script src="https://cdn.yourbot.com/widget/latest/...">       │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

### Pre-Development Checklist

Before starting implementation, verify:
- [ ] **CSRF Token**: Not applicable - documentation only
- [ ] **Python Version**: Not applicable - frontend/docs only
- [ ] **Message Encryption**: Not applicable - no message changes
- [ ] **External Integration**: Not applicable - documentation only
- [ ] **Story 5-8 Complete**: CDN caching docs exist as foundation
- [ ] **Widget Build Working**: `npm run build:widget` succeeds

### Project Structure Notes

```
docs/
├── widget-cdn-setup.md          # NEW - CDN URL patterns, provider selection
├── widget-cdn-caching.md        # REFERENCE - Existing caching docs (Story 5-8)
├── widget-integration-guide.md  # NEW - Full integration docs
├── widget-troubleshooting.md    # NEW - Error guide
├── widget-quick-start.md        # NEW - 5-minute setup
├── widget-release-process.md    # NEW - Release checklist, CI/CD, migration guide
└── widget-migration-*.md        # FUTURE - Breaking change guides

frontend/
├── vite.widget.config.ts        # MODIFY - Add version embedding (VITE_WIDGET_VERSION)
├── src/widget/
│   ├── loader.ts                # MODIFY - Expose window.ShopBotWidget.version
│   └── types.d.ts               # NEW - Add __VITE_WIDGET_VERSION__ declaration
└── package.json                 # Version source
```

### Run Commands

```bash
# Build widget (verify build works with version embedding)
cd frontend && npm run build:widget

# Check bundle size
npm run build:widget:size

# Verify version is embedded in build
grep -r "VITE_WIDGET_VERSION" dist/widget/widget.umd.js || echo "Version not found!"

# Validate documentation links (manual)
# Open each doc file and verify links resolve

# Test version detection in browser console
# After loading widget: console.log(window.ShopBotWidget.version)
```

### Testing Strategy

| Test Type | Tool | File | Target |
|-----------|------|------|--------|
| Link Validation | Manual | All doc files | Links resolve |
| Code Examples | Manual | All doc files | Syntax valid |
| Version Embedding | Unit | `test_widget-version.test.ts` | Version exposed correctly |
| Version Visibility | E2E | `story-5-9-version-visibility.spec.ts` | Version accessible after load |

> **Note:** Full CDN E2E tests (URL accessibility, cache headers, versioned URLs) require 
> deployed CDN infrastructure and belong in a separate deployment story.

### References

- [Source: _bmad-output/planning-artifacts/epics/epic-5-embeddable-widget.md#Story 5.9]
- [Source: _bmad-output/implementation-artifacts/5-8-performance-optimization.md] - Previous story, CDN caching docs
- [Source: _bmad-output/implementation-artifacts/5-7-security-rate-limiting.md] - Error codes
- [Source: docs/widget-cdn-caching.md] - Existing caching documentation
- [Source: frontend/vite.widget.config.ts] - Build configuration

## Dev Agent Record

### Agent Model Used

Claude (glm-5) via OpenCode

### Debug Log References

None - documentation-only story.

### Completion Notes List

**2026-02-19 Implementation Complete:**

All 5 tasks completed successfully:

1. **Task 1: CDN URL Patterns and Versioning** ✅
   - Created `docs/widget-cdn-setup.md` with URL structure, environment URLs, CDN provider selection
   - Added version embedding to `vite.widget.config.ts` (reads from package.json)
   - Updated `loader.ts` to expose `window.ShopBotWidget.version`
   - Created `vite-env.d.ts` for TypeScript declaration
   - Created `docs/widget-release-process.md` with release checklist, CI/CD, breaking change migration

2. **Task 2: Cache Header Configuration** ✅
   - Created `docs/widget-cache-headers.md` with cache-busting strategy
   - References existing `docs/widget-cdn-caching.md` for provider configs

3. **Task 3: Integration Documentation** ✅
   - Created `docs/widget-integration-guide.md` with full integration docs
   - Includes configuration options, theme customization, event callbacks
   - React component wrapper example

4. **Task 4: Troubleshooting Guide** ✅
   - Created `docs/widget-troubleshooting.md` with common issues and solutions
   - Error codes reference (8001-8005)
   - Browser compatibility table
   - Debug mode instructions

5. **Task 5: Quick Start Guide** ✅
   - Created `docs/widget-quick-start.md` with 5-minute setup guide
   - Copy-paste ready embed code examples
   - Embed code generator section

**Tests:**
- Created `test_widget-version.test.ts` - 3 tests passing
- Created `test_widget-performance.test.ts` - 5 tests passing  
- Created `story-5-9-version-visibility.spec.ts` - 2 E2E tests (2026-02-20)
- Widget build verified: 33.94 KB gzipped (under 100KB target)
- Version embedding verified: `window.ShopBotWidget.version` returns "0.1.0"

### E2E Test Addition (2026-02-20)

**Gap Analysis (TEA Test Architect + Advanced Elicitation):**
Story 5-9 was initially classified as "documentation-only" with no E2E tests. Critical Perspective analysis via Advanced Elicitation identified that version embedding has runtime behavior that merits E2E validation.

**Resolution:**
- Generated `frontend/tests/e2e/story-5-9-version-visibility.spec.ts`
- Initial: 2 tests: Version accessibility after widget load, API method exposure
- Priority: P1 (1 test), P2 (1 test)

**Test Quality Review (2026-02-20):**

After initial test generation, a comprehensive test quality review was conducted:

| Review Stage | Score | Grade | Issues Found |
|--------------|-------|-------|--------------|
| Initial Review | 96/100 | A | Minor coverage gaps |
| Critical Challenge | 88/100 | B+ | P0 blockers found |
| After P0 Fixes | ~95/100 | A | All tests passing |

**Critical Issues Found (Critical Perspective Challenge):**

| Severity | Issue | Description | Status |
|----------|-------|-------------|--------|
| **P0** | API methods never called | Tests only checked `typeof`, never invoked methods | ✅ Fixed |
| **P0** | No failure handling test | Widget load failure was untested | ✅ Fixed |
| **P1** | Magic timeout values | `timeout: 10000` with no constant | ✅ Fixed |
| **P1** | Wrong route | Tests used `/widget-demo` (doesn't exist) | ✅ Fixed |
| **P2** | Missing BDD comments | No Given-When-Then documentation | Backlog |

**Critical Review Quote:**
> "The API methods test only verifies that methods **exist** - it never **calls** them! This is a placebo test that proves nothing about actual functionality." — Critical Perspective

**P0 Fixes Applied:**

1. **API Methods Test Now Calls Methods:**
```typescript
test('[P0] should call init, unmount, and isMounted methods correctly', async ({ page }) => {
  // Call isMounted() and verify return value
  const beforeInit = await page.evaluate(() => (window as any).ShopBotWidget.isMounted());
  expect(beforeInit).toBe(true);

  // Call unmount() and verify state change
  await page.evaluate(() => (window as any).ShopBotWidget.unmount());
  const afterUnmount = await page.evaluate(() => (window as any).ShopBotWidget.isMounted());
  expect(afterUnmount).toBe(false);

  // Call init() and verify re-initialization
  await page.evaluate(() => { (window as any).ShopBotWidget.init(); });
  const afterReinit = await page.evaluate(() => (window as any).ShopBotWidget.isMounted());
  expect(afterReinit).toBe(true);
});
```

2. **Widget Load Failure Test:**
```typescript
test('[P0] should handle widget script load failure', async ({ page }) => {
  await page.route('**/widget*.{js,ts}', route => route.abort('failed'));
  await page.goto('/widget-bundle-test.html');

  await expect.poll(
    async () => await page.evaluate(() => typeof (window as any).ShopBotWidget !== 'undefined'),
    { timeout: WIDGET_LOAD_TIMEOUT }
  ).toBe(false);
});
```

3. **Constants Extracted:**
```typescript
const WIDGET_LOAD_TIMEOUT = 15000;
const VERSION_REGEX = /^\d+\.\d+\.\d+$/;
```

4. **Route Fixed:** Changed `/widget-demo` → `/widget-bundle-test.html`

5. **Bundle Updated:** Copied fresh `widget.umd.js` to `public/dist/widget/`

**Final Test Results:**
```
Running 4 tests using 4 workers

  ✓ [P1] should expose version on window.ShopBotWidget after load (1.0s)
  ✓ [P0] should call init, unmount, and isMounted methods correctly (1.0s)
  ✓ [P0] should handle widget script load failure (872ms)
  ✓ [P2] should expose init, unmount, and isMounted methods (1.1s)

  4 passed (4.9s)
```

**Review Report:** `_bmad-output/test-reviews/test-review-story-5-9.md`

**Validation Command:**
```bash
cd frontend && npm run test:e2e -- tests/e2e/story-5-9-version-visibility.spec.ts --project=chromium
```

### Story Validation Improvements Applied (2026-02-19)

**Critical Fixes (2):**
1. **Removed Task 6 (E2E Testing)** - E2E tests not feasible for documentation-only story. CDN URLs are placeholders, no actual CDN exists. Testing belongs in deployment story.
2. **Added Explicit Version Embedding Code** - Task 1 now includes complete implementation with code for vite.widget.config.ts, loader.ts, and types.d.ts.

**Enhancements (2):**
3. **Added CDN Provider Selection** - Decision matrix for CloudFront/Cloudflare/Fastly with recommendation (Cloudflare for MVP).
4. **Added Migration Guide Template** - Breaking change process for v2.0.0 releases, 90-day deprecation period.

**Optimizations (3):**
5. **Removed Duplicate CDN Provider Table** - Task 2 now references existing docs/widget-cdn-caching.md instead of duplicating.
6. **Fixed React Wrapper Cleanup** - Added `delete window.ShopBotConfig` to cleanup function to prevent memory leaks.
7. **Added CI/CD Integration** - GitHub Actions workflow example for automated widget releases.

### File List

**New Files Created:**
- `docs/widget-cdn-setup.md` - CDN URL patterns, provider selection, versioning
- `docs/widget-release-process.md` - Release checklist, CI/CD, migration guide
- `docs/widget-cache-headers.md` - Cache-busting strategy
- `docs/widget-integration-guide.md` - Full integration documentation
- `docs/widget-troubleshooting.md` - Common issues and solutions
- `docs/widget-quick-start.md` - 5-minute setup guide
- `frontend/src/widget/vite-env.d.ts` - TypeScript declaration for version constant
- `frontend/src/widget/test_widget-version.test.ts` - Unit tests for version embedding
- `frontend/tests/e2e/story-5-9-version-visibility.spec.ts` - E2E tests for version visibility (4 tests, all passing)

**Modified Files:**
- `frontend/vite.widget.config.ts` - Added version embedding from package.json
- `frontend/src/widget/loader.ts` - Added window.ShopBotWidget.version exposure
- `frontend/tests/e2e/story-5-9-version-visibility.spec.ts` - E2E tests updated with P0 fixes (2026-02-20)

**Untracked Files (Copied Bundles for E2E Testing):**
- `frontend/public/dist/widget/widget.umd.js` - Fresh bundle copied for E2E tests (2026-02-20)
- `frontend/public/dist/widget/widget.es.js` - Fresh bundle copied for E2E tests (2026-02-20)

> **Note:** Git shows other modified files (`App.tsx`, `Settings.tsx`, `Widget.tsx`, etc.) from previous stories (5-5, 5-6, 5-8). These are not part of Story 5-9.

**Referenced Existing Files:**
- `docs/widget-cdn-caching.md` - CDN provider configurations (Story 5-8)
- `frontend/package.json` - Version source

**Bundle Build Output (Not Tracked):**
- `frontend/dist/widget/` - Build output directory (regenerated by `npm run build:widget`)
- `frontend/public/dist/widget/` - Copy of bundle for E2E testing (manual copy step)

### Test Automation Summary (2026-02-20)

**Execution Mode**: BMad-Integrated (TEA Test Architect) + Advanced Elicitation + Critical Perspective Challenge

| Metric | Value |
|--------|-------|
| Total Tests | 12 (8 unit + 4 E2E) |
| Unit Tests | 8 |
| API Tests | 0 (not applicable) |
| E2E Tests | 4 (2 P0 + 1 P1 + 1 P2) |
| Tests Passing | 12/12 (100%) ✅ |
| Bundle Size | 33.94 KB gzipped ✅ |
| Test Quality Score | ~95/100 (Grade A) |

**Gap Analysis (Advanced Elicitation):**
Story was initially classified as "documentation-only", but Critical Perspective analysis revealed that version embedding has runtime behavior meriting E2E validation. Gap resolved with new E2E test generation.

**Critical Perspective Challenge Applied:**
Initial tests scored 96/100 but critical review revealed P0 blockers (API methods never called, no failure test). After fixes, all 4 E2E tests pass with ~95/100 quality score.

**Acceptance Criteria Test Coverage:**

| AC | Description | Testable | Coverage |
|----|-------------|----------|----------|
| AC1 | CDN URL Configuration | ❌ Documentation only | N/A |
| AC2 | Versioned Releases | ✅ Version embedding | Unit + **E2E (4 tests)** |
| AC3 | Cache Headers | ❌ Documentation only | N/A |
| AC4 | Integration Documentation | ❌ Documentation only | N/A |
| AC5 | Troubleshooting Guide | ❌ Documentation only | N/A |
| AC6 | Quick Start Guide | ❌ Documentation only | N/A |

**Test Files:**

| File | Tests | Priority | Status |
|------|-------|----------|--------|
| `frontend/src/widget/test_widget-version.test.ts` | 3 | P1 | ✅ Passing |
| `frontend/src/widget/test_widget-performance.test.ts` | 5 | P2 | ✅ Passing |
| `frontend/tests/e2e/story-5-9-version-visibility.spec.ts` | 4 | P0: 2, P1: 1, P2: 1 | ✅ All Passing |

**E2E Tests (4 total):**
- `[P0] should call init, unmount, and isMounted methods correctly` ✅
- `[P0] should handle widget script load failure` ✅
- `[P1] should expose version on window.ShopBotWidget after load` ✅
- `[P2] should expose init, unmount, and isMounted methods` ✅

**Rationale for Limited E2E Tests:**
Story 5-9 is primarily documentation-only. E2E tests added only for version embedding (runtime behavior). Full CDN E2E tests require deployed CDN infrastructure and belong in a separate deployment story.

**Output**: `_bmad-output/test-reviews/test-review-story-5-9.md`

### Code Review Summary (2026-02-20)

**Review Mode**: Adversarial Code Review (BMad Code-Review Workflow)

| Metric | Value |
|--------|-------|
| ACs Implemented | 6/6 (100%) ✅ |
| Critical Issues | 0 |
| High Issues | 0 |
| Medium Issues | 3 (all fixed) |
| Low Issues | 5 (deferred) |
| Tests Passing | 12/12 ✅ |

**Issues Found and Fixed:**

| Severity | Issue | Resolution |
|----------|-------|------------|
| MEDIUM | File List incorrectly marked bundle files as "Modified" | Moved to "Untracked Files" section |
| MEDIUM | Git shows modified files not in File List | Added note explaining files from other stories |
| MEDIUM | Two widget bundle locations without documentation | Added step 5b to release-process.md |

**Files Updated in Review:**
- `_bmad-output/implementation-artifacts/5-9-cdn-setup-documentation.md` - File List section
- `_bmad-output/implementation-artifacts/sprint-status.yaml` - Status: review → done
- `docs/widget-release-process.md` - Added bundle copy step (5b)

### Change Log

| Date | Change | Author |
|------|--------|--------|
| 2026-02-19 | Initial story implementation | AI Agent |
| 2026-02-19 | Documentation created (5 docs) | AI Agent |
| 2026-02-20 | Initial E2E tests generated (2 tests) | TEA Agent |
| 2026-02-20 | Test quality review completed | TEA Agent |
| 2026-02-20 | Critical Perspective Challenge applied | TEA Agent |
| 2026-02-20 | P0 fixes: API methods called, failure test, constants | TEA Agent |
| 2026-02-20 | All 4 E2E tests passing (4.9s) | TEA Agent |
| 2026-02-20 | Widget bundle updated in public/dist | TEA Agent |
| 2026-02-20 | Code review: Fixed File List accuracy, added bundle copy docs | Code Review Agent |
| 2026-02-20 | QA Automate workflow: Verified all 12 tests passing | Quinn QA Agent |
| 2026-02-20 | Post-completion: Dynamic LLM pricing from OpenRouter API | Dev Agent |
| 2026-02-20 | Post-completion: LLM service integration & bot response fixes | Dev Agent |
| 2026-02-20 | Post-completion: Environment loading, API key UI, Gemini fixes | Dev Agent |
| 2026-02-20 | Post-completion: Allow updating API key for existing provider | Dev Agent |
| 2026-02-20 | Post-completion: Fix CSRF token for LLM provider API | Dev Agent |
| 2026-02-20 | Post-completion: Fix schema validation for provider updates | Dev Agent |
| 2026-02-20 | Post-completion: Fix Gemini API URL handling with colon in path | Dev Agent |
| 2026-02-20 | Post-completion: Fix Gemini role mapping and system prompts | Dev Agent |

### Post-Completion Updates

#### 2026-02-20: Dynamic LLM Pricing Fix

**Problem**: LLM providers had hardcoded pricing tables that became stale when OpenRouter updated prices. Cost calculations could be inaccurate.

**Solution**: Refactored all LLM providers to use dynamic pricing fetched from OpenRouter API via `ModelDiscoveryService`.

**Changes Made:**

| File | Change |
|------|--------|
| `backend/app/services/llm/model_discovery_service.py` | Added `get_model_pricing()`, `get_model_pricing_sync()`, `get_provider_info()` methods |
| `backend/app/services/llm/base_llm_service.py` | Updated `estimate_cost()` to use pricing from config |
| `backend/app/services/llm/openai_service.py` | Removed hardcoded `PRICING` dict |
| `backend/app/services/llm/anthropic_service.py` | Removed hardcoded `PRICING` dict |
| `backend/app/services/llm/gemini_service.py` | Removed hardcoded `PRICING` dict, fixed API key regex |
| `backend/app/services/llm/glm_service.py` | Removed hardcoded `PRICING` dict |
| `backend/app/services/llm/llm_factory.py` | Added `_enrich_config_with_pricing()`, `get_available_providers_async()` |
| `backend/app/services/llm/provider_switch_service.py` | Fixed Gemini API key regex, removed GLM format validation |
| `backend/app/core/config.py` | Updated `GEMINI_DEFAULT_MODEL` to `google/gemini-2.0-flash` |
| `backend/app/services/llm/test_llm_factory.py` | Updated tests to mock `is_testing()` |
| `frontend/src/components/onboarding/LLMStatus.tsx` | Enhanced provider card to display selected model prominently |

**Benefits:**
- Pricing always reflects current OpenRouter rates
- Single source of truth for model pricing
- Transparent cost tracking for merchants
- Fixed Gemini API key validation (keys start with `AIza`)
- Fixed GLM API key validation (format varies, rely on API test)

**Test Results**: All 24 LLM service tests passing

**Commit**: `4690a70e` - feat: dynamic LLM pricing from OpenRouter API

#### 2026-02-20: LLM Service Integration Fix

**Problem**: Preview and widget services failed with error "'coroutine' object has no attribute 'faq'" when testing the bot.

**Root Causes:**
1. Missing `await` on async `match_faq()` call
2. Incorrect LLMConfiguration attribute access (`provider_name` instead of `provider`)
3. Not building proper `llm_config` dict from model fields
4. Lazy loading of `llm_configuration` relationship in async context

**Solution**: Fixed all async/await issues and proper config building.

**Changes Made:**

| File | Change |
|------|--------|
| `backend/app/services/preview/preview_service.py` | Added `await` to `match_faq()`, fixed LLMConfiguration access, proper config building |
| `backend/app/services/widget/widget_message_service.py` | Same fixes for LLMConfiguration access and config building |
| `backend/app/api/helpers.py` | Added `selectinload(Merchant.llm_configuration)` for eager loading |

**Commit**: `3741abb9` - fix: LLM service integration for preview and widget

#### 2026-02-20: Bot Response & Greeting Flow Fix

**Problem**: 
1. "hi" incorrectly matched FAQ "shipping" (substring match)
2. Any first message triggered greeting instead of actual greeting words
3. Off-topic questions not gracefully redirected
4. Duplicate greeting configuration in UI

**Solution**: 
1. Fixed FAQ matching with word boundary checks
2. Only trigger greeting for actual greeting words ("hi", "hello", etc.)
3. Added off-topic redirect instructions to system prompt
4. Removed duplicate greeting config from BotConfig page

**Changes Made:**

| File | Change |
|------|--------|
| `backend/app/services/faq.py` | Fixed `_contains_question_match()` with word boundary check, min 4 chars |
| `backend/app/services/preview/preview_service.py` | Greeting only for actual greeting words, not any first message |
| `backend/app/services/personality/personality_prompts.py` | Added off-topic redirect instructions to `BASE_SYSTEM_PROMPT` |
| `frontend/src/pages/BotConfig.tsx` | Removed duplicate greeting config section, link to Personality page |

**Commit**: `240d501d` - fix: greeting and off-topic handling improvements

#### 2026-02-20: IS_TESTING Configuration Note

**Important**: The `.env` file has `IS_TESTING=true` by default, which uses mock LLM responses. To use real LLM providers (Gemini, OpenAI, etc.), set:

```bash
IS_TESTING=false
```

Then restart the backend for the change to take effect.

#### 2026-02-20: Environment Loading & API Key UI Fix

**Problem**: 
1. `.env` file not being loaded - `IS_TESTING` setting ignored
2. Gemini model name format issue with native API
3. No UI to update API key after initial configuration
4. Missing encryption key for API key storage

**Solution**:
1. Added `python-dotenv` to load `.env` file on startup
2. Strip `google/` prefix from model names for native Gemini API
3. Added API key input field to LLM Settings page
4. Set `FACEBOOK_ENCRYPTION_KEY` in `.env` for secure API key storage

**Changes Made:**

| File | Change |
|------|--------|
| `backend/app/core/config.py` | Add `python-dotenv` to load `.env` file before reading config |
| `backend/app/services/llm/gemini_service.py` | Strip `google/` prefix, handle empty model names, add debug logging |
| `frontend/src/components/settings/LLMSettings.tsx` | Add API key input field with show/hide toggle |
| `frontend/src/stores/llmStore.ts` | Add `switchProvider` action to update API key |

**Commits**: 
- `b55e9d4f` - Load .env file and handle OpenRouter model names in Gemini
- `bb37b6f7` - Add API key update UI in LLM settings

**Setup Required**:
1. Add to `.env`: `FACEBOOK_ENCRYPTION_KEY=<generated-key>`
2. Set `IS_TESTING=false` in `.env`
3. Restart backend
4. Go to Settings → LLM Provider and enter your real Gemini API key

#### 2026-02-20: Allow Updating API Key for Existing Provider

**Problem**: 
Users couldn't update their API key after initial configuration. The "Current Provider" button was disabled and clicking it did nothing.

**Solution**:
- Enable configuration modal for active providers
- Allow model-only updates without requiring new API key
- Properly handle API key encryption/decryption

**Changes Made:**

| File | Change |
|------|--------|
| `frontend/src/components/providers/ProviderCard.tsx` | Change disabled "Current Provider" button to "Update Configuration" button |
| `frontend/src/components/providers/ProviderConfigModal.tsx` | Show "Update Configuration" title for existing providers, allow model-only updates |
| `backend/app/services/llm/provider_switch_service.py` | Keep existing encrypted API key when updating same provider without new key |

**Commit**: `91e20af2` - feat: allow updating API key for existing LLM provider

**Usage**:
1. Go to Settings → LLM Provider (`/settings/provider`)
2. Click "Update Configuration" on the active provider card
3. Enter new API key (or leave empty to keep current)
4. Select model and click "Update Configuration"

#### 2026-02-20: Fix CSRF Token for LLM Provider API

**Problem**: 
The LLM provider switch/update API returned 500 error due to missing CSRF token.

**Root Cause**:
- Frontend service wasn't including CSRF token in POST requests
- Request body used camelCase instead of snake_case

**Solution**:
- Import `getCsrfToken` from csrfStore
- Add `X-CSRF-Token` header for state-changing methods (POST, PUT, DELETE, PATCH)
- Fix request body to use snake_case (provider_id, api_key, server_url)

**Commit**: `7394db64` - fix: add CSRF token to LLM provider API requests

#### 2026-02-20: Fix Schema Validation for Provider Updates

**Problem**: 
400 Bad Request when updating existing provider without providing new API key.

**Root Cause**:
The `SwitchProviderRequest` schema had validators that required `api_key` for cloud providers and `server_url` for Ollama, even for updates to existing providers.

**Solution**:
- Removed strict validation from schema level
- Service layer already handles using existing credentials when none provided
- Validation of connectivity happens in `test_provider_call` which will fail if no valid credentials exist

**Commit**: `bb93e890` - fix: allow optional API key for provider updates

#### 2026-02-20: Fix Gemini API URL Handling

**Problem**: 
400 Bad Request when using Gemini provider. The model name was being lost in the API URL.

**Root Cause**:
httpx misinterprets URLs with colons (`:`) in the path when using `base_url`. The Gemini API uses URLs like:
`https://.../models/gemini-2.5-flash-lite:generateContent`

The colon before `generateContent` was causing httpx to build an incorrect URL.

**Solution**:
- Build full URL manually instead of relying on httpx `base_url`
- Use fresh httpx.AsyncClient for each request (no base_url)
- Strip `google/` prefix from model names for native Gemini API

**Changes Made:**

| File | Change |
|------|--------|
| `backend/app/services/llm/gemini_service.py` | Build full URL manually, use fresh client for requests |
| `backend/app/services/llm/model_discovery_service.py` | Add `gemini-2.5-flash-lite` to fallback models |

**Commits**: 
- `de3b2dfc` - fix: Gemini API URL handling with colon in model path
- `e83e8fb9` - fix: improve error handling in LLM provider API
- `c80f4f29` - feat: add gemini-2.5-flash-lite to fallback models

**Note**: Your Gemini free tier quota for `gemini-2.0-flash` may be exhausted. Use `gemini-2.5-flash-lite` instead.

#### 2026-02-20: Fix Gemini Role Mapping and System Prompts

**Problem**: 
Gemini API returned 400 error: "Please use a valid role: user, model" because the system prompts were being skipped and roles like "assistant" were passed directly.

**Root Cause**:
1. Gemini API only accepts "user" and "model" roles in contents
2. System prompts were being skipped entirely instead of using Gemini's `systemInstruction` field
3. Without system prompts, the bot didn't know to redirect off-topic questions

**Solution**:
1. Map "assistant" role to "model" for Gemini
2. Extract system messages and pass them via `systemInstruction` field
3. This ensures the bot's personality and redirect instructions are properly passed to the model

**Changes Made:**

| File | Change |
|------|--------|
| `frontend/src/stores/llmProviderStore.ts` | Allow selecting current provider for configuration updates |
| `backend/app/schemas/llm.py` | Remove strict validation that required API key for cloud providers |
| `backend/app/services/llm/gemini_service.py` | Map assistant→model, use systemInstruction for system prompts |

**Commits**: 
- `5c35d7d8` - fix: allow selecting current provider for configuration updates
- `bb93e890` - fix: allow optional API key for provider updates
- `58291735` - fix: map LLM roles to Gemini-compatible roles
- `bf06d3b7` - fix: use systemInstruction for Gemini system prompts

**Result**: 
- Bot now properly redirects off-topic questions to shopping assistance
- System prompts with personality and business info are correctly passed to Gemini
- Users can update API keys and models for existing providers

#### 2026-02-20: Complete Shopify Integration Fix

**Problem**: 
Shopify integration was non-functional with multiple blocking issues preventing real product data from being displayed.

**Root Causes**:
1. SSL certificate errors on macOS - Python doesn't use system certificates
2. Malformed URLs - duplicate `.myshopify.com` in URL templates
3. Credentials not persisting - SQLAlchemy JSONB change detection
4. OAuth popup not closing - returned JSON instead of HTML with postMessage
5. Storefront token NOT NULL constraint - removed token creation but column required value
6. Products showing mock data - required Storefront token which custom apps can't create
7. Pin count not updating - optimistic updates missing count increment

**Solution**:
1. Created SSL utility with certifi for macOS compatibility
2. Fixed URL templates in all Shopify service files
3. Added `flag_modified()` for JSONB persistence
4. Return HTML with `postMessage` and `window.close()` from OAuth callback
5. Made `storefront_token_encrypted` nullable via migration
6. Added `list_products()` to Admin API client, use Admin API instead of Storefront
7. Added optimistic count updates to `pinProduct` and `unpinProduct` functions

**Changes Made:**

| File | Change |
|------|--------|
| `backend/app/core/http_client.py` | **NEW** - SSL utility with certifi for macOS |
| `backend/app/services/shopify_base.py` | Use SSL context from http_client |
| `backend/app/services/shopify_oauth.py` | Fix URL template, add flag_modified, update scopes |
| `backend/app/services/shopify_admin.py` | Fix URL template, add `list_products()` method |
| `backend/app/services/shopify_storefront.py` | Fix URL template |
| `backend/app/services/shopify/storefront_client.py` | Use SSL context |
| `backend/app/services/shopify/product_service.py` | Use Admin API instead of Storefront |
| `backend/app/models/shopify_integration.py` | Make `storefront_token_encrypted` nullable |
| `backend/alembic/versions/024_nullable_storefront_tkn.py` | **NEW** - Migration for nullable column |
| `backend/app/api/integrations.py` | Return HTML with postMessage for popup callback |
| `backend/app/middleware/auth.py` | Bypass auth for Shopify callback/authorize |
| `backend/app/middleware/csrf.py` | Bypass CSRF for Shopify credentials endpoint |
| `frontend/src/pages/Settings.tsx` | Button visibility, inline errors, updated instructions |
| `frontend/src/stores/integrationsStore.ts` | Throw errors for inline display |
| `frontend/src/stores/botConfigStore.ts` | Fix pin count optimistic updates |
| `docs/stories/story-5-9-version-visibility.md` | Document all Shopify fixes and setup guide |

**OAuth Scopes Required:**

| Scope | Purpose |
|-------|---------|
| `read_products` | View products and collections |
| `write_products` | Required for checkout integration |
| `read_inventory` | Check stock levels |
| `read_orders` | View orders and transactions |
| `read_fulfillments` | Check shipping/tracking status |
| `read_customers` | Look up customer info |
| `read_all_orders` | (Optional) Access orders older than 60 days |

**Commit**: `d2d2ca58` - fix: complete Shopify integration with Admin API

**Shopify Integration Setup Guide:**

1. **Create App in Shopify Partners Dashboard**
   - Go to https://partners.shopify.com
   - Click Apps → Create app → Create app manually
   - Enter app name (e.g., "ShopBot Integration")

2. **Configure App URLs**
   - App URL: `http://localhost:8000` (dev) or production URL
   - Redirect URL: `http://localhost:8000/api/integrations/shopify/callback`

3. **Configure API Scopes**
   - Go to Configuration → Admin API integration
   - Select: `read_products`, `write_products`, `read_inventory`, `read_orders`, `read_fulfillments`, `read_customers`

4. **Get Credentials**
   - Copy Client ID and Client secret from App credentials

5. **Configure in Shop App**
   - Go to Settings → Shopify Integration
   - Enter API Key (Client ID) and API Secret
   - Click Save Credentials
   - Enter shop domain (e.g., `your-store.myshopify.com`)
   - Click Connect to Shopify

6. **Authorize in Shopify**
   - Popup opens to Shopify authorization page
   - Click Install app to authorize
   - Popup closes automatically
   - Settings shows "Connected"

**Result**:
- Real Shopify products now display in Bot Config → Product Pins
- Pin/unpin updates count dynamically
- Full OAuth flow working end-to-end
- Products fetched via Admin REST API (not Storefront API which requires Sales Channel status)

#### 2026-02-21: Order Tracking & Cart System

**Problem**: 
Preview chat had no cart functionality or order tracking. Users couldn't add products to cart, and the bot couldn't answer "Where's my order?" questions.

**Solution**:
1. Implemented cart store with Zustand (persisted to localStorage)
2. Added "Add to Cart" buttons to product cards and detail modal
3. Created MiniCart sidebar with quantity controls and checkout
4. Implemented Shopify cart permalink checkout (opens in new tab)
5. Added webhook handlers for order tracking (orders/create, orders/fulfilled, fulfillments/update, refunds/create)
6. Added order context to bot system prompts
7. Created order lookup API for preview chat

**Changes Made:**

| File | Change |
|------|--------|
| `frontend/src/stores/cartStore.ts` | **NEW** - Cart state management with persistence |
| `frontend/src/services/orderApi.ts` | **NEW** - Order API service for tracking |
| `frontend/src/services/productApi.ts` | Added `variant_id`, `shop_domain`, `buildCheckoutUrl()`, `getShopDomain()` |
| `frontend/src/components/preview/ProductCard.tsx` | Added "Add to Cart" button, variant ID support |
| `frontend/src/components/preview/ProductDetailModal.tsx` | Added quantity selector and "Add to Cart" button |
| `frontend/src/components/preview/ProductGrid.tsx` | Pass variant ID to ProductCard |
| `frontend/src/components/preview/MiniCart.tsx` | **NEW** - Cart sidebar with quantity controls, checkout |
| `frontend/src/components/preview/PreviewChat.tsx` | Added cart icon with item count badge, pass merchantId to MiniCart |
| `frontend/src/components/preview/MessageBubble.tsx` | Improved product name extraction from bot responses |
| `backend/app/api/preview.py` | Added `/preview/orders/{order_number}`, `/preview/orders`, `/preview/shop-domain` endpoints |
| `backend/app/api/webhooks/shopify.py` | Added `handle_fulfillment_event()`, `handle_refund_created()` handlers |
| `backend/app/services/product_context_service.py` | Added `get_order_context()`, `get_order_context_prompt_section()` |
| `backend/app/services/personality/personality_prompts.py` | Added `order_context` parameter |
| `backend/app/services/personality/bot_response_service.py` | Fetch order context for system prompt |
| `backend/app/services/shopify/order_processor.py` | Fixed `shopify_order_key` type (str), improved tracking extraction, added Conversation import |
| `backend/app/services/shopify_admin.py` | Fixed `available` calculation (check `inventory_quantity > 0`) |
| `backend/app/middleware/auth.py` | Removed `/api/v1/preview/` from BYPASS_PATHS (was causing merchant_id=1 default) |
| `backend/app/middleware/csrf.py` | Added `/api/v1/webhooks/` to BYPASS_PATHS |

**Webhook Events Supported:**

| Event | Purpose |
|-------|---------|
| `orders/create` | New order placed, store in database |
| `orders/updated` | Order status changes |
| `orders/fulfilled` | Order shipped with tracking |
| `fulfillments/create` | New fulfillment created |
| `fulfillments/update` | Tracking info added/updated |
| `refunds/create` | Refund processed |

**Cart Permalink Format:**
```
https://{shop}.myshopify.com/cart/{variant_id}:{quantity},{variant_id}:{quantity}
```

**Order Tracking Flow:**
1. User places order on Shopify → `orders/create` webhook → Order stored in DB
2. Merchant fulfills order with tracking → `fulfillments/update` webhook → Tracking stored
3. User asks "Where's my order?" → Bot queries DB → Responds with status + tracking link

**Commits**: 
- Cart functionality and checkout
- Order tracking webhook handlers
- Fix preview auth (merchant_id default)

**Result**:
- Cart with add/remove/update quantity working
- Checkout redirects to Shopify in new tab
- Cart clears on checkout
- Bot can answer "Where's my order?" with status and tracking
- Webhooks from Shopify properly stored in database
- Preview chat now uses logged-in merchant's LLM config (not default merchant_id=1)

**Local Testing with ngrok:**
```bash
ngrok http 8000
# Use ngrok URL for Shopify webhooks:
# https://{ngrok-id}.ngrok-free.app/api/webhooks/shopify
```

**Shopify Webhook Setup:**
1. Go to Settings → Notifications → Webhooks
2. Create webhooks for: orders/create, orders/updated, orders/fulfilled, orders/cancelled, fulfillments/create, fulfillments/update, refunds/create
3. Format: JSON
4. URL: `https://{ngrok-url}/api/webhooks/shopify`