# Agent Instructions

## Project Overview

Full-stack conversational commerce app: **FastAPI + SQLAlchemy** backend, **React + Vite + TypeScript** frontend, PostgreSQL + Redis. Python 3.11, Node >=22.

## Build / Lint / Test Commands

### Frontend (from `frontend/`)

```bash
npm run dev                     # Dev server on :5173
npm run build                   # Production build (vite build)
npm run build:with-typecheck    # Build with tsc check first
npm run type-check              # tsc --noEmit (type checking only)
npm run lint                    # ESLint: eslint . --ext .ts,.tsx
npm run lint:fix                # Auto-fix lint issues
npm run format                  # Prettier write
npm run format:check            # Prettier check
npm test                        # Vitest (unit/component, watch mode)
npm test -- --run               # Vitest single run (no watch)
npm test -- --run src/widget/components/QuickReplyButtons.test.tsx  # Single test file
npm run test:e2e                # Playwright E2E tests
npm run test:e2e -- tests/e2e/story-9-4-quick-reply.spec.ts        # Single E2E test
npm run test:e2e -- --grep "P0"                                     # Run tests by tag
npm run test:e2e:p0             # P0 critical tests only
npm run test:api                # API integration tests
npm run build:widget            # Build embeddable widget bundle
```

### Backend (from `backend/`, activate venv first)

```bash
source venv/bin/activate        # ALWAYS activate before Python work
python --version                # Verify 3.11.x (NOT system Python)

# Dev server
python -m uvicorn app.main:app --reload --port 8000

# Linting & formatting
ruff check .                    # Lint (ruff)
ruff check --fix .              # Auto-fix
black .                         # Format
mypy .                          # Type check

# Tests
python -m pytest -v                                        # All tests
python -m pytest tests/unit/test_service.py -v             # Single test file
python -m pytest tests/unit/test_service.py::test_func -v  # Single test function
python -m pytest tests/integration/ -v                     # Integration tests only
python -m pytest -v -k "test_name_pattern"                 # By name pattern
python -m pytest -m p0 -v                                  # By marker (p0/p1/p2/p3)
python -m pytest --cov=app --cov-report=html               # With coverage (min 80%)

# Database
alembic upgrade head            # Run migrations
alembic downgrade -1            # Rollback
python scripts/seed_test_data.py                          # Seed test data
```

### Docker

```bash
docker-compose up -d            # Start Postgres (port 5433) + Redis (6379) + backend (8000)
```

## Code Style

### Python (Backend)

- **Formatter**: Black (line-length 100, double quotes, spaces)
- **Linter**: Ruff (rules: E, F, I, N, W, UP; ignore E203)
- **Types**: mypy strict (`disallow_untyped_defs = true`), pydantic plugin
- **Imports**: `from __future__ import annotations`, stdlib → third-party → local, sorted by ruff
- **Naming**: `snake_case` for variables/functions, `PascalCase` for classes, `UPPER_CASE` for constants
- **Error handling**: Use FastAPI `HTTPException` in API layer, custom exceptions in services, structured logging via structlog
- **Async**: All DB operations async (`asyncpg`), pytest-asyncio with `asyncio_mode = "auto"`
- **Schemas**: Pydantic v2 models with `Field(alias="...")` for camelCase API fields
- **Test markers**: `@pytest.mark.p0`, `p1`, `p2`, `p3`, `smoke`, `test_id("STORY-X-Y-SEQ")`

### TypeScript / React (Frontend)

- **Formatter**: Prettier (semi: true, single quotes, trailing comma es5, print width 100, 2-space indent)
- **Linter**: ESLint with `@typescript-eslint/recommended`, `react-hooks/recommended`
- **Types**: `strict: true`, `noUnusedLocals`, `noUnusedParameters`
- **Path alias**: `@/*` maps to `./src/*`
- **Imports**: React hooks → external libs → internal modules → types, grouped with blank lines
- **Naming**: `camelCase` for variables/functions, `PascalCase` for components/types/interfaces, `kebab-case` for files
- **State**: Zustand for global, React Query for server state, `useState` for local
- **Styling**: Tailwind CSS v4, Lucide React for icons, existing UI components in `src/components/ui/` (DO NOT recreate primitives)
- **API**: Use `apiClient` which returns `{ data: T, meta }` envelope — access via `response.data`, NOT `response.data.data`
- **Tests**: Unit tests collocated with source (`Foo.test.tsx`), E2E in `tests/e2e/`, NO `__tests__/` folders

### Naming Conventions (Cross-Stack)

| Layer | Convention | Example |
|-------|-----------|---------|
| Database columns | `snake_case` | `created_at`, `merchant_id` |
| Python variables | `snake_case` | `user_name` |
| API JSON fields | `camelCase` | `createdAt`, `merchantId` |
| TypeScript variables | `camelCase` | `userName` |
| React components | `PascalCase` | `ChatBubble` |
| CSS classes | `kebab-case` | `chat-bubble` |
| Test files (frontend) | `*.test.tsx` | `ChatBubble.test.tsx` |
| Test files (backend) | `test_*.py` | `test_service.py` |
| E2E test files | `story-X-Y-name.spec.ts` | `story-9-4-reply.spec.ts` |

## Key Architecture Decisions

- **3 databases**: `shop_prod` / `shop_dev` / `shop_test` — integration tests MUST use `shop_test` only
- **Embeddings**: JSONB storage with `embedding_dimension` column, cast to vector at query time (NOT fixed `Vector(N)`)
- **Widget**: Separate Vite build (`vite.widget.config.ts`), embeddable bundle
- **CSRF**: New API routes must be added to bypass list in `backend/app/middleware/auth.py`
- **Datetime**: Use `datetime.now(timezone.utc)` — NOT `datetime.now(UTC)` (3.9 compat)
- **E2E waits**: Use `expect().toBeVisible()` / `waitForResponse()` — NEVER `waitForTimeout()` or `sleep()`
- **CSS transform**: NEVER on container/wrapper elements (breaks `position: fixed` children); use `left/top` instead
