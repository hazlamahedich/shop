# ErrorCode Governance

This document defines the governance process for managing error codes across the Shopping Assistant Bot application.

## Error Code Ranges

Error codes are divided into 1000-number ranges, each owned by a specific team:

| Range | Owner | Team | Description |
|-------|-------|------|-------------|
| 1000-1999 | core team | Platform/System | General system errors, validation failures |
| 2000-2999 | security team | Security | Authentication, authorization, webhooks |
| 3000-3999 | llm team | AI/LLM | LLM provider errors, rate limits, timeouts |
| 4000-4999 | shopify team | Integrations | Shopify API, products, checkout |
| 5000-5999 | facebook team | Integrations | Messenger webhooks, messaging |
| 6000-6999 | checkout team | Cart | Cart operations, checkout flow |
| 7000-7999 | conversation team | Session | Conversations, context, sessions |

## Adding New Error Codes

### 1. Check Ownership
Before adding a new error code, verify you're adding to your team's range:
- Check the table above for your team's range
- If adding outside your range, contact the owning team first

### 2. Document New Code
Add the new error code to this document with:
- Error code number
- Error name (CONSTANT_CASE)
- Description
- Related acceptance criteria or feature
- Date added

### 3. Update Code Registry
Add the new code to `backend/app/core/errors.py`:
```python
class ErrorCode(IntEnum):
    # ... existing codes ...
    YOUR_NEW_ERROR = 3XXX  # In your team's range
```

### 4. Create Tests
Add tests for the new error code in `test_errors.py`:
```python
def test_your_new_error():
    error = APIError(ErrorCode.YOUR_NEW_ERROR, "message")
    assert error.code == ErrorCode.YOUR_NEW_ERROR
```

## Error Code Lifecycle

### Active
Error codes in active use across the application.

### Deprecated
Error codes that should no longer be used but are maintained for backward compatibility:
- Mark with `# DEPRECATED: Use NEW_ERROR instead` comment
- Update API documentation to indicate deprecation
- Maintain for at least 2 major versions before removal

### Deleted (Never Reused)
Error codes that have been removed:
- Document deletion reason and date in this file
- **Never reuse deleted codes** - this maintains log stability
- Create a new code instead

## Current Error Codes

### 1000-1999: General/System
| Code | Name | Description | Added |
|------|------|-------------|-------|
| 1000 | UNKNOWN_ERROR | Unexpected system error | 2024-02-03 |
| 1001 | VALIDATION_ERROR | Request validation failed | 2024-02-03 |
| 1002 | INTERNAL_ERROR | Internal server error | 2024-02-03 |

### 2000-2999: Auth/Security
| Code | Name | Description | Added |
|------|------|-------------|-------|
| 2000 | AUTH_FAILED | Authentication failed | 2024-02-03 |
| 2001 | TOKEN_EXPIRED | Access token expired | 2024-02-03 |
| 2002 | WEBHOOK_SIGNATURE_INVALID | Webhook signature verification failed | 2024-02-03 |
| 2003 | UNAUTHORIZED | Unauthorized access attempt | 2024-02-03 |

### 3000-3999: LLM Provider
| Code | Name | Description | Added |
|------|------|-------------|-------|
| 3000 | LLM_PROVIDER_ERROR | LLM provider returned error | 2024-02-03 |
| 3001 | LLM_RATE_LIMIT | LLM rate limit exceeded | 2024-02-03 |
| 3002 | LLM_TIMEOUT | LLM request timeout | 2024-02-03 |
| 3003 | LLM_QUOTA_EXCEEDED | LLM quota exceeded | 2024-02-03 |

### 4000-4999: Shopify Integration
| Code | Name | Description | Added |
|------|------|-------------|-------|
| 4000 | SHOPIFY_API_ERROR | Shopify API error | 2024-02-03 |
| 4001 | CHECKOUT_GENERATION_FAILED | Checkout URL generation failed | 2024-02-03 |
| 4002 | PRODUCT_NOT_FOUND | Product not found | 2024-02-03 |
| 4003 | STOREFRONT_API_ERROR | Storefront API error | 2024-02-03 |

### 5000-5999: Facebook/Messenger
| Code | Name | Description | Added |
|------|------|-------------|-------|
| 5000 | MESSENGER_WEBHOOK_ERROR | Messenger webhook error | 2024-02-03 |
| 5001 | MESSAGE_SEND_FAILED | Failed to send message | 2024-02-03 |
| 5002 | WEBHOOK_VERIFICATION_FAILED | Webhook verification failed | 2024-02-03 |

### 6000-6999: Cart/Checkout
| Code | Name | Description | Added |
|------|------|-------------|-------|
| 6000 | CART_NOT_FOUND | Cart not found | 2024-02-03 |
| 6001 | INVALID_QUANTITY | Invalid product quantity | 2024-02-03 |
| 6002 | CHECKOUT_EXPIRED | Checkout link expired | 2024-02-03 |
| 6003 | CART_SESSION_EXPIRED | Cart session expired | 2024-02-03 |

### 7000-7999: Conversation/Session
| Code | Name | Description | Added |
|------|------|-------------|-------|
| 7000 | SESSION_EXPIRED | Session expired | 2024-02-03 |
| 7001 | CONVERSATION_NOT_FOUND | Conversation not found | 2024-02-03 |
| 7002 | INVALID_CONTEXT | Invalid conversation context | 2024-02-03 |

## Examples

### Adding a New Error Code

**Scenario:** Adding a new error for "Product out of stock"

1. **Check ownership:** Product-related → Shopify team → 4000-4999 range ✓
2. **Pick next code:** 4004 (after 4003)
3. **Update errors.py:**
   ```python
   PRODUCT_OUT_OF_STOCK = 4004
   ```
4. **Document here:** Add to 4000-4999 table
5. **Add tests:** Create test for new error

### Error Response Format

All API errors follow this format:
```json
{
  "error_code": 4002,
  "message": "Product not found",
  "details": {
    "product_id": "123456"
  }
}
```

## Review Process

Before merging new error codes:
1. Code review must verify code is in correct range
2. Documentation (this file) must be updated
3. Tests must be added
4. Update CHANGELOG.md with new error codes
