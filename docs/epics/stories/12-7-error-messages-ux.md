# Story 12-7: Error Messages UX Review

**Epic**: 12 - Security Hardening
**Priority**: P2 (Medium)
**Status**: backlog
**Estimate**: 4 hours
**Dependencies**: None

## Problem Statement

Error messages may reveal too much internal information (stack traces, internal paths, database errors) which aids attackers.

## Acceptance Criteria

- [ ] Audit all user-facing error messages
- [ ] Generic messages for authentication errors
- [ ] No stack traces in production responses
- [ ] No database error exposure
- [ ] Consistent error format across API
- [ ] Helpful but secure password reset messages
- [ ] Rate limit messages don't reveal limits

## Technical Design

### Error Response Standard

```python
# backend/app/core/errors.py
from enum import Enum

class ErrorCode(str, Enum):
    AUTH_FAILED = "AUTH_FAILED"
    INVALID_INPUT = "INVALID_INPUT"
    RATE_LIMITED = "RATE_LIMITED"
    NOT_FOUND = "NOT_FOUND"
    SERVER_ERROR = "SERVER_ERROR"

class APIError(Exception):
    def __init__(
        self, 
        code: ErrorCode, 
        message: str,
        details: dict | None = None
    ):
        self.code = code
        self.message = message
        self.details = details

# User-facing messages (generic)
USER_MESSAGES = {
    ErrorCode.AUTH_FAILED: "Invalid email or password",
    ErrorCode.RATE_LIMITED: "Too many requests. Please try again later",
    ErrorCode.SERVER_ERROR: "An unexpected error occurred",
}
```

### Auth Error Best Practices

```python
# DON'T: Reveal which field is wrong
"Email not found"  # Helps enumeration
"Password is incorrect"  # Helps enumeration

# DO: Generic message
"Invalid email or password"

# DON'T: Reveal password policy
"Password must be 8+ chars with uppercase, number, symbol"

# DO: Generic policy hint
"Password does not meet requirements"
```

## Testing Strategy

1. Review all API error responses
2. Test authentication failure messages
3. Test database error handling
4. Test production vs development error detail

## Related Files

- `backend/app/core/errors.py`
- `backend/app/middleware/error_handler.py`
- `frontend/src/components/ErrorBoundary.tsx`
