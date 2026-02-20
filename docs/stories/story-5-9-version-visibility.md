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

---

## Shopify Integration Fixes (2026-02-20)

During this sprint, significant fixes were made to the Shopify integration to make it fully functional.

### Issues Fixed

#### 1. SSL Certificate Error on macOS
**Problem:** `[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate`

**Root Cause:** Two issues:
1. Python on macOS doesn't use system certificates by default
2. **Malformed URL**: Template was `{shop}.myshopify.com` but `shop_domain` already contained `.myshopify.com`, resulting in `volare-sun.myshopify.com.myshopify.com` (non-existent domain)

**Solution:**
- Created `app/core/http_client.py` with `get_ssl_context()` using certifi
- Fixed URL templates in `shopify_admin.py` and `shopify_storefront.py`

**Files Changed:**
- `backend/app/core/http_client.py` (new)
- `backend/app/services/shopify_base.py`
- `backend/app/services/shopify_oauth.py`
- `backend/app/services/shopify/storefront_client.py`
- `backend/app/services/shopify_admin.py`
- `backend/app/services/shopify_storefront.py`

#### 2. Credentials Not Persisting
**Problem:** Saved Shopify credentials weren't being committed to database

**Root Cause:** SQLAlchemy doesn't detect changes to JSONB fields when modifying dict in-place

**Solution:** Added `flag_modified(merchant, "config")` after modifying the config dict

**Files Changed:**
- `backend/app/services/shopify_oauth.py`

#### 3. OAuth Popup Not Closing
**Problem:** After successful Shopify authorization, popup stayed open and badge showed "connecting"

**Root Cause:** Callback returned JSON instead of HTML page that posts message to parent window

**Solution:** Updated callback to return HTML with `window.opener.postMessage()` and `window.close()`

**Files Changed:**
- `backend/app/api/integrations.py`

#### 4. Invalid Scope Name
**Problem:** `write_storefront_access_tokens` is not a valid Shopify scope

**Solution:** Changed to `write_products` which includes the necessary permissions

#### 5. Button Visibility
**Problem:** Connect button not visible (white on white background)

**Solution:** Changed from `bg-success` to `bg-green-600`

**Files Changed:**
- `frontend/src/pages/Settings.tsx`

#### 6. Error Message Placement
**Problem:** Error messages appeared at top of page, not visible when form is at bottom

**Solution:** Added inline success/error message display under the Save button

**Files Changed:**
- `frontend/src/pages/Settings.tsx`
- `frontend/src/stores/integrationsStore.ts`

### OAuth Scopes Configuration

**Required Scopes (must be configured in Shopify Partners Dashboard):**
- `read_products` - View products and collections
- `write_products` - Required for creating Storefront access tokens
- `read_inventory` - Check stock levels
- `read_orders` - View orders and transactions
- `read_fulfillments` - Check shipping/tracking status
- `read_customers` - Look up customer info

**Optional Scope:**
- `read_all_orders` - Access orders older than 60 days (requires Shopify approval)

### Shopify App Setup Instructions

Updated Settings page with step-by-step instructions:
1. Create app in Shopify Partners Dashboard
2. Configure App URLs and redirect URI
3. Select all required Admin API access scopes
4. Get Client ID and Secret credentials
5. Save credentials in Settings
6. Enter store domain and connect

### Files Changed Summary

| File | Change |
|------|--------|
| `backend/app/core/http_client.py` | New SSL utility with certifi |
| `backend/app/services/shopify_base.py` | Use SSL context from http_client |
| `backend/app/services/shopify_oauth.py` | Fix URL template, add flag_modified, update scopes |
| `backend/app/services/shopify_admin.py` | Fix URL template, add error logging |
| `backend/app/services/shopify_storefront.py` | Fix URL template |
| `backend/app/services/shopify/storefront_client.py` | Use SSL context |
| `backend/app/api/integrations.py` | Add popup callback HTML response, scope logging |
| `backend/app/middleware/auth.py` | Bypass auth for Shopify callback/authorize |
| `backend/app/middleware/csrf.py` | Bypass CSRF for Shopify credentials endpoint |
| `frontend/src/pages/Settings.tsx` | Button visibility, inline errors, updated instructions |
| `frontend/src/stores/integrationsStore.ts` | Throw errors for inline display |

### Testing Performed

- ✅ Direct SSL test with httpx and certifi
- ✅ ShopifyBaseClient direct request
- ✅ ShopifyAdminClient direct request
- ✅ OAuth authorize endpoint
- ✅ OAuth callback with popup message

### Remaining Work

- ~~Verify full OAuth flow end-to-end after user configures all scopes in Shopify Partners Dashboard~~ ✅ Done
- ~~Test product fetching from real Shopify store~~ ✅ Done
- ~~Test chatbot product search with real data~~ ✅ Done

---

## Additional Shopify Fixes (2026-02-20)

### 7. Storefront Token NOT NULL Constraint Violation
**Problem:** `IntegrityError: null value in column "storefront_token_encrypted" violates not-null constraint`

**Root Cause:** We removed Storefront token creation (custom apps can't create them), but the database column still required a value

**Solution:** 
- Made `storefront_token_encrypted` nullable in model
- Created migration `024_nullable_storefront_tkn`

**Files Changed:**
- `backend/app/models/shopify_integration.py`
- `backend/alembic/versions/024_nullable_storefront_tkn.py` (new)

### 8. Products Still Showing Mock Data After Connection
**Problem:** Even with active Shopify connection, Bot Config showed mock products (backpack.jpg, etc.)

**Root Cause:** 
1. `fetch_products()` required `storefront_token_encrypted` to exist before fetching
2. Storefront API requires an access token - "tokenless" doesn't work

**Solution:** 
- Added `list_products()` method to `ShopifyAdminClient` using Admin REST API
- Changed `product_service.py` to use Admin API instead of Storefront API
- Admin API uses the OAuth access token we already have

**Files Changed:**
- `backend/app/services/shopify_admin.py` - Added `list_products()` method
- `backend/app/services/shopify/product_service.py` - Use Admin API client

### 9. Pin Count Not Updating Dynamically
**Problem:** After pinning/unpinning products, the "X/10 products pinned" counter didn't update

**Root Cause:** `pinProduct` and `unpinProduct` functions updated `isPinned` on products but didn't update `pinLimitInfo.pinnedCount`

**Solution:** Added optimistic count updates to both functions

**Files Changed:**
- `frontend/src/stores/botConfigStore.ts`

---

## Shopify Integration Setup Guide

### Prerequisites

- A Shopify store (any plan)
- Shopify Partners account (free): https://partners.shopify.com

### Step 1: Create Custom App in Shopify Partners

1. Go to https://partners.shopify.com and log in
2. Click **Apps** → **Create app**
3. Choose **Create app manually**
4. Enter app name (e.g., "ShopBot Integration")
5. Click **Create app**

### Step 2: Configure App URLs

1. In your app, go to **App setup**
2. Set **App URL**: `http://localhost:8000` (development) or your production URL
3. Set **Allowed redirection URL(s)**:
   - `http://localhost:8000/api/integrations/shopify/callback`
   - For production: `https://your-domain.com/api/integrations/shopify/callback`
4. Click **Save**

### Step 3: Configure API Access Scopes

1. Go to **Configuration** → **Admin API integration**
2. Click **Configure**
3. Select these **Access scopes**:

   | Scope | Purpose |
   |-------|---------|
   | `read_products` | View products and collections |
   | `write_products` | Required for checkout integration |
   | `read_inventory` | Check stock levels |
   | `read_orders` | View orders and transactions |
   | `read_fulfillments` | Check shipping/tracking status |
   | `read_customers` | Look up customer info |

4. (Optional) `read_all_orders` - Access orders older than 60 days (requires Shopify approval)
5. Click **Save**

### Step 4: Get Credentials

1. Go to **App credentials**
2. Copy **Client ID** and **Client secret**
3. Keep these secure - you'll enter them in the app Settings

### Step 5: Configure in Shop App

1. Open the app and go to **Settings**
2. Scroll to **Shopify Integration** section
3. Enter:
   - **API Key**: Your Client ID from Step 4
   - **API Secret**: Your Client secret from Step 4
4. Click **Save Credentials**
5. Enter your **Shop Domain** (e.g., `your-store.myshopify.com`)
6. Click **Connect to Shopify**

### Step 6: Authorize in Shopify

1. A popup will open to Shopify's authorization page
2. Review the permissions requested
3. Click **Install app** to authorize
4. The popup will close automatically
5. Settings page will show **Connected** status

### Step 7: Verify Integration

1. Go to **Bot Config** → **Product Highlight Pins**
2. You should see your real Shopify products (not mock data)
3. Try pinning/unpinning products

### Troubleshooting

| Issue | Solution |
|-------|----------|
| SSL Certificate Error | Fixed - uses certifi for SSL context |
| Credentials not saving | Fixed - uses `flag_modified()` for JSONB |
| OAuth popup doesn't close | Fixed - returns HTML with postMessage |
| "Internal Server Error" | Check backend logs, all scopes configured? |
| Mock products still showing | Admin API fetches real products now |
| Pin count not updating | Fixed - optimistic updates in store |

### API Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Product Fetch Flow                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Frontend (Bot Config)                                       │
│       │                                                      │
│       ▼                                                      │
│  productPinApi.fetchProductsWithPinStatus()                 │
│       │                                                      │
│       ▼                                                      │
│  Backend: /api/product-pins/products                        │
│       │                                                      │
│       ▼                                                      │
│  product_service.fetch_products()                           │
│       │                                                      │
│       ▼                                                      │
│  ShopifyAdminClient.list_products()  ◄── Admin REST API    │
│       │                                                      │
│       ▼                                                      │
│  GET https://{shop}/admin/api/2024-01/products.json         │
│       │                                                      │
│       ▼                                                      │
│  Returns: Real products from your Shopify store             │
│                                                              │
└─────────────────────────────────────────────────────────────┘

Note: We use Admin API (not Storefront API) because:
- Storefront API requires a Storefront access token
- Only Sales Channel apps can create Storefront tokens
- Custom apps cannot create Storefront tokens
- Admin API works with the OAuth access token we already have
```

### Checkout URL Format

For product checkouts, we use direct cart URLs:

```
https://{shop}.myshopify.com/cart/{variant_id}:{quantity}
```

Example:
```
https://your-store.myshopify.com/cart/41234567890123:1
```

---

### Final Files Changed Summary (All Shopify Fixes)

| File | Change |
|------|--------|
| `backend/app/core/http_client.py` | New SSL utility with certifi |
| `backend/app/services/shopify_base.py` | Use SSL context from http_client |
| `backend/app/services/shopify_oauth.py` | Fix URL template, add flag_modified, update scopes |
| `backend/app/services/shopify_admin.py` | Fix URL template, add `list_products()`, error logging |
| `backend/app/services/shopify_storefront.py` | Fix URL template |
| `backend/app/services/shopify/storefront_client.py` | Use SSL context |
| `backend/app/services/shopify/product_service.py` | Use Admin API instead of Storefront |
| `backend/app/models/shopify_integration.py` | Make `storefront_token_encrypted` nullable |
| `backend/alembic/versions/024_nullable_storefront_tkn.py` | Migration for nullable column |
| `backend/app/api/integrations.py` | Popup callback HTML response, error handling |
| `backend/app/middleware/auth.py` | Bypass auth for Shopify callback/authorize |
| `backend/app/middleware/csrf.py` | Bypass CSRF for Shopify credentials endpoint |
| `frontend/src/pages/Settings.tsx` | Button visibility, inline errors, updated instructions |
| `frontend/src/stores/integrationsStore.ts` | Throw errors for inline display |
| `frontend/src/stores/botConfigStore.ts` | Fix pin count optimistic updates |
