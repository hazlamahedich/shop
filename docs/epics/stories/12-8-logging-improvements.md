# Story 12-8: Logging Improvements

**Epic**: 12 - Security Hardening
**Priority**: P2 (Medium)
**Status**: backlog
**Estimate**: 6 hours
**Dependencies**: None

## Problem Statement

Verbose debug logging in frontend widget (`widgetWsClient.ts`) could expose internal state. Backend logging may include sensitive data.

## Acceptance Criteria

- [ ] Audit all log statements for PII exposure
- [ ] Remove or guard verbose debug logs
- [ ] Implement structured logging (JSON)
- [ ] Add log level configuration
- [ ] Redact sensitive fields in logs
- [ ] Centralized log aggregation setup
- [ ] Log retention policy defined
- [ ] Security event logging enhanced

## Technical Design

### Structured Logging

```python
# backend/app/core/logging.py
import structlog

def redact_sensitive(data: dict) -> dict:
    SENSITIVE_FIELDS = {
        'password', 'token', 'secret', 'api_key',
        'credit_card', 'ssn', 'email', 'phone'
    }
    
    redacted = {}
    for key, value in data.items():
        if key.lower() in SENSITIVE_FIELDS:
            redacted[key] = '***REDACTED***'
        else:
            redacted[key] = value
    return redacted

logger = structlog.get_logger()
logger = logger.bind(redact_processor=redact_sensitive)
```

### Frontend Logging

```typescript
// frontend/src/widget/utils/logger.ts
const LOG_LEVEL = import.meta.env.PROD ? 'warn' : 'debug';

export const logger = {
    debug: (...args: any[]) => {
        if (LOG_LEVEL === 'debug') {
            console.debug('[Widget]', ...args);
        }
    },
    // Never log sensitive data
    info: (message: string, data?: SafeData) => { ... },
    warn: (message: string, data?: SafeData) => { ... },
    error: (message: string, error?: Error) => { ... },
};
```

### Security Events to Log

- Authentication attempts (success/failure)
- Password changes
- Permission changes
- Data exports
- Account deletions
- API key usage
- Rate limit violations

## Testing Strategy

1. Search for PII in log files
2. Verify sensitive data is redacted
3. Test log levels in different environments
4. Verify structured log format

## Related Files

- `backend/app/core/logging.py`
- `frontend/src/widget/utils/logger.ts` (new)
- `frontend/src/widget/utils/widgetWsClient.ts`
- `docker-compose.yml` (log aggregation)
