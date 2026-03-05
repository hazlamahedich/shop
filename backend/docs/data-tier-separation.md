# Data Tier Separation Architecture

**Story**: 6-4, 6-5  
**Last Updated**: 2026-03-05  
**Purpose**: GDPR/CCPA compliance through data classification and retention

## Overview

The platform implements a three-tier data classification system to ensure GDPR/CCPA compliance while preserving business-critical operational data.

## Data Tiers

### 1. VOLUNTARY Tier

**Classification**: User-provided, non-essential data  
**Retention**: 30 days (configurable via `RETENTION_VOLUNTARY_DAYS`)  
**Examples**:
- Conversation messages (customer support chat)
- User preferences
- Search history
- Cart contents (non-transactional)

**Deletion**: Automatically deleted after retention period via daily scheduled job

### 2. OPERATIONAL Tier

**Classification**: Business-critical, transaction-related data  
**Retention**: **INDEFINITE** (never deleted)  
**Examples**:
- Order references
- Transaction IDs
- Payment metadata
- Shipping information
- Tax records

**Deletion**: Never automatically deleted. Manual deletion only with compliance approval.

### 3. ANONYMIZED Tier

**Classification**: De-identified data for analytics  
**Retention**: **INDEFINITE** (never deleted)  
**Examples**:
- Aggregated metrics
- Anonymized conversation patterns
- Trend analysis data

**Deletion**: Never automatically deleted. Preserved for business intelligence.

## Implementation

### Database Schema

```python
# models/conversation.py
class DataTier(str, Enum):
    VOLUNTARY = "voluntary"
    OPERATIONAL = "operational"
    ANONYMIZED = "anonymized"

class Conversation(Base):
    data_tier: Mapped[DataTier] = mapped_column(
        SQLEnum(DataTier, name="datatier", create_type=False),
        default=DataTier.VOLUNTARY,
        nullable=False,
        index=True,  # Critical for retention query performance
    )
```

### Retention Service

```python
# services/privacy/retention_service.py
class RetentionPolicy:
    @staticmethod
    async def delete_expired_voluntary_data(
        db: AsyncSession,
        days: int = 30,
        batch_size: int = 1000,
        timeout_seconds: int = 300,
    ) -> int:
        """Delete VOLUNTARY tier data older than retention period.
        
        Performance: Processes in batches to handle 10K+ conversations
        within 5-minute timeout requirement.
        """
```

### Scheduler Configuration

```python
# background_jobs/data_retention.py
scheduler.add_job(
    run_retention_cleanup,
    trigger=CronTrigger(hour=0, minute=0, timezone="UTC"),
    id="data_retention_cleanup",
    max_instances=1,  # Prevent concurrent execution
)
```

## Operational Procedures

### Checking Data Tier Distribution

```sql
SELECT 
    data_tier, 
    COUNT(*) as count,
    MIN(updated_at) as oldest_record,
    MAX(updated_at) as newest_record
FROM conversations
GROUP BY data_tier;
```

### Finding Records for Deletion

```sql
SELECT COUNT(*)
FROM conversations
WHERE data_tier = 'voluntary'
AND updated_at < NOW() - INTERVAL '30 days';
```

### Manual Tier Update

```sql
-- Reclassify conversation as operational
UPDATE conversations
SET data_tier = 'operational'
WHERE id = 123;
```

## Monitoring

### Health Check

```bash
curl -H "X-Internal-Request: true" \
  http://localhost:8000/api/v1/health/scheduler
```

### Audit Log Query

```bash
# Recent automated deletions
curl "http://localhost:8000/api/v1/audit/retention-logs?trigger=auto&pageSize=100"
```

### Structlog Events

- `retention_policy_executed` - Successful deletion
- `retention_policy_batch_processed` - Batch progress
- `voluntary_data_cleanup_failed` - Retry triggered

## Configuration

### Environment Variables

```bash
# .env
RETENTION_VOLUNTARY_DAYS=30
RETENTION_BATCH_SIZE=1000
RETENTION_TIMEOUT_SECONDS=300
RETENTION_RETRY_MAX_ATTEMPTS=3
RETENTION_RETRY_DELAY_SECONDS=10
```

### Performance Tuning

**For Large Datasets (>100K conversations)**:
```bash
RETENTION_BATCH_SIZE=500
RETENTION_TIMEOUT_SECONDS=600
```

**For Small Datasets (<10K conversations)**:
```bash
RETENTION_BATCH_SIZE=2000
RETENTION_TIMEOUT_SECONDS=180
```

## Compliance

### GDPR Requirements

✅ **Right to Erasure**: Automated deletion of voluntary data  
✅ **Data Minimization**: Only operational data retained indefinitely  
✅ **Audit Trail**: All deletions logged with customer ID, timestamp, retention period

### CCPA Requirements

✅ **Retention Periods**: 30-day default, configurable  
✅ **Deletion Tracking**: Audit logs accessible via API  
✅ **Business Purpose Exception**: Operational data preserved

## Migration Guide

### Adding Data Tier to New Tables

1. Add `data_tier` column with default `VOLUNTARY`:
```python
data_tier: Mapped[DataTier] = mapped_column(
    SQLEnum(DataTier, name="datatier", create_type=False),
    default=DataTier.VOLUNTARY,
    nullable=False,
    index=True,
)
```

2. Create migration:
```bash
alembic revision -m "add_data_tier_to_new_table"
```

3. Update retention service if needed

### Reclassifying Existing Data

1. Identify operational data:
```sql
SELECT id FROM conversations
WHERE /* operational criteria */;
```

2. Update tier:
```sql
UPDATE conversations
SET data_tier = 'operational'
WHERE /* operational criteria */;
```

3. Verify:
```sql
SELECT data_tier, COUNT(*) FROM conversations GROUP BY data_tier;
```

## Troubleshooting

### Issue: Operational Data Being Deleted

**Cause**: Incorrect `data_tier` classification  
**Solution**:
1. Stop retention scheduler
2. Reclassify affected records
3. Restore from backup if needed
4. Review classification logic

### Issue: Retention Job Timing Out

**Cause**: Large dataset, insufficient batch size  
**Solution**:
1. Reduce `RETENTION_BATCH_SIZE`
2. Increase `RETENTION_TIMEOUT_SECONDS`
3. Add database indexes

### Issue: Voluntary Data Not Being Deleted

**Cause**: 
- `data_tier` not set correctly
- Scheduler not running
- Job failing silently

**Solution**:
1. Check health endpoint
2. Verify `data_tier` values
3. Review structlog for errors

## Related Documentation

- [Retention Monitoring Runbook](./retention-monitoring-runbook.md)
- [Privacy Compliance](./privacy-compliance.md)
- [Database Schema](./database-schema.md)

## Version History

- **2026-03-05**: Added Story 6-5 documentation (batch processing, retry logic)
- **2026-03-04**: Initial version (Story 6-4 data tier separation)
