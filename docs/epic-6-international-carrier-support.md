# Epic 6: International Carrier Support

Status: ready-for-dev

## Overview

Add comprehensive international shipping carrier support to enable accurate tracking link generation for orders fulfilled with carriers worldwide (290+ carriers across US, UK, PH, SEA, EU, etc.), with merchant-configurable custom carriers for local providers not in Shopify's list.

## Epic Goal

Enable merchants to:
1. Automatically detect shipping carriers from Shopify webhooks
2. Generate accurate tracking links for international carriers
3. Configure custom carriers for local providers (e.g., LBC, J&T in Philippines)

## Requirements Inventory

### Functional Requirements

| ID | Requirement |
|----|-------------|
| FR-6.1 | System must extract and store `tracking_company` from Shopify webhooks |
| FR-6.2 | System must detect carrier from tracking number pattern when carrier name unavailable |
| FR-6.3 | System must support 290+ international carriers with URL templates |
| FR-6.4 | Merchants must be able to configure custom carriers with URL templates |
| FR-6.5 | Custom carriers must support optional regex patterns for auto-detection |
| FR-6.6 | Tracking URL resolution must follow priority: webhook URL > custom config > Shopify carrier > pattern > fallback |

### Non-Functional Requirements

| ID | Requirement |
|----|-------------|
| NFR-6.1 | Carrier detection must complete in <50ms |
| NFR-6.2 | Pattern matching must be case-insensitive |
| NFR-6.3 | All carrier patterns must be unit tested |

### Supported Regions

| Region | Carriers |
|--------|----------|
| United States | 27 carriers (UPS, FedEx, USPS, OnTrac, etc.) |
| United Kingdom | 24 carriers (Royal Mail, DPD, Evri, Yodel, etc.) |
| Philippines | 15 carriers (LBC, J&T, Ninja Van, 2GO, etc.) |
| Southeast Asia | 15 carriers (Kerry, Thailand Post, etc.) |
| Europe | 45 carriers (DHL, GLS, PostNL, etc.) |
| Middle East | 15 carriers (Aramex, SMSA, etc.) |
| Africa | 20 carriers |
| Latin America | 35 carriers |
| Oceania | 16 carriers |
| South Asia | 24 carriers |
| East Asia | 22 carriers |
| China | 18 carriers |
| Global | 15 carriers |
| **Total** | **~290 carriers** |

---

## Story List

| Story | Title | Priority | Est. Time |
|-------|-------|----------|-----------|
| 6.1 | Backend Core Infrastructure | P0 | 1.5 hours |
| 6.2 | Carrier Detection Service | P0 | 2 hours |
| 6.3 | Carrier Configuration API | P0 | 1.5 hours |
| 6.4 | Frontend Shipping Carriers Settings Page | P1 | 3 hours |
| 6.5 | Testing & Quality Assurance | P1 | 2 hours |

---

## Story 6.1: Backend Core Infrastructure

### User Story

As a **merchant with international customers**,
I want **my orders to automatically store carrier information from Shopify**,
So that **my customers receive accurate tracking links regardless of which carrier I use**.

### Acceptance Criteria

**AC1:** Given a Shopify fulfillment webhook is received, when the webhook contains `tracking_company` and `tracking_number`, then both values are stored in the order record and the tracking URL is generated using the carrier's URL template.

**AC2:** Given an order exists without `tracking_company`, when a fulfillment update webhook arrives, then the `tracking_company` field is populated.

### Tasks

- [ ] Add `tracking_company` field to Order model (AC: 1)
  - [ ] Update `backend/app/models/order.py`
  - [ ] Add field: `tracking_company: Mapped[str | None]`
- [ ] Create database migration (AC: 1)
  - [ ] Create `alembic/versions/XXX_add_tracking_company_and_carrier_configs.py`
- [ ] Create `CarrierConfig` model for custom carriers (AC: 1)
  - [ ] Create `backend/app/models/carrier_config.py`
- [ ] Update Shopify webhook handler (AC: 1, 2)
  - [ ] Modify `backend/app/api/webhooks/shopify.py` - `handle_fulfillment_event()`
  - [ ] Extract `tracking_company` from payload
- [ ] Update order processor (AC: 1, 2)
  - [ ] Modify `backend/app/services/shopify/order_processor.py`
  - [ ] Store `tracking_company` in order data

### Dev Notes

- **CSRF**: No new API endpoints in this story
- **Python Version**: Use `datetime.timezone.utc` (NOT `datetime.UTC`)
- **External Integration**: Shopify webhook - already implemented

### Files to Create

```
backend/app/models/carrier_config.py
backend/app/schemas/carrier.py
backend/alembic/versions/XXX_add_tracking_company_and_carrier_configs.py
```

### Files to Modify

```
backend/app/models/order.py
backend/app/api/webhooks/shopify.py
backend/app/services/shopify/order_processor.py
```

---

## Story 6.2: Carrier Detection Service

### User Story

As a **customer waiting for my order**,
I want **to click a tracking link that takes me to the correct carrier website**,
So that **I can easily track my package without manually looking up the carrier**.

### Acceptance Criteria

**AC1:** Given an order with `tracking_company` "LBC Express", when the tracking URL is generated, then the URL uses the LBC Express tracking template.

**AC2:** Given an order without `tracking_company` but with tracking number "1Z999AA10123456784", when the tracking URL is generated, then the carrier is detected as "UPS" via pattern matching and the URL uses the UPS tracking template.

**AC3:** Given a merchant has configured a custom carrier "LocalPH", when an order has tracking number matching the custom pattern, then the custom carrier's URL template is used.

**AC4:** Given a tracking number doesn't match any known carrier, when the tracking URL is generated, then no URL is returned (fallback to just showing tracking number).

### Tasks

- [ ] Create carrier patterns file (AC: 2)
  - [ ] Create `backend/app/services/carrier/carrier_patterns.py`
  - [ ] Add 290+ carrier patterns with URL templates
- [ ] Create Shopify carrier mapping (AC: 1)
  - [ ] Create `backend/app/services/carrier/shopify_carriers.py`
  - [ ] Map Shopify carrier names to URL templates
- [ ] Create carrier detection service (AC: 1, 2, 3, 4)
  - [ ] Create `backend/app/services/carrier/carrier_service.py`
  - [ ] Implement priority resolution: webhook URL > custom config > Shopify carrier > pattern > fallback
- [ ] Update tracking formatter (AC: 1, 2, 3, 4)
  - [ ] Modify `backend/app/services/shipping_notification/tracking_formatter.py`
  - [ ] Integrate with carrier service
- [ ] Update shipping notification service (AC: 1, 2, 3, 4)
  - [ ] Modify `backend/app/services/shipping_notification/service.py`
  - [ ] Pass `tracking_company` to formatter

### Dev Notes

- **Pattern Priority**: More specific patterns should be checked first
- **Region Patterns**: PH carriers like LBC may conflict with generic patterns - prioritize by specificity

### Files to Create

```
backend/app/services/carrier/__init__.py
backend/app/services/carrier/carrier_patterns.py
backend/app/services/carrier/shopify_carriers.py
backend/app/services/carrier/carrier_service.py
```

### Files to Modify

```
backend/app/services/shipping_notification/tracking_formatter.py
backend/app/services/shipping_notification/service.py
```

---

## Story 6.3: Carrier Configuration API

### User Story

As a **merchant using a local carrier not in Shopify's list**,
I want **to configure custom carrier settings with my own tracking URL template**,
So that **my customers still get clickable tracking links**.

### Acceptance Criteria

**AC1:** Given an authenticated merchant, when they create a custom carrier config via API, then the carrier is stored with name, URL template, and optional pattern.

**AC2:** Given a merchant has custom carrier configs, when they request the carrier list, then all their custom carriers are returned.

**AC3:** Given a tracking number, when the detect endpoint is called, then the detected carrier and URL are returned.

**AC4:** Given a custom carrier exists, when it is deleted, then it is removed from the merchant's configs.

### Tasks

- [ ] Create carrier API endpoints (AC: 1, 2, 4)
  - [ ] Create `backend/app/api/carriers.py`
  - [ ] Implement CRUD: GET, POST, PUT, DELETE
- [ ] Add carrier detection endpoint (AC: 3)
  - [ ] Add `POST /api/carriers/detect` endpoint
- [ ] Add supported carriers endpoint (AC: 3)
  - [ ] Add `GET /api/carriers/supported` endpoint
  - [ ] Add `GET /api/carriers/shopify` endpoint
- [ ] Add CSRF bypass for new endpoints (AC: 1, 2, 3, 4)
  - [ ] Update `backend/app/middleware/auth.py`
- [ ] Update mock provider for testing (AC: 1, 2, 3, 4)
  - [ ] Modify `backend/app/services/ecommerce/mock_provider.py`
  - [ ] Support custom carriers in mock

### Dev Notes

- **CSRF**: MUST add new routes to CSRF bypass in `auth.py`
- **Authentication**: All endpoints require merchant authentication

### API Endpoints

```
GET    /api/carriers/supported              # List all supported carriers
GET    /api/carriers/shopify                # List Shopify-supported carriers
GET    /api/merchants/{id}/carriers         # List merchant's custom carriers
POST   /api/merchants/{id}/carriers         # Add custom carrier
GET    /api/merchants/{id}/carriers/{cid}   # Get custom carrier
PUT    /api/merchants/{id}/carriers/{cid}   # Update custom carrier
DELETE /api/merchants/{id}/carriers/{cid}   # Delete custom carrier
POST   /api/carriers/detect                 # Detect carrier from tracking number
```

### Files to Create

```
backend/app/api/carriers.py
backend/tests/api/test_carriers.py
```

### Files to Modify

```
backend/app/middleware/auth.py
backend/app/services/ecommerce/mock_provider.py
backend/app/schemas/carrier.py (complete schemas)
```

---

## Story 6.4: Frontend Shipping Carriers Settings Page

### User Story

As a **merchant administrator**,
I want **a settings page to manage my custom shipping carriers**,
So that **I can easily add, edit, and remove carrier configurations without touching code**.

### Acceptance Criteria

**AC1:** Given a merchant navigates to Settings > Shipping, when the page loads, then their custom carriers are displayed in a list.

**AC2:** Given the shipping settings page, when "Add Carrier" is clicked, then a modal appears with form fields for carrier name, URL template, and pattern.

**AC3:** Given a filled carrier form, when the form is submitted, then the carrier is created via API and the list refreshes to show the new carrier.

**AC4:** Given an existing custom carrier, when "Edit" is clicked, then the modal opens pre-filled with carrier data.

**AC5:** Given an existing custom carrier, when "Delete" is clicked and confirmed, then the carrier is removed from the list.

### Tasks

- [ ] Create shipping carriers store (AC: 1, 3, 4, 5)
  - [ ] Create `frontend/src/stores/shippingCarriersStore.ts`
- [ ] Create API service (AC: 1, 3, 4, 5)
  - [ ] Create `frontend/src/services/shippingCarriers.ts`
- [ ] Create shipping carriers page (AC: 1)
  - [ ] Create `frontend/src/pages/ShippingCarriers.tsx`
  - [ ] Display custom carriers list
  - [ ] Show supported carriers reference
- [ ] Create carrier card component (AC: 1)
  - [ ] Create `frontend/src/components/shipping/CarrierCard.tsx`
- [ ] Create add/edit modal (AC: 2, 3, 4)
  - [ ] Create `frontend/src/components/shipping/AddCarrierModal.tsx`
  - [ ] Form validation with Zod
- [ ] Create supported carriers list component (AC: 1)
  - [ ] Create `frontend/src/components/shipping/SupportedCarriersList.tsx`
- [ ] Add to Settings tabs (AC: 1)
  - [ ] Modify `frontend/src/pages/Settings.tsx`
  - [ ] Add "Shipping" tab
- [ ] Add route (AC: 1)
  - [ ] Modify `frontend/src/components/App.tsx`

### Dev Notes

- **UI Framework**: React 18 + TypeScript + Tailwind CSS
- **State**: Zustand for local state
- **Data Fetching**: TanStack Query
- **Validation**: Zod schemas

### Files to Create

```
frontend/src/pages/ShippingCarriers.tsx
frontend/src/stores/shippingCarriersStore.ts
frontend/src/services/shippingCarriers.ts
frontend/src/components/shipping/CarrierCard.tsx
frontend/src/components/shipping/AddCarrierModal.tsx
frontend/src/components/shipping/SupportedCarriersList.tsx
```

### Files to Modify

```
frontend/src/pages/Settings.tsx
frontend/src/components/App.tsx
```

---

## Story 6.5: Testing & Quality Assurance

### User Story

As a **developer**,
I want **comprehensive tests for the carrier detection system**,
So that **I can be confident the feature feature works correctly for all supported carriers**.

### Acceptance Criteria

**AC1:** Given a tracking number for any of the 290+ carriers, when the carrier detection is tested, then the correct carrier is identified.

**AC2:** Given a custom carrier configuration, when CRUD operations are tested, then all operations work correctly.

**AC3:** Given the shipping notification flow, when integration tests run, then tracking URLs are correctly generated.

### Tasks

- [ ] Unit tests for carrier patterns (AC: 1)
  - [ ] Create `backend/tests/services/carrier/test_carrier_patterns.py`
  - [ ] Test all 290+ carrier patterns
- [ ] Unit tests for carrier service (AC: 1)
  - [ ] Create `backend/tests/services/carrier/test_carrier_service.py`
  - [ ] Test priority resolution
- [ ] Unit tests for carrier API (AC: 2)
  - [ ] Create `backend/tests/api/test_carriers.py`
  - [ ] Test CRUD endpoints
- [ ] Integration tests for webhook flow (AC: 3)
  - [ ] Update `backend/tests/api/test_story_4_2_shopify_webhook.py`
  - [ ] Test `tracking_company` extraction
- [ ] Frontend component tests (AC: 2)
  - [ ] Create `frontend/src/components/shipping/__tests__/`

### Files to Create

```
backend/tests/services/carrier/__init__.py
backend/tests/services/carrier/test_carrier_patterns.py
backend/tests/services/carrier/test_carrier_service.py
backend/tests/api/test_carriers.py
frontend/src/components/shipping/__tests__/CarrierCard.test.tsx
frontend/src/components/shipping/__tests__/AddCarrierModal.test.tsx
```

---

## Implementation Order

| Phase | Story | Dependencies | Est. Time |
|-------|-------|--------------|-----------|
| 1 | 6.1 Backend Core | None | 1.5 hours |
| 2 | 6.2 Carrier Service | 6.1 | 2 hours |
| 3 | 6.3 API Endpoints | 6.1, 6.2 | 1.5 hours |
| 4 | 6.4 Frontend UI | 6.3 | 3 hours |
| 5 | 6.5 Testing | 6.1-6.4 | 2 hours |
| **Total** | | | **10 hours** |

---

## Architecture Reference

### Carrier Detection Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           CARRIER DETECTION FLOW                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Shopify Webhook / Mock Order                                                │
│       │                                                                      │
│       ▼                                                                      │
│  ┌─────────────────────────────────────────┐                                │
│  │ Extract: tracking_company,              │                                │
│  │          tracking_number,               │                                │
│  │          tracking_url                   │                                │
│  └─────────────────────────────────────────┘                                │
│       │                                                                      │
│       ▼                                                                      │
│  ┌─────────────────────────────────────────┐                                │
│  │ PRIORITY RESOLUTION:                    │                                │
│  │                                         │                                │
│  │ 1. tracking_url from webhook (if set)   │◄── Shopify/merchant provided  │
│  │ 2. Merchant's custom carrier config     │◄── Database lookup            │
│  │ 3. tracking_company → Shopify carrier   │◄── Built-in mapping           │
│  │ 4. Pattern detection (290+ carriers)    │◄── Regex matching             │
│  │ 5. Fallback: just tracking number       │◄── No link, just text         │
│  └─────────────────────────────────────────┘                                │
│       │                                                                      │
│       ▼                                                                      │
│  ┌─────────────────────────────────────────┐                                │
│  │ Output: Tracking link for customer      │                                │
│  │         notification message            │                                │
│  └─────────────────────────────────────────┘                                │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Database Schema

```sql
-- Add to orders table
ALTER TABLE orders ADD COLUMN tracking_company VARCHAR(100);

-- New table for custom carriers
CREATE TABLE carrier_configs (
    id SERIAL PRIMARY KEY,
    merchant_id INTEGER NOT NULL REFERENCES merchants(id) ON DELETE CASCADE,
    carrier_name VARCHAR(100) NOT NULL,
    tracking_url_template VARCHAR(500) NOT NULL,
    tracking_number_pattern VARCHAR(200),
    is_active BOOLEAN DEFAULT true,
    priority INTEGER DEFAULT 50,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX ix_carrier_configs_merchant ON carrier_configs(merchant_id);
CREATE INDEX ix_carrier_configs_merchant_active ON carrier_configs(merchant_id, is_active);
```
