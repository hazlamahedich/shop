# Story 12-5: Dev Key Production Check

**Epic**: 12 - Security Hardening
**Priority**: P1 (High)
**Status**: backlog
**Estimate**: 3 hours
**Dependencies**: None

## Problem Statement

Development default keys exist in `backend/app/core/config.py` with warnings but no hard block. Production deployments could accidentally use insecure defaults.

## Acceptance Criteria

- [ ] Production environment detection implemented
- [ ] Application refuses to start with dev keys in production
- [ ] Clear error messages for missing required secrets
- [ ] Startup validation for all security-critical config
- [ ] Documentation for required production secrets
- [ ] CI check for hardcoded secrets

## Technical Design

### Production Validation

```python
# backend/app/core/config.py
from enum import Enum

class Environment(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"

class Settings(BaseSettings):
    ENVIRONMENT: Environment = Environment.DEVELOPMENT
    
    def validate_production(self) -> None:
        if self.ENVIRONMENT == Environment.PRODUCTION:
            errors = []
            
            if not self.SECRET_KEY or self.SECRET_KEY.startswith("dev-"):
                errors.append("SECRET_KEY must be set in production")
            
            if not self.DATABASE_URL:
                errors.append("DATABASE_URL must be set in production")
            
            if not self.JWT_SECRET_KEY or self.JWT_SECRET_KEY.startswith("dev-"):
                errors.append("JWT_SECRET_KEY must be set in production")
            
            if errors:
                raise RuntimeError(
                    "Production configuration errors:\n" + 
                    "\n".join(f"  - {e}" for e in errors)
                )

# At application startup
settings.validate_production()
```

### Required Production Secrets

```bash
# .env.production.example
ENVIRONMENT=production
SECRET_KEY=<generate with: openssl rand -hex 32>
JWT_SECRET_KEY=<generate with: openssl rand -hex 32>
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db
CONVERSATION_ENCRYPTION_KEY=<generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())">
REDIS_URL=redis://localhost:6379/0
```

## Testing Strategy

1. Test app starts with dev keys in development
2. Test app refuses to start with dev keys in production
3. Test app starts with valid production config
4. Test CI detects hardcoded secrets

## Related Files

- `backend/app/core/config.py`
- `backend/app/main.py`
- `.env.production.example` (new)
- `.github/workflows/security.yml`
