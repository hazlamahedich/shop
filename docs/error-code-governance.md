# ErrorCode Governance

This document defines the governance process for managing error codes across the Shopping Assistant Bot application.

## Error Code Ranges

Error codes are divided into 1000-number ranges, each owned by a specific team:

| Range     | Owner             | Team            | Description                                |
| --------- | ----------------- | --------------- | ------------------------------------------ |
| 1000-1999 | core team         | Platform/System | General system errors, validation failures |
| 2000-2999 | security team     | Security        | Authentication, authorization, webhooks    |
| 3000-3999 | llm team          | AI/LLM          | LLM provider errors, rate limits, timeouts |
| 4000-4999 | shopify team      | Integrations    | Shopify API, products, checkout            |
| 5000-5999 | facebook team     | Integrations    | Messenger webhooks, messaging              |
| 6000-6999 | checkout team     | Cart            | Cart operations, checkout flow             |
| 7000-7999 | conversation team | Session         | Conversations, context, sessions           |

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

| Code | Name             | Description               | Added      |
| ---- | ---------------- | ------------------------- | ---------- |
| 1000 | UNKNOWN_ERROR    | Unexpected system error   | 2024-02-03 |
| 1001 | VALIDATION_ERROR | Request validation failed | 2024-02-03 |
| 1002 | INTERNAL_ERROR   | Internal server error     | 2024-02-03 |

### 2000-2999: Auth/Security

| Code | Name                      | Description                                      | Added      |
| ---- | ------------------------- | ------------------------------------------------ | ---------- |
| 2000 | AUTH_FAILED               | Authentication failed                            | 2024-02-03 |
| 2001 | TOKEN_EXPIRED             | Access token expired                             | 2024-02-03 |
| 2002 | WEBHOOK_SIGNATURE_INVALID | Webhook signature verification failed            | 2024-02-03 |
| 2003 | UNAUTHORIZED              | Unauthorized access attempt                      | 2024-02-03 |
| 2004 | PREREQUISITES_INCOMPLETE  | Onboarding prerequisites not complete            | 2026-02-03 |
| 2005 | MERCHANT_NOT_FOUND        | Merchant account not found                       | 2026-02-03 |
| 2006 | DEPLOYMENT_IN_PROGRESS    | Deployment already in progress for this merchant | 2026-02-03 |
| 2007 | DEPLOYMENT_FAILED         | Deployment operation failed                      | 2026-02-03 |
| 2008 | DEPLOYMENT_CANCELLED      | Deployment was cancelled by user                 | 2026-02-03 |
| 2009 | DEPLOYMENT_TIMEOUT        | Deployment exceeded time limit (15 minutes)      | 2026-02-03 |
| 2010 | MERCHANT_ALREADY_EXISTS   | Merchant with this key already exists            | 2026-02-03 |

### 3000-3999: LLM Provider

| Code | Name               | Description                 | Added      |
| ---- | ------------------ | --------------------------- | ---------- |
| 3000 | LLM_PROVIDER_ERROR | LLM provider returned error | 2024-02-03 |
| 3001 | LLM_RATE_LIMIT     | LLM rate limit exceeded     | 2024-02-03 |
| 3002 | LLM_TIMEOUT        | LLM request timeout         | 2024-02-03 |
| 3003 | LLM_QUOTA_EXCEEDED | LLM quota exceeded          | 2024-02-03 |

### 4000-4999: Shopify Integration

| Code | Name                             | Description                                   | Added      |
| ---- | -------------------------------- | --------------------------------------------- | ---------- |
| 4000 | SHOPIFY_API_ERROR                | Generic Shopify API error                     | 2024-02-03 |
| 4001 | CHECKOUT_GENERATION_FAILED       | Checkout URL generation failed                | 2024-02-03 |
| 4002 | PRODUCT_NOT_FOUND                | Product not found                             | 2024-02-03 |
| 4003 | STOREFRONT_API_ERROR             | Storefront API error                          | 2024-02-03 |
| 4011 | SHOPIFY_OAUTH_STATE_MISMATCH     | OAuth state token mismatch (CSRF protection)  | 2026-02-03 |
| 4012 | SHOPIFY_OAUTH_DENIED             | User denied OAuth authorization               | 2026-02-03 |
| 4013 | SHOPIFY_TOKEN_EXCHANGE_FAILED    | Failed to exchange authorization code         | 2026-02-03 |
| 4014 | SHOPIFY_ADMIN_API_ACCESS_DENIED  | Insufficient permissions for Admin API        | 2026-02-03 |
| 4015 | SHOPIFY_STOREFRONT_TOKEN_FAILED  | Failed to create Storefront access token      | 2026-02-03 |
| 4016 | SHOPIFY_STOREFRONT_API_DENIED    | Storefront API access denied                  | 2026-02-03 |
| 4017 | SHOPIFY_ALREADY_CONNECTED        | Shopify store already connected               | 2026-02-03 |
| 4018 | SHOPIFY_NOT_CONNECTED            | Shopify store not connected                   | 2026-02-03 |
| 4019 | SHOPIFY_ENCRYPTION_KEY_MISSING   | Shopify encryption key not configured         | 2026-02-03 |
| 4020 | SHOPIFY_WEBHOOK_HMAC_INVALID     | Shopify webhook signature verification failed | 2026-02-03 |
| 4021 | SHOPIFY_WEBHOOK_VERIFY_FAILED    | Shopify webhook verification failed           | 2026-02-03 |
| 4022 | SHOPIFY_CHECKOUT_CREATE_FAILED   | Checkout creation failed                      | 2026-02-03 |
| 4023 | SHOPIFY_CHECKOUT_URL_INVALID     | Checkout URL validation failed                | 2026-02-03 |
| 4024 | SHOPIFY_SHOP_DOMAIN_INVALID      | Invalid Shopify domain format                 | 2026-02-03 |
| 4025 | SHOPIFY_PRODUCT_SEARCH_FAILED    | Product search failed                         | 2026-02-03 |
| 4026 | SHOPIFY_TIMEOUT                  | API timeout (Storefront)                      | 2026-02-04 |
| 4027 | SHOPIFY_INVALID_QUERY            | Malformed query                               | 2026-02-04 |
| 4028 | SHOPIFY_RATE_LIMITED             | Admin API rate limit (not Storefront)         | 2026-02-04 |
| 4029 | PRODUCT_MAPPING_FAILED           | Entity to filter mapping error                | 2026-02-04 |
| 4030 | SHOPIFY_PRODUCT_NOT_FOUND_SEARCH | No products found in search                   | 2026-02-04 |

### 5000-5999: Facebook/Messenger

| Code | Name                               | Description                                      | Added      |
| ---- | ---------------------------------- | ------------------------------------------------ | ---------- |
| 5000 | MESSENGER_WEBHOOK_ERROR            | Messenger webhook error                          | 2024-02-03 |
| 5001 | MESSAGE_SEND_FAILED                | Failed to send message                           | 2024-02-03 |
| 5002 | WEBHOOK_VERIFICATION_FAILED        | Webhook verification failed                      | 2024-02-03 |
| 5010 | FACEBOOK_OAUTH_STATE_MISMATCH      | OAuth state token mismatch (CSRF protection)     | 2026-02-03 |
| 5011 | FACEBOOK_OAUTH_DENIED              | User denied OAuth authorization                  | 2026-02-03 |
| 5012 | FACEBOOK_TOKEN_EXCHANGE_FAILED     | Failed to exchange authorization code for token  | 2026-02-03 |
| 5013 | FACEBOOK_PAGE_ACCESS_DENIED        | Insufficient permissions for page access         | 2026-02-03 |
| 5014 | FACEBOOK_WEBHOOK_SIGNATURE_INVALID | Webhook signature verification failed            | 2026-02-03 |
| 5015 | FACEBOOK_ALREADY_CONNECTED         | Facebook Page already connected to this merchant | 2026-02-03 |
| 5016 | FACEBOOK_NOT_CONNECTED             | Facebook Page not connected to this merchant     | 2026-02-03 |
| 5017 | FACEBOOK_ENCRYPTION_KEY_MISSING    | Facebook encryption key not configured           | 2026-02-03 |
| 5018 | FACEBOOK_WEBHOOK_VERIFY_FAILED     | Facebook webhook verification failed             | 2026-02-03 |
| 5026 | FACEBOOK_TIMEOUT                   | Send API timeout                                 | 2026-02-04 |
| 5027 | FACEBOOK_INVALID_RECIPIENT         | Invalid PSID                                     | 2026-02-04 |
| 5028 | FACEBOOK_MESSAGE_TOO_LARGE         | Message exceeds size limit                       | 2026-02-04 |
| 5029 | FACEBOOK_RATE_LIMITED              | Rate limit exceeded                              | 2026-02-04 |
| 5030 | MESSENGER_FORMATTING_FAILED        | Product formatting error                         | 2026-02-04 |
| 5031 | IMAGE_VALIDATION_FAILED            | Invalid image URL                                | 2026-02-04 |

| 5031 | IMAGE_VALIDATION_FAILED            | Invalid image URL                                | 2026-02-04 |

### 6000-6999: Cart/Checkout

| Code | Name                 | Description              | Added      |
| ---- | -------------------- | ------------------------ | ---------- |
| 6000 | CART_NOT_FOUND       | Cart not found           | 2024-02-03 |
| 6001 | INVALID_QUANTITY     | Invalid product quantity | 2024-02-03 |
| 6002 | CHECKOUT_EXPIRED     | Checkout link expired    | 2024-02-03 |
| 6003 | CART_SESSION_EXPIRED | Cart session expired     | 2024-02-03 |

### 7000-7999: Conversation/Session

| Code | Name                             | Description                                      | Added      |
| ---- | -------------------------------- | ------------------------------------------------ | ---------- |
| 7000 | SESSION_EXPIRED                  | Session expired                                  | 2024-02-03 |
| 7001 | CONVERSATION_NOT_FOUND           | Conversation does not exist or merchant lacks access | 2026-02-15 |
| 7002 | INVALID_CONTEXT                  | Invalid conversation context                     | 2024-02-03 |
| 7003 | INVALID_PAGE_NUMBER              | Page number < 1                                  | 2026-02-07 |
| 7004 | INVALID_PER_PAGE                 | Items per page out of range                      | 2026-02-07 |
| 7005 | INVALID_SORT_COLUMN              | Invalid sort column                              | 2026-02-07 |
| 7006 | MERCHANT_ACCESS_DENIED           | Merchant cannot access conversation              | 2026-02-07 |
| 7007 | INVALID_DATE_FORMAT              | Invalid date format for filtering                | 2026-02-07 |
| 7008 | INVALID_STATUS_VALUE             | Invalid status value for filtering               | 2026-02-07 |
| 7009 | INVALID_SENTIMENT_VALUE          | Invalid sentiment value for filtering            | 2026-02-07 |
| 7010 | CLARIFICATION_FLOW_FAILED        | Generic clarification error                      | 2026-02-04 |
| 7011 | CLARIFICATION_TIMEOUT            | User didn't respond to question                  | 2026-02-04 |
| 7012 | CLARIFICATION_MAX_ATTEMPTS       | Max 3 questions exceeded                         | 2026-02-04 |
| 7013 | QUESTION_GENERATION_FAILED       | Failed to generate question                      | 2026-02-04 |
| 7014 | CLARIFICATION_STATE_ERROR        | Invalid clarification state                      | 2026-02-04 |
| 7015 | CONSTRAINT_EXTRACTION_FAILED     | Failed to extract constraints                    | 2026-02-04 |
| 7020 | HANDOFF_DETECTION_ERROR          | Detection logic failed                           | 2026-02-14 |
| 7021 | HANDOFF_STATUS_UPDATE_FAILED     | Database update failed                           | 2026-02-14 |
| 7022 | HANDOFF_KEYWORD_TRIGGERED        | Keyword detection triggered handoff              | 2026-02-14 |
| 7023 | HANDOFF_LOW_CONFIDENCE_TRIGGERED | Low confidence triggered handoff                 | 2026-02-14 |
| 7024 | HANDOFF_LOOP_DETECTED            | Clarification loop triggered handoff             | 2026-02-14 |
| 7025 | HANDOFF_NOTIFICATION_FAILED      | General notification failure                     | 2026-02-14 |
| 7026 | HANDOFF_EMAIL_FAILED             | Email send failed                                | 2026-02-14 |
| 7027 | HANDOFF_ALERT_CREATE_FAILED      | Database alert creation failed                   | 2026-02-14 |
| 7028 | HANDOFF_URGENCY_DETECTION_FAILED | Urgency detection error                          | 2026-02-14 |
| 7029 | HANDOFF_RATE_LIMITED             | Email rate limited (info, not error)             | 2026-02-14 |

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
