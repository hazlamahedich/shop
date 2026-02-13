# Shopping Assistant Bot

AI-powered shopping assistant for Facebook Messenger with optional e-commerce integration.

## Project Overview

This is a monorepo containing backend (Python/FastAPI) and frontend (React/TypeScript) applications.

### Key Features

- **Optional E-Commerce** - Works with or without a store connected (Shopify optional)
- **FAQ & Business Info** - Configure FAQs and business information for automated responses
- **Human Handoff** - Route conversations to human support when needed
- **Pluggable Providers** - Extensible architecture for future integrations (WooCommerce, BigCommerce)

## Quick Start

### Prerequisites

- Python 3.11.7
- Node.js 20 LTS
- Docker (for local PostgreSQL and Redis)

### Local Development

1. **Start infrastructure:**
   ```bash
   docker-compose up -d
   ```

2. **Backend setup:**
   ```bash
   cd backend
   pip install -e ".[dev]"
   pytest
   ```

3. **Frontend setup:**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

## Project Structure

```
shop/
├── backend/               # Python/FastAPI backend
│   ├── app/              # Application code
│   │   ├── api/          # API routes
│   │   ├── core/         # Core functionality (errors, config, database)
│   │   ├── models/       # SQLAlchemy ORM models
│   │   ├── schemas/      # Pydantic schemas (API contracts)
│   │   └── services/     # Business logic
│   ├── tests/            # Test suite
│   │   ├── fixtures/     # Test data factories and mocks
│   │   ├── unit/         # Co-located unit tests
│   │   └── contract/     # API contract tests
│   └── alembic/          # Database migrations
├── frontend/             # React/TypeScript frontend
│   └── src/
│       ├── components/   # React components
│       ├── stores/       # Zustand state management
│       └── lib/types/    # Generated TypeScript types
├── scripts/              # Shared scripts (type generation, validation)
├── docs/                 # Documentation
└── .github/              # CI/CD workflows
```

## Development Tools

### Pre-commit Hooks

Automated code quality checks run before each commit:

```bash
# Install hooks
pip install pre-commit
pre-commit install

# Run manually
pre-commit run --all-files
```

### Type Generation

TypeScript types are auto-generated from Pydantic schemas:

```bash
python scripts/generate_types.py
```

### Test Colocation Validation

Ensures all code has co-located tests:

```bash
python scripts/validate_test_colocation.py
```

## Testing

### Backend Tests

```bash
cd backend
pytest                    # Run all tests
pytest --cov=app          # With coverage
pytest tests/contract/    # Contract tests only
```

### Frontend Tests

```bash
cd frontend
npm test                 # Run all tests
npm run test:coverage     # With coverage
```

## Environment Variables

### Backend (`.env`)

```bash
# Database
DATABASE_URL=postgresql+asyncpg://developer:developer@localhost:5432/shop_dev

# Redis
REDIS_URL=redis://localhost:6379/0

# Testing (optional - for development without real services)
IS_TESTING=false
MOCK_STORE_ENABLED=false

# Shopify (OPTIONAL - only if using e-commerce features)
SHOPIFY_STORE_URL=https://your-store.myshopify.com
SHOPIFY_STOREFRONT_TOKEN=your_token

# Facebook Messenger (required)
FACEBOOK_PAGE_ID=your_page_id
FACEBOOK_PAGE_ACCESS_TOKEN=your_token
FACEBOOK_APP_SECRET=your_secret
FACEBOOK_VERIFY_TOKEN=your_verify_token

# LLM Provider
LLM_PROVIDER=ollama  # ollama, openai, anthropic, gemini
LLM_API_KEY=your_api_key
```

### Running Without Shopify

The bot works fully without a connected e-commerce store. To test locally without Shopify:

```bash
# Enable mock store for development
export IS_TESTING=true
export MOCK_STORE_ENABLED=true
```

## Documentation

- [Architecture: E-Commerce Abstraction](docs/architecture/ecommerce-abstraction.md)
- [API: E-Commerce Provider](backend/docs/api/ecommerce-provider.md)
- [API: Business Info & FAQ](backend/docs/api/business-info-faq.md)
- [Error Code Governance](docs/error-code-governance.md)
- [Testing Patterns](docs/testing-patterns.md)
- [Pre-commit Hooks](docs/pre-commit-hooks.md)
- [Type Generation](docs/type-generation.md)

## CI/CD

- **Main Pipeline:** [`.github/workflows/ci.yml`](.github/workflows/ci.yml)
- **PR Validation:** [`.github/workflows/pr-validation.yml`](.github/workflows/pr-validation.yml)

## License

MIT
