#!/usr/bin/env bash
# Verify Party Mode tooling setup

echo "Party Mode Tooling Verification"
echo "================================"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

checks_passed=0
checks_failed=0

check_file() {
  if [ -f "$1" ]; then
    echo -e "${GREEN}✓${NC} $1"
    ((checks_passed++))
  else
    echo -e "${RED}✗${NC} $1 (missing)"
    ((checks_failed++))
  fi
}

check_dir() {
  if [ -d "$1" ]; then
    echo -e "${GREEN}✓${NC} $1/"
    ((checks_passed++))
  else
    echo -e "${YELLOW}⚠${NC} $1/ (not created yet - OK)"
    ((checks_passed++))
  fi
}

echo "Configuration Files"
echo "-------------------"
check_file ".pre-commit-config.yaml"
check_file ".github/workflows/party-mode-validation.yml"
check_file "pre-commit-setup.sh"
echo ""

echo "IDE Integration"
echo "----------------"
check_file ".vscode/settings.json"
check_file ".vscode/extensions.json"
check_file ".vscode/snippets/python.code-snippets"
check_file ".vscode/snippets/typescript.code-snippets"
echo ""

echo "Backend Hooks"
echo "--------------"
check_file "backend/scripts/hooks/__init__.py"
check_file "backend/scripts/hooks/test_colocation.py"
check_file "backend/scripts/hooks/openapi_gen.py"
echo ""

echo "Frontend Hooks"
echo "--------------"
check_file "frontend/scripts/hooks/test-colocation.js"
check_file "frontend/scripts/hooks/api-version.js"
echo ""

echo "Documentation"
echo "-------------"
check_file "TOOLING_ENFORCEMENT_REPORT.md"
check_file "SETUP_GUIDE.md"
check_file "QUICK_REFERENCE.md"
check_file "TOOLING_README.md"
check_file "IMPLEMENTATION_SUMMARY.md"
check_file "TOOLING_STRUCTURE.txt"
echo ""

echo "Summary"
echo "-------"
echo -e "Passed: ${GREEN}${checks_passed}${NC}"
echo -e "Failed: ${RED}${checks_failed}${NC}"
echo ""

if [ $checks_failed -eq 0 ]; then
  echo -e "${GREEN}All tooling files verified!${NC}"
  echo ""
  echo "Next steps:"
  echo "  1. Run: bash pre-commit-setup.sh"
  echo "  2. Read: SETUP_GUIDE.md"
  echo "  3. Reference: QUICK_REFERENCE.md"
  exit 0
else
  echo -e "${RED}Some files are missing!${NC}"
  exit 1
fi
