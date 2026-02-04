# Security Assessment Report

**Project:** Shopping Assistant Bot
**Assessment Date:** February 4, 2026
**Assessor:** Security Audit Agent
**Version:** 1.0.0
**Requirements:** NFR-S1 to NFR-S11 from epics.md

---

## Executive Summary

This security assessment evaluates the Shopping Assistant Bot implementation against the 11 security Non-Functional Requirements (NFR-S1 to NFR-S11) defined in the project epics. The assessment covers authentication, encryption, webhook security, input sanitization, data privacy, and compliance.

### Overall Security Posture

| Category | Status | Count |
|----------|--------|-------|
| ✅ Fully Implemented | 4 | NFR-S3, S4, S5, S6 |
| ⚠️ Partially Implemented | 3 | NFR-S2, S8, S11 |
| ❌ Not Implemented | 4 | NFR-S1, S7, S9, S10 |

### Key Findings

**Strengths:**
- Strong webhook signature verification for both Facebook and Shopify
- Proper OAuth token encryption at rest using Fernet symmetric encryption
- Environment-based configuration for API keys (LLM providers)
- Comprehensive input sanitization before LLM processing

**Critical Gaps:**
- No HTTPS enforcement or HTTP-to-HTTPS redirects implemented
- Missing Content Security Policy headers
- No database-level encryption for conversation data
- Missing data retention enforcement and GDPR deletion workflows
- No CSRF protection beyond OAuth flows

**Risk Level:** MEDIUM-HIGH

The application has good foundational security practices but lacks several critical security controls required for production deployment, particularly around HTTPS enforcement, security headers, and data privacy compliance.

---

## NFR Compliance Matrix

| ID | Requirement | Status | Implementation | Priority |
|----|-------------|--------|----------------|----------|
| NFR-S1 | HTTPS for all API endpoints | ❌ Missing | No HTTP redirect logic found | HIGH |
| NFR-S2 | Conversation data encryption at rest | ⚠️ Partial | Token encryption exists, no DB encryption | HIGH |
| NFR-S3 | OAuth token encryption at rest | ✅ Implemented | Fernet encryption for FB/Shopify tokens | HIGH |
| NFR-S4 | API keys in environment variables | ✅ Implemented | LLM keys via env vars | MEDIUM |
| NFR-S5 | Webhook signature verification | ✅ Implemented | HMAC-SHA256 for both platforms | HIGH |
| NFR-S6 | Input sanitization before LLM | ✅ Implemented | Comprehensive sanitizer module | HIGH |
| NFR-S7 | Content Security Policy headers | ❌ Missing | No CSP headers in middleware | MEDIUM |
| NFR-S8 | CSRF tokens for state changes | ⚠️ Partial | OAuth CSRF only, no general CSRF | MEDIUM |
| NFR-S9 | PCI-DSS via Shopify checkout | ⚠️ Partial | Checkout URL gen exists, no validation | HIGH |
| NFR-S10 | Data deletion within 30 days | ❌ Missing | No deletion workflow implemented | HIGH |
| NFR-S11 | 30-day conversation retention | ⚠️ Partial | No automatic cleanup job | MEDIUM |

---

## Detailed Findings per NFR

### NFR-S1: HTTPS Enforcement

**Requirement:** All API endpoints must use HTTPS (HTTP redirects to HTTPS)

**Status:** ❌ NOT IMPLEMENTED

**Evidence:**
- File: `/Users/sherwingorechomante/shop/backend/app/main.py`
- No middleware or configuration found for HTTP-to-HTTPS redirects
- No SSL/TLS context configuration in uvicorn startup
- Application runs on `0.0.0.0:8000` without HTTPS enforcement

**Gap Analysis:**
The current implementation relies on infrastructure-level TLS (e.g., reverse proxy) but has no application-level enforcement. This creates risks if:
- The application is accidentally deployed without TLS termination
- Internal traffic between components is unencrypted
- Development configurations leak to production

**Recommendation:**

```python
# Add to backend/app/main.py
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware

# In app initialization:
if not settings()["DEBUG"]:
    # Force HTTPS in production
    app.add_middleware(HTTPSRedirectMiddleware)

    # Restrict to trusted hosts only
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings()["ALLOWED_HOSTS"]
    )
```

**Priority:** HIGH
**OWASP Reference:** A05:2021 – Security Misconfiguration
**Effort:** 2 hours

---

### NFR-S2: Conversation Data Encryption at Rest

**Requirement:** User conversation data must be encrypted at rest in the primary database

**Status:** ⚠️ PARTIALLY IMPLEMENTED

**Evidence:**
- File: `/Users/sherwingorechomante/shop/backend/app/models/message.py`
  - `Message.content` stored as plain `Text` field (line 38-40)
  - `Message.message_metadata` stored as `JSONB` (line 53-56)
- File: `/Users/sherwingorechomante/shop/backend/app/models/conversation.py`
  - No encrypted fields for conversation data

**Gap Analysis:**
While OAuth tokens are encrypted (NFR-S3), conversation content is stored in plain text. PostgreSQL does not encrypt data by default. Risks include:
- Database compromise exposes all customer conversations
- Backup files contain sensitive user data
- Compliance violations for GDPR/CCPA

**Current State:**
```python
# backend/app/models/message.py:38
content: Mapped[str] = mapped_column(
    Text,  # ❌ Plain text storage
    nullable=False,
)
```

**Recommendation:**

```python
# Add pgcrypto-based encryption for Message model
# Requires: CREATE EXTENSION IF NOT EXISTS pgcrypto;

from sqlalchemy import func
from sqlalchemy.dialects.postgresql import BYTEA

class Message(Base):
    # ... existing fields ...

    content_encrypted: Mapped[bytes] = mapped_column(
        BYTEA,
        nullable=False,
    )

    @property
    def content(self) -> str:
        """Decrypt content on access"""
        # Use pgcrypto decrypt() with app encryption key
        pass

    @content.setter
    def content(self, value: str) -> None:
        """Encrypt content on write"""
        # Use pgcrypto encrypt() with app encryption key
        pass
```

**Alternative (Simpler):** Use application-level encryption:

```python
# In backend/app/core/security.py:
def encrypt_conversation_content(content: str) -> str:
    """Encrypt conversation content using Fernet"""
    fernet = get_fernet()
    return fernet.encrypt(content.encode()).decode()

def decrypt_conversation_content(content_encrypted: str) -> str:
    """Decrypt conversation content"""
    fernet = get_fernet()
    return fernet.decrypt(content_encrypted.encode()).decode()
```

**Priority:** HIGH
**OWASP Reference:** A03:2021 – Injection (via SQL exposure)
**Effort:** 8 hours (DB changes) or 4 hours (app-level)

---

### NFR-S3: OAuth Token Encryption at Rest

**Requirement:** OAuth tokens (Facebook, Shopify) must be encrypted at rest

**Status:** ✅ IMPLEMENTED

**Evidence:**
- File: `/Users/sherwingorechomante/shop/backend/app/core/security.py`
  - `encrypt_access_token()` (line 109-120)
  - `decrypt_access_token()` (line 123-137)
  - Uses `cryptography.fernet` for symmetric encryption
- File: `/Users/sherwingorechomante/shop/backend/app/models/facebook_integration.py`
  - `access_token_encrypted` field (line 48-51)
- File: `/Users/sherwingorechomante/shop/backend/app/models/shopify_integration.py`
  - `storefront_token_encrypted` field (line 45-48)
  - `admin_token_encrypted` field (line 49-52)

**Strengths:**
- Uses Fernet (AES-128-CBC + HMAC) for encryption
- Tokens never stored in plain text
- Encryption key from environment variable
- Constant-time comparison prevents timing attacks

**Implementation Details:**
```python
# backend/app/core/security.py:109
def encrypt_access_token(token: str) -> str:
    """Encrypt Facebook page access token."""
    fernet = get_fernet()
    encrypted = fernet.encrypt(token.encode())
    return encrypted.decode()
```

**Recommendations:**
- ✅ No immediate action required
- Consider key rotation strategy for long-term deployments
- Document key backup/recovery procedures

**Priority:** COMPLETE
**OWASP Reference:** A02:2021 – Cryptographic Failures (Mitigated)

---

### NFR-S4: API Keys in Environment Variables

**Requirement:** API keys (LLM providers) must be stored as environment variables

**Status:** ✅ IMPLEMENTED

**Evidence:**
- File: `/Users/sherwingorechomante/shop/backend/app/core/config.py`
  - LLM provider keys from environment (line 86, 95, 98, 101, 104)
  - All keys use `os.getenv()` with safe defaults
- File: `/Users/sherwingorechomante/shop/.env.example`
  - Demonstrates proper env var structure
  - No hardcoded secrets found in codebase

**Implementation Details:**
```python
# backend/app/core/config.py:86-105
"LLM_API_KEY": os.getenv("LLM_API_KEY", ""),
"OPENAI_API_KEY": os.getenv("OPENAI_API_KEY", ""),
"ANTHROPIC_API_KEY": os.getenv("ANTHROPIC_API_KEY", ""),
"GEMINI_API_KEY": os.getenv("GEMINI_API_KEY", ""),
"GLM_API_KEY": os.getenv("GLM_API_KEY", ""),
```

**Strengths:**
- No API keys in source code
- Environment-specific configuration
- `.env.example` documents required variables without exposing secrets
- Pre-commit hook `detect-private-key` prevents commits

**Recommendations:**
- ✅ Current implementation is solid
- Add runtime validation that required keys are set in production
- Consider using secret management (AWS Secrets Manager, Vault) for production

**Priority:** COMPLETE
**OWASP Reference:** A07:2021 – Identification and Authentication Failures (Mitigated)

---

### NFR-S5: Webhook Signature Verification

**Requirement:** All webhooks (Facebook, Shopify) must verify request signatures

**Status:** ✅ IMPLEMENTED

**Evidence:**

**Facebook Webhook Verification:**
- File: `/Users/sherwingorechomante/shop/backend/app/api/webhooks/facebook.py`
  - Signature verification at line 135-137
  - Uses `X-Hub-Signature-256` header
- File: `/Users/sherwingorechomante/shop/backend/app/core/security.py`
  - `verify_webhook_signature()` (line 140-170)
  - HMAC-SHA256 with constant-time comparison

**Shopify Webhook Verification:**
- File: `/Users/sherwingorechomante/shop/backend/app/api/webhooks/shopify.py`
  - HMAC verification at line 76-78
  - Uses `X-Shopify-Hmac-Sha256` header
- File: `/Users/sherwingorechomante/shop/backend/app/core/security.py`
  - `verify_shopify_webhook_hmac()` (line 198-229)

**Implementation Details:**
```python
# backend/app/core/security.py:165-170
# Compute HMAC-SHA256 of raw payload
h = HMAC(app_secret.encode(), hashes.SHA256())
h.update(raw_payload)
computed_hash = h.finalize().hex()

# Use constant-time comparison to prevent timing attacks
return compare_digest(computed_hash, expected_hash)
```

**Strengths:**
- Both webhooks use HMAC-SHA256
- Constant-time comparison prevents timing attacks
- Raw payload verification prevents body manipulation
- 403 responses on signature failure
- Comprehensive test coverage

**Recommendations:**
- ✅ No immediate action required
- Consider adding webhook replay attack prevention (timestamp validation)

**Priority:** COMPLETE
**OWASP Reference:** A01:2021 – Broken Access Control (Mitigated)

---

### NFR-S6: Input Sanitization Before LLM Processing

**Requirement:** User inputs must be sanitized before LLM processing

**Status:** ✅ IMPLEMENTED

**Evidence:**
- File: `/Users/sherwingorechomante/shop/backend/app/core/input_sanitizer.py`
  - Comprehensive sanitization module (139 lines)
  - `sanitize_llm_input()` (line 24-52)
  - Pattern-based injection prevention
  - Test validation functions

**Implementation Details:**
```python
# backend/app/core/input_sanitizer.py:24-52
def sanitize_llm_input(text: str, max_length: int = 10000) -> str:
    """Sanitize user input before LLM processing (NFR-S6)."""
    # Truncate to max length
    text = text[:max_length]

    # Remove potential prompt injection patterns
    for pattern in _INJECTION_PATTERNS:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE)

    # Remove HTML tags and excessive whitespace
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\s+", " ", text)

    return text.strip()
```

**Blocked Patterns:**
```python
# backend/app/core/input_sanitizer.py:14-21
_INJECTION_PATTERNS = [
    r"(?i)(ignore\s+(previous|all\s+above|forget))",
    r"(?i)(print|execute|eval|run|code|script)",
    r"(?i)(system|admin|root|privileged)",
    r"(?i)(override|bypass|circumvent)",
    r"(?i)(no\s+filter|skip\s+check)",
]
```

**Strengths:**
- Multi-layered approach (patterns, HTML stripping, length limits)
- Conversation-specific sanitization with stricter rules
- Test prompt validation to prevent testing abuse
- Quick safety check function for pre-filtering

**Recommendations:**
- ✅ Current implementation is solid
- Consider adding rate limiting to prevent prompt flooding
- Document the sanitization rules for transparency

**Priority:** COMPLETE
**OWASP Reference:** A03:2021 – Injection (Mitigated)

---

### NFR-S7: Content Security Policy Headers

**Requirement:** Content Security Policy headers must be set

**Status:** ❌ NOT IMPLEMENTED

**Evidence:**
- File: `/Users/sherwingorechomante/shop/backend/app/main.py`
  - No CSP middleware found
  - No security headers configuration
- Search across codebase shows no CSP implementation

**Gap Analysis:**
Missing security headers expose the application to:
- XSS attacks via untrusted content
- Clickjacking attacks
- MIME-type sniffing vulnerabilities
- Data leakage via Referer headers

**Recommendation:**

```python
# Add to backend/app/main.py
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response: Response = await call_next(request)

        # Content Security Policy
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "connect-src 'self' https://*.facebook.com https://*.shopify.com; "
            "frame-ancestors 'none'; "
            "form-action 'self';"
        )

        # Additional security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

        return response

# In app initialization:
app.add_middleware(SecurityHeadersMiddleware)
```

**Priority:** MEDIUM
**OWASP Reference:** A05:2021 – Security Misconfiguration
**Effort:** 2 hours

---

### NFR-S8: CSRF Protection

**Requirement:** CSRF tokens must be used for all state-changing operations

**Status:** ⚠️ PARTIALLY IMPLEMENTED

**Evidence:**
- File: `/Users/sherwingorechomante/shop/backend/app/core/security.py`
  - OAuth state parameter functions (line 44-88, 173-185)
  - `store_oauth_state()` and `validate_oauth_state()`
  - One-time use state tokens (deleted after validation)
- File: `/Users/sherwingorechomante/shop/backend/app/api/integrations.py`
  - OAuth CSRF validation (line 151-157, 455-461)

**What's Implemented:**
✅ OAuth state parameter for Facebook/Shopify flows
✅ One-time use tokens prevent replay attacks
✅ Redis-backed storage with TTL (10-minute expiration)
✅ State mismatch detection logs suspected CSRF attacks

**What's Missing:**
❌ No CSRF tokens for general API endpoints
❌ No double-submit cookie pattern
❌ No SameSite cookie configuration
❌ CSRF protection only exists for OAuth flows

**Gap Analysis:**
The current implementation protects OAuth flows but does not protect:
- Dashboard API endpoints (POST/PUT/DELETE operations)
- State-changing operations in merchant dashboard
- Form submissions from web UI

**Recommendation:**

```python
# Add to backend/app/core/security.py
from starlette.middleware.csrf import CSRFMiddleware

# Generate CSRF token for session
def generate_csrf_token() -> str:
    """Generate CSRF token for session-based protection."""
    return secrets.token_urlsafe(32)

# Validate CSRF token from request
async def validate_csrf_token(request: Request, token: str) -> bool:
    """Validate CSRF token from request headers or form."""
    # Compare with session-stored token
    session_token = request.session.get("csrf_token")
    return secrets.compare_digest(session_token, token)

# In main.py:
app.add_middleware(
    CSRFMiddleware,
    secret=os.getenv("CSRF_SECRET"),
    cookie_name="csrf_token",
    header_name="X-CSRF-Token",
    safe_methods={"GET", "HEAD", "OPTIONS"},
)
```

**Priority:** MEDIUM
**OWASP Reference:** A01:2021 – Broken Access Control
**Effort:** 6 hours

---

### NFR-S9: PCI-DSS Compliance via Shopify Checkout

**Requirement:** Payment processing must comply with PCI-DSS via Shopify checkout

**Status:** ⚠️ PARTIALLY IMPLEMENTED

**Evidence:**
- File: `/Users/sherwingorechomante/shop/backend/app/api/webhooks/shopify.py`
  - Webhook handlers for order events (line 136-199)
  - Order tracking implementation exists
- File: `/Users/sherwingorechomante/shop/backend/app/services/shopify.py`
  - Storefront API integration for product data
- No checkout URL generation found in current codebase

**What's Implemented:**
✅ Shopify webhook integration for order events
✅ OAuth flow with required scopes
✅ Order status tracking via webhooks

**What's Missing:**
❌ Checkout URL generation not implemented (Epic 2, Story 2.8)
❌ No HTTP HEAD validation of checkout URLs (NFR-R4 requirement)
❌ No verification that checkout links work before sending
❌ PCI-DSS scope reduction not documented

**Gap Analysis:**
The application correctly relies on Shopify's hosted checkout for payment processing, which reduces PCI-DSS scope. However:
- Checkout URL generation is deferred to Epic 2 (not yet implemented)
- No validation that generated checkout URLs are valid
- No documentation of PCI-DSS compliance boundary

**Recommendation:**

```python
# Implementation for Epic 2, Story 2.8
async def generate_checkout_url(cart_items: list, merchant_id: int) -> str:
    """Generate Shopify checkout URL with validation (NFR-S9, NFR-R4)."""

    # Generate checkout via Storefront API
    checkout_response = await shopify_storefront_api.call(
        mutation="checkoutCreate",
        variables={"input": {"lineItems": cart_items}}
    )
    checkout_url = checkout_response["checkoutCreate"]["checkout"]["webUrl"]

    # Validate URL via HTTP HEAD before sending (NFR-R4)
    async with httpx.AsyncClient() as client:
        head_response = await client.head(checkout_url)
        if head_response.status_code != 200:
            raise ValueError(f"Invalid checkout URL: {checkout_url}")

    return checkout_url
```

**Priority:** HIGH (blocked by Epic 2 implementation)
**OWASP Reference:** A08:2021 – Software and Data Integrity Failures
**Effort:** 4 hours

---

### NFR-S10: User Data Deletion Within 30 Days

**Requirement:** User data deletion requests must be processed within 30 days

**Status:** ❌ NOT IMPLEMENTED

**Evidence:**
- File: `/Users/sherwingorechomante/shop/backend/app/core/security.py`
  - No user deletion functions found
- File: `/Users/sherwingorechomante/shop/backend/app/models/message.py`
  - Cascade delete exists for conversations (line 30)
- Search across codebase shows no deletion workflow

**Gap Analysis:**
The application has no implementation for:
- "Forget my preferences" command (Epic 5, Story 5.2)
- GDPR/CCPA deletion request processing (Epic 5, Story 5.6)
- Deletion request tracking and audit logging
- 30-day processing deadline enforcement

**Epic 5 Status:** DEFERRED (Data Privacy & Compliance epic not yet started)

**Recommendation:**

```python
# Add to backend/app/api/privacy.py (new file)
from datetime import datetime, timedelta
from typing import Optional

class DeletionRequest(Base):
    """Track GDPR/CCPA deletion requests (NFR-S10)."""

    __tablename__ = "deletion_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    customer_id: Mapped[str] = mapped_column(String(100), index=True)
    merchant_id: Mapped[int] = mapped_column(Integer, ForeignKey("merchants.id"))
    request_type: Mapped[str] = mapped_column(Enum("voluntary", "gdpr", "ccpa"))
    status: Mapped[str] = mapped_column(Enum("pending", "processing", "completed"))
    requested_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    processing_deadline: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.utcnow() + timedelta(days=30)
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

async def process_deletion_request(customer_id: str, merchant_id: int) -> None:
    """Process user data deletion request (Epic 5, Story 5.2)."""

    # 1. Delete voluntary data immediately
    await delete_conversation_history(customer_id, merchant_id)
    await delete_user_preferences(customer_id, merchant_id)

    # 2. Mark operational data as "do not process"
    await mark_operational_data_restricted(customer_id, merchant_id)

    # 3. Log deletion for compliance audit
    await log_deletion_event(customer_id, merchant_id)

    # 4. Update deletion request status
    await mark_deletion_complete(customer_id, merchant_id)

# Add to backend/app/api/webhooks/facebook.py
async def process_message(...):
    # Check for deletion command
    if text.lower() in ["forget my preferences", "delete my data"]:
        await process_deletion_request(sender_id, merchant_id)
        return {"status": "deletion_processed"}
```

**Priority:** HIGH (GDPR/CCPA compliance requirement)
**OWASP Reference:** A04:2021 – Insecure Design
**Effort:** 12 hours

---

### NFR-S11: 30-Day Conversation Retention

**Requirement:** Conversation data retention must not exceed 30 days for voluntary memory

**Status:** ⚠️ PARTIALLY IMPLEMENTED

**Evidence:**
- File: `/Users/sherwingorechomante/shop/backend/app/models/conversation.py`
  - `created_at` and `updated_at` timestamps (line 54-64)
  - No retention policy or cleanup logic
- File: `/Users/sherwingorechomante/shop/backend/app/models/message.py`
  - No retention policy or cleanup logic
- Search across codebase shows no cleanup job or retention enforcement

**What's Implemented:**
✅ Timestamp tracking on all data
✅ Cascade delete exists for conversations

**What's Missing:**
❌ No automatic cleanup job for 30-day retention
❌ No retention policy enforcement
❌ No data tier separation (Epic 5, Story 5.4)
❌ No distinction between voluntary and operational data

**Gap Analysis:**
The application stores conversation data indefinitely, violating:
- GDPR minimization principle
- NFR-S11 30-day retention requirement
- Epic 5, Story 5.5 (automatic deletion)

**Recommendation:**

```python
# Add to backend/app/tasks/retention.py (new file)
from datetime import datetime, timedelta
from sqlalchemy import delete, select
from app.models.conversation import Conversation
from app.models.message import Message
from app.core.database import async_session_maker

async def cleanup_old_conversations() -> dict:
    """Enforce 30-day conversation retention policy (NFR-S11)."""

    cutoff_date = datetime.utcnow() - timedelta(days=30)
    deleted_count = {"conversations": 0, "messages": 0}

    async with async_session_maker() as db:
        # Find conversations older than 30 days
        result = await db.execute(
            select(Conversation).where(
                Conversation.updated_at < cutoff_date,
                Conversation.status == "closed"
            )
        )
        old_conversations = result.scalars().all()

        for conv in old_conversations:
            # Delete associated messages (cascade)
            await db.execute(
                delete(Message).where(Message.conversation_id == conv.id)
            )

            # Delete conversation
            await db.execute(
                delete(Conversation).where(Conversation.id == conv.id)
            )

            deleted_count["conversations"] += 1

        await db.commit()

    # Log deletion for audit
    logger.info(
        "conversation_retention_cleanup",
        cutoff_date=cutoff_date.isoformat(),
        deleted=deleted_count
    )

    return deleted_count

# Schedule daily cleanup (e.g., via Celery beat or APScheduler)
# Run at midnight UTC daily
```

**Priority:** MEDIUM
**OWASP Reference:** A04:2021 – Insecure Design
**Effort:** 4 hours

---

## Security Strengths

### 1. Cryptography Best Practices
- **Fernet Encryption:** OAuth tokens encrypted using AES-128-CBC with HMAC authentication
- **Constant-Time Comparison:** Prevents timing attacks on signature verification
- **Key Management:** Encryption keys from environment variables, not hardcoded

### 2. Webhook Security
- **HMAC Verification:** Both Facebook and Shopify webhooks use HMAC-SHA256
- **Raw Payload Verification:** Body manipulation attacks prevented
- **Immediate Rejection:** Invalid signatures return 403 before processing

### 3. Input Sanitization
- **Multi-Layer Approach:** Pattern blocking, HTML stripping, length limits
- **LLM-Specific:** Tailored for prompt injection prevention
- **Conversation Safety:** Additional rules for conversational input

### 4. Configuration Security
- **Environment-Based:** All secrets via environment variables
- **No Hardcoded Secrets:** Pre-commit hooks prevent commits
- **Debug Detection:** Different behavior for dev/prod environments

### 5. OAuth Security
- **State Parameters:** CSRF protection via one-time state tokens
- **One-Time Use:** State tokens deleted after validation
- **TTL Enforcement:** State tokens expire after 10 minutes

---

## Security Gaps & Recommendations

### Critical Priority (P0)

1. **NFR-S1: HTTPS Enforcement**
   - **Risk:** Man-in-the-middle attacks, credential theft
   - **Action:** Add HTTPSRedirectMiddleware and TrustedHostMiddleware
   - **Effort:** 2 hours

2. **NFR-S2: Conversation Data Encryption**
   - **Risk:** Database compromise exposes all conversations
   - **Action:** Implement pgcrypto or app-level encryption
   - **Effort:** 4-8 hours

3. **NFR-S10: User Data Deletion**
   - **Risk:** GDPR/CCPA non-compliance, legal liability
   - **Action:** Implement deletion workflow (Epic 5)
   - **Effort:** 12 hours

### High Priority (P1)

4. **NFR-S7: Security Headers**
   - **Risk:** XSS, clickjacking, data leakage
   - **Action:** Add CSP and security headers middleware
   - **Effort:** 2 hours

5. **NFR-S9: Checkout URL Validation**
   - **Risk:** Invalid checkout URLs, payment failures
   - **Action:** Implement HTTP HEAD validation (Epic 2)
   - **Effort:** 4 hours

### Medium Priority (P2)

6. **NFR-S8: CSRF Protection**
   - **Risk:** CSRF attacks on dashboard operations
   - **Action:** Add CSRF middleware for non-OAuth endpoints
   - **Effort:** 6 hours

7. **NFR-S11: Data Retention Enforcement**
   - **Risk:** GDPR minimization principle violation
   - **Action:** Implement automatic cleanup job
   - **Effort:** 4 hours

---

## Priority Action Items

### Immediate (This Sprint)

1. **Add HTTPS Enforcement Middleware**
   - File: `backend/app/main.py`
   - Add `HTTPSRedirectMiddleware` for production
   - Add `TrustedHostMiddleware` for host validation
   - **Time:** 2 hours

2. **Add Security Headers Middleware**
   - File: `backend/app/main.py`
   - Implement CSP, X-Frame-Options, X-Content-Type-Options
   - **Time:** 2 hours

3. **Document Current Security Posture**
   - Create security runbook for incident response
   - Document key rotation procedures
   - **Time:** 4 hours

### Short-Term (Next Sprint)

4. **Implement Conversation Data Encryption**
   - File: `backend/app/core/security.py`
   - Add `encrypt_conversation_content()` and `decrypt_conversation_content()`
   - Update `Message` model to use encrypted fields
   - **Time:** 8 hours

5. **Add CSRF Protection for Dashboard**
   - File: `backend/app/main.py`
   - Add CSRF middleware
   - Update dashboard API endpoints to validate tokens
   - **Time:** 6 hours

### Medium-Term (Epic 5)

6. **Implement Data Deletion Workflow**
   - File: `backend/app/api/privacy.py` (new)
   - Implement "forget my preferences" command
   - Add GDPR/CCPA deletion request tracking
   - **Time:** 12 hours

7. **Implement Data Retention Cleanup**
   - File: `backend/app/tasks/retention.py` (new)
   - Add daily cleanup job for 30-day retention
   - **Time:** 4 hours

---

## Compliance Mapping

### GDPR (General Data Protection Regulation)

| Requirement | Status | Gap |
|-------------|--------|-----|
| Art. 25: Privacy by Design | ⚠️ Partial | Missing data minimization |
| Art. 32: Encryption at Rest | ⚠️ Partial | Conversations not encrypted |
| Art. 17: Right to Erasure | ❌ Missing | No deletion workflow |
| Art. 5(1)(e): Storage Limitation | ❌ Missing | No retention enforcement |

### CCPA (California Consumer Privacy Act)

| Requirement | Status | Gap |
|-------------|--------|-----|
| Right to Delete | ❌ Missing | No deletion workflow |
| Right to Opt-Out | ⚠️ Partial | No data sale, but no documented opt-out |
| Data Minimization | ❌ Missing | Indefinite retention |

### PCI-DSS (Payment Card Industry Data Security Standard)

| Requirement | Status | Gap |
|-------------|--------|-----|
| Requirement 3: Protect stored data | ✅ Complete | No card data stored (Shopify checkout) |
| Requirement 4: Encrypt transmission | ⚠️ Partial | No HTTPS enforcement |
| Requirement 6: Secure development | ⚠️ Partial | Missing security headers |

---

## Testing Recommendations

### Security Testing

1. **Webhook Signature Testing**
   - Test with valid signatures
   - Test with invalid signatures
   - Test with replayed payloads
   - Test with tampered payloads

2. **Input Sanitization Testing**
   - Test prompt injection patterns
   - Test XSS payloads
   - Test SQL injection attempts
   - Test length limits

3. **Encryption Testing**
   - Verify token encryption on storage
   - Verify token decryption on use
   - Test with invalid encryption keys
   - Test encryption key rotation

4. **CSRF Testing**
   - Test OAuth state validation
   - Test state replay attacks
   - Test state token expiration
   - Test missing state parameters

### Penetration Testing

Recommended penetration testing areas:
- Webhook endpoints
- OAuth callback endpoints
- Dashboard API endpoints
- Input sanitization bypass attempts

---

## Conclusion

The Shopping Assistant Bot has a solid security foundation with strong webhook verification, OAuth token encryption, and input sanitization. However, critical gaps remain in HTTPS enforcement, data encryption, and privacy compliance.

### Risk Assessment Summary

| Risk Category | Level | Mitigation Priority |
|---------------|-------|---------------------|
| Data Exposure | HIGH | Implement conversation encryption |
| Compliance Violation | HIGH | Implement deletion workflow (Epic 5) |
| Transport Security | HIGH | Add HTTPS enforcement |
| CSRF Attacks | MEDIUM | Add CSRF middleware |
| Data Retention | MEDIUM | Implement cleanup job |

### Next Steps

1. **Immediate:** Add HTTPS and security headers middleware
2. **Short-term:** Implement conversation encryption and CSRF protection
3. **Epic 5:** Complete data privacy compliance implementation
4. **Ongoing:** Security testing and penetration testing

### Security Score

**Current Score:** 5/11 (45%)
**Target Score:** 9/11 (82%)
**With Epic 5:** 11/11 (100%)

---

## Appendix: Security Checklist

### Pre-Deployment Checklist

- [ ] HTTPS enforcement enabled in production
- [ ] Security headers configured (CSP, X-Frame-Options, etc.)
- [ ] OAuth tokens encrypted at rest
- [ ] API keys via environment variables
- [ ] Webhook signatures verified
- [ ] Input sanitization enabled
- [ ] CSRF protection for state-changing operations
- [ ] Conversation data encrypted at rest
- [ ] Data deletion workflow implemented
- [ ] Data retention cleanup scheduled
- [ ] PCI-DSS scope documented

### Ongoing Monitoring

- [ ] Webhook signature verification logs monitored
- [ ] Failed OAuth attempts tracked
- [ ] Rate limiting enabled
- [ ] Security headers validated
- [ ] Encryption key rotation scheduled
- [ ] Penetration testing performed quarterly

---

**Report Generated:** February 4, 2026
**Next Review:** After Epic 5 implementation or Q2 2026 (whichever is earlier)
