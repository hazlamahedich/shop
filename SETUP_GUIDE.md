# Party Mode Tooling Setup Guide

## Quick Start

### 1. Initial Setup (5 minutes)

```bash
# Run the setup script
bash pre-commit-setup.sh
```

This will:
- Create necessary directories
- Install pre-commit hooks
- Set up configuration files

### 2. Backend Setup (5 minutes)

```bash
# Create virtual environment
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install black isort flake8 bandit mypy pylint pre-commit

# Install pre-commit hooks
pre-commit install
```

### 3. Frontend Setup (5 minutes)

```bash
cd frontend

# Install dependencies
npm install

# Install pre-commit hooks (already done in step 1)
```

## Pre-commit Hooks

### What Gets Checked

Every commit triggers these checks:

**Python files:**
- Code formatting (black)
- Import sorting (isort)
- Linting (flake8)
- Security issues (bandit)
- Test file exists (custom hook)
- OpenAPI spec generated (custom hook)

**TypeScript files:**
- Test file exists (custom hook)
- API version prefix (custom hook)
- ESLint rules (when configured)

### Running Hooks Manually

```bash
# Run all hooks on all files
pre-commit run --all-files

# Run specific hook
pre-commit run black --all-files

# Skip hooks (not recommended)
git commit --no-verify -m "message"
```

## Code Snippets

### VS Code snippets are available for:

**Python:**
- `api-response` - API response with envelope
- `api-error` - Error response with envelope
- `api-endpoint` - FastAPI endpoint template
- `exception` - Domain exception with error code
- `test-header` - Test file template

**TypeScript:**
- `api-call` - Typed API call function
- `api-error-type` - API error interface
- `api-response-type` - API response interface
- `api-hook` - React Query hook
- `component-with-test` - React component template

## Pattern Enforcement Summary

| Pattern | Enforcement | Auto-fix |
|---------|-------------|----------|
| Test co-location | Pre-commit, CI | No |
| API envelope | Pylint, custom hooks | No |
| Error codes | Custom hooks | No |
| API versioning | ESLint, custom hooks | No |
| Type sync | OpenAPI generation | Yes |
| Code formatting | black, prettier | Yes |
| Import sorting | isort | Yes |

## Troubleshooting

### Pre-commit fails locally

```bash
# See what failed
pre-commit run --all-files

# Auto-fix what you can
black backend/
isort backend/
npx prettier --write frontend/src/**/*.{ts,tsx}
```

### Hooks fail in CI but pass locally

Check versions:
```bash
python --version  # Should be 3.11
node --version    # Should be 20
```

### Type generation fails

Ensure backend app can import:
```bash
cd backend
python -c "from app.main import app; print(app)"
```

## CI/CD Pipeline

The GitHub Actions workflow runs on every push/PR to `main` or `develop`:

1. **Backend validation**
   - Code formatting checks
   - Linting (flake8)
   - Type checking (mypy)
   - Security (bandit)
   - Test colocation
   - OpenAPI generation

2. **Frontend validation**
   - Test colocation
   - API versioning
   - ESLint
   - TypeScript checks
   - Tests

3. **Integration validation**
   - Contract compatibility
   - End-to-end checks

## File Structure

```
shop/
├── .pre-commit-config.yaml     # Pre-commit hook configuration
├── .github/workflows/
│   └── party-mode-validation.yml  # CI/CD pipeline
├── .vscode/
│   ├── settings.json            # VS Code settings
│   ├── extensions.json          # Recommended extensions
│   └── snippets/
│       ├── python.code-snippets
│       └── typescript.code-snippets
├── backend/
│   ├── scripts/
│   │   └── hooks/
│   │       ├── __init__.py
│   │       ├── test_colocation.py
│   │       └── openapi_gen.py
│   └── openapi.json             # Generated OpenAPI spec
├── frontend/
│   └── scripts/
│       └── hooks/
│           ├── test-colocation.js
│           └── api-version.js
└── TOOLING_ENFORCEMENT_REPORT.md
```

## Next Steps

1. Run `pre-commit run --all-files` to verify setup
2. Create a test file using the snippets
3. Commit your changes to see hooks in action
4. Check the CI/CD pipeline results

## Support

See `TOOLING_ENFORCEMENT_REPORT.md` for complete documentation.
