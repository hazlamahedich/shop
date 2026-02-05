---
title: Implementation Challenges and Solutions - Epic 1
description: Technical challenges encountered and solutions implemented during Epic 1
author: Team Mantis B
date: 2026-02-04
---

# Implementation Challenges and Solutions - Epic 1

## Overview

This document captures the technical challenges encountered during Epic 1 implementation and the solutions that were developed. These challenges and their solutions provide valuable learning for future development.

## Table of Contents

1. [Database Challenges](#database-challenges)
2. [API Compatibility Issues](#api-compatibility-issues)
3. [Frontend State Management](#frontend-state-management)
4. [Testing Challenges](#testing-challenges)
5. [Configuration Issues](#configuration-issues)
6. [Security Implementation](#security-implementation)
7. [Lessons Learned](#lessons-learned)

---

## Database Challenges

### Challenge 1: SQLAlchemy Reserved Attribute Conflict

**Problem:** Using `metadata` as a column name conflicted with SQLAlchemy's built-in `metadata` attribute on the `Base` class.

**Error Encountered:**
```python
# This code fails
class Message(Base):
    __tablename__ = "messages"

    metadata = Column(JSONB, nullable=True)  # Error!

# Error: Can't replace attribute `metadata` (reserved by SQLAlchemy)
```

**Solution:**
Rename the column to `message_metadata` and update all references:

```python
# Fixed version
class Message(Base):
    __tablename__ = "messages"

    message_metadata = Column(JSONB, nullable=True)

# Also update all references:
# - backend/app/models/message.py
# - backend/app/services/facebook.py
# - backend/app/api/webhooks/facebook.py
```

**Files Modified:**
- `backend/app/models/message.py`
- `backend/app/services/facebook.py`
- `backend/app/api/webhooks/facebook.py`

---

### Challenge 2: Enum Standardization Across Database

**Problem:** Inconsistent enum handling between stories led to database inconsistencies.

**Initial Issue:**
```python
# Story 1.3 - String column
provider = Column(String, nullable=False)  # "ollama", "openai", etc.

# Story 1.5 - Different approach
provider = Column(String(50), nullable=False)

# Led to: typos, case inconsistencies, invalid values
```

**Solution:**
Create PostgreSQL ENUM types with proper governance:

```python
# backend/app/models/llm_configuration.py
from sqlalchemy import Column, Integer, Enum as SQLEnum

class LLMConfiguration(Base):
    """LLM configuration with standardized enum."""

    __tablename__ = "llm_configurations"

    # PostgreSQL ENUM type (created via migration)
    provider = Column(
        SQLEnum(
            "ollama",
            "openai",
            "anthropic",
            "gemini",
            "glm",
            name="llm_provider",
            create_constraint=True,
            metadata={"schema": "public"}
        ),
        nullable=False,
        default="ollama"
    )

# Migration file to create ENUM
# alembic/versions/001_create_llm_provider_enum.py
from alembic import op
from sqlalchemy.dialects import postgresql

def upgrade():
    llm_provider_enum = postgresql.ENUM(
        "ollama", "openai", "anthropic", "gemini", "glm",
        name="llm_provider",
        create_type=True
    )
    llm_provider_enum.create(op.get_bind())

def downgrade():
    postgresql.ENUM(name="llm_provider").drop(op.get_bind())
```

---

## API Compatibility Issues

### Challenge 3: httpx 0.28+ API Changes

**Problem:** httpx 0.28 changed the API for `AsyncClient` transport initialization, breaking tests.

**Old API (0.27):**
```python
# This stopped working
self._async_client = httpx.AsyncClient(
    app=app,
    base_url="http://test"
)
```

**New API (0.28+):**
```python
# Use ASGITransport instead
from httpx import ASGITransport

self._async_client = httpx.AsyncClient(
    transport=ASGITransport(app=app),
    base_url="http://test"
)
```

**Implementation Pattern:**
```python
# backend/app/services/llm/ollama_service.py
from app.core.config import settings

class OllamaService(BaseLLMService):
    @property
    def async_client(self) -> httpx.AsyncClient:
        """Get or create async HTTP client with testing support."""
        if self._async_client is None:
            if settings.is_testing:
                from httpx import ASGITransport
                self._async_client = httpx.AsyncClient(
                    transport=ASGITransport(),
                    base_url="http://test"
                )
            else:
                self._async_client = httpx.AsyncClient(
                    base_url=self.ollama_url
                )
        return self._async_client
```

---

## Frontend State Management

### Challenge 4: localStorage Persistence in Pre-Authentication State

**Problem:** No merchant account exists before deployment, but we need to persist prerequisite checklist state.

**Initial Challenge:**
```typescript
// Can't use database - no merchant_id yet
// Can't use session - not authenticated
// Need persistence across page refreshes
```

**Solution:**
Use localStorage with specific key pattern, then migrate to PostgreSQL after merchant account creation.

```typescript
// frontend/src/stores/onboardingStore.ts
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

const LOCAL_STORAGE_KEY = 'shop_onboarding_prerequisites';

interface PrerequisitesState {
  facebook_account: boolean;
  shopify_store: boolean;
  ollama_installed: boolean;
  deployment_platform: boolean;
  updatePrerequisite: (key: string, value: boolean) => void;
  migrateToServer: () => Promise<void>;
}

export const useOnboardingStore = create<PrerequisitesState>()(
  persist(
    (set, get) => ({
      facebook_account: false,
      shopify_store: false,
      ollama_installed: false,
      deployment_platform: false,

      updatePrerequisite: (key, value) => {
        set({ [key]: value });
      },

      migrateToServer: async () => {
        // After deployment/merchant creation, migrate to database
        const state = get();

        await fetch('/api/onboarding/prerequisites/sync', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(state)
        });

        // Clear localStorage after successful sync
        localStorage.removeItem(LOCAL_STORAGE_KEY);
      }
    }),
    {
      name: LOCAL_STORAGE_KEY,
      version: 1
    }
  )
);
```

**Backend Sync Endpoint:**
```python
# backend/app/api/onboarding.py
@router.post("/prerequisites/sync")
async def sync_prerequisites(
    data: PrerequisiteSyncRequest,
    merchant_id: int,
    db: AsyncSession
):
    """Sync localStorage state to database after deployment."""
    # Find or create merchant prerequisites
    prereq = await db.find(
        Prerequisite,
        Prerequisite.merchant_id == merchant_id
    )

    if not prereq:
        prereq = Prerequisite(merchant_id=merchant_id)
        db.add(prereq)

    # Update from localStorage data
    prereq.facebook_account = data.facebook_account
    prereq.shopify_store = data.shopify_store
    prereq.ollama_installed = data.ollama_installed
    prereq.deployment_platform = data.deployment_platform

    await db.commit()

    return {"status": "synced"}
```

---

## Testing Challenges

### Challenge 5: API Credit Burn During Tests

**Problem:** Tests were calling actual LLM APIs, burning credits and causing slow test runs.

**Impact:**
- Tests costing money per run
- Slow test execution (waiting for API responses)
- Flaky tests due to network issues

**Solution:**
Implement `IS_TESTING` flag with ASGITransport for mocking.

```python
# backend/app/core/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings with testing flag."""

    is_testing: bool = False  # CRITICAL for preventing API calls

    class Config:
        env_file = ".env"

settings = Settings()

# backend/tests/conftest.py
@pytest.fixture(scope="session", autouse=True)
def set_testing_mode():
    """Set IS_TESTING flag for all tests."""
    os.environ["IS_TESTING"] = "true"
    yield
    os.environ["IS_TESTING"] = "false"
```

**Service Implementation:**
```python
# backend/app/services/llm/ollama_service.py
from app.core.config import settings

class OllamaService(BaseLLMService):
    @property
    def async_client(self) -> httpx.AsyncClient:
        """Get or create async HTTP client.

        During testing, use ASGITransport to prevent actual HTTP calls.
        """
        if self._async_client is None:
            if settings.is_testing:
                from httpx import ASGITransport
                self._async_client = httpx.AsyncClient(
                    transport=ASGITransport(),
                    base_url="http://test"
                )
            else:
                self._async_client = httpx.AsyncClient(
                    base_url=self.ollama_url
                )
        return self._async_client
```

**Result:**
- Zero API costs during testing
- Fast test execution
- Deterministic test results

---

## Configuration Issues

### Challenge 6: Environment Variable Management

**Problem:** Managing secrets and configuration across environments (dev, test, prod).

**Initial Approach:**
- Hardcoded values in code
- Secrets committed to repository
- Inconsistent configuration between environments

**Solution:**
Structured environment variable management with validation.

```python
# backend/app/core/config.py
from pydantic_settings import BaseSettings
from pydantic import Field, validator

class Settings(BaseSettings):
    """Application settings with validation."""

    # Required settings
    encryption_key: str = Field(..., env="ENCRYPTION_KEY")
    database_url: str = Field(..., env="DATABASE_URL")
    redis_url: str = Field(..., env="REDIS_URL")

    # Facebook (optional for local dev)
    facebook_app_id: str | None = Field(None, env="FACEBOOK_APP_ID")
    facebook_app_secret: str | None = Field(None, env="FACEBOOK_APP_SECRET")

    # Shopify (optional for local dev)
    shopify_api_key: str | None = Field(None, env="SHOPIFY_API_KEY")
    shopify_api_secret: str | None = Field(None, env="SHOPIFY_API_SECRET")

    # Testing
    is_testing: bool = Field(False, env="IS_TESTING")
    debug: bool = Field(False, env="DEBUG")

    @validator("encryption_key")
    def validate_encryption_key(cls, v):
        """Validate encryption key is proper Fernet key."""
        if v:
            try:
                from cryptography.fernet import Fernet
                Fernet(v.encode())
            except Exception:
                raise ValueError("Invalid ENCRYPTION_KEY format")
        return v

    @validator("database_url")
    def validate_database_url(cls, v):
        """Validate database URL format."""
        if v and not v.startswith(("postgresql://", "postgresql+asyncpg://")):
            raise ValueError("DATABASE_URL must use postgresql protocol")
        return v

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

settings = Settings()
```

**Environment File Template:**
```bash
# .env.example - Template for environment configuration

# REQUIRED - Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/db
REDIS_URL=redis://localhost:6379/0

# REQUIRED - Security (generate with: Fernet.generate_key())
ENCRYPTION_KEY=<your-fernet-key-base64>

# OPTIONAL - Facebook (leave blank if not using)
FACEBOOK_APP_ID=
FACEBOOK_APP_SECRET=
FACEBOOK_REDIRECT_URI=https://your-domain.com/api/integrations/facebook/callback
FACEBOOK_WEBHOOK_VERIFY_TOKEN=<random-32-char-string>

# OPTIONAL - Shopify (leave blank if not using)
SHOPIFY_API_KEY=
SHOPIFY_API_SECRET=
SHOPIFY_REDIRECT_URI=https://your-domain.com/api/integrations/shopify/callback

# OPTIONAL - LLM Configuration
DEFAULT_LLM_PROVIDER=ollama
OLLAMA_URL=http://localhost:11434
OPENAI_API_KEY=
ANTHROPIC_API_KEY=

# DEVELOPMENT/TESTING
IS_TESTING=false
DEBUG=false
```

---

## Security Implementation

### Challenge 7: Webhook Signature Verification Timing Attacks

**Problem:** String comparison timing could leak information about webhook signatures.

**Vulnerable Code:**
```python
# DON'T DO THIS - vulnerable to timing attacks
if computed_hash == expected_hash:
    return True
```

**Solution:**
Use constant-time comparison from `secrets` module.

```python
from secrets import compare_digest

def verify_webhook_signature(
    raw_payload: bytes,
    signature: str,
    app_secret: str
) -> bool:
    """Verify webhook signature with constant-time comparison."""
    if not signature or not signature.startswith("sha256="):
        return False

    expected_hash = signature[7:]
    computed_hash = hmac.new(
        app_secret.encode(),
        raw_payload,
        hashlib.sha256
    ).hexdigest()

    # Constant-time comparison prevents timing attacks
    return compare_digest(computed_hash, expected_hash)
```

**Why This Matters:**
- Regular string comparison (`==`) short-circuits on first mismatch
- Attacker can measure response time to guess correct hash
- Constant-time comparison always takes same time regardless of match position

---

## Lessons Learned

### For Developers

1. **Always check reserved names:** Before naming database columns or attributes, check framework reserved names
2. **Use ENUMs for fixed values:** PostgreSQL ENUMs prevent typos and ensure consistency
3. **Version compatibility:** Pin dependency versions and document breaking changes
4. **Test with IS_TESTING flag:** Prevent API calls and external dependencies during tests
5. **Constant-time security:** Use `compare_digest()` for security-sensitive comparisons

### For Architects

1. **Plan for state migration:** Design flows that work before and after authentication
2. **Abstract external dependencies:** Use patterns like BaseLLMService for easy provider switching
3. **Configuration validation:** Validate environment variables at startup, not at runtime
4. **Testing first approach:** Design systems with testability in mind from the start

### For Project Management

1. **Track technical debt:** Document challenges and solutions for future reference
2. **Share learnings:** Create documentation like this for team knowledge
3. **Plan for upgrades:** Schedule time for dependency updates and breaking changes
4. **Invest in tooling:** Good development tools prevent these issues from becoming blockers

---

## Challenge-Solution Summary

| Challenge | Solution | Impact |
|-----------|----------|--------|
| SQLAlchemy reserved names | Use `message_metadata` instead of `metadata` | Prevents framework conflicts |
| Enum inconsistency | PostgreSQL ENUM types with constraints | Data consistency |
| httpx 0.28+ changes | Use ASGITransport for testing | Tests work with latest httpx |
| Pre-auth state | localStorage with server migration | Seamless onboarding flow |
| API credit burn | IS_TESTING flag with mocking | Zero-cost testing |
| Config management | Pydantic Settings with validation | Fail-fast on bad config |
| Timing attacks | `compare_digest()` for security | Prevents information leakage |

---

*Document Version: 1.0*
*Last Updated: 2026-02-04*
*Maintainer: Team Mantis B*
