# Story 5.9: Widget Version Visibility

Status: done

## Story

As a merchant embedding the chat widget on my website,
I want to verify the widget version is exposed on `window.ShopBotWidget`,
so that I can programmatically check which version is loaded for debugging and support purposes.

## Acceptance Criteria

1. **Given** the widget bundle loads, **When** the loader script executes, **Then** `window.ShopBotWidget.version` is exposed as a string matching semantic versioning format (`X.Y.Z`)
2. **Given** the widget bundle loads, **When** the loader script executes, **Then** `window.ShopBotWidget.init()` is exposed as a function that initializes the widget
3. **Given** the widget bundle loads, **When** the loader script executes, **Then** `window.ShopBotWidget.unmount()` is exposed as a function that removes the widget from the DOM
4. **Given** the widget bundle loads, **When** the loader script executes, **Then** `window.ShopBotWidget.isMounted()` is exposed as a function that returns `true` if widget is mounted, `false` otherwise
5. **Given** the widget bundle fails to load, **When** the script fetch fails, **Then** `window.ShopBotWidget` remains `undefined` and the page does not crash

## Tasks / Subtasks

- [x] **Version Embedding** (AC: 1)
  - [x] Configure Vite to embed `__VITE_WIDGET_VERSION__` constant
  - [x] Expose version on `window.ShopBotWidget.version`
  - [x] Verify semver format (X.Y.Z)

- [x] **API Method Exposure** (AC: 2, 3, 4)
  - [x] Expose `init()` function for programmatic initialization
  - [x] Expose `unmount()` function for cleanup
  - [x] Expose `isMounted()` function for state checking
  - [x] Verify all methods are functions

- [x] **E2E Testing** (AC: 1-5)
  - [x] Create `frontend/tests/e2e/story-5-9-version-visibility.spec.ts`
  - [x] Test version exposure and format
  - [x] Test API method calls (init, unmount, isMounted)
  - [x] Test widget load failure handling

## Dev Notes

### Version Embedding Pattern

The widget version is embedded at build time using Vite's define feature:

```typescript
// vite.widget.config.ts
export default defineConfig({
  define: {
    __VITE_WIDGET_VERSION__: JSON.stringify(process.env.npm_package_version || '0.0.0'),
  },
  build: {
    lib: {
      name: 'ShopBotWidget',
      // ...
    },
  },
});
```

### API Surface

```typescript
interface ShopBotWidget {
  version: string;           // Semver format: "X.Y.Z"
  init: () => void;          // Initialize widget
  unmount: () => void;       // Remove widget from DOM
  isMounted: () => boolean;  // Check if widget is mounted
}
```

### Loader Pattern

```typescript
// src/widget/loader.ts
declare const __VITE_WIDGET_VERSION__: string;

// Expose version and API on window.ShopBotWidget
if (typeof window !== 'undefined') {
  window.ShopBotWidget = {
    version: __VITE_WIDGET_VERSION__,
    init: initWidget,
    unmount: unmountWidget,
    isMounted: isWidgetMounted,
  };
}
```

### Testing Standards

- **Version Test**: Verify format matches `/^\d+\.\d+\.\d+$/`
- **API Test**: Call methods and verify behavior (not just existence)
- **Failure Test**: Block widget script and verify graceful degradation
- **No Hard Waits**: Use `expect.poll()` for polling assertions

### References

- [Vite Define Feature]: https://vitejs.dev/config/shared-options.html#define
- [Semantic Versioning]: https://semver.org/

## Dev Agent Record

### Agent Model Used

Claude 3.5 Sonnet

### Completion Notes List

**Initial Implementation (2026-02-18):**
- Version embedded via `__VITE_WIDGET_VERSION__` constant
- API methods exposed on `window.ShopBotWidget`
- E2E tests created for version and API verification

**Test Quality Review (2026-02-20):**
- Initial score: 96/100 (reviewed)
- Critical challenge applied: 88/100 (coverage gaps found)
- P0 fixes implemented and verified
- Final score: ~95/100 (all tests passing)

### Change Log

| Date | Change | Author |
|------|--------|--------|
| 2026-02-18 | Story file created | AI Agent |
| 2026-02-18 | Initial E2E tests implemented | AI Agent |
| 2026-02-20 | Test quality review completed | TEA Agent |
| 2026-02-20 | P0 fixes: API methods called, failure test added | TEA Agent |

### File List

**Test Files:**
- `frontend/tests/e2e/story-5-9-version-visibility.spec.ts` (82 lines, 4 tests)

**Production Files:**
- `frontend/vite.widget.config.ts` - Widget build configuration with version embedding
- `frontend/src/widget/loader.ts` - Widget loader with API exposure

### Test Quality Review (2026-02-20)

**Review Date:** 2026-02-20
**Reviewer:** TEA Agent (Critical Perspective Challenge)
**Outcome:** Approve

**Initial Quality Score:** 96/100 (Grade A)
**After Critical Review:** 88/100 (Grade B+)
**After P0 Fixes:** ~95/100 (Grade A)

**Critical Issues Found:**

| Severity | Issue | Location | Status |
|----------|-------|----------|--------|
| P0 (Blocking) | API methods never called (only existence checked) | :28-36 | ✅ Fixed 2026-02-20 |
| P0 (Blocking) | No widget load failure test | N/A | ✅ Fixed 2026-02-20 |
| P1 | Magic timeout values (10000) | :9,25 | ✅ Fixed 2026-02-20 |
| P2 | Missing BDD-style comments | All tests | 🟡 Follow-up |

**Critical Review Findings:**

1. **API Methods Test Was Shallow (P0)**
   > "The API methods test only verifies that methods **exist** - it never **calls** them! This is a placebo test that proves nothing about actual functionality." — Critical Perspective

2. **No Failure Handling (P0)**
   > "No test verifies what happens when the widget fails to load. Users will see broken UI, but tests don't catch this scenario." — Critical Perspective

3. **Score Inflation**
   > "Coverage was scored 80/100, but this is generous. Zero negative tests exist. Score should be 65/100." — Critical Perspective

**Required Fixes Applied:**

```typescript
// ✅ P0 Fix: Actually call API methods
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

// ✅ P0 Fix: Test widget load failure
test('[P0] should handle widget script load failure', async ({ page }) => {
  await page.route('**/widget*.{js,ts}', route => route.abort('failed'));
  await page.goto('/widget-bundle-test.html');

  await expect.poll(
    async () => await page.evaluate(() => typeof (window as any).ShopBotWidget !== 'undefined'),
    { timeout: WIDGET_LOAD_TIMEOUT }
  ).toBe(false);
});
```

**Review Report:** `_bmad-output/test-reviews/test-review-story-5-9.md`

### Action Items

| # | Action | Priority | Status | Owner |
|---|--------|----------|--------|-------|
| 1 | Call API methods in tests (not just check existence) | P0 | ✅ Done | TEA Agent |
| 2 | Add widget load failure test | P0 | ✅ Done | TEA Agent |
| 3 | Extract magic timeout constants | P1 | ✅ Done | TEA Agent |
| 4 | Fix route to `/widget-bundle-test.html` | P1 | ✅ Done | TEA Agent |
| 5 | Add BDD-style comments | P2 | Backlog | Dev |

### Test Results

```
Running 4 tests using 4 workers

  ✓ [P1] should expose version on window.ShopBotWidget after load (1.0s)
  ✓ [P0] should call init, unmount, and isMounted methods correctly (1.0s)
  ✓ [P0] should handle widget script load failure (872ms)
  ✓ [P2] should expose init, unmount, and isMounted methods (1.1s)

  4 passed (4.9s)
```

### Change Log

| Date | Change | Author |
|------|--------|--------|
| 2026-02-18 | Story file created | AI Agent |
| 2026-02-18 | Initial E2E tests implemented | AI Agent |
| 2026-02-20 | Test quality review completed | TEA Agent |
| 2026-02-20 | P0 fixes: API methods called, failure test, constants | TEA Agent |
| 2026-02-20 | Widget bundle updated in public/dist | TEA Agent |
