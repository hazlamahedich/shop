# Story 6-4: Data Tier Separation - Test Suite Fix

## Summary
Fixed all 10 integration tests in `backend/tests/integration/test_data_tier_api.py` from 5 failing to 10 passing.

## Issues Fixed

### 1. Data Export Tier Filtering (2 tests)
- **Problem**: Export service counted ALL conversations, not filtering by data tier
- **Fix**: Updated `_count_conversations()` to filter by `DataTier.VOLUNTARY` and `DataTier.OPERATIONAL`
- **File**: `backend/app/services/export/merchant_data_export_service.py:525-541`

### 2. Analytics Router Prefix Duplication (3 tests)
- **Problem**: Router had prefix `/api/v1/analytics`, then registered with prefix `/api/v1`, creating `/api/v1/api/v1/analytics`
- **Fix**: Changed router prefix from `/api/v1/analytics` to `/analytics`
- **File**: `backend/app/api/analytics.py:23`

### 3. Missing Order Subtotal Field (2 tests)
- **Problem**: Tests created orders without required `subtotal` field, causing NOT NULL violation
- **Fix**: Added `subtotal=Decimal("...")` to order creation in tests
- **Files**: `backend/tests/integration/test_data_tier_api.py:192, 281`

### 4. Missing Orders Section in Export (1 test)
- **Problem**: Data export didn't include orders, test expected "ORD-EXPORT-001" in CSV
- **Fix**: 
  - Added `Order` model import
  - Created `_count_orders()` method with tier filtering
  - Created `_generate_orders_section()` method
  - Updated metadata to include `Total Orders` count
  - Called orders section in export flow
- **File**: `backend/app/services/export/merchant_data_export_service.py`

### 5. Missing Decimal Import (1 test)
- **Problem**: Tests used `Decimal` type but didn't import it
- **Fix**: Added `from decimal import Decimal` to test imports
- **File**: `backend/tests/integration/test_data_tier_api.py:10`

## Test Results
```
tests/integration/test_data_tier_api.py::TestConsentOptOutTierChange::test_consent_opt_out_updates_conversation_tier PASSED
tests/integration/test_data_tier_api.py::TestConsentOptOutTierChange::test_consent_opt_out_preserves_operational_data PASSED
tests/integration/test_data_tier_api.py::TestDataExportTierSeparation::test_export_excludes_anonymized_tier PASSED
tests/integration/test_data_tier_api.py::TestDataExportTierSeparation::test_export_includes_operational_tier PASSED
tests/integration/test_data_tier_api.py::TestAnalyticsSummaryAnonymized::test_analytics_summary_strips_pii PASSED
tests/integration/test_data_tier_api.py::TestAnalyticsSummaryAnonymized::test_analytics_summary_includes_tier_distribution PASSED
tests/integration/test_data_tier_api.py::TestRetentionJobVoluntaryOnly::test_retention_deletes_expired_voluntary_only PASSED
tests/integration/test_data_tier_api.py::TestRetentionJobVoluntaryOnly::test_retention_preserves_recent_voluntary PASSED
tests/integration/test_data_tier_api.py::TestAPIIntegrationEdgeCases::test_concurrent_tier_updates PASSED
tests/integration/test_data_tier_api.py::TestAPIIntegrationEdgeCases::test_analytics_empty_merchant PASSED

============================== 10 passed in 3.14s ==============================
```

## Key Changes

### Files Modified
1. `backend/app/api/analytics.py` - Fixed router prefix
2. `backend/app/services/export/merchant_data_export_service.py` - Added orders export + tier filtering
3. `backend/tests/integration/test_data_tier_api.py` - Fixed order creation, added Decimal import

### New Features
- Orders section in data export CSV with tier filtering
- Total Orders count in export metadata
- Proper data tier filtering for conversations and orders

## Next Steps
- All Story 6-4 integration tests complete
- Ready for deployment or next story
