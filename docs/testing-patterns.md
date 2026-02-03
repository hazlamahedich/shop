# Testing Patterns

This document describes the testing patterns and conventions used across the Shopping Assistant Bot project.

## Test Pyramid

Our test distribution follows the 70/20/10 rule:

- **70% Unit Tests**: Test individual functions and classes in isolation
- **20% Integration Tests**: Test component interactions
- **10% E2E Tests**: Test critical user flows end-to-end

## Test Structure

### Co-located Tests
Unit tests are co-located with the code they test:

```
backend/app/
├── services/
│   ├── llm/
│   │   ├── openai_service.py
│   │   └── test_openai_service.py  ← Co-located test
│   └── shopify/
│       ├── storefront.py
│       └── test_storefront.py      ← Co-located test
```

### Separate Test Suites
Integration and E2E tests live in separate directories:

```
backend/tests/
├── integration/
│   ├── test_llm_endpoints.py
│   └── test_shopify_integration.py
└── contract/
    └── test_api.py
```

## Testing with IS_TESTING Flag

The `IS_TESTING` environment variable forces use of test doubles:

```python
from backend.app.core.config import is_testing
from backend.tests.fixtures.mock_llm import MockLLMProvider

def get_llm_service():
    if is_testing():
        return MockLLMProvider(provider="test")
    return OpenAIService()
```

Tests always set `IS_TESTING=true` via `conftest.py`:
```python
@pytest.fixture(autouse=True)
def set_testing_env(monkeypatch):
    monkeypatch.setenv("IS_TESTING", "true")
```

## Unit Test Patterns

### Testing Service Functions

```python
# test_user_service.py
import pytest
from backend.app.services.user import UserService
from backend.tests.fixtures.factory import UserFactory

class TestUserService:
    async def test_create_user(self, db_session):
        # Arrange
        factory = UserFactory(email="test@example.com")
        service = UserService(db_session)

        # Act
        user = await service.create_user(factory.to_dict())

        # Assert
        assert user.email == "test@example.com"
        assert user.id is not None
```

### Testing Error Conditions

```python
async def test_create_user_duplicate_email(self, db_session):
    # Arrange
    factory = UserFactory(email="test@example.com")
    service = UserService(db_session)
    await service.create_user(factory.to_dict())

    # Act & Assert
    with pytest.raises(ValidationError) as exc:
        await service.create_user(factory.to_dict())
    assert "email already exists" in str(exc.value)
```

## Integration Test Patterns

### API Endpoint Tests

```python
# test_llm_endpoints.py
import pytest
from httpx import AsyncClient
from backend.app.main import app

@pytest.mark.asyncio
async def test_chat_endpoint_returns_intent():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post("/api/v1/chat", json={
            "message": "I want to buy shoes"
        })

    assert response.status_code == 200
    data = response.json()
    assert data["intent"] == "product_search"
```

### Database Tests

```python
# test_cart_repository.py
@pytest.mark.asyncio
async def test_cart_persists_to_db(db_session):
    # Arrange
    cart = CartFactory()

    # Act
    saved = await cart_repo.save(cart.to_dict())
    retrieved = await cart_repo.get_by_id(saved["id"])

    # Assert
    assert retrieved["session_id"] == cart.session_id
```

## Contract Testing

We use Schemathesis for API contract testing:

```python
# tests/contract/test_api.py
import schemathesis
from backend.app.main import app

schema = schemathesis.from_wsgi("/openapi.json", app)

@schema.parametrize()
async def test_api_endpoint(case):
    """Test all API endpoints against OpenAPI schema."""
    response = await case.call_asgi()
    case.validate_response(response)
```

## Mock LLM Usage

Always use mock LLM providers in tests:

```python
from backend.tests.fixtures.mock_llm import MockLLMProvider

@pytest.mark.asyncio
async def test_intent_classification():
    # Arrange
    mock_llm = MockLLMProvider(provider="test")

    # Act
    response = await mock_llm.chat("I want to checkout")

    # Assert
    assert response.intent == "checkout"
    assert response.confidence > 0.9
```

## Test Factories

Use factories to generate test data:

```python
from backend.tests.fixtures.factory import ProductFactory

def test_product_search():
    # Create test product
    product = ProductFactory(
        title="Test Shoe",
        price=99.99,
        category="footwear"
    )

    # Use in test
    result = search_products(product.title)
    assert result[0]["id"] == product.id
```

## Fixtures

### Async Database Session

```python
@pytest.fixture
async def db_session():
    async with async_session() as session:
        yield session
    await session.rollback()
```

### Authenticated Client

```python
@pytest.fixture
async def auth_client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        token = await get_test_token()
        ac.headers["Authorization"] = f"Bearer {token}"
        yield ac
```

## Running Tests

### Run All Tests
```bash
cd backend
pytest
```

### Run Specific Test File
```bash
pytest tests/unit/test_user_service.py
```

### Run With Coverage
```bash
pytest --cov=app --cov-report=html
```

### Run Contract Tests
```bash
pytest tests/contract/
```

## Best Practices

1. **One assertion per test** - Tests should verify one thing
2. **Arrange-Act-Assert** - Structure tests clearly
3. **Descriptive names** - `test_user_creation_fails_with_duplicate_email`
4. **Use factories** - Don't manually construct test data
5. **Mock external services** - Never call real APIs in tests
6. **Clean up** - Rollback transactions after each test
7. **Test edge cases** - Null inputs, empty strings, boundary values

## Pre-commit Test Validation

The test colocation hook ensures all code has tests:
```bash
./scripts/validate_test_colocation.py
```

This checks that for every `module.py` there's a `test_module.py` in the same directory.
