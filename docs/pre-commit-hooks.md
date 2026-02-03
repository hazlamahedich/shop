# Pre-commit Hooks

This document describes the pre-commit hooks configured for the Shopping Assistant Bot project.

## Overview

Pre-commit hooks automatically run checks before each commit, ensuring code quality and consistency.

## Installation

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run hooks on all files (first time)
pre-commit run --all-files
```

## Configured Hooks

### Generic Hooks

| Hook | Description | Files |
|------|-------------|-------|
| trailing-whitespace | Removes trailing whitespace | All |
| end-of-file-fixer | Ensures newline at EOF | All |
| check-yaml | Validates YAML syntax | *.yaml, *.yml |
| check-toml | Validates TOML syntax | *.toml |
| check-json | Validates JSON syntax | *.json |
| check-added-large-files | Blocks files > 1MB | All |
| check-merge-conflict | Blocks merge conflict markers | All |
| debug-statements | Blocks debug statements | *.py |
| detect-private-key | Blocks leaked private keys | All |

### Python Hooks

| Hook | Description | Version |
|------|-------------|---------|
| black | Code formatting | 24.1.1 |
| isort | Import sorting | 5.13.2 |
| flake8 | Linting | 7.0.0 |
| bandit | Security checks | 1.7.6 |
| test-colocation-python | Validates test co-location | Custom |
| openapi-generator | Generates OpenAPI spec | Custom |

### Custom Hooks

#### test-colocation-python

Validates that every Python source file has a co-located test file.

**Location:** `backend/scripts/hooks/test_colocation.py`

**Pattern:** `module.py` → `test_module.py` in same directory

**Example:**
```
backend/app/services/llm/openai.py
backend/app/services/llm/test_openai.py  ← Required
```

#### openapi-generator

Generates OpenAPI specification from FastAPI application.

**Location:** `backend/scripts/hooks/openapi_gen.py`

**Output:** `backend/openapi.json`

**Runs:** On every commit to `backend/`

## TypeScript Hooks

| Hook | Description | Files |
|------|-------------|-------|
| test-colocation-typescript | Validates test co-location | *.tsx, *.ts |
| api-version-prefix | Validates API version prefix | *.ts |

## Configuration File

The `.pre-commit-config.yaml` file at the project root defines all hooks:

```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      # ... more hooks

  - repo: local
    hooks:
      - id: test-colocation-python
        entry: bash -c 'cd backend && python -m scripts.hooks.test_colocation'
        # ...
```

## Running Hooks Manually

### Run All Hooks
```bash
pre-commit run --all-files
```

### Run Specific Hook
```bash
pre-commit run black --files backend/app/services/llm/openai.py
```

### Skip Hooks (Not Recommended)
```bash
git commit --no-verify -m "WIP"
```

## Hook Performance

Hooks run in parallel where possible. Typical run times:

- Generic hooks: ~2 seconds
- Python formatting: ~5 seconds
- Python linting: ~10 seconds
- Custom hooks: ~3 seconds

**Total:** ~20 seconds for typical changes

## Troubleshooting

### Hook Fails on New Files

If a hook fails on new files:
```bash
# Run hooks on all files to catch issues
pre-commit run --all-files
```

### Hook Passes but CI Fails

Local hooks may use different versions than CI. Sync versions:
```bash
pre-commit autoupdate
git add .pre-commit-config.yaml
```

### Specific Hook Issues

**Black formatting differs from IDE:**
- Configure IDE to use Black with line-length=100
- Or run `black` manually to see differences

**Flake8 errors:**
- Check `.flake8` config for ignores
- Some warnings are intentionally ignored (E203, W503)

## Adding New Hooks

To add a new pre-commit hook:

1. Add to `.pre-commit-config.yaml`
2. Run `pre-commit run --all-files` to verify
3. Commit the config change

Example:
```yaml
- repo: https://github.com/pre-commit/mirrors-mypy
  rev: v1.8.0
  hooks:
    - id: mypy
      additional_dependencies: [pydantic>=2.0]
```

## CI/CD Integration

The same hooks run in CI/CD via GitHub Actions (`.github/workflows/ci.yml`):

```yaml
- name: Run pre-commit
  run: |
    pip install pre-commit
    pre-commit run --all-files
```

This ensures all code passing locally also passes in CI.
