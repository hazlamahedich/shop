# Code Style and Conventions

## Python (Backend)

### Formatting
- **Line length**: 100 characters
- **Formatter**: Black (double quotes, space indentation)
- **Import sorting**: isort with black profile
- **Target version**: Python 3.11

### Linting
- **Ruff**: Primary linter with rules E, F, I, N, W, UP (ignore E203)
- **MyPy**: Strict type checking with `disallow_untyped_defs = true`
- **Pydantic plugin**: Enabled for MyPy

### Type Hints
- **Required**: All functions must have type hints
- **Use**: `Mapped[...]` for SQLAlchemy columns
- **Optional fields**: Use `Optional[Type]` or `Type | None`

### Naming Conventions
- **Classes**: PascalCase (e.g., `FaqMatcher`, `Merchant`)
- **Functions/Methods**: snake_case (e.g., `match_faq`, `get_merchant`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `SESSION_DURATION_MS`)
- **Private methods**: Prefix with underscore (e.g., `_exact_question_match`)
- **Variables**: snake_case

### Docstrings
- Use triple-double-quotes docstrings for classes and public methods
- Include Args, Returns, and Raises sections

### Database Models
- Inherit from `Base` class
- Use `Mapped[Type]` for type-annotated columns
- Use `mapped_column()` for column definitions
- Define relationships with `relationship()` and back_populates

### Pydantic Schemas
- Use Pydantic v2 syntax
- Create request/response schemas separately
- Use validators for data transformation (e.g., `@field_validator`)
- Export via `__all__` in schema modules

### API Routes
- Use FastAPI router with `/api/v1/` prefix
- Use dependency injection for database sessions
- Return Pydantic response models
- Use envelope pattern for responses (data/meta structure)

### Testing
- **Co-location**: Tests placed alongside source files as `test_*.py`
- **Framework**: pytest with pytest-asyncio
- **Async**: Use `asyncio_mode = "auto"`
- **Coverage target**: 80% minimum (fail_under = 80)
- **Fixtures**: Define in `conftest.py` files

## TypeScript (Frontend)

### Formatting
- **Formatter**: Prettier
- **Quote style**: Double quotes (from ESLint)

### Linting
- **ESLint** with TypeScript and React plugins
- React hooks rules enforced
- Unused vars with underscore prefix ignored

### TypeScript Configuration
- **Strict mode**: Enabled
- **Target**: ES2020
- **Module**: ESNext with bundler resolution
- **No unused locals/parameters**: True
- **Path alias**: `@/*` maps to `./src/*`

### Naming Conventions
- **Components**: PascalCase with `.tsx` extension
- **Files**: PascalCase for components, camelCase for utilities
- **Stores**: camelCase with `Store` suffix (e.g., `authStore.ts`)
- **Types/Interfaces**: PascalCase

### State Management (Zustand)
- Create stores with `create()` function
- Export hooks from store files (e.g., `useAuthStore`)
- Use TypeScript for store typing

### Testing
- **Framework**: Vitest
- **Co-location**: Tests placed as `*.test.ts` or `*.test.tsx`
- **Testing Library**: For React component testing
- **MSW**: For API mocking in tests

### React Patterns
- Functional components with hooks
- Use `@/` path alias for imports
- Tailwind CSS for styling

## General Principles

### Test Colocation
- Tests must be co-located with source code
- Pattern: `test_*.py` for Python, `*.test.ts(x)` for TypeScript
- Validation: `scripts/validate_test_colocation.py`

### API Versioning
- All API routes use `/api/v1/` prefix

### Error Handling
- Use structured error responses with error codes
- Log errors with structlog context

### Git Commits
- Use conventional commit format (feat, fix, docs, etc.)
- Pre-commit hooks enforce code quality
