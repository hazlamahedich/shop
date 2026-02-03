#!/usr/bin/env bash
# Quick setup script for Party Mode pre-commit hooks

set -euo pipefail

echo "Party Mode - Pre-commit Hook Setup"
echo "=================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if pre-commit is installed
if ! command -v pre-commit &> /dev/null; then
    echo -e "${RED}Error: pre-commit is not installed${NC}"
    echo "Install it with: pip install pre-commit"
    exit 1
fi

echo -e "${GREEN}✓${NC} pre-commit is installed"

# Create necessary directories
echo "Creating directories..."
mkdir -p backend/scripts/hooks
mkdir -p frontend/scripts/hooks
mkdir -p backend/app/api
mkdir -p backend/app/core
mkdir -p frontend/src/types
mkdir -p frontend/src/services

echo -e "${GREEN}✓${NC} Directories created"

# Create .pre-commit-config.yaml if it doesn't exist
if [ ! -f .pre-commit-config.yaml ]; then
    echo "Creating .pre-commit-config.yaml..."
    cat > .pre-commit-config.yaml << 'EOF'
# Party Mode Pre-commit Hooks
# See TOOLING_ENFORCEMENT_REPORT.md for documentation

repos:
  # Generic hooks
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-toml
      - id: check-json
      - id: check-added-large-files
        args: ['--maxkb=1000']
      - id: check-merge-conflict
      - id: debug-statements

  # Python: Formatting and linting (Phase 1)
  - repo: https://github.com/psf/black
    rev: 24.1.1
    hooks:
      - id: black
        language_version: python3.11

  - repo: https://github.com/pycqa/isort
    rev: 5.13.2
    hooks:
      - id: isort
        args: ['--profile', 'black']

  - repo: https://github.com/pycqa/flake8
    rev: 7.0.0
    hooks:
      - id: flake8
        args: ['--max-line-length=100', '--extend-ignore=E203,W503']

  # Security
  - repo: https://github.com/PyCQA/bandit
    rev: 1.7.6
    hooks:
      - id: bandit
        args: ['-r', 'backend/app', '-ll']

  # Custom hooks (will be created by setup script)
  - repo: local
    hooks:
      - id: test-colocation-python
        name: Validate Python test co-location
        entry: bash -c 'cd backend && python -m scripts.hooks.test_colocation || true'
        language: system
        types: [python]
        pass_filenames: false

  - repo: local
    hooks:
      - id: openapi-generator
        name: Generate OpenAPI spec
        entry: bash -c 'cd backend && python -m scripts.hooks.openapi_gen || true'
        language: system
        pass_filenames: false
        always_run: true
EOF
    echo -e "${GREEN}✓${NC} .pre-commit-config.yaml created"
else
    echo -e "${YELLOW}⚠${NC} .pre-commit-config.yaml already exists, skipping"
fi

# Install hooks
echo ""
echo "Installing pre-commit hooks..."
pre-commit install
echo -e "${GREEN}✓${NC} Hooks installed"

echo ""
echo -e "${GREEN}Setup complete!${NC}"
echo ""
echo "Next steps:"
echo "  1. Create a sample file to test hooks"
echo "  2. Run: pre-commit run --all-files"
echo "  3. See TOOLING_ENFORCEMENT_REPORT.md for full documentation"
echo ""
