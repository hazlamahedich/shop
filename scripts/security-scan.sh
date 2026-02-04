#!/bin/bash
# Local Security Scanning Script
# Usage: ./scripts/security-scan.sh [backend|frontend|all]
# Run this script locally to catch security issues before pushing

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Parse arguments
SCOPE="${1:-all}"

echo -e "${BLUE}=== Security Scanning Script ===${NC}"
echo -e "${BLUE}Scope: ${SCOPE}${NC}\n"

# Function to print section header
print_header() {
    echo -e "\n${BLUE}=== $1 ===${NC}"
}

# Function to print success
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

# Function to print warning
print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# Function to print error
print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Backend Security Scans
scan_backend() {
    print_header "Backend Security Scans"

    cd "${PROJECT_ROOT}/backend"

    # Bandit - Python Security Linter
    print_header "Bandit Security Scan"
    if command_exists bandit; then
        bandit -r app/ -ll || print_warning "Bandit found issues"
    else
        pip install bandit[toml] >/dev/null 2>&1
        bandit -r app/ -ll || print_warning "Bandit found issues"
    fi

    # Safety - Dependency Vulnerability Scanner
    print_header "Safety Dependency Scan"
    if command_exists safety; then
        safety check || print_warning "Safety found vulnerabilities"
    else
        pip install safety >/dev/null 2>&1
        safety check || print_warning "Safety found vulnerabilities"
    fi

    # Semgrep - Static Analysis (if installed)
    print_header "Semgrep Static Analysis"
    if command_exists semgrep; then
        semgrep --config auto --error || print_warning "Semgrep found issues"
    else
        print_warning "Semgrep not installed. Run: pip install semgrep"
    fi

    # PIP Audit (Python 3.11+)
    print_header "PIP Audit"
    if command_exists pip-audit; then
        pip-audit || print_warning "PIP audit found vulnerabilities"
    else
        pip install pip-audit >/dev/null 2>&1
        pip-audit || print_warning "PIP audit found vulnerabilities"
    fi

    cd "${PROJECT_ROOT}"
}

# Frontend Security Scans
scan_frontend() {
    print_header "Frontend Security Scans"

    cd "${PROJECT_ROOT}/frontend"

    # npm Audit
    print_header "npm Dependency Audit"
    npm audit --audit-level=high || print_warning "npm audit found vulnerabilities"

    # npm outdated
    print_header "Outdated Dependencies"
    npm outdated || print_success "All dependencies up to date"

    # Check for dotenv files
    print_header "Check for .env files"
    if find . -name ".env*" -type f | grep -v node_modules; then
        print_warning "Found .env files (ensure they're not committed)"
    fi

    cd "${PROJECT_ROOT}"
}

# Secret Scanning
scan_secrets() {
    print_header "Secret Scanning (Gitleaks)"

    cd "${PROJECT_ROOT}"

    # Gitleaks
    if command_exists gitleaks; then
        gitleaks detect --source . --verbose || print_warning "Gitleaks found potential secrets"
    else
        print_warning "Gitleaks not installed. Install from: https://github.com/gitleaks/gitleaks"
    fi

    # Check for common secret patterns
    print_header "Quick Secret Pattern Check"
    local secrets_found=false

    if git grep -iE "(password|secret|api[_-]?key|token)\s*=\s*['\"][^'\"]+['\"]" -- '*.py' '*.ts' '*.tsx' '*.js' '*.yml' '*.yaml' 2>/dev/null; then
        print_error "Possible hardcoded secrets found!"
        secrets_found=true
    fi

    if [ "$secrets_found" = false ]; then
        print_success "No obvious hardcoded secrets detected"
    fi
}

# Infrastructure Security Scans
scan_infrastructure() {
    print_header "Infrastructure Security Scans"

    # Trivy config scan
    if command_exists trivy; then
        print_header "Trivy Config Scan"
        trivy config --severity HIGH,CRITICAL . || print_warning "Trivy found issues"
    else
        print_warning "Trivy not installed. Install from: https://aquasecurity.github.io/trivy/"
    fi

    # Dockerfile linting
    if command_exists hadolint; then
        print_header "Dockerfile Linting"
        for dockerfile in $(find . -name "Dockerfile*" -not -path "./.git/*" -not -path "./node_modules/*"); do
            echo "Linting: $dockerfile"
            hadolint "$dockerfile" || print_warning "Hadolint found issues in $dockerfile"
        done
    else
        print_warning "Hadolint not installed. Install from: https://github.com/hadolint/hadolint"
    fi
}

# Run all scans
scan_all() {
    scan_secrets
    scan_backend
    scan_frontend
    scan_infrastructure

    print_header "Security Scan Summary"
    print_success "Security scans completed!"
    echo -e "\n${YELLOW}Remember:${NC}"
    echo "  - Review all warnings above"
    echo "  - Fix HIGH/CRITICAL issues before committing"
    echo "  - Update dependencies regularly"
    echo "  - Never commit secrets or credentials"
    echo "  - Use environment variables for sensitive data"
}

# Main execution
case "$SCOPE" in
    backend)
        scan_backend
        ;;
    frontend)
        scan_frontend
        ;;
    secrets)
        scan_secrets
        ;;
    infrastructure)
        scan_infrastructure
        ;;
    all)
        scan_all
        ;;
    *)
        echo "Usage: $0 [backend|frontend|secrets|infrastructure|all]"
        exit 1
        ;;
esac

exit 0
