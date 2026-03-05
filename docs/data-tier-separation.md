# Data Tier Separation

**Story:** 6-4 - Data Tier Separation  
**Epic:** 6 - Data Privacy & Compliance  
**Status:** Implementation Complete

## Overview

Data tier separation is a foundational privacy architecture that categorizes all customer data into three distinct tiers with different retention policies and deletion eligibility. This system ensures GDPR/CCPA compliance while supporting essential business operations.

## Data Tier Definitions

### VOLUNTARY (Tier 1)

**Definition:** User-initiated data that can be deleted upon request.

**Data Types:**
- Conversation history
- Product preferences
- Chat messages
- Search history
- Cart contents (Redis-only)

**Retention Policy:** 30 days maximum  
**Deletable:** ✅ Yes (GDPR/CCPA Right to be Forgotten)  
**Database Default:** `voluntary`

**Use Cases:**
- Personalization and recommendations
- Conversation context
- Shopping assistance

**Examples:**
```python
# Conversation with voluntary tier
conversation = Conversation(
    merchant_id=1,
    platform="widget",
    platform_sender_id="user123",
    data_tier=DataTier.VOLUNTARY  # Can be deleted on request
)

# Message with voluntary tier
message = Message(
    conversation_id=conversation.id,
    sender="customer",
    content="I'm looking for running shoes",
    data_tier=DataTier.VOLUNTARY
)
```

### OPERATIONAL (Tier 2)

**Definition:** Data required for business operations, exempt from deletion.

**Data Types:**
- Order references
- Transaction records
- Consent records
- Session IDs
- Timestamps

**Retention Policy:** Indefinite (business requirement)  
**Deletable:** ❌ No (required for operations)  
**Database Default:** `operational` (for orders)

**Use Cases:**
- Order tracking and fulfillment
- Payment processing
- Customer support
- Audit trails

**Examples:**
```python
# Order with operational tier (cannot be deleted)
order = Order(
    merchant_id=1,
    order_number="ORD-12345",
    platform_sender_id="user123",
    total=99.99,
    data_tier=DataTier.OPERATIONAL  # Required for business
)

# Consent record with operational tier
consent = Consent(
    merchant_id=1,
    session_id="user123",
    consent_type=ConsentType.CONVERSATION,
    granted=True,
    data_tier=DataTier.OPERATIONAL  # Required for compliance audit
)
```

### ANONYMIZED (Tier 3)

**Definition:** Aggregated analytics with all PII removed.

**Data Types:**
- Aggregated conversation counts
- Average response times
- Popular products (no customer association)
- Cost tracking (no customer IDs)
- Geographic distribution (no addresses)

**Retention Policy:** Indefinite (no privacy impact)  
**Deletable:** ❌ No (no personal data)  
**Database Default:** N/A (generated from other tiers)

**Use Cases:**
- Business analytics
- Performance monitoring
- Cost optimization
- Trend analysis

**Examples:**
```python
# Anonymized analytics (no PII)
analytics_summary = {
    "total_conversations": 1250,
    "avg_messages_per_conversation": 4.2,
    "total_cost_usd": 15.50,
    "tier": DataTier.ANONYMIZED.value,
    # No customer IDs, emails, or names
}
```

## Retention Policies

### VOLUNTARY Data Retention

**Policy:** Delete after 30 days of inactivity

**Implementation:**
```python
from app.services.privacy.retention_service import RetentionPolicy

# Delete expired voluntary data
policy = RetentionPolicy()
deleted_count = await policy.delete_expired_voluntary_data(db)
```

**Cron Job:** Daily at 2:00 AM UTC
```bash
# Runs retention policy for voluntary tier
python -m app.tasks.retention_cleanup
```

**Affected Tables:**
- `conversations` (where `data_tier = 'voluntary'`)
- `messages` (where `data_tier = 'voluntary'`)

### OPERATIONAL Data Retention

**Policy:** Keep indefinitely

**Rationale:**
- Required for order tracking
- Payment dispute resolution
- Tax compliance
- Business analytics

**No automated deletion**

### ANONYMIZED Data Retention

**Policy:** Keep indefinitely

**Rationale:**
- No personal identifiers
- No privacy impact
- Safe for long-term storage

**No automated deletion**

## Tier Transition Rules

### Allowed Transitions

✅ **VOLUNTARY → ANONYMIZED**
- User opts out of consent
- GDPR/CCPA deletion request
- PII stripped, aggregated metrics retained

✅ **VOLUNTARY → OPERATIONAL**
- Not applicable (tier escalation only)

✅ **OPERATIONAL → ANONYMIZED**
- Aggregation for analytics
- PII stripped before storage

### Forbidden Transitions

❌ **OPERATIONAL → VOLUNTARY**
- Would make business data deletable
- Violates operational requirements
- Error: `TIER_TRANSITION_NOT_ALLOWED (11021)`

❌ **ANONYMIZED → VOLUNTARY/OPERATIONAL**
- Would add PII to anonymized data
- Violates anonymization principle

### Implementation

```python
from app.services.privacy.data_tier_service import DataTierService
from app.services.privacy.data_tier_service import DataTier

service = DataTierService()

# Update tier (with validation)
await service.update_tier(
    db=db,
    model_class=Conversation,
    record_id=123,
    new_tier=DataTier.ANONYMIZED
)
```

## API Integration

### Tier Distribution Endpoint

**Endpoint:** `GET /api/v1/analytics/summary`

**Response:**
```json
{
  "merchantId": 1,
  "tierDistribution": {
    "conversations": {
      "voluntary": 100,
      "operational": 0,
      "anonymized": 50
    },
    "messages": {
      "voluntary": 500,
      "operational": 0,
      "anonymized": 250
    },
    "orders": {
      "voluntary": 0,
      "operational": 75,
      "anonymized": 0
    },
    "summary": {
      "totalVoluntary": 600,
      "totalOperational": 75,
      "totalAnonymized": 300
    }
  },
  "generatedAt": "2026-03-05T10:00:00Z",
  "tier": "anonymized"
}
```

### Data Export Filtering

**Endpoint:** `GET /api/v1/data/export`

**Behavior:**
- Excludes ANONYMIZED tier (no PII)
- Includes VOLUNTARY tier (with consent)
- Includes OPERATIONAL tier (business data)

**Implementation:**
```python
# MerchantDataExportService filters by tier
conversations = await db.execute(
    select(Conversation)
    .where(Conversation.merchant_id == merchant_id)
    .where(Conversation.data_tier.in_([
        DataTier.VOLUNTARY,
        DataTier.OPERATIONAL
    ]))
)
```

## Consent Integration

### Opt-Out Flow

When user opts out of consent:

1. **Delete voluntary data**
   ```python
   await consent_service.delete_voluntary_data(
       session_id="user123",
       merchant_id=1,
       visitor_id="visitor-abc"
   )
   ```

2. **Update tier to ANONYMIZED**
   ```python
   await consent_service.update_data_tier(
       session_id="user123",
       visitor_id="visitor-abc",
       new_tier="anonymized"
   )
   ```

3. **Preserve operational data**
   - Orders remain (operational tier)
   - Consent record remains (operational tier)
   - Session ID remains (operational tier)

### Opt-In Flow

When user opts in to consent:

1. **Keep tier as VOLUNTARY**
   - New conversations: `data_tier=DataTier.VOLUNTARY`
   - New messages: `data_tier=DataTier.VOLUNTARY`

2. **Enable persistence**
   - Conversation history stored
   - Personalization enabled

## Audit Trail

### Tier Changes

All tier transitions are logged in `deletion_audit_log`:

```sql
SELECT * FROM deletion_audit_log
WHERE session_id = 'user123'
ORDER BY created_at DESC;
```

**Fields:**
- `session_id`: User session
- `visitor_id`: Cross-platform identifier
- `conversations_deleted`: Count
- `messages_deleted`: Count
- `redis_keys_cleared`: Count
- `error_message`: Failure details (if any)

### Retention Job Logs

Retention policy execution is logged:

```python
logger.info(
    "retention_policy_executed",
    tier="voluntary",
    cutoff_days=30,
    conversations_deleted=150,
    messages_deleted=750,
    execution_time_ms=234
)
```

## Error Codes

| Code | Name | Description |
|------|------|-------------|
| 11020 | `INVALID_DATA_TIER` | Invalid data tier value (must be voluntary/operational/anonymized) |
| 11021 | `TIER_TRANSITION_NOT_ALLOWED` | Cannot downgrade tier (operational → voluntary) |
| 11022 | `RETENTION_POLICY_FAILED` | Failed to apply retention policy |
| 11023 | `ANONYMIZATION_FAILED` | Failed to anonymize data |

## Database Schema

### Migration: 037_add_data_tier_columns.py

**Changes:**
1. Created `datatier` ENUM
2. Added `data_tier` columns to tables
3. Created composite indexes

**Rollback:**
```bash
alembic downgrade -1
```

**Tables:**
- `conversations.data_tier` (default: voluntary)
- `messages.data_tier` (default: voluntary)
- `orders.data_tier` (default: operational)

**Indexes:**
- `ix_conversations_tier_created` (data_tier, created_at)
- `ix_messages_tier_created` (data_tier, created_at)
- `ix_orders_tier_created` (data_tier, created_at)

## Testing

### Unit Tests

```bash
cd backend
source venv/bin/activate
python -m pytest app/services/privacy/test_data_tier_service.py -v
```

### Integration Tests

```bash
python -m pytest tests/integration/test_data_tier_migration.py -v
python -m pytest tests/integration/test_consent_tier_integration.py -v
```

### API Tests

```bash
python -m pytest tests/integration/test_analytics.py::test_get_anonymized_summary -v
```

## Performance Considerations

| Operation | Target | Optimization |
|-----------|--------|--------------|
| Tier update | <100ms | Index on data_tier column |
| Retention query | <5s for 10K records | Composite index (tier, created_at) |
| Analytics aggregation | <30s for 100K records | Batch processing, background job |
| Export with tier filter | <10s for 10K records | Index-based filtering |

## Compliance

### GDPR Requirements Met

✅ **Right to be Forgotten**
- VOLUNTARY tier data deleted on request
- ANONYMIZED tier preserves non-personal analytics

✅ **Data Minimization**
- Only necessary data stored in OPERATIONAL tier
- Personal data limited to VOLUNTARY tier

✅ **Purpose Limitation**
- VOLUNTARY: Personalization
- OPERATIONAL: Business operations
- ANONYMIZED: Analytics only

✅ **Storage Limitation**
- VOLUNTARY: 30-day retention
- OPERATIONAL: Indefinite (with justification)
- ANONYMIZED: Indefinite (no PII)

### CCPA Requirements Met

✅ **Right to Delete**
- VOLUNTARY tier deletable
- OPERATIONAL tier exempt (business need)

✅ **Right to Know**
- Data export includes tier information
- Clear categorization of data types

✅ **Opt-Out Rights**
- Consent opt-out triggers tier update
- Data deletion within 45 days

## References

- [Story 6-4 Implementation](_bmad-output/implementation-artifacts/6-4-data-tier-separation.md)
- [Epic 6 Definition](_bmad-output/planning-artifacts/epics/epic-6-data-privacy-compliance.md)
- [Architecture - GDPR/CCPA Compliance](_bmad-output/planning-artifacts/architecture.md#compliance-requirements)
- [Story 6-1: Opt-In Consent Flow](6-1-opt-in-consent-flow.md)
- [Story 6-2: Request Data Deletion](6-2-request-data-deletion.md)
- [Story 6-3: Merchant CSV Export](6-3-merchant-csv-export.md)
