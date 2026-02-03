# Party Mode Quick Reference

## File Location Patterns

### Backend (Python)

| Pattern | Location | Example |
|---------|----------|---------|
| Source file | `backend/app/module/` | `backend/app/services/user.py` |
| Test file | Same directory | `backend/app/services/test_user.py` |
| API routes | `backend/app/api/v1/` | `backend/app/api/v1/routes.py` |
| Errors | `backend/app/core/errors.py` | `ErrorCode.USER_NOT_FOUND` |

### Frontend (TypeScript)

| Pattern | Location | Example |
|---------|----------|---------|
| Source file | `frontend/src/` | `frontend/src/services/User.ts` |
| Test file | Same directory | `frontend/src/services/User.test.ts` |
| Components | `frontend/src/components/` | `Button.tsx` + `Button.test.tsx` |
| API calls | `frontend/src/services/` | `api.getUser()` |

## API Response Format

### Success Response

```json
{
  "data": { ... },
  "meta": {
    "request_id": "uuid",
    "timestamp": "2024-01-01T00:00:00Z"
  }
}
```

### Error Response

```json
{
  "data": null,
  "error": {
    "error_code": "SPECIFIC_ERROR",
    "message": "Human readable message",
    "details": { ... }
  },
  "meta": {
    "request_id": "uuid",
    "timestamp": "2024-01-01T00:00:00Z"
  }
}
```

## API Endpoint Pattern

### Python (FastAPI)

```python
from app.core.errors import ErrorCode
from app.core.exceptions import DomainException

@router.get("/api/v1/users/{user_id}")
async def get_user(
    user_id: int,
    request_id: str = Header(default=None),
) -> UserResponse:
    """Get user by ID."""
    user = await service.get_user(user_id)

    if not user:
        raise UserNotFoundException(
            message=f"User {user_id} not found",
            details={"user_id": user_id}
        )

    return {
        "data": user,
        "meta": {
            "request_id": request_id or str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat()
        }
    }
```

### TypeScript

```typescript
interface ApiResponse<T> {
  data: T;
  meta: {
    request_id: string;
    timestamp: string;
  };
}

interface ApiError {
  error_code: string;
  message: string;
  details?: Record<string, unknown>;
  meta: {
    request_id: string;
    timestamp: string;
  };
}

async function getUser(userId: number): Promise ApiResponse<User>> {
  const response = await fetch(`/api/v1/users/${userId}`);

  if (!response.ok) {
    const error: ApiError = await response.json();
    throw new Error(error.message);
  }

  return response.json();
}
```

## Error Handling Pattern

### Define Exception

```python
# backend/app/core/exceptions.py
class DomainException(Exception):
    """Base domain exception."""
    error_code: ErrorCode = ErrorCode.INTERNAL_ERROR

class UserNotFoundException(DomainException):
    """User not found exception."""
    error_code = ErrorCode.USER_NOT_FOUND
```

### Register Error Code

```python
# backend/app/core/errors.py
class ErrorCode(str, Enum):
    """Error code registry."""
    USER_NOT_FOUND = "USER_NOT_FOUND"
    INVALID_INPUT = "INVALID_INPUT"
```

### Raise Error

```python
raise UserNotFoundException(
    message="User not found",
    details={"user_id": 123}
)
```

## Testing Patterns

### Backend Test

```python
# test_user_service.py
import pytest
from fastapi.testclient import TestClient

class TestUserService:
    @pytest.fixture
    def client(self):
        from app.main import app
        return TestClient(app)

    def test_get_user_success(self, client):
        response = client.get("/api/v1/users/123")

        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "meta" in data
        assert "request_id" in data["meta"]
```

### Frontend Test

```typescript
// User.test.tsx
import { render, screen } from '@testing-library/react';
import { User } from './User';

describe('User', () => {
  it('displays user name', () => {
    render(<User name="John" />);
    expect(screen.getByText('John')).toBeInTheDocument();
  });
});
```

## Naming Conventions

### Backend

| Context | Convention | Example |
|---------|-----------|---------|
| Database | snake_case | `first_name` |
| Python variables | snake_case | `user_id` |
| API response keys | snake_case | `{"user_id": 123}` |
| Error codes | SCREAMING_SNAKE_CASE | `USER_NOT_FOUND` |

### Frontend

| Context | Convention | Example |
|---------|-----------|---------|
| TypeScript | camelCase | `userId` |
| Components | PascalCase | `UserProfile` |
| Hooks | camelCase with 'use' | `useUserProfile` |
| API keys (auto-converted) | camelCase | `userId` from `user_id` |

## Common Commands

### Backend

```bash
# Format code
black backend/app
isort backend/app

# Run linting
flake8 backend/app
pylint backend/app

# Type checking
mypy backend/app

# Security scan
bandit -r backend/app

# Run tests
pytest backend/app

# Generate OpenAPI spec
cd backend && python -m scripts.hooks.openapi_gen
```

### Frontend

```bash
# Format code
npx prettier --write frontend/src/**/*.{ts,tsx}

# Run linting
cd frontend && npm run lint

# Type checking
cd frontend && npm run typecheck

# Run tests
cd frontend && npm test

# Generate types
cd frontend && npm run types:generate
```

## VS Code Snippets

Type these in VS Code to expand:

Python:
- `api-response` → Response envelope
- `api-error` → Error with envelope
- `api-endpoint` → FastAPI endpoint
- `exception` → Domain exception
- `test-header` → Test file template

TypeScript:
- `api-call` → API function
- `api-error-type` → Error interface
- `api-response-type` → Response interface
- `api-hook` → React Query hook

## Type Sync Workflow

1. **Backend**: Add/change API endpoint
2. **Commit**: Pre-commit generates `openapi.json`
3. **Frontend**: Run `npm run types:generate`
4. **Use**: Auto-generated types in `api.generated.ts`

```bash
# Backend (automatic on commit)
cd backend && python -m scripts.hooks.openapi_gen

# Frontend (manual or in CI)
cd frontend
npx openapi-typescript ../backend/openapi.json -o src/types/api.generated.ts
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Pre-commit fails | Run `pre-commit run --all-files` |
| Type errors | Run `mypy backend/app` or `npm run typecheck` |
| Tests missing | Create `test_X.py` or `X.test.tsx` |
| API version wrong | Use `/api/v1/...` not `/api/...` |
| Format issues | Run `black .` or `npx prettier --write .` |
