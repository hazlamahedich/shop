#!/bin/bash
# Railway Deployment Script for Shopping Assistant Bot
# Usage: ./railway.sh <MERCHANT_KEY> <SECRET_KEY>
set -euo pipefail  # Exit on error, undefined vars, pipe failures

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Required arguments
MERCHANT_KEY="${1:-}"
SECRET_KEY="${2:-}"

# Validate arguments
if [[ -z "$MERCHANT_KEY" ]] || [[ -z "$SECRET_KEY" ]]; then
    echo -e "${RED}ERROR: Missing required arguments${NC}"
    echo "Usage: $0 <MERCHANT_KEY> <SECRET_KEY>"
    exit 1
fi

# Configuration
PROJECT_NAME="shop-bot-${MERCHANT_KEY}"
SERVICE_NAME="web"

# Progress tracking
PROGRESS=0
MAX_PROGRESS=100

log_progress() {
    local step=$1
    local message=$2
    PROGRESS=$3
    echo -e "${BLUE}[${PROGRESS}%]${NC} $step: $message"
}

log_success() {
    echo -e "${GREEN}✓${NC} $1"
}

log_error() {
    echo -e "${RED}✗${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Error handler with specific messaging and troubleshooting links
handle_error() {
    local step=$1
    local error_type=$2
    local troubleshooting_url=$3
    log_error "Deployment failed at step: $step"
    log_error "Error type: $error_type"
    if [[ -n "$troubleshooting_url" ]]; then
        log_error "Troubleshooting: $troubleshooting_url"
    fi
    exit 1
}

trap 'handle_error "Unknown error during deployment" "unknown" "https://docs.railway.app/reference/troubleshooting"' ERR

# Check prerequisites
check_railway_cli() {
    if ! command -v railway &> /dev/null; then
        handle_error "CLI check" "railway-cli-missing" "https://docs.railway.app/reference/cli#installation"
    fi
    log_success "Railway CLI detected"
}

# Deploy to Railway
deploy_railway() {
    log_progress "Prerequisites" "Checking required tools" 10
    check_railway_cli

    # Login check (will prompt if not authenticated)
    log_progress "Authentication" "Verifying Railway authentication" 20
    if ! railway whoami &> /dev/null; then
        log_warning "Not authenticated with Railway. Please run: railway login"
        handle_error "Authentication" "not-authenticated" "https://docs.railway.app/reference/cli"
    fi
    log_success "Authenticated with Railway"

    # Initialize project or link existing
    log_progress "Project Setup" "Creating/checking Railway project" 30
    if ! railway list &> /dev/null; then
        railway init --name "$PROJECT_NAME" || {
            handle_error "Project initialization" "project-init-failed" "https://docs.railway.app/reference/cli"
        }
        log_success "Created project: $PROJECT_NAME"
    else
        log_warning "Project already exists, linking to current directory"
    fi

    # Set environment variables
    log_progress "Configuration" "Setting environment variables" 40
    railway variables set "MERCHANT_KEY=$MERCHANT_KEY" "SECRET_KEY=$SECRET_KEY" "DEBUG=false" "LOG_LEVEL=info" || {
        handle_error "Environment configuration" "env-vars-failed" "https://docs.railway.app/reference/variables"
    }
    log_success "Set environment variables"

    # Add service from root directory
    log_progress "Service Setup" "Configuring Railway service" 50
    if [[ ! -f "railway.toml" ]]; then
        cat > railway.toml << EOF
[build]
builder = "DOCKERFILE"
dockerfilePath = "backend/Dockerfile"

[deploy]
startCommand = "uvicorn backend.app.main:app --host 0.0.0.0 --port \\\$PORT"
healthcheckPath = "/health"
healthcheckTimeout = 300
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 10
EOF
        log_success "Created railway.toml configuration"
    fi

    # Deploy application
    log_progress "Deployment" "Building and deploying containers" 70
    deploy_output=$(railway up 2>&1)
    deploy_exit=$?

    if [[ $deploy_exit -ne 0 ]]; then
        if echo "$deploy_output" | grep -qi "timeout"; then
            handle_error "Container build" "build-timeout" "https://docs.railway.app/deploy/builds"
        fi
        handle_error "Deployment" "deploy-failed" "https://docs.railway.app/deploy/deployments"
    fi
    log_success "Deployment completed successfully"

    # Wait for deployment to be active
    log_progress "Health Check" "Verifying deployment health" 90
    local max_attempts=30
    local attempt=0
    while [[ $attempt -lt $max_attempts ]]; do
        STATUS=$(railway status --json 2>/dev/null | grep -o '"status":"[^"]*"' | head -1 | cut -d'"' -f4)
        if [[ "$STATUS" == "running" || "$STATUS" == "healthy" ]]; then
            log_success "Service is running and healthy"
            break
        fi
        attempt=$((attempt + 1))
        sleep 2
    done

    if [[ $attempt -eq $max_attempts ]]; then
        log_warning "Deployment complete but health check inconclusive"
    fi

    # Get service URL
    PROJECT_URL=$(railway domain --json 2>/dev/null | grep -o '"domain":"[^"]*"' | head -1 | cut -d'"' -f4)

    log_progress "Complete" "Deployment successful!" 100
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}Deployment Complete!${NC}"
    echo ""
    echo -e "Project Name: ${BLUE}$PROJECT_NAME${NC}"
    if [[ -n "$PROJECT_URL" ]]; then
        echo -e "Project URL: ${BLUE}https://$PROJECT_URL${NC}"
    fi
    echo ""
    echo -e "${YELLOW}Next Steps:${NC}"
    echo "  1. Connect your Facebook Page (Story 1.3)"
    echo "  2. Connect your Shopify Store (Story 1.4)"
    echo "  3. Configure LLM Provider (Story 1.5)"
    echo ""
    echo -e "Monitor logs: ${BLUE}railway logs${NC}"
    echo -e "View status: ${BLUE}railway status${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

# Main deployment flow
main() {
    echo -e "${BLUE}════════════════════════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}Railway Deployment Script${NC}"
    echo -e "${BLUE}Shopping Assistant Bot - One-Click Deployment${NC}"
    echo -e "${BLUE}════════════════════════════════════════════════════════════════════════════════${NC}"
    echo ""

    deploy_railway

    echo ""
    log_success "STEP:SUCCESS"
}

# Run main function
main "$@"
