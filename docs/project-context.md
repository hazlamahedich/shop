---
project_name: "shop"
user_name: "team mantis b"
date: "2026-02-03"
sections_completed: ["discovery", "party-mode-review"]
existing_patterns_found: 27
party_mode_enhancements: 7
---

# Project Context for AI Agents

_This file contains critical rules and patterns that AI agents must follow when implementing code in this project. Focus on unobvious details that agents might otherwise miss._

---

## Technology Stack & Versions

### Backend (Python 3.11+)

```
FastAPI: 0.104.0+
SQLAlchemy: 2.0.23+ (async)
Pydantic: 2.5.0+
asyncpg: 0.29.0+ (PostgreSQL driver)
Alembic: 1.13.0+ (migrations)
httpx: 0.25.0+ (async HTTP)
python-jose: 3.3.0+ (JWT)
pytest: 8.0.0+
schemathesis: 3.20.0+ (contract testing)
```

### Frontend (TypeScript 5.3+)

```
React: 18.2.0
Vite: 5.0.0+
Zustand: 4.4.0+
Vitest: 1.0.0+
```

### Tooling

```
Python: Ruff, Black, mypy, pre-commit
TypeScript: ESLint, Prettier
```

---

## Critical Implementation Rules

### LLM Integration (CRITICAL)

**`IS_TESTING` Environment Variable**

- ALL tests MUST set `IS_TESTING=true` (enforced via conftest.py)
- When `IS_TESTING=true`, services use MockLLMProvider instead of real APIs
- This prevents API credit burn during development/testing
- Pattern:

  ```python
  from backend.app.core.config import is_testing
  from backend.tests.fixtures.mock_llm import MockLLMProvider

  def get_llm_service():
      if is_testing():
          return MockLLMProvider(provider="test")
      return OpenAIService()
  ```

**Multi-Provider LLM Support**

- Providers: ollama (local/default), openai, anthropic, gemini, glm-4.7
- Use thin custom abstraction over direct API calls (NOT LangChain)
- Zero dependencies beyond `httpx` for LLM calls
- Every LLM provider MUST have test double in `tests/fixtures/mock_llm.py`

### Error Handling & ErrorCode Registry

**ErrorCode Governance**

- ErrorCodes use ranges 1000-9999 with team ownership
- Check owner team before adding new code in range
- Document in `docs/error-code-governance.md`
- DELETED CODES ARE NEVER REUSED (maintains log stability)
- **Team ownership must be documented before adding codes**

**Ranges and Team Owners:**

- 1000-1999: General/System → **core team** (platform infrastructure)
- 2000-2999: Auth/Security → **security team** (authentication, webhooks, tokens)
- 3000-3999: LLM Provider → **llm team** (AI integration, prompt handling)
- 4000-4999: Shopify Integration → **shopify team** (Storefront/Admin API, products, orders)
- 5000-5999: Facebook/Messenger → **facebook team** (webhooks, messaging, page management)
- 6000-6999: Cart/Checkout → **checkout team** (cart management, checkout URLs)
- 7000-7999: Conversation/Session → **conversation team** (chat sessions, context, user state)

**Pattern:**

```python
class APIError(Exception):
    def __init__(self, code: ErrorCode, message: str, details: Optional[dict] = None):
        self.code = code
        self.message = message
        self.details = details or {}

# Usage
raise APIError(ErrorCode.LLM_RATE_LIMIT, "Too many requests", {"retry_after": 60})
```

### Testing Structure

**Test Pyramid: 70% Unit / 20% Integration / 10% E2E**

**Co-located Unit Tests:**

- Place `test_<module>.py` next to `<module>.py` in same directory
- Pre-commit hook enforces this pattern
- Example: `backend/app/services/llm/openai_service.py` → `test_openai_service.py`

**Separate Test Suites:**

```
backend/tests/
├── integration/  # Component interaction tests
└── contract/     # API contract tests (schemathesis)
```

**Contract Testing:**

- ALL API endpoints tested against OpenAPI schema via Schemathesis
- Schema auto-generated from FastAPI: `python scripts/hooks/openapi_gen.py`
- Run: `pytest tests/contract/`

### Naming Conventions

**Database → API Conversion:**

- Database: `snake_case` (PostgreSQL convention)
- API: `camelCase` (JavaScript convention)
- Conversion via Pydantic `alias_generator`:
  ```python
  class ProductSchema(BaseModel):
      display_name: str = Field(alias="displayName")  # API side
      # Or use ConfigDict
      class Config:
          alias_generator = to_camel
          populate_by_name = True
  ```

**File Naming:**

- Python modules: `snake_case.py`
- Test files: `test_<module>.py`
- React components: `PascalCase.tsx`
- Test files: `<Component>.test.tsx`

### API Response Format

**Minimal Envelope Pattern:**

```python
{
    "data": {...},           # Response payload
    "meta": {
        "request_id": "uuid",
        "timestamp": "ISO-8601",
        "pagination": {...}   # If applicable
    }
}
```

**Error Response:**

```python
{
    "error_code": 3001,      # ErrorCode enum value
    "message": "Human readable",
    "details": {...}         # Optional field-specific errors
}
```

### Type Synchronization

**Python → TypeScript Auto-Generation:**

- OpenAPI schema generated from Pydantic models
- TypeScript types generated from OpenAPI
- Do NOT manually write TypeScript types for API responses
- Pre-commit hook auto-runs when schemas change
- Runtime validation via Zod on frontend

### Security Rules

**SECRET_KEY Requirement:**

- MUST be set in non-debug environments
- Raises ValueError if missing in production
- Generate: `python -c "import secrets; print(secrets.token_urlsafe(32))"`

**Webhook Verification:**

- Facebook: X-Hub-Signature validation
- Shopify: HMAC signature verification
- REQUIRED before processing any webhook payload

### Code Organization

**Backend Structure:**

```
backend/app/
├── core/          # Config, errors, security, database
├── models/        # SQLAlchemy ORM models
├── schemas/       # Pydantic request/response schemas
├── api/           # Route handlers (grouped by feature)
├── services/      # Business logic (LLM, Shopify, etc.)
└── main.py        # FastAPI app entry
```

**Frontend Structure:**

```
frontend/src/
├── components/    # Feature-based React components
├── stores/        # Zustand state stores
├── services/      # API client functions
├── types/         # Auto-generated TypeScript types
└── tests/         # Test setup and utilities
```

### Webhook Reliability

**Dead Letter Queue Pattern:**

- Redis lists as temporary queue (migrate to RabbitMQ/Kafka at scale)
- 3 retry attempts with exponential backoff
- Polling fallback: Every 5 minutes for orders <24 hours old
- NOT a replacement for webhooks - gap coverage only

### GDPR/CCPA Compliance

**Data Tiers:**

1. **Voluntary**: User-initiated (preferences, explicit opt-ins)
2. **Operational**: Required for service (order references, session data)
3. **Anonymized**: Aggregated analytics (cannot identify individuals)

**Retention Rules:**

- Voluntary memory: 30-day max, auto-deletion
- Operational data: Keep until account deletion
- Anonymized data: Indefinite retention

### Development Workflow

**Pre-commit Hooks:**

- Test colocation validation (fails if `module.py` lacks `test_module.py`)
- Type generation from OpenAPI (runs when schemas change)
- Black, Ruff, Flake8 formatting
- Security checks (bandit, detect-private-key)

**Linting Configuration:**

- Python: 100 char line length, double quotes
- TypeScript: 100 char line length, single quotes, semicolons

### Observability

**Structured Logging:**

- Use `structlog` with `request_id` correlation
- Log format includes: timestamp, level, request_id, message, context
- Do NOT use print() statements

### Async Patterns

**Database Operations:**

- All DB operations MUST be async (SQLAlchemy 2.0 async mode)
- Use `async_session()` from `backend.app.core.database`
- Pattern:
  ```python
  async def get_user(db: AsyncSession, user_id: int):
      result = await db.execute(select(User).where(User.id == user_id))
      return result.scalars().first()
  ```

**Async Function Signatures (CRITICAL):**

- EVERY async function MUST include type hints for all parameters and return
- Database functions MUST accept `db: AsyncSession` as first parameter
- Pattern: `async def function_name(db: AsyncSession, param: Type) -> ReturnType:`
- NEVER override `IS_TESTING` in individual tests - it's set via conftest.py autouse

### Import Path Conventions

**Python Imports:**

- Use absolute imports starting from `backend.app`
- Pattern: `from backend.app.core.config import settings`
- Pattern: `from backend.app.core.errors import APIError, ErrorCode`
- NEVER use relative imports for cross-module imports
- Within same module: `from .config import settings` is acceptable

### Error-Raising Decision Tree

**When to Raise Which Error:**

| Situation              | Error Type                                    | Example                                                                      |
| ---------------------- | --------------------------------------------- | ---------------------------------------------------------------------------- |
| Input validation fails | `ValidationError`                             | `raise ValidationError("Invalid email", fields={"email": "invalid format"})` |
| Auth/token issues      | `AuthenticationError`                         | `raise AuthenticationError("Invalid token")`                                 |
| Resource not found     | `NotFoundError`                               | `raise NotFoundError("User", user_id)`                                       |
| LLM provider issues    | `APIError(ErrorCode.LLM_PROVIDER_ERROR, ...)` | `raise APIError(ErrorCode.LLM_RATE_LIMIT, "...")`                            |
| Shopify API errors     | `APIError(ErrorCode.SHOPIFY_API_ERROR, ...)`  | `raise APIError(ErrorCode.PRODUCT_NOT_FOUND, "...")`                         |
| Generic/uncategorized  | `APIError(ErrorCode.UNKNOWN_ERROR, ...)`      | `raise APIError(ErrorCode.UNKNOWN_ERROR, "Unexpected condition")`            |

**Rule:** Use the most specific error type available. Domain errors from ErrorCode enum take precedence over generic errors.

### Test Fixture Patterns

**Fixture Inheritance (for new models):**
When adding new models, create corresponding test fixtures:

```python
# backend/tests/fixtures/factory.py
from backend.tests.fixtures.factory import BaseFactory

class CartFactory(BaseFactory):
    """Test fixture for Cart model."""
    model = Cart

    def __init__(self, **kwargs):
        defaults = {
            "session_id": "test-session",
            "items": [],
            "created_at": datetime.utcnow()
        }
        defaults.update(kwargs)
        super().__init__(**defaults)
```

**Async Test Patterns:**

- ALL async tests MUST use `@pytest.mark.asyncio` decorator
- Database tests MUST use `async with` for session management
- Pattern:
  ```python
  @pytest.mark.asyncio
  async def test_cart_creation(db_session):
      async with db_session as session:
          cart = CartFactory()
          result = await session.execute(select(Cart).where(Cart.id == cart.id))
          assert result.scalars().first() is not None
  ```

### Coverage and Quality Gates

**Coverage Requirements:**

- Minimum coverage: 80% (enforced via `backend/pyproject.toml:85`)
- Coverage below 80% blocks commits
- Run coverage: `pytest --cov=app --cov-report=html`

**Flakiness Protocol:**

- Flaky tests BLOCK story progress
- A test that sometimes fails is worse than no test
- When a test is flaky: fix it before proceeding with implementation
- Flakiness is critical technical debt - address immediately

### Process Agreements (Retrospective Action Items)

**Privacy-First Design Check (Epic 2 AI-1):**

- **Trigger**: Planning phase of every story
- **Requirement**: Explicitly check for data persistence, user consent, and PII handling
- **Action**: Add "Privacy & Compliance" section to Story Implementation Plan if applicable

**API Contract Verification (Epic 2 AI-2):**

- **Trigger**: Implementing webhook listeners or 3rd party integrations
- **Requirement**: Manually inspect REAL payloads before writing code (do not rely solely on docs)
- **Method**: Use `curl`, Postman, or `ngrok` to capture actual events
- **Goal**: Prevent "missing field" surprises (like missing PSID in Shopify webhooks)

**Proactive Refactoring (Epic 2 AI-3):**

- **Trigger**: Story implementation exceeds complexity threshold (e.g., >5 new files, >300 lines in one file)
- **Requirement**: Schedule explicit "cleanup" task or refactoring story
- **Goal**: Prevent tech debt accumulation in complex flows (like Clarification Flow)

---

## Project References

- Architecture: `_bmad-output/planning-artifacts/architecture.md`
- PRD: `_bmad-output/planning-artifacts/prd.md`
- Testing Patterns: `docs/testing-patterns.md`
- Error Code Governance: `docs/error-code-governance.md`
- Pre-commit Hooks: `docs/pre-commit-hooks.md`

---

## Next Steps

This context file will be updated as patterns evolve. When implementing:

1. Follow all rules in this document
2. Check `docs/` for detailed pattern documentation
3. Run tests before committing
4. Ensure pre-commit hooks pass
