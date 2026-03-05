# Data Retention Monitoring Runbook

**Story**: 6-5 - 30-Day Retention Enforcement  
**Last Updated**: 2026-03-05  
**Owner**: Platform Team

## Overview

Automated data retention system that enforces GDPR/CCPA compliance by deleting voluntary conversation data after 30 days while preserving operational data indefinitely.

## Architecture

- **Scheduler**: APScheduler runs daily at midnight UTC
- **Retention Service**: `RetentionPolicy.delete_expired_voluntary_data()`
- **Batch Processing**: 1000 records per batch
- **Timeout**: 300 seconds (5 minutes) max execution time
- **Retry Logic**: 3 attempts with 10-second delay

## Monitoring

### Health Check Endpoint

```bash
# Check scheduler health
curl -H "X-Internal-Request: true" http://localhost:8000/api/v1/health/scheduler
```

**Expected Response**:
```json
{
  "status": "healthy",
  "running": true,
  "job_count": 1,
  "jobs": [
    {
      "id": "data_retention_cleanup",
      "name": "Daily data retention cleanup",
      "next_run": "2026-03-06T00:00:00+00:00",
      "trigger": "cron[hour='0', minute='0']"
    }
  ]
}
```

**Status Codes**:
- `200`: Scheduler healthy
- `503`: Scheduler not running (critical alert)

### Structlog Metrics

Monitor these log events:

**Success Events**:
- `retention_policy_executed` - Job completed successfully
- `retention_policy_batch_processed` - Batch processed
- `data_retention_job_completed` - Full job finished

**Warning Events**:
- `retention_policy_timeout_reached` - Job hit timeout limit

**Error Events**:
- `voluntary_data_cleanup_failed` - Retry triggered
- `voluntary_data_cleanup_failed_permanently` - All retries exhausted
- `data_retention_job_failed` - Job failed

### Key Metrics to Track

```python
# CloudWatch/Datadog queries
retention.jobs.completed:  # Count of successful jobs
retention.jobs.failed:     # Count of failed jobs
retention.deleted.count:   # Total records deleted
retention.timeout.count:   # Timeout events
retention.retry.count:     # Retry attempts
retention.elapsed_seconds: # Job duration histogram
```

## Alerting

### Critical Alerts

**Scheduler Down**:
- **Condition**: Health check returns 503
- **Impact**: GDPR/CCPA compliance risk
- **Action**: Restart backend service immediately
- **Escalation**: On-call engineer → Platform team lead

**Permanent Failure**:
- **Condition**: `voluntary_data_cleanup_failed_permanently` logged
- **Impact**: Data not being deleted, compliance violation
- **Action**: 
  1. Check database connectivity
  2. Review error logs for root cause
  3. Manually trigger cleanup if needed
- **Escalation**: Database team → Compliance officer

### Warning Alerts

**High Retry Count**:
- **Condition**: `retry.count > 5` in 1 hour
- **Impact**: Performance degradation
- **Action**: Investigate transient failures
- **Escalation**: Platform team (non-urgent)

**Timeout Events**:
- **Condition**: `retention.timeout.count > 0`
- **Impact**: Incomplete deletions
- **Action**: 
  1. Reduce batch size
  2. Increase timeout
  3. Check database performance
- **Escalation**: Database team

## Troubleshooting

### Job Not Running

**Symptoms**: Health check shows `running: false`

**Steps**:
1. Check backend logs for scheduler initialization errors
2. Verify APScheduler is started in `main.py`
3. Restart backend service
4. Check for port conflicts

### Job Running But Not Deleting Data

**Symptoms**: Job completes with `deleted_count: 0`

**Steps**:
1. Check if data exists past retention period:
   ```sql
   SELECT COUNT(*) FROM conversations 
   WHERE data_tier = 'voluntary' 
   AND updated_at < NOW() - INTERVAL '30 days';
   ```
2. Verify `data_tier` column is set correctly
3. Check audit logs for deletion attempts
4. Review structlog for errors

### Performance Issues

**Symptoms**: Job timing out, slow execution

**Steps**:
1. Check database performance metrics
2. Reduce batch size via `RETENTION_BATCH_SIZE` env var
3. Increase timeout via `RETENTION_TIMEOUT_SECONDS`
4. Add database indexes on `updated_at` and `data_tier`

### Database Connection Errors

**Symptoms**: Retry events in logs

**Steps**:
1. Check database connection pool settings
2. Verify `DATABASE_URL` is correct
3. Check for connection leaks
4. Review database logs for errors

## Manual Operations

### Trigger Manual Cleanup

```python
# Connect to backend container
python -m app.background_jobs.data_retention

# Or via API (if exposed)
curl -X POST http://localhost:8000/api/v1/admin/retention/trigger
```

### Query Audit Logs

```bash
# Recent automated deletions
curl "http://localhost:8000/api/v1/audit/retention-logs?trigger=auto&pageSize=100"

# Manual deletions
curl "http://localhost:8000/api/v1/audit/retention-logs?trigger=manual"

# Specific merchant
curl "http://localhost:8000/api/v1/audit/retention-logs?merchantId=123"
```

### Emergency Data Recovery

If operational data was accidentally deleted:

1. **Stop retention scheduler immediately**
2. **Restore from backup**:
   ```bash
   pg_restore -d shop_dev backup_2026-03-05.dump
   ```
3. **Verify data tier classification**:
   ```sql
   SELECT data_tier, COUNT(*) FROM conversations GROUP BY data_tier;
   ```
4. **Update data tiers if needed**:
   ```sql
   UPDATE conversations 
   SET data_tier = 'operational' 
   WHERE <criteria>;
   ```

## Configuration

### Environment Variables

```bash
# Retention period (days)
RETENTION_VOLUNTARY_DAYS=30

# Batch processing
RETENTION_BATCH_SIZE=1000
RETENTION_TIMEOUT_SECONDS=300

# Retry logic
RETENTION_RETRY_MAX_ATTEMPTS=3
RETENTION_RETRY_DELAY_SECONDS=10
```

### Changing Configuration

1. Update `.env` file or environment variables
2. Restart backend service
3. Verify new settings in health check response
4. Monitor first job run after change

## Compliance

### GDPR Requirements

- ✅ Voluntary data deleted within 30 days
- ✅ Audit trail maintained for all deletions
- ✅ Customer ID logged for each deletion
- ✅ Timestamp and retention period recorded

### CCPA Requirements

- ✅ Data retention period enforced
- ✅ Deletion requests tracked
- ✅ Operational data preserved for business purposes

### Audit Trail

All deletions logged in `deletion_audit_log` table with:
- Session/customer ID
- Merchant ID
- Deletion trigger (manual/auto)
- Retention period
- Timestamp
- Records deleted

Query audit logs via `/api/v1/audit/retention-logs` endpoint.

## Related Documentation

- [Data Tier Separation](./data-tier-separation.md)
- [Privacy Compliance](./privacy-compliance.md)
- [Database Schema](./database-schema.md)

## Support

**On-Call**: Platform team  
**Escalation**: platform-team@example.com  
**Runbook Version**: 1.0
